from io import StringIO

import pandas as pd

from feed_comparison.feeds.base import Feed
from feed_comparison.settings import MissingOptionalDependencyError, Settings
from feed_comparison.utils.normalize import canonicalize_feed


def _fetch_raw(days, base_url, token):
    try:
        from pymisp import ExpandedPyMISP
    except ImportError as exc:
        raise MissingOptionalDependencyError("misp", ["pymisp"]) from exc

    misp = ExpandedPyMISP(base_url, token, ssl=True)
    body = {
        "returnFormat": "csv",
        "type": "url",
        "attribute_timestamp": f"{int(days)}d",
        "requested_attributes": ["uuid", "value", "timestamp"],
    }
    csv_text = misp.direct_call("attributes/restSearch", body)
    df = pd.read_csv(StringIO(csv_text))
    df["discovered_date"] = pd.to_datetime(df["date"], unit="s")
    df = df.rename(columns={"value": "url"})
    return df


class Misp:
    name = "misp"
    short_name = "misp"
    homepage = "https://www.misp-project.org/"
    description = "Self-hosted MISP instance; requires base URL and API key."
    requires_credentials: tuple[str, ...] = ("misp_url", "misp_key")

    def fetch(self, days, settings: Settings):
        url, key = settings.require(*self.requires_credentials)
        raw = _fetch_raw(days, url, key)
        return canonicalize_feed(raw, self.short_name)


feed: Feed = Misp()
