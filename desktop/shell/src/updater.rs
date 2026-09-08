//! The thin I/O driver for the update subsystem.
//!
//! This module is deliberately dumb. Every decision lives in
//! [`crate::update_policy`]; everything here either
//!
//! 1. resolves the §7 environment surface into a [`Config`],
//! 2. hands one [`UpdateEvent`] to [`update_policy::step`], or
//! 3. performs the [`Effect`]s the policy returned and turns their outcomes
//!    back into events.
//!
//! Keeping the driver dumb is what makes the policy exhaustively testable
//! without mocking: the interesting logic never touches a socket. The
//! effect *performers* are behind the [`EffectSink`] trait, so this module's
//! own sequencing (journal-then-emit ordering, beacon fire-and-forget,
//! install-only-after-sidecar-exit) is testable with a recording sink and no
//! network either.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::update_journal::UpdateJournal;
use crate::update_policy::{
    self, Config, ConsentChoice, Effect, ErrorCode, JournalRecord, UpdateEvent, UpdateState,
    UpdateStatePayload,
};

/// Freeze gate. `off` (case-insensitive) disables checks, downloads,
/// installs and the beacon.
pub const UPDATES_ENV_VAR: &str = "RYTM_RAND_UPDATES";
/// Beacon gate. `off` keeps checking but stops reporting.
pub const BEACON_ENV_VAR: &str = "RYTM_RAND_UPDATE_BEACON";
/// Channel override (`stable` / `beta`).
pub const CHANNEL_ENV_VAR: &str = "RYTM_RAND_UPDATE_CHANNEL";
/// Manifest base-URL override, for the e2e mock-manifest server.
pub const MANIFEST_URL_ENV_VAR: &str = "RYTM_RAND_UPDATE_MANIFEST_URL";

/// Default channel when the operator has not chosen one.
pub const DEFAULT_CHANNEL: &str = "stable";
/// The only channels this client will fetch.
pub const KNOWN_CHANNELS: &[&str] = &["stable", "beta"];
/// Default manifest base URL (raw manifests on the `releases` branch).
pub const DEFAULT_MANIFEST_BASE_URL: &str =
    "https://raw.githubusercontent.com/buzzijose-hub/RytmRandomizer/releases";

/// The value that turns a gate off. Anything else leaves it on, so a typo
/// fails *safe* for availability and the operator's explicit "off" is the
/// only way to disable checking.
const OFF: &str = "off";

/// Filename stem of the fire-and-forget beacon asset (contract I6).
///
/// A plain GET of a static release asset: no query string, no install id, no
/// headers of ours. The only information it can convey is "some client on
/// `<target>` fetched the `<version>` beacon", which is exactly the
/// coarse-adoption signal spec §6 Tier 0 asks for.
pub fn beacon_asset_name(version: &str, target: &str) -> String {
    format!("beacon-{version}-{target}.txt")
}

/// Whether an env value means "off".
fn is_off(value: Option<&str>) -> bool {
    value.is_some_and(|v| v.trim().eq_ignore_ascii_case(OFF))
}

/// Normalise a channel override; unknown channels fall back to the default
/// rather than fetching an attacker-chosen path segment.
pub fn resolve_channel(raw: Option<&str>) -> String {
    let candidate = raw.unwrap_or("").trim().to_ascii_lowercase();
    if KNOWN_CHANNELS.contains(&candidate.as_str()) {
        candidate
    } else {
        DEFAULT_CHANNEL.to_string()
    }
}

/// Normalise a manifest base URL override.
///
/// Only `https://` is accepted from the environment, with one deliberate
/// exception: `http://127.0.0.1` / `http://localhost`, which is what the
/// Playwright mock-manifest server binds. Anything else falls back to the
/// default, so a stray env var cannot silently downgrade the transport.
pub fn resolve_manifest_base_url(raw: Option<&str>) -> String {
    let candidate = raw.unwrap_or("").trim();
    if candidate.is_empty() {
        return DEFAULT_MANIFEST_BASE_URL.to_string();
    }
    let is_loopback =
        candidate.starts_with("http://127.0.0.1") || candidate.starts_with("http://localhost");
    if candidate.starts_with("https://") || is_loopback {
        candidate.trim_end_matches('/').to_string()
    } else {
        DEFAULT_MANIFEST_BASE_URL.to_string()
    }
}

/// The `<os>-<arch>` target string this build runs on.
pub fn current_target() -> String {
    let os = if cfg!(target_os = "macos") {
        "darwin"
    } else if cfg!(target_os = "windows") {
        "windows"
    } else {
        "linux"
    };
    let arch = if cfg!(target_arch = "aarch64") {
        "aarch64"
    } else {
        "x86_64"
    };
    format!("{os}-{arch}")
}

/// Whether an updater public key is compiled into this build.
///
/// **Operator action item 1 is still open**: no key exists yet, so this is
/// `false` on every build today and the policy is structurally incapable of
/// emitting an install effect (see
/// `update_policy::Config::install_permitted`). When the key lands it is
/// supplied through `tauri.conf.json`'s `plugins.updater.pubkey`, and the
/// build script sets `RYTM_RAND_UPDATER_PUBKEY` so this returns `true`.
pub fn signing_key_present() -> bool {
    option_env!("RYTM_RAND_UPDATER_PUBKEY").is_some_and(|key| !key.trim().is_empty())
}

/// Resolve the whole §7 surface from explicit inputs.
///
/// Pure with respect to the process environment (values are passed in) so
/// the resolution table is unit-testable, matching
/// `sidecar::resolve_sidecar_launch`'s posture.
pub fn resolve_config(
    current_version: &str,
    install_id: &str,
    updates_raw: Option<&str>,
    beacon_raw: Option<&str>,
    channel_raw: Option<&str>,
    key_present: bool,
) -> Config {
    let updates_enabled = !is_off(updates_raw);
    Config {
        current_version: current_version.to_string(),
        target: current_target(),
        install_id: install_id.to_string(),
        updates_enabled,
        // Freeze mode disables the beacon too — a frozen machine phones home
        // about nothing at all.
        beacon_enabled: updates_enabled && !is_off(beacon_raw),
        channel: resolve_channel(channel_raw),
        signing_key_present: key_present,
    }
}

/// Resolve the config from the live process environment.
pub fn resolve_config_from_env(current_version: &str, install_id: &str) -> Config {
    let updates = std::env::var(UPDATES_ENV_VAR).ok();
    let beacon = std::env::var(BEACON_ENV_VAR).ok();
    let channel = std::env::var(CHANNEL_ENV_VAR).ok();
    resolve_config(
        current_version,
        install_id,
        updates.as_deref(),
        beacon.as_deref(),
        channel.as_deref(),
        signing_key_present(),
    )
}

/// The URL of a channel manifest.
pub fn manifest_url(base: &str, channel: &str) -> String {
    format!("{}/{}.json", base.trim_end_matches('/'), channel)
}

/// Milliseconds since the Unix epoch, or 0 if the clock is before it.
///
/// The only clock read in the update subsystem, and it feeds *timestamps*
/// only — never a decision.
pub fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis().min(u128::from(u64::MAX)) as u64)
        .unwrap_or(0)
}

/// Performs the side effects the policy describes.
///
/// Split into a trait so the driver's sequencing is testable with a
/// recording implementation — no HTTP server, no Tauri app, no filesystem.
pub trait EffectSink {
    /// Fetch the manifest for `channel`. Implementations must not block the
    /// UI thread.
    fn fetch_manifest(&self, channel: &str);
    /// Download, verify and stage an artifact.
    fn download_artifact(&self, version: &str, url: &str, signature: &str);
    /// Install an already-staged, already-verified artifact.
    ///
    /// Only ever called after the graceful sidecar shutdown confirmed the
    /// child exited — the policy emits the effect on `SidecarExited` and
    /// nowhere else.
    fn install_staged(&self, version: &str, choice: ConsentChoice);
    /// Fire-and-forget beacon GET. Must never block and never retry.
    fn send_beacon(&self, version: &str, target: &str);
    /// Append one journal row.
    fn journal(&self, record: &JournalRecord);
    /// Emit the contract-I2 `rytm-update-state` event to the webview.
    fn emit_state(&self, payload: &UpdateStatePayload);
}

/// A shared sink is a sink.
///
/// The shell needs the *same* sink object in two places — the driver
/// performs effects through it, and `main` attaches the webview to it and
/// emits the first state directly — so it holds an `Arc`. Forwarding here
/// means neither the shell nor the tests hand-roll that delegation
/// (`Arc<Recorder>` in the test module gets it for free too).
impl<T: EffectSink + ?Sized> EffectSink for Arc<T> {
    fn fetch_manifest(&self, channel: &str) {
        (**self).fetch_manifest(channel);
    }

    fn download_artifact(&self, version: &str, url: &str, signature: &str) {
        (**self).download_artifact(version, url, signature);
    }

    fn install_staged(&self, version: &str, choice: ConsentChoice) {
        (**self).install_staged(version, choice);
    }

    fn send_beacon(&self, version: &str, target: &str) {
        (**self).send_beacon(version, target);
    }

    fn journal(&self, record: &JournalRecord) {
        (**self).journal(record);
    }

    fn emit_state(&self, payload: &UpdateStatePayload) {
        (**self).emit_state(payload);
    }
}

/// Owns the policy state and drives one effect sink.
///
/// Cloneable: the tray thread, the periodic-check thread and the webview
/// command handlers all hand events to the same driver.
#[derive(Clone)]
pub struct Updater<S: EffectSink> {
    config: Arc<Config>,
    state: Arc<Mutex<UpdateState>>,
    sink: Arc<S>,
}

impl<S: EffectSink> Updater<S> {
    /// Build a driver for `config`, starting from the initial state.
    pub fn new(config: Config, sink: S) -> Self {
        let state = UpdateState::initial(&config);
        Self {
            config: Arc::new(config),
            state: Arc::new(Mutex::new(state)),
            sink: Arc::new(sink),
        }
    }

    /// The resolved configuration.
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// A snapshot of the current contract-I2 payload.
    pub fn payload(&self) -> UpdateStatePayload {
        self.locked_state().payload()
    }

    fn locked_state(&self) -> std::sync::MutexGuard<'_, UpdateState> {
        self.state
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
    }

    /// Feed one event through the policy and perform the resulting effects.
    ///
    /// The state lock is released before any effect runs: an effect may
    /// re-enter `handle` (a synchronous sink completing a download inline,
    /// say), and holding the lock across that would deadlock.
    pub fn handle(&self, event: UpdateEvent) {
        let effects = {
            let mut guard = self.locked_state();
            // The state is *moved* through the policy and moved back, never
            // cloned: `UpdateState` may hold a `ConsentToken`, and a clone
            // would be a second authorisation for the same consent. The
            // placeholder swapped in for the duration of the call is a fresh
            // `initial` state, so a panic inside `step` leaves the updater
            // passive rather than holding a stale token.
            let current = std::mem::replace(&mut *guard, UpdateState::initial(&self.config));
            let transition = update_policy::step(current, event, &self.config);
            *guard = transition.state;
            transition.effects
        };
        for effect in &effects {
            self.perform(effect);
        }
    }

    fn perform(&self, effect: &Effect) {
        match effect {
            Effect::FetchManifest { channel } => self.sink.fetch_manifest(channel),
            Effect::DownloadArtifact {
                version,
                url,
                signature,
            } => self.sink.download_artifact(version, url, signature),
            Effect::InstallStagedUpdate(auth) => {
                self.sink.install_staged(auth.version(), auth.choice())
            }
            Effect::SendBeacon { version, target } => self.sink.send_beacon(version, target),
            Effect::Journal(record) => self.sink.journal(record),
            Effect::EmitState(payload) => self.sink.emit_state(payload),
        }
    }
}

/// An [`EffectSink`] half: the journal-writing part, which is the one piece
/// of real I/O that is safe to exercise in unit tests.
///
/// A failed journal write is logged as a typed code and swallowed: losing an
/// observability row must never break an update, and the code is all we have
/// (the underlying `io::Error` would carry an absolute path).
pub fn write_journal_row(journal: &UpdateJournal, record: &JournalRecord) {
    if let Err(code) = journal.append(record, now_ms()) {
        log::warn!(
            "update journal append failed: code={code} event={}",
            record.event
        );
    }
}

/// Filename of the persisted rollout-bucketing identifier.
pub const INSTALL_ID_FILE_NAME: &str = "install-id";

/// Canonical length of a hyphenated UUID.
const UUID_TEXT_LEN: usize = 36;

/// Whether a stored value is a well-formed hyphenated UUID.
///
/// A corrupted or hand-edited file must not silently become a different
/// rollout bucket, so anything that is not exactly the canonical shape is
/// discarded and re-minted rather than trusted.
fn is_well_formed_install_id(value: &str) -> bool {
    if value.len() != UUID_TEXT_LEN {
        return false;
    }
    value.chars().enumerate().all(|(i, c)| {
        if matches!(i, 8 | 13 | 18 | 23) {
            c == '-'
        } else {
            c.is_ascii_hexdigit()
        }
    })
}

/// Mint a fresh UUIDv4-shaped identifier from OS randomness.
///
/// Hand-rolled rather than pulling in the `uuid` crate: the value is never
/// parsed, compared or transmitted — it is hashed into a bucket and nothing
/// else — so a dependency would buy nothing.
///
/// Randomness comes from `/dev/urandom` where it exists. **Windows has no
/// `/dev/urandom`, so the fallback is the only path there** — it is production
/// code on that platform, not a curiosity. The first version mixed `now_ms()`,
/// a stack address and the pid, all three of which are constant for two calls
/// in the same millisecond, so two mints in a loop returned the SAME id. CI
/// caught it on windows-latest with `left == right`.
///
/// A colliding `install_id` is not cosmetic: spec §5 buckets the staged
/// rollout on `sha256(install_id)`, so identical ids mean those installs move
/// as one — the opposite of a staged rollout. The counter below guarantees
/// distinct output within a process regardless of clock resolution.
fn mint_install_id() -> String {
    let mut bytes = [0_u8; 16];
    if std::fs::File::open("/dev/urandom")
        .and_then(|mut f| {
            use std::io::Read as _;
            f.read_exact(&mut bytes)
        })
        .is_err()
    {
        fill_without_urandom(&mut bytes);
    }
    format_uuid_v4(bytes)
}

/// The no-`/dev/urandom` path — i.e. **every Windows install**.
///
/// Split out so it is testable on a machine that HAS `/dev/urandom`. The
/// original was only reachable on Windows, so the collision it contained was
/// invisible to every local run and surfaced only in CI.
fn fill_without_urandom(bytes: &mut [u8; 16]) {
    {
        // Degrade, never panic (the `sidecar` module's posture). The
        // monotonic counter is what makes two same-millisecond mints differ;
        // the clock and pid only spread ids ACROSS processes and machines.
        static MINT_COUNTER: AtomicU64 = AtomicU64::new(0);
        let unique = MINT_COUNTER.fetch_add(1, Ordering::Relaxed);
        let seed = now_ms()
            ^ (&bytes as *const _ as u64)
            ^ u64::from(std::process::id())
            ^ unique.rotate_left(32)
            ^ unique.wrapping_mul(0xD6E8_FEB8_6659_FD93);
        for (i, slot) in bytes.iter_mut().enumerate() {
            let mixed = seed
                .rotate_left((i as u32).wrapping_mul(7))
                .wrapping_mul(0x9E37_79B9_7F4A_7C15)
                .wrapping_add(i as u64);
            *slot = (mixed >> 24) as u8;
        }
    }
}

/// Stamp the version-4 and RFC-4122 variant bits and render the canonical
/// 8-4-4-4-12 form (spec §5).
fn format_uuid_v4(mut bytes: [u8; 16]) -> String {
    bytes[6] = (bytes[6] & 0x0F) | 0x40;
    bytes[8] = (bytes[8] & 0x3F) | 0x80;
    let h = |b: &[u8]| b.iter().map(|x| format!("{x:02x}")).collect::<String>();
    format!(
        "{}-{}-{}-{}-{}",
        h(&bytes[0..4]),
        h(&bytes[4..6]),
        h(&bytes[6..8]),
        h(&bytes[8..10]),
        h(&bytes[10..16])
    )
}

/// Read the install id from `config_dir`, minting and persisting one on
/// first launch (spec §5).
///
/// Stable for the life of the install: the whole point is that a machine
/// does not flap in and out of a staged rollout as the percentage rises. If
/// the file cannot be written the minted value is still returned and used
/// for this process — a machine with an unwritable config dir gets a
/// *random* bucket each launch rather than no updates at all, which is the
/// right way to fail for an availability-shaped feature.
///
/// The value is never transmitted: §6's beacon carries the version and
/// target only.
pub fn resolve_install_id(config_dir: &std::path::Path) -> String {
    let path = config_dir.join(INSTALL_ID_FILE_NAME);
    if let Ok(existing) = std::fs::read_to_string(&path) {
        let trimmed = existing.trim();
        if is_well_formed_install_id(trimmed) {
            return trimmed.to_string();
        }
        log::warn!("discarding a malformed install id; minting a replacement");
    }
    let minted = mint_install_id();
    if std::fs::create_dir_all(config_dir)
        .and_then(|()| std::fs::write(&path, &minted))
        .is_err()
    {
        // No path in the log line — the #224/#238 hygiene standard.
        log::warn!("could not persist the install id; this launch uses a transient one");
    }
    minted
}

/// Map a transport failure onto the typed taxonomy.
///
/// The `io::Error` itself never escapes: its `Display` embeds absolute paths
/// and OS strings, both of which are forbidden in journal rows and log
/// lines that the Connection Doctor surfaces.
pub fn classify_transport_error(kind: std::io::ErrorKind) -> ErrorCode {
    match kind {
        std::io::ErrorKind::NotFound | std::io::ErrorKind::PermissionDenied => {
            ErrorCode::StageWriteFailed
        }
        std::io::ErrorKind::ConnectionRefused
        | std::io::ErrorKind::ConnectionReset
        | std::io::ErrorKind::ConnectionAborted
        | std::io::ErrorKind::NotConnected
        | std::io::ErrorKind::TimedOut => ErrorCode::NetworkUnavailable,
        _ => ErrorCode::DownloadFailed,
    }
}

/// Map an HTTP status onto the typed taxonomy.
pub fn classify_http_status(status: u16) -> Option<ErrorCode> {
    if (200..300).contains(&status) {
        None
    } else {
        Some(ErrorCode::ManifestHttpStatus)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::update_policy::{DetailKey, JournalEvent, StateKind};
    use std::sync::Mutex as StdMutex;

    #[derive(Debug, Default)]
    struct Recorder {
        fetches: StdMutex<Vec<String>>,
        downloads: StdMutex<Vec<String>>,
        installs: StdMutex<Vec<(String, ConsentChoice)>>,
        beacons: StdMutex<Vec<(String, String)>>,
        rows: StdMutex<Vec<JournalEvent>>,
        payloads: StdMutex<Vec<UpdateStatePayload>>,
    }

    // Implemented for the bare type; the blanket `impl EffectSink for
    // Arc<T>` above makes `Arc<Recorder>` a sink too, which is what the
    // driver is handed.
    impl EffectSink for Recorder {
        fn fetch_manifest(&self, channel: &str) {
            self.fetches.lock().unwrap().push(channel.to_string());
        }
        fn download_artifact(&self, version: &str, url: &str, _signature: &str) {
            self.downloads
                .lock()
                .unwrap()
                .push(format!("{version}|{url}"));
        }
        fn install_staged(&self, version: &str, choice: ConsentChoice) {
            self.installs
                .lock()
                .unwrap()
                .push((version.to_string(), choice));
        }
        fn send_beacon(&self, version: &str, target: &str) {
            self.beacons
                .lock()
                .unwrap()
                .push((version.to_string(), target.to_string()));
        }
        fn journal(&self, record: &JournalRecord) {
            self.rows.lock().unwrap().push(record.event);
        }
        fn emit_state(&self, payload: &UpdateStatePayload) {
            self.payloads.lock().unwrap().push(payload.clone());
        }
    }

    fn manifest_body(version: &str) -> String {
        format!(
            r#"{{"schema_version":1,"channel":"stable","version":"{version}","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"rollout_percent":100,
              "platforms":{{"{target}":{{"signature":"c2ln",
                "url":"https://github.com/o/r/releases/download/v{version}/app.tar.gz"}}}}}}"#,
            target = current_target()
        )
    }

    fn driver(config: Config) -> (Updater<Arc<Recorder>>, Arc<Recorder>) {
        let recorder = Arc::new(Recorder::default());
        let updater = Updater::new(config, Arc::clone(&recorder));
        (updater, recorder)
    }

    fn enabled_config() -> Config {
        resolve_config("1.34.0", "install-1", None, None, None, true)
    }

    // -- env surface ----------------------------------------------------

    #[test]
    fn env_var_names_match_the_spec_seven_surface() {
        assert_eq!(UPDATES_ENV_VAR, "RYTM_RAND_UPDATES");
        assert_eq!(BEACON_ENV_VAR, "RYTM_RAND_UPDATE_BEACON");
        assert_eq!(CHANNEL_ENV_VAR, "RYTM_RAND_UPDATE_CHANNEL");
        assert_eq!(MANIFEST_URL_ENV_VAR, "RYTM_RAND_UPDATE_MANIFEST_URL");
    }

    #[test]
    fn updates_off_freezes_and_also_silences_the_beacon() {
        for raw in ["off", "OFF", " Off "] {
            let config = resolve_config("1.34.0", "id", Some(raw), None, None, true);
            assert!(!config.updates_enabled);
            assert!(!config.beacon_enabled);
        }
    }

    #[test]
    fn anything_other_than_off_leaves_updates_enabled() {
        for raw in [None, Some(""), Some("on"), Some("1"), Some("offf")] {
            let config = resolve_config("1.34.0", "id", raw, None, None, true);
            assert!(config.updates_enabled, "raw {raw:?}");
        }
    }

    #[test]
    fn the_beacon_gate_is_independent_of_the_freeze_gate() {
        let config = resolve_config("1.34.0", "id", None, Some("off"), None, true);
        assert!(config.updates_enabled);
        assert!(!config.beacon_enabled);
        let config = resolve_config("1.34.0", "id", None, Some("on"), None, true);
        assert!(config.beacon_enabled);
    }

    #[test]
    fn channel_resolution_normalises_and_falls_back() {
        assert_eq!(resolve_channel(None), "stable");
        assert_eq!(resolve_channel(Some("")), "stable");
        assert_eq!(resolve_channel(Some(" BETA ")), "beta");
        assert_eq!(resolve_channel(Some("stable")), "stable");
        assert_eq!(resolve_channel(Some("../../evil")), "stable");
        assert_eq!(resolve_channel(Some("nightly")), "stable");
    }

    #[test]
    fn manifest_base_url_resolution_refuses_a_downgrade() {
        assert_eq!(resolve_manifest_base_url(None), DEFAULT_MANIFEST_BASE_URL);
        assert_eq!(
            resolve_manifest_base_url(Some("  ")),
            DEFAULT_MANIFEST_BASE_URL
        );
        assert_eq!(
            resolve_manifest_base_url(Some("http://evil.example")),
            DEFAULT_MANIFEST_BASE_URL
        );
        assert_eq!(
            resolve_manifest_base_url(Some("https://example.test/m/")),
            "https://example.test/m"
        );
        // The e2e mock-manifest server is the one permitted plaintext origin.
        assert_eq!(
            resolve_manifest_base_url(Some("http://127.0.0.1:8931/manifests")),
            "http://127.0.0.1:8931/manifests"
        );
        assert_eq!(
            resolve_manifest_base_url(Some("http://localhost:8931")),
            "http://localhost:8931"
        );
    }

    #[test]
    fn manifest_url_appends_the_channel_json() {
        assert_eq!(
            manifest_url("https://example.test/m", "beta"),
            "https://example.test/m/beta.json"
        );
        assert_eq!(
            manifest_url("https://example.test/m/", "stable"),
            "https://example.test/m/stable.json"
        );
    }

    #[test]
    fn the_current_target_is_an_os_dash_arch_pair() {
        let target = current_target();
        let (os, arch) = target.split_once('-').expect("os-arch");
        assert!(["darwin", "windows", "linux"].contains(&os));
        assert!(["aarch64", "x86_64"].contains(&arch));
    }

    #[test]
    fn resolve_config_from_env_matches_the_explicit_resolver() {
        let from_env = resolve_config_from_env("1.34.0", "install-1");
        assert_eq!(from_env.current_version, "1.34.0");
        assert_eq!(from_env.install_id, "install-1");
        assert_eq!(from_env.target, current_target());
        assert_eq!(from_env.signing_key_present, signing_key_present());
    }

    #[test]
    fn no_compiled_in_key_means_check_and_notify_only() {
        // Operator action item 1 is open: no key is compiled in today, so
        // this build cannot install anything at all.
        assert!(!signing_key_present());
        assert!(!resolve_config_from_env("1.34.0", "id").install_permitted());
    }

    #[test]
    fn now_ms_is_after_the_epoch() {
        assert!(now_ms() > 1_600_000_000_000);
    }

    // -- beacon ---------------------------------------------------------

    #[test]
    fn the_beacon_asset_name_carries_no_identifying_data() {
        let name = beacon_asset_name("1.35.0", "darwin-aarch64");
        assert_eq!(name, "beacon-1.35.0-darwin-aarch64.txt");
        assert!(!name.contains('?'), "no query string, so no install id");
        assert!(!name.contains('='));
    }

    // -- error classification --------------------------------------------

    #[test]
    fn transport_errors_map_onto_typed_codes() {
        use std::io::ErrorKind;
        assert_eq!(
            classify_transport_error(ErrorKind::TimedOut),
            ErrorCode::NetworkUnavailable
        );
        assert_eq!(
            classify_transport_error(ErrorKind::ConnectionRefused),
            ErrorCode::NetworkUnavailable
        );
        assert_eq!(
            classify_transport_error(ErrorKind::ConnectionReset),
            ErrorCode::NetworkUnavailable
        );
        assert_eq!(
            classify_transport_error(ErrorKind::ConnectionAborted),
            ErrorCode::NetworkUnavailable
        );
        assert_eq!(
            classify_transport_error(ErrorKind::NotConnected),
            ErrorCode::NetworkUnavailable
        );
        assert_eq!(
            classify_transport_error(ErrorKind::NotFound),
            ErrorCode::StageWriteFailed
        );
        assert_eq!(
            classify_transport_error(ErrorKind::PermissionDenied),
            ErrorCode::StageWriteFailed
        );
        assert_eq!(
            classify_transport_error(ErrorKind::InvalidData),
            ErrorCode::DownloadFailed
        );
    }

    #[test]
    fn http_statuses_map_onto_typed_codes() {
        assert_eq!(classify_http_status(200), None);
        assert_eq!(classify_http_status(299), None);
        assert_eq!(
            classify_http_status(404),
            Some(ErrorCode::ManifestHttpStatus)
        );
        assert_eq!(
            classify_http_status(500),
            Some(ErrorCode::ManifestHttpStatus)
        );
        assert_eq!(
            classify_http_status(199),
            Some(ErrorCode::ManifestHttpStatus)
        );
        assert_eq!(
            classify_http_status(302),
            Some(ErrorCode::ManifestHttpStatus)
        );
    }

    // -- driver sequencing ------------------------------------------------

    #[test]
    fn a_check_fetches_the_configured_channel_and_emits_state() {
        let mut config = enabled_config();
        config.channel = "beta".to_string();
        let (updater, recorder) = driver(config);
        updater.handle(UpdateEvent::CheckRequested);
        assert_eq!(recorder.fetches.lock().unwrap().as_slice(), ["beta"]);
        assert_eq!(
            recorder.rows.lock().unwrap().as_slice(),
            [JournalEvent::CheckStarted]
        );
        let payloads = recorder.payloads.lock().unwrap();
        assert_eq!(payloads.last().expect("payload").state, StateKind::Checking);
        assert_eq!(updater.payload().state, StateKind::Checking);
    }

    #[test]
    fn a_frozen_driver_performs_no_network_effect_for_any_event() {
        let config = resolve_config("1.34.0", "id", Some("off"), Some("on"), None, true);
        let (updater, recorder) = driver(config);
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetched {
            body: manifest_body("1.35.0"),
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::ConsentGranted {
            version: "1.35.0".into(),
            choice: ConsentChoice::RestartAndInstall,
        });
        updater.handle(UpdateEvent::SidecarExited);
        assert!(recorder.fetches.lock().unwrap().is_empty());
        assert!(recorder.downloads.lock().unwrap().is_empty());
        assert!(recorder.beacons.lock().unwrap().is_empty());
        assert!(recorder.installs.lock().unwrap().is_empty());
        assert!(recorder
            .rows
            .lock()
            .unwrap()
            .iter()
            .all(|e| *e == JournalEvent::FreezeSuppressed));
        assert_eq!(updater.payload().state, StateKind::Frozen);
    }

    #[test]
    fn the_full_happy_path_installs_only_after_the_sidecar_exits() {
        let (updater, recorder) = driver(enabled_config());
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetched {
            body: manifest_body("1.35.0"),
            duration_ms: 4,
        });
        assert_eq!(recorder.downloads.lock().unwrap().len(), 1);
        updater.handle(UpdateEvent::DownloadStaged {
            version: "1.35.0".into(),
            bytes: 100,
            duration_ms: 50,
        });
        assert_eq!(updater.payload().state, StateKind::Staged);
        updater.handle(UpdateEvent::ConsentGranted {
            version: "1.35.0".into(),
            choice: ConsentChoice::InstallOnQuit,
        });
        // Consent alone installs nothing.
        assert!(recorder.installs.lock().unwrap().is_empty());
        updater.handle(UpdateEvent::SidecarExited);
        assert_eq!(
            recorder.installs.lock().unwrap().as_slice(),
            [("1.35.0".to_string(), ConsentChoice::InstallOnQuit)]
        );
        updater.handle(UpdateEvent::InstallSucceeded {
            version: "1.35.0".into(),
        });
        assert!(recorder
            .rows
            .lock()
            .unwrap()
            .contains(&JournalEvent::InstallOk));
    }

    #[test]
    fn a_quit_with_a_live_sidecar_never_installs() {
        let (updater, recorder) = driver(enabled_config());
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetched {
            body: manifest_body("1.35.0"),
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::DownloadStaged {
            version: "1.35.0".into(),
            bytes: 1,
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::ConsentGranted {
            version: "1.35.0".into(),
            choice: ConsentChoice::RestartAndInstall,
        });
        updater.handle(UpdateEvent::QuitWithoutSidecarExit);
        assert!(recorder.installs.lock().unwrap().is_empty());
        assert_eq!(
            updater.payload().error_code,
            Some(ErrorCode::SidecarStillRunning)
        );
    }

    #[test]
    fn the_beacon_effect_reaches_the_sink_when_enabled() {
        let mut config = enabled_config();
        config.beacon_enabled = true;
        let (updater, recorder) = driver(config);
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetched {
            body: manifest_body("1.35.0"),
            duration_ms: 1,
        });
        let beacons = recorder.beacons.lock().unwrap();
        assert_eq!(beacons.len(), 1);
        assert_eq!(beacons[0], ("1.34.0".to_string(), current_target()));
        drop(beacons);
        updater.handle(UpdateEvent::BeaconCompleted { ok: false });
        assert!(recorder
            .rows
            .lock()
            .unwrap()
            .contains(&JournalEvent::PingFailed));
    }

    #[test]
    fn a_keyless_build_never_reaches_the_install_sink() {
        let mut config = enabled_config();
        config.signing_key_present = false;
        let (updater, recorder) = driver(config);
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetched {
            body: manifest_body("1.35.0"),
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::DownloadStaged {
            version: "1.35.0".into(),
            bytes: 1,
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::ConsentGranted {
            version: "1.35.0".into(),
            choice: ConsentChoice::RestartAndInstall,
        });
        updater.handle(UpdateEvent::SidecarExited);
        assert!(recorder.installs.lock().unwrap().is_empty());
    }

    #[test]
    fn a_manifest_failure_event_reaches_the_journal_with_a_typed_reason() {
        let (updater, _recorder) = driver(enabled_config());
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetchFailed {
            code: ErrorCode::NetworkUnavailable,
        });
        assert_eq!(updater.payload().state, StateKind::Failed);
        assert_eq!(
            updater.payload().error_code,
            Some(ErrorCode::NetworkUnavailable)
        );
    }

    #[test]
    fn download_and_signature_failures_reach_the_sink() {
        let (updater, recorder) = driver(enabled_config());
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetched {
            body: manifest_body("1.35.0"),
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::SignatureRejected {
            version: "1.35.0".into(),
        });
        assert!(recorder
            .rows
            .lock()
            .unwrap()
            .contains(&JournalEvent::SignatureRejected));
        updater.handle(UpdateEvent::DownloadFailed {
            version: "1.35.0".into(),
            code: ErrorCode::StageWriteFailed,
        });
        assert!(recorder
            .rows
            .lock()
            .unwrap()
            .contains(&JournalEvent::StageFailed));
    }

    #[test]
    fn skipping_reaches_the_sink_and_clears_the_chip() {
        let (updater, recorder) = driver(enabled_config());
        updater.handle(UpdateEvent::CheckRequested);
        updater.handle(UpdateEvent::ManifestFetched {
            body: manifest_body("1.35.0"),
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::DownloadStaged {
            version: "1.35.0".into(),
            bytes: 1,
            duration_ms: 1,
        });
        updater.handle(UpdateEvent::SkipRequested {
            version: "1.35.0".into(),
        });
        assert!(recorder
            .rows
            .lock()
            .unwrap()
            .contains(&JournalEvent::SkipRecorded));
        assert_eq!(updater.payload().state, StateKind::Skipped);
    }

    #[test]
    fn install_failure_reaches_the_sink() {
        let (updater, recorder) = driver(enabled_config());
        updater.handle(UpdateEvent::InstallFailed {
            version: "1.35.0".into(),
            code: ErrorCode::InstallFailed,
        });
        assert!(recorder
            .rows
            .lock()
            .unwrap()
            .contains(&JournalEvent::InstallFailed));
    }

    #[test]
    fn the_driver_is_cloneable_and_shares_one_state() {
        let (updater, _recorder) = driver(enabled_config());
        let clone = updater.clone();
        clone.handle(UpdateEvent::CheckRequested);
        assert_eq!(updater.payload().state, StateKind::Checking);
        assert_eq!(updater.config().channel, "stable");
    }

    #[test]
    fn a_poisoned_state_lock_still_serves_the_payload() {
        let (updater, _recorder) = driver(enabled_config());
        let inner = Arc::clone(&updater.state);
        let _ = std::thread::spawn(move || {
            let _guard = inner.lock().unwrap();
            panic!("poison the lock");
        })
        .join();
        // Recovering rather than propagating keeps a background-thread panic
        // from taking the whole update surface down with it.
        updater.handle(UpdateEvent::CheckRequested);
        assert_eq!(updater.payload().state, StateKind::Checking);
    }

    // -- journal integration ---------------------------------------------

    #[test]
    fn write_journal_row_appends_and_swallows_a_typed_failure() {
        let dir = std::env::temp_dir().join(format!("rytm-updater-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        let journal = UpdateJournal::new(dir.clone());
        let record = JournalRecord::new(JournalEvent::CheckOk, Some("1.35.0".into()))
            .with(DetailKey::DurationMs, 3_u64);
        write_journal_row(&journal, &record);
        let body = std::fs::read_to_string(journal.path()).expect("journal written");
        assert!(body.contains("\"event\":\"check_ok\""));

        // A blocked directory makes the append fail; the helper must not panic.
        let blocked = dir.join("blocked");
        std::fs::write(&blocked, b"x").expect("blocker");
        write_journal_row(&UpdateJournal::new(blocked), &record);

        let _ = std::fs::remove_dir_all(&dir);
    }

    // -- install id (spec §5) ---------------------------------------------

    fn scratch_dir(tag: &str) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "rytm-install-id-{tag}-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ));
        let _ = std::fs::remove_dir_all(&dir);
        dir
    }

    #[test]
    fn a_minted_install_id_is_a_well_formed_uuid_v4() {
        for _ in 0..50 {
            let id = mint_install_id();
            assert!(is_well_formed_install_id(&id), "malformed: {id}");
            // Version nibble 4 and RFC-4122 variant bits.
            assert_eq!(id.as_bytes()[14], b'4', "version nibble: {id}");
            assert!(
                matches!(id.as_bytes()[19], b'8' | b'9' | b'a' | b'b'),
                "variant nibble: {id}"
            );
        }
    }

    #[test]
    fn minted_install_ids_are_not_all_the_same() {
        let a = mint_install_id();
        let b = mint_install_id();
        assert_ne!(a, b, "two mints must not collide");
    }

    /// The Windows path, exercised on every OS.
    ///
    /// `mint_install_id` reads `/dev/urandom` where it exists, so on macOS and
    /// Linux the fallback is never reached and a defect in it is invisible
    /// locally — which is exactly what happened: the first version mixed only
    /// values that are constant within a millisecond (clock, stack address,
    /// pid), so two mints in a loop returned the SAME id, and only
    /// windows-latest ever saw it.
    ///
    /// A colliding `install_id` is not cosmetic. Spec §5 buckets the staged
    /// rollout on `sha256(install_id)`, so identical ids move as one install:
    /// a "10% rollout" would reach either none of those machines or all of
    /// them.
    #[test]
    fn the_no_urandom_fallback_does_not_collide_within_a_millisecond() {
        let mut seen = std::collections::HashSet::new();
        for _ in 0..256 {
            let mut bytes = [0_u8; 16];
            fill_without_urandom(&mut bytes);
            assert!(
                seen.insert(format_uuid_v4(bytes)),
                "the no-urandom fallback repeated an id; on Windows this is the ONLY path"
            );
        }
    }

    #[test]
    fn the_fallback_still_produces_well_formed_uuid_v4s() {
        let mut bytes = [0_u8; 16];
        fill_without_urandom(&mut bytes);
        let rendered = format_uuid_v4(bytes);
        let parts: Vec<&str> = rendered.split('-').collect();
        assert_eq!(
            parts.iter().map(|p| p.len()).collect::<Vec<_>>(),
            vec![8, 4, 4, 4, 12]
        );
        assert!(
            parts[2].starts_with('4'),
            "version nibble must be 4: {rendered}"
        );
        assert!(
            matches!(parts[3].as_bytes()[0], b'8' | b'9' | b'a' | b'b'),
            "RFC-4122 variant bits must be set: {rendered}"
        );
    }

    /// Spec §5: minted on first launch, "never regenerated". A drifting id
    /// would move the install between rollout buckets on every launch, which
    /// is precisely the flapping the stable-bucket rule exists to prevent.
    #[test]
    fn the_install_id_is_minted_once_and_then_reused_verbatim() {
        let dir = scratch_dir("stable");
        let first = resolve_install_id(&dir);
        assert!(is_well_formed_install_id(&first));
        for _ in 0..5 {
            assert_eq!(
                resolve_install_id(&dir),
                first,
                "id must never be re-minted"
            );
        }
        // And the stable id means a stable bucket.
        assert_eq!(
            update_policy::rollout_bucket(&first),
            update_policy::rollout_bucket(&resolve_install_id(&dir))
        );
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn a_corrupt_install_id_file_is_replaced_rather_than_trusted() {
        for junk in ["", "   ", "not-a-uuid", "deadbeef", &"f".repeat(80)] {
            let dir = scratch_dir("corrupt");
            std::fs::create_dir_all(&dir).expect("scratch dir");
            std::fs::write(dir.join(INSTALL_ID_FILE_NAME), junk).expect("junk");
            let id = resolve_install_id(&dir);
            assert!(is_well_formed_install_id(&id), "junk {junk:?} -> {id}");
            // The replacement is persisted, so it is stable from now on.
            assert_eq!(resolve_install_id(&dir), id);
            let _ = std::fs::remove_dir_all(&dir);
        }
    }

    #[test]
    fn surrounding_whitespace_in_the_stored_id_is_tolerated() {
        let dir = scratch_dir("whitespace");
        std::fs::create_dir_all(&dir).expect("scratch dir");
        let id = mint_install_id();
        std::fs::write(dir.join(INSTALL_ID_FILE_NAME), format!("\n  {id}  \n")).expect("write");
        assert_eq!(resolve_install_id(&dir), id);
        let _ = std::fs::remove_dir_all(&dir);
    }

    /// An unwritable config dir must not disable updates: the launch gets a
    /// transient id (a random bucket for this run) rather than an error.
    #[test]
    fn an_unwritable_config_dir_still_yields_a_usable_id() {
        let dir = scratch_dir("unwritable");
        std::fs::create_dir_all(dir.parent().expect("parent")).expect("parent dir");
        // A *file* where the directory should be makes create_dir_all fail.
        std::fs::write(&dir, b"x").expect("blocker");
        let id = resolve_install_id(&dir);
        assert!(is_well_formed_install_id(&id));
        let _ = std::fs::remove_file(&dir);
    }

    #[test]
    fn install_id_shape_validation_rejects_every_malformation() {
        let good = mint_install_id();
        assert!(is_well_formed_install_id(&good));
        // Right length, wrong hyphen positions.
        let mut wrong_hyphens = good.replace('-', "0");
        wrong_hyphens.replace_range(0..1, "-");
        assert_eq!(wrong_hyphens.len(), UUID_TEXT_LEN);
        assert!(!is_well_formed_install_id(&wrong_hyphens));
        // Right shape, a non-hex digit.
        let mut non_hex = good.clone();
        non_hex.replace_range(0..1, "z");
        assert!(!is_well_formed_install_id(&non_hex));
        // Too short and too long.
        assert!(!is_well_formed_install_id(&good[..UUID_TEXT_LEN - 1]));
        assert!(!is_well_formed_install_id(&format!("{good}0")));
    }
}
