from __future__ import annotations

from gpwbpp.cpu.registration import estimate_translation
from gpwbpp.cpu.star_detect import Star


def test_estimate_translation_from_star_lists():
    reference = [Star(10, 10, 100), Star(20, 20, 90), Star(30, 12, 80)]
    moving = [Star(8, 13, 100), Star(18, 23, 90), Star(28, 15, 80)]
    dx, dy = estimate_translation(reference, moving)
    assert dx == 2.0
    assert dy == -3.0

