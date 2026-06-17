# S2-Gate 191 Status: Labeled CPU Portable Package Smoke

## Gate

- Gate: S2-Gate 191
- Scope: build and smoke-test the labeled Windows CPU fallback portable package.
- Status: green
- Date: 2026-06-17

## Completed

- Built `GLASS-Portable-win64-cpu.zip`.
- Used package label: `cpu`.
- Package manifest records `build_cuda=false`.
- Ran package smoke with `--expected-package-label cpu` and
  `--expected-source a1604b0`.
- CUDA was not required for this smoke test.

## Commands Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cpu
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cpu.zip --expected-source a1604b0 --expected-package-label cpu --out C:\glass_runs\phase2_s2_gate_191_cpu_package_smoke\cpu_portable_smoke.json --markdown C:\glass_runs\phase2_s2_gate_191_cpu_package_smoke\cpu_portable_smoke.md --fail-on-failure
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cpu.zip --expected-source a1604b0 --expected-package-label cpu --out runs\checkpoints\s2_gate_191_cpu_portable_smoke.json --markdown runs\checkpoints\s2_gate_191_cpu_portable_smoke.md --fail-on-failure
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Package Result

- Full ruff: passed.
- Full pytest: `464 passed in 26.78s`.
- Status: `package_smoke_passed`.
- Recommendation: `portable_package_ready_for_next_release_step`.
- Zip: `.release\windows\GLASS-Portable-win64-cpu.zip`.
- Zip size: `296215418` bytes.
- Source stamp: `a1604b0`.
- Package label: `cpu`.
- CUDA build flag: `false`.

## Artifacts

- External smoke JSON:
  `C:\glass_runs\phase2_s2_gate_191_cpu_package_smoke\cpu_portable_smoke.json`
- External smoke Markdown:
  `C:\glass_runs\phase2_s2_gate_191_cpu_package_smoke\cpu_portable_smoke.md`
- Checkpoint smoke JSON:
  `runs\checkpoints\s2_gate_191_cpu_portable_smoke.json`
- Checkpoint smoke Markdown:
  `runs\checkpoints\s2_gate_191_cpu_portable_smoke.md`

## Known Limitations

- The package is not signed and no installer was produced.
- The package source stamp is `a1604b0`; formal release artifacts should be
  rebuilt after final release commits/tags if exact source-stamp matching is
  required.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS package artifacts and GLASS doctor output.
- No input image directory was modified.

## Next Step

- Generate a single package-suite readiness artifact covering `cuda13`,
  `cuda12`, `cuda11`, and `cpu` smoke outputs.
