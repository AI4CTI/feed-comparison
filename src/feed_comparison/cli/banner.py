"""ASCII banner printed on stderr at the top of every CLI invocation.

We skip the banner when stderr isn't a TTY (so output piped to a file or
captured in CI logs stays clean), when the user passes --no-banner, or
when ``FEED_COMPARISON_NO_BANNER`` is set in the environment.

Stderr (not stdout) is intentional: subcommands like
``list-feeds --json`` write machine-readable output to stdout that
must not be polluted by the banner.
"""

import sys

_BANNER = (
    "\033[1;31m"  # bold red
    "███████╗██████╗ ███╗   ███╗███████╗███████╗\n"
    "██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝\n"
    "█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗\n"
    "██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║\n"
    "███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║\n"
    "╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝"
    "\033[0m\n"  # reset
    "\033[2m"  # dim
    "         feed-comparison · benchmark phishing feeds"
    "\033[0m\n"  # reset
)


def print_banner(suppress: bool = False) -> None:
    """Print the ASCII banner to stderr, unless suppressed.

    The banner is suppressed when:
      * ``suppress=True`` (typically wired to a ``--no-banner`` CLI flag
        with ``FEED_COMPARISON_NO_BANNER`` as the matching env var)
      * stderr isn't a TTY (piped to a file, captured by CI, …)
      * the terminal can't encode the box-drawing Unicode glyphs
    """
    if suppress or not sys.stderr.isatty():
        return
    try:
        sys.stderr.write(_BANNER)
        sys.stderr.flush()
    except UnicodeEncodeError:
        # Older terminals without UTF-8 support: silently skip rather
        # than crashing. The banner is decorative; nothing depends on it.
        pass
