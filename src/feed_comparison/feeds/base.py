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
    """

    name: str
    short_name: str
    homepage: str
    description: str
    requires_credentials: tuple[str, ...]

    def fetch(self, days: float, settings: Settings) -> pd.DataFrame: ...
