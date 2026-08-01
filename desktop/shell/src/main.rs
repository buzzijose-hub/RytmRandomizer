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
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

use rytm_randomizer_shell_lib::sidecar::{self, SidecarLaunch};

const TOKEN_BRIDGE_POLL_MS: u64 = 250;

fn supervise<F>(
    shutdown: Arc<AtomicBool>,
    child_slot: Arc<Mutex<Option<std::process::Child>>>,
    token_file: PathBuf,
    arm_secret_file: PathBuf,
    launch: SidecarLaunch,
    port: u16,
    on_spawn_failure: F,
) where
    F: Fn(u32, &str),
{
    let mut failures: u32 = 0;
    let mut spawn_failures: u32 = 0;
    while !shutdown.load(Ordering::SeqCst) {
        let started = Instant::now();
        if let Err(err) = sidecar::clear_token_file(&token_file) {
            log::warn!("failed to clear stale sidecar token file: {err}");
        }
        // Same reason as the token: a secret left over from the previous
        // launch must never be injected as if it authorised this one.
        if let Err(err) = sidecar::clear_token_file(&arm_secret_file) {
            log::warn!("failed to clear stale sidecar arm-secret file: {err}");
        }
        match sidecar::spawn_sidecar(&launch, &token_file, &arm_secret_file, port) {
            Ok(child) => {
                spawn_failures = 0;
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
                if started.elapsed() >= Duration::from_secs(sidecar::BACKOFF_RESET_SECS) {
                    failures = 0;
                }
            }
            Err(err) => {
                spawn_failures = spawn_failures.saturating_add(1);
                log::error!(
                    "sidecar spawn failed ({spawn_failures} consecutive): {err} [{}]",
                    launch.describe()
                );
                // Surface the real error to the operator instead of
                // crash-looping silently. The callback fires once, at the
                // threshold, so the retry loop never stacks dialogs.
                on_spawn_failure(spawn_failures, &err.to_string());
            }
        }
        if shutdown.load(Ordering::SeqCst) {
            return;
        }
        let delay = sidecar::backoff_delay(failures);
        log::warn!("sidecar exited; restarting in {delay:?}");
        thread::sleep(delay);
        failures = failures.saturating_add(1);
    }
}

/// Poll one sidecar-written credential file and inject it into the webview
/// whenever its value changes.
///
/// Shared by the WS handshake token and the ARM secret. Both are written by
/// the sidecar *after* the shell has already started, and both are rewritten
/// on every sidecar restart, so the contract is identical: poll, skip while
/// the file is missing or blank (`read_token_file` returns `None`), inject on
/// first sight and again on any change, and never latch a value the sidecar
/// has since replaced. Injecting on change — not just once — is what makes a
/// mid-session sidecar restart recover without the operator relaunching.
///
/// `label` only names the credential in the logs; the value itself is never
/// logged.
fn start_credential_bridge<S>(
    shutdown: Arc<AtomicBool>,
    window: WebviewWindow,
    credential_file: PathBuf,
    label: &'static str,
    build_script: S,
) -> JoinHandle<()>
where
    S: Fn(&str) -> String + Send + 'static,
{
    thread::spawn(move || {
        let mut injected: Option<String> = None;
        while !shutdown.load(Ordering::SeqCst) {
            match sidecar::read_token_file(&credential_file) {
                Ok(Some(value)) if injected.as_deref() != Some(value.as_str()) => {
                    let script = build_script(&value);
                    match window.eval(&script) {
                        Ok(()) => {
                            injected = Some(value);
                            log::info!("bridged sidecar {label} into cockpit webview");
                        }
                        Err(err) => {
                            log::warn!("failed to inject sidecar {label}: {err}");
                        }
                    }
                }
                Ok(_) => {}
                Err(err) => {
                    log::warn!("failed to read sidecar {label} file: {err}");
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
    let arm_bridge_slot: Arc<Mutex<Option<JoinHandle<()>>>> = Arc::new(Mutex::new(None));
    let token_file = sidecar::resolve_token_file_path();
    let arm_secret_file = sidecar::resolve_arm_secret_file_path();
    let teardown = {
        let shutdown = Arc::clone(&shutdown);
        let slot = Arc::clone(&child_slot);
        let bridge_slot = Arc::clone(&token_bridge_slot);
        let arm_slot = Arc::clone(&arm_bridge_slot);
        move || {
            shutdown.store(true, Ordering::SeqCst);
            if let Some(mut child) = slot.lock().expect("child slot poisoned").take() {
                sidecar::shutdown_child(&mut child);
            }
            if let Some(handle) = bridge_slot
                .lock()
                .expect("token bridge slot poisoned")
                .take()
            {
                let _ = handle.join();
            }
            if let Some(handle) = arm_slot
                .lock()
                .expect("arm secret bridge slot poisoned")
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

            // Launch resolution: bundled binary from the Tauri resources
            // (production double-click) with a PATH-python dev fallback,
            // plus a dynamically-selected WS port so an occupied 4317 can
            // never brick the launch.
            let exe_dir = std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(std::path::Path::to_path_buf));
            let resource_dir = app.path().resource_dir().ok();
            let candidates = sidecar::bundled_sidecar_candidates(exe_dir, resource_dir);
            let bin_override = std::env::var(sidecar::SIDECAR_BIN_ENV_VAR).ok();
            let launch = sidecar::resolve_sidecar_launch(bin_override.as_deref(), &candidates);
            let port_override = std::env::var(sidecar::PORT_ENV_VAR).ok();
            let port = sidecar::pick_ws_port(port_override.as_deref());
            log::info!("sidecar launch mode: {} (ws port {port})", launch.describe());

            let dialog_handle = app.handle().clone();
            let launch_description = launch.describe();
            let on_spawn_failure = move |failures: u32, err: &str| {
                if failures != sidecar::SPAWN_FAILURE_DIALOG_THRESHOLD {
                    return;
                }
                let message = format!(
                    "The RytmRandomizer cockpit sidecar failed to start {failures} times in a row.\n\n\
                     Launch mode: {launch_description}\n\
                     Last error: {err}\n\n\
                     If this is a dev checkout, make sure `python` is on PATH with the project \
                     installed (pip install -e \".[dev]\"). The shell keeps retrying in the \
                     background; the window will connect automatically once the sidecar starts."
                );
                dialog_handle
                    .dialog()
                    .message(message)
                    .kind(MessageDialogKind::Error)
                    .title("RytmRandomizer sidecar failed to start")
                    .show(|_| {});
            };

            {
                let shutdown = Arc::clone(&shutdown);
                let slot = Arc::clone(&child_slot);
                let token_file = token_file.clone();
                let arm_secret_file = arm_secret_file.clone();
                thread::spawn(move || {
                    supervise(
                        shutdown,
                        slot,
                        token_file,
                        arm_secret_file,
                        launch,
                        port,
                        on_spawn_failure,
                    )
                });
            }

            if let Some(window) = app.get_webview_window("main") {
                let handle = start_credential_bridge(
                    Arc::clone(&shutdown),
                    window.clone(),
                    token_file.clone(),
                    "websocket token",
                    move |token| sidecar::token_bootstrap_script(token, port),
                );
                *token_bridge_slot
                    .lock()
                    .expect("token bridge slot poisoned") = Some(handle);
                // The ARM secret rides its own bridge: it is written a moment
                // later than the token and authorises transmit rather than
                // connection, so a shared bridge would either delay the
                // handshake or couple the two credentials' lifetimes.
                let arm_handle = start_credential_bridge(
                    Arc::clone(&shutdown),
                    window,
                    arm_secret_file.clone(),
                    "arm secret",
                    sidecar::arm_secret_bootstrap_script,
                );
                *arm_bridge_slot
                    .lock()
                    .expect("arm secret bridge slot poisoned") = Some(arm_handle);
            } else {
                log::warn!("main webview not found; credential bridges not started");
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
}
