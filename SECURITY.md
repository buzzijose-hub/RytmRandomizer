# Security Policy

RytmRandomizer is intended to be installed and run on end-user machines, where
it communicates with MIDI hardware (the Elektron Analog Rytm MK2). Because it is
a consumer-facing tool, we take security and safety reports seriously.

## Reporting a Vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report vulnerabilities privately to the repository owner:

- Use GitHub's **"Report a vulnerability"** feature (Security tab → Advisories)
  on this repository, **or**
- Contact the repository owner directly via the email on their GitHub profile.

When reporting, please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce (a proof of concept is ideal).
- The version / commit of RytmRandomizer affected.
- Any relevant environment details (OS, Python version, MIDI setup).

## Response Time

- **Acknowledgement:** within **3 business days** of receipt.
- **Initial assessment:** within **10 business days**, including a severity
  rating and an expected remediation timeline.
- **Resolution:** we aim to ship a fix or mitigation for confirmed
  high-severity issues as quickly as is practical, and will keep the reporter
  updated on progress.

We will credit reporters in the release notes unless anonymity is requested.

## Supported Versions

RytmRandomizer is pre-1.0 and under active modularization. Security fixes are
applied to the **latest released version only**. Older versions are not
maintained — please upgrade to the latest release before reporting.

| Version            | Supported          |
| ------------------ | ------------------ |
| Latest release     | :white_check_mark: |
| Older releases     | :x:                |

## Scope

In scope:

- The `rytm_randomizer/` package and the `rytm_hybrid_randomizer_v134.py`
  entry point.
- Handling of user-supplied files (kit/pattern/SysEx dumps) and any code paths
  that parse external input.

Out of scope:

- Vulnerabilities in third-party dependencies (report those upstream; we will
  bump the dependency once a fix is available).
- Issues that require physical access to an already-compromised machine.
