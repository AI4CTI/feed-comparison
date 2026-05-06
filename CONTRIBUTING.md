# Contributing to feed-comparison

Thank you for your interest in contributing! This is a small research-grade tool, so we keep the workflow lightweight.

## Code of conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating you agree to abide by its terms.

## Development setup

You need [`uv`](https://docs.astral.sh/uv/) (recommended) or any standards-compliant Python tool.

```bash
git clone https://github.com/AI4CTI/feed-comparison.git
cd feed-comparison
uv sync --extra dev
uv run pre-commit install
uv run pytest
```

## Coding conventions

- **Formatter and linter:** [`ruff`](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`). Run `uv run ruff format` and `uv run ruff check --fix`.
- **Type checking:** [`mypy`](https://mypy-lang.org/) on `src/feed_comparison/`. Aim for clean output.
- **Tests:** [`pytest`](https://pytest.org). HTTP-based feed tests must use [`responses`](https://github.com/getsentry/responses) — never hit real APIs in CI.
- **Commits:** sign your commits with `git commit -s` (DCO sign-off). We do not require a CLA.

The full pipeline runs on every PR via GitHub Actions on Python 3.10 to 3.13.

## Adding a new feed integration

Adding a new feed in `v0.1.x` is intentionally a small change:

1. Create a new module under `src/feed_comparison/feeds/<name>.py`.
2. Implement a class that satisfies the `Feed` protocol from `feed_comparison.feeds.base`. Required attributes: `name`, `short_name`, `homepage`, `description`, `requires_credentials`. Required method: `fetch(days, settings) -> pandas.DataFrame`.
3. Make `fetch` produce a *raw* DataFrame with columns `url` and `discovered_date`, then pass it through `feed_comparison.utils.normalize.canonicalize_feed(raw, self.short_name)` so that the schema is consistent across feeds.
4. Expose a module-level `feed: Feed` instance and import the module in `src/feed_comparison/feeds/__init__.py` so the registry picks it up.
5. Add tests under `tests/feeds/test_<name>.py` using `responses` to mock HTTP calls. Cover the happy path, the credential-missing path, and at least one error path.
6. Add the new env vars (if any) to `Settings` in `src/feed_comparison/settings.py`, to `README.md`, and to `.env.example`.

## Filing issues

Use the issue templates under `.github/ISSUE_TEMPLATE/`:

- **Bug report** — for unexpected behaviour
- **Feature request** — for new functionality
- **Suggest a new feed** — to nominate a feed you'd like to see supported

## Reporting security vulnerabilities

Please do not file public issues for security-sensitive matters. See [`SECURITY.md`](SECURITY.md) for the disclosure process.
