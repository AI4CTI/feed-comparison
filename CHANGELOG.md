# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ASCII banner shown on stderr at the top of every CLI invocation (suppressed when stderr isn't a TTY, when `--no-banner` is passed, or when `FEED_COMPARISON_NO_BANNER` is set in the environment). Stays out of stdout so machine-readable subcommands like `list-feeds --json` keep parsing cleanly.
- New `feed-comparison about` subcommand that prints project metadata, repository URLs, license, maintainer, authors, affiliations (Ermes Browser Security · Politecnico di Torino), funding statement (Italian Ministry of Education Grant FISA-2023-00168) and citation hint.

## [0.2.0] — 2026-05-13

### Added
- New `ermes` feed integration over STIX/TAXII with OAuth 2.0 Client Credentials, opt-in via the new `[ermes]` extra (depends on `taxii2-client` and `requests-oauth2client`). Requires `ERMES_API_SERVER`, `ERMES_CLIENT_ID`, `ERMES_CLIENT_SECRET`. Surfaced in `feed-comparison list-feeds` for everyone, gated by credentials at fetch time (clean `MissingCredentialsError` for users without access).
- Pagination progress logs (per-page IoC counts, per-interval rate, advancing-timeline indicator) for `ermes` and `phishstats` feeds.
- `MAX_PAGES_SAFETY` hard cap on both `ermes` (TAXII) and `phishstats` paginated downloads — protects against runaway pagination from a misbehaving server; emits a clear WARNING when tripped.
- Optional `skip_recent_days` hint on the `Feed` Protocol; the `ermes` implementation uses it to early-stop TAXII pagination once `newest_seen > now − N days`. The other feeds accept it for protocol compliance and ignore it (their endpoints don't paginate in a way that benefits). The CLI threads `--ignore-last-days` to this hint automatically.
- Test suite grown to 141 tests (was 105 at v0.1.0). Coverage steady at ~75% overall, 92% on the canonicalisation modules.

### Changed
- Pagination progress log for `ermes`: replaced the misleading "oldest IoC" indicator (which locks to the cutoff for ASC-sorted feeds and never moves) with "newest IoC reached" (decreases monotonically toward 0 days back), giving the user a real progress signal.
- Larger TAXII page size (50 → 200) to reduce round-trips on the slow upstream server.

### Fixed
- Time-delta CDF: normalise tz-aware vs tz-naive timestamps before subtraction. Previously the Ermes feed's offset-aware timestamps mixed with the naive-UTC timestamps from the other feeds caused a `TypeError` mid-pipeline.
- Time-delta CDF: replace the deprecated pandas-1.x `astype("timedelta64[h]")` cast with `.dt.total_seconds() / 86400` for pandas 2.x compatibility.
- `compare` and `download` CLI: catch ALL per-feed exceptions (not just the typed ones) so an unexpected failure in one feed doesn't abort the entire run. The full traceback is still available with `--verbose`.
- Ermes feed: surface OAuth authentication failures as a typed `FeedConfigurationError` with an actionable message naming the env vars to verify, instead of a raw OAuth2 traceback.

### Security
- New `bounded_get` HTTP wrapper: caps response size to 256 MiB (configurable per call) and streams the body. Raises `ResponseTooLargeError` on cap breach, preventing memory exhaustion from a compromised or misbehaving upstream. Used by `phishstats`, `phishtank` and `urlscan`.
- Logging hardening: pin `urllib3`, `requests`, `requests_oauth2client`, `taxii2client` and `pymisp` loggers to INFO even with `--verbose`, to prevent leakage of `Authorization: Bearer …` and other credentials in the debug output.
- `Settings.__repr__` overridden to mask credential fields (`client_secret`, `misp_key`, `urlscan_token`, …) — prevents accidental leakage when the Settings object is printed/logged during debugging.

## [0.1.0] — 2026-05-06

First public release under the [AI4CTI](https://github.com/AI4CTI) organisation, on GitHub at <https://github.com/AI4CTI/feed-comparison>. The previous lifetime of this codebase as an Ermes-internal tool is intentionally not part of the public git history.

### Added
- AGPL-3.0-or-later license; AI4CTI attribution and funding statement (Italian Ministry of Education, Grant FISA-2023-00168).
- Modern Python toolchain: PEP 621 `pyproject.toml`, `uv` workflow, `hatchling` + `hatch-vcs` build backend, `ruff`, `mypy`, `pre-commit`.
- Typer-based command-line interface with four subcommands: `list-feeds`, `download`, `compare`, `plot`. Layered configuration via flags, environment variables and `.env`.
- Pluggable feed architecture: `Feed` Protocol + `FeedRegistry` singleton. Adding a new feed is a self-contained module that registers an instance via import side-effect.
- Four built-in feed integrations: PhishStats, PhishTank, urlscan.io, MISP (the latter as opt-in `[misp]` extra).
- URL canonicalisation pipeline (`utils/canonicalize.py` + `utils/normalize.py`) following Google Safe Browsing semantics.
- Overlap analysis (SuperVenn) and time-delta CDF plotting helpers (`utils/plots.py`).
- Test suite of 105 tests with ~75% line coverage; 92% on the canonicalisation modules. HTTP-based feeds are tested with the `responses` library — no real network traffic in CI.
- GitHub Actions CI matrix on Python 3.10 to 3.13 (lint, typecheck, test). CodeQL Python scanning. Dependabot weekly updates for `pip` and `github-actions`.

### Fixed
- `time.force_temporal_boundaries` now correctly accumulates the overall min/max across feeds instead of using the last feed's boundaries only (the legacy implementation overwrote both inside the per-feed loop).
- The fragile `feed = filename.split('_')[1]` heuristic used to load CSV exports has been removed; `plot` now parses filenames from the right and tolerates feed names that contain underscores.
- `time._discovered_date_column` is anchored to the singular column name and no longer accidentally returns the plural list-valued column.
- Several lint warnings inherited from the legacy code (redundant boolean returns, unused loop variables, printf-style formatting) have been resolved.

### Removed compared to the original internal version

This first public release intentionally ships a curated subset of the original internal tool. The following components have been removed because they are tied to private infrastructure, depend on commercial APIs we cannot redistribute, or rely on artefacts we cannot publish:

- The `compare-protection` mode and its dependency on a private MongoDB collection.
- The Ermes-internal feed integrations (`ermesv2`, `ermesv2wt`).
- The BrightCloud feed (depends on a proprietary CSV asset).
- The BitDefender feed (commercial API).
- The zVelo PhishBlockList feed (commercial API).
- The bulk OSINT feeds downloader: ~90 third-party block-lists used to be fetched from a private S3 bucket via an internal AWS Lambda. Re-introducing OSINT feed support in a public-friendly way is on the roadmap for a future `v0.2.x` release.
- The Jenkins CI pipeline (replaced by GitHub Actions).
- The legacy global `available_feeds` mapping; every feed now carries its own `short_name` used as the column suffix in merged DataFrames.
