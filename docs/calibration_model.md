# Calibration Model

This document records the independent calibration semantics used by GPWBPP.

Master bias is the mean or median of bias frames. Gate 2 uses mean stacking as a
CPU baseline.

Master dark records its exposure and whether it includes bias. If a master dark
is made directly from raw dark frames, `master_dark_includes_bias=true`. If the
dark frames are bias-subtracted before stacking, `master_dark_includes_bias=false`.
This flag changes the light calibration formula and is always exposed in plan,
state, and report artifacts.

Master flat is calibrated by subtracting either bias or flat-dark data, then
normalizing by median or mean. A `flat_floor` avoids division by zero.

Light calibration:

```text
scaled_dark = master_dark * light_exposure_s / dark_exposure_s
```

When `master_dark_includes_bias=true`:

```text
calibrated = (light - scaled_dark) / normalized_flat
```

When `master_dark_includes_bias=false`:

```text
calibrated = (light - master_bias - scaled_dark) / normalized_flat
```

Dark scaling is controlled by policy and can be disabled. Pedestal is applied
after flat division.

