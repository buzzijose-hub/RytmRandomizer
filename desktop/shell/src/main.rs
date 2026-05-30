//! RytmRandomizer Cockpit — Tauri shell entry point.

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::path::PathBuf;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};
use std::thread;
use std::thread::JoinHandle;
use std::time::{Duration, Instant};

use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager, WebviewWindow, WindowEvent,
};

use rytm_randomizer_shell_lib::sidecar::{
    backoff_delay, clear_token_file, read_token_file, resolve_token_file_path, shutdown_child,
    spawn_sidecar, token_bootstrap_script, BACKOFF_RESET_SECS,
};

const PYTHON_BIN: &str = "python";
const TOKEN_BRIDGE_POLL_MS: u64 = 250;

fn supervise(
    shutdown: Arc<AtomicBool>,
    child_slot: Arc<Mutex<Option<std::process::Child>>>,
    token_file: PathBuf,
) {
    let mut failures: u32 = 0;
    while !shutdown.load(Ordering::SeqCst) {
        let started = Instant::now();
        if let Err(err) = clear_token_file(&token_file) {
            log::warn!("failed to clear stale sidecar token file: {err}");
        }
        match spawn_sidecar(PYTHON_BIN, &token_file) {
            Ok(child) => {
                *child_slot.lock().expect("child slot poisoned") = Some(child);
                loop {
                    if shutdown.load(Ordering::SeqCst) {
                        return;
                    }
                    let exited = {
                        let mut guard = child_slot.lock().expect("child slot poisoned");
                        match guard.as_mut() {
                            Some(c) => matches!(c.try_wait(), Ok(Some(_))),
                            None => true,
                        }
                    };
                    if exited {
                        break;
                    }
                    thread::sleep(Duration::from_millis(250));
                }
                if started.elapsed() >= Duration::from_secs(BACKOFF_RESET_SECS) {
                    failures = 0;
                }
            }
            Err(err) => {
                log::error!("sidecar spawn failed: {err}");
            }
        }
        if shutdown.load(Ordering::SeqCst) {
            return;
        }
        let delay = backoff_delay(failures);
        log::warn!("sidecar exited; restarting in {delay:?}");
        thread::sleep(delay);
        failures = failures.saturating_add(1);
    }
}

fn start_token_bridge(
    shutdown: Arc<AtomicBool>,
    window: WebviewWindow,
    token_file: PathBuf,
) -> JoinHandle<()> {
    thread::spawn(move || {
        let mut injected_token: Option<String> = None;
        while !shutdown.load(Ordering::SeqCst) {
            match read_token_file(&token_file) {
                Ok(Some(token)) if injected_token.as_deref() != Some(token.as_str()) => {
                    let script = token_bootstrap_script(&token);
                    match window.eval(&script) {
                        Ok(()) => {
                            injected_token = Some(token);
                            log::info!("bridged sidecar websocket token into cockpit webview");
                        }
                        Err(err) => {
                            log::warn!("failed to inject sidecar websocket token: {err}");
                        }
                    }
                }
                Ok(_) => {}
                Err(err) => {
                    log::warn!("failed to read sidecar websocket token file: {err}");
                }
            }
            thread::sleep(Duration::from_millis(TOKEN_BRIDGE_POLL_MS));
        }
    })
}

fn main() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    let shutdown = Arc::new(AtomicBool::new(false));
    let child_slot: Arc<Mutex<Option<std::process::Child>>> = Arc::new(Mutex::new(None));
    let token_bridge_slot: Arc<Mutex<Option<JoinHandle<()>>>> = Arc::new(Mutex::new(None));
    let token_file = resolve_token_file_path();
    let supervisor = {
        let shutdown = Arc::clone(&shutdown);
        let slot = Arc::clone(&child_slot);
        let token_file = token_file.clone();
        thread::spawn(move || supervise(shutdown, slot, token_file))
    };
    let teardown = {
        let shutdown = Arc::clone(&shutdown);
        let slot = Arc::clone(&child_slot);
        let bridge_slot = Arc::clone(&token_bridge_slot);
        move || {
            shutdown.store(true, Ordering::SeqCst);
            if let Some(mut child) = slot.lock().expect("child slot poisoned").take() {
                shutdown_child(&mut child);
            }
            if let Some(handle) = bridge_slot
                .lock()
                .expect("token bridge slot poisoned")
                .take()
            {
                let _ = handle.join();
            }
        }
    };
    let teardown_for_close = teardown.clone();
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(move |app| {
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&quit])?;
            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .on_menu_event({
                    let teardown = teardown.clone();
                    move |app, event| {
                        if event.id.as_ref() == "quit" {
                            teardown();
                            app.exit(0);
                        }
                    }
                })
                .build(app)?;
            if let Some(window) = app.get_webview_window("main") {
                let handle = start_token_bridge(Arc::clone(&shutdown), window, token_file.clone());
                *token_bridge_slot
                    .lock()
                    .expect("token bridge slot poisoned") = Some(handle);
            } else {
                log::warn!("main webview not found; websocket token bridge not started");
            }
            Ok(())
        })
        .on_window_event(move |window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                teardown_for_close();
                window.app_handle().exit(0);
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running RytmRandomizer Cockpit");
    let _ = supervisor.join();
}
