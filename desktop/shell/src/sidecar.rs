//! Python sidecar supervision.
//!
//! Spawns `python -m rytm_randomizer.cockpit` as a child process, restarts it
//! on crash with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 16s,
//! resets after 60s of clean uptime), and shuts it down cleanly on window
//! close (SIGTERM, then SIGKILL after 5s).

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

/// Spawn the Python sidecar process and return the handle. Caller owns the
/// child and is responsible for tearing it down via [`shutdown_child`].
pub fn spawn_sidecar(python_bin: &str) -> std::io::Result<Child> {
    log::info!("spawning sidecar: {python_bin} -m rytm_randomizer.cockpit");
    Command::new(python_bin)
        .args(["-m", "rytm_randomizer.cockpit"])
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn()
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
}
