from datetime import datetime

import pandas as pd

from feed_comparison.utils.normalize import canonicalize_feed


def _raw(urls, dates):
    return pd.DataFrame({"url": urls, "discovered_date": dates})


def test_canonicalize_feed_returns_expected_columns():
    df = canonicalize_feed(
        _raw(["http://www.evil.com/a"], [datetime(2026, 1, 1)]),
        "demo",
    )
    cols = set(df.columns)
    assert {"hostname", "domain", "normURLwScheme", "discovered_date_demo"}.issubset(cols)


def test_canonicalize_feed_dedups_by_normalised_url():
    df = canonicalize_feed(
        _raw(
            ["http://www.evil.com/a/", "http://www.EVIL.com/a/"],  # host-case differs only
            [datetime(2026, 1, 1), datetime(2026, 1, 5)],
        ),
        "demo",
    )
    assert len(df) == 1
    # Earliest discovery date wins
    assert df["discovered_date_demo"].iloc[0] == datetime(2026, 1, 1)


def test_canonicalize_feed_extracts_domain_for_hostnames():
    df = canonicalize_feed(
        _raw(["http://login.foo.example.co.uk/"], [datetime(2026, 1, 1)]),
        "demo",
    )
    assert df["domain"].iloc[0] == "example.co.uk"


def test_canonicalize_feed_keeps_ip_as_domain():
    df = canonicalize_feed(
        _raw(["http://192.168.1.1/login"], [datetime(2026, 1, 1)]),
        "demo",
    )
    assert df["domain"].iloc[0].startswith("192.168.1.1")


def test_canonicalize_feed_suffixes_non_reserved_columns_only():
    raw = pd.DataFrame(
        {
            "url": ["http://a.com/"],
            "discovered_date": [datetime(2026, 1, 1)],
            "extra": ["meta"],
        }
    )
    out = canonicalize_feed(raw, "demo")
    # Reserved columns are NOT suffixed.
    for reserved in ("hostname", "domain", "normURLwScheme"):
        assert reserved in out.columns
    # Other columns get the short_name suffix.
    assert "extra_demo" in out.columns
    assert "discovered_date_demo" in out.columns


def test_canonicalize_feed_returns_input_when_empty():
    out = canonicalize_feed(pd.DataFrame(columns=["url", "discovered_date"]), "demo")
    assert out.empty
