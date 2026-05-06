from feed_comparison.feeds import ermes as _ermes
from feed_comparison.feeds import misp as _misp
from feed_comparison.feeds import phishstats as _phishstats
from feed_comparison.feeds import phishtank as _phishtank
from feed_comparison.feeds import url_scan as _url_scan
from feed_comparison.feeds.registry import UnknownFeedError, registry

for _mod in (_ermes, _misp, _phishstats, _phishtank, _url_scan):
    registry.register(_mod.feed)

__all__ = ["UnknownFeedError", "registry"]
