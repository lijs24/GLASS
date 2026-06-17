# S2-Gate 149 Status - Tile-Local Rejection/Registration Audit

## Gate

S2-Gate 149: tile-local rejection/registration audit.

## Completed

- Added `glass tile-local-rejection-registration-audit`.
- Aggregated resident contribution frame rows by frame id across residual
  candidate tiles.
- Ranked high-rejection frames and recorded focus/control/top-family
  membership, high/low/rejected/accepted fractions, triangle agreement score,
  agreement weight multiplier, NCC, registration RMS, and status counts.
- Added group summaries and correlation diagnostics for high rejection versus
  registration/agreement metrics.
- Added focused unit and CLI smoke coverage.
- Ran the audit on the S2-Gate 144 new-region contribution artifact using the
  S2-Gate 147 frame-family search artifact.
- Updated Phase 2 planning and algorithm-source documentation.

## Real-Data Artifacts

- Rejection/registration audit JSON:
  `C:\glass_runs\phase2_s2_gate_149_rejection_registration\new_region_rejection_registration_audit.json`
- Rejection/registration audit Markdown:
  `C:\glass_runs\phase2_s2_gate_149_rejection_registration\new_region_rejection_registration_audit.md`
- Doctor report:
  `runs\checkpoints\s2_gate_149_doctor.json`

## Real-Data Results

- Recommendation: `prioritize_registration_agreement_rejection_interaction`.
- Focus minus control high-rejected fraction mean: `0.032384334910999645`.
- Focus minus other high-rejected fraction mean: `0.035392264735119035`.
- High-rejection-excess frame count: `17`.
- Low-agreement high-rejection frame count: `16`.
- Top frame-family high-rejection-excess frame count: `11`.
- High rejection vs triangle agreement score correlation:
  `-0.26200282754894316`.
- High rejection vs triangle NCC correlation: `-0.046714858848798675`.
- High rejection vs registration RMS correlation: `0.03841985181571034`.

Group means:

| group | frames | high rejected | rejected | accepted | agreement score | NCC | RMS px | agreement weight |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| focus/top family | `11` | `0.03684152256358753` | `0.03687884590842507` | `0.963121154091575` | `0.4551052727272728` | `0.9293301818181819` | `0.6558194919065996` | `0.5688816363636365` |
| control | `10` | `0.0044571876525878905` | `0.0045989990234375` | `0.9954010009765625` | `0.5247729999999999` | `0.9413615999999999` | `0.6147008538246155` | `0.6559663` |
| other | `172` | `0.0014492578284685002` | `0.002786519915558571` | `0.9972134800844414` | `0.5115823485380117` | `0.8986299773099414` | `0.636805041238319` | `0.6394779403508771` |

Top high-rejection frames begin with `F000100`, `F000101`, `F000102`,
`F000103`, `F000104`, and `F000105`, all in the focus/top-family group. This
supports investigating the registration-agreement/rejection interaction before
promoting any tile-local boost policy.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_rejection_registration_audit.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_rejection_registration_audit.py src\glass\cli.py tests\test_tile_local_rejection_registration_audit.py tests\test_cli_smoke.py
.\.venv\Scripts\glass.exe tile-local-rejection-registration-audit --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --frame-family-search C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search.json --out C:\glass_runs\phase2_s2_gate_149_rejection_registration\new_region_rejection_registration_audit.json --markdown C:\glass_runs\phase2_s2_gate_149_rejection_registration\new_region_rejection_registration_audit.md --high-rejection-threshold 0.01 --low-agreement-score-threshold 0.5 --top-n 30
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_149_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused pytest after test correction: `3 passed in 1.09s`.
- Full pytest: `380 passed in 134.80s (0:02:14)`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_149_doctor.json`.

The first full-pytest attempt used a `120 s` command timeout and was killed by
the tool before completion; the same command was immediately re-run with a
longer timeout and passed.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Recommended package: `cuda`.

## Known Limitations

- This gate consumes GLASS resident contribution JSON only; it does not read
  image pixels or run integration.
- Correlations are diagnostic and do not prove root cause.
- The audit uses registration/agreement metrics recorded in the contribution
  artifact and does not recompute registration.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 150 should create a measured experiment plan around the
registration-agreement/rejection interaction. The likely next safe step is a
bounded replay or candidate run that adjusts the treatment of the
F000100-F000110 high-rejection/low-agreement family, then compares residual
tiles, full-frame agreement, frame accounting, runtime, and DQ maps before any
default policy change.

## Clean-Room Compliance

Compliant. This gate consumes GLASS JSON artifacts only. No proprietary
implementation source was read, copied, summarized, or reworked.
