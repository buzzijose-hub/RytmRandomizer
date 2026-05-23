//! RytmRandomizer Cockpit — Tauri shell entry point.

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};
use std::thread;
use std::time::{Duration, Instant};

use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager, WindowEvent,
};

use rytm_randomizer_shell_lib::sidecar::{
    backoff_delay, shutdown_child, spawn_sidecar, BACKOFF_RESET_SECS,
};

const PYTHON_BIN: &str = "python";

fn supervise(shutdown: Arc<AtomicBool>, child_slot: Arc<Mutex<Option<std::process::Child>>>) {
    let mut failures: u32 = 0;
    while !shutdown.load(Ordering::SeqCst) {
        let started = Instant::now();
        match spawn_sidecar(PYTHON_BIN) {
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
        log::warn!("sidecar exited; restarting in {:?}", delay);
        thread::sleep(delay);
        failures = failures.saturating_add(1);
    }
}

fn main() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    let shutdown = Arc::new(AtomicBool::new(false));
    let child_slot: Arc<Mutex<Option<std::process::Child>>> = Arc::new(Mutex::new(None));
    let supervisor = {
        let shutdown = Arc::clone(&shutdown);
        let slot = Arc::clone(&child_slot);
        thread::spawn(move || supervise(shutdown, slot))
    };
    let teardown = {
        let shutdown = Arc::clone(&shutdown);
        let slot = Arc::clone(&child_slot);
        move || {
            shutdown.store(true, Ordering::SeqCst);
            if let Some(mut child) = slot.lock().expect("child slot poisoned").take() {
                shutdown_child(&mut child);
            }
        }
    };
    let teardown_for_close = teardown.clone();
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
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
