from __future__ import annotations

from gpwbpp.capabilities import capability_report


def test_capability_report_records_structured_gate_flags():
    report = capability_report()

    assert report["metadata_scan"] is True
    assert report["planning"] is True
    assert report["cpu_baseline"] is True
    assert isinstance(report["cuda_features"], dict)
    assert report["registration"]["status"].startswith("partial")
    assert "resident" in report["registration"]["cuda"]
    assert "coefficient artifacts" in report["local_normalization"]["cpu"]
    assert "resident grid apply" in report["local_normalization"]["cuda"]
    assert report["weighted_integration"]["status"] == "partial WBPP-like integration"
