import ipaddress
import posixpath
import re
import string
from urllib.parse import unquote_to_bytes

# This is equivalent of ("([.])\1+", "\1") to replace consecutive "."
consecutive_dots_re = (b"\x28\x5b\x2e\x5d\x29\x5c\x31\x2b", b"\x5c\x31")
# This is equivalent of ("([/])\1+", "\1") to replace consecutive "/"
consecutive_slashes_re = (b"\x28\x5b\x5c\x2f\x5d\x29\x5c\x31\x2b", b"\x5c\x31")
# This is equivalent of ":\d+$" to find ports in netlocs
find_port_re = b"\x3a\x5c\x64\x2b\x24"

test_urls = [
    ("http://www.bücher...com///", "http://www.xn--bcher-kva.com/"),
    ("http://www.bücher...com/../", "http://www.xn--bcher-kva.com/"),
    ("http://www.gotaport.com:1234/", "http://www.gotaport.com/"),
    ("http://host/%25%32%35", "http://host/%25"),
    ("http://host/%25%32%35%25%32%35", "http://host/%25%25"),
    ("http://host/%2525252525252525", "http://host/%25"),
    ("http://host/asdf%25%32%35asd", "http://host/asdf%25asd"),
    ("http://host/%%%25%32%35asd%%", "http://host/%25%25%25asd%25%25"),
    ("http://www.google.com/", "http://www.google.com/"),
    (
        "http://%31%36%38%2e%31%38%38%2e%39%39%2e%32%36/%2E%73%65%63%75%72%65/%77%77%77%2E%65%62%61%79%2E%63%6F%6D/",
        "http://168.188.99.26/.secure/www.ebay.com/",
    ),
    (
        "http://195.127.0.11/uploads/%20%20%20%20/.verify/.eBaysecure=updateuserdataxplimnbqmn-xplmvalidateinfoswqpcmlx=hgplmcx/",
        "http://195.127.0.11/uploads/%20%20%20%20/.verify/.eBaysecure=updateuserdataxplimnbqmn-xplmvalidateinfoswqpcmlx=hgplmcx/",
    ),
    (
        "http://host%23.com/%257Ea%2521b%2540c%2523d%2524e%25f%255E00%252611%252A22%252833%252944_55%252B",
        "http://host%23.com/~a!b@c%23d$e%25f^00&11*22(33)44_55+",
    ),
    ("http://3279880203/blah", "http://195.127.0.11/blah"),
    ("http://www.google.com/blah/..", "http://www.google.com/"),
    ("www.google.com/", "http://www.google.com/"),
    ("www.google.com", "http://www.google.com/"),
    ("http://www.evil.com/blah#frag", "http://www.evil.com/blah"),
    ("http://www.GOOgle.com/", "http://www.google.com/"),
    ("http://www.google.com.../", "http://www.google.com/"),
    ("http://www.google.com/foo\tbar\rbaz\n2", "http://www.google.com/foobarbaz2"),
    ("http://www.google.com/q?", "http://www.google.com/q"),
    ("http://www.google.com/q?r?", "http://www.google.com/q"),
    ("http://www.google.com/q?r?s", "http://www.google.com/q"),
    ("http://evil.com/foo#bar#baz", "http://evil.com/foo"),
    ("http://evil.com/foo;", "http://evil.com/foo;"),
    ("http://evil.com/foo?bar;", "http://evil.com/foo"),
    ("http://notrailingslash.com", "http://notrailingslash.com/"),
    ("http://www.gotaport.com:1234/", "http://www.gotaport.com/"),
    ("  http://www.google.com/  ", "http://www.google.com/"),
    ("http:// leadingspace.com/", "http://%20leadingspace.com/"),
    ("http://%20leadingspace.com/", "http://%20leadingspace.com/"),
    ("%20leadingspace.com/", "http://%20leadingspace.com/"),
    ("https://www.securesite.com/", "https://www.securesite.com/"),
    ("http://host.com/ab%23cd", "http://host.com/ab%23cd"),
    ("http://host.com//twoslashes?more//slashes", "http://host.com/twoslashes"),
    ("ftp://ftp.myfiles.com/", "ftp://ftp.myfiles.com/"),
    ("http://some%1bhost.com/%1b", "http://some%1bhost.com/%1b"),
    ("http://some%1Bhost.com/%1B", "http://some%1bhost.com/%1b"),
    ("  http://www.google.com/  ", "http://www.google.com/"),
    ("http://www.google.com/q?r?s%3F", "http://www.google.com/q"),
    ("http://\x01\x80.com/", "http://%01%80.com/"),
    ("http://www.\xc3\xbcmlat.com/", "http://www.xn--mlat-zra.com/"),
    ("http://www.\xc3\xbcmlat.com/", "http://www.xn--mlat-zra.com/"),
    ("http://[2001:470:1:18::114]/", "http://[2001:470:1:18::114]/"),
    ("http%3A%2F%2Fwackyurl.com:80/", "http://wackyurl.com/"),
    ("http://W!eird<>Ho$^.com/", "http://w!eird<>ho$^.com/"),
    ("http://i.have.way.too.many.dots.com/", "http://i.have.way.too.many.dots.com/"),
]

test_full_urls = [
    (
        "http://www.query-test.com/test?a=g&b=2&c=3",
        "http://www.query-test.com/test?a=g&b=2&c=3",
    ),
    (
        "http://www.query-test.com/test?b=2&a=0&c=3&a=g",
        "http://www.query-test.com/test?a=0&a=g&b=2&c=3",
    ),
    (
        "http://www.query-test.com/test?foo&a=0&c=3&bar",
        "http://www.query-test.com/test?a=0&bar&c=3&foo",
    ),
    ("http://www.google.com/q?", "http://www.google.com/q"),
    ("http://www.google.com/q?r?", "http://www.google.com/q?r?"),
    ("http://www.google.com/q?r?s", "http://www.google.com/q?r?s"),
    ("http://evil.com/foo?bar;", "http://evil.com/foo?bar;"),
    (
        "http://host.com//twoslashes?more//slashes",
        "http://host.com/twoslashes?more//slashes",
    ),
    (
        "https://foo.bar.evil.com/path/something?q=stuff&more#frags",
        "https://foo.bar.evil.com/path/something?more&q=stuff",
    ),
    (
        "http://example.it/display?lang=en&article=fred",
        "http://example.it/display?article=fred&lang=en",
    ),
    ("http://example.it/path1/path2?more", "http://example.it/path1/path2?more"),
    ("http://exa.it/query?a=1&a=1", "http://exa.it/query?a=1&a=1"),
    ("http://exa.it/query?a=1&a=2&a=3,4", "http://exa.it/query?a=1&a=2&a=3,4"),
    ("http://exa.it/query?a=1&a2", "http://exa.it/query?a=1&a2"),
    ("http://exa.it/query?a=1,2&&a=1", "http://exa.it/query?a=1&a=1,2"),
]


# split splits the string s around the delimiter c.
#
# Let string s be of the form:
# 	"%s%s%s" % (t, c, u)
#
# Then split returns (t, u) if cutc is set,
# otherwise, it returns (t, c+u).
# If c does not exist in s, then (s, "") is returned.
def split(s: bytes, c: bytes, cutc: bool):
    if s.count(c) == 0:
        return s, b""
    if cutc:
        i = s.index(c)
        return s[:i], s[i + len(c) :]
    i = s.index(c)
    return s[:i], s[i:]


# is_hex reports whether c is a hexadecimal character.
def is_hex(c: int):
    if chr(c) in string.hexdigits:
        return True
    return False


# is_unicode reports whether s is a Unicode string
def is_unicode(s: bytes):
    for x in s:
        if int(x) > 128:
            return True
    return False


# unescape returns the decoded form of a percent-encoded
# string s.
def unescape(s: bytes):
    b = bytearray()
    while len(s) > 0:
        if len(s) >= 3 and chr(s[0]) == "%" and is_hex(s[1]) and is_hex(s[2]):
            to_add = unquote_to_bytes(bytes(s[0:3]))
            b.extend(to_add)
            s = s[3:]
        else:
            b.append(s[0])
            s = s[1:]
    return b


# escape returns the percent-encoded form of the string s.
def escape(s: bytearray):
    b = bytearray()
    for c in s:
        if int(c) < 32 or int(c) >= 127 or chr(c) == " " or chr(c) == "#" or chr(c) == "%":
            bits = "%%%02x" % c
            b.extend(map(ord, bits))
        else:
            b.append(c)
    return b


# recursiveUnescape unescapes the string s recursively
# until it cannot be unescaped anymore. It reports
# an error if the unescaping process seemed to
# have no end.
def recursive_unescape(s: bytes):
    MAX_DEPTH = 1024
    b = bytearray()
    b.extend(s)
    for i in range(0, MAX_DEPTH):
        t = unescape(b)
        if t == b:
            return b
        b = t
    return ""


# normalizeEscape performs a recursive unescape and
# then escapes the string exactly once. It reports
# an error if it was unable to unescape the string.
def normalize_escape(s: bytes):
    u = recursive_unescape(s)
    return escape(u)


# get_scheme splits the url into (scheme, path) where scheme is the protocol.
# If the scheme cannot be determined ("", url) is returned.
def get_scheme(s: bytes):
    # http:
    if s.startswith(b"h") and len(s) > 4 and chr(s[4]) == ":":
        return s[:7], s[7:]
    # https:
    elif s.startswith(b"h") and len(s) > 5 and chr(s[5]) == ":":
        return s[:8], s[8:]
    # ftp:
    elif s.startswith(b"f") and len(s) > 3 and chr(s[3]) == ":":
        return s[:5], s[5:]
    # file:
    elif s.startswith(b"f") and len(s) > 4 and chr(s[4]) == ":":
        return s[:8], s[8:]
    # In this case there is no valid URL scheme
    return b"", s


# is_ip checks whether the hostname is IP address or not
def is_ip(s: bytes):
    b = bytearray()
    to_return = ""
    is_ip = False
    try:
        x = str(s, "utf-8")
        to_return = str(ipaddress.ip_address(x))
        is_ip = True
    except ValueError:
        pass
    try:
        i = int(s)
        to_return = str(ipaddress.ip_address(i))
        is_ip = True
    except ValueError:
        pass
    if is_ip:
        b.extend(map(ord, to_return))
        return b
    return s


# parse_qsl splits a query string into a list of (param, value) tuples
def parse_qsl(s: bytes):
    lst_tuples = []

    for item in s.split(b"&"):
        if len(item) > 0:  # to handle multiple separators
            second_split = item.split(b"=")
            if len(second_split) == 1:  # to handle param without value
                lst_tuples.append((item, b""))
            else:
                lst_tuples.append((second_split[0], second_split[1]))
    return lst_tuples


# parse_query parses input query (in bytes) to get a normalized query:
# - sort parameters (keys) in the query alphabetically
# - sort values associated to duplicate parameters alphabetically
# TO CONSIDER FOR FUTURE
# - combine values of duplicate parameters in array
# - eliminate duplicate key-value pairs
# - eliminate byte sequences not corresponding to key-value pairs
def parse_query(s: bytes):
    # save params as list of tuples (par,value)
    params_tuples = parse_qsl(s)

    # sort list by first and second element
    params_tuples.sort(key=lambda t: (t[0], t[1]))

    # transform list back into a query string
    to_return = b"&".join(
        par + b"=" + value if value != b"" else par for par, value in params_tuples
    )
    return to_return


# parse_host parses a string to get host by the stripping the
# username, password, and port.
def parse_host(s: bytes):
    # Drop username and password
    i = s.rfind(b"@")
    if i > 0:
        s = s[i + 1 :]
    # Parse an IP-literal
    # examples: "[fe80::1] or "[fe80::1%25en0]"
    if len(s) and s[0] == b"[":
        i = s.rfind(b"]")
        if i < 0:
            raise Exception("Missing ']' in host!")

    # Filter off port
    port = re.findall(find_port_re, s)
    if len(port):
        s = s.replace(port[0], b"")

    # Remove any useless '.' in the hostname
    s = re.sub(consecutive_dots_re[0], consecutive_dots_re[1], s)
    s = s[:-1] if s.endswith(b".") else s

    # Convert internazionalized hostnames to IDNA
    unescaped_s = unescape(s)
    if is_unicode(unescaped_s):
        try:
            s = str(unescaped_s, "utf-8").encode("idna")
        except UnicodeDecodeError:
            s = str(unescaped_s, "unicode_escape").encode("idna")

    # Lower case
    s = s.lower()

    # Convert host to IP Address if needed
    s = is_ip(s)
    return s


# parse_path parses a string to get a normalized path:
# - replaces multiple consecutive slashes with a single slash
# - eliminate each . path name element
# - eliminate each inner .. path name element (the parent directory)
#   along with the non-.. element that precedes it
# - eliminate .. elements that begin a rooted path: that is, replace "/.."
#   by "/" at the beginning of a path
#
# The returned path ends in a slash only if it is the root "/"
#
# If the result of this process is an empty string, parse_path returns the string "."
def parse_path(s: bytes):

    is_empty = len(s) == 0
    last_char_is_slash = s.endswith(b"/")

    # Replace any consecutive '/' in the path with a single '/'
    s = re.sub(consecutive_slashes_re[0], consecutive_slashes_re[1], s)

    # Eliminate . path name element, each inner .. along with the non-.. element,
    # and .. elements that begin a rooted path
    if not is_empty:
        s = posixpath.normpath(s)

    if not s.endswith(b"/") and (last_char_is_slash or is_empty):
        s += b"/"

    return s


def parse_url(url):
    # For legacy reasons, this is a simplified version of the net/url logic.
    #
    # Few cases where net/url was not helpful:
    # 1. URLs are are expected to have no escaped encoding in
    # the host but to be escaped in the path.
    # Safe Browsing allows escaped characters in both.
    # 2. Also it has different behavior with and without a
    # scheme for absolute paths. Safe Browsing test web
    # URLs only; and a scheme is optional. If missing,
    # we assume that it is an "http".
    # 3. We strip off the fragment as this is not
    # required for building patterns for Safe Browsing.
    # 4. We normalize the query to sort keys and values alphabetically

    # Remove the URL fragment.
    # Also, we decode and encode the URL.
    # The '#' in a fragment is not friendly to that.
    rest, fragment = split(url, b"#", True)
    # Start by stripping any leading and trailing whitespace.
    rest = rest.strip()
    # Remove any embedded tabs and CR/LF
    # characters which aren't escaped.
    rest = rest.replace(b"\t", b"")
    rest = rest.replace(b"\n", b"")
    rest = rest.replace(b"\r", b"")
    rest = normalize_escape(rest)
    scheme, rest = get_scheme(rest)
    if scheme == b"":
        scheme = b"http://"
    rest, query = split(rest, b"?", True)
    host, path = split(rest, b"/", False)
    host = parse_host(host)
    path = parse_path(path)
    normalized_url = scheme + host
    full_normalized_url = normalized_url
    if path != b"":
        normalized_url += path
        if query != b"":
            normalized_query = parse_query(query)
            full_normalized_url = normalized_url + b"?" + normalized_query
    return normalized_url, full_normalized_url, scheme, host, path, query, fragment


def canonical_url(url):
    if type(url) is not bytearray:
        try:
            url = bytearray(map(ord, url))
        except ValueError:
            url = bytearray(url, "utf-8")
    parsed_url, full_parsed_url, scheme, host, path, query, fragment = parse_url(url)
    return parsed_url, full_parsed_url, scheme, host, path, query, fragment


if __name__ == "__main__":
    # TESTING URLS
    count = 1
    for couple in test_urls:
        print("Checking couple {}, input: {} -> normalized: {}".format(count, couple[0], couple[1]))
        url_to_parse = bytearray()
        try:
            url_to_parse = bytearray(map(ord, couple[0]))
        except ValueError:
            url_to_parse = bytearray(couple[0], "utf-8")
        url_to_match = bytearray(couple[1], "utf-8")
        url_to_parse, full_url_to_parse = canonical_url(url_to_parse)
        url_to_parse_b = str(url_to_parse, "utf-8")
        url_to_match_b = str(url_to_match, "utf-8")
        assert url_to_parse == url_to_match, "{} Rule, {} is not equal to {}".format(
            count, url_to_parse_b, url_to_match_b
        )
        print(
            "Couple {} check passed! parsed: {}, full URL parsed {} -> normalized: {}\n".format(
                count, url_to_parse_b, full_url_to_parse, url_to_match_b
            )
        )
        count += 1

    # TESTING FULL URLS
    count = 1
    for couple in test_full_urls:
        print("Checking couple {}, input: {} -> normalized: {}".format(count, couple[0], couple[1]))
        url_to_parse = bytearray(map(ord, couple[0]))
        url_to_match = bytearray(couple[1], "utf-8")
        url_to_parse, full_url_to_parse = canonical_url(url_to_parse)
        url_to_parse_b = str(full_url_to_parse, "utf-8")
        url_to_match_b = str(url_to_match, "utf-8")
        assert full_url_to_parse == url_to_match, "{} Rule, {} is not equal to {}".format(
            count, url_to_parse_b, url_to_match_b
        )
        print(
            "Couple {} check passed! parsed: {}, full URL parsed {} -> normalized: {}\n".format(
                count, url_to_parse_b, full_url_to_parse, url_to_match_b
            )
        )
        count += 1
