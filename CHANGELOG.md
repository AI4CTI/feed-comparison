# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release scaffolding under the AI4CTI organisation.
- AGPL-3.0-or-later license, contributor docs, security policy.
- Modern Python toolchain: PEP 621 `pyproject.toml`, `uv` workflow, `hatchling` + `hatch-vcs` build backend, `ruff`, `mypy`, `pre-commit`.

### Removed compared to the original internal version
This first public release intentionally ships a curated subset of the original internal tool. The following components have been removed because they are tied to private infrastructure, depend on commercial APIs we cannot redistribute, or rely on artefacts we cannot publish:

- The `compare-protection` mode and its dependency on a private MongoDB collection.
- The Ermes-internal feed integrations (`ermesv2`, `ermesv2wt`).
- The BrightCloud feed (depends on a proprietary CSV asset).
- The BitDefender feed (commercial API).
- The zVelo PhishBlockList feed (commercial API).
- The bulk OSINT feeds downloader: ~90 third-party block-lists used to be fetched from a private S3 bucket via an internal AWS Lambda. Re-introducing OSINT feed support in a public-friendly way is on the roadmap; see the project README for the current status.
- The Jenkins CI pipeline (replaced by GitHub Actions).
