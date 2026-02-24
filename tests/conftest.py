from pathlib import Path

import pytest


@pytest.fixture()
def created_at() -> str:
    return "1970-01-01T00:00:00Z"


@pytest.fixture()
def template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "docreview" / "templates"
