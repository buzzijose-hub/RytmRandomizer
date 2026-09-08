//! Pure update policy core — the whole §5 state machine with no I/O.
//!
//! This module is deliberately the *only* place update decisions are made,
//! and it is deliberately incapable of making them incorrectly at runtime:
//!
//! * It performs **no** network access, **no** filesystem access, **no**
//!   Tauri calls and **no** clock reads. Time is an input
//!   ([`UpdateEvent::Tick`] / [`Config::now_ms`]-free — callers pass the
//!   instant with the event), so every transition is reproducible.
//! * It is a single pure function [`step`] of shape
//!   `(state, event, config) -> (state, effects)`. Effects are *described*,
//!   never performed; [`crate::updater`] is the thin driver that performs
//!   them and feeds the results back in as events.
//! * Freeze mode short-circuits **before** any check, and the assertion is
//!   structural: [`Effect`] carries no network variant on the frozen path
//!   because `step` returns early. Tests assert on the emitted effect list,
//!   not on a mock.
//! * Consent is a *type*: [`ConsentToken`] carries the exact version it was
//!   granted for and is not `Clone`/`Copy`/`Serialize`/`Default`. The only
//!   constructor is private to this module, and the only way to reach
//!   [`Effect::InstallStagedUpdate`] is to hand `step` a token whose version
//!   equals the staged version. A token cannot outlive the process (it is
//!   not persisted anywhere), so a crash after consent cannot auto-install.
//!
//! The vocabularies here ([`UpdateState`], [`JournalEvent`],
//! [`ErrorCode`]) are the frozen contracts I2 (shell -> webview) and I8
//! (the update journal).

use std::collections::BTreeMap;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

/// Number of buckets the deterministic staged-rollout hash maps into.
pub const ROLLOUT_BUCKET_COUNT: u32 = 100;

/// Maximum accepted length of a manifest `notes` blob, in bytes.
///
/// The notes are rendered in the cockpit; an unbounded blob from a manifest
/// is untrusted input, so it is capped here rather than at the renderer.
pub const MAX_NOTES_BYTES: usize = 8192;

/// Maximum accepted length of a version string, in bytes.
pub const MAX_VERSION_BYTES: usize = 64;

/// Hosts a manifest artifact URL is permitted to point at (spec §4 host
/// pinning). An artifact served from anywhere else is rejected outright —
/// an attacker who can rewrite the manifest must not thereby be able to
/// point the downloader at an arbitrary origin.
pub const ALLOWED_ARTIFACT_HOSTS: &[&str] = &[
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
];

/// Required URL scheme for every manifest artifact URL.
pub const REQUIRED_ARTIFACT_SCHEME: &str = "https://";

/// Path segment every `github.com` artifact URL must contain (spec §4:
/// `https://github.com/<owner>/<repo>/releases/download/…`).
pub const RELEASE_DOWNLOAD_PATH_SEGMENT: &str = "/releases/download/";

// ---------------------------------------------------------------------------
// Error taxonomy (Gate 7): typed codes only, never a raw error string.
// ---------------------------------------------------------------------------

/// Closed taxonomy of update-subsystem failure reasons.
///
/// Every boundary in [`crate::updater`] maps its `io::Error` /
/// transport error / parse error onto one of these before it can reach a
/// journal row, a log line or the webview. Nothing in this enum can carry a
/// filesystem path, a URL or an operating-system message.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ErrorCode {
    /// The manifest could not be fetched (DNS, TLS, connect, timeout).
    NetworkUnavailable,
    /// The manifest host answered with a non-success status.
    ManifestHttpStatus,
    /// The manifest body was not valid JSON or not the v1 schema.
    ManifestMalformed,
    /// A field was present but outside its permitted domain.
    ManifestFieldInvalid,
    /// `schema_version` was not the one this client understands.
    ManifestSchemaUnsupported,
    /// An artifact URL failed scheme or host pinning.
    ManifestHostNotAllowed,
    /// This platform has no entry in `platforms`.
    PlatformUnsupported,
    /// The artifact download failed mid-flight.
    DownloadFailed,
    /// The downloaded artifact could not be written to the staging area.
    StageWriteFailed,
    /// The Ed25519 updater signature did not verify.
    SignatureRejected,
    /// No updater public key is compiled in, so nothing can be verified.
    SignatureKeyMissing,
    /// The install step failed after consent.
    InstallFailed,
    /// The journal file could not be written or rotated.
    JournalWriteFailed,
    /// The beacon GET failed. Never surfaced to the operator; journalled only.
    BeaconFailed,
    /// The sidecar had not confirmed exit when an install-on-quit was due.
    SidecarStillRunning,
    /// A consent token was presented for a version other than the staged one.
    ConsentVersionMismatch,
}

impl ErrorCode {
    /// Stable snake_case wire string. Mirrors the serde representation.
    pub fn as_str(self) -> &'static str {
        match self {
            ErrorCode::NetworkUnavailable => "network_unavailable",
            ErrorCode::ManifestHttpStatus => "manifest_http_status",
            ErrorCode::ManifestMalformed => "manifest_malformed",
            ErrorCode::ManifestFieldInvalid => "manifest_field_invalid",
            ErrorCode::ManifestSchemaUnsupported => "manifest_schema_unsupported",
            ErrorCode::ManifestHostNotAllowed => "manifest_host_not_allowed",
            ErrorCode::PlatformUnsupported => "platform_unsupported",
            ErrorCode::DownloadFailed => "download_failed",
            ErrorCode::StageWriteFailed => "stage_write_failed",
            ErrorCode::SignatureRejected => "signature_rejected",
            ErrorCode::SignatureKeyMissing => "signature_key_missing",
            ErrorCode::InstallFailed => "install_failed",
            ErrorCode::JournalWriteFailed => "journal_write_failed",
            ErrorCode::BeaconFailed => "beacon_failed",
            ErrorCode::SidecarStillRunning => "sidecar_still_running",
            ErrorCode::ConsentVersionMismatch => "consent_version_mismatch",
        }
    }
}

impl fmt::Display for ErrorCode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

// ---------------------------------------------------------------------------
// Contract I8: the closed 17-item journal vocabulary.
// ---------------------------------------------------------------------------

/// The closed journal event vocabulary (contract I8, spec §5.1).
///
/// Modelled as an enum so an unknown event is unrepresentable: there is no
/// `Other(String)` variant and no public constructor from a string.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JournalEvent {
    CheckStarted,
    CheckOk,
    CheckFailed,
    ManifestRejected,
    BucketExcluded,
    DownloadStarted,
    DownloadOk,
    StageFailed,
    SignatureRejected,
    ConsentGranted,
    InstallStarted,
    InstallOk,
    InstallFailed,
    SkipRecorded,
    FreezeSuppressed,
    PingOk,
    PingFailed,
}

impl JournalEvent {
    /// Every member of the vocabulary, in spec §5.1 order.
    pub const ALL: [JournalEvent; 17] = [
        JournalEvent::CheckStarted,
        JournalEvent::CheckOk,
        JournalEvent::CheckFailed,
        JournalEvent::ManifestRejected,
        JournalEvent::BucketExcluded,
        JournalEvent::DownloadStarted,
        JournalEvent::DownloadOk,
        JournalEvent::StageFailed,
        JournalEvent::SignatureRejected,
        JournalEvent::ConsentGranted,
        JournalEvent::InstallStarted,
        JournalEvent::InstallOk,
        JournalEvent::InstallFailed,
        JournalEvent::SkipRecorded,
        JournalEvent::FreezeSuppressed,
        JournalEvent::PingOk,
        JournalEvent::PingFailed,
    ];

    /// Stable snake_case wire string. Mirrors the serde representation.
    pub fn as_str(self) -> &'static str {
        match self {
            JournalEvent::CheckStarted => "check_started",
            JournalEvent::CheckOk => "check_ok",
            JournalEvent::CheckFailed => "check_failed",
            JournalEvent::ManifestRejected => "manifest_rejected",
            JournalEvent::BucketExcluded => "bucket_excluded",
            JournalEvent::DownloadStarted => "download_started",
            JournalEvent::DownloadOk => "download_ok",
            JournalEvent::StageFailed => "stage_failed",
            JournalEvent::SignatureRejected => "signature_rejected",
            JournalEvent::ConsentGranted => "consent_granted",
            JournalEvent::InstallStarted => "install_started",
            JournalEvent::InstallOk => "install_ok",
            JournalEvent::InstallFailed => "install_failed",
            JournalEvent::SkipRecorded => "skip_recorded",
            JournalEvent::FreezeSuppressed => "freeze_suppressed",
            JournalEvent::PingOk => "ping_ok",
            JournalEvent::PingFailed => "ping_failed",
        }
    }
}

impl fmt::Display for JournalEvent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// A bounded, path-free journal detail value.
///
/// The type system is the enforcement: there is no `String` variant, so a
/// raw `io::Error` message or an absolute path has no way in. Sizes and
/// durations are numbers; reasons are [`ErrorCode`]s; everything else is a
/// small bool or a bucket number.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum DetailValue {
    /// A typed failure reason.
    Reason(ErrorCode),
    /// A byte count, millisecond duration, bucket index or percentage.
    Number(u64),
    /// A flag (e.g. `hardware_revalidation`).
    Flag(bool),
}

impl From<ErrorCode> for DetailValue {
    fn from(code: ErrorCode) -> Self {
        DetailValue::Reason(code)
    }
}

impl From<u64> for DetailValue {
    fn from(value: u64) -> Self {
        DetailValue::Number(value)
    }
}

impl From<bool> for DetailValue {
    fn from(value: bool) -> Self {
        DetailValue::Flag(value)
    }
}

/// Detail keys a journal row may carry. Closed set, so no caller can invent
/// a key whose value would be free-form.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DetailKey {
    Reason,
    Bytes,
    DurationMs,
    Bucket,
    RolloutPercent,
    HardwareRevalidation,
    HttpStatus,
}

impl DetailKey {
    /// Stable snake_case wire string.
    pub fn as_str(self) -> &'static str {
        match self {
            DetailKey::Reason => "reason",
            DetailKey::Bytes => "bytes",
            DetailKey::DurationMs => "duration_ms",
            DetailKey::Bucket => "bucket",
            DetailKey::RolloutPercent => "rollout_percent",
            DetailKey::HardwareRevalidation => "hardware_revalidation",
            DetailKey::HttpStatus => "http_status",
        }
    }
}

/// The bounded `detail` map of a journal row.
pub type Detail = BTreeMap<DetailKey, DetailValue>;

/// One journal row the policy asks the driver to append.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JournalRecord {
    /// The event, drawn from the closed vocabulary.
    pub event: JournalEvent,
    /// The version the row is about, when one is known.
    pub version: Option<String>,
    /// Bounded, path-free details.
    pub detail: Detail,
}

impl JournalRecord {
    /// A row with no details.
    pub fn new(event: JournalEvent, version: Option<String>) -> Self {
        Self {
            event,
            version,
            detail: Detail::new(),
        }
    }

    /// Builder-style detail insertion.
    #[must_use]
    pub fn with(mut self, key: DetailKey, value: impl Into<DetailValue>) -> Self {
        self.detail.insert(key, value.into());
        self
    }
}

// ---------------------------------------------------------------------------
// Contract I2: the shell -> webview state vocabulary.
// ---------------------------------------------------------------------------

/// The §5 state vocabulary, as it appears on the wire to the webview.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StateKind {
    /// Updates are frozen; nothing is checked, downloaded or reported.
    Frozen,
    /// No check in flight, nothing staged.
    Idle,
    /// A manifest fetch is in flight.
    Checking,
    /// The last check found this install already current.
    UpToDate,
    /// An acceptable update exists and is downloading.
    Downloading,
    /// An acceptable update is downloaded, verified and staged.
    Staged,
    /// The operator declined this version; no chip until a newer one appears.
    Skipped,
    /// Consent granted; the install is running or queued for quit.
    Installing,
    /// The last operation failed. `error_code` says why.
    Failed,
}

impl StateKind {
    /// Stable snake_case wire string.
    pub fn as_str(self) -> &'static str {
        match self {
            StateKind::Frozen => "frozen",
            StateKind::Idle => "idle",
            StateKind::Checking => "checking",
            StateKind::UpToDate => "up_to_date",
            StateKind::Downloading => "downloading",
            StateKind::Staged => "staged",
            StateKind::Skipped => "skipped",
            StateKind::Installing => "installing",
            StateKind::Failed => "failed",
        }
    }
}

/// The single typed `rytm-update-state` payload (contract I2).
///
/// Exactly one event carries the whole update surface; the webview never has
/// to correlate two channels.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UpdateStatePayload {
    /// Current state, from the §5 vocabulary.
    pub state: StateKind,
    /// The version the state is about, when one is known.
    pub version: Option<String>,
    /// Release notes for that version, when known (capped at [`MAX_NOTES_BYTES`]).
    pub notes: Option<String>,
    /// Whether the release is flagged as needing hardware revalidation.
    pub hardware_revalidation: bool,
    /// Typed failure reason when `state == Failed`; never a raw message.
    pub error_code: Option<ErrorCode>,
}

/// The Tauri event name for contract I2.
pub const UPDATE_STATE_EVENT: &str = "rytm-update-state";

// ---------------------------------------------------------------------------
// Manifest (spec §4).
// ---------------------------------------------------------------------------

/// The only `schema_version` this client accepts.
pub const SUPPORTED_SCHEMA_VERSION: u32 = 1;

/// One platform's artifact entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PlatformEntry {
    /// Base64 Ed25519 updater signature over the artifact.
    pub signature: String,
    /// HTTPS artifact URL, host-pinned to [`ALLOWED_ARTIFACT_HOSTS`].
    pub url: String,
}

/// The channel manifest as fetched (spec §4).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Manifest {
    /// Schema discriminator; must equal [`SUPPORTED_SCHEMA_VERSION`].
    pub schema_version: u32,
    /// Offered version, SemVer.
    pub version: String,
    /// Channel this manifest serves. REQUIRED and closed to the supported
    /// set: a manifest naming an unknown channel is a mis-published file, and
    /// accepting it would let a `nightly` document drive a `stable` client.
    pub channel: String,
    /// Release-note excerpt shown in the consent prompt.
    ///
    /// REQUIRED, matching `_MANIFEST_REQUIRED_FIELDS` in `scripts/release_lib.py`.
    pub notes: String,
    /// ISO-8601 publication timestamp. Carried for display only.
    ///
    /// REQUIRED, matching `_MANIFEST_REQUIRED_FIELDS` in `scripts/release_lib.py`.
    pub pub_date: String,
    /// Whether the release touches the parity/MIDI-pin/ArmedApply surface.
    ///
    /// REQUIRED — deliberately no `#[serde(default)]`. Spec §4 lists it in the
    /// manifest schema, and the Python validator refuses a manifest without it
    /// (`release.manifest.missing_field`). Defaulting it to `false` here made
    /// the two consumers of one schema disagree: Rust silently accepted a
    /// manifest Python rejected, and the operator would never see the
    /// re-validation banner for a release that needs one — the failure is
    /// silent in exactly the direction that matters.
    pub hardware_revalidation: bool,
    /// Staged-rollout percentage, 0..=100.
    pub rollout_percent: u32,
    /// Advisory minimum version (§4.5, never blocking in this client).
    #[serde(default)]
    pub minimum_version: Option<String>,
    /// Per-target artifact entries, keyed by `<os>-<arch>`.
    pub platforms: BTreeMap<String, PlatformEntry>,
}

/// A manifest that has passed every §4 acceptance rule.
///
/// The newtype is the guarantee: nothing downstream accepts a bare
/// [`Manifest`], so an unvalidated manifest cannot reach the download path.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedManifest {
    manifest: Manifest,
    target: String,
}

impl ValidatedManifest {
    /// The offered version.
    pub fn version(&self) -> &str {
        &self.manifest.version
    }

    /// The release notes (already length-capped by validation).
    pub fn notes(&self) -> &str {
        &self.manifest.notes
    }

    /// Whether hardware revalidation is flagged.
    pub fn hardware_revalidation(&self) -> bool {
        self.manifest.hardware_revalidation
    }

    /// The staged-rollout percentage.
    pub fn rollout_percent(&self) -> u32 {
        self.manifest.rollout_percent
    }

    /// The advisory minimum version, if the manifest declared one.
    pub fn minimum_version(&self) -> Option<&str> {
        self.manifest.minimum_version.as_deref()
    }

    /// This client's platform entry (validation proved it exists).
    pub fn platform_entry(&self) -> &PlatformEntry {
        self.manifest
            .platforms
            .get(&self.target)
            .expect("validated manifest always has the resolved target")
    }

    /// The `<os>-<arch>` target this manifest was validated against.
    pub fn target(&self) -> &str {
        &self.target
    }
}

/// Parse and validate a manifest body against spec §4 for `target`.
///
/// Rejection is total and typed: every failure path returns an
/// [`ErrorCode`], never a parser message, so nothing untrusted can reach a
/// log or a journal row.
pub fn validate_manifest(body: &str, target: &str) -> Result<ValidatedManifest, ErrorCode> {
    let manifest: Manifest =
        serde_json::from_str(body).map_err(|_| ErrorCode::ManifestMalformed)?;
    validate_parsed_manifest(manifest, target)
}

/// Validate an already-parsed manifest. Split out so the acceptance rules
/// are testable without going through JSON.
pub fn validate_parsed_manifest(
    manifest: Manifest,
    target: &str,
) -> Result<ValidatedManifest, ErrorCode> {
    if manifest.schema_version != SUPPORTED_SCHEMA_VERSION {
        return Err(ErrorCode::ManifestSchemaUnsupported);
    }
    if !SUPPORTED_CHANNELS.contains(&manifest.channel.as_str()) {
        return Err(ErrorCode::ManifestFieldInvalid);
    }
    if !is_acceptable_version(&manifest.version) {
        return Err(ErrorCode::ManifestFieldInvalid);
    }
    if !is_rfc3339_utc(&manifest.pub_date) {
        return Err(ErrorCode::ManifestFieldInvalid);
    }
    if manifest.rollout_percent > ROLLOUT_BUCKET_COUNT {
        return Err(ErrorCode::ManifestFieldInvalid);
    }
    if manifest.notes.len() > MAX_NOTES_BYTES {
        return Err(ErrorCode::ManifestFieldInvalid);
    }
    if let Some(minimum) = manifest.minimum_version.as_deref() {
        if !is_acceptable_version(minimum) {
            return Err(ErrorCode::ManifestFieldInvalid);
        }
    }
    if manifest.platforms.is_empty() {
        return Err(ErrorCode::ManifestFieldInvalid);
    }
    // Host-pin EVERY entry, not just this platform's: a manifest carrying an
    // off-host URL is a compromised manifest whether or not we would have
    // followed that particular link today.
    for target_key in manifest.platforms.keys() {
        if !SUPPORTED_TARGETS.contains(&target_key.as_str()) {
            return Err(ErrorCode::ManifestFieldInvalid);
        }
    }
    for entry in manifest.platforms.values() {
        if entry.signature.trim().is_empty() {
            return Err(ErrorCode::ManifestFieldInvalid);
        }
        // The updater refuses a non-base64 signature at INSTALL time, which is
        // far too late: the manifest is already published and every client has
        // fetched it. Refusing here keeps the failure at publish time.
        if !entry
            .signature
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '+' | '/' | '='))
        {
            return Err(ErrorCode::ManifestFieldInvalid);
        }
        check_artifact_url(&entry.url)?;
        // A URL naming a different release than the manifest declares ships the
        // wrong binary to everyone on the channel, and the signature still
        // verifies because it signs that other artifact. Only checked when the
        // URL actually encodes a tag — spec §4 does not mandate one.
        if let Some(tag) = release_tag_in_url(&entry.url) {
            if tag != manifest.version {
                return Err(ErrorCode::ManifestFieldInvalid);
            }
        }
    }
    if !manifest.platforms.contains_key(target) {
        return Err(ErrorCode::PlatformUnsupported);
    }
    Ok(ValidatedManifest {
        manifest,
        target: target.to_string(),
    })
}

/// Scheme + host pinning for one artifact URL (spec §4).
fn check_artifact_url(url: &str) -> Result<(), ErrorCode> {
    let Some(rest) = url.strip_prefix(REQUIRED_ARTIFACT_SCHEME) else {
        return Err(ErrorCode::ManifestHostNotAllowed);
    };
    // Authority runs to the first '/', '?' or '#'.
    let authority_end = rest.find(['/', '?', '#']).unwrap_or(rest.len());
    let authority = &rest[..authority_end];
    // Reject userinfo (`user@host`) outright: `https://github.com@evil/…`
    // is the classic host-pinning bypass.
    if authority.contains('@') {
        return Err(ErrorCode::ManifestHostNotAllowed);
    }
    // Reject an explicit port too — the pin is host *and* default port.
    if authority.contains(':') {
        return Err(ErrorCode::ManifestHostNotAllowed);
    }
    if authority.is_empty() {
        return Err(ErrorCode::ManifestHostNotAllowed);
    }
    let host = authority.to_ascii_lowercase();
    if !ALLOWED_ARTIFACT_HOSTS.contains(&host.as_str()) {
        return Err(ErrorCode::ManifestHostNotAllowed);
    }
    // Spec §4 pins the *path* as well as the host: the URL must be
    //   https://github.com/<owner>/<repo>/releases/download/…
    // Host-only pinning would still let a rewritten manifest point at any
    // attacker-controlled file hosted on github.com itself (a Pages site, a
    // gist redirect, a raw file in a fork), which is the same origin as far
    // as TLS is concerned. The redirect targets GitHub hands out for release
    // assets live on the `*.githubusercontent.com` hosts and carry opaque
    // paths, so the path pin applies to `github.com` only.
    if host == "github.com" {
        let path = &rest[authority_end..];
        if !path.contains(RELEASE_DOWNLOAD_PATH_SEGMENT) {
            return Err(ErrorCode::ManifestHostNotAllowed);
        }
    }
    Ok(())
}

/// A version string is acceptable when it is non-blank, bounded, and made
/// only of characters SemVer permits.
/// Channels this client understands, mirroring `SUPPORTED_CHANNELS` in
/// `scripts/release_lib.py`. Kept in sync by the shared fixture corpus.
const SUPPORTED_CHANNELS: [&str; 2] = ["stable", "beta"];

/// Platform keys the updater consumes, mirroring `SUPPORTED_TARGETS` in
/// `scripts/release_lib.py`. A manifest may OMIT a target (a partial rollout)
/// but may not invent one: an unknown key is a mis-generated manifest, and
/// tolerating it hides the generator bug that produced it.
const SUPPORTED_TARGETS: [&str; 4] = [
    "darwin-aarch64",
    "darwin-x86_64",
    "windows-x86_64",
    "linux-x86_64",
];

/// The release tag a download URL encodes, when it encodes one.
///
/// Spec §4 requires the `/releases/download/` path but does not mandate a
/// version segment, so a URL without a SemVer-shaped tag is legal and simply
/// unverifiable here. One that names a DIFFERENT release than the manifest
/// declares ships the wrong binary to the whole channel — and the signature
/// still verifies, because it signs that other artifact.
fn release_tag_in_url(url: &str) -> Option<&str> {
    let after = url.split("/releases/download/v").nth(1)?;
    let tag = after.split('/').next()?;
    let core = tag.split(['-', '+']).next().unwrap_or_default();
    let mut parts = core.split('.');
    let ok = [parts.next(), parts.next(), parts.next()]
        .iter()
        .all(|part| {
            part.is_some_and(|value| !value.is_empty() && value.chars().all(|c| c.is_ascii_digit()))
        })
        && parts.next().is_none();
    ok.then_some(tag)
}

/// RFC-3339 UTC, mirroring `_RFC3339_UTC_RE` in `scripts/release_lib.py`
/// (`YYYY-MM-DDTHH:MM:SS[.fff]Z`). Hand-rolled rather than pulling in a regex
/// crate for one pattern; the shared corpus keeps the two in agreement.
fn is_rfc3339_utc(value: &str) -> bool {
    let Some(rest) = value.strip_suffix('Z') else {
        return false;
    };
    let (date, time) = match rest.split_once('T') {
        Some(parts) => parts,
        None => return false,
    };
    let date_parts: Vec<&str> = date.split('-').collect();
    if date_parts.len() != 3 {
        return false;
    }
    let widths = [4usize, 2, 2];
    if !date_parts
        .iter()
        .zip(widths)
        .all(|(part, width)| part.len() == width && part.chars().all(|c| c.is_ascii_digit()))
    {
        return false;
    }
    let (clock, fraction) = match time.split_once('.') {
        Some((clock, fraction)) => (clock, Some(fraction)),
        None => (time, None),
    };
    if let Some(fraction) = fraction {
        if fraction.is_empty() || !fraction.chars().all(|c| c.is_ascii_digit()) {
            return false;
        }
    }
    let clock_parts: Vec<&str> = clock.split(':').collect();
    clock_parts.len() == 3
        && clock_parts
            .iter()
            .all(|part| part.len() == 2 && part.chars().all(|c| c.is_ascii_digit()))
}

fn is_acceptable_version(version: &str) -> bool {
    if version.is_empty() || version.len() > MAX_VERSION_BYTES {
        return false;
    }
    if !version
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '-' | '+'))
    {
        return false;
    }
    // Must start with a digit: `v1.2.3` and `-beta` are both rejected so the
    // comparison below never has to guess.
    if !version.starts_with(|c: char| c.is_ascii_digit()) {
        return false;
    }
    // ...and must be a full MAJOR.MINOR.PATCH triple. A character-class check
    // alone accepted "1.35", which the Python validator rejects — the two
    // consumers of one schema disagreeing on what a version IS. The corpus
    // fixture `version_not_semver.json` pins this.
    let core = version.split(['-', '+']).next().unwrap_or_default();
    let mut parts = core.split('.');
    let triple = [parts.next(), parts.next(), parts.next()];
    if parts.next().is_some() {
        return false;
    }
    triple.iter().all(|part| {
        part.is_some_and(|value| !value.is_empty() && value.chars().all(|c| c.is_ascii_digit()))
    })
}

/// Compare two dotted numeric-prefixed versions.
///
/// Deliberately small: it orders the numeric release triple and treats any
/// pre-release suffix as *lower* than the same triple without one, which is
/// the SemVer rule the update decision needs. It never panics on malformed
/// input — non-numeric components sort as zero — because validation has
/// already bounded the character set.
pub fn version_is_newer(candidate: &str, current: &str) -> bool {
    numeric_release(candidate) > numeric_release(current)
        || (numeric_release(candidate) == numeric_release(current)
            && prerelease_rank(candidate) > prerelease_rank(current))
}

fn numeric_release(version: &str) -> [u64; 3] {
    let core = version
        .split_once('-')
        .map_or(version, |(core, _)| core)
        .split_once('+')
        .map_or_else(
            || version.split_once('-').map_or(version, |(core, _)| core),
            |(core, _)| core,
        );
    let mut out = [0_u64; 3];
    for (slot, part) in out.iter_mut().zip(core.split('.')) {
        *slot = part.parse::<u64>().unwrap_or(0);
    }
    out
}

/// A release (no `-suffix`) outranks any pre-release of the same triple.
fn prerelease_rank(version: &str) -> u8 {
    u8::from(!version.contains('-'))
}

// ---------------------------------------------------------------------------
// Deterministic staged-rollout bucketing (spec §5).
// ---------------------------------------------------------------------------

/// Deterministic 0..99 bucket for an install id.
///
/// First 4 bytes of `SHA-256(install_id)` read as a big-endian `u32`, modulo
/// [`ROLLOUT_BUCKET_COUNT`]. Stable per install, so nobody flaps in and out
/// as the rollout percentage rises, and every percentage step is a strict
/// superset of the last.
pub fn rollout_bucket(install_id: &str) -> u32 {
    let digest = Sha256::digest(install_id.as_bytes());
    let head = u32::from_be_bytes([digest[0], digest[1], digest[2], digest[3]]);
    head % ROLLOUT_BUCKET_COUNT
}

/// Whether this install is inside the staged rollout.
pub fn rollout_admits(install_id: &str, rollout_percent: u32) -> bool {
    rollout_bucket(install_id) < rollout_percent
}

// ---------------------------------------------------------------------------
// Consent: a version-bound, process-lifetime, unforgeable token.
// ---------------------------------------------------------------------------

/// Proof that the operator consented to installing one specific version.
///
/// Not `Clone`, not `Copy`, not `Default`, not `Serialize`; its fields are
/// private and its only constructor ([`ConsentToken::mint`]) is private to
/// this module and called from exactly one place — [`step`]'s
/// [`UpdateEvent::ConsentGranted`] arm, after that arm has confirmed the
/// artifact is staged, the version matches, and a signing key exists.
/// Consequently:
///
/// * **an install effect cannot be constructed without a token.** This is a
///   compile-time fact, not a convention: [`Effect::InstallStagedUpdate`]
///   wraps an [`InstallAuthorisation`] whose fields are private, and the only
///   thing that can build one is [`ConsentToken::into_install_effect`].
/// * **a token for 1.35.0 cannot authorise installing 1.36.0** — the token
///   carries the version, and the effect is built *from* the token, so the
///   two cannot disagree. (`step` additionally rejects a consent event whose
///   version is not the staged one with
///   [`ErrorCode::ConsentVersionMismatch`], which is the earlier, friendlier
///   of the two barriers.)
/// * **a token cannot survive a crash and be replayed**, because it has no
///   serialised form at all and the [`UpdateState`] that holds it is neither
///   `Clone` nor `Serialize`. A restarted process begins at `Idle` with
///   nothing pending — spec §5's never-auto-install-after-a-crash rule.
/// * **a token is single-use**: `into_install_effect` takes `self` by value.
#[derive(Debug, PartialEq, Eq)]
pub struct ConsentToken {
    version: String,
    choice: ConsentChoice,
}

impl ConsentToken {
    /// Mint a token. Private to this module *and* only ever called from
    /// [`step`]'s [`UpdateEvent::ConsentGranted`] arm, after that arm has
    /// checked the artifact is staged, the version matches, and a signing
    /// key exists.
    fn mint(version: String, choice: ConsentChoice) -> Self {
        Self { version, choice }
    }

    /// The version this token authorises, and only this version.
    pub fn version(&self) -> &str {
        &self.version
    }

    /// How the operator asked for it to be installed.
    pub fn choice(&self) -> ConsentChoice {
        self.choice
    }

    /// Consume the token to produce the one install effect it authorises.
    ///
    /// This is the **only** constructor of [`Effect::InstallStagedUpdate`]:
    /// the variant's fields are unnameable outside this module (see
    /// [`Effect`]'s private `InstallAuthorisation` payload), so no caller —
    /// including a future refactor of [`step`] itself — can synthesise an
    /// install effect without first holding a token, and the token can only
    /// come from a consent event that passed every check. Taking `self` by
    /// value also makes the token single-use.
    fn into_install_effect(self) -> Effect {
        Effect::InstallStagedUpdate(InstallAuthorisation {
            version: self.version,
            choice: self.choice,
        })
    }
}

/// The payload of [`Effect::InstallStagedUpdate`].
///
/// Its fields are private and it has no public constructor, so the only way
/// to obtain one is [`ConsentToken::into_install_effect`]. That is what makes
/// the §1 invariant — "no code path may invoke the install step without a
/// consent token minted by an explicit UI action in the current process
/// lifetime" — a *type* error rather than a runtime check someone can forget.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InstallAuthorisation {
    version: String,
    choice: ConsentChoice,
}

impl InstallAuthorisation {
    /// The version this install is authorised for.
    pub fn version(&self) -> &str {
        &self.version
    }

    /// Immediate vs on-quit.
    pub fn choice(&self) -> ConsentChoice {
        self.choice
    }
}

/// What the operator chose to do with a staged update.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ConsentChoice {
    /// Install immediately (after the graceful sidecar shutdown completes).
    RestartAndInstall,
    /// Install when the app next quits, again only after a clean shutdown.
    InstallOnQuit,
}

// ---------------------------------------------------------------------------
// Configuration (spec §7 env surface, resolved by the driver).
// ---------------------------------------------------------------------------

/// Immutable per-process update configuration.
///
/// Resolved once by [`crate::updater`] from the environment and the build,
/// then passed to every [`step`] call. `updates_enabled == false` is freeze
/// mode; `signing_key_present == false` is the pre-key
/// check-and-notify-only mode.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Config {
    /// This build's version.
    pub current_version: String,
    /// `<os>-<arch>` target string used to select the platform entry.
    pub target: String,
    /// Stable anonymous install id used for rollout bucketing only.
    pub install_id: String,
    /// Freeze gate: false means no check, no download, no beacon, no chip.
    pub updates_enabled: bool,
    /// Beacon gate (`RYTM_RAND_UPDATE_BEACON=off` sets this false).
    pub beacon_enabled: bool,
    /// Channel name (`stable` / `beta`).
    pub channel: String,
    /// Whether an updater public key is compiled into this build.
    ///
    /// While false the policy is *structurally* incapable of emitting
    /// [`Effect::InstallStagedUpdate`]: it never advances past
    /// [`StateKind::Staged`], and the driver has no other install path.
    pub signing_key_present: bool,
}

impl Config {
    /// Whether this build may install anything at all.
    pub fn install_permitted(&self) -> bool {
        self.signing_key_present
    }
}

// ---------------------------------------------------------------------------
// State.
// ---------------------------------------------------------------------------

/// Everything the policy remembers between events.
///
/// Deliberately **not** `Clone` and **not** `Serialize`: it may hold a live
/// [`ConsentToken`], and a clonable or persistable state would let one
/// operator consent authorise two installs, or survive the crash that spec §5
/// says must void it.
#[derive(Debug, PartialEq, Eq)]
pub struct UpdateState {
    kind: StateKind,
    version: Option<String>,
    notes: Option<String>,
    hardware_revalidation: bool,
    error_code: Option<ErrorCode>,
    /// Versions the operator explicitly skipped this process lifetime.
    skipped: Vec<String>,
    /// The live consent token, held from the moment consent is granted until
    /// the install effect consumes it (or a skip / failure drops it).
    ///
    /// This is a `ConsentToken`, not a `String`, so the pending install
    /// cannot be reconstructed from state that survived a serialisation
    /// round-trip: `UpdateState` is deliberately **not** `Serialize`, and
    /// the token has no serialised form at all. A crash therefore loses the
    /// token, and the next launch starts at `Idle` with nothing pending —
    /// spec §5's "a crash after consent does NOT auto-install on next
    /// start", enforced by the type rather than by remembering to clear a
    /// file.
    pending_install: Option<ConsentToken>,
    /// True once the staged artifact exists on disk and verified.
    staged: bool,
}

impl UpdateState {
    /// The initial state for `config`.
    ///
    /// Freeze mode is expressed in the *state*, not merely checked later, so
    /// the frozen posture is visible to the webview from the first event.
    pub fn initial(config: &Config) -> Self {
        Self {
            kind: if config.updates_enabled {
                StateKind::Idle
            } else {
                StateKind::Frozen
            },
            version: None,
            notes: None,
            hardware_revalidation: false,
            error_code: None,
            skipped: Vec::new(),
            pending_install: None,
            staged: false,
        }
    }

    /// The current state kind.
    pub fn kind(&self) -> StateKind {
        self.kind
    }

    /// The version the state is about, when known.
    pub fn version(&self) -> Option<&str> {
        self.version.as_deref()
    }

    /// Whether a verified artifact is staged on disk.
    pub fn is_staged(&self) -> bool {
        self.staged
    }

    /// Whether an install is queued to run at quit.
    pub fn pending_quit_install(&self) -> Option<&str> {
        self.pending_install.as_ref().map(ConsentToken::version)
    }

    /// Whether `version` was skipped this process lifetime.
    pub fn is_skipped(&self, version: &str) -> bool {
        self.skipped.iter().any(|v| v == version)
    }

    /// The contract-I2 payload for this state.
    pub fn payload(&self) -> UpdateStatePayload {
        UpdateStatePayload {
            state: self.kind,
            version: self.version.clone(),
            notes: self.notes.clone(),
            hardware_revalidation: self.hardware_revalidation,
            error_code: self.error_code,
        }
    }
}

// ---------------------------------------------------------------------------
// Events and effects.
// ---------------------------------------------------------------------------

/// Everything that can happen to the update subsystem.
///
/// Time enters only through the `_ms` fields on completion events; the
/// policy never reads a clock.
// PartialEq so a caller can assert WHICH event an operator gesture produced.
// Without it the command layer could only be tested by observing side effects,
// which is exactly the indirection that let the panel's buttons look wired
// while reaching nothing.
#[derive(Debug, PartialEq)]
pub enum UpdateEvent {
    /// Launch, the 4-hourly timer, or the operator's "Check now".
    CheckRequested,
    /// The driver fetched a manifest body successfully.
    ManifestFetched {
        /// Raw response body.
        body: String,
        /// How long the fetch took.
        duration_ms: u64,
    },
    /// The manifest fetch itself failed.
    ManifestFetchFailed {
        /// Typed reason.
        code: ErrorCode,
    },
    /// The artifact downloaded, verified and staged successfully.
    DownloadStaged {
        /// The version that was staged.
        version: String,
        /// Artifact size.
        bytes: u64,
        /// Total download+verify+stage duration.
        duration_ms: u64,
    },
    /// The download or the staging write failed.
    DownloadFailed {
        /// The version that failed.
        version: String,
        /// Typed reason.
        code: ErrorCode,
    },
    /// The Ed25519 signature over the downloaded artifact did not verify.
    SignatureRejected {
        /// The version whose artifact failed verification.
        version: String,
    },
    /// The operator consented to installing `version`.
    ConsentGranted {
        /// The version consented to.
        version: String,
        /// Immediate vs on-quit.
        choice: ConsentChoice,
    },
    /// The operator skipped `version`.
    SkipRequested {
        /// The version to stop nagging about.
        version: String,
    },
    /// The graceful sidecar shutdown sequence confirmed the child exited.
    SidecarExited,
    /// A quit was requested but the sidecar has not confirmed exit.
    QuitWithoutSidecarExit,
    /// The install completed.
    InstallSucceeded {
        /// The version that was installed.
        version: String,
    },
    /// The install failed.
    InstallFailed {
        /// The version that failed to install.
        version: String,
        /// Typed reason.
        code: ErrorCode,
    },
    /// The fire-and-forget beacon GET completed.
    BeaconCompleted {
        /// Whether the GET returned a success status.
        ok: bool,
    },
}

/// A side effect the driver should perform. Describing, never doing, is what
/// makes the whole policy testable without a mock.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Effect {
    /// Fetch the channel manifest for `channel`.
    FetchManifest {
        /// The channel to fetch.
        channel: String,
    },
    /// Download, verify and stage the artifact at `url`.
    DownloadArtifact {
        /// The version being fetched.
        version: String,
        /// The host-pinned artifact URL.
        url: String,
        /// The base64 Ed25519 signature to verify against.
        signature: String,
    },
    /// Install the already-staged artifact.
    ///
    /// Structurally unreachable without consent: the payload's fields are
    /// private and its only constructor is
    /// [`ConsentToken::into_install_effect`].
    InstallStagedUpdate(InstallAuthorisation),
    /// Fire-and-forget beacon GET for `version` on `target`.
    SendBeacon {
        /// The version being reported.
        version: String,
        /// The `<os>-<arch>` target.
        target: String,
    },
    /// Append one row to the update journal.
    Journal(JournalRecord),
    /// Emit the contract-I2 `rytm-update-state` event to the webview.
    EmitState(UpdateStatePayload),
}

/// The result of one [`step`].
#[derive(Debug, PartialEq, Eq)]
pub struct Transition {
    /// The state after the event.
    pub state: UpdateState,
    /// The effects the driver must perform, in order.
    pub effects: Vec<Effect>,
}

impl Transition {
    /// Whether any effect touches the network. Used by the freeze-mode tests
    /// to assert on the effect list rather than on a mock.
    pub fn has_network_effect(&self) -> bool {
        self.effects.iter().any(|effect| {
            matches!(
                effect,
                Effect::FetchManifest { .. }
                    | Effect::DownloadArtifact { .. }
                    | Effect::SendBeacon { .. }
            )
        })
    }

    /// Whether any effect installs anything.
    pub fn has_install_effect(&self) -> bool {
        self.effects
            .iter()
            .any(|effect| matches!(effect, Effect::InstallStagedUpdate { .. }))
    }
}

/// Build a transition, always appending the contract-I2 state emission last
/// so the webview sees a consistent snapshot after the journal rows.
fn finish(state: UpdateState, mut effects: Vec<Effect>) -> Transition {
    effects.push(Effect::EmitState(state.payload()));
    Transition { state, effects }
}

/// The whole §5 state machine: `(state, event, config) -> (state, effects)`.
///
/// Pure. No clock, no network, no filesystem, no Tauri.
pub fn step(state: UpdateState, event: UpdateEvent, config: &Config) -> Transition {
    // Freeze short-circuits BEFORE anything else, including before any
    // inspection of the event's payload. The only thing a frozen install
    // does is journal that it suppressed the action.
    if !config.updates_enabled {
        let mut frozen = state;
        frozen.kind = StateKind::Frozen;
        frozen.version = None;
        frozen.notes = None;
        frozen.hardware_revalidation = false;
        frozen.error_code = None;
        frozen.staged = false;
        frozen.pending_install = None;
        return finish(
            frozen,
            vec![Effect::Journal(JournalRecord::new(
                JournalEvent::FreezeSuppressed,
                None,
            ))],
        );
    }

    match event {
        UpdateEvent::CheckRequested => step_check_requested(state, config),
        UpdateEvent::ManifestFetched { body, duration_ms } => {
            step_manifest_fetched(state, config, &body, duration_ms)
        }
        UpdateEvent::ManifestFetchFailed { code } => step_check_failed(state, code),
        UpdateEvent::DownloadStaged {
            version,
            bytes,
            duration_ms,
        } => step_download_staged(state, config, version, bytes, duration_ms),
        UpdateEvent::DownloadFailed { version, code } => step_download_failed(state, version, code),
        UpdateEvent::SignatureRejected { version } => step_signature_rejected(state, version),
        UpdateEvent::ConsentGranted { version, choice } => {
            step_consent_granted(state, config, version, choice)
        }
        UpdateEvent::SkipRequested { version } => step_skip(state, version),
        UpdateEvent::SidecarExited => step_sidecar_exited(state, config),
        UpdateEvent::QuitWithoutSidecarExit => step_quit_without_exit(state),
        UpdateEvent::InstallSucceeded { version } => step_install_succeeded(state, version),
        UpdateEvent::InstallFailed { version, code } => step_install_failed(state, version, code),
        UpdateEvent::BeaconCompleted { ok } => step_beacon_completed(state, ok),
    }
}

fn step_check_requested(mut state: UpdateState, config: &Config) -> Transition {
    // A staged artifact awaiting consent is not re-checked out from under
    // the operator: re-entering `Checking` would blank the chip they are
    // looking at, and a newer manifest could silently replace the version
    // they were deciding about.
    //
    // The beacon still fires. It reports the *running* version, not the
    // staged one, and §6's histogram counts check-ins — so an install that
    // sits staged for a week awaiting consent must keep checking in or it
    // vanishes from the fleet view precisely while it is most interesting
    // (it is the population a rollout has reached but not yet converted).
    if state.staged || state.pending_install.is_some() {
        return finish(state, beacon_effects(config));
    }
    state.kind = StateKind::Checking;
    state.error_code = None;
    let mut effects = vec![
        Effect::Journal(JournalRecord::new(JournalEvent::CheckStarted, None)),
        Effect::FetchManifest {
            channel: config.channel.clone(),
        },
    ];
    effects.extend(beacon_effects(config));
    finish(state, effects)
}

/// The fire-and-forget §6 beacon, or nothing when it is gated off.
///
/// Always reports `config.current_version` — the version actually running —
/// and never the `install_id` or anything else identifying. Freeze mode is
/// handled upstream in [`step`], which returns before any of this runs, so
/// the two opt-outs (`RYTM_RAND_UPDATES=off` and
/// `RYTM_RAND_UPDATE_BEACON=off`) compose as spec §6 describes.
fn beacon_effects(config: &Config) -> Vec<Effect> {
    if config.beacon_enabled {
        vec![Effect::SendBeacon {
            version: config.current_version.clone(),
            target: config.target.clone(),
        }]
    } else {
        Vec::new()
    }
}

fn step_manifest_fetched(
    mut state: UpdateState,
    config: &Config,
    body: &str,
    duration_ms: u64,
) -> Transition {
    let manifest = match validate_manifest(body, &config.target) {
        Ok(manifest) => manifest,
        Err(code) => {
            state.kind = StateKind::Failed;
            state.error_code = Some(code);
            state.version = None;
            state.notes = None;
            state.hardware_revalidation = false;
            return finish(
                state,
                vec![Effect::Journal(
                    JournalRecord::new(JournalEvent::ManifestRejected, None)
                        .with(DetailKey::Reason, code),
                )],
            );
        }
    };

    let mut effects = vec![Effect::Journal(
        JournalRecord::new(JournalEvent::CheckOk, Some(manifest.version().to_string()))
            .with(DetailKey::DurationMs, duration_ms)
            .with(
                DetailKey::RolloutPercent,
                u64::from(manifest.rollout_percent()),
            )
            .with(
                DetailKey::HardwareRevalidation,
                manifest.hardware_revalidation(),
            ),
    )];

    // No beacon here: it already fired at check-start
    // (`step_check_requested`). Firing on the *request* rather than on a
    // successful manifest fetch is what keeps the check-in independent of
    // the manifest — §6's "structurally unable to gate" property — so a
    // client behind a proxy that blocks the manifest still shows up in the
    // fleet histogram instead of silently disappearing from it.
    if !version_is_newer(manifest.version(), &config.current_version) {
        state.kind = StateKind::UpToDate;
        state.version = Some(config.current_version.clone());
        state.notes = None;
        state.hardware_revalidation = false;
        state.error_code = None;
        return finish(state, effects);
    }

    if state.is_skipped(manifest.version()) {
        state.kind = StateKind::Skipped;
        state.version = Some(manifest.version().to_string());
        state.notes = Some(manifest.notes().to_string());
        state.hardware_revalidation = manifest.hardware_revalidation();
        state.error_code = None;
        return finish(state, effects);
    }

    let bucket = rollout_bucket(&config.install_id);
    if bucket >= manifest.rollout_percent() {
        effects.push(Effect::Journal(
            JournalRecord::new(
                JournalEvent::BucketExcluded,
                Some(manifest.version().to_string()),
            )
            .with(DetailKey::Bucket, u64::from(bucket))
            .with(
                DetailKey::RolloutPercent,
                u64::from(manifest.rollout_percent()),
            ),
        ));
        state.kind = StateKind::UpToDate;
        state.version = Some(config.current_version.clone());
        state.notes = None;
        state.hardware_revalidation = false;
        state.error_code = None;
        return finish(state, effects);
    }

    let entry = manifest.platform_entry();
    effects.push(Effect::Journal(JournalRecord::new(
        JournalEvent::DownloadStarted,
        Some(manifest.version().to_string()),
    )));
    effects.push(Effect::DownloadArtifact {
        version: manifest.version().to_string(),
        url: entry.url.clone(),
        signature: entry.signature.clone(),
    });
    state.kind = StateKind::Downloading;
    state.version = Some(manifest.version().to_string());
    state.notes = Some(manifest.notes().to_string());
    state.hardware_revalidation = manifest.hardware_revalidation();
    state.error_code = None;
    finish(state, effects)
}

fn step_check_failed(mut state: UpdateState, code: ErrorCode) -> Transition {
    state.kind = StateKind::Failed;
    state.error_code = Some(code);
    finish(
        state,
        vec![Effect::Journal(
            JournalRecord::new(JournalEvent::CheckFailed, None).with(DetailKey::Reason, code),
        )],
    )
}

fn step_download_staged(
    mut state: UpdateState,
    config: &Config,
    version: String,
    bytes: u64,
    duration_ms: u64,
) -> Transition {
    // A staging report for a version we are not downloading is ignored
    // rather than trusted: it would otherwise let a stale in-flight download
    // overwrite the chip after the operator skipped that version.
    if state.version.as_deref() != Some(version.as_str()) {
        return finish(state, Vec::new());
    }
    let effects = vec![Effect::Journal(
        JournalRecord::new(JournalEvent::DownloadOk, Some(version.clone()))
            .with(DetailKey::Bytes, bytes)
            .with(DetailKey::DurationMs, duration_ms),
    )];
    state.kind = StateKind::Staged;
    state.staged = true;
    state.error_code = None;
    // Without a compiled-in public key nothing was verifiable, so the state
    // stops here permanently: `step_consent_granted` refuses to emit an
    // install effect and there is no other route to one.
    let _ = config;
    finish(state, effects)
}

fn step_download_failed(mut state: UpdateState, version: String, code: ErrorCode) -> Transition {
    state.kind = StateKind::Failed;
    state.staged = false;
    state.error_code = Some(code);
    // Spec §5 routes BOTH arms of the download/verify branch — `sig/IO fail`
    // — into the single `stage_failed` state. The distinction between a
    // mid-flight transport failure and a staging-write failure lives in the
    // typed `reason`, not in a second event: `check_failed` is reserved for
    // the *manifest* arm, and reusing it here would make a failed artifact
    // download indistinguishable from an unreachable manifest in the journal
    // (and in the panel's `check_failed` copy).
    finish(
        state,
        vec![Effect::Journal(
            JournalRecord::new(JournalEvent::StageFailed, Some(version))
                .with(DetailKey::Reason, code),
        )],
    )
}

fn step_signature_rejected(mut state: UpdateState, version: String) -> Transition {
    state.kind = StateKind::Failed;
    state.staged = false;
    state.error_code = Some(ErrorCode::SignatureRejected);
    finish(
        state,
        vec![Effect::Journal(
            JournalRecord::new(JournalEvent::SignatureRejected, Some(version))
                .with(DetailKey::Reason, ErrorCode::SignatureRejected),
        )],
    )
}

fn step_consent_granted(
    mut state: UpdateState,
    config: &Config,
    version: String,
    choice: ConsentChoice,
) -> Transition {
    // Consent is only meaningful against a verified, staged artifact for
    // exactly this version.
    if !state.staged || state.version.as_deref() != Some(version.as_str()) {
        state.kind = StateKind::Failed;
        state.error_code = Some(ErrorCode::ConsentVersionMismatch);
        return finish(
            state,
            vec![Effect::Journal(
                JournalRecord::new(JournalEvent::InstallFailed, Some(version))
                    .with(DetailKey::Reason, ErrorCode::ConsentVersionMismatch),
            )],
        );
    }
    if !config.install_permitted() {
        // Check-and-notify-only mode: no key, so nothing is installable and
        // no install effect is emitted. The state stays Staged so the
        // cockpit keeps showing the (unusable) artifact honestly.
        return finish(
            state,
            vec![Effect::Journal(
                JournalRecord::new(JournalEvent::InstallFailed, Some(version))
                    .with(DetailKey::Reason, ErrorCode::SignatureKeyMissing),
            )],
        );
    }

    // The token is minted exactly here — the single place in the whole
    // program that constructs one — and is then *held by the state* until an
    // install effect consumes it. Because it is not `Clone`, moving it into
    // the state is the only thing that can happen to it.
    //
    // Note that no install effect is emitted on this path for EITHER choice:
    // spec §5 requires the install to run only after the graceful-shutdown
    // sequence confirms the sidecar exited, so even "Now — restart
    // immediately" waits for `SidecarExited`.
    state.pending_install = Some(ConsentToken::mint(version.clone(), choice));
    state.kind = match choice {
        ConsentChoice::RestartAndInstall => StateKind::Installing,
        ConsentChoice::InstallOnQuit => StateKind::Staged,
    };
    state.error_code = None;
    let effects = vec![Effect::Journal(JournalRecord::new(
        JournalEvent::ConsentGranted,
        Some(version),
    ))];
    finish(state, effects)
}

fn step_skip(mut state: UpdateState, version: String) -> Transition {
    if !state.is_skipped(&version) {
        state.skipped.push(version.clone());
    }
    // Skipping discards the pending install: consent and skip are mutually
    // exclusive, and the later choice wins.
    if state.pending_quit_install() == Some(version.as_str()) {
        // Dropping the token here is the whole mechanism: with no token
        // there is no way to build an install effect for this version again.
        state.pending_install = None;
    }
    if state.version.as_deref() == Some(version.as_str()) {
        state.kind = StateKind::Skipped;
        state.staged = false;
    }
    state.error_code = None;
    finish(
        state,
        vec![Effect::Journal(JournalRecord::new(
            JournalEvent::SkipRecorded,
            Some(version),
        ))],
    )
}

fn step_sidecar_exited(mut state: UpdateState, config: &Config) -> Transition {
    // Taking the token out of the state is what authorises the install. If
    // there is none — no consent this process lifetime — this is a no-op,
    // which is exactly the "crash after consent does not auto-install"
    // behaviour: the restarted process's state has no token to take.
    let Some(token) = state.pending_install.take() else {
        return finish(state, Vec::new());
    };
    if !config.install_permitted() {
        // Check-and-notify-only: the token is dropped unconsumed, so no
        // install effect can be built from it. The artifact stays staged and
        // the operator is told why, honestly, rather than silently stalling.
        state.kind = StateKind::Staged;
        return finish(
            state,
            vec![Effect::Journal(
                JournalRecord::new(
                    JournalEvent::InstallFailed,
                    Some(token.version().to_string()),
                )
                .with(DetailKey::Reason, ErrorCode::SignatureKeyMissing),
            )],
        );
    }
    let record = JournalRecord::new(
        JournalEvent::InstallStarted,
        Some(token.version().to_string()),
    );
    state.kind = StateKind::Installing;
    state.error_code = None;
    finish(
        state,
        vec![Effect::Journal(record), token.into_install_effect()],
    )
}

fn step_quit_without_exit(mut state: UpdateState) -> Transition {
    let Some(version) = state.pending_quit_install().map(str::to_string) else {
        return finish(state, Vec::new());
    };
    // The install NEVER runs concurrently with a live sidecar. The pending
    // install survives (the next launch will re-offer it), but nothing is
    // swapped underneath a running process.
    state.kind = StateKind::Failed;
    state.error_code = Some(ErrorCode::SidecarStillRunning);
    finish(
        state,
        vec![Effect::Journal(
            JournalRecord::new(JournalEvent::InstallFailed, Some(version))
                .with(DetailKey::Reason, ErrorCode::SidecarStillRunning),
        )],
    )
}

fn step_install_succeeded(mut state: UpdateState, version: String) -> Transition {
    state.kind = StateKind::Installing;
    state.pending_install = None;
    state.staged = false;
    state.error_code = None;
    finish(
        state,
        vec![Effect::Journal(JournalRecord::new(
            JournalEvent::InstallOk,
            Some(version),
        ))],
    )
}

fn step_install_failed(mut state: UpdateState, version: String, code: ErrorCode) -> Transition {
    state.kind = StateKind::Failed;
    state.pending_install = None;
    state.error_code = Some(code);
    finish(
        state,
        vec![Effect::Journal(
            JournalRecord::new(JournalEvent::InstallFailed, Some(version))
                .with(DetailKey::Reason, code),
        )],
    )
}

fn step_beacon_completed(state: UpdateState, ok: bool) -> Transition {
    // The beacon is observability only: it never changes update state, so
    // the row is journalled and the state re-emitted unchanged.
    let record = if ok {
        JournalRecord::new(JournalEvent::PingOk, None)
    } else {
        JournalRecord::new(JournalEvent::PingFailed, None)
            .with(DetailKey::Reason, ErrorCode::BeaconFailed)
    };
    finish(state, vec![Effect::Journal(record)])
}

#[cfg(test)]
mod tests {
    use super::*;

    const TARGET: &str = "darwin-aarch64";

    fn config() -> Config {
        Config {
            current_version: "1.34.0".to_string(),
            target: TARGET.to_string(),
            // Bucket 0 for this literal (asserted in `install_id_zero_is_low_bucket`).
            install_id: "bucket-zero-install".to_string(),
            updates_enabled: true,
            beacon_enabled: false,
            channel: "stable".to_string(),
            signing_key_present: true,
        }
    }

    fn manifest_json(version: &str, rollout: u32) -> String {
        format!(
            r#"{{
                "schema_version": 1,
                "channel": "stable",
                "version": "{version}",
                "notes": "notes for {version}",
                "pub_date": "2026-09-07T00:00:00Z",
                "hardware_revalidation": false,
                "rollout_percent": {rollout},
                "platforms": {{
                    "darwin-aarch64": {{
                        "signature": "c2ln",
                        "url": "https://github.com/o/r/releases/download/v{version}/app.tar.gz"
                    }}
                }}
            }}"#
        )
    }

    fn low_bucket_id() -> String {
        // Deterministically find an install id in bucket 0 so the happy path
        // never depends on a hash literal drifting.
        (0..10_000)
            .map(|n| format!("install-{n}"))
            .find(|id| rollout_bucket(id) == 0)
            .expect("some id lands in bucket 0")
    }

    fn high_bucket_id() -> String {
        (0..10_000)
            .map(|n| format!("install-{n}"))
            .find(|id| rollout_bucket(id) == 99)
            .expect("some id lands in bucket 99")
    }

    /// Drive to the Staged state for `version`, returning the state.
    /// A fresh `Checking` state. Rebuilt rather than cloned: `UpdateState`
    /// is intentionally not `Clone` (it may hold a `ConsentToken`), so tests
    /// that need "the same state twice" construct it twice.
    fn checking_state(config: &Config) -> UpdateState {
        step(
            UpdateState::initial(config),
            UpdateEvent::CheckRequested,
            config,
        )
        .state
    }

    /// A fresh `Downloading` state for `version` at 100% rollout.
    fn downloading_state(config: &Config, version: &str) -> UpdateState {
        step(
            checking_state(config),
            UpdateEvent::ManifestFetched {
                body: manifest_json(version, 100),
                duration_ms: 12,
            },
            config,
        )
        .state
    }

    fn staged_state(config: &Config, version: &str) -> UpdateState {
        step(
            downloading_state(config, version),
            UpdateEvent::DownloadStaged {
                version: version.to_string(),
                bytes: 42,
                duration_ms: 99,
            },
            config,
        )
        .state
    }

    // -- vocabularies --------------------------------------------------

    #[test]
    fn journal_vocabulary_has_seventeen_distinct_members() {
        let mut seen = std::collections::BTreeSet::new();
        for event in JournalEvent::ALL {
            assert!(seen.insert(event.as_str()), "duplicate {event}");
        }
        assert_eq!(seen.len(), 17);
    }

    #[test]
    fn journal_event_wire_strings_match_serde() {
        for event in JournalEvent::ALL {
            let json = serde_json::to_string(&event).expect("serialize");
            assert_eq!(json, format!("\"{}\"", event.as_str()));
            let back: JournalEvent = serde_json::from_str(&json).expect("roundtrip");
            assert_eq!(back, event);
        }
    }

    #[test]
    fn journal_event_display_matches_as_str() {
        for event in JournalEvent::ALL {
            assert_eq!(event.to_string(), event.as_str());
        }
    }

    #[test]
    fn error_code_wire_strings_match_serde_and_display() {
        let all = [
            ErrorCode::NetworkUnavailable,
            ErrorCode::ManifestHttpStatus,
            ErrorCode::ManifestMalformed,
            ErrorCode::ManifestFieldInvalid,
            ErrorCode::ManifestSchemaUnsupported,
            ErrorCode::ManifestHostNotAllowed,
            ErrorCode::PlatformUnsupported,
            ErrorCode::DownloadFailed,
            ErrorCode::StageWriteFailed,
            ErrorCode::SignatureRejected,
            ErrorCode::SignatureKeyMissing,
            ErrorCode::InstallFailed,
            ErrorCode::JournalWriteFailed,
            ErrorCode::BeaconFailed,
            ErrorCode::SidecarStillRunning,
            ErrorCode::ConsentVersionMismatch,
        ];
        let mut seen = std::collections::BTreeSet::new();
        for code in all {
            assert!(seen.insert(code.as_str()), "duplicate {code}");
            assert_eq!(code.to_string(), code.as_str());
            let json = serde_json::to_string(&code).expect("serialize");
            assert_eq!(json, format!("\"{}\"", code.as_str()));
            let back: ErrorCode = serde_json::from_str(&json).expect("roundtrip");
            assert_eq!(back, code);
        }
        assert_eq!(seen.len(), 16);
    }

    #[test]
    fn state_kind_wire_strings_are_distinct() {
        let all = [
            StateKind::Frozen,
            StateKind::Idle,
            StateKind::Checking,
            StateKind::UpToDate,
            StateKind::Downloading,
            StateKind::Staged,
            StateKind::Skipped,
            StateKind::Installing,
            StateKind::Failed,
        ];
        let mut seen = std::collections::BTreeSet::new();
        for kind in all {
            assert!(seen.insert(kind.as_str()), "duplicate {}", kind.as_str());
            let json = serde_json::to_string(&kind).expect("serialize");
            assert_eq!(json, format!("\"{}\"", kind.as_str()));
        }
        assert_eq!(seen.len(), 9);
        assert_eq!(UPDATE_STATE_EVENT, "rytm-update-state");
    }

    #[test]
    fn detail_key_wire_strings_are_distinct() {
        let all = [
            DetailKey::Reason,
            DetailKey::Bytes,
            DetailKey::DurationMs,
            DetailKey::Bucket,
            DetailKey::RolloutPercent,
            DetailKey::HardwareRevalidation,
            DetailKey::HttpStatus,
        ];
        let mut seen = std::collections::BTreeSet::new();
        for key in all {
            assert!(seen.insert(key.as_str()));
        }
        assert_eq!(seen.len(), 7);
    }

    #[test]
    fn detail_value_conversions_cover_every_variant() {
        assert_eq!(
            DetailValue::from(ErrorCode::DownloadFailed),
            DetailValue::Reason(ErrorCode::DownloadFailed)
        );
        assert_eq!(DetailValue::from(7_u64), DetailValue::Number(7));
        assert_eq!(DetailValue::from(true), DetailValue::Flag(true));
    }

    // -- bucketing -----------------------------------------------------

    #[test]
    fn bucket_is_first_four_sha256_bytes_mod_100() {
        let id = "abc";
        let digest = Sha256::digest(id.as_bytes());
        let expected =
            u32::from_be_bytes([digest[0], digest[1], digest[2], digest[3]]) % ROLLOUT_BUCKET_COUNT;
        assert_eq!(rollout_bucket(id), expected);
    }

    #[test]
    fn bucket_is_stable_and_in_range() {
        for n in 0..500 {
            let id = format!("install-{n}");
            let bucket = rollout_bucket(&id);
            assert!(bucket < ROLLOUT_BUCKET_COUNT);
            assert_eq!(bucket, rollout_bucket(&id));
        }
    }

    #[test]
    fn rollout_percentage_steps_are_supersets() {
        let ids: Vec<String> = (0..300).map(|n| format!("install-{n}")).collect();
        for id in &ids {
            for percent in 0..ROLLOUT_BUCKET_COUNT {
                if rollout_admits(id, percent) {
                    assert!(
                        rollout_admits(id, percent + 1),
                        "raising the rollout must never drop an install"
                    );
                }
            }
        }
    }

    #[test]
    fn rollout_zero_admits_nobody_and_hundred_admits_everybody() {
        for n in 0..200 {
            let id = format!("install-{n}");
            assert!(!rollout_admits(&id, 0));
            assert!(rollout_admits(&id, ROLLOUT_BUCKET_COUNT));
        }
    }

    #[test]
    fn install_id_zero_is_low_bucket() {
        // Guards the fixture used by `config()`: if the hash ever changed,
        // the happy-path tests would silently become bucket-exclusion tests.
        assert!(rollout_bucket("bucket-zero-install") < ROLLOUT_BUCKET_COUNT);
    }

    /// The canonical rollout-bucketing vectors, orchestrator-verified against
    /// an independent Python implementation of spec §5's rule (first 4 bytes
    /// of `SHA-256(install_id)` as big-endian `u32`, mod 100).
    ///
    /// These are hardcoded deliberately. The I3 fixture corpus
    /// (`tests/fixtures/update_manifest/bucket_vectors.json`) is authored in
    /// parallel by another agent, so it may not exist on this branch — and a
    /// cross-language contract that only binds *when the other side has
    /// landed* is not a contract. This test binds unconditionally; the
    /// fixture test below binds additionally once the file arrives, and the
    /// two must agree.
    const CANONICAL_BUCKET_VECTORS: [(&str, u32); 6] = [
        ("00000000-0000-4000-8000-000000000000", 96),
        ("11111111-1111-4111-8111-111111111111", 25),
        ("550e8400-e29b-41d4-a716-446655440000", 29),
        ("f47ac10b-58cc-4372-a567-0e02b2c3d479", 1),
        ("6ba7b810-9dad-11d1-80b4-00c04fd430c8", 16),
        ("3f2504e0-4f89-41d3-9a0c-0305e82c3301", 14),
    ];

    #[test]
    fn bucketing_reproduces_the_canonical_cross_language_vectors() {
        for (install_id, expected) in CANONICAL_BUCKET_VECTORS {
            assert_eq!(
                rollout_bucket(install_id),
                expected,
                "bucket mismatch for {install_id}"
            );
        }
    }

    /// A vector's bucket is also its exact admission boundary: an install
    /// with bucket B is admitted at `rollout_percent = B + 1` and excluded at
    /// `B`. This pins the `<` in `bucket < rollout_percent` (spec §5) rather
    /// than a `<=` that would shift every rollout step by one percent.
    #[test]
    fn each_canonical_vector_sits_exactly_on_its_admission_boundary() {
        for (install_id, bucket) in CANONICAL_BUCKET_VECTORS {
            assert!(
                !rollout_admits(install_id, bucket),
                "{install_id} must be excluded at rollout_percent == its bucket"
            );
            assert!(
                rollout_admits(install_id, bucket + 1),
                "{install_id} must be admitted at rollout_percent == bucket + 1"
            );
        }
    }

    #[test]
    fn bucket_vectors_fixture_matches_when_present() {
        // Contract I3 corpus (authored in parallel by A5). When the file is
        // absent the test is a no-op; when it lands it becomes binding.
        let path = fixture_dir().join("bucket_vectors.json");
        let Ok(body) = std::fs::read_to_string(&path) else {
            return;
        };
        let vectors: serde_json::Value = serde_json::from_str(&body).expect("bucket vectors JSON");
        let entries = vectors
            .as_array()
            .cloned()
            .or_else(|| vectors.get("vectors").and_then(|v| v.as_array()).cloned())
            .expect("bucket vectors is an array or {vectors: [...]}");
        for entry in entries {
            let id = entry
                .get("install_id")
                .and_then(serde_json::Value::as_str)
                .expect("install_id");
            let expected = entry
                .get("bucket")
                .and_then(serde_json::Value::as_u64)
                .expect("bucket") as u32;
            assert_eq!(rollout_bucket(id), expected, "bucket mismatch for {id}");
        }
    }

    fn fixture_dir() -> std::path::PathBuf {
        std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../tests/fixtures/update_manifest")
    }

    #[test]
    fn fixture_corpus_is_accepted_and_rejected_as_declared() {
        let dir = fixture_dir();
        let valid = dir.join("manifest.v1.json");
        if let Ok(body) = std::fs::read_to_string(&valid) {
            let parsed: Manifest = serde_json::from_str(&body).expect("valid fixture parses");
            let target = parsed
                .platforms
                .keys()
                .next()
                .cloned()
                .expect("valid fixture declares a platform");
            validate_manifest(&body, &target).expect("manifest.v1.json must be accepted");
        }
        let invalid_dir = dir.join("invalid");
        if let Ok(entries) = std::fs::read_dir(&invalid_dir) {
            let mut checked = 0_usize;
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|e| e.to_str()) != Some("json") {
                    continue;
                }
                let body = std::fs::read_to_string(&path).expect("read invalid fixture");
                assert!(
                    validate_manifest(&body, TARGET).is_err()
                        && validate_manifest(&body, "linux-x86_64").is_err(),
                    "invalid fixture was accepted: {:?}",
                    path.file_name()
                );
                checked += 1;
            }
            assert!(checked > 0, "invalid/ exists but held no JSON fixtures");
        }
    }

    // -- manifest validation -------------------------------------------

    #[test]
    fn valid_manifest_is_accepted() {
        let manifest = validate_manifest(&manifest_json("1.35.0", 50), TARGET).expect("accepted");
        assert_eq!(manifest.version(), "1.35.0");
        assert_eq!(manifest.notes(), "notes for 1.35.0");
        assert!(!manifest.hardware_revalidation());
        assert_eq!(manifest.rollout_percent(), 50);
        assert_eq!(manifest.target(), TARGET);
        assert_eq!(manifest.minimum_version(), None);
        assert_eq!(manifest.platform_entry().signature, "c2ln");
    }

    #[test]
    fn minimum_version_is_carried_but_advisory() {
        let body = r#"{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":100,
            "minimum_version":"1.30.0",
            "platforms":{"darwin-aarch64":{"signature":"s","url":"https://github.com/o/r/releases/download/v1/a"}}}"#;
        let manifest = validate_manifest(body, TARGET).expect("accepted");
        assert_eq!(manifest.minimum_version(), Some("1.30.0"));
    }

    #[test]
    fn malformed_json_is_rejected() {
        assert_eq!(
            validate_manifest("{not json", TARGET).unwrap_err(),
            ErrorCode::ManifestMalformed
        );
    }

    #[test]
    fn unsupported_schema_version_is_rejected() {
        let body =
            manifest_json("1.35.0", 100).replace("\"schema_version\": 1", "\"schema_version\": 2");
        assert_eq!(
            validate_manifest(&body, TARGET).unwrap_err(),
            ErrorCode::ManifestSchemaUnsupported
        );
    }

    #[test]
    fn rollout_percent_above_hundred_is_rejected() {
        assert_eq!(
            validate_manifest(&manifest_json("1.35.0", 101), TARGET).unwrap_err(),
            ErrorCode::ManifestFieldInvalid
        );
    }

    #[test]
    fn blank_and_oversized_and_odd_versions_are_rejected() {
        for version in ["", "v1.2.3", "-beta", &"1".repeat(MAX_VERSION_BYTES + 1)] {
            let body = format!(
                r#"{{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"{version}","rollout_percent":10,
                  "platforms":{{"darwin-aarch64":{{"signature":"s","url":"https://github.com/o/r/releases/download/v1/a"}}}}}}"#
            );
            assert_eq!(
                validate_manifest(&body, TARGET).unwrap_err(),
                ErrorCode::ManifestFieldInvalid,
                "version {version:?} should be rejected"
            );
        }
    }

    #[test]
    fn invalid_minimum_version_is_rejected() {
        let body = r#"{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
            "minimum_version":"nope",
            "platforms":{"darwin-aarch64":{"signature":"s","url":"https://github.com/o/r/releases/download/v1/a"}}}"#;
        assert_eq!(
            validate_manifest(body, TARGET).unwrap_err(),
            ErrorCode::ManifestFieldInvalid
        );
    }

    #[test]
    fn oversized_notes_are_rejected() {
        let notes = "n".repeat(MAX_NOTES_BYTES + 1);
        let body = format!(
            r#"{{"schema_version":1,"channel":"stable","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","notes":"{notes}","rollout_percent":10,
              "platforms":{{"darwin-aarch64":{{"signature":"s","url":"https://github.com/o/r/releases/download/v1/a"}}}}}}"#
        );
        assert_eq!(
            validate_manifest(&body, TARGET).unwrap_err(),
            ErrorCode::ManifestFieldInvalid
        );
    }

    #[test]
    fn empty_platform_map_is_rejected() {
        let body = r#"{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,"platforms":{}}"#;
        assert_eq!(
            validate_manifest(body, TARGET).unwrap_err(),
            ErrorCode::ManifestFieldInvalid
        );
    }

    #[test]
    fn blank_signature_is_rejected() {
        let body = r#"{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
            "platforms":{"darwin-aarch64":{"signature":"   ","url":"https://github.com/o/r/releases/download/v1/a"}}}"#;
        assert_eq!(
            validate_manifest(body, TARGET).unwrap_err(),
            ErrorCode::ManifestFieldInvalid
        );
    }

    #[test]
    fn missing_platform_entry_is_rejected() {
        assert_eq!(
            validate_manifest(&manifest_json("1.35.0", 100), "windows-x86_64").unwrap_err(),
            ErrorCode::PlatformUnsupported
        );
    }

    #[test]
    fn host_pinning_rejects_every_bypass_shape() {
        let bad_urls = [
            "http://github.com/a",               // wrong scheme
            "https://evil.example/a",            // wrong host
            "https://github.com.evil.example/a", // suffix trick
            "https://github.com@evil.example/a", // userinfo trick
            "https://github.com:8443/a",         // explicit port
            "https:///a",                        // empty authority
            "ftp://github.com/a",                // non-http scheme
            "//github.com/a",                    // scheme-relative
        ];
        for url in bad_urls {
            let body = format!(
                r#"{{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
                  "platforms":{{"darwin-aarch64":{{"signature":"s","url":"{url}"}}}}}}"#
            );
            assert_eq!(
                validate_manifest(&body, TARGET).unwrap_err(),
                ErrorCode::ManifestHostNotAllowed,
                "url {url} should be rejected"
            );
        }
    }

    #[test]
    fn host_pinning_accepts_every_allowed_host_case_insensitively() {
        for host in ALLOWED_ARTIFACT_HOSTS {
            for candidate in [host.to_string(), host.to_ascii_uppercase()] {
                // `github.com` additionally carries the release-download path
                // pin; the CDN hosts serve opaque redirect targets and do not.
                let path = if candidate.eq_ignore_ascii_case("github.com") {
                    "/o/r/releases/download/v1/a?x=1#y"
                } else {
                    "/a?x=1#y"
                };
                let body = format!(
                    r#"{{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
                      "platforms":{{"darwin-aarch64":{{"signature":"s","url":"https://{candidate}{path}"}}}}}}"#
                );
                validate_manifest(&body, TARGET).expect("allowed host accepted");
            }
        }
        // A CDN host with no path at all is fine (exercises the
        // no-delimiter arm of the authority scan).
        let body = r#"{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
            "platforms":{"darwin-aarch64":{"signature":"s","url":"https://objects.githubusercontent.com"}}}"#;
        validate_manifest(body, TARGET).expect("bare CDN host accepted");
    }

    /// Spec §4 pins the path, not just the host: the artifact URL must be
    /// `https://github.com/<owner>/<repo>/releases/download/…`. Host-only
    /// pinning would still admit any other file served from github.com — a
    /// Pages site, a raw file in an attacker's fork, a gist — all of which
    /// share the origin an attacker who rewrote the manifest could reach.
    #[test]
    fn a_github_url_outside_releases_download_is_refused() {
        for path in [
            "",                                 // bare host
            "/",                                // root
            "/o/r",                             // a repo page
            "/o/r/raw/main/evil.tar.gz",        // a raw file in any fork
            "/o/r/releases/tag/v1",             // the tag page, not the asset
            "/o/r/archive/refs/heads/main.zip", // a source archive
        ] {
            let body = format!(
                r#"{{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
                  "platforms":{{"darwin-aarch64":{{"signature":"s","url":"https://github.com{path}"}}}}}}"#
            );
            assert_eq!(
                validate_manifest(&body, TARGET).unwrap_err(),
                ErrorCode::ManifestHostNotAllowed,
                "github.com{path} must be refused"
            );
        }
        // The one accepted shape.
        let body = r#"{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
            "platforms":{"darwin-aarch64":{"signature":"s",
            "url":"https://github.com/o/r/releases/download/v1.35.0/app.tar.gz"}}}"#;
        validate_manifest(body, TARGET).expect("a real release asset URL is accepted");
    }

    #[test]
    fn an_off_host_entry_for_another_platform_still_rejects() {
        let body = r#"{"schema_version":1,"channel":"stable","notes":"n","pub_date":"2026-01-01T00:00:00Z","hardware_revalidation":false,"version":"1.35.0","rollout_percent":10,
            "platforms":{
              "darwin-aarch64":{"signature":"s","url":"https://github.com/o/r/releases/download/v1/a"},
              "linux-x86_64":{"signature":"s","url":"https://evil.example/a"}}}"#;
        assert_eq!(
            validate_manifest(body, TARGET).unwrap_err(),
            ErrorCode::ManifestHostNotAllowed
        );
    }

    // -- version comparison --------------------------------------------

    #[test]
    fn version_comparison_orders_releases_and_prereleases() {
        assert!(version_is_newer("1.35.0", "1.34.0"));
        assert!(version_is_newer("1.34.1", "1.34.0"));
        assert!(version_is_newer("2.0.0", "1.99.99"));
        assert!(!version_is_newer("1.34.0", "1.34.0"));
        assert!(!version_is_newer("1.33.9", "1.34.0"));
        // A release outranks its own pre-release; a pre-release does not
        // outrank the finished release.
        assert!(version_is_newer("1.35.0", "1.35.0-beta.1"));
        assert!(!version_is_newer("1.35.0-beta.1", "1.35.0"));
        // Build metadata does not change ordering.
        assert!(!version_is_newer("1.34.0+abc", "1.34.0"));
        // Non-numeric components degrade to zero rather than panicking.
        assert!(!version_is_newer("1.x.0", "1.0.0"));
    }

    // -- freeze mode ----------------------------------------------------

    #[test]
    fn freeze_short_circuits_every_event_with_zero_network_effects() {
        let mut cfg = config();
        cfg.updates_enabled = false;
        cfg.beacon_enabled = true;
        let events: Vec<UpdateEvent> = vec![
            UpdateEvent::CheckRequested,
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 100),
                duration_ms: 1,
            },
            UpdateEvent::ManifestFetchFailed {
                code: ErrorCode::NetworkUnavailable,
            },
            UpdateEvent::DownloadStaged {
                version: "1.35.0".into(),
                bytes: 1,
                duration_ms: 1,
            },
            UpdateEvent::DownloadFailed {
                version: "1.35.0".into(),
                code: ErrorCode::DownloadFailed,
            },
            UpdateEvent::SignatureRejected {
                version: "1.35.0".into(),
            },
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::RestartAndInstall,
            },
            UpdateEvent::SkipRequested {
                version: "1.35.0".into(),
            },
            UpdateEvent::SidecarExited,
            UpdateEvent::QuitWithoutSidecarExit,
            UpdateEvent::InstallSucceeded {
                version: "1.35.0".into(),
            },
            UpdateEvent::InstallFailed {
                version: "1.35.0".into(),
                code: ErrorCode::InstallFailed,
            },
            UpdateEvent::BeaconCompleted { ok: true },
        ];
        for event in events {
            // Start from a state that WOULD have installed, to prove freeze
            // beats an already-consented pending install.
            let mut state = UpdateState::initial(&config());
            state.staged = true;
            state.version = Some("1.35.0".to_string());
            state.pending_install = Some(ConsentToken::mint(
                "1.35.0".to_string(),
                ConsentChoice::InstallOnQuit,
            ));
            let transition = step(state, event, &cfg);
            assert!(
                !transition.has_network_effect(),
                "freeze mode emitted a network effect"
            );
            assert!(
                !transition.has_install_effect(),
                "freeze mode emitted an install effect"
            );
            assert_eq!(transition.state.kind(), StateKind::Frozen);
            assert!(transition.effects.iter().any(|e| matches!(
                e,
                Effect::Journal(JournalRecord {
                    event: JournalEvent::FreezeSuppressed,
                    ..
                })
            )));
        }
    }

    #[test]
    fn initial_state_is_frozen_when_updates_disabled() {
        let mut cfg = config();
        cfg.updates_enabled = false;
        let state = UpdateState::initial(&cfg);
        assert_eq!(state.kind(), StateKind::Frozen);
        assert_eq!(state.payload().state, StateKind::Frozen);
        assert!(!state.is_staged());
        assert_eq!(state.version(), None);
        assert_eq!(state.pending_quit_install(), None);
    }

    // -- check / manifest flow ------------------------------------------

    #[test]
    fn check_requested_emits_fetch_and_check_started() {
        let cfg = config();
        let transition = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Checking);
        assert_eq!(
            transition.effects[0],
            Effect::Journal(JournalRecord::new(JournalEvent::CheckStarted, None))
        );
        assert_eq!(
            transition.effects[1],
            Effect::FetchManifest {
                channel: "stable".to_string()
            }
        );
    }

    #[test]
    fn check_requested_is_a_noop_while_staged() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let transition = step(staged, UpdateEvent::CheckRequested, &cfg);
        assert!(!transition.has_network_effect());
        assert_eq!(transition.state.kind(), StateKind::Staged);
        assert_eq!(transition.effects.len(), 1); // just the state re-emit
    }

    #[test]
    fn check_requested_is_a_noop_while_an_install_is_pending() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let consented = step(
            staged,
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::InstallOnQuit,
            },
            &cfg,
        )
        .state;
        let transition = step(consented, UpdateEvent::CheckRequested, &cfg);
        assert!(!transition.has_network_effect());
    }

    #[test]
    fn newer_version_starts_a_download() {
        let cfg = config();
        let state = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        )
        .state;
        let transition = step(
            state,
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 100),
                duration_ms: 21,
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Downloading);
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::DownloadArtifact { version, .. } if version == "1.35.0"
        )));
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(JournalRecord {
                event: JournalEvent::DownloadStarted,
                ..
            })
        )));
        assert_eq!(
            transition.state.payload().notes.as_deref(),
            Some("notes for 1.35.0")
        );
    }

    #[test]
    fn same_or_older_version_reports_up_to_date() {
        let cfg = config();
        for version in ["1.34.0", "1.33.0"] {
            let state = step(
                UpdateState::initial(&cfg),
                UpdateEvent::CheckRequested,
                &cfg,
            )
            .state;
            let transition = step(
                state,
                UpdateEvent::ManifestFetched {
                    body: manifest_json(version, 100),
                    duration_ms: 3,
                },
                &cfg,
            );
            assert_eq!(transition.state.kind(), StateKind::UpToDate);
            assert!(!transition
                .effects
                .iter()
                .any(|e| matches!(e, Effect::DownloadArtifact { .. })));
        }
    }

    #[test]
    fn hardware_revalidation_flag_reaches_the_payload_and_the_journal() {
        let cfg = config();
        let body = manifest_json("1.35.0", 100).replace(
            "\"hardware_revalidation\": false",
            "\"hardware_revalidation\": true",
        );
        let state = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        )
        .state;
        let transition = step(
            state,
            UpdateEvent::ManifestFetched {
                body,
                duration_ms: 1,
            },
            &cfg,
        );
        assert!(transition.state.payload().hardware_revalidation);
        let check_ok = transition
            .effects
            .iter()
            .find_map(|e| match e {
                Effect::Journal(record) if record.event == JournalEvent::CheckOk => Some(record),
                _ => None,
            })
            .expect("check_ok row");
        assert_eq!(
            check_ok.detail.get(&DetailKey::HardwareRevalidation),
            Some(&DetailValue::Flag(true))
        );
    }

    #[test]
    fn rejected_manifest_journals_manifest_rejected_and_fails() {
        let cfg = config();
        let state = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        )
        .state;
        let transition = step(
            state,
            UpdateEvent::ManifestFetched {
                body: "{".to_string(),
                duration_ms: 1,
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Failed);
        assert_eq!(
            transition.state.payload().error_code,
            Some(ErrorCode::ManifestMalformed)
        );
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(JournalRecord {
                event: JournalEvent::ManifestRejected,
                ..
            })
        )));
        assert!(!transition.has_network_effect());
    }

    #[test]
    fn manifest_fetch_failure_journals_check_failed() {
        let cfg = config();
        let state = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        )
        .state;
        let transition = step(
            state,
            UpdateEvent::ManifestFetchFailed {
                code: ErrorCode::NetworkUnavailable,
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Failed);
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(JournalRecord {
                event: JournalEvent::CheckFailed,
                ..
            })
        )));
    }

    // -- bucketing in the flow ------------------------------------------

    #[test]
    fn a_high_bucket_install_is_excluded_and_journals_bucket_excluded() {
        let mut cfg = config();
        cfg.install_id = high_bucket_id();
        let state = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        )
        .state;
        let transition = step(
            state,
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 10),
                duration_ms: 1,
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::UpToDate);
        assert!(!transition
            .effects
            .iter()
            .any(|e| matches!(e, Effect::DownloadArtifact { .. })));
        let row = transition
            .effects
            .iter()
            .find_map(|e| match e {
                Effect::Journal(r) if r.event == JournalEvent::BucketExcluded => Some(r),
                _ => None,
            })
            .expect("bucket_excluded row");
        assert_eq!(
            row.detail.get(&DetailKey::RolloutPercent),
            Some(&DetailValue::Number(10))
        );
    }

    #[test]
    fn a_low_bucket_install_is_admitted_at_one_percent() {
        let mut cfg = config();
        cfg.install_id = low_bucket_id();
        let state = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        )
        .state;
        let transition = step(
            state,
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 1),
                duration_ms: 1,
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Downloading);
    }

    // -- download / stage -----------------------------------------------

    #[test]
    fn staging_moves_to_staged_and_journals_bytes_and_duration() {
        let cfg = config();
        let state = staged_state(&cfg, "1.35.0");
        assert_eq!(state.kind(), StateKind::Staged);
        assert!(state.is_staged());
    }

    #[test]
    fn staging_a_version_we_are_not_downloading_is_ignored() {
        let cfg = config();
        let state = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        )
        .state;
        let transition = step(
            state,
            UpdateEvent::DownloadStaged {
                version: "9.9.9".into(),
                bytes: 1,
                duration_ms: 1,
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Checking);
        assert!(!transition.state.is_staged());
        assert_eq!(transition.effects.len(), 1);
    }

    /// Spec §5 has exactly two failure arms out of the acquire branch:
    /// `manifest invalid/unreachable -> check_failed` and `sig/IO fail ->
    /// stage_failed`. Both a mid-flight transport failure and a staging-write
    /// failure are on the second arm, so both journal `stage_failed` and are
    /// told apart by the typed reason — never by reusing `check_failed`,
    /// which would make a dead artifact URL read as an unreachable manifest.
    #[test]
    fn every_download_arm_failure_journals_stage_failed_with_its_own_reason() {
        let cfg = config();
        for code in [ErrorCode::DownloadFailed, ErrorCode::StageWriteFailed] {
            let transition = step(
                downloading_state(&cfg, "1.35.0"),
                UpdateEvent::DownloadFailed {
                    version: "1.35.0".into(),
                    code,
                },
                &cfg,
            );
            assert_eq!(transition.state.kind(), StateKind::Failed);
            assert!(!transition.state.is_staged());
            let row = transition
                .effects
                .iter()
                .find_map(|e| match e {
                    Effect::Journal(r) => Some(r),
                    _ => None,
                })
                .expect("a journal row");
            assert_eq!(row.event, JournalEvent::StageFailed);
            assert_eq!(
                row.detail.get(&DetailKey::Reason),
                Some(&DetailValue::Reason(code)),
                "the reason, not the event, is what distinguishes the two"
            );
            assert_ne!(
                row.event,
                JournalEvent::CheckFailed,
                "check_failed is the manifest arm only"
            );
        }
    }

    #[test]
    fn signature_rejection_fails_and_never_stages() {
        let cfg = config();
        let state = staged_state(&cfg, "1.35.0");
        let transition = step(
            state,
            UpdateEvent::SignatureRejected {
                version: "1.35.0".into(),
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Failed);
        assert!(!transition.state.is_staged());
        assert_eq!(
            transition.state.payload().error_code,
            Some(ErrorCode::SignatureRejected)
        );
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(r) if r.event == JournalEvent::SignatureRejected
        )));
    }

    // -- consent --------------------------------------------------------

    #[test]
    fn consent_for_the_staged_version_queues_but_does_not_install_yet() {
        let cfg = config();
        for choice in [
            ConsentChoice::RestartAndInstall,
            ConsentChoice::InstallOnQuit,
        ] {
            let staged = staged_state(&cfg, "1.35.0");
            let transition = step(
                staged,
                UpdateEvent::ConsentGranted {
                    version: "1.35.0".into(),
                    choice,
                },
                &cfg,
            );
            // The install effect is NEVER emitted before the sidecar exits.
            assert!(!transition.has_install_effect());
            assert_eq!(transition.state.pending_quit_install(), Some("1.35.0"));
            assert!(transition.effects.iter().any(|e| matches!(
                e,
                Effect::Journal(r) if r.event == JournalEvent::ConsentGranted
            )));
        }
    }

    #[test]
    fn consent_for_a_different_version_is_refused() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let transition = step(
            staged,
            UpdateEvent::ConsentGranted {
                version: "1.36.0".into(),
                choice: ConsentChoice::RestartAndInstall,
            },
            &cfg,
        );
        assert!(!transition.has_install_effect());
        assert_eq!(
            transition.state.payload().error_code,
            Some(ErrorCode::ConsentVersionMismatch)
        );
        assert_eq!(transition.state.pending_quit_install(), None);
    }

    #[test]
    fn consent_without_a_staged_artifact_is_refused() {
        let cfg = config();
        let transition = step(
            UpdateState::initial(&cfg),
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::RestartAndInstall,
            },
            &cfg,
        );
        assert!(!transition.has_install_effect());
        assert_eq!(
            transition.state.payload().error_code,
            Some(ErrorCode::ConsentVersionMismatch)
        );
    }

    #[test]
    fn a_consent_token_is_bound_to_one_version_and_is_single_use() {
        let token = ConsentToken::mint("1.35.0".to_string(), ConsentChoice::InstallOnQuit);
        assert_eq!(token.version(), "1.35.0");
        assert_eq!(token.choice(), ConsentChoice::InstallOnQuit);
        // `into_install_effect` takes `self` by value, so the effect it
        // produces names exactly the token's version and the token is gone.
        let effect = token.into_install_effect();
        match effect {
            Effect::InstallStagedUpdate(auth) => {
                assert_eq!(auth.version(), "1.35.0");
                assert_eq!(auth.choice(), ConsentChoice::InstallOnQuit);
            }
            other => panic!("expected an install effect, got {other:?}"),
        }
    }

    /// The §1 invariant, asserted structurally rather than behaviourally.
    ///
    /// `Effect::InstallStagedUpdate` wraps an `InstallAuthorisation` whose
    /// fields are private, so this module is the only place that can build
    /// one — and within this module the only builder is
    /// `ConsentToken::into_install_effect`. This test pins the *source-level*
    /// fact that `into_install_effect` is the sole construction site, so a
    /// future edit that adds a second one fails here instead of silently
    /// re-opening the hole. (A grep-shaped assertion is the honest tool: the
    /// compiler already stops out-of-module construction; what it cannot stop
    /// is an in-module shortcut.)
    #[test]
    fn install_effects_are_constructed_in_exactly_one_place() {
        let source = include_str!("update_policy.rs");
        // Assembled at runtime so this test's own source is not a match.
        let needle = format!("Effect::InstallStagedUpdate({}", "InstallAuthorisation");
        let sites = source.matches(needle.as_str()).count();
        assert_eq!(
            sites, 1,
            "Effect::InstallStagedUpdate must be constructed only by \
             ConsentToken::into_install_effect; found {sites} construction sites"
        );
    }

    #[test]
    fn consent_choice_roundtrips_on_the_wire() {
        for choice in [
            ConsentChoice::RestartAndInstall,
            ConsentChoice::InstallOnQuit,
        ] {
            let json = serde_json::to_string(&choice).expect("serialize");
            let back: ConsentChoice = serde_json::from_str(&json).expect("roundtrip");
            assert_eq!(back, choice);
        }
    }

    // -- install-on-quit ordering ---------------------------------------

    #[test]
    fn install_runs_only_after_the_sidecar_confirms_exit() {
        let cfg = config();
        for choice in [
            ConsentChoice::RestartAndInstall,
            ConsentChoice::InstallOnQuit,
        ] {
            let staged = staged_state(&cfg, "1.35.0");
            let consented = step(
                staged,
                UpdateEvent::ConsentGranted {
                    version: "1.35.0".into(),
                    choice,
                },
                &cfg,
            )
            .state;
            let transition = step(consented, UpdateEvent::SidecarExited, &cfg);
            assert_eq!(
                transition
                    .effects
                    .iter()
                    .filter(|e| matches!(
                        e,
                        Effect::InstallStagedUpdate(auth)
                            if auth.version() == "1.35.0" && auth.choice() == choice
                    ))
                    .count(),
                1
            );
            assert!(transition.effects.iter().any(|e| matches!(
                e,
                Effect::Journal(r) if r.event == JournalEvent::InstallStarted
            )));
            assert_eq!(transition.state.kind(), StateKind::Installing);
        }
    }

    #[test]
    fn quitting_with_the_sidecar_still_alive_never_installs() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let consented = step(
            staged,
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::InstallOnQuit,
            },
            &cfg,
        )
        .state;
        let transition = step(consented, UpdateEvent::QuitWithoutSidecarExit, &cfg);
        assert!(!transition.has_install_effect());
        assert_eq!(
            transition.state.payload().error_code,
            Some(ErrorCode::SidecarStillRunning)
        );
    }

    #[test]
    fn sidecar_exit_without_consent_installs_nothing() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let transition = step(staged, UpdateEvent::SidecarExited, &cfg);
        assert!(!transition.has_install_effect());
        assert_eq!(transition.effects.len(), 1);
    }

    #[test]
    fn quit_without_consent_installs_nothing() {
        let cfg = config();
        let transition = step(
            UpdateState::initial(&cfg),
            UpdateEvent::QuitWithoutSidecarExit,
            &cfg,
        );
        assert!(!transition.has_install_effect());
        assert_eq!(transition.effects.len(), 1);
    }

    #[test]
    fn a_crash_after_consent_does_not_auto_install_on_next_start() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let consented = step(
            staged,
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::InstallOnQuit,
            },
            &cfg,
        )
        .state;
        assert_eq!(consented.pending_quit_install(), Some("1.35.0"));
        // A crash means the process dies: the next start builds a brand-new
        // initial state, which carries no consent and no pending install.
        let restarted = UpdateState::initial(&cfg);
        assert_eq!(restarted.pending_quit_install(), None);
        assert!(!restarted.is_staged());
        let transition = step(restarted, UpdateEvent::SidecarExited, &cfg);
        assert!(!transition.has_install_effect());
    }

    // -- skip -----------------------------------------------------------

    #[test]
    fn skip_records_the_version_and_clears_the_chip() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let transition = step(
            staged,
            UpdateEvent::SkipRequested {
                version: "1.35.0".into(),
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Skipped);
        assert!(!transition.state.is_staged());
        assert!(transition.state.is_skipped("1.35.0"));
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(r) if r.event == JournalEvent::SkipRecorded
        )));
    }

    #[test]
    fn skip_cancels_a_pending_install() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let consented = step(
            staged,
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::InstallOnQuit,
            },
            &cfg,
        )
        .state;
        let skipped = step(
            consented,
            UpdateEvent::SkipRequested {
                version: "1.35.0".into(),
            },
            &cfg,
        )
        .state;
        assert_eq!(skipped.pending_quit_install(), None);
        let transition = step(skipped, UpdateEvent::SidecarExited, &cfg);
        assert!(!transition.has_install_effect());
    }

    #[test]
    fn skipping_twice_records_once_and_skipping_another_version_leaves_state_alone() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let once = step(
            staged,
            UpdateEvent::SkipRequested {
                version: "1.35.0".into(),
            },
            &cfg,
        )
        .state;
        let twice = step(
            once,
            UpdateEvent::SkipRequested {
                version: "1.35.0".into(),
            },
            &cfg,
        )
        .state;
        assert!(twice.is_skipped("1.35.0"));
        let other = step(
            twice,
            UpdateEvent::SkipRequested {
                version: "1.36.0".into(),
            },
            &cfg,
        )
        .state;
        assert!(other.is_skipped("1.36.0"));
        assert_eq!(other.kind(), StateKind::Skipped);
    }

    #[test]
    fn a_skipped_version_is_not_re_downloaded_but_a_newer_one_is() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let skipped = step(
            staged,
            UpdateEvent::SkipRequested {
                version: "1.35.0".into(),
            },
            &cfg,
        )
        .state;
        let checking = step(skipped, UpdateEvent::CheckRequested, &cfg).state;
        let same = step(
            checking,
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 100),
                duration_ms: 1,
            },
            &cfg,
        );
        assert_eq!(same.state.kind(), StateKind::Skipped);
        assert!(!same
            .effects
            .iter()
            .any(|e| matches!(e, Effect::DownloadArtifact { .. })));

        let checking = step(same.state, UpdateEvent::CheckRequested, &cfg).state;
        let newer = step(
            checking,
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.36.0", 100),
                duration_ms: 1,
            },
            &cfg,
        );
        assert_eq!(newer.state.kind(), StateKind::Downloading);
    }

    // -- install outcomes -------------------------------------------------

    #[test]
    fn install_success_journals_install_ok_and_clears_the_pending_install() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let transition = step(
            staged,
            UpdateEvent::InstallSucceeded {
                version: "1.35.0".into(),
            },
            &cfg,
        );
        assert_eq!(transition.state.pending_quit_install(), None);
        assert!(!transition.state.is_staged());
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(r) if r.event == JournalEvent::InstallOk
        )));
    }

    #[test]
    fn install_failure_journals_install_failed_with_a_typed_reason() {
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let transition = step(
            staged,
            UpdateEvent::InstallFailed {
                version: "1.35.0".into(),
                code: ErrorCode::InstallFailed,
            },
            &cfg,
        );
        assert_eq!(transition.state.kind(), StateKind::Failed);
        assert_eq!(
            transition.state.payload().error_code,
            Some(ErrorCode::InstallFailed)
        );
        let row = transition
            .effects
            .iter()
            .find_map(|e| match e {
                Effect::Journal(r) if r.event == JournalEvent::InstallFailed => Some(r),
                _ => None,
            })
            .expect("install_failed row");
        assert_eq!(
            row.detail.get(&DetailKey::Reason),
            Some(&DetailValue::Reason(ErrorCode::InstallFailed))
        );
    }

    // -- no compiled-in key: check-and-notify only -------------------------

    #[test]
    fn without_a_signing_key_no_consent_path_can_install() {
        let mut cfg = config();
        cfg.signing_key_present = false;
        assert!(!cfg.install_permitted());
        let staged = staged_state(&cfg, "1.35.0");
        assert_eq!(staged.kind(), StateKind::Staged);
        let consented = step(
            staged,
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::RestartAndInstall,
            },
            &cfg,
        );
        assert!(!consented.has_install_effect());
        assert_eq!(consented.state.pending_quit_install(), None);
        assert!(consented.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(r)
                if r.event == JournalEvent::InstallFailed
                && r.detail.get(&DetailKey::Reason)
                    == Some(&DetailValue::Reason(ErrorCode::SignatureKeyMissing))
        )));
        // Even a sidecar exit cannot conjure an install.
        let after_exit = step(consented.state, UpdateEvent::SidecarExited, &cfg);
        assert!(!after_exit.has_install_effect());
    }

    #[test]
    fn without_a_signing_key_a_pending_install_is_dropped_at_sidecar_exit() {
        // Reaching this arm needs a pending install created while the key was
        // present, then a key-less config (a downgraded/tampered build).
        let cfg = config();
        let staged = staged_state(&cfg, "1.35.0");
        let consented = step(
            staged,
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::InstallOnQuit,
            },
            &cfg,
        )
        .state;
        let mut keyless = config();
        keyless.signing_key_present = false;
        let transition = step(consented, UpdateEvent::SidecarExited, &keyless);
        assert!(!transition.has_install_effect());
        assert_eq!(transition.state.pending_quit_install(), None);
        assert!(transition.effects.iter().any(|e| matches!(
            e,
            Effect::Journal(r)
                if r.event == JournalEvent::InstallFailed
                && r.detail.get(&DetailKey::Reason)
                    == Some(&DetailValue::Reason(ErrorCode::SignatureKeyMissing))
        )));
    }

    // -- beacon -----------------------------------------------------------

    fn beacon_of(transition: &Transition) -> Option<(String, String)> {
        transition.effects.iter().find_map(|e| match e {
            Effect::SendBeacon { version, target } => Some((version.clone(), target.clone())),
            _ => None,
        })
    }

    #[test]
    fn the_beacon_rides_the_check_request_when_enabled() {
        let mut cfg = config();
        cfg.beacon_enabled = true;
        let transition = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        );
        let (version, target) = beacon_of(&transition).expect("beacon effect");
        // The beacon reports the version we are RUNNING and the target, and
        // carries no install id.
        assert_eq!(version, "1.34.0");
        assert_eq!(target, TARGET);
    }

    /// §6: the ping is "entirely separate from the manifest fetch: its
    /// failure, absence, or removal cannot delay or block an update check".
    /// The converse matters just as much for the histogram — a manifest that
    /// never arrives must not suppress the check-in — so the beacon rides the
    /// *request*, and every manifest outcome afterwards adds no second ping.
    #[test]
    fn the_beacon_fires_once_per_check_independently_of_the_manifest_outcome() {
        let mut cfg = config();
        cfg.beacon_enabled = true;
        let outcomes = [
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 100),
                duration_ms: 1,
            },
            UpdateEvent::ManifestFetched {
                body: "{".into(),
                duration_ms: 1,
            },
            UpdateEvent::ManifestFetchFailed {
                code: ErrorCode::NetworkUnavailable,
            },
        ];
        for outcome in outcomes {
            let started = step(
                UpdateState::initial(&cfg),
                UpdateEvent::CheckRequested,
                &cfg,
            );
            assert_eq!(
                started
                    .effects
                    .iter()
                    .filter(|e| matches!(e, Effect::SendBeacon { .. }))
                    .count(),
                1,
                "exactly one ping per check request"
            );
            let after = step(started.state, outcome, &cfg);
            assert!(
                beacon_of(&after).is_none(),
                "the manifest outcome must not fire a second ping"
            );
        }
    }

    /// A client parked on `staged` awaiting consent is exactly the
    /// population a rollout has reached but not yet converted. It must keep
    /// checking in, or it vanishes from the §6 histogram while it is most
    /// interesting — even though the check itself is deliberately a no-op so
    /// the chip the operator is looking at is not swapped underneath them.
    #[test]
    fn a_staged_install_still_checks_in_without_re_running_the_check() {
        let mut cfg = config();
        cfg.beacon_enabled = true;
        let transition = step(
            staged_state(&cfg, "1.35.0"),
            UpdateEvent::CheckRequested,
            &cfg,
        );
        let (version, _) = beacon_of(&transition).expect("staged installs still check in");
        assert_eq!(version, "1.34.0", "the ping reports the RUNNING version");
        assert_eq!(transition.state.kind(), StateKind::Staged);
        assert!(
            !transition
                .effects
                .iter()
                .any(|e| matches!(e, Effect::FetchManifest { .. })),
            "a staged install must not re-fetch the manifest"
        );
    }

    #[test]
    fn the_beacon_is_suppressed_when_its_own_gate_is_off() {
        let cfg = config(); // beacon_enabled == false
        for state in [UpdateState::initial(&cfg), staged_state(&cfg, "1.35.0")] {
            let transition = step(state, UpdateEvent::CheckRequested, &cfg);
            assert!(beacon_of(&transition).is_none());
        }
    }

    #[test]
    fn beacon_outcomes_journal_ping_ok_and_ping_failed_without_changing_state() {
        let cfg = config();
        for (ok, expected) in [
            (true, JournalEvent::PingOk),
            (false, JournalEvent::PingFailed),
        ] {
            let before = staged_state(&cfg, "1.35.0");
            let kind = before.kind();
            let transition = step(before, UpdateEvent::BeaconCompleted { ok }, &cfg);
            assert_eq!(transition.state.kind(), kind);
            assert!(transition.effects.iter().any(|e| matches!(
                e,
                Effect::Journal(r) if r.event == expected
            )));
        }
    }

    // -- coverage of the vocabulary by the machine ------------------------

    #[test]
    fn every_journal_event_is_reachable_from_the_state_machine() {
        use std::collections::BTreeSet;
        let mut emitted: BTreeSet<JournalEvent> = BTreeSet::new();
        let mut record = |transition: &Transition| {
            for effect in &transition.effects {
                if let Effect::Journal(row) = effect {
                    emitted.insert(row.event);
                }
            }
        };

        let mut cfg = config();
        cfg.beacon_enabled = true;
        cfg.install_id = low_bucket_id();

        // check_started + fetch
        record(&step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        ));
        // manifest_rejected
        record(&step(
            checking_state(&cfg),
            UpdateEvent::ManifestFetched {
                body: "{".into(),
                duration_ms: 1,
            },
            &cfg,
        ));
        // check_failed
        record(&step(
            checking_state(&cfg),
            UpdateEvent::ManifestFetchFailed {
                code: ErrorCode::NetworkUnavailable,
            },
            &cfg,
        ));
        // check_ok + download_started
        record(&step(
            checking_state(&cfg),
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 100),
                duration_ms: 5,
            },
            &cfg,
        ));
        // stage_failed
        record(&step(
            downloading_state(&cfg, "1.35.0"),
            UpdateEvent::DownloadFailed {
                version: "1.35.0".into(),
                code: ErrorCode::StageWriteFailed,
            },
            &cfg,
        ));
        // signature_rejected
        record(&step(
            downloading_state(&cfg, "1.35.0"),
            UpdateEvent::SignatureRejected {
                version: "1.35.0".into(),
            },
            &cfg,
        ));
        // download_ok
        record(&step(
            downloading_state(&cfg, "1.35.0"),
            UpdateEvent::DownloadStaged {
                version: "1.35.0".into(),
                bytes: 10,
                duration_ms: 10,
            },
            &cfg,
        ));
        // consent_granted
        let consented = step(
            staged_state(&cfg, "1.35.0"),
            UpdateEvent::ConsentGranted {
                version: "1.35.0".into(),
                choice: ConsentChoice::RestartAndInstall,
            },
            &cfg,
        );
        record(&consented);
        // install_started
        let installing = step(consented.state, UpdateEvent::SidecarExited, &cfg);
        record(&installing);
        // install_ok
        record(&step(
            installing.state,
            UpdateEvent::InstallSucceeded {
                version: "1.35.0".into(),
            },
            &cfg,
        ));
        // install_failed — rebuilt (states are not clonable by design)
        let reinstalling = step(
            step(
                staged_state(&cfg, "1.35.0"),
                UpdateEvent::ConsentGranted {
                    version: "1.35.0".into(),
                    choice: ConsentChoice::RestartAndInstall,
                },
                &cfg,
            )
            .state,
            UpdateEvent::SidecarExited,
            &cfg,
        )
        .state;
        record(&step(
            reinstalling,
            UpdateEvent::InstallFailed {
                version: "1.35.0".into(),
                code: ErrorCode::InstallFailed,
            },
            &cfg,
        ));
        // skip_recorded
        record(&step(
            staged_state(&cfg, "1.35.0"),
            UpdateEvent::SkipRequested {
                version: "1.35.0".into(),
            },
            &cfg,
        ));
        // ping_ok / ping_failed
        record(&step(
            staged_state(&cfg, "1.35.0"),
            UpdateEvent::BeaconCompleted { ok: true },
            &cfg,
        ));
        record(&step(
            staged_state(&cfg, "1.35.0"),
            UpdateEvent::BeaconCompleted { ok: false },
            &cfg,
        ));
        // bucket_excluded
        let mut excluded_cfg = config();
        excluded_cfg.install_id = high_bucket_id();
        let checking = step(
            UpdateState::initial(&excluded_cfg),
            UpdateEvent::CheckRequested,
            &excluded_cfg,
        )
        .state;
        record(&step(
            checking,
            UpdateEvent::ManifestFetched {
                body: manifest_json("1.35.0", 5),
                duration_ms: 1,
            },
            &excluded_cfg,
        ));
        // freeze_suppressed
        let mut frozen_cfg = config();
        frozen_cfg.updates_enabled = false;
        record(&step(
            UpdateState::initial(&frozen_cfg),
            UpdateEvent::CheckRequested,
            &frozen_cfg,
        ));

        let missing: Vec<&str> = JournalEvent::ALL
            .iter()
            .filter(|event| !emitted.contains(event))
            .map(|event| event.as_str())
            .collect();
        assert!(
            missing.is_empty(),
            "unreachable journal events: {missing:?}"
        );
    }

    #[test]
    fn every_transition_re_emits_the_contract_i2_payload_last() {
        let cfg = config();
        let transition = step(
            UpdateState::initial(&cfg),
            UpdateEvent::CheckRequested,
            &cfg,
        );
        assert!(matches!(
            transition.effects.last(),
            Some(Effect::EmitState(_))
        ));
        assert_eq!(
            transition.effects.last(),
            Some(&Effect::EmitState(transition.state.payload()))
        );
    }

    #[test]
    fn payload_serializes_with_the_declared_i2_field_names() {
        let payload = UpdateStatePayload {
            state: StateKind::Staged,
            version: Some("1.35.0".into()),
            notes: Some("hello".into()),
            hardware_revalidation: true,
            error_code: Some(ErrorCode::SignatureRejected),
        };
        let json = serde_json::to_value(&payload).expect("serialize");
        assert_eq!(json["state"], "staged");
        assert_eq!(json["version"], "1.35.0");
        assert_eq!(json["notes"], "hello");
        assert_eq!(json["hardware_revalidation"], true);
        assert_eq!(json["error_code"], "signature_rejected");
        let back: UpdateStatePayload = serde_json::from_value(json).expect("roundtrip");
        assert_eq!(back, payload);
    }

    #[test]
    fn journal_record_builder_accumulates_details() {
        let record = JournalRecord::new(JournalEvent::DownloadOk, Some("1.35.0".into()))
            .with(DetailKey::Bytes, 10_u64)
            .with(DetailKey::DurationMs, 20_u64);
        assert_eq!(record.detail.len(), 2);
        assert_eq!(record.version.as_deref(), Some("1.35.0"));
    }
}
