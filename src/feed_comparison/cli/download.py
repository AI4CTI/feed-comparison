import logging
from datetime import datetime
from pathlib import Path

import typer

from feed_comparison.feeds.registry import registry
from feed_comparison.settings import MissingCredentialsError, Settings
from feed_comparison.utils.time import filter_off_last_days

_log = logging.getLogger(__name__)


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

    for name in feeds:
        feed = registry.get(name)
        _log.info("Downloading %s (%.1f days)...", name, days)
        try:
            df = feed.fetch(days=days, settings=settings)
        except MissingCredentialsError as exc:
            _log.error("%s: %s", name, exc)
            raise typer.Exit(code=2) from None

        if df is None or df.empty:
            _log.warning("%s: no data returned", name)
            continue

        if last_days_to_ignore > 0:
            df = filter_off_last_days(df, last_days_to_ignore)

        path = out / f"dataframe_{name}_{days}_{run_id}.csv"
        df.to_csv(path, encoding="utf-8", errors="replace")
        _log.info("%s: %d rows written to %s", name, len(df), path)
