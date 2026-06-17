from __future__ import annotations

from pathlib import Path


def test_windows_portable_builder_declares_package_label_and_isolated_user_site():
    script = Path("packaging/windows/build_portable.ps1").read_text(encoding="utf-8")

    assert "[string]$PackageLabel" in script
    assert "GLASS-Portable-win64-$PackageLabelValue.zip" in script
    assert "$env:PYTHONNOUSERSITE = \"1\"" in script
    assert "set PYTHONNOUSERSITE=1" in script
    assert "package_manifest.json" in script
    assert "Write-Utf8NoBomFile" in script
    assert "System.Text.UTF8Encoding($false)" in script
    assert "Import-VisualStudioBuildEnvironment" in script
    assert "vswhere.exe" in script
    assert "vcvars64.bat" in script
