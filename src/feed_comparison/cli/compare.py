import logging
from datetime import datetime
from pathlib import Path

import typer

from feed_comparison.feeds.registry import registry
from feed_comparison.settings import MissingCredentialsError, Settings
from feed_comparison.utils.plots import plot_supervenn, plot_timeplot
from feed_comparison.utils.time import filter_off_last_days, force_temporal_boundaries

_log = logging.getLogger(__name__)

_DEFAULT_METRICS = ("hostname", "domain", "normURLwScheme")


def compare(
    feeds: list[str] = typer.Argument(..., help="Names of feeds to compare."),
    days: float = typer.Option(7.0, "--days", "-d", help="Look-back window in days."),
    benchmark: str = typer.Option(
        None,
        "--benchmark",
        "-b",
        help="Feed to use as the reference for the time-delta CDF.",
    ),
    output_dir: Path = typer.Option(
        None, "--output-dir", "-o", help="Override the output directory."
    ),
    no_supervenn: bool = typer.Option(
        False, "--no-supervenn", help="Skip the SuperVenn overlap plots."
    ),
    no_cdf: bool = typer.Option(False, "--no-cdf", help="Skip the time-delta CDF plot."),
    force_window: bool = typer.Option(
        False, "--force-window", help="Restrict every feed to the time window common to all."
    ),
    last_days_to_ignore: float = typer.Option(
        0.0,
        "--ignore-last-days",
        help="Drop entries discovered in the last N days for each feed.",
    ),
):
    """Download feeds and compare them: overlap (SuperVenn) and time-delta CDF."""
    settings = Settings.from_env()
    out = output_dir or settings.output_dir
    out.mkdir(parents=True, exist_ok=True)

    run_id = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    downloaded = {}

    for name in feeds:
        feed = registry.get(name)
        _log.info("Downloading %s (%.1f days)...", name, days)
        try:
            df = feed.fetch(days=days, settings=settings)
        except MissingCredentialsError as exc:
            _log.error("%s: %s", name, exc)
            raise typer.Exit(code=2) from None
        if df is None or df.empty:
            _log.warning("%s: no data returned, skipping", name)
            continue
        if last_days_to_ignore > 0:
            df = filter_off_last_days(df, last_days_to_ignore)
        downloaded[name] = df
        df.to_csv(out / f"dataframe_{name}_{days}_{run_id}.csv", encoding="utf-8", errors="replace")

    if len(downloaded) < 2:
        _log.error("Need at least two non-empty feeds to compare; got %d", len(downloaded))
        raise typer.Exit(code=1)

    if force_window:
        downloaded = force_temporal_boundaries(downloaded)

    feed_names = list(downloaded.keys())

    if not no_supervenn:
        for metric in _DEFAULT_METRICS:
            plot_supervenn(feed_names, downloaded, metric, str(out), days, run_id)

    if not no_cdf:
        bench = benchmark or feed_names[0]
        if bench not in downloaded:
            _log.error("Benchmark %r is not among non-empty feeds %s", bench, feed_names)
            raise typer.Exit(code=1)
        plot_timeplot(bench, feed_names, downloaded, str(out), days, run_id)
