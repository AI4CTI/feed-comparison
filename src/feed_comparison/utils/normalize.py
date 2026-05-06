import logging

import pandas as pd
import tldextract

from feed_comparison.utils import canonicalize
from feed_comparison.utils.text import get_hostname, is_ip_address

_log = logging.getLogger(__name__)


def _canonical_url_with_scheme(url):
    return canonicalize.canonical_url(url)[0].decode()


def _strip_scheme(canonical):
    """Return the URL without its `scheme://` prefix, or "" if no scheme is present.

    Some entries (notably from MISP, where attribute values can be effectively
    anything) survive `canonical_url` without producing a `//` separator. We
    return an empty string for those and let the caller drop them, instead of
    crashing with IndexError.
    """
    _, sep, rest = canonical.partition("//")
    return rest if sep else ""


def _domain_of(url_no_scheme):
    # Strip path / query so an IP literal in the host is still recognised.
    host = url_no_scheme.split("/", 1)[0]
    if is_ip_address(host):
        return host
    try:
        extracted = tldextract.extract(host)
    except (ValueError, UnicodeError):
        return ""
    if extracted.ipv4:
        return extracted.ipv4
    if not extracted.domain or not extracted.suffix:
        return ""
    return f"{extracted.domain}.{extracted.suffix}"


def canonicalize_feed(df, short_name):
    """Normalise a raw feed DataFrame into the schema used across the tool.

    Input requirements:
      - column ``url`` with the raw URL string for each entry
      - column ``discovered_date`` with the timestamp of discovery

    Output schema (indexed by ``normURLwoScheme``):
      - ``normURLwScheme``: canonicalised URL with scheme
      - ``hostname``: network location
      - ``domain``: registered domain (eTLD+1) or IP literal
      - ``discovered_date``: earliest observation across duplicates
      - ``discovered_dates``: list of all observations
      - any other column from the input is suffixed with ``_{short_name}``
        so that DataFrames from different feeds can be merged side-by-side
        without collisions.
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    # Drop NaN/empty URLs up front: feeds like MISP can expose any attribute
    # value as a "url", including blanks that crash canonicalisation.
    initial = len(df)
    df = df[df["url"].notna() & (df["url"].astype(str).str.strip() != "")]
    if len(df) < initial:
        _log.debug("canonicalize_feed: dropped %d empty/NaN URLs", initial - len(df))
    if df.empty:
        return df

    df["normURLwScheme"] = df["url"].map(_canonical_url_with_scheme)
    df["normURLwoScheme"] = df["normURLwScheme"].map(_strip_scheme)
    # Drop entries that survived canonicalisation without a scheme/host —
    # they can't be merged or compared meaningfully.
    pre = len(df)
    df = df[df["normURLwoScheme"] != ""]
    if len(df) < pre:
        _log.debug(
            "canonicalize_feed: dropped %d unparseable URLs after canonicalisation",
            pre - len(df),
        )
    if df.empty:
        return df

    # Comma-to-tab to keep CSV serialisation safe even for fields that
    # legitimately contain commas (titles, descriptions...).
    df = df.replace(",", "\t", regex=True)

    df = df.set_index("normURLwoScheme", drop=True)
    df = df.sort_values(by="discovered_date")

    aggregations = dict.fromkeys(df.columns, list)
    df = df.groupby(by=["normURLwoScheme"]).aggregate(aggregations)

    df = df.rename(columns={"discovered_date": "discovered_dates"})
    df["discovered_date"] = df["discovered_dates"].map(min)

    df = df.rename(columns={"normURLwScheme": "normURLwSchemes"})
    df["normURLwScheme"] = df["normURLwSchemes"].map(lambda d: d[0])
    df = df.sort_values(by="discovered_date")

    df["hostname"] = df["normURLwScheme"].map(get_hostname)
    # An empty hostname means urlparse refused the URL (e.g. unbalanced
    # IPv6 brackets); such rows can't participate in overlap or merge
    # analyses, so we drop them with a debug-level note.
    pre = len(df)
    df = df[df["hostname"] != ""]
    if len(df) < pre:
        _log.debug(
            "canonicalize_feed: dropped %d entries with unparseable hostname",
            pre - len(df),
        )
    if df.empty:
        return df

    df.insert(2, "domain", [_domain_of(idx) for idx in df.index])

    reserved = {"domain", "hostname", "normURLwoScheme", "normURLwScheme"}
    df = df.rename(columns={c: f"{c}_{short_name}" for c in df.columns if c not in reserved})

    return df


def concat_feeds(downloaded_dfs):
    """Side-by-side outer-join of the canonicalised DataFrames of every feed."""
    return pd.concat(list(downloaded_dfs.values()), axis=1)
