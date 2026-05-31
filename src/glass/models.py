from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from typing import Any, Literal


FrameType = Literal["bias", "dark", "flat", "light", "unknown"]


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {k: to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


@dataclass(slots=True)
class FrameRecord:
    id: str
    path: str
    file_format: str
    frame_type: FrameType = "unknown"
    filter: str | None = None
    exposure_s: float | None = None
    gain: float | None = None
    offset: float | None = None
    temperature_c: float | None = None
    binning_x: int | None = None
    binning_y: int | None = None
    width: int | None = None
    height: int | None = None
    camera: str | None = None
    date_obs: str | None = None
    object_name: str | None = None
    ra: str | float | None = None
    dec: str | float | None = None
    header_summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    checksum_optional: str | None = None


@dataclass(slots=True)
class FrameGroup:
    group_id: str
    group_type: str
    filter: str | None
    exposure_s: float | None
    gain: float | None
    offset: float | None
    temperature_c: float | None
    binning: tuple[int | None, int | None]
    shape: tuple[int | None, int | None]
    frames: list[str]
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CalibrationPolicy:
    master_dark_includes_bias: bool = True
    dark_scaling_enabled: bool = True
    flat_normalization: str = "median"
    flat_floor: float = 1.0e-6
    overscan_enabled: bool = False
    overscan_columns: int = 0
    overscan_rows: int = 0
    trim_overscan: bool = True
    pedestal: float = 0.0
    master_rejection: str = "winsorized_sigma"
    master_rejection_low_sigma: float = 3.0
    master_rejection_high_sigma: float = 3.0
    master_rejection_iterations: int = 1
    master_rejection_min_samples: int = 3
    master_rejection_max_fraction: float = 0.5
    cosmetic_correction_enabled: bool = False
    cosmetic_hot_sigma: float = 8.0
    cosmetic_cold_sigma: float = 8.0
    saturation_level: float | None = None


@dataclass(slots=True)
class CalibrationPlan:
    master_bias_groups: list[str] = field(default_factory=list)
    master_dark_groups: list[str] = field(default_factory=list)
    master_flat_groups: list[str] = field(default_factory=list)
    dark_scaling_policy: str = "scale_by_exposure_when_enabled"
    bias_dark_semantics_warning: str | None = None
    calibration_policy: CalibrationPolicy = field(default_factory=CalibrationPolicy)


@dataclass(slots=True)
class RegistrationPolicy:
    reference_mode: str = "auto"
    transform_model: str = "translation"
    min_stars: int = 8
    min_inliers: int = 6
    max_rms_px: float = 2.0
    save_registered: bool = False
    reject_failed_frames: bool = True


@dataclass(slots=True)
class LocalNormalizationPolicy:
    enabled: bool = False
    reference_mode: str = "registration_reference"
    tile_radius: int = 64
    background_mask_policy: str = "sigma"
    outlier_policy: str = "clip"


@dataclass(slots=True)
class IntegrationPolicy:
    combine: str = "mean"
    weighting: str = "none"
    rejection: str = "none"
    iterations: int = 1
    low_sigma: float = 3.0
    high_sigma: float = 3.0
    output_weight_map: bool = True
    output_rejection_maps: bool = True
    output_coverage_map: bool = True


@dataclass(slots=True)
class LightPlan:
    filter: str | None
    frames: list[str]
    matching_bias_group: str | None
    matching_dark_group: str | None
    matching_flat_group: str | None
    calibration_status: str
    registration_status: str = "pending"
    local_normalization_status: str = "pending"
    integration_status: str = "pending"
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProcessingPlan:
    project_id: str
    created_at: str
    manifest_path: str
    frames: list[FrameRecord]
    groups: list[FrameGroup]
    calibration_plan: CalibrationPlan
    registration_policy: RegistrationPolicy
    local_normalization_policy: LocalNormalizationPolicy
    integration_policy: IntegrationPolicy
    light_plans: list[LightPlan]
    global_warnings: list[str] = field(default_factory=list)
    executable: bool = False
    next_steps: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FrameQuality:
    frame_id: str
    filter: str | None
    background_median: float
    background_rms: float
    star_count: int
    fwhm_px: float | None
    eccentricity: float | None
    snr: float
    weight: float
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RegistrationResult:
    frame_id: str
    reference_frame_id: str
    transform_model: str
    matrix: list[list[float]]
    matched_stars: int
    inliers: int
    rms_px: float
    status: str
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PipelineArtifact:
    stage: str
    path: str
    format: str
    created_at: str
    source_frames: list[str]
    checksum_optional: str | None = None


@dataclass(slots=True)
class RunState:
    run_id: str
    created_at: str
    current_stage: str
    completed_stages: list[str] = field(default_factory=list)
    failed_stage: str | None = None
    artifacts: list[PipelineArtifact] = field(default_factory=list)
    checksums: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    resume_supported: bool = True
