---
name: coverage-py-blended-vs-pure-branch
description: coverage.py's fail_under gates on a blended line+branch number; coverage.xml's branch-rate is pure-branch only. They disagree by construction. Pick one metric and pin both gates to it.
user-invocable: false
origin: auto-extracted
---

# coverage.py: blended fail_under vs pure-branch coverage.xml

**Extracted:** 2026-05-15
**Context:** You configure `branch = True` in `.coveragerc` and a `fail_under` floor. You also have a custom ratchet script that reads `coverage.xml` to enforce the same floor. The two disagree by several percentage points and one of them fails in CI.

## Problem

Your CI step runs:

```bash
pytest --cov=mypkg --cov-branch --cov-report=term-missing --cov-report=xml
```

`.coveragerc` says:

```ini
[run]
branch = True
source = mypkg

[report]
fail_under = 86
```

CI logs:

```
Required test coverage of 86.0% reached. Total coverage: 86.06%
```

Then your custom ratchet script runs:

```python
import xml.etree.ElementTree as ET
branch_rate = float(ET.parse("coverage.xml").getroot().get("branch-rate"))
print(f"branch coverage: {branch_rate * 100:.2f}%")
# branch coverage: 78.60%
```

Both numbers are **correct**. They measure different things:

- **`.coveragerc` `fail_under` with `branch = True`**: the BLENDED metric, computed as `(lines_covered + branches_covered) / (lines_valid + branches_valid)`. Always >= pure-branch.
- **`coverage.xml`'s `branch-rate` attribute**: pure branch coverage, `branches_covered / branches_valid` only.

If you naively use the same `fail_under` integer for both, they disagree. The blended one passes, the pure-branch one fails. Your CI green/red light flickers depending on which gate runs first.

## Solution

**Pick one metric and pin both gates to it.** Don't try to make `.coveragerc`'s number satisfy both — they cannot, by construction.

### Option A — pure-branch (stricter, recommended)

Pure branch coverage rewards actually testing the branchy code, not just touching every line. Use it when branch coverage is the metric you actually care about.

```ini
# .coveragerc
[report]
# Ratcheting baseline: pin to PURE-BRANCH percentage. coverage.py's
# blended fail_under is >= pure-branch, so it passes trivially when
# pure-branch passes.
fail_under = 78
```

```python
# scripts/coverage_ratchet.py
def _read_branch_coverage_from_xml(path):
    root = ET.parse(path).getroot()
    return float(root.get("branch-rate")) * 100.0
```

### Option B — blended (looser, what coverage.py does natively)

Use when you accept that line-coverage growth from dead code addition can mask insufficient branch testing.

```python
def _read_total_coverage_from_xml(path):
    root = ET.parse(path).getroot()
    lines_valid = int(root.get("lines-valid"))
    lines_covered = int(root.get("lines-covered"))
    branches_valid = int(root.get("branches-valid"))
    branches_covered = int(root.get("branches-covered"))
    denominator = lines_valid + branches_valid
    return (lines_covered + branches_covered) / denominator * 100.0
```

In both cases, the `.coveragerc` `fail_under` number must match the metric your ratchet/CI computes.

## When to Use

Trigger conditions:

- You're configuring branch coverage AND a ratcheting floor mechanism.
- Your ratchet script disagrees with `.coveragerc`'s `fail_under` verdict and you're not sure why.
- You see `Required test coverage of N% reached. Total coverage: M%` (M > N) followed by a separate "branch coverage below floor" failure.

Diagnostic — when the two numbers seem inconsistent:

```python
import xml.etree.ElementTree as ET
root = ET.parse("coverage.xml").getroot()
print("line-rate:        ", root.get("line-rate"))       # blended numerator (lines only)
print("branch-rate:      ", root.get("branch-rate"))     # PURE branch
print("lines-valid:      ", root.get("lines-valid"))
print("lines-covered:    ", root.get("lines-covered"))
print("branches-valid:   ", root.get("branches-valid"))
print("branches-covered: ", root.get("branches-covered"))
# Blended fail_under = (lines_covered + branches_covered) / (lines_valid + branches_valid)
```

Compute the blended number and the pure-branch number from these primitives. Decide which one IS the floor for your project. Document the choice in `.coveragerc` so the next maintainer doesn't try to "fix" the disagreement.
