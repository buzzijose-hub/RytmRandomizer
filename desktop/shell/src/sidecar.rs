//! Python sidecar supervision.
//!
//! Spawns the cockpit sidecar — preferring the bundled one-file
//! `rytm-sidecar` binary produced by `scripts/build_sidecar_binary.py`
//! when it is present in the Tauri resources, falling back to a PATH
//! `python -m rytm_randomizer.cockpit` for dev checkouts — restarts it
//! on crash with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at
//! 16s, resets after 60s of clean uptime), and shuts it down cleanly on
//! window close (stdin shutdown sentinel on every OS, plus SIGTERM on
//! unix, then a hard kill after 5s).

use std::env;
use std::fs;
use std::io;
use std::io::Write as _;
use std::net::TcpListener;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::Duration;

/// Initial backoff before restart, doubles each consecutive failure.
const INITIAL_BACKOFF_SECS: u64 = 1;
/// Cap on the backoff interval.
const MAX_BACKOFF_SECS: u64 = 16;
/// Clean-uptime threshold after which the failure counter resets to zero.
pub const BACKOFF_RESET_SECS: u64 = 60;
/// Grace period between the graceful-shutdown request and the hard kill.
pub const SHUTDOWN_GRACE_SECS: u64 = 5;
/// Environment variable consumed by the Python cockpit sidecar for token handoff.
pub const TOKEN_FILE_ENV_VAR: &str = "RYTM_RAND_WS_TOKEN_FILE";
/// Environment variable consumed by the Python cockpit sidecar for the WS port.
pub const PORT_ENV_VAR: &str = "RYTM_RAND_WS_PORT";
/// Operator override pointing at a specific bundled sidecar binary.
pub const SIDECAR_BIN_ENV_VAR: &str = "RYTM_RAND_SIDECAR_BIN";
/// Line written to the sidecar's stdin to request a graceful shutdown.
///
/// Must match `SHUTDOWN_SENTINEL` in `scripts/build_sidecar_binary.py` —
/// `tests/test_launch_smoke.py` pins the two strings in lockstep. The
/// stdin channel is the cross-platform half of shutdown: Windows has no
/// SIGTERM, but every OS can close a pipe.
pub const SHUTDOWN_SENTINEL: &str = "RYTM_SIDECAR_SHUTDOWN";
/// Browser storage key consumed by the cockpit WebSocket client.
pub const TOKEN_STORAGE_KEY: &str = "rytm-rand-ws-token";
/// Window property consumed by the cockpit WebSocket client.
pub const TOKEN_WINDOW_PROPERTY: &str = "__RYTM_RAND_WS_TOKEN__";
/// Browser storage key the cockpit WebSocket client may read the port from.
pub const PORT_STORAGE_KEY: &str = "rytm-rand-ws-port";
/// Window property the cockpit WebSocket client may read the port from.
pub const PORT_WINDOW_PROPERTY: &str = "__RYTM_RAND_WS_PORT__";
/// The sidecar's default WS port (mirrors `_DEFAULT_PORT` in `cockpit/__main__.py`).
pub const DEFAULT_WS_PORT: u16 = 4317;
/// Consecutive spawn failures before the shell surfaces an error dialog.
pub const SPAWN_FAILURE_DIALOG_THRESHOLD: u32 = 3;
/// Basename (without platform suffix) of the bundled sidecar binary.
pub const SIDECAR_BINARY_STEM: &str = "rytm-sidecar";
/// Subdirectory (under the exe dir / resource dir) holding the bundled binary.
pub const SIDECAR_BINARY_DIR: &str = "binaries";
/// Interpreter used for the dev fallback launch.
pub const PYTHON_BIN: &str = "python";
const DEFAULT_TOKEN_DIR: &str = "RytmRandomizer";
const DEFAULT_TOKEN_FILE: &str = "cockpit-ws-token.txt";

/// How the sidecar process is launched.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SidecarLaunch {
    /// A bundled one-file binary (production double-click path).
    Bundled(PathBuf),
    /// `python -m rytm_randomizer.cockpit` from PATH (dev fallback).
    DevPython(String),
}

impl SidecarLaunch {
    /// Human-readable description for logs and the spawn-failure dialog.
    pub fn describe(&self) -> String {
        match self {
            SidecarLaunch::Bundled(path) => format!("bundled sidecar `{}`", path.display()),
            SidecarLaunch::DevPython(python) => {
                format!("`{python} -m rytm_randomizer.cockpit` (dev fallback)")
            }
        }
    }
}

/// Platform filename of the bundled sidecar binary.
pub fn sidecar_binary_name() -> String {
    if cfg!(windows) {
        format!("{SIDECAR_BINARY_STEM}.exe")
    } else {
        SIDECAR_BINARY_STEM.to_string()
    }
}

/// Candidate paths for the bundled sidecar binary, highest priority first.
///
/// The installers workflow drops the binary into `desktop/shell/binaries/`,
/// which `tauri.conf.json` bundles via the `bundle.resources` glob. At
/// runtime that lands under the app's resource dir (`Contents/Resources`
/// on macOS, the install dir on Windows, `lib/<app>/resources` on Linux);
/// the exe-adjacent candidates cover `externalBin`-style layouts and
/// hand-assembled portable folders.
pub fn bundled_sidecar_candidates(
    exe_dir: Option<PathBuf>,
    resource_dir: Option<PathBuf>,
) -> Vec<PathBuf> {
    let name = sidecar_binary_name();
    let mut candidates = Vec::new();
    if let Some(dir) = resource_dir {
        candidates.push(dir.join(SIDECAR_BINARY_DIR).join(&name));
        candidates.push(dir.join(&name));
    }
    if let Some(dir) = exe_dir {
        candidates.push(dir.join(SIDECAR_BINARY_DIR).join(&name));
        candidates.push(dir.join(&name));
    }
    candidates
}

/// Pick the launch mode: env override, first existing bundled candidate,
/// then the PATH-python dev fallback.
///
/// Pure with respect to the process environment (the override is passed
/// in) so the priority order is unit-testable.
pub fn resolve_sidecar_launch(
    env_override: Option<&str>,
    candidates: &[PathBuf],
) -> SidecarLaunch {
    if let Some(path) = env_override {
        let trimmed = path.trim();
        if !trimmed.is_empty() {
            return SidecarLaunch::Bundled(PathBuf::from(trimmed));
        }
    }
    for candidate in candidates {
        if candidate.is_file() {
            return SidecarLaunch::Bundled(candidate.clone());
        }
    }
    SidecarLaunch::DevPython(PYTHON_BIN.to_string())
}

/// True when loopback `port` can be bound right now.
fn port_is_free(port: u16) -> bool {
    TcpListener::bind(("127.0.0.1", port)).is_ok()
}

/// Ask the OS for a free ephemeral loopback port.
fn free_ephemeral_port() -> Option<u16> {
    TcpListener::bind(("127.0.0.1", 0))
        .ok()
        .and_then(|listener| listener.local_addr().ok())
        .map(|addr| addr.port())
}

/// Resolve the WS port to run this launch on.
///
/// Priority: a valid operator `RYTM_RAND_WS_PORT` override (passed in),
/// then the default 4317 when free, then an OS-assigned free ephemeral
/// port. A busy 4317 therefore degrades to "different port" instead of
/// "sidecar crash-loops on EADDRINUSE and the launch bricks". The chosen
/// port is exported to both the sidecar (env) and the webview (bootstrap
/// script) so all three parties agree.
pub fn pick_ws_port(env_override: Option<&str>) -> u16 {
    if let Some(raw) = env_override {
        if let Ok(port) = raw.trim().parse::<u16>() {
            if port != 0 {
                return port;
            }
        }
    }
    if port_is_free(DEFAULT_WS_PORT) {
        return DEFAULT_WS_PORT;
    }
    free_ephemeral_port().unwrap_or(DEFAULT_WS_PORT)
}

/// Compute the next restart delay given a non-negative consecutive-failure
/// count.
///
/// `failures == 0` returns the initial backoff (1s); each additional failure
/// doubles the delay until the cap is reached. The function is pure so the
/// table is unit-testable without spawning real processes.
pub fn backoff_delay(failures: u32) -> Duration {
    let multiplier = 1_u64.checked_shl(failures).unwrap_or(u64::MAX);
    let raw = INITIAL_BACKOFF_SECS.saturating_mul(multiplier);
    Duration::from_secs(raw.min(MAX_BACKOFF_SECS))
}

/// Resolve the sidecar token handoff path. Operators may override the path through
/// `RYTM_RAND_WS_TOKEN_FILE`; otherwise the shell uses a stable per-user temp path.
pub fn resolve_token_file_path() -> PathBuf {
    if let Ok(path) = env::var(TOKEN_FILE_ENV_VAR) {
        if !path.trim().is_empty() {
            return PathBuf::from(path);
        }
    }
    let base = env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(env::temp_dir);
    base.join(DEFAULT_TOKEN_DIR).join(DEFAULT_TOKEN_FILE)
}

/// Remove a stale token before launching a fresh sidecar. Missing files are fine.
pub fn clear_token_file(path: &Path) -> io::Result<()> {
    match fs::remove_file(path) {
        Ok(()) => Ok(()),
        Err(err) if err.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(err) => Err(err),
    }
}

/// Read and trim the sidecar token file. Missing or whitespace-only files are "not ready".
pub fn read_token_file(path: &Path) -> io::Result<Option<String>> {
    match fs::read_to_string(path) {
        Ok(contents) => {
            let token = contents.trim();
            if token.is_empty() {
                Ok(None)
            } else {
                Ok(Some(token.to_string()))
            }
        }
        Err(err) if err.kind() == io::ErrorKind::NotFound => Ok(None),
        Err(err) => Err(err),
    }
}

/// JavaScript injected into the WebView once the Python sidecar writes its
/// token: hands over both the handshake token and the per-launch WS port.
pub fn token_bootstrap_script(token: &str, port: u16) -> String {
    let token_json = serde_json::to_string(token).expect("serialize ws token");
    let key_json = serde_json::to_string(TOKEN_STORAGE_KEY).expect("serialize token key");
    let port_json = serde_json::to_string(&port.to_string()).expect("serialize ws port");
    let port_key_json = serde_json::to_string(PORT_STORAGE_KEY).expect("serialize port key");
    format!(
        "(() => {{ window.{TOKEN_WINDOW_PROPERTY} = {token_json}; window.{PORT_WINDOW_PROPERTY} = {port_json}; try {{ window.localStorage.setItem({key_json}, {token_json}); window.localStorage.setItem({port_key_json}, {port_json}); }} catch (_err) {{}} }})();"
    )
}

/// Build the sidecar command so tests can inspect env propagation without spawning.
///
/// stdin is piped: it is the cross-platform graceful-shutdown channel
/// ([`shutdown_child`] writes [`SHUTDOWN_SENTINEL`] then closes the pipe).
pub fn sidecar_command(launch: &SidecarLaunch, token_file: &Path, port: u16) -> Command {
    let mut command = match launch {
        SidecarLaunch::Bundled(path) => Command::new(path),
        SidecarLaunch::DevPython(python) => {
            let mut dev = Command::new(python);
            dev.args(["-m", "rytm_randomizer.cockpit"]);
            dev
        }
    };
    command
        .env(TOKEN_FILE_ENV_VAR, token_file)
        .env(PORT_ENV_VAR, port.to_string())
        .stdin(Stdio::piped())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit());
    command
}

/// Spawn the sidecar process and return the handle. Caller owns the
/// child and is responsible for tearing it down via [`shutdown_child`].
pub fn spawn_sidecar(launch: &SidecarLaunch, token_file: &Path, port: u16) -> io::Result<Child> {
    log::info!("spawning sidecar on port {port}: {}", launch.describe());
    if let Some(parent) = token_file.parent() {
        fs::create_dir_all(parent)?;
    }
    sidecar_command(launch, token_file, port).spawn()
}

/// Request a graceful shutdown on every OS: write the stdin sentinel and
/// close the pipe (EOF). The bundled binary's entry stub watches stdin and
/// raises SIGINT in-process; a dev `python -m` sidecar ignores stdin, which
/// is fine — unix gets SIGTERM next and Windows dev falls through to the
/// timed kill.
fn request_graceful_shutdown(child: &mut Child) {
    if let Some(mut stdin) = child.stdin.take() {
        let _ = writeln!(stdin, "{SHUTDOWN_SENTINEL}");
        let _ = stdin.flush();
        // Dropping stdin closes the pipe — EOF is the second trigger the
        // bundled entry stub honours, covering a sentinel lost mid-write.
    }
}

/// Send a graceful shutdown to the child (stdin sentinel everywhere,
/// SIGTERM additionally on unix), wait up to [`SHUTDOWN_GRACE_SECS`],
/// then kill if it is still alive.
pub fn shutdown_child(child: &mut Child) {
    log::info!("shutting down sidecar pid={}", child.id());
    request_graceful_shutdown(child);
    #[cfg(unix)]
    {
        use nix::sys::signal::{kill, Signal};
        use nix::unistd::Pid;
        let pid = Pid::from_raw(child.id() as i32);
        let _ = kill(pid, Signal::SIGTERM);
    }
    let deadline = std::time::Instant::now() + Duration::from_secs(SHUTDOWN_GRACE_SECS);
    while std::time::Instant::now() < deadline {
        if let Ok(Some(_)) = child.try_wait() {
            return;
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    let _ = child.kill();
    let _ = child.wait();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn backoff_starts_at_one_second() {
        assert_eq!(backoff_delay(0), Duration::from_secs(1));
    }

    #[test]
    fn backoff_doubles_each_failure() {
        assert_eq!(backoff_delay(1), Duration::from_secs(2));
        assert_eq!(backoff_delay(2), Duration::from_secs(4));
        assert_eq!(backoff_delay(3), Duration::from_secs(8));
        assert_eq!(backoff_delay(4), Duration::from_secs(16));
    }

    #[test]
    fn backoff_caps_at_sixteen_seconds() {
        assert_eq!(backoff_delay(5), Duration::from_secs(16));
        assert_eq!(backoff_delay(10), Duration::from_secs(16));
        assert_eq!(backoff_delay(u32::MAX), Duration::from_secs(16));
    }

    #[test]
    fn shutdown_grace_is_five_seconds() {
        assert_eq!(SHUTDOWN_GRACE_SECS, 5);
    }

    #[test]
    fn backoff_reset_window_is_one_minute() {
        assert_eq!(BACKOFF_RESET_SECS, 60);
    }

    #[test]
    fn resolve_token_file_path_honors_env_override() {
        let prior = std::env::var_os(TOKEN_FILE_ENV_VAR);
        std::env::set_var(TOKEN_FILE_ENV_VAR, "C:/tmp/override-token.txt");
        assert_eq!(
            resolve_token_file_path(),
            std::path::PathBuf::from("C:/tmp/override-token.txt")
        );
        match prior {
            Some(value) => std::env::set_var(TOKEN_FILE_ENV_VAR, value),
            None => std::env::remove_var(TOKEN_FILE_ENV_VAR),
        }
    }

    #[test]
    fn sidecar_command_sets_token_file_and_port_env() {
        let launch = SidecarLaunch::DevPython(PYTHON_BIN.to_string());
        let command = sidecar_command(&launch, std::path::Path::new("C:/tmp/ws-token.txt"), 4444);
        let envs: Vec<_> = command
            .get_envs()
            .map(|(key, value)| {
                (
                    key.to_string_lossy().to_string(),
                    value.map(|v| v.to_string_lossy().to_string()),
                )
            })
            .collect();
        assert!(envs.contains(&(
            TOKEN_FILE_ENV_VAR.to_string(),
            Some("C:/tmp/ws-token.txt".to_string()),
        )));
        assert!(envs.contains(&(PORT_ENV_VAR.to_string(), Some("4444".to_string()))));
    }

    #[test]
    fn sidecar_command_dev_fallback_runs_module_entry() {
        let launch = SidecarLaunch::DevPython("python".to_string());
        let command = sidecar_command(&launch, std::path::Path::new("/tmp/tok"), 4317);
        let args: Vec<String> = command
            .get_args()
            .map(|a| a.to_string_lossy().to_string())
            .collect();
        assert_eq!(args, vec!["-m", "rytm_randomizer.cockpit"]);
    }

    #[test]
    fn sidecar_command_bundled_has_no_module_args() {
        let launch = SidecarLaunch::Bundled(PathBuf::from("/opt/app/binaries/rytm-sidecar"));
        let command = sidecar_command(&launch, std::path::Path::new("/tmp/tok"), 4317);
        assert_eq!(command.get_args().count(), 0);
    }

    #[test]
    fn resolve_sidecar_launch_prefers_env_override() {
        let launch = resolve_sidecar_launch(Some("/custom/rytm-sidecar"), &[]);
        assert_eq!(launch, SidecarLaunch::Bundled(PathBuf::from("/custom/rytm-sidecar")));
    }

    #[test]
    fn resolve_sidecar_launch_ignores_blank_override_and_missing_candidates() {
        let launch = resolve_sidecar_launch(Some("   "), &[PathBuf::from("/no/such/file")]);
        assert_eq!(launch, SidecarLaunch::DevPython(PYTHON_BIN.to_string()));
    }

    #[test]
    fn resolve_sidecar_launch_picks_first_existing_candidate() {
        let dir =
            std::env::temp_dir().join(format!("rytm-rand-sidecar-test-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).expect("create temp dir");
        let existing = dir.join(sidecar_binary_name());
        std::fs::write(&existing, b"stub").expect("write stub binary");
        let missing = dir.join("missing").join(sidecar_binary_name());
        let launch = resolve_sidecar_launch(None, &[missing, existing.clone()]);
        assert_eq!(launch, SidecarLaunch::Bundled(existing));
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn bundled_candidates_cover_resource_and_exe_dirs() {
        let candidates = bundled_sidecar_candidates(
            Some(PathBuf::from("/exe")),
            Some(PathBuf::from("/resources")),
        );
        let name = sidecar_binary_name();
        assert_eq!(
            candidates,
            vec![
                PathBuf::from("/resources").join(SIDECAR_BINARY_DIR).join(&name),
                PathBuf::from("/resources").join(&name),
                PathBuf::from("/exe").join(SIDECAR_BINARY_DIR).join(&name),
                PathBuf::from("/exe").join(&name),
            ]
        );
    }

    #[test]
    fn pick_ws_port_honors_valid_override() {
        assert_eq!(pick_ws_port(Some("5005")), 5005);
    }

    #[test]
    fn pick_ws_port_rejects_invalid_override_and_returns_bindable_port() {
        let port = pick_ws_port(Some("not-a-port"));
        assert_ne!(port, 0);
        // The chosen port must be bindable right now (default free, or a
        // fresh ephemeral port when the default is occupied).
        assert!(TcpListener::bind(("127.0.0.1", port)).is_ok());
    }

    #[test]
    fn pick_ws_port_falls_past_occupied_default() {
        // Hold the default port so the picker must find another one.
        match TcpListener::bind(("127.0.0.1", DEFAULT_WS_PORT)) {
            Ok(_guard) => {
                let port = pick_ws_port(None);
                assert_ne!(port, DEFAULT_WS_PORT);
                assert_ne!(port, 0);
            }
            Err(_) => {
                // Something else already owns 4317 on this machine; the
                // picker must still avoid it.
                assert_ne!(pick_ws_port(None), DEFAULT_WS_PORT);
            }
        }
    }

    #[test]
    fn read_token_file_trims_and_ignores_missing_or_empty() {
        let dir =
            std::env::temp_dir().join(format!("rytm-randomizer-token-test-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).expect("create temp token dir");
        let missing = dir.join("missing.txt");
        assert_eq!(read_token_file(&missing).expect("read missing token"), None);

        let empty = dir.join("empty.txt");
        std::fs::write(&empty, "   \n").expect("write empty token");
        assert_eq!(read_token_file(&empty).expect("read empty token"), None);

        let token = dir.join("token.txt");
        std::fs::write(&token, "  abc123  \n").expect("write token");
        assert_eq!(
            read_token_file(&token).expect("read token"),
            Some("abc123".to_string())
        );

        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn token_bootstrap_script_sets_window_properties_and_storage_keys() {
        let script = token_bootstrap_script("tok'en\\value", 4919);
        assert!(script.contains("__RYTM_RAND_WS_TOKEN__"));
        assert!(script.contains("rytm-rand-ws-token"));
        assert!(script.contains("__RYTM_RAND_WS_PORT__"));
        assert!(script.contains("rytm-rand-ws-port"));
        assert!(script.contains("localStorage.setItem"));
        assert!(script.contains("tok'en\\\\value"));
        assert!(script.contains("\"4919\""));
    }

    #[test]
    fn shutdown_sentinel_matches_build_script_contract() {
        // Lockstep with scripts/build_sidecar_binary.py::SHUTDOWN_SENTINEL
        // (also pinned from the Python side in tests/test_launch_smoke.py).
        assert_eq!(SHUTDOWN_SENTINEL, "RYTM_SIDECAR_SHUTDOWN");
    }
}
