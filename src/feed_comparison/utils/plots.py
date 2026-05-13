import itertools
import logging

import fastplot
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from supervenn import supervenn

from feed_comparison.feeds.registry import registry
from feed_comparison.utils.plot_style import WONG_PALETTE, apply_style
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


# Cycler used by the time-delta CDF: colour from the shared Wong palette
# combined with distinct linestyles so traces remain identifiable in B&W
# print or for users with colour-vision deficiencies. Markers are off by
# design — they were noisy on dense CDFs and are no longer needed once
# we have linestyle distinction.
_CDF_CYCLER = cycler("color", WONG_PALETTE) + cycler(
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


def plot_supervenn(feeds, downloaded_dfs, metric, output_dir, days, run_id):
    """Render a SuperVenn plot of the overlap between feeds on a given metric."""
    _log.info("Plotting SuperVenn (%s)", metric)
    apply_style()
    sets = []
    labels = []
    for feed in feeds:
        df = downloaded_dfs[feed]
        data = set(df.index) if metric == "normURLwoScheme" else set(df[metric].to_list())
        sets.append(data)
        labels.append(feed)

    fig = plt.figure(figsize=(16, 8))
    # Cycle through the shared palette; supervenn picks one colour per set.
    set_colors = [WONG_PALETTE[i % len(WONG_PALETTE)] for i in range(len(sets))]
    supervenn(sets, labels, color_cycle=set_colors)
    fig.suptitle(
        f"Overlap on {metric} — {len(sets)} feeds, {days}-day window",
        fontsize=13,
        fontweight="bold",
        y=0.995,
    )
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

    apply_style()
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

        median = float(np.median(diffs.time_diff))
        mean = float(np.mean(diffs.time_diff))
        label = (
            f"{benchmark} vs {other} — n={len(diffs)} — median {median:+.2f} d, mean {mean:+.2f} d"
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

    def _cdf_callback(plt_):
        # Subtle vertical reference at delta=0: positive → benchmark later,
        # negative → benchmark earlier. The dashed grey line makes the
        # asymmetry of the CDF visible at a glance.
        plt_.axvline(0, color="#999999", linewidth=0.8, linestyle="--", zorder=1)

    fastplot.plot(
        time_diffs,
        plot_name,
        mode="CDF_multi",
        xlabel="Delta [days]   (positive = benchmark observed later)",
        ylabel="CDF",
        legend=True,
        cycler=_CDF_CYCLER,
        figsize=(10, 6),
        grid=True,
        linewidth=1.6,
        legend_loc="lower right",
        legend_fancybox=False,
        legend_frameon=True,
        callback=_cdf_callback,
    )
    _log.info("Timedelta CDF written to %s", plot_name)
    return plot_name
