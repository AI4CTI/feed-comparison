import re
from urllib.parse import urlparse

_IP_V4_RE = re.compile(r"^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$")


def get_hostname(url):
    if not url.startswith("http"):
        url = "http://" + url
    return urlparse(url).netloc


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
