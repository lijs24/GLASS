from __future__ import annotations

import numpy as np


def warp_translation(data: np.ndarray, dx: float, dy: float, fill: float = 0.0) -> np.ndarray:
    image = np.asarray(data, dtype=np.float32)
    h, w = image.shape
    out = np.full_like(image, fill, dtype=np.float32)
    ix = int(round(dx))
    iy = int(round(dy))
    src_x0 = max(0, -ix)
    src_x1 = min(w, w - ix)
    dst_x0 = max(0, ix)
    dst_x1 = min(w, w + ix)
    src_y0 = max(0, -iy)
    src_y1 = min(h, h - iy)
    dst_y0 = max(0, iy)
    dst_y1 = min(h, h + iy)
    if src_x0 < src_x1 and src_y0 < src_y1:
        out[dst_y0:dst_y1, dst_x0:dst_x1] = image[src_y0:src_y1, src_x0:src_x1]
    return out

