//! Contract I8 — the update journal.
//!
//! One JSONL file (`update-journal.jsonl`) in the config dir, one row per
//! event, size-capped with two-generation rotation
//! (`update-journal.jsonl` -> `update-journal.jsonl.1`, older dropped).
//!
//! The privacy guarantee is structural, not procedural. A row is built from
//! a [`JournalRecord`], whose `event` is a closed enum, whose `version` is a
//! validated version string, and whose `detail` map is keyed by a closed
//! [`DetailKey`] enum with [`DetailValue`]s that can only be a typed
//! [`ErrorCode`], a number or a bool. There is no `String` detail variant,
//! so an `io::Error` message, a URL or an absolute path has no representable
//! way into the file — see `path_injection_never_reaches_the_journal`.
//!
//! The version field is the one string that reaches disk, so it is
//! defensively re-sanitised here even though [`crate::update_policy`]
//! already validated it: a journal writer that trusts its caller is one
//! refactor away from leaking.

use std::fs;
use std::io::Write as _;
use std::path::{Path, PathBuf};

use serde_json::{Map, Value};

use crate::update_policy::{DetailValue, ErrorCode, JournalRecord};

/// Journal filename inside the config directory.
pub const JOURNAL_FILE_NAME: &str = "update-journal.jsonl";
/// Rotated-generation suffix. Exactly one generation is kept.
pub const ROTATED_SUFFIX: &str = ".1";
/// Size at or above which the journal rotates, in bytes.
pub const MAX_JOURNAL_BYTES: u64 = 256 * 1024;
/// Longest version string a row may carry. Longer values are dropped, not
/// truncated: a truncated version is a *wrong* version.
pub const MAX_VERSION_FIELD_BYTES: usize = 64;

/// Subdirectory under the platform config root.
const CONFIG_DIR_NAME: &str = "RytmRandomizer";

/// Resolve the journal path from a config directory.
pub fn journal_path(config_dir: &Path) -> PathBuf {
    config_dir.join(JOURNAL_FILE_NAME)
}

/// Path of the single rotated generation.
pub fn rotated_path(config_dir: &Path) -> PathBuf {
    config_dir.join(format!("{JOURNAL_FILE_NAME}{ROTATED_SUFFIX}"))
}

/// Default config directory for the journal.
///
/// `$XDG_CONFIG_HOME` / `%APPDATA%` when set, else `$HOME/.config`, else the
/// process temp dir. Mirrors the posture of
/// `sidecar::resolve_arm_secret_file_path`: degrade, never panic.
pub fn default_config_dir() -> PathBuf {
    let base = std::env::var_os("XDG_CONFIG_HOME")
        .or_else(|| std::env::var_os("APPDATA"))
        .map(PathBuf::from)
        .or_else(|| {
            std::env::var_os("HOME")
                .or_else(|| std::env::var_os("USERPROFILE"))
                .map(|home| PathBuf::from(home).join(".config"))
        })
        .unwrap_or_else(std::env::temp_dir);
    base.join(CONFIG_DIR_NAME)
}

/// Whether a version string is safe to write verbatim into a row.
///
/// Same character class the policy accepts, re-checked here so the journal
/// cannot be made to emit a path, a URL or a newline even if a future caller
/// hands it an unvalidated string.
fn version_is_writable(version: &str) -> bool {
    !version.is_empty()
        && version.len() <= MAX_VERSION_FIELD_BYTES
        && version
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '-' | '+'))
}

/// Render one record as a JSON object.
///
/// `ts` is passed in (milliseconds since the Unix epoch) rather than read
/// from a clock, so rows are reproducible in tests.
pub fn render_row(record: &JournalRecord, ts_ms: u64) -> Value {
    let mut row = Map::new();
    row.insert("ts".to_string(), Value::from(ts_ms));
    row.insert("event".to_string(), Value::from(record.event.as_str()));
    let version = record
        .version
        .as_deref()
        .filter(|v| version_is_writable(v))
        .map(|v| Value::from(v.to_string()))
        .unwrap_or(Value::Null);
    row.insert("version".to_string(), version);
    let mut detail = Map::new();
    for (key, value) in &record.detail {
        let rendered = match value {
            DetailValue::Reason(code) => Value::from(code.as_str()),
            DetailValue::Number(n) => Value::from(*n),
            DetailValue::Flag(flag) => Value::from(*flag),
        };
        detail.insert(key.as_str().to_string(), rendered);
    }
    row.insert("detail".to_string(), Value::Object(detail));
    Value::Object(row)
}

/// A journal bound to one config directory.
#[derive(Debug, Clone)]
pub struct UpdateJournal {
    config_dir: PathBuf,
}

impl UpdateJournal {
    /// Bind a journal to `config_dir`. No I/O happens until [`Self::append`].
    pub fn new(config_dir: PathBuf) -> Self {
        Self { config_dir }
    }

    /// Bind a journal to [`default_config_dir`].
    pub fn with_default_dir() -> Self {
        Self::new(default_config_dir())
    }

    /// The active journal file's path.
    pub fn path(&self) -> PathBuf {
        journal_path(&self.config_dir)
    }

    /// The rotated generation's path.
    pub fn rotated(&self) -> PathBuf {
        rotated_path(&self.config_dir)
    }

    /// Append one row, rotating first if the file has reached the cap.
    ///
    /// Returns a typed [`ErrorCode`] on failure — never the underlying
    /// `io::Error`, whose message would carry an absolute path. The caller
    /// (the driver) logs the code; the failure is deliberately non-fatal
    /// because losing an observability row must never break an update.
    pub fn append(&self, record: &JournalRecord, ts_ms: u64) -> Result<(), ErrorCode> {
        fs::create_dir_all(&self.config_dir).map_err(|_| ErrorCode::JournalWriteFailed)?;
        let path = self.path();
        self.rotate_if_needed(&path)?;
        let mut line = serde_json::to_string(&render_row(record, ts_ms))
            .map_err(|_| ErrorCode::JournalWriteFailed)?;
        line.push('\n');
        let mut file = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .map_err(|_| ErrorCode::JournalWriteFailed)?;
        file.write_all(line.as_bytes())
            .map_err(|_| ErrorCode::JournalWriteFailed)
    }

    /// Rotate when the active file is at or over [`MAX_JOURNAL_BYTES`].
    ///
    /// Two generations total: the current file becomes `.1`, and whatever
    /// `.1` held is dropped. A missing file is not an error.
    fn rotate_if_needed(&self, path: &Path) -> Result<(), ErrorCode> {
        let size = match fs::metadata(path) {
            Ok(meta) => meta.len(),
            Err(err) if err.kind() == std::io::ErrorKind::NotFound => return Ok(()),
            Err(_) => return Err(ErrorCode::JournalWriteFailed),
        };
        if size < MAX_JOURNAL_BYTES {
            return Ok(());
        }
        let rotated = self.rotated();
        match fs::remove_file(&rotated) {
            Ok(()) => {}
            Err(err) if err.kind() == std::io::ErrorKind::NotFound => {}
            Err(_) => return Err(ErrorCode::JournalWriteFailed),
        }
        fs::rename(path, &rotated).map_err(|_| ErrorCode::JournalWriteFailed)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::update_policy::{DetailKey, JournalEvent};

    struct TempDir {
        path: PathBuf,
    }

    impl TempDir {
        fn new(tag: &str) -> Self {
            let path = std::env::temp_dir().join(format!(
                "rytm-journal-{tag}-{}-{:?}",
                std::process::id(),
                std::thread::current().id()
            ));
            let _ = fs::remove_dir_all(&path);
            fs::create_dir_all(&path).expect("create temp dir");
            Self { path }
        }
    }

    impl Drop for TempDir {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.path);
        }
    }

    fn read_rows(path: &Path) -> Vec<Value> {
        fs::read_to_string(path)
            .expect("read journal")
            .lines()
            .map(|line| serde_json::from_str(line).expect("row is JSON"))
            .collect()
    }

    #[test]
    fn paths_are_derived_from_the_config_dir() {
        let dir = Path::new("/some/config");
        assert_eq!(journal_path(dir).file_name().unwrap(), JOURNAL_FILE_NAME);
        assert_eq!(
            rotated_path(dir).file_name().unwrap().to_str().unwrap(),
            format!("{JOURNAL_FILE_NAME}{ROTATED_SUFFIX}")
        );
        let journal = UpdateJournal::new(dir.to_path_buf());
        assert_eq!(journal.path(), journal_path(dir));
        assert_eq!(journal.rotated(), rotated_path(dir));
    }

    #[test]
    fn default_config_dir_ends_in_the_app_directory() {
        let dir = default_config_dir();
        assert_eq!(
            dir.file_name().and_then(|n| n.to_str()),
            Some(CONFIG_DIR_NAME)
        );
        assert_eq!(
            UpdateJournal::with_default_dir().path(),
            journal_path(&default_config_dir())
        );
    }

    #[test]
    fn a_row_has_exactly_the_four_contract_fields() {
        let record = JournalRecord::new(JournalEvent::CheckOk, Some("1.35.0".into()))
            .with(DetailKey::DurationMs, 12_u64);
        let row = render_row(&record, 1_700_000_000_000);
        let object = row.as_object().expect("object");
        let mut keys: Vec<&str> = object.keys().map(String::as_str).collect();
        keys.sort_unstable();
        assert_eq!(keys, ["detail", "event", "ts", "version"]);
        assert_eq!(object["event"], "check_ok");
        assert_eq!(object["version"], "1.35.0");
        assert_eq!(object["ts"], 1_700_000_000_000_u64);
        assert_eq!(object["detail"]["duration_ms"], 12);
    }

    #[test]
    fn a_versionless_row_writes_json_null() {
        let record = JournalRecord::new(JournalEvent::FreezeSuppressed, None);
        let row = render_row(&record, 1);
        assert_eq!(row["version"], Value::Null);
        assert!(row["detail"].as_object().expect("detail").is_empty());
    }

    #[test]
    fn every_detail_variant_renders_to_its_json_shape() {
        let record = JournalRecord::new(JournalEvent::CheckOk, Some("1.0.0".into()))
            .with(DetailKey::Reason, ErrorCode::NetworkUnavailable)
            .with(DetailKey::Bytes, 4096_u64)
            .with(DetailKey::HardwareRevalidation, true);
        let row = render_row(&record, 0);
        assert_eq!(row["detail"]["reason"], "network_unavailable");
        assert_eq!(row["detail"]["bytes"], 4096);
        assert_eq!(row["detail"]["hardware_revalidation"], true);
    }

    #[test]
    fn every_vocabulary_member_renders_its_wire_string() {
        for event in JournalEvent::ALL {
            let row = render_row(&JournalRecord::new(event, None), 0);
            assert_eq!(row["event"], event.as_str());
        }
    }

    /// The load-bearing privacy test: feed a record whose version field is a
    /// hostile absolute path and assert no fragment of it reaches the file.
    ///
    /// The `detail` map needs no equivalent test-by-construction argument —
    /// [`DetailValue`] has no string variant at all — but the assertion below
    /// covers the whole serialised row anyway, so a future `String` variant
    /// would fail this test rather than silently leak.
    #[test]
    fn path_injection_never_reaches_the_journal() {
        let dir = TempDir::new("path-injection");
        let journal = UpdateJournal::new(dir.path.clone());
        let hostile = [
            "/Users/misteredr/RytmRandomizer/secret.key",
            "C:\\Users\\misteredr\\AppData\\token.txt",
            "../../etc/passwd",
            "1.35.0 (from /var/folders/xy/T/rytm-staging/app.tar.gz)",
            "https://github.com/o/r/releases/download/v1.35.0/app.tar.gz",
            "No such file or directory (os error 2): /tmp/rytm/update.bin",
        ];
        for version in hostile {
            journal
                .append(
                    &JournalRecord::new(JournalEvent::StageFailed, Some(version.to_string()))
                        .with(DetailKey::Reason, ErrorCode::StageWriteFailed),
                    7,
                )
                .expect("append");
        }
        let raw = fs::read_to_string(journal.path()).expect("read journal");
        for needle in [
            "misteredr",
            "/Users",
            "C:\\",
            "AppData",
            "passwd",
            "/var/folders",
            "/tmp/",
            "https://",
            ".tar.gz",
            "os error",
            "secret",
        ] {
            assert!(!raw.contains(needle), "journal leaked {needle:?}:\n{raw}");
        }
        // The rows still exist and are still typed — the version was dropped,
        // not the observability.
        let rows = read_rows(&journal.path());
        assert_eq!(rows.len(), hostile.len());
        for row in rows {
            assert_eq!(row["event"], "stage_failed");
            assert_eq!(row["version"], Value::Null);
            assert_eq!(row["detail"]["reason"], "stage_write_failed");
        }
    }

    #[test]
    fn an_oversized_version_is_dropped_rather_than_truncated() {
        let long = "1".repeat(MAX_VERSION_FIELD_BYTES + 1);
        let row = render_row(&JournalRecord::new(JournalEvent::CheckOk, Some(long)), 0);
        assert_eq!(row["version"], Value::Null);
    }

    #[test]
    fn a_blank_version_is_dropped() {
        let row = render_row(
            &JournalRecord::new(JournalEvent::CheckOk, Some(String::new())),
            0,
        );
        assert_eq!(row["version"], Value::Null);
    }

    #[test]
    fn appending_creates_the_directory_and_writes_one_line_per_row() {
        let dir = TempDir::new("append");
        let nested = dir.path.join("nested").join("deeper");
        let journal = UpdateJournal::new(nested.clone());
        for (n, event) in JournalEvent::ALL.iter().enumerate() {
            journal
                .append(&JournalRecord::new(*event, Some("1.35.0".into())), n as u64)
                .expect("append");
        }
        assert!(nested.is_dir());
        let rows = read_rows(&journal.path());
        assert_eq!(rows.len(), JournalEvent::ALL.len());
        for (n, event) in JournalEvent::ALL.iter().enumerate() {
            assert_eq!(rows[n]["event"], event.as_str());
            assert_eq!(rows[n]["ts"], n as u64);
        }
    }

    #[test]
    fn the_journal_rotates_at_the_cap_and_keeps_exactly_two_generations() {
        let dir = TempDir::new("rotate");
        let journal = UpdateJournal::new(dir.path.clone());
        // Pre-fill past the cap so the very next append rotates.
        fs::write(journal.path(), vec![b'x'; MAX_JOURNAL_BYTES as usize]).expect("prefill");
        journal
            .append(&JournalRecord::new(JournalEvent::CheckOk, None), 1)
            .expect("append after rotation");
        assert!(journal.rotated().is_file(), "generation 1 must exist");
        assert_eq!(
            fs::metadata(journal.rotated()).expect("meta").len(),
            MAX_JOURNAL_BYTES
        );
        let rows = read_rows(&journal.path());
        assert_eq!(rows.len(), 1, "the fresh generation starts empty");

        // Rotate a second time: the old `.1` is discarded, not chained to `.2`.
        fs::write(journal.path(), vec![b'y'; MAX_JOURNAL_BYTES as usize]).expect("prefill again");
        journal
            .append(&JournalRecord::new(JournalEvent::CheckOk, None), 2)
            .expect("append after second rotation");
        let rotated = fs::read(journal.rotated()).expect("read rotated");
        assert!(rotated.iter().all(|b| *b == b'y'), "newest generation kept");
        assert!(
            !dir.path.join(format!("{JOURNAL_FILE_NAME}.2")).exists(),
            "only two generations are kept"
        );
    }

    #[test]
    fn a_file_below_the_cap_does_not_rotate() {
        let dir = TempDir::new("no-rotate");
        let journal = UpdateJournal::new(dir.path.clone());
        fs::write(journal.path(), vec![b'x'; (MAX_JOURNAL_BYTES - 1) as usize]).expect("prefill");
        journal
            .append(&JournalRecord::new(JournalEvent::CheckOk, None), 1)
            .expect("append");
        assert!(!journal.rotated().exists());
    }

    #[test]
    fn append_failure_is_reported_as_a_typed_code_without_a_path() {
        // A config "dir" that is actually a file makes create_dir_all fail.
        let dir = TempDir::new("failure");
        let blocked = dir.path.join("not-a-dir");
        fs::write(&blocked, b"x").expect("write blocker");
        let journal = UpdateJournal::new(blocked);
        let err = journal
            .append(&JournalRecord::new(JournalEvent::CheckOk, None), 1)
            .expect_err("must fail");
        assert_eq!(err, ErrorCode::JournalWriteFailed);
        // The error carries a code and nothing else — no Display path leak.
        assert_eq!(err.to_string(), "journal_write_failed");
    }

    #[test]
    fn rotation_failure_is_reported_as_a_typed_code() {
        let dir = TempDir::new("rotate-failure");
        let journal = UpdateJournal::new(dir.path.clone());
        fs::write(journal.path(), vec![b'x'; MAX_JOURNAL_BYTES as usize]).expect("prefill");
        // A directory at the rotated path defeats both remove_file and rename.
        fs::create_dir_all(journal.rotated().join("child")).expect("blocking dir");
        let err = journal
            .append(&JournalRecord::new(JournalEvent::CheckOk, None), 1)
            .expect_err("rotation must fail");
        assert_eq!(err, ErrorCode::JournalWriteFailed);
    }

    #[test]
    fn a_missing_journal_file_is_not_a_rotation_error() {
        let dir = TempDir::new("missing");
        let journal = UpdateJournal::new(dir.path.clone());
        assert!(!journal.path().exists());
        journal
            .append(&JournalRecord::new(JournalEvent::CheckStarted, None), 0)
            .expect("first append succeeds");
        assert_eq!(read_rows(&journal.path()).len(), 1);
    }

    #[test]
    fn rotation_replaces_a_pre_existing_rotated_generation() {
        let dir = TempDir::new("replace-rotated");
        let journal = UpdateJournal::new(dir.path.clone());
        fs::write(journal.rotated(), b"stale").expect("stale rotated");
        fs::write(journal.path(), vec![b'z'; MAX_JOURNAL_BYTES as usize]).expect("prefill");
        journal
            .append(&JournalRecord::new(JournalEvent::CheckOk, None), 1)
            .expect("append");
        let rotated = fs::read(journal.rotated()).expect("read rotated");
        assert!(rotated.iter().all(|b| *b == b'z'));
    }

    #[test]
    fn version_writability_accepts_semver_and_rejects_separators() {
        assert!(version_is_writable("1.35.0"));
        assert!(version_is_writable("1.35.0-beta.1+abc"));
        assert!(!version_is_writable(""));
        assert!(!version_is_writable("1.35.0/../etc"));
        assert!(!version_is_writable("1.35.0\nfake"));
        assert!(!version_is_writable("C:\\x"));
        assert!(!version_is_writable(
            &"1".repeat(MAX_VERSION_FIELD_BYTES + 1)
        ));
        assert!(version_is_writable(&"1".repeat(MAX_VERSION_FIELD_BYTES)));
    }
}
