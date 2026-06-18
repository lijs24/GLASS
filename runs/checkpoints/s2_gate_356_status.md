# S2-Gate 356 Status

- Gate: S2-Gate 356
- Scope: Phase2 quality saturation handoff
- Status: green
- Date: 2026-06-19

## Completed Content

- Added optional `frame_quality.json` ingestion to `glass phase2-status` via
  `--quality-results`.
- Added `quality_saturation` summary payload with saturation status, pass/fail
  state, total/saturated frame counts, saturation quality-gate rejection count,
  maximum/mean saturation fraction, threshold/source metadata, worst frame id,
  and rejected frame ids.
- Added Phase2 status check `quality_saturation_no_rejections`; explicitly
  supplied quality artifacts with saturation quality-gate rejections now make
  Phase2 status `attention_required`.
- Added `quality_saturation_no_rejections_preserved` to
  `glass phase2-status-compare` so candidates cannot lose previously passing
  saturation handoff evidence.
- Added Phase2 Markdown and CLI console output for saturation handoff evidence.
- Added focused build, CLI, Markdown, and compare tests.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\phase2_status.py src\\glass\\cli.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py::test_phase2_status_surfaces_quality_saturation_summary tests\\test_phase2_status.py::test_phase2_status_blocks_quality_saturation_rejection tests\\test_phase2_status.py::test_phase2_status_compare_flags_quality_saturation_regression tests\\test_phase2_status.py::test_cli_phase2_status_writes_outputs`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status --checkpoint-dir runs\\checkpoints --quality-results runs\\checkpoints\\s2_gate_356_quality_saturation_pass_frame_quality.json --out runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_pass_status.json --markdown runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_pass_status.md`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status --checkpoint-dir runs\\checkpoints --quality-results runs\\checkpoints\\s2_gate_354_quality_saturation_run\\frame_quality.json --out runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_fail_status.json --markdown runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_fail_status.md`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_pass_status.json --candidate-status runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_fail_status.json --out runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_compare.json --markdown runs\\checkpoints\\s2_gate_356_phase2_quality_saturation_compare.md`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_356_cuda_doctor.json --allow-cpu-only`
- `Select-String` checks over Gate356 Phase2 status and compare Markdown
  artifacts for `Quality Saturation`,
  `quality_saturation_no_rejections_preserved`, and saturation rejection
  counts.

## Test Results

- Ruff: passed.
- Focused pytest: `4 passed in 0.43s`.
- Full pytest: `809 passed in 34.30s`.
- Phase2 pass artifact: `status=green`,
  `quality_saturation_status=passed`, rejected count `0`.
- Phase2 fail artifact: `status=attention_required`,
  `quality_saturation_status=attention_required`, rejected count `1`.
- Phase2 compare artifact: `status=regressed` with failed
  `quality_saturation_no_rejections_preserved`.

## CUDA Status

- CUDA available: yes.
- CUDA extension importable: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_356_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_356_quality_saturation_pass_frame_quality.json`
- `runs/checkpoints/s2_gate_356_phase2_quality_saturation_pass_status.json`
- `runs/checkpoints/s2_gate_356_phase2_quality_saturation_pass_status.md`
- `runs/checkpoints/s2_gate_356_phase2_quality_saturation_fail_status.json`
- `runs/checkpoints/s2_gate_356_phase2_quality_saturation_fail_status.md`
- `runs/checkpoints/s2_gate_356_phase2_quality_saturation_compare.json`
- `runs/checkpoints/s2_gate_356_phase2_quality_saturation_compare.md`
- `runs/checkpoints/s2_gate_356_cuda_doctor.json`
- `runs/checkpoints/s2_gate_356_status.md`

## Artifact Summary

- Passing quality artifact: 2 frames, 1 saturated frame, 0 saturation
  quality-gate rejections, worst frame `F_SAT`.
- Failing quality artifact: reused
  `runs/checkpoints/s2_gate_354_quality_saturation_run/frame_quality.json`,
  2 frames, 1 saturated frame, 1 saturation quality-gate rejection, worst
  frame `bad`.
- Compare regression evidence shows a previously passing quality-saturation
  handoff cannot regress to `attention_required` without a failed compare
  check.

## Known Limitations

- This gate only carries existing Gate354/Gate355 saturation evidence into
  Phase2 status and compare reports; it does not add a new saturation metric,
  visualization, or default threshold.
- The status check fails only on saturation quality-gate rejections, not on
  every nonzero saturated-pixel count.
- This gate does not change quality metric math, star detection, registration,
  integration, CUDA kernels, runtime defaults, packaging, publication, or
  real-data benchmark outputs.

## Next Step

- Continue Phase2 quality hardening with the next missing quality diagnostic or
  carry this status handoff into acceptance/release gates if the publication
  chain should require saturation evidence.

## Clean-Room Compliance

- Compliant. This gate used only GLASS-owned `frame_quality.json` artifacts,
  Phase2 status/compare code, CLI code, tests, docs, and generated checkpoint
  artifacts.
- No official PixInsight/WBPP/PJSR source code or proprietary implementation
  material was read, copied, summarized, or reworked.
- Input image directories were not modified.
