from __future__ import annotations

import numpy as np

from gpwbpp.cpu.star_detect import detect_stars
from gpwbpp.synthetic.generator import render_star_field


def test_cpu_star_detection_finds_synthetic_stars():
    stars = np.array([[16.0, 16.0, 1000.0], [8.0, 20.0, 800.0]], dtype=np.float32)
    image = render_star_field(32, 32, stars)
    detected = detect_stars(image, threshold_sigma=3.0)
    assert len(detected) >= 2
    assert abs(detected[0].x - 16.0) < 1.0
    assert abs(detected[0].y - 16.0) < 1.0

