# Gate 14 Status: Optional PixInsight Front-end

- Gate: 14
- Date: 2026-05-13
- Status: completed as optional launcher

## Completed

- Added `pixinsight/GLASS.js`, an independent clean-room launcher for the
  external `glass` CLI.
- Added `pixinsight/README.md` with manual use instructions.
- Added `docs/pixinsight_frontend.md` documenting the front-end boundary.
- Added tests that verify the launcher is a thin wrapper around `glass audit`
  and does not contain forbidden official preprocessing script names.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check tests\test_pixinsight_frontend.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_pixinsight_frontend.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- PixInsight front-end tests: `2 passed in 0.01s`.
- Full suite: `180 passed in 7.96s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: true.

## Known Limitations

- The launcher was not executed inside PixInsight during automated tests.
- The supported automation interface remains the `glass` CLI.
- The launcher does not implement PixInsight process instances or scientific
  image-processing algorithms; it only calls `glass audit` externally.

## Next Step

- Keep Phase B work separate from the completed core Gate 0-14 path.

## Clean-room

- Compliant.
- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- The launcher does not modify PixInsight installation directories.
