import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def canonicalize_cases():
    with (DATA_DIR / "canonicalize_cases.json").open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def output_dir(tmp_path):
    out = tmp_path / "output"
    out.mkdir()
    return out
