import re
from urllib.parse import urlparse

_IP_V4_RE = re.compile(r"^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$")


def get_hostname(url):
    """Return the network location of an http(s) URL, or "" if it cannot be parsed.

    Python 3.11+ raises ValueError on malformed inputs (e.g. unbalanced
    `[` from a partial IPv6 literal). We treat those as "no hostname"
    rather than crashing the whole feed pipeline; callers are expected
    to drop entries with an empty hostname.
    """
    if not url.startswith("http"):
        url = "http://" + url
    try:
        return urlparse(url).netloc
    except ValueError:
        return ""


def is_ip_address(host):
    return bool(_IP_V4_RE.match(host))


def cut_filename(filename, max_length=255):
    if len(filename) <= max_length:
        return filename
    name, _, ext = filename.rpartition(".")
    if not name:
        return filename[:max_length]
    keep = max_length - len(ext) - 1
    return name[:keep] + "." + ext
