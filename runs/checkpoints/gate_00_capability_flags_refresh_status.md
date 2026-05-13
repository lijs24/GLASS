# Gate 00 Capability Flags Refresh Status

## Gate

Gate 00 audit/capability metadata checkpoint.

## Completed Content

- Refreshed `capability_report()` so it no longer reports outdated early-gate capability text.
- Added structured registration, Local Normalization, and integration capability records.
- Added dynamic CUDA feature flags for important native/resident primitives:
  - Lanczos3 matrix warp;
  - grid Local Normalization apply;
  - resident stack;
  - resident grid Local Normalization apply;
  - resident sigma/winsorized rejection.
- Added tests to ensure the capability report clearly marks partial status and current LN/registration support.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\capabilities.py tests\test_capabilities.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_capabilities.py tests\test_cli_smoke.py tests\test_cuda_import.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Targeted capability/CLI/CUDA import tests: `5 passed in 0.23s`.
- Full test suite: `170 passed in 7.84s`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- Capability flags are descriptive metadata. They do not complete missing gates.
- Registration, Local Normalization, and weighted integration are explicitly marked partial.

## Next Step

- Keep capability flags synchronized with each new gate so `glass` does not overstate or understate implemented behavior.

## Clean-room Compliance

- Compliant. This is project-owned metadata.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
