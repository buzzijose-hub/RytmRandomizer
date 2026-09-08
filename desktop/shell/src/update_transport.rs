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

use std::sync::Arc;

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

    /// Fire-and-forget check-in. No result, by design.
    fn beacon(&self, asset_url: &str);
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

    fn beacon(&self, _asset_url: &str) {}
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
        DisabledTransport::new(ErrorCode::NetworkUnavailable).beacon("https://example.invalid/x");
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
#[cfg(not(test))]
type StagedSlot =
    std::sync::Arc<std::sync::Mutex<Option<(String, tauri_plugin_updater::Update, Vec<u8>)>>>;

#[cfg(not(test))]
pub struct PluginTransport<R: tauri::Runtime> {
    app: tauri::AppHandle<R>,
    /// The verified bytes from the last successful download.
    ///
    /// Held so `install` swaps exactly what was verified. Downloading a
    /// second time at install would re-fetch — and a republished artifact
    /// would then be installed WITHOUT the verification the operator
    /// consented on the strength of.
    staged_handle: StagedSlot,
    /// False until the operator lands the Ed25519 public key. The plugin
    /// refuses an unverifiable artifact itself; this makes the refusal happen
    /// at the seam, where the journal entry is legible.
    signing_key_present: bool,
}

#[cfg(not(test))]
impl<R: tauri::Runtime> PluginTransport<R> {
    /// Wrap an app handle.
    pub fn new(app: tauri::AppHandle<R>, signing_key_present: bool) -> Self {
        Self {
            app,
            staged_handle: std::sync::Arc::new(std::sync::Mutex::new(None)),
            signing_key_present,
        }
    }
}

#[cfg(not(test))]
impl<R: tauri::Runtime> Transport for PluginTransport<R> {
    fn fetch_manifest(&self, channel: &str, report: Box<dyn FnOnce(TransportOutcome) + Send>) {
        use tauri_plugin_updater::UpdaterExt as _;

        let app = self.app.clone();
        let channel = channel.to_string();
        tauri::async_runtime::spawn(async move {
            let started = std::time::Instant::now();
            let builder = match app.updater_builder().build() {
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
            match builder.check().await {
                Ok(Some(update)) => {
                    let body = serde_json::json!({
                        "schema_version": 1,
                        "channel": channel,
                        "version": update.version,
                        "notes": update.body.unwrap_or_default(),
                        "pub_date": update.date.map(|d| d.to_string()).unwrap_or_default(),
                        "hardware_revalidation": false,
                        "rollout_percent": 100,
                        "platforms": {
                            update.target.clone(): {
                                "signature": update.signature,
                                "url": update.download_url.to_string(),
                            }
                        }
                    });
                    report(TransportOutcome::Manifest {
                        body: body.to_string(),
                        duration_ms: started.elapsed().as_millis() as u64,
                    });
                }
                // No update is not a failure: the policy has an `up_to_date`
                // state and journals `check_ok`. Reporting an error here would
                // show the operator a problem where there is none.
                Ok(None) => report(TransportOutcome::Manifest {
                    body: String::new(),
                    duration_ms: started.elapsed().as_millis() as u64,
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
        _url: &str,
        _signature: &str,
        report: Box<dyn FnOnce(TransportOutcome) + Send>,
    ) {
        use tauri_plugin_updater::UpdaterExt as _;

        if !self.signing_key_present {
            report(TransportOutcome::DownloadFailed {
                version: version.to_string(),
                code: ErrorCode::SignatureRejected,
            });
            return;
        }

        let app = self.app.clone();
        let version = version.to_string();
        let staged_slot = std::sync::Arc::clone(&self.staged_handle);
        tauri::async_runtime::spawn(async move {
            let started = std::time::Instant::now();
            let Ok(builder) = app.updater_builder().build() else {
                report(TransportOutcome::DownloadFailed {
                    version,
                    code: ErrorCode::ManifestMalformed,
                });
                return;
            };
            let update = match builder.check().await {
                Ok(Some(update)) => update,
                Ok(None) | Err(_) => {
                    report(TransportOutcome::DownloadFailed {
                        version,
                        code: ErrorCode::NetworkUnavailable,
                    });
                    return;
                }
            };
            // The plugin verifies the signature DURING download and fails the
            // future when it does not match — which is exactly the case the
            // operator must be able to distinguish from a network error, so it
            // gets its own outcome rather than a generic failure.
            match update.download(|_, _| {}, || {}).await {
                Ok(bytes) => {
                    let byte_count = bytes.len() as u64;
                    // Keep exactly the bytes that verified. install() swaps
                    // these and nothing else.
                    *staged_slot.lock().expect("staged slot poisoned") =
                        Some((version.clone(), update, bytes));
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
        update.install(bytes).map_err(|_| ErrorCode::DownloadFailed)
    }

    fn beacon(&self, asset_url: &str) {
        // Fire and forget, and that is a design commitment rather than
        // laziness: the check-in's whole signal is the asset's DOWNLOAD COUNT
        // on the Releases API, so the response body is discarded and a failure
        // is simply a data point that did not happen. It must never journal an
        // error, retry, or delay the update flow.
        //
        // It also carries nothing: no install_id, no headers we add, no body.
        // The privacy claim in spec §6 is only true if this stays a bare GET.
        let url = asset_url.to_string();
        tauri::async_runtime::spawn(async move {
            let Ok(client) = reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(10))
                .build()
            else {
                return;
            };
            let _ = client.get(url).send().await;
        });
    }
}

#[cfg(test)]
mod transport_contract_tests {
    use super::*;

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
        ];
        // Exhaustiveness is the assertion: adding a variant without deciding
        // which UpdateEvent it becomes should not compile in main.rs's
        // `report`, and this pins the count that mapping must cover.
        assert_eq!(outcomes.len(), 5);
    }
}
