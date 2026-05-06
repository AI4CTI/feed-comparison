import logging
from datetime import datetime, timedelta

import pandas as pd
import requests

from feed_comparison.feeds.base import Feed
from feed_comparison.settings import Settings
from feed_comparison.utils.normalize import canonicalize_feed

_DOWNLOAD_URL = "https://data.phishtank.com/data/online-valid.csv"
_log = logging.getLogger(__name__)


def _parse_submission_time(s):
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in s else "%Y-%m-%dT%H:%M:%S%z"
    return datetime.strptime(s, fmt)


def _fetch_raw(days, username):
    cutoff = datetime.utcnow() - timedelta(days=days)
    headers = {"User-Agent": f"phishtank/{username}"}
    resp = requests.get(_DOWNLOAD_URL, headers=headers, timeout=120)
    resp.raise_for_status()

    from io import StringIO

    df = pd.read_csv(
        StringIO(resp.text),
        lineterminator="\n",
        header="infer",
        encoding="utf-8",
        encoding_errors="ignore",
        sep=",",
    )
    df["discovered_date"] = pd.to_datetime(df["submission_time"], utc=True).dt.tz_localize(None)
    return df.loc[df["discovered_date"] >= cutoff].reset_index(drop=True)


class PhishTank:
    name = "phishtank"
    short_name = "pt"
    homepage = "https://phishtank.org/"
    description = "Public phishing feed; requires a free PhishTank username."
    requires_credentials: tuple[str, ...] = ("phishtank_username",)

    def fetch(self, days, settings: Settings):
        (username,) = settings.require(*self.requires_credentials)
        raw = _fetch_raw(days, username)
        return canonicalize_feed(raw, self.short_name)


feed: Feed = PhishTank()
