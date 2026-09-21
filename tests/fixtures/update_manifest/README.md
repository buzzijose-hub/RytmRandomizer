# Update-manifest contract fixtures (I3 + I6, abstraction R2)

These files are the **cross-language single source of truth** for the
auto-update manifest. They are consumed by three independent
implementations and must stay pure JSON with no language-specific
fields:

| Consumer | What it reads | Why |
|---|---|---|
| Python — `scripts/validate_manifest.py` over `scripts/release_lib.py` | `manifest.v1.json`, every `invalid/*.json` | the validator's golden corpus; each invalid file must be refused with the reason code its filename names |
| Rust — `desktop/shell/src/update_policy.rs` | `manifest.v1.json`, `invalid/*.json`, `bucket_vectors.json` | serde round-trip, refusal parity with Python, rollout bucketing |
| TypeScript — `desktop/web/e2e/` mock manifest server | `manifest.v1.json` | the e2e mock serves this byte-for-byte |

Owner: agent **A5** (plan `2026-09-07-autoupdate-implementation.md`,
contracts I3 and I6). Design source of truth:
[`2026-08-03-autoupdate-distribution.md`](../../../docs/superpowers/plans/2026-08-03-autoupdate-distribution.md)
§4 (schema) and §6 (beacon). Changing any file here is a
cross-language contract change: update all three consumers in the same
PR.

---

## `manifest.v1.json` — contract I3

The one valid manifest. It is the spec §4 document shape with the
placeholder ellipses replaced by realistic values; the field set,
including `build` and the `null` `minimum_version`, is that section
verbatim.

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | must be a value the client understands — today exactly `1`. An unrecognised value is refused outright ("manifest not understood"), never best-effort parsed |
| `channel` | string | `"stable"` or `"beta"` |
| `version` | string | strict SemVer (`MAJOR.MINOR.PATCH`, optional `-prerelease`); no `v` prefix |
| `pub_date` | string | RFC 3339 UTC instant, `Z`-suffixed |
| `notes` | string | markdown excerpt of the generated changelog, shown in the consent prompt |
| `hardware_revalidation` | boolean | spec §2.7 — drives the loud banner in the update panel |
| `rollout_percent` | integer | `0..=100` inclusive. **Absent means 100** (spec §4), so there is deliberately no `missing_rollout_percent` fixture |
| `minimum_version` | string or `null` | strict SemVer and `<= version` when present. **Advisory-banner-only in v1** — it never blocks an update |
| `build` | object | informational provenance: `source_sha`, `workflow_run_url`, `builder_workflow_sha`. Its shape is checked, but **a client must never refuse an update over a provenance field** (spec §4) |
| `platforms` | object | non-empty; keys from the target table below |

Each `platforms` entry is an object with exactly two keys:

- `signature` — the Tauri updater Ed25519 signature, base64.
- `url` — an `https://` URL on `github.com` under
  `/<owner>/<repo>/releases/download/v<version>/…`. Host pinning plus
  the tag check is what stops a valid-looking manifest from pointing a
  fleet at an attacker-controlled artifact.

### Forward compatibility — unknown keys

Spec §4 is explicit and the two levels differ, deliberately:

- **Unknown *top-level* keys are IGNORED**, not refused.
  `schema_version` is what gates interpretation, so a v1 client
  tolerating a field a future v2 adds is exactly the forward
  compatibility the schema version exists to provide. There is
  therefore no `unknown_field` fixture — a manifest carrying one is
  *valid*.
- **Unknown keys inside a `platforms` entry ARE refused**
  (`platform_entry_unknown_field`). A platform entry is the security
  boundary: it names the bytes that will be downloaded and executed.
  Silently ignoring an unrecognised key there would let a future
  required field — a checksum, an alternate URL — be dropped by an old
  client without anyone noticing.

### Platform target strings (normative)

These exact strings are the manifest keys **and** the `<target>`
component of the I6 ping asset name. They are the Tauri updater's own
target-triple shorthand; do not invent variants.

| Target | Artifact shape |
|---|---|
| `darwin-aarch64` | `.app.tar.gz` (Apple silicon) |
| `darwin-x86_64` | `.app.tar.gz` (Intel Mac) |
| `windows-x86_64` | `-setup.nsis.zip` |
| `linux-x86_64` | `.AppImage.tar.gz` |

Spec §12 notes that `.deb` / `.rpm` installs update through the distro
package manager and get the chip as notification only; they are
deliberately **not** manifest targets.

---

## `invalid/` — the refusal corpus

One file per typed violation, named for the reason code the validator
must emit. Every file is the canonical `manifest.v1.json` with exactly
one field mutated, so the fixture isolates a single rule. The Python
validator (`release_lib.validate_manifest`) and the Rust serde/policy
layer must BOTH refuse every one of them.

The filename **is** the contract: `invalid/unknown_channel.json` must
produce a violation whose `.code` is `unknown_channel`. A validator
that refuses the file for a different reason is still wrong — it means
the two implementations can diverge on which rule fired, and
`manifest-validate.yml`'s step summary would name the wrong rule to the
operator.

Codes, grouped:

**Required fields absent** — `missing_schema_version`,
`missing_channel`, `missing_version`, `missing_notes`,
`missing_pub_date`, `missing_hardware_revalidation`,
`missing_platforms`. (`rollout_percent` and `minimum_version` are
optional; `build` is required in generated manifests but is provenance
— see below.)

**Document-level value violations** — `unsupported_schema_version`,
`schema_version_not_integer`, `unknown_channel`, `channel_not_string`,
`version_not_semver`, `version_not_string`, `notes_not_string`,
`pub_date_not_rfc3339`, `hardware_revalidation_not_boolean`,
`rollout_percent_not_integer`, `rollout_percent_out_of_range`,
`minimum_version_not_semver`, `minimum_version_exceeds_version`,
`build_not_object`.

**Platform-map violations** — `platforms_not_object`,
`platforms_empty`, `unknown_platform_target`,
`platform_entry_not_object`, `platform_missing_signature`,
`platform_missing_url`, `platform_signature_empty`,
`platform_signature_not_base64`, `platform_url_not_https`,
`platform_url_host_not_allowed`, `platform_url_version_mismatch`,
`platform_entry_unknown_field`.

`build_not_object` is the one provenance refusal, and it is a *shape*
check, not an eligibility check: a `build` that is not an object means
the generator malfunctioned. Spec §4's "a client must not refuse an
update over provenance fields" governs the *contents* — a stale
`workflow_run_url` or an unrecognised `source_sha` is never grounds for
refusing an update.

Adding a rule means adding a fixture here, a code to the Python
taxonomy, and a Rust refusal arm — in one PR.

### Message discipline

A violation's `message` is bounded and **path-free**: it names the JSON
pointer of the offending field and the rule, never a filesystem path,
and never an attacker-controlled value verbatim (a URL or signature is
echoed truncated). The validator runs in CI where its output lands in a
public step summary.

---

## `bucket_vectors.json` — staged-rollout bucketing

Spec §5's deterministic bucketing, pinned to exact numbers so the Rust
implementation cannot silently disagree with the Python one.

The rule, stated so there is no room for interpretation:

```
digest   = SHA-256(utf8_bytes(install_id))
prefix   = digest[0..4]                    # first four bytes
value    = u32::from_be_bytes(prefix)      # BIG-endian
bucket   = value % 100                     # 0..=99
eligible = bucket < rollout_percent
```

Endianness is the trap. `from_be_bytes` and `from_le_bytes` give
different buckets for the same install; the `prefix_u32_be` field in
each vector exists so an implementation can assert the intermediate
value and localise a mismatch to the byte order rather than to the
hash.

`rollout_percent: 0` admits nobody (no bucket is `< 0`);
`rollout_percent: 100` admits everybody (every bucket is `< 100`).
Because eligibility is a `<` comparison against a stable per-install
bucket, every percentage step is a strict superset of the last — an
install eligible at 10% is still eligible at 50%. Nobody flaps in and
out of a rollout as the percentage rises.

Each vector's `eligible_at_rollout_percent` map deliberately includes
the pair straddling that install's own bucket (`bucket` ⇒ false,
`bucket + 1` ⇒ true), which is the off-by-one the `<` versus `<=`
mistake produces. `boundary_cases` pre-computes the whole eligible-id
set at 0 / 10 / 50 / 100 so a test can assert it in one comparison.

---

## Ping assets — contract I6

`release.yml` uploads one **one-byte** asset per OS target to every
GitHub Release:

```
beacon-<version>-<target>.txt
```

`<version>` is the release version without the `v` prefix (matching
`manifest.version`); `<target>` is one of the four target strings
above — the same strings, so a client derives its beacon URL from the
platform key it already resolved. For `1.35.1` that is exactly four
assets:

```
beacon-1.35.1-darwin-aarch64.txt
beacon-1.35.1-darwin-x86_64.txt
beacon-1.35.1-windows-x86_64.txt
beacon-1.35.1-linux-x86_64.txt
```

Each file's content is a single `.` (0x2E) — one byte, no newline.

**Why a one-byte file is the whole beacon.** Spec §6 gets fleet
awareness from GitHub's own per-asset download counter. A client
running `1.35.1` on `darwin-aarch64` issues a fire-and-forget GET for
its own beacon asset; the Releases API download count for that asset
then *is* the version histogram, per version per OS, with zero
infrastructure and zero PII — the request carries no id, no query
string, and nothing that distinguishes one install from another. The
asset is one byte so the ping costs less than the TLS handshake that
carries it.

Consequences the consumers must honour:

- The ping is **never** on the update's critical path. A failed or
  blocked ping is journalled (`ping_failed`) and dropped; it can never
  delay, gate, or fail a check, a download, or an install. Spec §6
  pins this with a dedicated test, and PR-C's e2e suite proves it by
  pointing the beacon URL at a dead port and asserting the chip still
  appears.
- `RYTM_RAND_UPDATES=off` disables it along with everything else;
  `RYTM_RAND_UPDATE_BEACON=off` disables the ping alone
  (check-but-don't-report).
- The release train uploads the assets even when the beacon is
  disabled fleet-wide — a missing asset would turn a client's optional
  ping into a 404 in its journal.

The upload step itself is owned by agent **C-snap**; `release.yml`
carries a marked insertion point for it in the `manifest` job.
