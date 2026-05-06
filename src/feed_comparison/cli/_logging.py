import logging

from rich.logging import RichHandler

# Third-party loggers we explicitly keep at INFO even when the user asks for
# DEBUG-level verbosity, because at DEBUG they print HTTP request/response
# details — including Authorization / API-Key / Cookie headers. Leaking a
# bearer token into a debug log that a user pastes into a bug report is a
# realistic, high-impact mistake we want to prevent by default.
_SECRET_LEAKING_LOGGERS = (
    "urllib3",
    "requests",
    "requests_oauth2client",
    "taxii2client",
    "pymisp",
)


def configure_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    # `force=True` re-configures the root logger even if a previous call (or
    # a test fixture) has already set up handlers; without it `basicConfig`
    # is a silent no-op the second time around and the verbosity flag has
    # no effect.
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_time=True, show_path=False)],
        force=True,
    )

    if verbose:
        for name in _SECRET_LEAKING_LOGGERS:
            logging.getLogger(name).setLevel(logging.INFO)
