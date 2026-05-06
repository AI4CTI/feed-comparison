from datetime import datetime, timedelta

import pandas as pd
import pytest

from feed_comparison.utils.time import (
    _discovered_date_column,
    filter_off_last_days,
    force_temporal_boundaries,
)


def _df_with_dates(dates, col="discovered_date"):
    return pd.DataFrame({"url": [f"http://x.com/{i}" for i in range(len(dates))], col: dates})


def test_filter_off_last_days_drops_recent_entries():
    now = datetime.utcnow()
    df = _df_with_dates(
        [now - timedelta(days=10), now - timedelta(days=5), now - timedelta(hours=1)]
    )
    out = filter_off_last_days(df, last_days_to_ignore=1)
    assert len(out) == 2
    assert out["discovered_date"].max() < now - timedelta(days=1)


def test_filter_off_last_days_picks_suffixed_column():
    now = datetime.utcnow()
    df = _df_with_dates([now - timedelta(days=2)], col="discovered_date_ps")
    out = filter_off_last_days(df, last_days_to_ignore=1)
    assert len(out) == 1


def test_discovered_date_column_prefers_singular():
    df = pd.DataFrame(
        {
            "discovered_dates_ps": [[1, 2]],
            "discovered_date_ps": [datetime(2026, 1, 1)],
        }
    )
    assert _discovered_date_column(df) == "discovered_date_ps"


def test_force_temporal_boundaries_uses_overall_min_max():
    """Regression: the original implementation overwrote min/max in the loop
    and ended up using only the boundaries of the *last* feed."""
    feed_a = _df_with_dates([datetime(2026, 1, 1), datetime(2026, 1, 5), datetime(2026, 1, 10)])
    feed_b = _df_with_dates([datetime(2026, 1, 3), datetime(2026, 1, 6), datetime(2026, 1, 8)])
    feed_c = _df_with_dates([datetime(2026, 1, 4), datetime(2026, 1, 7), datetime(2026, 1, 9)])

    out = force_temporal_boundaries({"a": feed_a, "b": feed_b, "c": feed_c})

    # Window should be [max-of-min, min-of-max] = [2026-01-04, 2026-01-08]
    for name, df in out.items():
        assert df["discovered_date"].min() >= datetime(2026, 1, 4), name
        assert df["discovered_date"].max() <= datetime(2026, 1, 8), name


def test_force_temporal_boundaries_empty_input_returns_empty():
    assert force_temporal_boundaries({}) == {}


def test_filter_off_last_days_raises_without_discovered_date_column():
    df = pd.DataFrame({"url": ["http://x.com/"], "other": [1]})
    with pytest.raises(ValueError):
        filter_off_last_days(df, 1)
