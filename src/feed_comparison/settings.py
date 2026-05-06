import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


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

        Optionally loads a ``.env`` file first. The default search behaviour
        of ``python-dotenv`` walks up from the current working directory.
        """
        load_dotenv(dotenv_path=env_file, override=False)

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
