from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations

import numpy as np

from glass.cpu.star_detect import Star


@dataclass(slots=True)
class StarRegistration:
    transform_model: str
    matrix: list[list[float]]
    matched_stars: int
    inliers: int
    rms_px: float
    status: str
    warnings: list[str]
    pairs: list[tuple[int, int]]


def estimate_translation(reference: list[Star], moving: list[Star]) -> tuple[float, float]:
    if not reference or not moving:
        raise ValueError("cannot estimate translation without stars")
    n = min(len(reference), len(moving), 30)
    ref = np.array([(s.x, s.y) for s in reference[:n]], dtype=np.float32)
    mov = np.array([(s.x, s.y) for s in moving[:n]], dtype=np.float32)
    delta = np.median(ref - mov, axis=0)
    return float(delta[0]), float(delta[1])


def translation_matrix(dx: float, dy: float) -> list[list[float]]:
    return [[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]]


def _points(stars: list[Star], max_stars: int) -> np.ndarray:
    selected = stars[: max(0, int(max_stars))]
    return np.asarray([(star.x, star.y) for star in selected], dtype=np.float64)


def _matrix_to_list(matrix: np.ndarray) -> list[list[float]]:
    return [[float(value) for value in row] for row in matrix]


def _apply_matrix(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    ones = np.ones((points.shape[0], 1), dtype=np.float64)
    homogeneous = np.hstack([points, ones])
    transformed = homogeneous @ matrix.T
    w = transformed[:, 2:3]
    return np.divide(transformed[:, :2], w, out=transformed[:, :2].copy(), where=np.abs(w) > 1.0e-12)


def estimate_astroalign_transform(
    reference_image: np.ndarray,
    moving_image: np.ndarray,
    max_control_points: int = 50,
    detection_sigma: float = 5.0,
    min_area: int = 5,
) -> StarRegistration:
    try:
        import astroalign
    except ModuleNotFoundError as exc:
        raise RuntimeError("astroalign registration requires installing glass[align]") from exc

    reference = np.nan_to_num(np.asarray(reference_image, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    moving = np.nan_to_num(np.asarray(moving_image, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    if reference.shape != moving.shape:
        raise ValueError(f"shape mismatch for astroalign registration: {reference.shape} != {moving.shape}")

    transform, matched = astroalign.find_transform(
        moving,
        reference,
        max_control_points=max_control_points,
        detection_sigma=detection_sigma,
        min_area=min_area,
    )
    matrix = np.asarray(transform.params, dtype=np.float64)
    moving_points = np.asarray(matched[0], dtype=np.float64)
    reference_points = np.asarray(matched[1], dtype=np.float64)
    transformed = _apply_matrix(moving_points, matrix)
    residuals = transformed - reference_points
    rms = float(np.sqrt(np.mean(np.sum(residuals * residuals, axis=1)))) if len(residuals) else float("nan")
    matched_count = int(len(moving_points))
    status = "ok" if matched_count > 0 and np.isfinite(rms) else "failed"
    warnings = ["open-source astroalign similarity registration"]
    if status != "ok":
        warnings.append("astroalign did not return matched control points")
    return StarRegistration(
        transform_model="similarity",
        matrix=_matrix_to_list(matrix),
        matched_stars=matched_count,
        inliers=matched_count,
        rms_px=rms,
        status=status,
        warnings=warnings,
        pairs=[],
    )


def _fit_translation_matrix(moving: np.ndarray, reference: np.ndarray) -> np.ndarray:
    delta = np.median(reference - moving, axis=0)
    return np.asarray([[1.0, 0.0, delta[0]], [0.0, 1.0, delta[1]], [0.0, 0.0, 1.0]], dtype=np.float64)


def _fit_affine_matrix(moving: np.ndarray, reference: np.ndarray) -> np.ndarray:
    if len(moving) < 3:
        raise ValueError("affine registration requires at least three matched stars")
    rows = []
    rhs = []
    for (x, y), (rx, ry) in zip(moving, reference, strict=True):
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0])
        rows.append([0.0, 0.0, 0.0, x, y, 1.0])
        rhs.extend([rx, ry])
    params, *_ = np.linalg.lstsq(np.asarray(rows, dtype=np.float64), np.asarray(rhs, dtype=np.float64), rcond=None)
    return np.asarray(
        [[params[0], params[1], params[2]], [params[3], params[4], params[5]], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def _fit_homography_matrix(moving: np.ndarray, reference: np.ndarray) -> np.ndarray:
    if len(moving) < 4:
        raise ValueError("homography registration requires at least four matched stars")
    rows = []
    for (x, y), (rx, ry) in zip(moving, reference, strict=True):
        rows.append([-x, -y, -1.0, 0.0, 0.0, 0.0, rx * x, rx * y, rx])
        rows.append([0.0, 0.0, 0.0, -x, -y, -1.0, ry * x, ry * y, ry])
    _u, _s, vt = np.linalg.svd(np.asarray(rows, dtype=np.float64))
    matrix = vt[-1, :].reshape(3, 3)
    scale = matrix[2, 2]
    if abs(float(scale)) <= 1.0e-12:
        norm = float(np.linalg.norm(matrix))
        if norm <= 1.0e-12:
            raise ValueError("degenerate homography fit")
        return matrix / norm
    return matrix / scale


def _fit_similarity_matrix(moving: np.ndarray, reference: np.ndarray) -> np.ndarray:
    if len(moving) < 2:
        raise ValueError("similarity registration requires at least two matched stars")
    mov_mean = np.mean(moving, axis=0)
    ref_mean = np.mean(reference, axis=0)
    mov_centered = moving - mov_mean
    ref_centered = reference - ref_mean
    variance = float(np.sum(mov_centered * mov_centered))
    if variance <= 1.0e-12:
        raise ValueError("degenerate moving stars for similarity registration")
    covariance = mov_centered.T @ ref_centered
    u, singular_values, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0:
        vt[-1, :] *= -1
        rotation = vt.T @ u.T
    scale = float(np.sum(singular_values) / variance)
    linear = scale * rotation
    translation = ref_mean - mov_mean @ linear.T
    return np.asarray(
        [[linear[0, 0], linear[0, 1], translation[0]], [linear[1, 0], linear[1, 1], translation[1]], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def _fit_model_matrix(transform_model: str, moving: np.ndarray, reference: np.ndarray) -> np.ndarray:
    if transform_model == "translation":
        return _fit_translation_matrix(moving, reference)
    if transform_model == "similarity":
        return _fit_similarity_matrix(moving, reference)
    if transform_model == "affine":
        return _fit_affine_matrix(moving, reference)
    if transform_model == "homography":
        return _fit_homography_matrix(moving, reference)
    raise ValueError(f"unsupported star registration model: {transform_model}")


def _greedy_pairs(
    reference: np.ndarray,
    transformed_moving: np.ndarray,
    tolerance_px: float,
) -> tuple[list[tuple[int, int]], float]:
    if len(reference) == 0 or len(transformed_moving) == 0:
        return [], float("inf")
    deltas = transformed_moving[:, None, :] - reference[None, :, :]
    distances = np.sqrt(np.sum(deltas * deltas, axis=2))
    candidate_indices = np.argwhere(distances <= tolerance_px)
    if candidate_indices.size == 0:
        return [], float("inf")
    candidate_indices = sorted(
        ((int(mov_i), int(ref_i)) for mov_i, ref_i in candidate_indices),
        key=lambda pair: float(distances[pair[0], pair[1]]),
    )
    used_moving: set[int] = set()
    used_reference: set[int] = set()
    pairs: list[tuple[int, int]] = []
    residuals: list[float] = []
    for moving_index, reference_index in candidate_indices:
        if moving_index in used_moving or reference_index in used_reference:
            continue
        used_moving.add(moving_index)
        used_reference.add(reference_index)
        pairs.append((moving_index, reference_index))
        residuals.append(float(distances[moving_index, reference_index]))
    rms = float(np.sqrt(np.mean(np.square(residuals)))) if residuals else float("inf")
    return pairs, rms


def _score_matrix(
    reference: np.ndarray,
    moving: np.ndarray,
    matrix: np.ndarray,
    tolerance_px: float,
) -> tuple[list[tuple[int, int]], float]:
    transformed = _apply_matrix(moving, matrix)
    return _greedy_pairs(reference, transformed, tolerance_px)


def _translation_candidates(reference: np.ndarray, moving: np.ndarray, brightest: int) -> list[np.ndarray]:
    ref = reference[: min(len(reference), brightest)]
    mov = moving[: min(len(moving), brightest)]
    candidates = []
    seen: set[tuple[int, int]] = set()
    for ref_point in ref:
        for moving_point in mov:
            delta = ref_point - moving_point
            key = (int(round(delta[0])), int(round(delta[1])))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                np.asarray([[1.0, 0.0, delta[0]], [0.0, 1.0, delta[1]], [0.0, 0.0, 1.0]], dtype=np.float64)
            )
    return candidates


def _triangle_area(triangle: np.ndarray) -> float:
    edge_a = triangle[1] - triangle[0]
    edge_b = triangle[2] - triangle[0]
    return abs(float(edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0])) * 0.5


def _ordered_triangle_by_sides(
    points: np.ndarray,
    indices: tuple[int, int, int],
) -> tuple[np.ndarray, tuple[int, int, int], np.ndarray]:
    triangle = points[list(indices)]
    pairs = ((0, 1), (1, 2), (2, 0))
    side_lengths = np.asarray([np.linalg.norm(triangle[a] - triangle[b]) for a, b in pairs], dtype=np.float64)
    ordered_lengths = np.sort(side_lengths)
    shortest = float(ordered_lengths[0])
    middle = float(ordered_lengths[1])
    longest = float(ordered_lengths[2])
    if shortest <= 1.0e-6 or middle <= 1.0e-6:
        raise ValueError("degenerate triangle")

    longest_pair = pairs[int(np.argmax(side_lengths))]
    local_indices = set(range(3))
    local_indices.remove(longest_pair[0])
    local_indices.remove(longest_pair[1])
    third = local_indices.pop()
    first, second = longest_pair
    if np.linalg.norm(triangle[first] - triangle[third]) < np.linalg.norm(
        triangle[second] - triangle[third]
    ):
        first, second = second, first

    order = (first, second, third)
    ordered_global = tuple(indices[index] for index in order)
    descriptor = np.asarray([longest / middle, middle / shortest], dtype=np.float64)
    return points[list(ordered_global)], ordered_global, descriptor


def _local_triangle_descriptors(
    points: np.ndarray,
    max_points: int,
    neighbors: int,
    max_descriptors: int,
) -> list[tuple[np.ndarray, tuple[int, int, int], float]]:
    limited = points[: min(len(points), max_points)]
    if len(limited) < 3:
        return []
    neighbor_count = min(len(limited), max(3, int(neighbors)))
    seen: set[tuple[int, int, int]] = set()
    descriptors: list[tuple[np.ndarray, tuple[int, int, int], float]] = []
    for anchor in range(len(limited)):
        distances = np.sqrt(np.sum((limited - limited[anchor]) ** 2, axis=1))
        local_indices = np.argsort(distances, kind="stable")[:neighbor_count]
        for raw_indices in combinations((int(index) for index in local_indices), 3):
            key = tuple(sorted(raw_indices))
            if key in seen:
                continue
            seen.add(key)
            triangle = limited[list(raw_indices)]
            area = _triangle_area(triangle)
            if area < 2.0:
                continue
            try:
                _ordered_triangle, ordered_indices, descriptor = _ordered_triangle_by_sides(limited, raw_indices)
            except ValueError:
                continue
            descriptors.append((descriptor, ordered_indices, area))
    descriptors.sort(key=lambda item: item[2], reverse=True)
    return descriptors[:max_descriptors]


def _triangle_descriptors(points: np.ndarray, max_points: int, max_triangles: int) -> list[tuple[np.ndarray, tuple[int, int, int]]]:
    limited = points[: min(len(points), max_points)]
    triangles: list[tuple[np.ndarray, tuple[int, int, int], float]] = []
    for i, j, k in combinations(range(len(limited)), 3):
        tri = limited[[i, j, k]]
        edge_a = tri[1] - tri[0]
        edge_b = tri[2] - tri[0]
        area = abs(float(edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0])) * 0.5
        if area < 2.0:
            continue
        sides = np.asarray(
            [
                np.linalg.norm(tri[0] - tri[1]),
                np.linalg.norm(tri[1] - tri[2]),
                np.linalg.norm(tri[2] - tri[0]),
            ],
            dtype=np.float64,
        )
        longest = float(np.max(sides))
        if longest <= 1.0e-6:
            continue
        ordered = np.sort(sides)
        descriptor = np.asarray([ordered[0] / longest, ordered[1] / longest], dtype=np.float64)
        triangles.append((descriptor, (i, j, k), area))
    triangles.sort(key=lambda item: item[2], reverse=True)
    return [(descriptor, indices) for descriptor, indices, _area in triangles[:max_triangles]]


def _asterism_candidates(
    reference: np.ndarray,
    moving: np.ndarray,
    transform_model: str,
    descriptor_tolerance: float,
    max_triangles: int,
) -> list[np.ndarray]:
    ref_triangles = _triangle_descriptors(reference, max_points=30, max_triangles=max_triangles)
    moving_triangles = _triangle_descriptors(moving, max_points=30, max_triangles=max_triangles)
    candidates: list[np.ndarray] = []
    for moving_descriptor, moving_indices in moving_triangles:
        for reference_descriptor, reference_indices in ref_triangles:
            if float(np.linalg.norm(moving_descriptor - reference_descriptor)) > descriptor_tolerance:
                continue
            moving_triangle = moving[list(moving_indices)]
            reference_triangle_raw = reference[list(reference_indices)]
            for order in permutations(range(3)):
                reference_triangle = reference_triangle_raw[list(order)]
                try:
                    candidates.append(_fit_model_matrix(transform_model, moving_triangle, reference_triangle))
                except ValueError:
                    continue
            if len(candidates) >= max_triangles:
                return candidates
    return candidates


def estimate_triangle_asterism_transform(
    reference: list[Star],
    moving: list[Star],
    transform_model: str = "similarity",
    min_inliers: int = 6,
    tolerance_px: float = 3.0,
    max_stars: int = 80,
    neighbors: int = 5,
    descriptor_radius: float = 0.1,
    max_descriptors: int = 1200,
    max_candidates: int = 1500,
) -> StarRegistration:
    if transform_model not in {"similarity", "affine"}:
        raise ValueError("triangle asterism registration supports similarity or affine transforms")
    reference_points = _points(reference, max_stars)
    moving_points = _points(moving, max_stars)
    warnings: list[str] = []
    minimum_points = 3
    if len(reference_points) < minimum_points or len(moving_points) < minimum_points:
        return StarRegistration(
            transform_model=transform_model,
            matrix=translation_matrix(0.0, 0.0),
            matched_stars=0,
            inliers=0,
            rms_px=float("nan"),
            status="failed",
            warnings=[f"not enough stars for {transform_model} triangle asterism registration"],
            pairs=[],
        )

    reference_descriptors = _local_triangle_descriptors(reference_points, max_stars, neighbors, max_descriptors)
    moving_descriptors = _local_triangle_descriptors(moving_points, max_stars, neighbors, max_descriptors)
    warnings.extend(
        [
            f"triangle_asterism_reference_descriptors={len(reference_descriptors)}",
            f"triangle_asterism_moving_descriptors={len(moving_descriptors)}",
            f"triangle_asterism_neighbors={neighbors}",
        ]
    )
    if not reference_descriptors or not moving_descriptors:
        return StarRegistration(
            transform_model=transform_model,
            matrix=translation_matrix(0.0, 0.0),
            matched_stars=0,
            inliers=0,
            rms_px=float("nan"),
            status="failed",
            warnings=warnings + ["no nondegenerate local triangle descriptors"],
            pairs=[],
        )

    descriptor_matches: list[tuple[float, tuple[int, int, int], tuple[int, int, int]]] = []
    reference_vectors = np.asarray([item[0] for item in reference_descriptors], dtype=np.float64)
    for moving_descriptor, moving_indices, _moving_area in moving_descriptors:
        distances = np.sqrt(np.sum((reference_vectors - moving_descriptor) ** 2, axis=1))
        matched_indices = np.nonzero(distances <= descriptor_radius)[0]
        for reference_descriptor_index in matched_indices:
            _reference_descriptor, reference_indices, _reference_area = reference_descriptors[
                int(reference_descriptor_index)
            ]
            descriptor_matches.append(
                (float(distances[int(reference_descriptor_index)]), moving_indices, reference_indices)
            )
    descriptor_matches.sort(key=lambda item: item[0])
    descriptor_matches = descriptor_matches[:max_candidates]
    warnings.append(f"triangle_asterism_descriptor_matches={len(descriptor_matches)}")

    best_matrix = np.eye(3, dtype=np.float64)
    best_pairs: list[tuple[int, int]] = []
    best_rms = float("inf")
    for _descriptor_distance, moving_indices, reference_indices in descriptor_matches:
        moving_triangle = moving_points[list(moving_indices)]
        reference_triangle = reference_points[list(reference_indices)]
        reference_orders = (reference_triangle, reference_triangle[[1, 0, 2]])
        for ordered_reference_triangle in reference_orders:
            try:
                matrix = _fit_model_matrix(transform_model, moving_triangle, ordered_reference_triangle)
            except ValueError:
                continue
            pairs, rms = _score_matrix(reference_points, moving_points, matrix, tolerance_px)
            if len(pairs) > len(best_pairs) or (len(pairs) == len(best_pairs) and rms < best_rms):
                best_matrix = matrix
                best_pairs = pairs
                best_rms = rms

    for _iteration in range(3):
        if len(best_pairs) < minimum_points:
            break
        moving_fit = moving_points[[pair[0] for pair in best_pairs]]
        reference_fit = reference_points[[pair[1] for pair in best_pairs]]
        try:
            refined = _fit_model_matrix(transform_model, moving_fit, reference_fit)
        except ValueError:
            break
        pairs, rms = _score_matrix(reference_points, moving_points, refined, tolerance_px)
        if len(pairs) > len(best_pairs) or (len(pairs) == len(best_pairs) and rms <= best_rms):
            best_matrix = refined
            best_pairs = pairs
            best_rms = rms

    status = "ok" if len(best_pairs) >= min_inliers else "failed"
    if status != "ok":
        warnings.append(f"registration has {len(best_pairs)} inliers, below min_inliers={min_inliers}")
    return StarRegistration(
        transform_model=transform_model,
        matrix=_matrix_to_list(best_matrix),
        matched_stars=len(best_pairs),
        inliers=len(best_pairs),
        rms_px=float(best_rms) if np.isfinite(best_rms) else float("nan"),
        status=status,
        warnings=warnings,
        pairs=best_pairs,
    )


def estimate_star_transform(
    reference: list[Star],
    moving: list[Star],
    transform_model: str = "translation",
    min_inliers: int = 6,
    tolerance_px: float = 3.0,
    max_stars: int = 80,
) -> StarRegistration:
    reference_points = _points(reference, max_stars)
    moving_points = _points(moving, max_stars)
    warnings: list[str] = []
    minimum_points = (
        4
        if transform_model == "homography"
        else 3
        if transform_model == "affine"
        else 2
        if transform_model == "similarity"
        else 1
    )
    if len(reference_points) < minimum_points or len(moving_points) < minimum_points:
        return StarRegistration(
            transform_model=transform_model,
            matrix=translation_matrix(0.0, 0.0),
            matched_stars=0,
            inliers=0,
            rms_px=float("nan"),
            status="failed",
            warnings=[f"not enough stars for {transform_model} registration"],
            pairs=[],
        )

    candidates = _translation_candidates(reference_points, moving_points, brightest=35)
    if transform_model in {"similarity", "affine"}:
        candidates = _asterism_candidates(
            reference_points,
            moving_points,
            transform_model,
            descriptor_tolerance=0.025,
            max_triangles=600,
        ) + candidates
    elif transform_model == "homography":
        warnings.append("homography model uses affine/translation hypotheses before homography refit")
        candidates = _asterism_candidates(
            reference_points,
            moving_points,
            "affine",
            descriptor_tolerance=0.025,
            max_triangles=600,
        ) + candidates
    if not candidates:
        candidates = [np.eye(3, dtype=np.float64)]

    best_matrix = candidates[0]
    best_pairs: list[tuple[int, int]] = []
    best_rms = float("inf")
    for matrix in candidates:
        pairs, rms = _score_matrix(reference_points, moving_points, matrix, tolerance_px)
        if len(pairs) > len(best_pairs) or (len(pairs) == len(best_pairs) and rms < best_rms):
            best_matrix = matrix
            best_pairs = pairs
            best_rms = rms

    for _ in range(2):
        if len(best_pairs) < minimum_points:
            break
        moving_fit = moving_points[[pair[0] for pair in best_pairs]]
        reference_fit = reference_points[[pair[1] for pair in best_pairs]]
        try:
            refined = _fit_model_matrix(transform_model, moving_fit, reference_fit)
        except ValueError:
            break
        pairs, rms = _score_matrix(reference_points, moving_points, refined, tolerance_px)
        if len(pairs) > len(best_pairs) or (len(pairs) == len(best_pairs) and rms <= best_rms):
            best_matrix = refined
            best_pairs = pairs
            best_rms = rms

    status = "ok" if len(best_pairs) >= min_inliers else "failed"
    if status != "ok":
        warnings.append(f"registration has {len(best_pairs)} inliers, below min_inliers={min_inliers}")
    return StarRegistration(
        transform_model=transform_model,
        matrix=_matrix_to_list(best_matrix),
        matched_stars=len(best_pairs),
        inliers=len(best_pairs),
        rms_px=float(best_rms) if np.isfinite(best_rms) else float("nan"),
        status=status,
        warnings=warnings,
        pairs=best_pairs,
    )


def estimate_translation_phase_correlation(reference: np.ndarray, moving: np.ndarray) -> tuple[float, float]:
    ref = np.asarray(reference, dtype=np.float32)
    mov = np.asarray(moving, dtype=np.float32)
    if ref.shape != mov.shape:
        raise ValueError(f"shape mismatch for registration: {ref.shape} != {mov.shape}")
    ref = ref - float(np.mean(ref))
    mov = mov - float(np.mean(mov))
    cross_power = np.fft.fft2(ref) * np.conj(np.fft.fft2(mov))
    denom = np.abs(cross_power)
    cross_power = np.divide(cross_power, denom, out=np.zeros_like(cross_power), where=denom > 0)
    corr = np.fft.ifft2(cross_power)
    y, x = np.unravel_index(np.argmax(np.abs(corr)), corr.shape)
    height, width = ref.shape
    if x > width // 2:
        x -= width
    if y > height // 2:
        y -= height
    return float(x), float(y)
