import itertools
import logging

import fastplot
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from supervenn import supervenn

from feed_comparison.feeds.registry import registry
from feed_comparison.utils.text import cut_filename

_log = logging.getLogger(__name__)


def _to_naive_utc(series):
    """Coerce a series of date-like strings/datetimes to tz-naive UTC.

    Different feeds emit `discovered_date` with different timezone
    conventions (Ermes uses offset-aware, MISP/PhishTank/PhishStats use
    naive UTC). Without this normalisation the time-delta arithmetic in
    `plot_timeplot` raises:
        TypeError: Cannot subtract tz-naive and tz-aware datetime-like objects
    Forcing through `utc=True` reads naive values as UTC and converts
    aware values to UTC, then we drop the tzinfo so subtraction with
    other naive series is well-defined.
    """
    parsed = pd.to_datetime(series, utc=True, errors="coerce")
    return parsed.dt.tz_localize(None)


_CYCLER_LINESPOINTS = (
    cycler("color", ["r", "b", "g", "purple", "c", "black", "orange", "grey"])
    + cycler(
        "linestyle",
        [
            "-",
            "--",
            "-.",
            ":",
            (0, (3, 1, 1, 1)),
            (0, (5, 10)),
            (0, (1, 1)),
            (0, (5, 1)),
        ],
    )
    + cycler("marker", ["o", "s", "v", "d", "^", "x", "|", "P"])
)


def plot_supervenn(feeds, downloaded_dfs, metric, output_dir, days, run_id):
    """Render a SuperVenn plot of the overlap between feeds on a given metric."""
    _log.info("Plotting SuperVenn (%s)", metric)
    sets = []
    labels = []
    for feed in feeds:
        df = downloaded_dfs[feed]
        data = set(df.index) if metric == "normURLwoScheme" else set(df[metric].to_list())
        sets.append(data)
        labels.append(feed)

    plt.figure(figsize=(16, 8))
    supervenn(sets, labels)
    filename = cut_filename(
        f"{output_dir}/supervenn_{metric}_{days}_{run_id}_" + "-".join(sorted(feeds)) + ".png"
    )
    plt.savefig(filename)
    plt.close()
    _log.info("SuperVenn written to %s", filename)
    return filename


def plot_timeplot(benchmark, feeds, downloaded_dfs, output_dir, days, run_id):
    """Render a CDF of per-hostname time deltas between benchmark and other feeds."""
    if benchmark not in feeds:
        raise ValueError(f"Benchmark feed {benchmark!r} not in selected feeds {feeds}")

    merge = pd.concat([downloaded_dfs[feed] for feed in feeds], axis=1)
    bench_short = registry.get(benchmark).short_name
    time_diffs = []

    for pair in itertools.combinations(feeds, 2):
        if benchmark not in pair:
            continue
        other = next(f for f in pair if f != benchmark)
        other_short = registry.get(other).short_name

        col_b = f"discovered_date_{bench_short}"
        col_o = f"discovered_date_{other_short}"
        merge[col_b] = _to_naive_utc(merge[col_b])
        merge[col_o] = _to_naive_utc(merge[col_o])

        diffs = pd.DataFrame(index=merge.index)
        # pandas 2.x removed the `timedelta64[h]` cast; build the days-delta
        # via total_seconds() instead, which works on all 1.x and 2.x.
        diffs["time_diff"] = (merge[col_b] - merge[col_o]).dt.total_seconds() / 86400.0
        diffs = diffs[diffs.time_diff.notnull()]

        diffs.to_csv(
            f"{output_dir}/timedelta_{benchmark}-vs-{other}_{days}_{run_id}.csv",
            errors="ignore",
        )
        if diffs.empty:
            _log.info("No intersection between %s and %s", benchmark, other)
            continue

        avg = float(np.mean(diffs.time_diff))
        label = (
            f"{len(downloaded_dfs[benchmark])} in {benchmark} vs "
            f"{len(downloaded_dfs[other])} in {other} - "
            f"intersec {len(diffs)} - avg {avg:.2f} [days]"
        )
        time_diffs.append((label, diffs["time_diff"]))

    if not time_diffs:
        _log.warning("No pairs produced a non-empty intersection; skipping CDF")
        return None

    plot_name = cut_filename(
        f"{output_dir}/timedelta_CDF_{benchmark}_{days}_{run_id}_"
        + "-".join(f for f in feeds if f != benchmark)
        + ".png"
    )
    fastplot.plot(
        time_diffs,
        plot_name,
        mode="CDF_multi",
        xlabel="Delta [days]",
        legend=True,
        cycler=_CYCLER_LINESPOINTS,
        plot_args={"markevery": 100},
        figsize=(10, 6),
        grid=True,
        linewidth=2.0,
        legend_loc=(0.2, 1.05),
        legend_fancybox=True,
        legend_frameon=True,
    )
    _log.info("Timedelta CDF written to %s", plot_name)
    return plot_name
