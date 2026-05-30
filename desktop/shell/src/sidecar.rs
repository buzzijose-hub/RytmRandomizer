//! Python sidecar supervision.
//!
//! Spawns `python -m rytm_randomizer.cockpit` as a child process, restarts it
//! on crash with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 16s,
//! resets after 60s of clean uptime), and shuts it down cleanly on window
//! close (SIGTERM, then SIGKILL after 5s).

use std::env;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::Duration;

/// Initial backoff before restart, doubles each consecutive failure.
const INITIAL_BACKOFF_SECS: u64 = 1;
/// Cap on the backoff interval.
const MAX_BACKOFF_SECS: u64 = 16;
/// Clean-uptime threshold after which the failure counter resets to zero.
pub const BACKOFF_RESET_SECS: u64 = 60;
/// Grace period between SIGTERM and SIGKILL on shutdown.
pub const SHUTDOWN_GRACE_SECS: u64 = 5;
/// Environment variable consumed by the Python cockpit sidecar for token handoff.
pub const TOKEN_FILE_ENV_VAR: &str = "RYTM_RAND_WS_TOKEN_FILE";
/// Browser storage key consumed by the cockpit WebSocket client.
pub const TOKEN_STORAGE_KEY: &str = "rytm-rand-ws-token";
/// Window property consumed by the cockpit WebSocket client.
pub const TOKEN_WINDOW_PROPERTY: &str = "__RYTM_RAND_WS_TOKEN__";
const DEFAULT_TOKEN_DIR: &str = "RytmRandomizer";
const DEFAULT_TOKEN_FILE: &str = "cockpit-ws-token.txt";

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

/// JavaScript injected into the WebView once the Python sidecar writes its token.
pub fn token_bootstrap_script(token: &str) -> String {
    let token_json = serde_json::to_string(token).expect("serialize ws token");
    let key_json = serde_json::to_string(TOKEN_STORAGE_KEY).expect("serialize token key");
    format!(
        "(() => {{ window.{TOKEN_WINDOW_PROPERTY} = {token_json}; try {{ window.localStorage.setItem({key_json}, {token_json}); }} catch (_err) {{}} }})();"
    )
}

/// Build the sidecar command so tests can inspect env propagation without spawning.
pub fn sidecar_command(python_bin: &str, token_file: &Path) -> Command {
    let mut command = Command::new(python_bin);
    command
        .args(["-m", "rytm_randomizer.cockpit"])
        .env(TOKEN_FILE_ENV_VAR, token_file)
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit());
    command
}

/// Spawn the Python sidecar process and return the handle. Caller owns the
/// child and is responsible for tearing it down via [`shutdown_child`].
pub fn spawn_sidecar(python_bin: &str, token_file: &Path) -> std::io::Result<Child> {
    log::info!("spawning sidecar: {python_bin} -m rytm_randomizer.cockpit");
    if let Some(parent) = token_file.parent() {
        fs::create_dir_all(parent)?;
    }
    sidecar_command(python_bin, token_file).spawn()
}

/// Send a graceful shutdown to the child, wait up to [`SHUTDOWN_GRACE_SECS`],
/// then SIGKILL if it is still alive.
pub fn shutdown_child(child: &mut Child) {
    log::info!("shutting down sidecar pid={}", child.id());
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
    fn sidecar_command_sets_token_file_env() {
        let command = sidecar_command("python", std::path::Path::new("C:/tmp/ws-token.txt"));
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
    fn token_bootstrap_script_sets_window_property_and_storage_key() {
        let script = token_bootstrap_script("tok'en\\value");
        assert!(script.contains("__RYTM_RAND_WS_TOKEN__"));
        assert!(script.contains("rytm-rand-ws-token"));
        assert!(script.contains("localStorage.setItem"));
        assert!(script.contains("tok'en\\\\value"));
    }
}
