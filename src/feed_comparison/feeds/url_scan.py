import pandas as pd
import requests

from feed_comparison.feeds.base import Feed
from feed_comparison.settings import Settings
from feed_comparison.utils.normalize import canonicalize_feed


def _fetch_raw(days, base_url, token):
    days = max(int(days), 1)
    headers = {"API-Key": token}
    url = f"{base_url}?format=json&q=date:%3Enow-{days}d"
    resp = requests.get(url, headers=headers, timeout=120)
    resp.raise_for_status()

    results = resp.json().get("results", [])
    df = pd.DataFrame.from_records(results)
    if df.empty:
        return df

    df["discovered_date"] = pd.to_datetime(df["date"], utc=True).dt.tz_localize(None)
    df = df.rename(columns={"page_url": "url"})
    return df


class UrlScan:
    name = "urlscan"
    short_name = "us"
    homepage = "https://urlscan.io/"
    description = "urlscan.io search API; requires endpoint URL and an API token."
    requires_credentials: tuple[str, ...] = ("urlscan_url", "urlscan_token")

    def fetch(self, days, settings: Settings):
        url, token = settings.require(*self.requires_credentials)
        raw = _fetch_raw(days, url, token)
        return canonicalize_feed(raw, self.short_name)


feed: Feed = UrlScan()
