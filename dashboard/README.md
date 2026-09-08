# Fleet dashboard

`index.html` is the RytmRandomizer fleet dashboard: one self-contained static
page that answers "which versions is the fleet running, per OS, and how is the
current rollout going?"

It is specified in
[`docs/superpowers/plans/2026-08-03-autoupdate-distribution.md`](../docs/superpowers/plans/2026-08-03-autoupdate-distribution.md)
§6.1.

## How it is served

The page is published to GitHub Pages from the **`releases`** branch, alongside
the `fleet-history.json` file it reads. Living next to its data is the whole
trick: the fetch is same-origin, so there is no CORS configuration, no API
token, no build step, and no service anyone has to operate or pay for.

Deploying it means copying `index.html` to the root of the `releases` branch.
Enabling Pages on that branch is a one-time repo setting (operator action item
4 in the implementation plan).

## What it must never grow

These are load-bearing properties, not preferences — `tests/test_fleet_dashboard.py`
enforces each one:

- **No external requests.** No CDN, no font host, no analytics, no chart
  library. The only network call the page makes is `fetch("fleet-history.json")`
  from its own directory. A reader behind a restrictive network, or someone
  reading a checked-out copy of the branch offline, gets the full page.
- **No build step.** What is committed is what is served. Nothing transpiles,
  bundles, or minifies it.
- **No hardcoded versions.** Every series is derived from the data. A literal
  SemVer string anywhere in the script is a test failure.
- **No colour-only encoding.** Each version carries a distinct dash pattern and
  a glyph as well as a hue; promote markers carry a rule, a caret, and text.
  Light and dark palettes are defined separately.
- **An empty or malformed history renders "No data yet."** — never a broken
  chart and never a thrown exception.

## The data it reads

`fleet-history.json` is an array of snapshot rows appended by the scheduled
`fleet-snapshot.yml` workflow. The row shape is frozen as interface contract
I5:

```json
{
  "date": "2026-09-02",
  "counts": { "1.35.0": { "darwin-aarch64": 1440, "windows-x86_64": 840 } },
  "stable": { "version": "1.35.0", "rollout_percent": 100 },
  "beta": { "version": "1.35.1-beta.1", "rollout_percent": 100 }
}
```

`counts` holds GitHub's release-asset `download_count` for each per-version,
per-OS beacon asset. **Those counters are cumulative** — they only ever grow.

## What the numbers mean

One measurement underlies the whole page: an anonymous **check-in**. When a
client checks for an update it also fetches a tiny marker asset for its own
version and OS, and GitHub increments that asset's download counter. No
identifier is transmitted; the `install_id` used for rollout bucketing never
leaves the machine.

Because the counters are cumulative, the page charts the **difference between
consecutive snapshots** — check-ins that arrived during each interval — and
converts that to a device figure by dividing by how often one device is
expected to check in:

```
estimated devices = check-ins in the interval
                  ÷ (interval length in days × 6)
```

The 6 comes from the D2 cadence: launch plus every 4 hours while running. The
divisor scales with the actual gap between snapshots, so a missed cron run
reads as a longer interval rather than as a doubled fleet.

### The honest limits

- It is an **estimate, not a count**, and it is **not a count of unique
  devices**. A machine left running all day looks like several machines used
  briefly; a machine that is switched off contributes nothing.
- It cannot tell you that any particular machine is on any particular version.
- Raw check-in totals are the ground truth, and the page shows them beside
  every estimate — in the composition table and in each chart point's tooltip.
- A **single snapshot cannot be charted**: one cumulative reading carries no
  rate information, so N snapshots yield N−1 intervals and a lone row renders
  the empty state rather than presenting the counter's whole lifetime as one
  interval's traffic.
- A **negative delta** means a release was re-cut and its assets replaced. The
  interval is clamped to zero and the page says so, rather than drawing a dip
  that never happened.
- Per-version resolution begins with the first release that shipped beacon
  assets; a client that never updates past a pre-beacon version is invisible.

This caveat is stated on the page itself, in prose, above the charts — not
buried in a comment. That is a requirement, and a test asserts it.

## What it renders

1. **Fleet composition now** — estimated devices per version for the most
   recent interval, as horizontal bars stacked by OS, with a table repeating
   each estimate beside its raw check-in count and the version's share.
2. **Rollout adoption over time** — estimated devices per version across every
   interval, with **promote markers**: dashed rules wherever a channel changed
   its target version or its `rollout_percent`. Those markers are what make the
   page a rollout monitor rather than a snapshot — you watch the curve bend
   after each promote.
3. **Rollout promotions** — the same channel changes as a table, so a promotion
   recorded outside the charted window is still visible.

## Testing it

`tests/test_fleet_dashboard.py` covers both layers:

- The **source contract** is checked with Python's `html.parser`: self-
  containment, the mount points, the caveat prose, the cadence constant, the
  light/dark palettes.
- The **behavioural render** extracts the page's inline module, runs it under
  `node` against `tests/fixtures/fleet/synthetic_history.json`, and parses the
  markup it produces — asserting every fixture version is charted, every
  channel change gets a marker, estimates match an independently re-derived
  delta calculation, and the empty, malformed, single-snapshot, flat-counter,
  counter-reset, uneven-spacing, and XSS cases all behave.

```bash
python -m pytest tests/test_fleet_dashboard.py
```

The synthetic fixture is deliberately cumulative and monotonic — a test
enforces that. A per-interval fixture would silently validate the wrong
estimator against data no real snapshot could produce.
