//! Debug-only native acceptance controls. Production builds contain none of this.
//!
//! The real shell, IPC, driver, journal, supervisor and plugin verifier run.
//! Only network destinations and terminal install/restart operations are fixtures.

use std::path::PathBuf;
use std::process::Child;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tauri::Runtime;

use crate::update_policy::{ConsentChoice, ErrorCode};

pub const CONFIG_ENV: &str = "RYTM_RAND_NATIVE_TEST_CONFIG";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Options {
    root: PathBuf,
    origin: String,
    scenario: String,
    public_key: String,
    install_id: String,
    python: PathBuf,
    sidecar_entry: PathBuf,
}

#[derive(Clone, Serialize)]
struct TerminalEvent {
    event: &'static str,
    version: String,
    choice: String,
    sha256: String,
}

type Teardown = Arc<dyn Fn() + Send + Sync>;

pub struct NativeFixture {
    options: Options,
    terminal: Mutex<Vec<TerminalEvent>>,
    teardown: Mutex<Option<Teardown>>,
    child: Mutex<Option<Arc<Mutex<Option<Child>>>>>,
    shutdown_requested: Mutex<Option<Arc<AtomicBool>>>,
}

impl NativeFixture {
    /// A feature-enabled binary refuses to start without an explicit sandbox.
    pub fn from_env() -> Arc<Self> {
        let path = std::env::var_os(CONFIG_ENV).expect("native-test requires a fixture config");
        let options: Options =
            serde_json::from_slice(&std::fs::read(path).expect("read native fixture config"))
                .expect("decode native fixture config");
        let url = reqwest::Url::parse(&options.origin).expect("fixture origin URL");
        assert!(
            url.scheme() == "http"
                && url.host_str() == Some("127.0.0.1")
                && url.port().is_some()
                && url.path() == "/"
                && url.username().is_empty()
                && url.password().is_none()
                && url.query().is_none()
                && url.fragment().is_none(),
            "native fixture must use one explicit loopback origin"
        );
        assert!(options.root.is_absolute() && options.root.is_dir());
        assert!(!options.public_key.is_empty());
        assert!(options.python.is_absolute() && options.python.is_file());
        assert!(options.sidecar_entry.is_absolute() && options.sidecar_entry.is_file());
        assert!(options.sidecar_entry.starts_with(&options.root));
        assert!(options
            .scenario
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_'));
        assert_eq!(
            std::env::var("RYTM_RAND_MIDI_BACKEND").as_deref(),
            Ok("off")
        );
        assert_eq!(
            std::env::var(crate::updater::MANIFEST_URL_ENV_VAR)
                .ok()
                .as_deref(),
            Some(options.origin.as_str()),
            "native manifest traffic must use the fixture origin"
        );
        Arc::new(Self {
            options,
            terminal: Mutex::new(Vec::new()),
            teardown: Mutex::new(None),
            child: Mutex::new(None),
            shutdown_requested: Mutex::new(None),
        })
    }

    pub fn install_id(&self) -> &str {
        &self.options.install_id
    }

    pub fn signing_key_present(&self) -> bool {
        self.options.scenario != "missing_key"
    }

    pub fn sidecar_launch(&self) -> crate::sidecar::SidecarLaunch {
        crate::sidecar::SidecarLaunch::NativeFixturePython {
            python: self.options.python.clone(),
            entry: self.options.sidecar_entry.clone(),
        }
    }

    pub fn configure(&self, config: &mut tauri::Config) {
        config.build.dev_url = Some("http://127.0.0.1:5173".parse().expect("fixture Vite URL"));
        config.plugins.0.insert(
            "updater".into(),
            serde_json::json!({
                "endpoints": [format!("{}/stable.json", self.options.origin)],
                "pubkey": if self.signing_key_present() { self.options.public_key.as_str() } else { "" },
                "dangerousInsecureTransportProtocol": true,
                "windows": {"installMode": "passive"},
            }),
        );
        // WebView cookies/storage cannot cross fixture runs or touch a real profile.
        for window in &mut config.app.windows {
            window.data_directory = Some(self.options.root.join("webview"));
            window.visible = false;
        }
    }

    pub fn attach_lifecycle(
        &self,
        teardown: Teardown,
        child: Arc<Mutex<Option<Child>>>,
        shutdown_requested: Arc<AtomicBool>,
    ) {
        *self.teardown.lock().expect("fixture teardown") = Some(teardown);
        *self.child.lock().expect("fixture child") = Some(child);
        *self
            .shutdown_requested
            .lock()
            .expect("fixture shutdown flag") = Some(shutdown_requested);
    }

    pub fn artifact_url(&self) -> reqwest::Url {
        format!("{}/artifact.bin", self.options.origin)
            .parse()
            .expect("fixture artifact URL")
    }

    pub fn beacon_url(&self) -> String {
        format!("{}/beacon.txt", self.options.origin)
    }

    pub fn bootstrap_script(&self) -> String {
        let scenario = serde_json::to_string(&self.options.scenario).expect("scenario JSON");
        let origin = serde_json::to_string(&self.options.origin).expect("origin JSON");
        format!(
            "import('/e2e/fixtures/native_update_driver.ts').then(m => m.run({scenario}, {origin}));"
        )
    }

    fn persist_terminal(&self, event: TerminalEvent) {
        let mut terminal = self.terminal.lock().expect("fixture terminal");
        terminal.push(event);
        std::fs::write(
            self.options.root.join("terminal.json"),
            serde_json::to_vec(&*terminal).expect("terminal JSON"),
        )
        .expect("write native terminal evidence");
    }

    pub fn record_install(
        &self,
        version: &str,
        choice: ConsentChoice,
        bytes: &[u8],
    ) -> Result<(), ErrorCode> {
        self.persist_terminal(TerminalEvent {
            event: "install",
            version: version.into(),
            choice: match choice {
                ConsentChoice::InstallOnQuit => "install_on_quit",
                ConsentChoice::RestartAndInstall => "install_now",
            }
            .into(),
            sha256: format!("{:x}", Sha256::digest(bytes)),
        });
        if self.options.scenario == "install_failure" {
            Err(ErrorCode::InstallFailed)
        } else {
            Ok(())
        }
    }

    pub fn record_restart(&self) {
        self.persist_terminal(TerminalEvent {
            event: "restart",
            version: String::new(),
            choice: String::new(),
            sha256: String::new(),
        });
    }

    fn shutdown(&self) {
        let teardown = self.teardown.lock().expect("fixture teardown").clone();
        if let Some(teardown) = teardown {
            teardown();
        }
    }

    fn stats(&self) -> serde_json::Value {
        let terminal = self.terminal.lock().expect("fixture terminal").clone();
        serde_json::json!({"terminal": terminal})
    }
}

#[tauri::command]
pub async fn control<R: Runtime>(
    _app: tauri::AppHandle<R>,
    state: tauri::State<'_, Arc<NativeFixture>>,
    action: String,
) -> Result<serde_json::Value, String> {
    let fixture = Arc::clone(state.inner());
    match action.as_str() {
        "stats" => Ok(fixture.stats()),
        "shutdown" => tauri::async_runtime::spawn_blocking(move || {
            fixture.shutdown();
            fixture.stats()
        })
        .await
        .map_err(|_| "fixture_shutdown_failed".into()),
        "restart_backend" => {
            let slot = fixture
                .child
                .lock()
                .expect("fixture child")
                .clone()
                .ok_or("fixture_child_missing")?;
            let mut child = slot.lock().expect("child slot");
            child
                .as_mut()
                .ok_or("fixture_child_missing")?
                .kill()
                .map_err(|_| "fixture_child_kill_failed")?;
            Ok(serde_json::Value::Null)
        }
        "crash_after_consent" if fixture.options.scenario == "consent_crash" => {
            // A real process termination, without the shutdown policy event.
            // Reap our passive child first so this crash fixture owns no orphan.
            if let Some(shutdown) = fixture
                .shutdown_requested
                .lock()
                .expect("fixture shutdown flag")
                .as_ref()
            {
                shutdown.store(true, Ordering::SeqCst);
            }
            if let Some(slot) = fixture.child.lock().expect("fixture child").clone() {
                if let Some(mut child) = slot.lock().expect("child slot").take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
            std::fs::write(fixture.options.root.join("crashed"), b"consent_crash")
                .map_err(|_| "fixture_crash_marker_failed")?;
            std::process::exit(86);
        }
        _ => Err("unknown_fixture_action".into()),
    }
}

#[tauri::command]
pub async fn report<R: Runtime>(
    app: tauri::AppHandle<R>,
    state: tauri::State<'_, Arc<NativeFixture>>,
    passed: bool,
    detail: String,
) -> Result<(), String> {
    let fixture = Arc::clone(state.inner());
    tauri::async_runtime::spawn_blocking(move || {
        fixture.shutdown();
        let result = serde_json::json!({
            "passed": passed,
            "scenario": fixture.options.scenario,
            "detail": detail.chars().take(2000).collect::<String>(),
        });
        std::fs::write(fixture.options.root.join("result.json"), result.to_string())
            .expect("write native fixture result");
        app.exit(if passed { 0 } else { 1 });
    });
    Ok(())
}
