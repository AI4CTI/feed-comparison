# Security policy

## Supported versions

`feed-comparison` is a research-grade tool released as part of the publicly-funded [AI4CTI](https://ai4cti.polito.it/) initiative. We follow a single-stream support model: only the **latest released minor version** receives security fixes. Earlier versions are not patched.

| Version | Supported            |
| ------- | -------------------- |
| 0.1.x   | ✅ (current release) |
| < 0.1   | ❌                   |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive matters. Instead, contact us privately at:

> **info@ermes.company** — please include `[feed-comparison security]` in the subject line so the message is routed to the maintainers.

What to include in your report:

- A clear description of the issue and the impact you observed.
- A minimal reproduction (CLI command, config, sample data).
- The version of `feed-comparison` you tested (`feed-comparison --version`).

## Process and timing

This is a research project, not a commercial product, so we cannot offer enterprise-grade SLAs. We commit to:

- **Acknowledgement** within **14 days** of receipt.
- An assessment and indicative remediation timeline within **30 days**.
- A coordinated disclosure once a fix is available; we are happy to credit reporters in the release notes unless they prefer to remain anonymous.

If a vulnerability is in a third-party dependency, we will route the report to the upstream project (and CC you).

## Out of scope

- Issues that require attacker-controlled credentials for the third-party feeds.
- Vulnerabilities only reachable when the user runs the tool against an attacker-controlled malicious feed endpoint configured by themselves.
- Findings against the legacy internal Ermes version of this codebase, which is not part of the public release (see [`CHANGELOG.md`](CHANGELOG.md)).
