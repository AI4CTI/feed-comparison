# feed-comparison

[![CI](https://github.com/AI4CTI/feed-comparison/actions/workflows/ci.yml/badge.svg)](https://github.com/AI4CTI/feed-comparison/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org)

A reproducible command-line tool to **compare and benchmark feeds of malicious URLs**: download samples from threat-intelligence providers, normalise the URLs they expose with Google Safe Browsing-style canonicalisation, and quantify how the feeds **overlap** (SuperVenn) and how their **discovery times** compare (CDF of per-URL deltas).

> **Citation.** If you use this tool in academic work, please cite it via the metadata in [`CITATION.cff`](CITATION.cff). A Zenodo DOI will be attached to the first tagged release.

> **Funding.** This work was carried out within **AI4CTI** (a joint research initiative between [Politecnico di Torino](https://www.polito.it/) and [Ermes Browser Security](https://www.ermes.company/)) and is **funded by the Italian Ministry of Education, Grant FISA-2023-00168**.

## Background

Threat-intelligence feeds for malicious URLs are usually consumed in isolation, but their **coverage**, **freshness** and **mutual overlap** vary significantly. This makes it hard to answer practical questions like *"if I already subscribe to feed A, what extra signal does feed B give me?"* or *"how many days earlier does feed A surface a phishing campaign compared to feed B?"*. `feed-comparison` provides a small, reproducible workflow to answer those questions on the feeds you have access to.

## Features in v0.1.0

- **Four feed integrations** out of the box: PhishStats (anonymous), PhishTank (free username), urlscan.io (API token) and MISP (self-hosted instance, optional extra).
- **URL canonicalisation** following the Google Safe Browsing approach (host normalisation, IDNA, percent-encoding, query-string sorting...). 92% line coverage in tests against ~60 reference cases.
- **Overlap analysis** with SuperVenn plots over hostname, registered domain or full normalised URL.
- **Time-delta analysis**: CDF of per-URL discovery deltas relative to a chosen benchmark feed.
- **Discoverable CLI** built with [Typer](https://typer.tiangolo.com): `list-feeds`, `download`, `compare`, `plot`. Rich-formatted output, JSON mode for scripting, layered configuration via `.env`/environment.
- **Reproducible builds**: PEP 621 `pyproject.toml`, `uv`-managed lockfile, `hatchling` build backend, GitHub Actions CI on Python 3.10 to 3.13.

See the [Limitations](#limitations) section below for what *isn't* shipped in v0.1.0.

## Install

The package is not yet on PyPI; for the v0.1.0 release we recommend installing from source:

```bash
git clone https://github.com/AI4CTI/feed-comparison.git
cd feed-comparison
uv tool install .
# or, with pipx:
# pipx install .
```

If you want to develop on the codebase:

```bash
uv sync --extra dev
uv run pre-commit install
uv run pytest
```

The MISP integration is opt-in (it pulls in the heavy `pymisp` dependency):

```bash
uv tool install '.[misp]'
```

## Quickstart

```bash
# 1. List the feeds the tool knows about, and which credentials they need.
feed-comparison list-feeds

# 2. Download a one-day sample from PhishStats (no credentials required).
feed-comparison download phishstats --days 1 --output-dir ./output

# 3. Compare two feeds: SuperVenn + time-delta CDF in ./output.
feed-comparison compare phishstats phishtank --days 1 --benchmark phishstats

# 4. Re-render plots from previously saved CSVs without re-downloading.
feed-comparison plot supervenn ./output/dataframe_*.csv --metric domain
```

## Configuration

Per-feed credentials are read from environment variables (and from a `.env` file in the current working directory if present). Only the variables for the feeds you actually use are required:

| Env var               | Used by    | Notes                                       |
| --------------------- | ---------- | ------------------------------------------- |
| `MISP_URL`            | MISP       | Base URL of your self-hosted MISP instance  |
| `MISP_KEY`            | MISP       | API key                                     |
| `PHISHTANK_USERNAME`  | PhishTank  | Free username for the User-Agent string     |
| `URLSCAN_URL`         | urlscan.io | Search API endpoint, e.g. `.../api/v1/search/` |
| `URLSCAN_TOKEN`       | urlscan.io | API token                                   |
| `FEED_COMPARISON_OUTPUT_DIR` | global | Default output directory               |

A reference template lives in [`.env.example`](.env.example).

## Available feeds

| Name        | Provider                            | Credentials                       |
| ----------- | ----------------------------------- | --------------------------------- |
| `phishstats`| <https://phishstats.info/>          | none                              |
| `phishtank` | <https://phishtank.org/>            | free username                     |
| `urlscan`   | <https://urlscan.io/>               | endpoint URL + API token          |
| `misp`      | <https://www.misp-project.org/>     | self-hosted instance URL + API key (extra `[misp]`) |

`feed-comparison list-feeds --json` prints the same catalogue in machine-readable form for scripting.

## Limitations

- The original internal version supported additional commercial feeds (BitDefender, BrightCloud, zVelo PhishBlockList) and a "compare-protection" mode that queried Ermes' MongoDB. These are **not** part of the public release. See [`CHANGELOG.md`](CHANGELOG.md) for the full list of removed components and the rationale.
- The original internal version also supported ~90 OSINT block-lists fetched from a private S3 bucket. A public-friendly OSINT downloader is on the roadmap for `v0.2.x`; in `v0.1.0` only the four API-based feeds above are available.
- `phishstats.info` is occasionally rate-limited or unavailable upstream (HTTP 5xx via Cloudflare). The tool reports this with a warning and exits gracefully.

## Contributing

Contributions are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development setup, coding conventions and how to add new feed integrations.

## Security

Please report vulnerabilities privately via the channel documented in [`SECURITY.md`](SECURITY.md). Do not open public issues for security-sensitive matters.

## License

This project is distributed under the GNU Affero General Public License v3.0 or later. See [`LICENSE`](LICENSE) for the full text.

The AGPL choice means that running a modified version as a network service requires sharing the modified source code with the users of that service. We picked AGPLv3 to keep the tool, and any derivative offered as a hosted service, fully open as a deliverable of a publicly-funded research project.

## Acknowledgements

`feed-comparison` was originally developed inside [Ermes Browser Security](https://www.ermes.company/) and is being released as open source under the [AI4CTI](https://ai4cti.polito.it/) joint research initiative with the [Politecnico di Torino](https://www.polito.it/), funded by the Italian Ministry of Education, Grant FISA-2023-00168.
