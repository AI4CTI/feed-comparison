from feed_comparison.feeds.base import Feed


class UnknownFeedError(KeyError):
    def __init__(self, name, available):
        self.name = name
        self.available = sorted(available)
        super().__init__(f"Unknown feed: {name!r}. Available: {', '.join(self.available)}")


class _FeedRegistry:
    def __init__(self):
        self._feeds: dict[str, Feed] = {}

    def register(self, feed):
        if feed.name in self._feeds:
            raise ValueError(f"Feed already registered: {feed.name!r}")
        if not isinstance(feed, Feed):
            raise TypeError(f"{type(feed).__name__} does not implement the Feed protocol")
        self._feeds[feed.name] = feed
        return feed

    def get(self, name):
        try:
            return self._feeds[name]
        except KeyError:
            raise UnknownFeedError(name, self._feeds.keys()) from None

    def names(self):
        return sorted(self._feeds.keys())

    def all(self):
        return [self._feeds[n] for n in self.names()]


registry = _FeedRegistry()
