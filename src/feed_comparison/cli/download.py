import logging
from datetime import datetime
from pathlib import Path

import typer

from feed_comparison.feeds.registry import registry
from feed_comparison.settings import (
    FeedConfigurationError,
    MissingCredentialsError,
    MissingOptionalDependencyError,
    Settings,
)
from feed_comparison.utils.time import filter_off_last_days

_log = logging.getLogger(__name__)

_PER_FEED_ERRORS = (
    MissingCredentialsError,
    MissingOptionalDependencyError,
    FeedConfigurationError,
)


def download(
    feeds: list[str] = typer.Argument(..., help="Names of feeds to download."),
    days: float = typer.Option(7.0, "--days", "-d", help="Look-back window in days."),
    output_dir: Path = typer.Option(
        None, "--output-dir", "-o", help="Override the output directory."
    ),
    last_days_to_ignore: float = typer.Option(
        0.0,
        "--ignore-last-days",
        help="Drop entries discovered in the last N days (useful to discard not-yet-stabilised data).",
    ),
):
    """Download feeds and write one CSV per feed into the output directory."""
    settings = Settings.from_env()
    out = output_dir or settings.output_dir
    out.mkdir(parents=True, exist_ok=True)

    run_id = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")

    succeeded = 0
    for name in feeds:
        feed = registry.get(name)
        _log.info("Downloading %s (%.1f days)...", name, days)
        try:
            df = feed.fetch(days=days, settings=settings, skip_recent_days=last_days_to_ignore)
        except _PER_FEED_ERRORS as exc:
            _log.error("%s: %s", name, exc)
            continue
        except Exception as exc:
            # Unexpected per-feed failure (HTTPError, transient network issue,
            # upstream API change, ...). One concise ERROR line, plus the full
            # traceback at DEBUG level so it's available with `--verbose`. We
            # don't abort the whole run — other feeds may still produce data.
            _log.error(
                "%s: unexpected error during fetch (skipping): %s: %s",
                name,
                type(exc).__name__,
                exc,
            )
            _log.debug("%s: traceback:", name, exc_info=True)
            continue

        if df is None or df.empty:
            _log.warning("%s: no data returned", name)
            continue

        if last_days_to_ignore > 0:
            df = filter_off_last_days(df, last_days_to_ignore)

        path = out / f"dataframe_{name}_{days}_{run_id}.csv"
        df.to_csv(path, encoding="utf-8", errors="replace")
        _log.info("%s: %d rows written to %s", name, len(df), path)
        succeeded += 1

    if succeeded == 0 and feeds:
        _log.error("All %d requested feeds failed; nothing written.", len(feeds))
        raise typer.Exit(code=2)
