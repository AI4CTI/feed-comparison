import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables and ``.env``.

    Per-feed credentials are optional: feeds that need them will refuse to run
    with a clear error message; feeds that do not are immediately usable.
    """

    # Per-feed credentials
    misp_url: str | None = None
    misp_key: str | None = None
    phishtank_username: str | None = None
    urlscan_url: str | None = None
    urlscan_token: str | None = None

    # Generic
    output_dir: Path = Path("./output")

    @classmethod
    def from_env(cls, env_file=None):
        """Build a Settings instance from environment variables.

        If ``env_file`` is given, that file is loaded; otherwise we walk up
        from the *current working directory* looking for a ``.env`` file.
        We must pass ``usecwd=True`` to ``find_dotenv``: the default
        behaviour starts the search from the caller's source file, which
        breaks completely when ``feed-comparison`` is installed as a tool
        (the caller then lives inside an isolated tool venv, far from the
        user's project directory).
        """
        dotenv_path = str(env_file) if env_file is not None else find_dotenv(usecwd=True)

        if dotenv_path:
            loaded = load_dotenv(dotenv_path=dotenv_path, override=False)
            if loaded:
                _log.debug("Loaded environment from %s", dotenv_path)
        else:
            _log.debug("No .env file found while walking up from %s", Path.cwd())

        output_dir = os.environ.get("FEED_COMPARISON_OUTPUT_DIR", "./output")
        return cls(
            misp_url=os.environ.get("MISP_URL"),
            misp_key=os.environ.get("MISP_KEY"),
            phishtank_username=os.environ.get("PHISHTANK_USERNAME"),
            urlscan_url=os.environ.get("URLSCAN_URL"),
            urlscan_token=os.environ.get("URLSCAN_TOKEN"),
            output_dir=Path(output_dir),
        )

    def require(self, *names):
        """Return the listed credential values or raise if any is missing."""
        missing = [n for n in names if not getattr(self, n, None)]
        if missing:
            raise MissingCredentialsError(missing)
        return tuple(getattr(self, n) for n in names)


class MissingCredentialsError(RuntimeError):
    def __init__(self, missing):
        self.missing = list(missing)
        env_hints = ", ".join(name.upper() for name in self.missing)
        super().__init__(
            f"Missing required credential(s): {env_hints}. "
            "Set them in the environment or in a .env file."
        )


class MissingOptionalDependencyError(RuntimeError):
    """Raised when a feed needs an optional Python package that is not installed."""

    def __init__(self, extra, packages):
        self.extra = extra
        self.packages = list(packages)
        pkgs = ", ".join(self.packages)
        super().__init__(
            f"This feed requires the optional '{extra}' extra (Python package(s): {pkgs}). "
            f"Install it with: uv tool install --force 'feed-comparison[{extra}]' "
            f"(or: pip install 'feed-comparison[{extra}]')."
        )
