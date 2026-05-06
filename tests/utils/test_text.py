import pytest

from feed_comparison.utils.text import cut_filename, get_hostname, is_ip_address


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://www.example.com/foo", "www.example.com"),
        ("https://example.com:8080/", "example.com:8080"),
        ("example.com/foo", "example.com"),  # scheme injected
    ],
)
def test_get_hostname(url, expected):
    """get_hostname is intentionally http(s)-oriented; non-http schemes are out of scope."""
    assert get_hostname(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://[unbalanced.example.com/",  # unbalanced IPv6 bracket -> ValueError on 3.11+
        "http://]nope.example.com/",
    ],
)
def test_get_hostname_returns_empty_on_unparseable(url):
    """Regression: urlparse on Python 3.11+ raises ValueError on malformed inputs.
    We must degrade gracefully so the per-feed pipeline doesn't crash."""
    assert get_hostname(url) == ""


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("192.168.1.1", True),
        ("8.8.8.8", True),
        ("0.0.0.0", True),
        ("256.0.0.1", False),
        ("example.com", False),
        ("2001:db8::1", False),  # IPv6 is not handled by is_ip_address
    ],
)
def test_is_ip_address(host, expected):
    assert is_ip_address(host) is expected


def test_cut_filename_short_unchanged():
    assert cut_filename("short.png") == "short.png"


def test_cut_filename_long_truncated_preserving_extension():
    name = "a" * 300 + ".png"
    cut = cut_filename(name)
    assert len(cut) <= 255
    assert cut.endswith(".png")


def test_cut_filename_no_extension():
    name = "a" * 300
    cut = cut_filename(name)
    assert len(cut) <= 255
