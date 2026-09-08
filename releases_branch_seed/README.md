# The `releases` branch

This directory is the **seed content** of the orphan `releases` branch — the
static distribution surface of the auto-update system
([spec §3](../docs/superpowers/plans/2026-08-03-autoupdate-distribution.md)).
It is published once by
[`scripts/bootstrap_releases_branch.py`](../scripts/bootstrap_releases_branch.py),
which creates the branch if it is absent and is a no-op ever after.

**This branch is machine-written. Do not hand-edit it.** Every file on it is
produced by a workflow. A manual edit is silently overwritten by the next
release, promote, or snapshot run — and, worse, an edit that breaks the schema
breaks the update check for every installed client at once. There are no
servers in this design (spec §0.2); these files *are* the service.

## What lives here and who writes it

| File | Written by | When |
|---|---|---|
| `beta.json` | `release.yml` (`manifest` job) | every `v*` tag push |
| `stable.json` | `promote.yml` (environment `stable-promote`, human-approved) | a maintainer-approved promote run |
| `fleet-history.json` | `fleet-snapshot.yml` | every 6 h, and only when the counts actually changed |

Every push to this branch is validated by `manifest-validate.yml`, which runs
the same `scripts/release_lib.py` validator that generated the file — the last
gate in front of the fleet. `test.yml` deliberately does **not** run here
(`branches-ignore: ["releases"]`): the full suite has nothing to say about a
manifest commit, and running it would burn CI minutes on every snapshot.

## Channel manifests (`stable.json`, `beta.json`)

The shape is the spec §4 v1 channel manifest. `rollout_percent` gates staged
rollout: a client hashes its anonymous `install_id` into a 0–99 bucket and takes
the update only when `bucket < rollout_percent`.

Promotion and rollback are both one-line, reviewable, revertable commits to
these files. Rollback = re-point `stable.json` at the previous release; clients
that already updated stay put, and clients that have not yet updated never see
the bad version.

### The seeded manifests are empty — and that is a valid, successful state

These two manifests are the **first thing every client ever fetches**, from the
first launch of the first install, before any release exists.

An empty manifest means exactly one thing to a client:

> **No update is available.** Not an error, not a failed check, not a degraded
> state. The check succeeded and the answer was "you are current."

A client that fetches a seed manifest must record a successful check
(`check_ok`, spec §5.1) and show no update chip. It must **not** raise, must not
journal a failure, must not enter a retry-backoff loop, and must not surface
anything to the operator. A fleet-wide false error on day one would be
indistinguishable from the update system being broken.

The seed encodes "no update" **three independent ways**, so no single client-side
reading mistake can turn it into an offer or an error:

1. `version` is `"0.0.0"` — strict SemVer, so it parses cleanly under the §4
   rule, and it is the lowest possible version, so it is never *newer* than the
   running version. The §4 client rule ("acts only when it is newer") therefore
   declines on its own. Note this is deliberately **not** `null`: `null` would
   fail the "`version` strict SemVer" rule and make the very first fetch a
   validation failure rather than a clean "no update".
2. `platforms` is `{}` — there is no artifact to download on any target, so
   there is nothing to stage even if a client somehow got past rule 1.
3. `rollout_percent` is `0` — no bucket satisfies `bucket < 0`, so the update is
   offered to nobody.

`build` carries zero-SHA placeholders because it is informational provenance
only; §4 forbids a client refusing an update over provenance fields, so these
values are inert. `pub_date` is the epoch for the same reason.

## Fleet history (`fleet-history.json`)

A JSON array of the snapshot rows defined by interface contract I5:
`{date, counts: {version: {os: n}}, stable: {version, rollout_percent},
beta: {version, rollout_percent}}`.

It seeds as `[]` — an empty history is a fleet nobody has measured yet, again
not an error. The dashboard (spec §6.1) renders an empty state from it rather
than failing.

## Bootstrapping

```bash
python scripts/bootstrap_releases_branch.py --dry-run   # report only
python scripts/bootstrap_releases_branch.py             # create if absent
```

The script never pushes, never force-updates a ref, never checks anything out,
and never touches your working tree or index. Publishing the branch to the
remote is a deliberate operator (or workflow) step.
