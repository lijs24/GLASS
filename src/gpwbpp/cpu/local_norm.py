from __future__ import annotations

import numpy as np


def match_global_background(data: np.ndarray, reference: np.ndarray) -> np.ndarray:
    src = np.asarray(data, dtype=np.float32)
    ref = np.asarray(reference, dtype=np.float32)
    src_std = float(np.std(src)) or 1.0
    return ((src - float(np.median(src))) / src_std * float(np.std(ref)) + float(np.median(ref))).astype(
        np.float32
    )

