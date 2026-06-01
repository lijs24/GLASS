# S2 Gate 132 Status

## Gate

S2-Gate 132: Tile-Local Policy Proposal

## Completed

- Added `glass tile-local-policy-proposal`.
- The command consumes a `resident-tile-contribution` artifact and the matching
  residual tile-pack manifest.
- It solves a first-order tile-local multiplier for a target group, currently
  `focus` or `control`, from signed GLASS-minus-reference residuals and
  resident-captured group contribution in reference units.
- It records per-tile action (`boost`, `downweight`, `hold`, or
  `insufficient_signal`), unconstrained multiplier, clamped multiplier,
  predicted residual after the local multiplier, reduction fraction, and a
  summary recommendation.
- Added focused tests and CLI help coverage.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\tile_local_policy.py tests\test_tile_local_policy.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_policy.py tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\glass.exe tile-local-policy-proposal --contribution C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.json --out C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_signed_mean_policy.json --markdown C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_signed_mean_policy.md --target-group focus --residual-stat signed_mean --min-multiplier 0.0 --max-multiplier 2.0`
- `.\.venv\Scripts\glass.exe tile-local-policy-proposal --contribution C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.json --out C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_tail_policy.json --markdown C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_tail_policy.md --target-group focus --residual-stat tail_signed_mean --min-multiplier 0.0 --max-multiplier 2.0`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_132_doctor.json`
- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`

## Test Results

- Focused ruff: passed.
- Focused tests: `5 passed in 0.52s`.
- Full ruff: passed.
- Full pytest: `352 passed in 38.07s`.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_132_doctor.json`.

## Real Artifact Results

- Input contribution:
  `C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.json`.
- Signed-mean proposal:
  `C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_signed_mean_policy.json`.
- Signed-mean Markdown:
  `C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_signed_mean_policy.md`.
- Tail proposal:
  `C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_tail_policy.json`.
- Tail Markdown:
  `C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_tail_policy.md`.

Signed-mean proposal summary:

- Recommendation: `tile_local_policy_candidate`.
- Tiles toward reference: 3.
- Tiles away from reference: 0.
- Boost tiles: 3.
- Downweight tiles: 0.
- Clamped tiles: 3.
- Mean absolute residual before: `0.00022419545100954487`.
- Mean absolute residual after: `0.00017668149320412265`.

Per-tile signed-mean proposal:

- Tile 0: unconstrained multiplier `9.126479793677584`, clamped to `2.0`,
  predicted residual `-0.0003904426131072114 -> -0.0003423968881414056`.
- Tile 1: unconstrained multiplier `3.5919180627529235`, clamped to `2.0`,
  predicted residual `-0.00012285434405214345 -> -0.00007545533641466528`.
- Tile 2: unconstrained multiplier `4.382145776148059`, clamped to `2.0`,
  predicted residual `-0.0001592893958692798 -> -0.0001121922550562971`.

Tail-signed proposal summary:

- Recommendation: `tile_local_policy_candidate`.
- Tiles toward reference: 3.
- Tiles away from reference: 0.
- Boost tiles: 3.
- Clamped tiles: 3.

## Interpretation

The direction is now consistent across three independent diagnostic layers:

- S2-Gate 130 showed full-frame downweighting moves the localized negative
  residuals away from the reference.
- S2-Gate 131 showed the focus-family contribution is present in resident CUDA
  post-warp pixels, not just CPU replay.
- S2-Gate 132 shows a tile-local correction would need to boost, not downweight,
  the F000100-F000110 focus-family contribution inside these localized tiles.

The unconstrained multipliers are large and all capped at `2.0`, so this is not
a production policy yet. It is a strong direction signal for a future
tile-local native implementation or a deeper local-normalization/rejection
investigation.

## Known Limitations

- Artifact-only. No integration output is changed.
- Uses tile-level means, not per-pixel native integration weights.
- Boost multipliers above 1 require a future tile-local integration
  implementation before they can affect production results.
- The proposal is derived from localized residual diagnostics and should not be
  generalized without additional benchmark gates.

## Next Step

S2-Gate 133 should prototype an explicit tile-local integration experiment on
captured resident tiles, applying the proposal only inside the selected tiles
and measuring whether the reconstructed tile residual improves without relying
on full-frame multipliers. A later native gate can move the same policy into
CUDA only if the localized experiment is numerically promising.

## Clean-Room Compliance

Compliant. This gate uses only GLASS resident contribution artifacts, GLASS
comparison tile packs, and user-generated reference residual summaries. It
does not read, copy, summarize, or rework proprietary implementation source
code.
