import pytest

from feed_comparison.feeds import registry  # registers the four built-in feeds
from feed_comparison.feeds.registry import UnknownFeedError, _FeedRegistry


def test_builtin_feeds_are_registered():
    names = registry.names()
    assert {"misp", "phishstats", "phishtank", "urlscan"}.issubset(names)


def test_get_unknown_feed_lists_alternatives():
    with pytest.raises(UnknownFeedError) as exc:
        registry.get("nope-not-a-feed")
    assert "nope-not-a-feed" in str(exc.value)
    assert "phishstats" in str(exc.value)


def test_register_rejects_duplicates():
    r = _FeedRegistry()

    class Dummy:
        name = "x"
        short_name = "x"
        homepage = "https://example.com"
        description = ""
        requires_credentials: tuple[str, ...] = ()

        def fetch(self, days, settings):
            raise NotImplementedError

    r.register(Dummy())
    with pytest.raises(ValueError, match="already registered"):
        r.register(Dummy())


def test_register_rejects_non_feed_protocol():
    r = _FeedRegistry()

    class NotAFeed:
        name = "y"  # missing the rest of the protocol

    with pytest.raises(TypeError):
        r.register(NotAFeed())
