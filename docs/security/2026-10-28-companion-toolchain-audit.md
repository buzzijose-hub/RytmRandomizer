# Companion Build-Tool Audit

Status: documented, unresolved development-tool dependency debt. No advisory
is dismissed here. This is separate from current-source CodeQL/Python security
checks and from hardware or protected human approval.

## Retained Evidence

The October27 audit used the unchanged lockfile at companion head 80c5b53d:

- `desktop/web/package-lock.json` SHA256
  `dac025500f4c28c6ecf18d458adacd5800d2726ab09ea604cc9ecbd632c53b27`.
- `npm audit --json`: exit1, eight affected package groups (five high, three
  moderate), retained as `output/local/companion-npm-audit.json`, SHA256
  `be302c47e1fe7f530f2fc650d4e13adf773a60cc07e5cb3bd04b4fb96878b215`.
- `npm audit --omit=dev --json`: exit0, zero advisories in that projection,
  retained as `output/local/companion-npm-runtime-audit.json`, SHA256
  `38b3d296273e61398dea149829e026714c02baff2c5592b559d0c91977bf4a69`.

All affected lockfile entries are development dependencies:

| Package Group | Severity | Disposition |
| --- | --- | --- |
| @vitest/coverage-v8 | Moderate | Pending reviewed toolchain update |
| @vitest/mocker | Moderate | Pending reviewed toolchain update |
| vitest | Moderate | Pending reviewed toolchain update |
| vite | High | Pending reviewed toolchain update |
| brace-expansion | High | Pending reviewed transitive update |
| js-yaml | High | Pending reviewed transitive update |
| nanoid | High | Pending reviewed transitive update |
| source-map-js | High | Pending reviewed transitive update |

Exact advisory URLs, affected ranges, dependency paths and suggested fixes are
preserved in the complete audit JSON; package-group counts are not a count of
distinct vulnerabilities. The registry may change after this dated snapshot.
Reproduce with the locked install and both commands above, without running
advisory exploit samples or an automatic `npm audit fix`.

## Reachability And Limits

The companion portable workflow ships a frozen Python sidecar and a Rust shell
with embedded static frontend assets. It does not ship `node_modules`, npm,
Vitest, or a Vite development server. The reviewed runtime `src` imports and
the two generated JavaScript source maps have no modules from the affected
package groups (98 and one mapped source respectively). These observations
support a limited inference: these Node execution paths are not part of the
packaged app's runtime. They do not prove build-time safety or absence of
other vulnerabilities. Downloaded binary/frontend identity and actual runtime
acceptance are separate delivery gates, recorded in the matching receipt.

Development tools can still process hostile project/configuration material or
expose development endpoints. Keep development services loopback-only and do
not use untrusted repositories, configuration or generated input in this build
environment. No production safety boundary or scanner is disabled. No pin,
lockfile, hardware dependency, audit suppression or alert state is changed.
Coordinate the necessary toolchain upgrade as a separately verified change;
the companion cancellation repair does not claim to remediate this debt.
