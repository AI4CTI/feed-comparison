from datetime import datetime
from unittest.mock import patch

import pandas as pd

from feed_comparison.feeds.registry import registry
from feed_comparison.utils.normalize import canonicalize_feed
from feed_comparison.utils.plots import plot_timeplot


class _FakeFeed:
    def __init__(self, name, short_name):
        self.name = name
        self.short_name = short_name
        self.homepage = ""
        self.description = ""
        self.requires_credentials: tuple[str, ...] = ()

    def fetch(self, days, settings):
        raise NotImplementedError


def _register_fake(name, short_name):
    registry._feeds[name] = _FakeFeed(name, short_name)


def test_plot_timeplot_handles_pandas_2x_timedelta(tmp_path):
    """Regression: pandas 2.x rejects `astype('timedelta64[h]')` and we must
    use `.dt.total_seconds()` instead."""
    _register_fake("alpha", "alpha")
    _register_fake("beta", "beta")

    df_a = canonicalize_feed(
        pd.DataFrame(
            {
                "url": ["http://shared.example.com/x", "http://only-a.example.com/"],
                "discovered_date": [datetime(2026, 1, 1), datetime(2026, 1, 5)],
            }
        ),
        "alpha",
    )
    df_b = canonicalize_feed(
        pd.DataFrame(
            {
                "url": ["http://shared.example.com/x", "http://only-b.example.com/"],
                "discovered_date": [datetime(2026, 1, 3), datetime(2026, 1, 7)],
            }
        ),
        "beta",
    )

    with patch("feed_comparison.utils.plots.fastplot") as fastplot_mock:
        out = plot_timeplot(
            "alpha", ["alpha", "beta"], {"alpha": df_a, "beta": df_b}, str(tmp_path), 1, "test"
        )

    assert out is not None
    assert fastplot_mock.plot.called
    # The per-pair CSV is also written next to the plot.
    csvs = list(tmp_path.glob("timedelta_alpha-vs-beta_*.csv"))
    assert len(csvs) == 1


def test_plot_timeplot_returns_none_when_no_intersection(tmp_path):
    _register_fake("alpha2", "alpha2")
    _register_fake("beta2", "beta2")

    df_a = canonicalize_feed(
        pd.DataFrame(
            {"url": ["http://a-only.example.com/"], "discovered_date": [datetime(2026, 1, 1)]}
        ),
        "alpha2",
    )
    df_b = canonicalize_feed(
        pd.DataFrame(
            {"url": ["http://b-only.example.com/"], "discovered_date": [datetime(2026, 1, 1)]}
        ),
        "beta2",
    )

    with patch("feed_comparison.utils.plots.fastplot"):
        out = plot_timeplot(
            "alpha2", ["alpha2", "beta2"], {"alpha2": df_a, "beta2": df_b}, str(tmp_path), 1, "x"
        )
    assert out is None
