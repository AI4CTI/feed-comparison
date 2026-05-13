"""Banner is decorative — it must NEVER write to stdout (would break
machine-readable subcommands like `list-feeds --json`) and must stay
silent in non-interactive contexts (CI logs, output redirected to a file)
unless the user explicitly opts in."""

import contextlib
from unittest.mock import patch

from feed_comparison.cli.banner import print_banner


def test_banner_is_silent_when_stderr_not_a_tty(capsys):
    """The default behaviour for non-TTY stderr is silence — important
    for piped output and CI logs."""
    with patch("sys.stderr.isatty", return_value=False):
        print_banner()
    captured = capsys.readouterr()
    assert captured.out == "", "Banner must never write to stdout"
    assert captured.err == "", "Banner must stay silent on non-TTY stderr"


def test_banner_writes_to_stderr_when_tty(capsys):
    """When stderr is a TTY, the banner appears on stderr only."""
    with patch("sys.stderr.isatty", return_value=True):
        print_banner()
    captured = capsys.readouterr()
    assert captured.out == "", "Banner must never write to stdout"
    assert "feed-comparison" in captured.err
    assert "phishing feeds" in captured.err


def test_banner_suppressed_by_flag_even_on_tty(capsys):
    """The --no-banner flag (suppress=True) wins even when stderr is a TTY."""
    with patch("sys.stderr.isatty", return_value=True):
        print_banner(suppress=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_banner_silent_on_unicode_encode_error(capsys):
    """Old terminals without UTF-8 support: skip banner instead of crashing."""

    class _BrokenStderr:
        def isatty(self):
            return True

        def write(self, _):
            raise UnicodeEncodeError("ascii", "x", 0, 1, "boom")

        def flush(self):
            pass

    with patch("sys.stderr", _BrokenStderr()):
        print_banner()  # must not raise


def test_main_prints_banner_on_bare_invocation(capsys, monkeypatch):
    """Regression: `feed-comparison` (no args) must show the banner.

    Typer's `no_args_is_help=True` short-circuits to --help BEFORE the
    root callback runs, so the banner has to be printed by the entry-point
    wrapper (`main()`), not by the callback."""
    from feed_comparison.cli.app import main

    monkeypatch.setattr("sys.argv", ["feed-comparison"])
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    # Typer prints help and raises SystemExit(0) for no_args_is_help.
    with contextlib.suppress(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "feed-comparison" in captured.err
    assert "phishing feeds" in captured.err


def test_main_suppresses_banner_for_version_flag(capsys, monkeypatch):
    """`--version` is consumed by scripts; the banner must stay quiet."""
    from feed_comparison.cli.app import main

    monkeypatch.setattr("sys.argv", ["feed-comparison", "--version"])
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    with contextlib.suppress(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "feed-comparison 0." in captured.out  # version printed on stdout
    assert "███" not in captured.err, "Banner must NOT appear with --version"


def test_main_strips_no_banner_from_argv(monkeypatch):
    """`--no-banner` is suppressed by main() and stripped from sys.argv,
    so subcommands don't fail on an unknown flag."""
    from feed_comparison.cli import app as app_module

    monkeypatch.setattr("sys.argv", ["feed-comparison", "list-feeds", "--no-banner"])
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setattr(app_module, "app", lambda: None)  # don't actually run Typer
    app_module.main()
    assert "--no-banner" not in __import__("sys").argv
