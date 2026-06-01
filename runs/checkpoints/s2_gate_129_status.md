# S2 Gate 129 Status

## Gate

S2-Gate 129: Localized Frame-Weight Proposal

## Completed

- Added `glass frame-weight-proposal` to convert a localized
  `compare-tile-integration` audit into an explicit per-frame multiplier
  proposal JSON and optional Markdown summary.
- Added optional resident CUDA argument `--resident-frame-weight-proposal`.
- Resident CUDA now applies proposal multipliers after baseline integration
  weighting, triangle agreement downweighting, and registration-motion
  weighting.
- Resident artifacts now record proposal path, frame count, applied
  downweighted count, per-frame proposal multipliers, and registration warnings.
- Added focused tests for proposal generation, CLI output, proposal loading,
  and resident CUDA application.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass\report\frame_weight_proposal.py tests\test_frame_weight_proposal.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_weight_proposal.py tests\test_cli_smoke.py::test_cli_help_commands tests\test_resident_cuda_run.py::test_frame_weight_proposal_loader_accepts_list_and_object`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration`
- `.\.venv\Scripts\glass.exe frame-weight-proposal --integration-audit C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.json --out C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_control_ratio_proposal.json --markdown C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_control_ratio_proposal.md --min-multiplier 0.05 --max-multiplier 1.0`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_run --backend cuda --until-stage integration --memory-mode resident ... --resident-frame-weight-proposal C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_control_ratio_proposal.json`
- `.\.venv\Scripts\glass.exe compare-outliers --glass C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_run\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_outliers.json --markdown C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_outliers.md --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --ignore-border-px 16 --target-abs-diff 0.00042000063695013523 --tile-size 256 --top-tiles 10 --top-pixels 25 --glass-coverage-map C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_run\integration\resident_coverage_map_H.fits`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_129_doctor.json`
- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`

## Test Results

- Focused ruff: passed.
- Focused proposal/help tests: `5 passed in 0.64s`.
- Focused resident CUDA proposal application test: `1 passed in 0.31s`.
- Full ruff: passed.
- Full pytest: `343 passed in 18.24s`.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_129_doctor.json`.

## Real 200-Light Candidate

- Proposal source:
  `C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.json`.
- Proposal artifact:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_control_ratio_proposal.json`.
- Markdown summary:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_control_ratio_proposal.md`.
- Proposed multiplier: `0.3198566500155444`.
- Proposal frames: 11, F000100-F000110.
- Candidate run:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_run`.
- Runtime: `17.948854899965227 s`.
- Frame accounting: 193 positive-weight frames, 7 zero-weight frames, 200 total.
- Applied proposal downweights: 11 frames.
- Compare-outliers artifact:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_outliers.json`.
- Compare-outliers Markdown:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_outliers.md`.
- Target-threshold exceedance pixels: `647877`.
- Tail pixels: `590492`.

## Interpretation

The infrastructure is green, but the first `control_ratio` candidate is not
promotable. It preserves frame counts and runtime, but global strict-threshold
exceedance worsened versus the previous Gate120/Gate128 baseline near
599k pixels. This indicates that whole-frame downweighting from a localized
residual family can reduce local contribution evidence while damaging other
regions. The next corrective work should be spatially localized, or should
model rejection/registration residuals at tile level rather than multiplying
entire light frames.

## Known Limitations

- `frame-weight-proposal` currently supports only `control_ratio`.
- The proposal is an explicit experiment artifact and is disabled by default.
- Proposal multipliers are frame-wide, not tile-local.
- The first real candidate is negative evidence and must not be promoted into
  defaults.

## Next Step

S2-Gate 130 should target tile-local residual handling: either a spatially
localized correction/weight mask experiment or a resident integration diagnostic
that captures per-tile per-frame accepted contribution directly from the native
integration path.

## Clean-Room Compliance

Compliant. This gate uses only GLASS-generated diagnostics, GLASS resident CUDA
artifacts, user image inputs treated as read-only, and user-generated external
reference outputs. It does not read, copy, summarize, or rework proprietary
implementation source code.
