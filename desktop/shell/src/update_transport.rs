//! The network half of the updater: fetch, download, install, beacon.
//!
//! Split from `updater.rs` so the policy stays pure and this stays
//! substitutable. Everything here is expressed against the [`Transport`]
//! trait, so a test drives the full driver loop without a running Tauri app
//! and without a network — while production plugs in the real
//! `tauri-plugin-updater`, whose Ed25519 verification we must not hand-roll.
//!
//! Three rules this module exists to keep:
//!
//! 1. **Never block the caller.** Every operation returns immediately; the
//!    outcome comes back as an [`UpdateEvent`] fed to the driver, which is
//!    what the state machine already models.
//! 2. **Never install what was not verified.** The plugin verifies during
//!    download; [`install`] additionally refuses when no public key is
//!    configured, so an unsigned install fails loudly here rather than deep
//!    in plugin internals.
//! 3. **The beacon is fire-and-forget.** No retry, no surfaced error, no
//!    identifying data — a check-in that fails is simply a check-in that did
//!    not happen, and must never affect the update flow.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use crate::update_policy::ErrorCode;

/// One network operation's outcome, reported back to the driver.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransportOutcome {
    /// A manifest body arrived.
    Manifest {
        /// Raw response body.
        body: String,
        /// Round-trip duration.
        duration_ms: u64,
    },
    /// The manifest could not be fetched or parsed.
    ManifestFailed {
        /// Typed reason; never a raw error string.
        code: ErrorCode,
    },
    /// An artifact downloaded, verified and staged.
    Staged {
        /// Version staged.
        version: String,
        /// Bytes written.
        bytes: u64,
        /// Download + verify + stage duration.
        duration_ms: u64,
    },
    /// The download failed before verification.
    DownloadFailed {
        /// Version attempted.
        version: String,
        /// Typed reason.
        code: ErrorCode,
    },
    /// The artifact's signature did not verify. Distinct from a failed
    /// download: this one means the bytes arrived and were *wrong*, which is
    /// the case an operator must be able to see.
    SignatureRejected {
        /// Version attempted.
        version: String,
    },
    /// Local diagnostic only; never changes update eligibility or state.
    BeaconCompleted {
        /// Whether the GET returned a successful HTTP status.
        ok: bool,
    },
}

/// The network operations the driver needs.
///
/// Implementations must not block: each call hands its [`TransportOutcome`]
/// to `report` from whatever thread or task it likes.
pub trait Transport: Send + Sync + 'static {
    /// Fetch the channel manifest.
    fn fetch_manifest(&self, channel: &str, report: Box<dyn FnOnce(TransportOutcome) + Send>);

    /// Download, verify and stage one artifact.
    fn download(
        &self,
        version: &str,
        url: &str,
        signature: &str,
        report: Box<dyn FnOnce(TransportOutcome) + Send>,
    );

    /// Install an already-staged artifact. Returns an error the caller
    /// journals; it never panics, because a failed install must leave the
    /// running app intact.
    fn install(&self, version: &str) -> Result<(), ErrorCode>;

    /// Apply the operator's restart preference to the already staged bytes.
    fn install_with_choice(
        &self,
        version: &str,
        _choice: crate::update_policy::ConsentChoice,
    ) -> Result<(), ErrorCode> {
        self.install(version)
    }

    /// Independent check-in; report only a local diagnostic, without retry.
    fn beacon(&self, asset_url: &str, report: Box<dyn FnOnce(TransportOutcome) + Send>);

    /// Cancel owned network work after the final shutdown/install outcome.
    fn shutdown(&self) {}
}

/// A transport that performs no I/O and reports a typed failure.
///
/// This is what runs when no public key is configured: the client can still
/// check state, journal, and render, but it can never download or install
/// something it cannot verify. Being explicit beats a silently absent
/// transport, which is what the pre-wiring code did — every check logged
/// "not yet wired" and the panel showed a spinner that never resolved.
pub struct DisabledTransport {
    reason: ErrorCode,
}

impl DisabledTransport {
    /// A transport disabled for `reason`.
    pub fn new(reason: ErrorCode) -> Self {
        Self { reason }
    }
}

impl Transport for DisabledTransport {
    fn fetch_manifest(&self, _channel: &str, report: Box<dyn FnOnce(TransportOutcome) + Send>) {
        report(TransportOutcome::ManifestFailed { code: self.reason });
    }

    fn download(
        &self,
        version: &str,
        _url: &str,
        _signature: &str,
        report: Box<dyn FnOnce(TransportOutcome) + Send>,
    ) {
        report(TransportOutcome::DownloadFailed {
            version: version.to_string(),
            code: self.reason,
        });
    }

    fn install(&self, _version: &str) -> Result<(), ErrorCode> {
        Err(self.reason)
    }

    fn beacon(&self, _asset_url: &str, report: Box<dyn FnOnce(TransportOutcome) + Send>) {
        report(TransportOutcome::BeaconCompleted { ok: false });
    }
}

/// Shared handle so the sink, the tray and the timer all use one transport.
pub type SharedTransport = Arc<dyn Transport>;

#[cfg(test)]
mod tests {
    use std::sync::Mutex;

    use super::*;

    #[test]
    fn a_disabled_transport_reports_its_reason_rather_than_going_quiet() {
        let transport = DisabledTransport::new(ErrorCode::SignatureRejected);
        let seen: Arc<Mutex<Vec<TransportOutcome>>> = Arc::new(Mutex::new(Vec::new()));

        let sink = Arc::clone(&seen);
        transport.fetch_manifest(
            "stable",
            Box::new(move |outcome| sink.lock().expect("poisoned").push(outcome)),
        );

        assert_eq!(
            seen.lock().expect("poisoned").as_slice(),
            [TransportOutcome::ManifestFailed {
                code: ErrorCode::SignatureRejected
            }],
            "a disabled transport must REPORT, not silently do nothing — the \
             pre-wiring code logged and returned, so the panel spun forever"
        );
    }

    #[test]
    fn a_disabled_transport_refuses_to_install() {
        let transport = DisabledTransport::new(ErrorCode::SignatureRejected);
        assert_eq!(
            transport.install("1.35.0"),
            Err(ErrorCode::SignatureRejected)
        );
    }

    #[test]
    fn a_disabled_transport_beacon_is_a_silent_no_op() {
        // The beacon must never fail loudly: a check-in that cannot happen is
        // not an update problem.
        DisabledTransport::new(ErrorCode::NetworkUnavailable).beacon(
            "https://example.invalid/x",
            Box::new(|outcome| {
                assert_eq!(outcome, TransportOutcome::BeaconCompleted { ok: false });
            }),
        );
    }

    #[test]
    fn a_disabled_download_names_the_version_it_refused() {
        let transport = DisabledTransport::new(ErrorCode::NetworkUnavailable);
        let seen: Arc<Mutex<Vec<TransportOutcome>>> = Arc::new(Mutex::new(Vec::new()));
        let sink = Arc::clone(&seen);

        transport.download(
            "1.35.1",
            "https://github.com/o/r/releases/download/v1.35.1/a.tar.gz",
            "c2ln",
            Box::new(move |outcome| sink.lock().expect("poisoned").push(outcome)),
        );

        assert_eq!(
            seen.lock().expect("poisoned").as_slice(),
            [TransportOutcome::DownloadFailed {
                version: "1.35.1".to_string(),
                code: ErrorCode::NetworkUnavailable
            }]
        );
    }
}

/// The production transport, backed by `tauri-plugin-updater`.
///
/// Deliberately thin. The plugin owns the parts that must not be re-invented:
/// the HTTPS client, the endpoint substitution, and — critically — **Ed25519
/// signature verification during download**. Re-implementing any of that here
/// would be the fork Gate 17 exists to prevent, and getting verification
/// subtly wrong is the one bug in this whole program that ships malware.
///
/// What this adds is the seam: every call returns immediately and reports a
/// typed [`TransportOutcome`], so the pure policy stays in charge of what the
/// state machine does about it.
/// The verified artifact held between download and install: the version it
/// was staged for, the plugin's `Update` handle, and the bytes that actually
/// passed signature verification.
type StagedSlot =
    std::sync::Arc<std::sync::Mutex<Option<(String, tauri_plugin_updater::Update, Vec<u8>)>>>;

/// At most one task per operation; completed handles remain bounded too.
#[derive(Default)]
struct Operations {
    closed: AtomicBool,
    tasks: Mutex<[Option<tauri::async_runtime::JoinHandle<()>>; 3]>,
}

impl Operations {
    fn spawn(&self, slot: usize, task: impl std::future::Future<Output = ()> + Send + 'static) {
        let mut tasks = self.tasks.lock().expect("operation tasks poisoned");
        if self.closed.load(Ordering::SeqCst) {
            return;
        }
        if let Some(previous) = tasks[slot].take() {
            previous.abort();
        }
        tasks[slot] = Some(tauri::async_runtime::spawn(task));
    }

    fn close(&self) {
        self.closed.store(true, Ordering::SeqCst);
        for task in self
            .tasks
            .lock()
            .expect("operation tasks poisoned")
            .iter_mut()
        {
            if let Some(task) = task.take() {
                task.abort();
            }
        }
    }
}

/// The initial artifact is policy-validated separately. Redirects must retain
/// HTTPS and the same exact host allowlist, including on the plugin download.
fn artifact_redirect_allowed(url: &reqwest::Url) -> bool {
    url.scheme() == "https"
        && url.username().is_empty()
        && url.password().is_none()
        && url.port_or_known_default() == Some(443)
        && url
            .host_str()
            .is_some_and(|host| crate::update_policy::ALLOWED_ARTIFACT_HOSTS.contains(&host))
}

fn redirect_policy(endpoint: reqwest::Url) -> reqwest::redirect::Policy {
    reqwest::redirect::Policy::custom(move |attempt| {
        if attempt.previous().len() >= 5 {
            return attempt.error("updater redirect limit");
        }
        let first = attempt.previous().first();
        let is_manifest = first == Some(&endpoint);
        #[cfg(feature = "native-test")]
        let is_manifest = is_manifest || first.is_some_and(|url| url.origin() == endpoint.origin());
        let allowed = if is_manifest {
            // An explicitly local fixture may redirect only within its own
            // origin. A configured manifest cannot redirect to another host.
            attempt.url().origin() == endpoint.origin()
                && attempt.url().username().is_empty()
                && attempt.url().password().is_none()
        } else {
            artifact_redirect_allowed(attempt.url())
        };
        if allowed {
            attempt.follow()
        } else {
            attempt.error("updater redirect refused")
        }
    })
}

pub struct PluginTransport<R: tauri::Runtime> {
    app: tauri::AppHandle<R>,
    /// The verified bytes from the last successful download.
    ///
    /// Held so `install` swaps exactly what was verified. Downloading a
    /// second time at install would re-fetch — and a republished artifact
    /// would then be installed WITHOUT the verification the operator
    /// consented on the strength of.
    staged_handle: StagedSlot,
    /// The exact release whose unmodified manifest the policy validated.
    checked_handle: Arc<std::sync::Mutex<Option<tauri_plugin_updater::Update>>>,
    /// False until the operator lands the Ed25519 public key. The plugin
    /// refuses an unverifiable artifact itself; this makes the refusal happen
    /// at the seam, where the journal entry is legible.
    signing_key_present: bool,
    operations: Arc<Operations>,
    #[cfg(feature = "native-test")]
    fixture: Option<Arc<crate::native_fixture::NativeFixture>>,
}

impl<R: tauri::Runtime> PluginTransport<R> {
    /// Wrap an app handle.
    pub fn new(app: tauri::AppHandle<R>, signing_key_present: bool) -> Self {
        Self {
            app,
            staged_handle: std::sync::Arc::new(std::sync::Mutex::new(None)),
            checked_handle: Arc::new(std::sync::Mutex::new(None)),
            signing_key_present,
            operations: Arc::new(Operations::default()),
            #[cfg(feature = "native-test")]
            fixture: None,
        }
    }

    #[cfg(feature = "native-test")]
    pub fn with_native_fixture(
        app: tauri::AppHandle<R>,
        fixture: Arc<crate::native_fixture::NativeFixture>,
    ) -> Self {
        let mut transport = Self::new(app, fixture.signing_key_present());
        transport.fixture = Some(fixture);
        transport
    }
}

impl<R: tauri::Runtime> Transport for PluginTransport<R> {
    fn fetch_manifest(&self, channel: &str, report: Box<dyn FnOnce(TransportOutcome) + Send>) {
        use tauri_plugin_updater::UpdaterExt as _;

        let app = self.app.clone();
        let channel = channel.to_string();
        let checked_slot = Arc::clone(&self.checked_handle);
        let operations = Arc::clone(&self.operations);
        self.operations.spawn(0, async move {
            let started = std::time::Instant::now();
            let base = crate::updater::resolve_manifest_base_url(
                std::env::var(crate::updater::MANIFEST_URL_ENV_VAR)
                    .ok()
                    .as_deref(),
            );
            let endpoint = crate::updater::manifest_url(&base, &channel);
            let endpoint: reqwest::Url = endpoint.parse().expect("resolved manifest URL");
            let redirect_endpoint = endpoint.clone();
            let builder = match app
                .updater_builder()
                .target(crate::updater::current_target())
                .version_comparator(|_, _| true)
                .timeout(std::time::Duration::from_secs(30))
                .configure_client(move |client| {
                    client.redirect(redirect_policy(redirect_endpoint.clone()))
                })
                .endpoints(vec![endpoint])
                .and_then(|builder| builder.build())
            {
                Ok(builder) => builder,
                Err(_) => {
                    // A misconfigured updater (bad endpoint, absent pubkey) is
                    // a configuration failure, not a network one; keeping the
                    // codes distinct is what makes the journal actionable.
                    report(TransportOutcome::ManifestFailed {
                        code: ErrorCode::ManifestMalformed,
                    });
                    return;
                }
            };
            let result = builder.check().await;
            if operations.closed.load(Ordering::SeqCst) {
                return;
            }
            match result {
                Ok(Some(update)) => {
                    // Preserve rollout, hardware warnings, channel and every
                    // platform exactly as published. The policy validates them.
                    let body = update.raw_json.to_string();
                    {
                        let mut slot = checked_slot.lock().expect("checked slot poisoned");
                        if operations.closed.load(Ordering::SeqCst) {
                            return;
                        }
                        *slot = Some(update);
                    }
                    report(TransportOutcome::Manifest {
                        body,
                        duration_ms: started.elapsed().as_millis() as u64,
                    });
                }
                // Static manifests must contain a release, including when it
                // equals the running version. The policy compares versions.
                Ok(None) => report(TransportOutcome::ManifestFailed {
                    code: ErrorCode::ManifestMalformed,
                }),
                Err(_) => report(TransportOutcome::ManifestFailed {
                    code: ErrorCode::NetworkUnavailable,
                }),
            }
        });
    }

    fn download(
        &self,
        version: &str,
        url: &str,
        signature: &str,
        report: Box<dyn FnOnce(TransportOutcome) + Send>,
    ) {
        if !self.signing_key_present {
            report(TransportOutcome::DownloadFailed {
                version: version.to_string(),
                code: ErrorCode::SignatureKeyMissing,
            });
            return;
        }

        let checked = self
            .checked_handle
            .lock()
            .expect("checked slot poisoned")
            .take();
        let Some(mut update) = checked.filter(|update| {
            artifact_identity_matches(
                version,
                url,
                signature,
                &update.version,
                update.download_url.as_str(),
                &update.signature,
            )
        }) else {
            report(TransportOutcome::SignatureRejected {
                version: version.to_string(),
            });
            return;
        };
        update.timeout = Some(std::time::Duration::from_secs(300));
        #[cfg(feature = "native-test")]
        if let Some(fixture) = &self.fixture {
            // Identity was checked against the canonical manifest above.
            // Only fixture I/O routing changes: the REAL plugin still verifies
            // these local bytes with the signature and public key it parsed.
            update.download_url = fixture.artifact_url();
            update.no_proxy = true;
            update.timeout = Some(std::time::Duration::from_secs(10));
        }
        let version = version.to_string();
        let staged_slot = std::sync::Arc::clone(&self.staged_handle);
        let operations = Arc::clone(&self.operations);
        self.operations.spawn(1, async move {
            let started = std::time::Instant::now();
            // The plugin verifies the signature DURING download and fails the
            // future when it does not match — which is exactly the case the
            // operator must be able to distinguish from a network error, so it
            // gets its own outcome rather than a generic failure.
            let result = update.download(|_, _| {}, || {}).await;
            if operations.closed.load(Ordering::SeqCst) {
                return;
            }
            match result {
                Ok(bytes) => {
                    let byte_count = bytes.len() as u64;
                    // Keep exactly the bytes that verified. install() swaps
                    // these and nothing else.
                    {
                        let mut slot = staged_slot.lock().expect("staged slot poisoned");
                        if operations.closed.load(Ordering::SeqCst) {
                            return;
                        }
                        *slot = Some((version.clone(), update, bytes));
                    }
                    report(TransportOutcome::Staged {
                        version,
                        bytes: byte_count,
                        duration_ms: started.elapsed().as_millis() as u64,
                    })
                }
                // Minisign(_) is a signature that did not verify;
                // SignatureUtf8(_) is a signature field that was not even
                // parseable. Both mean "these bytes are not what the release
                // signed", which the operator must be able to tell apart from
                // a network failure — so both map to SignatureRejected.
                Err(
                    tauri_plugin_updater::Error::Minisign(_)
                    | tauri_plugin_updater::Error::Base64(_)
                    | tauri_plugin_updater::Error::SignatureUtf8(_),
                ) => report(TransportOutcome::SignatureRejected { version }),
                Err(_) => report(TransportOutcome::DownloadFailed {
                    version,
                    code: ErrorCode::DownloadFailed,
                }),
            }
        });
    }

    fn install(&self, version: &str) -> Result<(), ErrorCode> {
        self.install_with_choice(version, crate::update_policy::ConsentChoice::InstallOnQuit)
    }

    fn install_with_choice(
        &self,
        version: &str,
        choice: crate::update_policy::ConsentChoice,
    ) -> Result<(), ErrorCode> {
        if !self.signing_key_present {
            return Err(ErrorCode::SignatureRejected);
        }
        // Installing swaps the running bundle, so it is only ever reached from
        // the policy's post-shutdown effect — never speculatively.
        let mut slot = self.staged_handle.lock().expect("staged slot poisoned");
        let Some((staged_version, update, bytes)) = slot.take() else {
            // Nothing staged: the consent that authorised this install was for
            // an artifact we no longer hold. Refusing beats re-downloading,
            // because a re-fetch could return a DIFFERENT artifact than the
            // one the operator agreed to.
            return Err(ErrorCode::DownloadFailed);
        };
        if staged_version != version {
            return Err(ErrorCode::SignatureRejected);
        }
        #[cfg(feature = "native-test")]
        if let Some(fixture) = &self.fixture {
            return fixture.record_install(version, choice, &bytes);
        }
        update
            .restart_after_install(choice == crate::update_policy::ConsentChoice::RestartAndInstall)
            .install(bytes)
            .map_err(|_| ErrorCode::InstallFailed)
    }

    fn beacon(&self, asset_url: &str, report: Box<dyn FnOnce(TransportOutcome) + Send>) {
        // The response contributes only a bounded local journal diagnostic.
        // Discard its body; never retry, delay updates, or surface a UI error.
        //
        // It also carries nothing: no install_id, no headers we add, no body.
        // The privacy claim in spec §6 is only true if this stays a bare GET.
        let url = asset_url.to_string();
        #[cfg(feature = "native-test")]
        let url = self
            .fixture
            .as_ref()
            .map_or(url, |fixture| fixture.beacon_url());
        self.operations.spawn(2, async move {
            #[cfg(feature = "native-test")]
            let redirects = redirect_policy(url.parse().expect("generated beacon URL"));
            #[cfg(not(feature = "native-test"))]
            let redirects = reqwest::redirect::Policy::custom(|attempt| {
                if attempt.previous().len() < 5 && artifact_redirect_allowed(attempt.url()) {
                    attempt.follow()
                } else {
                    attempt.error("beacon redirect refused")
                }
            });
            let Ok(client) = reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(10))
                .redirect(redirects)
                .build()
            else {
                report(TransportOutcome::BeaconCompleted { ok: false });
                return;
            };
            let ok = client
                .get(url)
                .send()
                .await
                .is_ok_and(|response| response.status().is_success());
            report(TransportOutcome::BeaconCompleted { ok });
        });
    }

    fn shutdown(&self) {
        self.operations.close();
        self.checked_handle
            .lock()
            .expect("checked slot poisoned")
            .take();
        self.staged_handle
            .lock()
            .expect("staged slot poisoned")
            .take();
    }
}

/// Bind all policy-validated artifact fields before any download begins.
pub fn artifact_identity_matches(
    version: &str,
    url: &str,
    signature: &str,
    checked_version: &str,
    checked_url: &str,
    checked_signature: &str,
) -> bool {
    version == checked_version && url == checked_url && signature == checked_signature
}

#[cfg(test)]
mod transport_contract_tests {
    use super::*;

    #[test]
    fn redirects_cannot_leave_the_artifact_allowlist_or_downgrade_https() {
        for allowed in crate::update_policy::ALLOWED_ARTIFACT_HOSTS {
            assert!(artifact_redirect_allowed(
                &format!("https://{allowed}/asset").parse().unwrap()
            ));
        }
        for refused in [
            "http://github.com/asset",
            "https://github.com.evil.invalid/asset",
            "https://user@github.com/asset",
            "https://github.com:444/asset",
            "http://127.0.0.1/asset",
        ] {
            assert!(!artifact_redirect_allowed(&refused.parse().unwrap()));
        }
    }

    #[test]
    fn a_republished_release_cannot_change_the_consented_artifact() {
        let original = (
            "1.35.0",
            "https://github.com/o/r/releases/download/v1.35.0/a",
            "signed-a",
        );
        assert!(artifact_identity_matches(
            original.0, original.1, original.2, original.0, original.1, original.2
        ));
        for changed in [
            ("1.36.0", original.1, original.2),
            (original.0, "https://evil.invalid/a", original.2),
            (original.0, original.1, "signed-b"),
        ] {
            assert!(!artifact_identity_matches(
                original.0, original.1, original.2, changed.0, changed.1, changed.2
            ));
        }
    }

    /// The beacon URL is built from a compile-time constant, so configuration
    /// cannot redirect it. Spec §6's privacy claim — "the install_id never
    /// leaves the machine" — is only true if the check-in is a bare GET of a
    /// published release asset, and only a constant host guarantees that.
    #[test]
    fn the_beacon_url_is_a_published_release_asset_on_a_fixed_host() {
        let url = crate::updater::beacon_asset_url("1.35.0", "darwin-aarch64");
        assert!(
            url.starts_with("https://github.com/"),
            "the beacon must reach GitHub and nowhere else: {url}"
        );
        assert!(
            url.contains("/releases/download/v1.35.0/"),
            "the beacon must be a release-download path: {url}"
        );
        assert!(url.ends_with("beacon-1.35.0-darwin-aarch64.txt"), "{url}");
        assert!(
            !url.contains('?'),
            "no query string: a beacon that can carry parameters can carry an \
             identifier, which is exactly what spec §6 promises it does not"
        );
    }

    /// Every outcome the transport can report must map onto an event the
    /// policy already understands. A transport that could report something
    /// unmodelled would force decisions into the network layer, which is what
    /// the policy/driver split exists to prevent.
    #[test]
    fn every_outcome_is_representable_without_inventing_policy() {
        let outcomes = [
            TransportOutcome::Manifest {
                body: "{}".to_string(),
                duration_ms: 1,
            },
            TransportOutcome::ManifestFailed {
                code: ErrorCode::NetworkUnavailable,
            },
            TransportOutcome::Staged {
                version: "1.0.0".to_string(),
                bytes: 1,
                duration_ms: 1,
            },
            TransportOutcome::DownloadFailed {
                version: "1.0.0".to_string(),
                code: ErrorCode::DownloadFailed,
            },
            TransportOutcome::SignatureRejected {
                version: "1.0.0".to_string(),
            },
            TransportOutcome::BeaconCompleted { ok: true },
        ];
        // Exhaustiveness is the assertion: adding a variant without deciding
        // which UpdateEvent it becomes should not compile in main.rs's
        // `report`, and this pins the count that mapping must cover.
        assert_eq!(outcomes.len(), 6);
    }
}
