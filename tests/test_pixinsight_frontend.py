from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pixinsight_launcher_is_clean_room_wrapper():
    script = ROOT / "pixinsight" / "GPWBPP.js"
    text = script.read_text(encoding="utf-8")

    assert "gpwbpp" in text
    assert "audit" in text
    assert "ExternalProcess" in text
    assert "official preprocessing scripts" in text
    assert "WeightedBatchPreprocessing" not in text
    assert "BatchPreprocessing" not in text
    assert "WBPP.js" not in text
    assert "FBPP.js" not in text


def test_pixinsight_frontend_docs_exist():
    assert (ROOT / "pixinsight" / "README.md").exists()
    assert (ROOT / "docs" / "pixinsight_frontend.md").exists()
