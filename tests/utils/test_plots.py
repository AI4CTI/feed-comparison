from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd

from feed_comparison.feeds.registry import registry
from feed_comparison.utils.normalize import canonicalize_feed
from feed_comparison.utils.plots import _to_naive_utc, plot_timeplot


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


def test_to_naive_utc_handles_naive_aware_and_string_inputs():
    """Helper must coerce *any* combination of naive datetimes, tz-aware
    datetimes and ISO 8601 strings into a single tz-naive UTC series."""
    s = pd.Series(
        [
            "2026-04-29T12:00:00Z",  # tz-aware via Z
            "2026-04-29T14:00:00+02:00",  # tz-aware via offset (= 12:00 UTC)
            datetime(2026, 4, 29, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 4, 29, 12, 0, 0),  # naive, treated as UTC
        ]
    )
    out = _to_naive_utc(s)
    # Series is now tz-naive
    assert out.dt.tz is None
    # All four values land on the same UTC instant.
    assert (out == datetime(2026, 4, 29, 12, 0, 0)).all()


def test_plot_timeplot_handles_mixed_timezone_feeds(tmp_path):
    """Regression for the production crash with `compare ermes phishtank misp`:
    one feed (Ermes) emits tz-aware timestamps while the others emit naive UTC,
    so pandas refuses to subtract the two columns. The CDF must still be
    produced after _to_naive_utc normalises both."""
    _register_fake("aware", "aware")
    _register_fake("naive", "naive")

    df_aware = canonicalize_feed(
        pd.DataFrame(
            {
                "url": ["http://shared.example.com/x", "http://only-aware.example.com/"],
                "discovered_date": [
                    datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                    datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
                ],
            }
        ),
        "aware",
    )
    df_naive = canonicalize_feed(
        pd.DataFrame(
            {
                "url": ["http://shared.example.com/x", "http://only-naive.example.com/"],
                "discovered_date": [datetime(2026, 1, 3), datetime(2026, 1, 7)],
            }
        ),
        "naive",
    )

    with patch("feed_comparison.utils.plots.fastplot") as fastplot_mock:
        out = plot_timeplot(
            "aware",
            ["aware", "naive"],
            {"aware": df_aware, "naive": df_naive},
            str(tmp_path),
            1,
            "tz",
        )
    assert out is not None
    assert fastplot_mock.plot.called


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
