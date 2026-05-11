from typing import Protocol, runtime_checkable

import pandas as pd

from feed_comparison.settings import Settings


@runtime_checkable
class Feed(Protocol):
    """Interface every feed implementation must satisfy.

    Implementations declare static metadata as class attributes (or
    properties) and return a *canonicalised* DataFrame from ``fetch``.

    The DataFrame schema returned by ``fetch`` must already be the one
    produced by ``feed_comparison.utils.normalize.canonicalize_feed``;
    feeds typically obtain raw data and pass it through that helper.

    ``skip_recent_days`` is an *optimisation hint*: when > 0, the caller
    will drop entries discovered in the last N days anyway, so a feed
    that knows how to short-circuit (e.g. early-stop pagination) may use
    it to save bandwidth. Correctness is enforced by the caller's
    post-fetch filter — feeds that ignore the hint stay correct.
    """

    name: str
    short_name: str
    homepage: str
    description: str
    requires_credentials: tuple[str, ...]

    def fetch(
        self, days: float, settings: Settings, skip_recent_days: float = 0.0
    ) -> pd.DataFrame: ...
