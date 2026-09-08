//! RytmRandomizer Cockpit — Tauri shell entry point.

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::path::PathBuf;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex, Weak,
};
use std::thread;
use std::thread::JoinHandle;
use std::time::{Duration, Instant};

use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Emitter, Manager, WebviewWindow, WindowEvent,
};
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

use rytm_randomizer_shell_lib::sidecar::{self, SidecarLaunch};
use rytm_randomizer_shell_lib::update_commands;
use rytm_randomizer_shell_lib::update_journal::{self, UpdateJournal};
use rytm_randomizer_shell_lib::update_policy::{
    Config as UpdateConfig, ConsentChoice, ErrorCode, JournalRecord, UpdateEvent,
    UpdateStatePayload, UPDATE_STATE_EVENT,
};
use rytm_randomizer_shell_lib::update_transport::{
    DisabledTransport, PluginTransport, SharedTransport, TransportOutcome,
};
use rytm_randomizer_shell_lib::updater::{self, EffectSink, Updater};

const TOKEN_BRIDGE_POLL_MS: u64 = 250;

/// This build's version, from Cargo. `sync_version.py` (PR-A) keeps
/// `Cargo.toml` equal to the repo-root `VERSION` file, and
/// `test_version_single_source.py` fails CI if they drift — so this is the
/// single source of truth reaching the updater, not a second declaration.
const APP_VERSION: &str = env!("CARGO_PKG_VERSION");

/// The production [`EffectSink`].
///
/// Deliberately minimal, and deliberately **incomplete in one direction**:
/// it journals every effect and republishes state to the webview, but the
/// three network/install effects are not yet performed. See the module note
/// on [`ShellSink::install_staged`].
struct ShellSink {
    journal: UpdateJournal,
    window: Mutex<Option<WebviewWindow>>,
    /// The network half. Held behind the [`Transport`] trait so the driver
    /// loop is exercised in tests without a network or a running app.
    transport: Mutex<Option<SharedTransport>>,
    /// A weak handle to this same sink, for transport callbacks.
    weak_self: Mutex<Weak<ShellSink>>,
    /// Feeds transport outcomes back in as [`UpdateEvent`]s.
    ///
    /// Set after construction because the driver owns the sink — the cycle is
    /// deliberate and is what lets an async result re-enter the pure state
    /// machine on whatever thread it completes on.
    driver: Mutex<Option<Updater<Arc<ShellSink>>>>,
}

impl ShellSink {
    fn new(journal: UpdateJournal) -> Self {
        Self {
            journal,
            window: Mutex::new(None),
            transport: Mutex::new(None),
            weak_self: Mutex::new(Weak::new()),
            driver: Mutex::new(None),
        }
    }

    fn attach_window(&self, window: WebviewWindow) {
        *self.window.lock().expect("update window slot poisoned") = Some(window);
    }

    /// Install the transport and the driver the outcomes feed back into.
    fn attach_transport(
        &self,
        transport: SharedTransport,
        driver: Updater<Arc<ShellSink>>,
        weak_self: Weak<ShellSink>,
    ) {
        *self.weak_self.lock().expect("weak self slot poisoned") = weak_self;
        *self.transport.lock().expect("transport slot poisoned") = Some(transport);
        *self.driver.lock().expect("driver slot poisoned") = Some(driver);
    }

    /// The attached transport, if any.
    fn transport(&self) -> Option<SharedTransport> {
        self.transport
            .lock()
            .expect("transport slot poisoned")
            .as_ref()
            .map(Arc::clone)
    }

    /// A weak self-reference for transport callbacks.
    ///
    /// Weak so a completing download cannot keep the sink — and through it the
    /// window and journal — alive past shutdown.
    fn self_handle(&self) -> Weak<ShellSink> {
        self.weak_self
            .lock()
            .expect("weak self slot poisoned")
            .clone()
    }

    /// Hand one transport outcome back to the state machine.
    ///
    /// Every network result re-enters through here, so the policy stays the
    /// only thing that decides what an outcome MEANS — the transport reports
    /// facts, never decisions.
    fn report(&self, outcome: TransportOutcome) {
        let driver = self
            .driver
            .lock()
            .expect("driver slot poisoned")
            .as_ref()
            .cloned();
        let Some(driver) = driver else {
            log::warn!("update transport reported before the driver was attached");
            return;
        };
        driver.handle(match outcome {
            TransportOutcome::Manifest { body, duration_ms } => {
                UpdateEvent::ManifestFetched { body, duration_ms }
            }
            TransportOutcome::ManifestFailed { code } => UpdateEvent::ManifestFetchFailed { code },
            TransportOutcome::Staged {
                version,
                bytes,
                duration_ms,
            } => UpdateEvent::DownloadStaged {
                version,
                bytes,
                duration_ms,
            },
            TransportOutcome::DownloadFailed { version, code } => {
                UpdateEvent::DownloadFailed { version, code }
            }
            TransportOutcome::SignatureRejected { version } => {
                UpdateEvent::SignatureRejected { version }
            }
        });
    }
}

impl EffectSink for ShellSink {
    fn fetch_manifest(&self, channel: &str) {
        let Some(transport) = self.transport() else {
            // No transport attached is a wiring bug, not a network condition.
            // Reporting it as a typed failure keeps the panel honest instead
            // of leaving it spinning on a check that will never resolve.
            self.report(TransportOutcome::ManifestFailed {
                code: ErrorCode::NetworkUnavailable,
            });
            return;
        };
        let sink = self.self_handle();
        transport.fetch_manifest(
            channel,
            Box::new(move |outcome| {
                if let Some(sink) = sink.upgrade() {
                    sink.report(outcome);
                }
            }),
        );
    }

    fn download_artifact(&self, version: &str, url: &str, signature: &str) {
        let Some(transport) = self.transport() else {
            self.report(TransportOutcome::DownloadFailed {
                version: version.to_string(),
                code: ErrorCode::NetworkUnavailable,
            });
            return;
        };
        let sink = self.self_handle();
        transport.download(
            version,
            url,
            signature,
            Box::new(move |outcome| {
                if let Some(sink) = sink.upgrade() {
                    sink.report(outcome);
                }
            }),
        );
    }

    fn install_staged(&self, version: &str, choice: ConsentChoice) {
        // Only ever reached after the graceful sidecar shutdown confirmed the
        // child exited — the policy emits this effect on `SidecarExited` and
        // nowhere else, so the swap never races a live MIDI session.
        let Some(transport) = self.transport() else {
            log::error!("install requested for {version} ({choice:?}) with no transport attached");
            return;
        };
        if let Err(code) = transport.install(version) {
            // A failed install must leave the RUNNING app intact and say so.
            // Silently swallowing it would strand the operator on a version
            // they were told had updated.
            log::error!("install of {version} refused: {code:?}");
        }
    }

    fn send_beacon(&self, version: &str, target: &str) {
        // Fire-and-forget by construction: no retry, no error surfaced, no
        // identifying data. The policy has already decided a beacon is
        // permitted (freeze and BEACON=off suppress the effect entirely), so
        // reaching here means the operator's settings allow the check-in.
        let Some(transport) = self.transport() else {
            return;
        };
        transport.beacon(&updater::beacon_asset_url(version, target));
    }

    fn journal(&self, record: &JournalRecord) {
        updater::write_journal_row(&self.journal, record);
    }

    fn emit_state(&self, payload: &UpdateStatePayload) {
        // Contract I2: one typed event carries the whole update surface.
        if let Some(window) = self
            .window
            .lock()
            .expect("update window slot poisoned")
            .as_ref()
        {
            if let Err(err) = window.emit(UPDATE_STATE_EVENT, payload) {
                log::warn!("failed to emit {UPDATE_STATE_EVENT}: {err}");
            }
        }
    }
}

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
                Ok(current)
                    if sidecar::should_inject_credential(
                        current.as_deref(),
                        injected.as_deref(),
                    ) =>
                {
                    let value = current.expect("should_inject_credential implies Some");
                    let script = build_script(&value);
                    match window.eval(&script) {
                        Ok(()) => {
                            injected = Some(value);
                            log::info!("bridged sidecar {label} into cockpit webview");
                        }
                        Err(err) => {
                            // Deliberately do NOT record the value as
                            // injected: a failed eval must be retried on the
                            // next poll, or a transient webview error would
                            // strand the cockpit without its credential.
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

/// The driver handle the update commands dispatch into.
type UpdateCommands = update_commands::UpdateCommandState<Arc<ShellSink>>;

// ---------------------------------------------------------------------------
// The update command surface (what the panel's buttons actually invoke)
// ---------------------------------------------------------------------------
//
// Each command is a two-line adapter: turn a gesture into an UpdateEvent and
// hand it to the driver. No command decides anything — whether an update
// exists, whether freeze applies, whether a consent is still valid are all the
// policy's calls. Keeping these thin is what stops a second, divergent state
// machine growing in the IPC layer.

/// "Check now". Idempotent: the policy ignores a check while one is running.
#[tauri::command]
fn update_check_now(state: tauri::State<'_, UpdateCommands>) {
    state.driver.handle(UpdateEvent::CheckRequested);
}

/// "Confirm choice" — install now, install on quit, or skip this version.
///
/// Returns `Err` on an unrecognised choice rather than defaulting, so a
/// malformed invocation surfaces in the panel instead of silently installing
/// or silently suppressing.
#[tauri::command]
fn update_confirm_choice(
    version: String,
    choice: String,
    state: tauri::State<'_, UpdateCommands>,
) -> Result<(), String> {
    let event = update_commands::prompt_event(&version, &choice)
        .ok_or_else(|| format!("unrecognised update choice: {choice}"))?;
    state.driver.handle(event);
    Ok(())
}

// NOTE: there is deliberately no `update_set_frozen` command.
//
// Freeze is a PROCESS-LIFETIME posture read from `RYTM_RAND_UPDATES` at
// startup, not runtime state. Adding a command to flip it would mean the
// policy's freeze short-circuit could change mid-flight — so a check already
// in the air could complete after the operator froze updates, which is
// exactly the guarantee freeze exists to make. The panel's checkbox is a
// client-side rendering of the env var (spec §7), and making it a real
// toggle is a design change, not a wiring gap.

fn main() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    let shutdown = Arc::new(AtomicBool::new(false));
    let child_slot: Arc<Mutex<Option<std::process::Child>>> = Arc::new(Mutex::new(None));
    let token_bridge_slot: Arc<Mutex<Option<JoinHandle<()>>>> = Arc::new(Mutex::new(None));
    let arm_bridge_slot: Arc<Mutex<Option<JoinHandle<()>>>> = Arc::new(Mutex::new(None));
    let token_file = sidecar::resolve_token_file_path();
    let arm_secret_file = sidecar::resolve_arm_secret_file_path();

    // Update subsystem. The config dir is resolved once and shared by the
    // journal and the install id; the driver holds all update state.
    let update_config_dir = update_journal::default_config_dir();
    let update_config: UpdateConfig = updater::resolve_config_from_env(
        APP_VERSION,
        &updater::resolve_install_id(&update_config_dir),
    );
    log::info!(
        "updates: enabled={} beacon={} channel={} install_permitted={}",
        update_config.updates_enabled,
        update_config.beacon_enabled,
        update_config.channel,
        update_config.install_permitted()
    );
    let update_sink = Arc::new(ShellSink::new(UpdateJournal::new(update_config_dir)));
    let updater_driver = Updater::new(update_config, Arc::clone(&update_sink));

    let teardown = {
        let shutdown = Arc::clone(&shutdown);
        let slot = Arc::clone(&child_slot);
        let bridge_slot = Arc::clone(&token_bridge_slot);
        let arm_slot = Arc::clone(&arm_bridge_slot);
        let updater_driver = updater_driver.clone();
        move || {
            shutdown.store(true, Ordering::SeqCst);
            if let Some(mut child) = slot.lock().expect("child slot poisoned").take() {
                // Spec §5: an install-on-quit runs ONLY after this sequence
                // confirms the sidecar exited — never concurrently with it.
                // The outcome, not the mere fact that we asked, is what
                // decides: a SIGKILL after the grace window is not a
                // confirmed clean exit, so it feeds the refusal event and the
                // pending install is journalled as failed rather than run.
                let outcome = sidecar::shutdown_child(&mut child);
                updater_driver.handle(if outcome.is_clean_exit() {
                    UpdateEvent::SidecarExited
                } else {
                    UpdateEvent::QuitWithoutSidecarExit
                });
            } else {
                // No child was running, so there is nothing to race with.
                updater_driver.handle(UpdateEvent::SidecarExited);
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
        // The updater plugin owns the signed download/stage/swap transport.
        // Registering it is inert until `tauri.conf.json`'s
        // `plugins.updater.pubkey` is non-empty (operator action item 1): with
        // no key the plugin cannot verify — and therefore cannot install — any
        // artifact, which is the structural half of "check-and-notify-only".
        // The policy half is `Config::install_permitted()`, which is false for
        // the same reason and stops an install effect being emitted at all.
        .plugin(tauri_plugin_updater::Builder::new().build())
        // Without this the panel's buttons are decorative: "Check now" set a
        // note and "Confirm choice" updated React state, and neither reached
        // the driver. Same class of defect as the IPC/DOM mismatch, one layer
        // up — everything looked wired and nothing was.
        .manage(UpdateCommands::new(updater_driver.clone()))
        .invoke_handler(tauri::generate_handler![
            update_check_now,
            update_confirm_choice
        ])
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
                // Contract I2: give the sink the window it publishes
                // `rytm-update-state` on, then emit the current state once so
                // the cockpit renders the right body (frozen / up-to-date /
                // dev-loop) from first paint instead of an empty panel.
                update_sink.attach_window(window.clone());

                // Attach the network half. Without a public key the plugin
                // cannot verify — and therefore must not download or install
                // — anything, so the transport is explicitly DISABLED rather
                // than absent: a disabled transport reports a typed failure
                // the panel can show, where an absent one left the check
                // spinning forever.
                let transport: SharedTransport = if updater::signing_key_present() {
                    Arc::new(PluginTransport::new(app.handle().clone(), true))
                } else {
                    Arc::new(DisabledTransport::new(ErrorCode::SignatureRejected))
                };
                update_sink.attach_transport(
                    transport,
                    updater_driver.clone(),
                    Arc::downgrade(&update_sink),
                );

                update_sink.emit_state(&updater_driver.payload());

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
