import logging

from feed_comparison.cli._logging import _SECRET_LEAKING_LOGGERS, configure_logging


def _restore_levels():
    """Snapshot/restore loggers we mutate so tests don't leak global state."""
    return {name: logging.getLogger(name).level for name in _SECRET_LEAKING_LOGGERS}


def test_verbose_mode_keeps_secret_leaking_loggers_at_info():
    snapshot = _restore_levels()
    try:
        configure_logging(verbose=True)
        # Our own logger goes DEBUG with --verbose ...
        assert logging.getLogger("feed_comparison").getEffectiveLevel() == logging.DEBUG
        # ... but third-party loggers known to print Authorization headers
        # at DEBUG are pinned at INFO so secrets don't leak into bug reports.
        for name in _SECRET_LEAKING_LOGGERS:
            assert logging.getLogger(name).level == logging.INFO, name
    finally:
        for name, level in snapshot.items():
            logging.getLogger(name).setLevel(level)


def test_non_verbose_mode_does_not_lower_third_party_loggers():
    snapshot = _restore_levels()
    try:
        # Pre-set one to a non-default value to verify we don't touch it.
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        configure_logging(verbose=False)
        assert logging.getLogger("urllib3").level == logging.WARNING
    finally:
        for name, level in snapshot.items():
            logging.getLogger(name).setLevel(level)
