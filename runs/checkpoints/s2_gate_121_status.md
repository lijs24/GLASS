# S2-Gate 121 Status: Localized Compare Tile Package

## Gate

S2-Gate 121: Localized Compare Tile Package.

## Completed Work

- Added `glass compare-tile-pack`.
- The command consumes a `compare-outliers` JSON artifact and exports the top
  residual tiles as small FITS cutouts.
- Optional PNG previews are written for GLASS, reference, absolute diff, and
  signed diff.
- The package preserves the compare audit candidate transform, source image
  coordinates, coverage map, and top-tile metadata.
- Added `tile_pack_manifest.json` with tile extents, artifact paths, and local
  signed/absolute difference statistics.
- Added focused API and CLI tests.
- Updated the Phase 2 gate plan and algorithm-source ledger.

## Real 200-Light Tile Package

Command input:

- Audit:
  `C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.json`

Artifact:

- `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`

Exported top tiles:

| Tile | Extent | abs p99 | abs max | signed mean |
| ---: | --- | ---: | ---: | ---: |
| 0 | x=1488..2128, y=3536..4176 | 0.0015709820389747625 | 0.20986396074295044 | -0.0003904426131072114 |
| 1 | x=464..1104, y=464..1104 | 0.0028177165798842965 | 0.1004926934838295 | -0.00012285434405214345 |
| 2 | x=1488..2128, y=3024..3664 | 0.0011004611104726792 | 0.013945672661066055 | -0.0001592893958692798 |

Manual preview inspection of the first two signed-diff PNGs shows localized
negative residual structures around stars and nebulosity-like signal, not an
edge-band or global coverage artifact. This agrees with S2-Gate 120's
`localized_tail` recommendation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\compare_tile_pack.py src\glass\cli.py tests\test_compare_tile_pack.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_tile_pack.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe compare-tile-pack --audit "C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.json" --out-dir "C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles" --max-tiles 3 --pad-px 64 --preview-max-size 768
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_121_doctor.json
```

## Test Result

- Focused ruff: passed.
- Focused pytest: 3 passed.
- Full ruff: passed.
- Full pytest: 325 passed in 17.69 s.
- Native CUDA build: passed; Ninja reported no work to do.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs\checkpoints\s2_gate_121_doctor.json`.

## Known Limitations

- This gate is diagnostic only and does not change registration, local
  normalization, rejection, weighting, or integration defaults.
- The tile package currently reads full compared images before slicing, so it
  is intended for diagnostic output masters and not raw-frame streaming.
- The package localizes residual morphology but does not yet attribute a tile
  to specific input frames or rejection decisions.

## Next Step

S2-Gate 122 should add per-tile frame contribution and rejection attribution for
the localized residual regions exported here.

## Clean-Room Compliance

This gate uses only GLASS-generated artifacts and user-generated external
reference outputs. It does not read, copy, summarize, or rework proprietary
implementation source code.
