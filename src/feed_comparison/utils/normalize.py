import pandas as pd
import tldextract

from feed_comparison.utils import canonicalize
from feed_comparison.utils.text import get_hostname, is_ip_address


def _canonical_url_with_scheme(url):
    return canonicalize.canonical_url(url)[0].decode()


def _domain_of(url_no_scheme):
    if is_ip_address(url_no_scheme):
        return url_no_scheme
    extracted = tldextract.extract(url_no_scheme)
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
    df["normURLwScheme"] = df["url"].map(_canonical_url_with_scheme)
    df["normURLwoScheme"] = df["normURLwScheme"].map(lambda u: u.split("//", 1)[1])

    # Comma-to-tab to keep CSV serialisation safe even for fields that
    # legitimately contain commas (titles, descriptions...).
    df = df.replace(",", "\t", regex=True)

    df = df.set_index("normURLwoScheme", drop=True)
    df = df.sort_values(by="discovered_date")

    aggregations = {col: list for col in df.columns}
    df = df.groupby(by=["normURLwoScheme"]).aggregate(aggregations)

    df = df.rename(columns={"discovered_date": "discovered_dates"})
    df["discovered_date"] = df["discovered_dates"].map(min)

    df = df.rename(columns={"normURLwScheme": "normURLwSchemes"})
    df["normURLwScheme"] = df["normURLwSchemes"].map(lambda d: d[0])
    df = df.sort_values(by="discovered_date")

    df["hostname"] = df["normURLwScheme"].map(get_hostname)
    df.insert(2, "domain", [_domain_of(idx) for idx in df.index])

    reserved = {"domain", "hostname", "normURLwoScheme", "normURLwScheme"}
    df = df.rename(columns={c: f"{c}_{short_name}" for c in df.columns if c not in reserved})

    return df


def concat_feeds(downloaded_dfs):
    """Side-by-side outer-join of the canonicalised DataFrames of every feed."""
    return pd.concat(list(downloaded_dfs.values()), axis=1)
