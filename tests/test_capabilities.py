from __future__ import annotations

from glass.capabilities import capability_report


def test_capability_report_records_structured_gate_flags():
    report = capability_report()

    assert report["metadata_scan"] is True
    assert report["planning"] is True
    assert report["cpu_baseline"] is True
    assert isinstance(report["cuda_features"], dict)
    assert report["registration"]["status"].startswith("partial")
    assert "resident" in report["registration"]["cuda"]
    assert "coefficient artifacts" in report["local_normalization"]["cpu"]
    assert "resident global/grid mean/std" in report["local_normalization"]["cuda"]
    assert "simple_snr weights" in report["weighted_integration"]["cuda"]
    assert report["weighted_integration"]["status"] == "partial WBPP-like integration"


def test_capability_report_can_skip_cuda_probe():
    report = capability_report(probe_cuda=False)

    assert report["cuda_available"] is False
    assert report["cuda_features"] == {}
