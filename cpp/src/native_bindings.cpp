#include <cuda_runtime.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <cmath>
#include <limits>
#include <algorithm>
#include <array>
#include <utility>
#include <chrono>
#include <cstring>
#include <memory>

namespace py = pybind11;

struct CudaFloatFree {
  void operator()(float* ptr) const noexcept {
    if (ptr != nullptr) {
      (void)cudaFree(ptr);
    }
  }
};

struct CudaUCharFree {
  void operator()(unsigned char* ptr) const noexcept {
    if (ptr != nullptr) {
      (void)cudaFree(ptr);
    }
  }
};

struct CudaUllFree {
  void operator()(unsigned long long* ptr) const noexcept {
    if (ptr != nullptr) {
      (void)cudaFree(ptr);
    }
  }
};

void glass_smoke_add_f32_launch(const float* a, const float* b, float* out, std::size_t n);
void glass_calibrate_tile_f32_launch(
    const float* light,
    const float* bias,
    const float* dark,
    const float* flat,
    float* out,
    std::size_t n,
    bool has_bias,
    bool has_dark,
    bool has_flat,
    bool master_dark_includes_bias,
    float dark_scale,
    float flat_floor,
    float pedestal);
void glass_calibrate_tile_f32_launch_stream(
    const float* light,
    const float* bias,
    const float* dark,
    const float* flat,
    float* out,
    std::size_t n,
    bool has_bias,
    bool has_dark,
    bool has_flat,
    bool master_dark_includes_bias,
    float dark_scale,
    float flat_floor,
    float pedestal,
    cudaStream_t stream);
void glass_mean_stack_tiles_f32_launch(
    const float* stack, float* out, std::size_t frame_count, std::size_t pixels_per_frame);
void glass_warp_translation_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    int dx,
    int dy,
    float fill,
    float* coverage_accumulator);
void glass_warp_translation_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    float dx,
    float dy,
    float fill,
    float* coverage_accumulator);
void glass_warp_matrix_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill,
    float* coverage_accumulator);
void glass_warp_matrix_lanczos3_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill,
    float clamping_threshold,
    float* coverage_accumulator);
void glass_warp_matrix_bilinear_batch_f32_launch(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill);
void glass_warp_matrix_lanczos3_batch_f32_launch(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill,
    float clamping_threshold);
void glass_warp_batch_coverage_reduce_f32_launch(
    const unsigned char* batch_coverage,
    float* coverage_accumulator,
    int frame_count,
    std::size_t pixels_per_frame);
void glass_warp_batch_scatter_f32_launch(
    const float* batch_output,
    float* stack,
    const unsigned long long* frame_indices,
    int frame_count,
    std::size_t pixels_per_frame);
void glass_coverage_accumulate_f32_launch(const float* coverage, float* accumulator, std::size_t n);
void glass_coverage_accumulate_full_f32_launch(float* accumulator, std::size_t n);
void glass_matrix_alignment_metrics_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverse,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int blocks);
void glass_matrix_alignment_metrics_candidates_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverses,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int candidate_count);
void glass_matrix_alignment_metrics_batch_candidates_f32_launch(
    const float* reference,
    const float* stack,
    const int* moving_frame_indices,
    unsigned long long pixels_per_frame,
    const float* inverses,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int candidate_count);
void glass_star_core_metrics_candidates_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverses,
    float threshold,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int candidate_count);
void glass_estimate_translation_search_f32_launch(
    const float* reference,
    const float* moving,
    float* scores,
    int* best_dx,
    int* best_dy,
    float* best_score,
    int width,
    int height,
    int max_shift_x,
    int max_shift_y,
    int sample_stride);
void glass_estimate_translation_subpixel_ncc_f32_launch(
    const float* reference,
    const float* moving,
    float* scores,
    float* best_dx,
    float* best_dy,
    float* best_score,
    int width,
    int height,
    float center_dx,
    float center_dy,
    int radius_steps,
    float step,
    int sample_stride);
void glass_estimate_translation_from_catalogs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_dx,
    float* candidate_dy,
    int* scores,
    float* best_dx,
    float* best_dy,
    int* best_inliers,
    int* moving_best_reference,
    int* reference_best_moving,
    float* refine_sums,
    int* mutual_inliers,
    float* refined_dx,
    float* refined_dy,
    float* rms_px,
    int reference_count,
    int moving_count,
    float tolerance_px,
    float max_abs_dx,
    float max_abs_dy,
    float prior_dx,
    float prior_dy,
    float prior_radius_px);
void glass_triangle_asterism_descriptors_f32_launch(
    const float* x,
    const float* y,
    float* descriptors,
    int* indices,
    float* areas,
    unsigned char* valid,
    int count,
    int neighbors,
    int raw_count);
void glass_estimate_similarity_from_triangle_descriptors_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const float* reference_descriptors,
    const int* reference_indices,
    const float* moving_descriptors,
    const int* moving_indices,
    float* candidate_params,
    int* candidate_scores,
    float* candidate_rms,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* best_inliers,
    int* best_index,
    int reference_count,
    int moving_count,
    int reference_descriptor_count,
    int moving_descriptor_count,
    int candidate_count,
    float tolerance_px,
    float descriptor_radius);
void glass_estimate_similarity_from_pairs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* valid_count,
    int* status,
    double* partial_sums,
    unsigned long long* partial_count,
    double* partial_residual_sums,
    int count,
    int blocks);
void glass_estimate_similarity_from_catalogs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_params,
    int* candidate_scores,
    float* candidate_rms,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* best_inliers,
    int* best_index,
    int* refit_inliers,
    int* refit_status,
    float* refit_matrix,
    float* refit_scale,
    float* refit_rotation_rad,
    float* refit_rms_px,
    double* refit_partial_sums,
    unsigned long long* refit_partial_count,
    double* refit_partial_residual_sums,
    int refit_blocks,
    int reference_count,
    int moving_count,
    int candidate_count,
    float tolerance_px,
    float min_pair_distance,
    float prior_dx,
    float prior_dy,
    float prior_radius_px,
    float min_scale,
    float max_scale,
    float max_abs_rotation_rad);
void glass_local_norm_apply_f32_launch(
    const float* input, float* output, std::size_t n, float scale, float offset);
void glass_local_norm_apply_grid_f32_launch(
    const float* input,
    float* output,
    const float* scales,
    const float* offsets,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows);
void glass_frame_sum_stats_f32_launch(
    const float* input,
    double* partial_sum,
    double* partial_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks);
void glass_pair_sum_stats_f32_launch(
    const float* source,
    const float* reference,
    double* partial_source_sum,
    double* partial_source_sum2,
    double* partial_reference_sum,
    double* partial_reference_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks);
void glass_pair_grid_sum_stats_f32_launch(
    const float* source,
    const float* reference,
    double* source_sum,
    double* source_sum2,
    double* reference_sum,
    double* reference_sum2,
    unsigned long long* count,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows);
void glass_integrate_accumulate_mean_tile_f32_launch(
    const float* frame, const float* weight, float* sum, float* weight_sum, std::size_t n);
void glass_integrate_resident_weighted_mean_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame);
void glass_integrate_resident_sigma_clip_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    bool winsorize);
void glass_integrate_matrix_warped_mean_f32_launch(
    const float* stack,
    const float* weights,
    const float* inverses,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* geometric_coverage_map,
    std::size_t frame_count,
    int width,
    int height,
    int interpolation,
    float clamping_threshold);
void glass_star_local_max_mask_f32_launch(
    const float* input,
    unsigned char* mask,
    int width,
    int height,
    float threshold);
void glass_star_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int width,
    int height,
    float threshold,
    int max_candidates);
void glass_star_top_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int* lock,
    int width,
    int height,
    float threshold,
    int max_candidates);
void glass_star_top_nms_candidates_f32_launch(
    const float* input,
    float* scan_xs,
    float* scan_ys,
    float* scan_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* lock,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int scan_candidates,
    int max_output_candidates,
    float min_separation_px);
void glass_star_grid_top_nms_candidates_f32_launch(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* locks,
    int* cell_counts,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px);
void glass_star_grid_top_nms_candidates_deterministic_f32_launch(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px);
void glass_star_grid_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int* locks,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows);

namespace {

void check_cuda(cudaError_t status, const char* operation) {
  if (status == cudaSuccess) {
    return;
  }
  std::ostringstream message;
  message << operation << " failed: " << cudaGetErrorString(status);
  throw std::runtime_error(message.str());
}

std::size_t element_count(const py::buffer_info& info) {
  std::size_t n = 1;
  for (const auto dim : info.shape) {
    n *= static_cast<std::size_t>(dim);
  }
  return n;
}

void require_same_shape(const py::buffer_info& a, const py::buffer_info& b) {
  if (a.shape != b.shape) {
    throw std::invalid_argument("input arrays must have the same shape");
  }
}

bool dict_bool(const py::dict& dict, const char* key, bool fallback) {
  if (!dict.contains(key)) {
    return fallback;
  }
  return py::cast<bool>(dict[key]);
}

float dict_float(const py::dict& dict, const char* key, float fallback) {
  if (!dict.contains(key)) {
    return fallback;
  }
  return py::cast<float>(dict[key]);
}

using Clock = std::chrono::steady_clock;

double seconds_since(const Clock::time_point& start) {
  return std::chrono::duration<double>(Clock::now() - start).count();
}

const char* grid_catalog_sort_mode(int grid_capacity) {
  return grid_capacity <= 4096 ? "shared_bitonic_power2" : "single_thread_selection";
}

const char* grid_catalog_topk_mode(bool deterministic = false, int candidates_per_cell = 0) {
  if (!deterministic) {
    return "strict_flux_precheck_per_cell_lock";
  }
  return candidates_per_cell <= 16 ? "deterministic_parallel_per_cell" : "deterministic_serial_per_cell";
}

struct CalibrationParameters {
  bool master_dark_includes_bias = true;
  bool dark_scaling_enabled = true;
  float flat_floor = 1.0e-6f;
  float pedestal = 0.0f;
  float dark_scale = 1.0f;
};

struct ResidentCalibrationTiming {
  double host_copy_s = 0.0;
  double h2d_s = 0.0;
  double calibrate_store_s = 0.0;
  double total_s = 0.0;
};

class CudaEvent {
 public:
  explicit CudaEvent(const char* operation) {
    check_cuda(cudaEventCreate(&event_), operation);
  }

  CudaEvent(const CudaEvent&) = delete;
  CudaEvent& operator=(const CudaEvent&) = delete;

  ~CudaEvent() {
    if (event_ != nullptr) {
      cudaEventDestroy(event_);
    }
  }

  cudaEvent_t get() const { return event_; }

 private:
  cudaEvent_t event_ = nullptr;
};

double cuda_event_elapsed_s(const CudaEvent& start, const CudaEvent& stop, const char* operation) {
  float elapsed_ms = 0.0f;
  check_cuda(cudaEventElapsedTime(&elapsed_ms, start.get(), stop.get()), operation);
  return static_cast<double>(elapsed_ms) / 1000.0;
}

double cuda_event_elapsed_s(cudaEvent_t start, cudaEvent_t stop, const char* operation) {
  float elapsed_ms = 0.0f;
  check_cuda(cudaEventElapsedTime(&elapsed_ms, start, stop), operation);
  return static_cast<double>(elapsed_ms) / 1000.0;
}

void require_frame_shape(const py::buffer_info& info, std::size_t height, std::size_t width) {
  if (info.ndim != 2) {
    throw std::invalid_argument("frame must have shape (height, width)");
  }
  if (static_cast<std::size_t>(info.shape[0]) != height ||
      static_cast<std::size_t>(info.shape[1]) != width) {
      throw std::invalid_argument("frame shape does not match the resident stack");
  }
}

std::array<float, 9> parse_matrix3x3(py::object matrix_obj) {
  auto matrix = py::array_t<float, py::array::c_style | py::array::forcecast>::ensure(matrix_obj);
  if (!matrix) {
    throw std::invalid_argument("matrix must be convertible to a float32 array");
  }
  const py::buffer_info info = matrix.request();
  if (info.ndim != 2 || info.shape[0] != 3 || info.shape[1] != 3) {
    throw std::invalid_argument("matrix must have shape (3, 3)");
  }
  const auto* values = static_cast<const float*>(info.ptr);
  std::array<float, 9> out{};
  for (std::size_t i = 0; i < out.size(); ++i) {
    out[i] = values[i];
  }
  return out;
}

py::list matrix3x3_to_pylist(const std::array<float, 9>& matrix) {
  py::list rows;
  for (int row = 0; row < 3; ++row) {
    py::list values;
    for (int col = 0; col < 3; ++col) {
      values.append(matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    rows.append(values);
  }
  return rows;
}

std::vector<std::array<float, 9>> parse_matrix_stack(py::object matrices_obj) {
  auto matrices = py::array_t<float, py::array::c_style | py::array::forcecast>::ensure(matrices_obj);
  if (!matrices) {
    throw std::invalid_argument("matrices must be convertible to a float32 array");
  }
  const py::buffer_info info = matrices.request();
  if (info.ndim == 2 && info.shape[0] == 3 && info.shape[1] == 3) {
    return {parse_matrix3x3(matrices)};
  }
  if (info.ndim != 3 || info.shape[1] != 3 || info.shape[2] != 3) {
    throw std::invalid_argument("matrices must have shape (N, 3, 3) or (3, 3)");
  }
  if (info.shape[0] <= 0) {
    throw std::invalid_argument("matrices must contain at least one matrix");
  }
  const auto* values = static_cast<const float*>(info.ptr);
  std::vector<std::array<float, 9>> out(static_cast<std::size_t>(info.shape[0]));
  for (std::size_t matrix_index = 0; matrix_index < out.size(); ++matrix_index) {
    for (std::size_t value_index = 0; value_index < 9; ++value_index) {
      out[matrix_index][value_index] = values[matrix_index * 9 + value_index];
    }
  }
  return out;
}

std::vector<std::size_t> parse_index_sequence(py::object indices_obj, const char* name) {
  auto indices = py::array_t<long long, py::array::c_style | py::array::forcecast>::ensure(indices_obj);
  if (!indices) {
    throw std::invalid_argument(std::string(name) + " must be convertible to an int64 array");
  }
  const py::buffer_info info = indices.request();
  if (info.ndim != 1) {
    throw std::invalid_argument(std::string(name) + " must be one-dimensional");
  }
  const auto* values = static_cast<const long long*>(info.ptr);
  std::vector<std::size_t> out(static_cast<std::size_t>(info.shape[0]));
  for (std::size_t i = 0; i < out.size(); ++i) {
    if (values[i] < 0) {
      throw std::invalid_argument(std::string(name) + " must not contain negative frame indices");
    }
    out[i] = static_cast<std::size_t>(values[i]);
  }
  return out;
}

std::vector<float> parse_float_sequence(py::object values_obj, const char* name) {
  auto values = py::array_t<float, py::array::c_style | py::array::forcecast>::ensure(values_obj);
  if (!values) {
    throw std::invalid_argument(std::string(name) + " must be convertible to a float32 array");
  }
  const py::buffer_info info = values.request();
  if (info.ndim != 1) {
    throw std::invalid_argument(std::string(name) + " must be one-dimensional");
  }
  const auto* ptr = static_cast<const float*>(info.ptr);
  return std::vector<float>(ptr, ptr + static_cast<std::size_t>(info.shape[0]));
}

std::array<float, 9> invert_matrix3x3(const std::array<float, 9>& m) {
  const double a = m[0];
  const double b = m[1];
  const double c = m[2];
  const double d = m[3];
  const double e = m[4];
  const double f = m[5];
  const double g = m[6];
  const double h = m[7];
  const double i = m[8];
  const double c00 = e * i - f * h;
  const double c01 = -(d * i - f * g);
  const double c02 = d * h - e * g;
  const double c10 = -(b * i - c * h);
  const double c11 = a * i - c * g;
  const double c12 = -(a * h - b * g);
  const double c20 = b * f - c * e;
  const double c21 = -(a * f - c * d);
  const double c22 = a * e - b * d;
  const double det = a * c00 + b * c01 + c * c02;
  if (std::abs(det) <= 1.0e-20) {
    throw std::invalid_argument("matrix must be invertible");
  }
  const double inv_det = 1.0 / det;
  return {
      static_cast<float>(c00 * inv_det),
      static_cast<float>(c10 * inv_det),
      static_cast<float>(c20 * inv_det),
      static_cast<float>(c01 * inv_det),
      static_cast<float>(c11 * inv_det),
      static_cast<float>(c21 * inv_det),
      static_cast<float>(c02 * inv_det),
      static_cast<float>(c12 * inv_det),
      static_cast<float>(c22 * inv_det)};
}

struct MatrixCandidateMetrics {
  float dx = 0.0f;
  float dy = 0.0f;
  std::array<float, 9> matrix{};
  unsigned long long valid_pixels = 0ULL;
  int sampled_pixels = 0;
  int sample_stride = 1;
  double rms = std::numeric_limits<double>::quiet_NaN();
  double mean_abs_diff = std::numeric_limits<double>::quiet_NaN();
  double ncc = std::numeric_limits<double>::quiet_NaN();
};

struct MatrixRefineWorkspace {
  float* d_inverses = nullptr;
  double* d_partial_stats = nullptr;
  unsigned long long* d_partial_count = nullptr;
  int* d_moving_frame_indices = nullptr;
  int candidate_capacity = 0;
};

std::size_t matrix_refine_workspace_bytes(int candidate_capacity) {
  if (candidate_capacity <= 0) {
    return 0;
  }
  return static_cast<std::size_t>(candidate_capacity) * 9 * sizeof(float) +
         static_cast<std::size_t>(candidate_capacity) * 7 * sizeof(double) +
         static_cast<std::size_t>(candidate_capacity) * sizeof(unsigned long long) +
         static_cast<std::size_t>(candidate_capacity) * sizeof(int);
}

std::vector<std::pair<float, float>> translation_offsets(
    float center_dx,
    float center_dy,
    float radius,
    float step) {
  if (radius < 0.0f) {
    throw std::invalid_argument("search radius must be non-negative");
  }
  if (step <= 0.0f) {
    throw std::invalid_argument("search step must be positive");
  }
  std::vector<std::pair<float, float>> offsets;
  for (float dx = center_dx - radius; dx <= center_dx + radius + step * 0.5f; dx += step) {
    for (float dy = center_dy - radius; dy <= center_dy + radius + step * 0.5f; dy += step) {
      offsets.emplace_back(dx, dy);
    }
  }
  if (offsets.empty()) {
    offsets.emplace_back(center_dx, center_dy);
  }
  return offsets;
}

MatrixCandidateMetrics metrics_from_sums(
    const std::array<float, 9>& matrix,
    float dx,
    float dy,
    const double* sums,
    unsigned long long valid_pixels,
    int sampled_pixels,
    int sample_stride) {
  MatrixCandidateMetrics metrics;
  metrics.dx = dx;
  metrics.dy = dy;
  metrics.matrix = matrix;
  metrics.valid_pixels = valid_pixels;
  metrics.sampled_pixels = sampled_pixels;
  metrics.sample_stride = sample_stride;
  if (valid_pixels == 0ULL) {
    return metrics;
  }
  const double count = static_cast<double>(valid_pixels);
  metrics.rms = std::sqrt(sums[5] / count);
  metrics.mean_abs_diff = sums[6] / count;
  if (valid_pixels > 1ULL) {
    const double numerator = sums[4] - (sums[0] * sums[1] / count);
    const double ref_var = std::max(sums[2] - (sums[0] * sums[0] / count), 0.0);
    const double mov_var = std::max(sums[3] - (sums[1] * sums[1] / count), 0.0);
    const double denominator = std::sqrt(ref_var * mov_var);
    if (denominator > 0.0) {
      metrics.ncc = numerator / denominator;
    }
  }
  return metrics;
}

bool better_matrix_metric(const MatrixCandidateMetrics& candidate, const MatrixCandidateMetrics& current) {
  const bool candidate_rms_finite = std::isfinite(candidate.rms);
  const bool current_rms_finite = std::isfinite(current.rms);
  if (candidate_rms_finite != current_rms_finite) {
    return candidate_rms_finite;
  }
  if (candidate_rms_finite && std::abs(candidate.rms - current.rms) > 1.0e-12) {
    return candidate.rms < current.rms;
  }
  const bool candidate_ncc_finite = std::isfinite(candidate.ncc);
  const bool current_ncc_finite = std::isfinite(current.ncc);
  if (candidate_ncc_finite != current_ncc_finite) {
    return candidate_ncc_finite;
  }
  if (candidate_ncc_finite && std::abs(candidate.ncc - current.ncc) > 1.0e-12) {
    return candidate.ncc > current.ncc;
  }
  return candidate.valid_pixels > current.valid_pixels;
}

py::dict matrix_candidate_to_dict(const MatrixCandidateMetrics& metrics, const char* model) {
  py::dict result;
  result["valid_pixels"] = metrics.valid_pixels;
  result["sampled_pixels"] = metrics.sampled_pixels;
  result["sample_stride"] = metrics.sample_stride;
  result["rms"] = metrics.rms;
  result["mean_abs_diff"] = metrics.mean_abs_diff;
  result["ncc"] = metrics.ncc;
  result["model"] = model;
  return result;
}

MatrixCandidateMetrics score_matrix_translation_candidates_f32_workspace(
    const float* d_reference,
    const float* d_moving,
    const std::array<float, 9>& base_matrix,
    const std::vector<std::pair<float, float>>& offsets,
    int width,
    int height,
    int sample_stride,
    MatrixRefineWorkspace workspace) {
  if (offsets.empty()) {
    throw std::invalid_argument("candidate offsets must be non-empty");
  }
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sampled_pixels = sample_width * sample_height;
  const int candidate_count = static_cast<int>(offsets.size());
  if (candidate_count > workspace.candidate_capacity ||
      workspace.d_inverses == nullptr ||
      workspace.d_partial_stats == nullptr ||
      workspace.d_partial_count == nullptr) {
    throw std::invalid_argument("matrix refine workspace is smaller than candidate count");
  }

  std::vector<std::array<float, 9>> matrices(offsets.size());
  std::vector<float> inverses(static_cast<std::size_t>(candidate_count) * 9, 0.0f);
  for (int i = 0; i < candidate_count; ++i) {
    auto matrix = base_matrix;
    matrix[2] += offsets[static_cast<std::size_t>(i)].first;
    matrix[5] += offsets[static_cast<std::size_t>(i)].second;
    matrices[static_cast<std::size_t>(i)] = matrix;
    const auto inverse = invert_matrix3x3(matrix);
    std::copy(inverse.begin(), inverse.end(), inverses.begin() + static_cast<std::size_t>(i) * 9);
  }

  std::vector<double> partial_stats(static_cast<std::size_t>(candidate_count) * 7, 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(candidate_count), 0ULL);
  check_cuda(
      cudaMemcpy(workspace.d_inverses, inverses.data(), inverses.size() * sizeof(float), cudaMemcpyHostToDevice),
      "cudaMemcpy(matrix refine candidate inverses)");
  glass_matrix_alignment_metrics_candidates_f32_launch(
      d_reference,
      d_moving,
      workspace.d_inverses,
      workspace.d_partial_stats,
      workspace.d_partial_count,
      width,
      height,
      stride,
      candidate_count);
  check_cuda(cudaGetLastError(), "matrix translation refine candidate kernel launch");
  check_cuda(cudaDeviceSynchronize(), "matrix translation refine candidate synchronize");
  check_cuda(
      cudaMemcpy(
          partial_stats.data(),
          workspace.d_partial_stats,
          partial_stats.size() * sizeof(double),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix refine partial stats)");
  check_cuda(
      cudaMemcpy(
          partial_count.data(),
          workspace.d_partial_count,
          partial_count.size() * sizeof(unsigned long long),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix refine partial count)");

  MatrixCandidateMetrics best;
  bool have_best = false;
  for (int i = 0; i < candidate_count; ++i) {
    const std::size_t offset = static_cast<std::size_t>(i) * 7;
    const auto metrics = metrics_from_sums(
        matrices[static_cast<std::size_t>(i)],
        offsets[static_cast<std::size_t>(i)].first,
        offsets[static_cast<std::size_t>(i)].second,
        partial_stats.data() + offset,
        partial_count[static_cast<std::size_t>(i)],
        sampled_pixels,
        stride);
    if (!have_best || better_matrix_metric(metrics, best)) {
      best = metrics;
      have_best = true;
    }
  }
  return best;
}

MatrixCandidateMetrics score_matrix_translation_candidates_f32(
    const float* d_reference,
    const float* d_moving,
    const std::array<float, 9>& base_matrix,
    const std::vector<std::pair<float, float>>& offsets,
    int width,
    int height,
    int sample_stride) {
  if (offsets.empty()) {
    throw std::invalid_argument("candidate offsets must be non-empty");
  }
  const int candidate_count = static_cast<int>(offsets.size());
  MatrixRefineWorkspace workspace;
  workspace.candidate_capacity = candidate_count;
  try {
    check_cuda(
        cudaMalloc(&workspace.d_inverses, static_cast<std::size_t>(candidate_count) * 9 * sizeof(float)),
        "cudaMalloc(matrix refine candidate inverses)");
    check_cuda(
        cudaMalloc(&workspace.d_partial_stats, static_cast<std::size_t>(candidate_count) * 7 * sizeof(double)),
        "cudaMalloc(matrix refine partial stats)");
    check_cuda(
        cudaMalloc(
            &workspace.d_partial_count,
            static_cast<std::size_t>(candidate_count) * sizeof(unsigned long long)),
        "cudaMalloc(matrix refine partial count)");
    const MatrixCandidateMetrics best = score_matrix_translation_candidates_f32_workspace(
        d_reference, d_moving, base_matrix, offsets, width, height, sample_stride, workspace);
    cudaFree(workspace.d_inverses);
    cudaFree(workspace.d_partial_stats);
    cudaFree(workspace.d_partial_count);
    return best;
  } catch (...) {
    cudaFree(workspace.d_inverses);
    cudaFree(workspace.d_partial_stats);
    cudaFree(workspace.d_partial_count);
    throw;
  }
}

std::vector<MatrixCandidateMetrics> score_matrix_translation_candidates_batch_f32_workspace(
    const float* d_reference,
    const float* d_stack,
    std::size_t pixels_per_frame,
    const std::vector<std::size_t>& moving_indices,
    const std::vector<std::array<float, 9>>& base_matrices,
    const std::vector<std::vector<std::pair<float, float>>>& offsets_by_frame,
    int width,
    int height,
    int sample_stride,
    MatrixRefineWorkspace workspace) {
  if (moving_indices.empty()) {
    return {};
  }
  if (base_matrices.size() != moving_indices.size() || offsets_by_frame.size() != moving_indices.size()) {
    throw std::invalid_argument("batch matrix scoring requires one matrix and offset list per moving frame");
  }
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sampled_pixels = sample_width * sample_height;

  std::vector<int> frame_starts(moving_indices.size(), 0);
  std::vector<int> frame_counts(moving_indices.size(), 0);
  std::size_t total_candidates_size = 0;
  for (std::size_t frame = 0; frame < moving_indices.size(); ++frame) {
    if (offsets_by_frame[frame].empty()) {
      throw std::invalid_argument("candidate offsets must be non-empty");
    }
    if (moving_indices[frame] > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("moving frame index exceeds native batch metric index range");
    }
    total_candidates_size += offsets_by_frame[frame].size();
  }
  if (total_candidates_size > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
    throw std::invalid_argument("too many matrix metric candidates for one native batch");
  }
  const int total_candidates = static_cast<int>(total_candidates_size);
  if (total_candidates > workspace.candidate_capacity ||
      workspace.d_inverses == nullptr ||
      workspace.d_partial_stats == nullptr ||
      workspace.d_partial_count == nullptr ||
      workspace.d_moving_frame_indices == nullptr) {
    throw std::invalid_argument("matrix batch refine workspace is smaller than candidate count");
  }

  std::vector<std::array<float, 9>> matrices(total_candidates_size);
  std::vector<std::pair<float, float>> candidate_offsets(total_candidates_size);
  std::vector<float> inverses(total_candidates_size * 9, 0.0f);
  std::vector<int> moving_frame_indices(total_candidates_size, 0);
  std::size_t cursor = 0;
  for (std::size_t frame = 0; frame < moving_indices.size(); ++frame) {
    frame_starts[frame] = static_cast<int>(cursor);
    frame_counts[frame] = static_cast<int>(offsets_by_frame[frame].size());
    const int moving_index = static_cast<int>(moving_indices[frame]);
    for (const auto& offset : offsets_by_frame[frame]) {
      auto matrix = base_matrices[frame];
      matrix[2] += offset.first;
      matrix[5] += offset.second;
      matrices[cursor] = matrix;
      candidate_offsets[cursor] = offset;
      moving_frame_indices[cursor] = moving_index;
      const auto inverse = invert_matrix3x3(matrix);
      std::copy(inverse.begin(), inverse.end(), inverses.begin() + cursor * 9);
      ++cursor;
    }
  }

  std::vector<double> partial_stats(total_candidates_size * 7, 0.0);
  std::vector<unsigned long long> partial_count(total_candidates_size, 0ULL);
  check_cuda(
      cudaMemcpy(workspace.d_inverses, inverses.data(), inverses.size() * sizeof(float), cudaMemcpyHostToDevice),
      "cudaMemcpy(matrix batch refine candidate inverses)");
  check_cuda(
      cudaMemcpy(
          workspace.d_moving_frame_indices,
          moving_frame_indices.data(),
          moving_frame_indices.size() * sizeof(int),
          cudaMemcpyHostToDevice),
      "cudaMemcpy(matrix batch refine moving frame indices)");
  glass_matrix_alignment_metrics_batch_candidates_f32_launch(
      d_reference,
      d_stack,
      workspace.d_moving_frame_indices,
      static_cast<unsigned long long>(pixels_per_frame),
      workspace.d_inverses,
      workspace.d_partial_stats,
      workspace.d_partial_count,
      width,
      height,
      stride,
      total_candidates);
  check_cuda(cudaGetLastError(), "matrix batch translation refine candidate kernel launch");
  check_cuda(cudaDeviceSynchronize(), "matrix batch translation refine candidate synchronize");
  check_cuda(
      cudaMemcpy(
          partial_stats.data(),
          workspace.d_partial_stats,
          partial_stats.size() * sizeof(double),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix batch refine partial stats)");
  check_cuda(
      cudaMemcpy(
          partial_count.data(),
          workspace.d_partial_count,
          partial_count.size() * sizeof(unsigned long long),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix batch refine partial count)");

  std::vector<MatrixCandidateMetrics> results;
  results.reserve(moving_indices.size());
  for (std::size_t frame = 0; frame < moving_indices.size(); ++frame) {
    MatrixCandidateMetrics best;
    bool have_best = false;
    const int start = frame_starts[frame];
    const int count = frame_counts[frame];
    for (int local = 0; local < count; ++local) {
      const int candidate = start + local;
      const std::size_t candidate_offset = static_cast<std::size_t>(candidate) * 7;
      const auto metrics = metrics_from_sums(
          matrices[static_cast<std::size_t>(candidate)],
          candidate_offsets[static_cast<std::size_t>(candidate)].first,
          candidate_offsets[static_cast<std::size_t>(candidate)].second,
          partial_stats.data() + candidate_offset,
          partial_count[static_cast<std::size_t>(candidate)],
          sampled_pixels,
          stride);
      if (!have_best || better_matrix_metric(metrics, best)) {
        best = metrics;
        have_best = true;
      }
    }
    if (!have_best) {
      throw std::runtime_error("matrix batch refine produced no candidates");
    }
    results.push_back(best);
  }
  return results;
}

std::vector<MatrixCandidateMetrics> score_star_core_matrix_candidates_f32(
    const float* d_reference,
    const float* d_moving,
    const std::vector<std::array<float, 9>>& matrices,
    int width,
    int height,
    float threshold) {
  if (matrices.empty()) {
    throw std::invalid_argument("candidate matrices must be non-empty");
  }
  if (!std::isfinite(threshold)) {
    throw std::invalid_argument("star core threshold must be finite");
  }
  const int candidate_count = static_cast<int>(matrices.size());
  const int sampled_pixels = width * height;

  std::vector<float> inverses(static_cast<std::size_t>(candidate_count) * 9, 0.0f);
  for (int i = 0; i < candidate_count; ++i) {
    const auto inverse = invert_matrix3x3(matrices[static_cast<std::size_t>(i)]);
    std::copy(inverse.begin(), inverse.end(), inverses.begin() + static_cast<std::size_t>(i) * 9);
  }

  std::vector<double> partial_stats(static_cast<std::size_t>(candidate_count) * 7, 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(candidate_count), 0ULL);
  float* d_inverses = nullptr;
  double* d_partial_stats = nullptr;
  unsigned long long* d_partial_count = nullptr;
  try {
    check_cuda(
        cudaMalloc(&d_inverses, inverses.size() * sizeof(float)),
        "cudaMalloc(star core metric inverses)");
    check_cuda(
        cudaMalloc(&d_partial_stats, partial_stats.size() * sizeof(double)),
        "cudaMalloc(star core metric partial stats)");
    check_cuda(
        cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
        "cudaMalloc(star core metric partial count)");
    check_cuda(
        cudaMemcpy(d_inverses, inverses.data(), inverses.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(star core metric inverses)");
    glass_star_core_metrics_candidates_f32_launch(
        d_reference,
        d_moving,
        d_inverses,
        threshold,
        d_partial_stats,
        d_partial_count,
        width,
        height,
        candidate_count);
    check_cuda(cudaGetLastError(), "star core candidate metrics kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star core candidate metrics synchronize");
    check_cuda(
        cudaMemcpy(partial_stats.data(), d_partial_stats, partial_stats.size() * sizeof(double), cudaMemcpyDeviceToHost),
        "cudaMemcpy(star core metric partial stats)");
    check_cuda(
        cudaMemcpy(
            partial_count.data(),
            d_partial_count,
            partial_count.size() * sizeof(unsigned long long),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(star core metric partial count)");
  } catch (...) {
    cudaFree(d_inverses);
    cudaFree(d_partial_stats);
    cudaFree(d_partial_count);
    throw;
  }
  cudaFree(d_inverses);
  cudaFree(d_partial_stats);
  cudaFree(d_partial_count);

  std::vector<MatrixCandidateMetrics> results;
  results.reserve(matrices.size());
  for (int i = 0; i < candidate_count; ++i) {
    const std::size_t offset = static_cast<std::size_t>(i) * 7;
    results.push_back(metrics_from_sums(
        matrices[static_cast<std::size_t>(i)],
        0.0f,
        0.0f,
        partial_stats.data() + offset,
        partial_count[static_cast<std::size_t>(i)],
        sampled_pixels,
        1));
  }
  return results;
}

py::dict device_info_dict(int device_id) {
  cudaDeviceProp props{};
  check_cuda(cudaGetDeviceProperties(&props, device_id), "cudaGetDeviceProperties");
  py::dict info;
  info["device_id"] = device_id;
  info["name"] = std::string(props.name);
  info["compute_capability"] = std::to_string(props.major) + "." + std::to_string(props.minor);
  info["memory_total_mib"] = static_cast<unsigned long long>(props.totalGlobalMem / (1024 * 1024));
  info["multi_processor_count"] = props.multiProcessorCount;
  info["native_backend"] = true;
  info["available_to_glass"] = true;
  return info;
}

py::array_t<float> host_pinned_empty_f32(std::size_t height, std::size_t width) {
  if (height == 0 || width == 0) {
    throw std::invalid_argument("pinned host array dimensions must be non-empty");
  }
  float* ptr = nullptr;
  check_cuda(
      cudaHostAlloc(
          reinterpret_cast<void**>(&ptr),
          height * width * sizeof(float),
          cudaHostAllocPortable),
      "cudaHostAlloc(host_pinned_empty_f32)");
  py::capsule owner(ptr, [](void* value) {
    if (value != nullptr) {
      cudaFreeHost(value);
    }
  });
  return py::array_t<float>(
      {static_cast<py::ssize_t>(height), static_cast<py::ssize_t>(width)},
      {static_cast<py::ssize_t>(width * sizeof(float)), static_cast<py::ssize_t>(sizeof(float))},
      ptr,
      owner);
}

class ResidentCalibratedStack {
 public:
  ResidentCalibratedStack(std::size_t frame_count, std::size_t height, std::size_t width)
      : frame_count_(frame_count),
        height_(height),
        width_(width),
        pixels_per_frame_(height * width),
        loaded_(frame_count, 0) {
    if (frame_count_ == 0 || height_ == 0 || width_ == 0) {
      throw std::invalid_argument("resident stack dimensions must be non-empty");
    }
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    check_cuda(cudaMalloc(&d_stack_, frame_count_ * frame_bytes), "cudaMalloc(resident calibrated stack)");
    check_cuda(cudaMalloc(&d_light_, frame_bytes), "cudaMalloc(resident raw light buffer)");
    check_cuda(cudaStreamCreate(&calibrate_stream_), "cudaStreamCreate(resident calibration stream)");
    check_cuda(cudaEventCreate(&calibrate_h2d_start_), "cudaEventCreate(resident reusable h2d start)");
    check_cuda(cudaEventCreate(&calibrate_h2d_stop_), "cudaEventCreate(resident reusable h2d stop)");
    check_cuda(cudaEventCreate(&calibrate_kernel_start_), "cudaEventCreate(resident reusable calibration start)");
    check_cuda(cudaEventCreate(&calibrate_kernel_stop_), "cudaEventCreate(resident reusable calibration stop)");
  }

  ResidentCalibratedStack(const ResidentCalibratedStack&) = delete;
  ResidentCalibratedStack& operator=(const ResidentCalibratedStack&) = delete;

  ~ResidentCalibratedStack() {
    if (calibrate_h2d_start_ != nullptr) {
      cudaEventDestroy(calibrate_h2d_start_);
    }
    if (calibrate_h2d_stop_ != nullptr) {
      cudaEventDestroy(calibrate_h2d_stop_);
    }
    if (calibrate_kernel_start_ != nullptr) {
      cudaEventDestroy(calibrate_kernel_start_);
    }
    if (calibrate_kernel_stop_ != nullptr) {
      cudaEventDestroy(calibrate_kernel_stop_);
    }
    if (calibrate_stream_ != nullptr) {
      cudaStreamDestroy(calibrate_stream_);
    }
    for (cudaEvent_t event : calibration_lane_start_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaEvent_t event : calibration_lane_stop_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaEvent_t event : calibration_lane_h2d_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaEvent_t event : calibration_lane_h2d_start_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaStream_t stream : calibration_lane_streams_) {
      if (stream != nullptr) {
        cudaStreamDestroy(stream);
      }
    }
    if (h_pinned_light_ != nullptr) {
      cudaFreeHost(h_pinned_light_);
    }
    cudaFree(d_stack_);
    cudaFree(d_light_);
    for (float* buffer : d_calibration_lane_lights_) {
      cudaFree(buffer);
    }
    cudaFree(d_bias_);
    cudaFree(d_dark_);
    cudaFree(d_flat_);
    cudaFree(d_warp_coverage_);
    cudaFree(d_warp_output_);
    cudaFree(d_warp_frame_coverage_);
    cudaFree(d_warp_inverse_);
  }

  std::size_t frame_count() const { return frame_count_; }
  std::size_t height() const { return height_; }
  std::size_t width() const { return width_; }
  std::size_t pixels_per_frame() const { return pixels_per_frame_; }
  std::size_t loaded_count() const { return loaded_count_; }
  std::size_t host_pinned_bytes() const {
    return h_pinned_light_ == nullptr ? 0 : pixels_per_frame_ * sizeof(float);
  }
  std::size_t calibration_lane_count() const { return d_calibration_lane_lights_.size(); }
  std::size_t calibration_lane_buffer_bytes() const {
    return d_calibration_lane_lights_.size() * pixels_per_frame_ * sizeof(float);
  }

  std::size_t warp_scratch_bytes() const {
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    std::size_t total = 0;
    if (d_warp_output_ != nullptr) {
      total += frame_bytes;
    }
    if (d_warp_frame_coverage_ != nullptr) {
      total += frame_bytes;
    }
    if (d_warp_inverse_ != nullptr) {
      total += 9 * sizeof(float);
    }
    return total;
  }

  std::string warp_copy_mode() const {
    return "default_stream_async_device_to_device";
  }

  std::size_t bytes_allocated() const {
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    std::size_t total = frame_count_ * frame_bytes + frame_bytes + calibration_lane_buffer_bytes();
    if (has_bias_) {
      total += frame_bytes;
    }
    if (has_dark_) {
      total += frame_bytes;
    }
    if (has_flat_) {
      total += frame_bytes;
    }
    if (d_warp_coverage_ != nullptr) {
      total += frame_bytes;
    }
    total += warp_scratch_bytes();
    return total;
  }

  std::size_t warp_coverage_frame_count() const { return warp_coverage_frame_count_; }

  void reset_warp_coverage() {
    allocate_warp_coverage_if_needed();
    check_cuda(
        cudaMemset(d_warp_coverage_, 0, pixels_per_frame_ * sizeof(float)),
        "cudaMemset(resident warp coverage)");
    warp_coverage_frame_count_ = 0;
  }

  void accumulate_full_warp_coverage_frame() {
    allocate_warp_coverage_if_needed();
    glass_coverage_accumulate_full_f32_launch(d_warp_coverage_, pixels_per_frame_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.accumulate_full_warp_coverage_frame kernel launch");
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.accumulate_full_warp_coverage_frame synchronize");
    ++warp_coverage_frame_count_;
  }

  py::array_t<float> warp_coverage_map() const {
    py::array_t<float> result(
        {static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info info = result.request();
    auto* output = static_cast<float*>(info.ptr);
    if (d_warp_coverage_ == nullptr) {
      std::fill(output, output + pixels_per_frame_, 0.0f);
      return result;
    }
    check_cuda(
        cudaMemcpy(output, d_warp_coverage_, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(resident warp coverage map)");
    return result;
  }

  void set_calibration_masters(py::object bias_obj, py::object dark_obj, py::object flat_obj) {
    upload_optional_master(bias_obj, &d_bias_, &has_bias_, "bias");
    upload_optional_master(dark_obj, &d_dark_, &has_dark_, "dark");
    upload_optional_master(flat_obj, &d_flat_, &has_flat_, "flat");
  }

  void upload_calibrated_frame(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> frame) {
    require_index(index);
    const py::buffer_info info = frame.request();
    require_frame_shape(info, height_, width_);
    check_cuda(
        cudaMemcpy(
            d_stack_ + index * pixels_per_frame_,
            info.ptr,
            pixels_per_frame_ * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(resident calibrated frame)");
    mark_loaded(index);
  }

  void calibrate_frame(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    calibrate_frame_pageable_impl(index, light_info.ptr, params);
    mark_loaded(index);
  }

  py::dict calibrate_frame_timed(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    const ResidentCalibrationTiming timing =
        calibrate_frame_pageable_impl(index, light_info.ptr, params);
    mark_loaded(index);
    return calibration_timing_dict(timing, "pageable");
  }

  void calibrate_frame_pinned_async(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    calibrate_frame_pinned_async_impl(index, light_info.ptr, params);
    mark_loaded(index);
  }

  py::dict calibrate_frame_pinned_async_timed(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    const ResidentCalibrationTiming timing =
        calibrate_frame_pinned_async_impl(index, light_info.ptr, params);
    mark_loaded(index);
    return calibration_timing_dict(timing, "pinned_async");
  }

  py::dict calibrate_frame_host_async_timed(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    const ResidentCalibrationTiming timing =
        calibrate_frame_host_async_impl(index, light_info.ptr, params);
    mark_loaded(index);
    return calibration_timing_dict(timing, "host_async");
  }

  py::dict calibrate_frames_host_async_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      py::object policy_obj) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_batch";
      out["event_mode"] = "reused_stack_events";
      out["timing_model"] = "single_stream_sequential_h2d_kernel_one_sync";
      out["frame_count"] = 0;
      out["host_copy_s"] = 0.0;
      out["h2d_s"] = 0.0;
      out["calibrate_store_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_pinned_bytes"] = host_pinned_bytes();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    double sync_s = 0.0;
    double stream_s = 0.0;
    {
      py::gil_scoped_release release;
      check_cuda(
          cudaEventRecord(calibrate_h2d_start_, calibrate_stream_),
          "cudaEventRecord(resident batch calibration start)");
      for (std::size_t i = 0; i < frame_count; ++i) {
        check_cuda(
            cudaMemcpyAsync(
                d_light_,
                light_ptrs[i],
                frame_bytes,
                cudaMemcpyHostToDevice,
                calibrate_stream_),
            "cudaMemcpyAsync(resident batch host raw light)");
        glass_calibrate_tile_f32_launch_stream(
            d_light_,
            d_bias_,
            d_dark_,
            d_flat_,
            d_stack_ + indices[i] * pixels_per_frame_,
            pixels_per_frame_,
            has_bias_,
            has_dark_,
            has_flat_,
            params[i].master_dark_includes_bias,
            params[i].dark_scale,
            params[i].flat_floor,
            params[i].pedestal,
            calibrate_stream_);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frames_host_async kernel launch");
      }
      check_cuda(
          cudaEventRecord(calibrate_kernel_stop_, calibrate_stream_),
          "cudaEventRecord(resident batch calibration stop)");
      const auto sync_start = Clock::now();
      check_cuda(
          cudaStreamSynchronize(calibrate_stream_),
          "ResidentCalibratedStack.calibrate_frames_host_async synchronize");
      sync_s = seconds_since(sync_start);
      stream_s = cuda_event_elapsed_s(
          calibrate_h2d_start_,
          calibrate_kernel_stop_,
          "cudaEventElapsedTime(resident batch h2d calibration)");
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "host_async_batch");
    out["timing_model"] = "single_stream_sequential_h2d_kernel_one_sync";
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    return out;
  }

  py::dict calibrate_frames_host_async_multistream_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      py::object policy_obj) {
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_multistream_batch";
      out["event_mode"] = "reused_stack_lane_events";
      out["timing_model"] = "multi_stream_lanes_one_sync";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["frame_count"] = 0;
      out["host_copy_s"] = 0.0;
      out["h2d_s"] = 0.0;
      out["calibrate_store_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_pinned_bytes"] = host_pinned_bytes();
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["lane_stream_elapsed_s"] = py::list();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t lane_count =
        std::min<std::size_t>(static_cast<std::size_t>(stream_count), frame_count);
    ensure_calibration_lanes(lane_count);

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_used(lane_count, 0);
    std::vector<double> lane_elapsed(lane_count, 0.0);
    double sync_s = 0.0;
    double stream_s = 0.0;
    {
      py::gil_scoped_release release;
      for (std::size_t i = 0; i < frame_count; ++i) {
        const std::size_t lane = i % lane_count;
        if (!lane_used[lane]) {
          check_cuda(
              cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident multistream batch lane start)");
          lane_used[lane] = 1;
        }
        check_cuda(
            cudaMemcpyAsync(
                d_calibration_lane_lights_[lane],
                light_ptrs[i],
                frame_bytes,
                cudaMemcpyHostToDevice,
                calibration_lane_streams_[lane]),
            "cudaMemcpyAsync(resident multistream batch host raw light)");
        glass_calibrate_tile_f32_launch_stream(
            d_calibration_lane_lights_[lane],
            d_bias_,
            d_dark_,
            d_flat_,
            d_stack_ + indices[i] * pixels_per_frame_,
            pixels_per_frame_,
            has_bias_,
            has_dark_,
            has_flat_,
            params[i].master_dark_includes_bias,
            params[i].dark_scale,
            params[i].flat_floor,
            params[i].pedestal,
            calibration_lane_streams_[lane]);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frames_host_async_multistream kernel launch");
      }
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_used[lane]) {
          check_cuda(
              cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident multistream batch lane stop)");
        }
      }
      const auto sync_start = Clock::now();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_used[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.calibrate_frames_host_async_multistream synchronize");
        }
      }
      sync_s = seconds_since(sync_start);
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_used[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident multistream batch lane)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "host_async_multistream_batch");
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }
    out["event_mode"] = "reused_stack_lane_events";
    out["timing_model"] = "multi_stream_lanes_one_sync";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    return out;
  }

  py::dict calibrate_frames_host_async_multistream_h2d_release_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      py::object policy_obj) {
    if (pending_calibration_) {
      throw std::runtime_error("a resident calibration batch is already pending");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_multistream_h2d_release_batch";
      out["event_mode"] = "reused_stack_lane_h2d_events";
      out["timing_model"] = "multi_stream_one_frame_per_lane_h2d_release_then_wait";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["frame_count"] = 0;
      out["h2d_release_s"] = 0.0;
      out["h2d_event_sync_s"] = 0.0;
      out["h2d_event_elapsed_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_release_safe"] = true;
      out["pending"] = false;
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["lane_h2d_elapsed_s"] = py::list();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t lane_count =
        std::min<std::size_t>(static_cast<std::size_t>(stream_count), frame_count);
    if (frame_count > lane_count) {
      throw std::invalid_argument(
          "h2d-release calibration requires frame_count <= stream_count so each lane holds one frame");
    }
    ensure_calibration_lanes(lane_count);

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_used(lane_count, 0);
    std::vector<double> lane_h2d_elapsed(lane_count, 0.0);
    double h2d_event_sync_s = 0.0;
    double h2d_event_elapsed_s = 0.0;
    {
      py::gil_scoped_release release;
      try {
        for (std::size_t i = 0; i < frame_count; ++i) {
          const std::size_t lane = i;
          check_cuda(
              cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident h2d-release lane start)");
          lane_used[lane] = 1;
          check_cuda(
              cudaMemcpyAsync(
                  d_calibration_lane_lights_[lane],
                  light_ptrs[i],
                  frame_bytes,
                  cudaMemcpyHostToDevice,
                  calibration_lane_streams_[lane]),
              "cudaMemcpyAsync(resident h2d-release host raw light)");
          check_cuda(
              cudaEventRecord(calibration_lane_h2d_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident h2d-release lane h2d done)");
          glass_calibrate_tile_f32_launch_stream(
              d_calibration_lane_lights_[lane],
              d_bias_,
              d_dark_,
              d_flat_,
              d_stack_ + indices[i] * pixels_per_frame_,
              pixels_per_frame_,
              has_bias_,
              has_dark_,
              has_flat_,
              params[i].master_dark_includes_bias,
              params[i].dark_scale,
              params[i].flat_floor,
              params[i].pedestal,
              calibration_lane_streams_[lane]);
          check_cuda(
              cudaGetLastError(),
              "ResidentCalibratedStack.calibrate_frames_host_async_multistream_h2d_release kernel launch");
          check_cuda(
              cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident h2d-release lane calibration stop)");
        }
        const auto h2d_sync_start = Clock::now();
        for (std::size_t lane = 0; lane < lane_count; ++lane) {
          if (lane_used[lane]) {
            check_cuda(
                cudaEventSynchronize(calibration_lane_h2d_events_[lane]),
                "cudaEventSynchronize(resident h2d-release lane h2d)");
          }
        }
        h2d_event_sync_s = seconds_since(h2d_sync_start);
        for (std::size_t lane = 0; lane < lane_count; ++lane) {
          if (lane_used[lane]) {
            lane_h2d_elapsed[lane] = cuda_event_elapsed_s(
                calibration_lane_start_events_[lane],
                calibration_lane_h2d_events_[lane],
                "cudaEventElapsedTime(resident h2d-release lane h2d)");
            h2d_event_elapsed_s = std::max(h2d_event_elapsed_s, lane_h2d_elapsed[lane]);
          }
        }
      } catch (...) {
        for (std::size_t lane = 0; lane < lane_count; ++lane) {
          if (lane_used[lane]) {
            cudaStreamSynchronize(calibration_lane_streams_[lane]);
          }
        }
        throw;
      }
    }

    pending_calibration_ = true;
    pending_calibration_indices_ = indices;
    pending_calibration_lane_used_ = lane_used;
    pending_calibration_lane_count_ = lane_count;
    pending_calibration_total_start_ = total_start;
    pending_calibration_h2d_release_s_ = seconds_since(total_start);
    pending_calibration_h2d_event_sync_s_ = h2d_event_sync_s;
    pending_calibration_h2d_event_elapsed_s_ = h2d_event_elapsed_s;

    py::list lane_h2d_elapsed_s;
    for (const double value : lane_h2d_elapsed) {
      lane_h2d_elapsed_s.append(value);
    }
    py::dict out;
    out["schema_version"] = 1;
    out["h2d_mode"] = "host_async_multistream_h2d_release_batch";
    out["event_mode"] = "reused_stack_lane_h2d_events";
    out["timing_model"] = "multi_stream_one_frame_per_lane_h2d_release_then_wait";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["h2d_release_s"] = pending_calibration_h2d_release_s_;
    out["h2d_event_sync_s"] = h2d_event_sync_s;
    out["h2d_event_elapsed_s"] = h2d_event_elapsed_s;
    out["total_s"] = pending_calibration_h2d_release_s_;
    out["host_release_safe"] = true;
    out["pending"] = true;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_h2d_elapsed_s"] = lane_h2d_elapsed_s;
    return out;
  }

  py::dict finish_pending_calibration_timed() {
    if (!pending_calibration_) {
      py::dict out;
      out["schema_version"] = 1;
      out["pending"] = false;
      out["wait_sync_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["total_s"] = 0.0;
      out["frame_count"] = 0;
      out["stream_count"] = 0;
      out["lane_stream_elapsed_s"] = py::list();
      return out;
    }
    double wait_sync_s = 0.0;
    double stream_s = 0.0;
    std::vector<double> lane_elapsed(pending_calibration_lane_count_, 0.0);
    {
      py::gil_scoped_release release;
      const auto wait_start = Clock::now();
      for (std::size_t lane = 0; lane < pending_calibration_lane_count_; ++lane) {
        if (pending_calibration_lane_used_[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.finish_pending_calibration synchronize");
        }
      }
      wait_sync_s = seconds_since(wait_start);
      for (std::size_t lane = 0; lane < pending_calibration_lane_count_; ++lane) {
        if (pending_calibration_lane_used_[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident h2d-release lane calibration)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : pending_calibration_indices_) {
      mark_loaded(index);
    }
    const double total_s = seconds_since(pending_calibration_total_start_);
    const std::size_t frame_count = pending_calibration_indices_.size();
    const std::size_t stream_count = pending_calibration_lane_count_;
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }

    pending_calibration_ = false;
    pending_calibration_indices_.clear();
    pending_calibration_lane_used_.clear();
    pending_calibration_lane_count_ = 0;

    py::dict out;
    out["schema_version"] = 1;
    out["pending"] = false;
    out["event_mode"] = "reused_stack_lane_h2d_events";
    out["timing_model"] = "multi_stream_one_frame_per_lane_h2d_release_then_wait";
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["stream_count"] = static_cast<unsigned long long>(stream_count);
    out["h2d_release_s"] = pending_calibration_h2d_release_s_;
    out["h2d_event_sync_s"] = pending_calibration_h2d_event_sync_s_;
    out["h2d_event_elapsed_s"] = pending_calibration_h2d_event_elapsed_s_;
    out["wait_sync_s"] = wait_sync_s;
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = wait_sync_s;
    out["total_s"] = total_s;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    return out;
  }

  py::dict calibrate_frames_host_async_multistream_callback_release_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      int wave_frames,
      py::object release_callback,
      py::object policy_obj) {
    if (pending_calibration_) {
      throw std::runtime_error("a resident calibration batch is already pending");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    if (wave_frames <= 0) {
      throw std::invalid_argument("wave_frames must be positive");
    }
    if (wave_frames > stream_count) {
      throw std::invalid_argument("callback-release calibration requires wave_frames <= stream_count");
    }
    if (!PyCallable_Check(release_callback.ptr())) {
      throw std::invalid_argument("release_callback must be callable");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_multistream_callback_release_batch";
      out["event_mode"] = "reused_stack_lane_h2d_callback_events";
      out["timing_model"] = "multi_stream_callback_release_waves_one_final_sync";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["requested_wave_frames"] = wave_frames;
      out["wave_frames"] = 0;
      out["wave_count"] = 0;
      out["frame_count"] = 0;
      out["callback_release_count"] = 0;
      out["h2d_release_s"] = 0.0;
      out["h2d_event_sync_s"] = 0.0;
      out["h2d_event_elapsed_s"] = 0.0;
      out["callback_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_release_safe"] = true;
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["lane_stream_elapsed_s"] = py::list();
      out["wave_h2d_elapsed_s"] = py::list();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t requested_wave_frames = static_cast<std::size_t>(wave_frames);
    const std::size_t lane_count = std::min<std::size_t>(
        static_cast<std::size_t>(stream_count),
        std::min<std::size_t>(requested_wave_frames, frame_count));
    ensure_calibration_lanes(lane_count);

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_started(lane_count, 0);
    std::vector<unsigned char> lane_used_in_wave(lane_count, 0);
    std::vector<double> lane_elapsed(lane_count, 0.0);
    std::vector<double> wave_h2d_elapsed;
    wave_h2d_elapsed.reserve((frame_count + requested_wave_frames - 1) / requested_wave_frames);
    double h2d_event_sync_s = 0.0;
    double h2d_event_elapsed_s = 0.0;
    double callback_s = 0.0;
    std::size_t callback_release_count = 0;
    std::size_t wave_count = 0;
    double h2d_release_s = 0.0;
    try {
      for (std::size_t wave_start = 0; wave_start < frame_count; wave_start += requested_wave_frames) {
        const std::size_t frames_in_wave = std::min<std::size_t>(requested_wave_frames, frame_count - wave_start);
        std::fill(lane_used_in_wave.begin(), lane_used_in_wave.end(), 0);
        double wave_elapsed_s = 0.0;
        {
          py::gil_scoped_release release;
          for (std::size_t j = 0; j < frames_in_wave; ++j) {
            const std::size_t lane = j;
            const std::size_t frame_offset = wave_start + j;
            if (!lane_started[lane]) {
              check_cuda(
                  cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
                  "cudaEventRecord(resident callback-release lane start)");
              lane_started[lane] = 1;
            }
            lane_used_in_wave[lane] = 1;
            check_cuda(
                cudaEventRecord(calibration_lane_h2d_start_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident callback-release lane h2d start)");
            check_cuda(
                cudaMemcpyAsync(
                    d_calibration_lane_lights_[lane],
                    light_ptrs[frame_offset],
                    frame_bytes,
                    cudaMemcpyHostToDevice,
                    calibration_lane_streams_[lane]),
                "cudaMemcpyAsync(resident callback-release host raw light)");
            check_cuda(
                cudaEventRecord(calibration_lane_h2d_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident callback-release lane h2d done)");
            glass_calibrate_tile_f32_launch_stream(
                d_calibration_lane_lights_[lane],
                d_bias_,
                d_dark_,
                d_flat_,
                d_stack_ + indices[frame_offset] * pixels_per_frame_,
                pixels_per_frame_,
                has_bias_,
                has_dark_,
                has_flat_,
                params[frame_offset].master_dark_includes_bias,
                params[frame_offset].dark_scale,
                params[frame_offset].flat_floor,
                params[frame_offset].pedestal,
                calibration_lane_streams_[lane]);
            check_cuda(
                cudaGetLastError(),
                "ResidentCalibratedStack.calibrate_frames_host_async_multistream_callback_release kernel launch");
            check_cuda(
                cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident callback-release lane calibration stop)");
          }
          const auto h2d_sync_start = Clock::now();
          for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
            if (lane_used_in_wave[lane]) {
              check_cuda(
                  cudaEventSynchronize(calibration_lane_h2d_events_[lane]),
                  "cudaEventSynchronize(resident callback-release lane h2d)");
            }
          }
          h2d_event_sync_s += seconds_since(h2d_sync_start);
          for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
            if (lane_used_in_wave[lane]) {
              const double lane_h2d_s = cuda_event_elapsed_s(
                  calibration_lane_h2d_start_events_[lane],
                  calibration_lane_h2d_events_[lane],
                  "cudaEventElapsedTime(resident callback-release lane h2d)");
              wave_elapsed_s = std::max(wave_elapsed_s, lane_h2d_s);
              h2d_event_elapsed_s = std::max(h2d_event_elapsed_s, lane_h2d_s);
            }
          }
        }
        py::list released_indices;
        for (std::size_t j = 0; j < frames_in_wave; ++j) {
          released_indices.append(static_cast<unsigned long long>(indices[wave_start + j]));
        }
        const auto callback_start = Clock::now();
        release_callback(released_indices);
        callback_s += seconds_since(callback_start);
        callback_release_count += frames_in_wave;
        wave_h2d_elapsed.push_back(wave_elapsed_s);
        ++wave_count;
      }
      h2d_release_s = seconds_since(total_start);
    } catch (...) {
      py::gil_scoped_release release;
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          cudaStreamSynchronize(calibration_lane_streams_[lane]);
        }
      }
      throw;
    }

    double sync_s = 0.0;
    double stream_s = 0.0;
    {
      py::gil_scoped_release release;
      const auto sync_start = Clock::now();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.calibrate_frames_host_async_multistream_callback_release synchronize");
        }
      }
      sync_s = seconds_since(sync_start);
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident callback-release lane calibration)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }
    py::list wave_h2d_elapsed_s;
    for (const double value : wave_h2d_elapsed) {
      wave_h2d_elapsed_s.append(value);
    }
    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "host_async_multistream_callback_release_batch");
    out["event_mode"] = "reused_stack_lane_h2d_callback_events";
    out["timing_model"] = "multi_stream_callback_release_waves_one_final_sync";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["requested_wave_frames"] = wave_frames;
    out["wave_frames"] = static_cast<unsigned long long>(requested_wave_frames);
    out["wave_count"] = static_cast<unsigned long long>(wave_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["callback_release_count"] = static_cast<unsigned long long>(callback_release_count);
    out["h2d_release_s"] = h2d_release_s;
    out["h2d_event_sync_s"] = h2d_event_sync_s;
    out["h2d_event_elapsed_s"] = h2d_event_elapsed_s;
    out["callback_s"] = callback_s;
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    out["host_release_safe"] = true;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    out["wave_h2d_elapsed_s"] = wave_h2d_elapsed_s;
    return out;
  }

  void apply_translation_frame(std::size_t index, int dx, int dy, float fill) {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before translation warp");
    }
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(false);
    allocate_warp_coverage_if_needed();
    glass_warp_translation_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        dx,
        dy,
        fill,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_translation_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident translated frame)");
    ++warp_coverage_frame_count_;
  }

  void apply_translation_bilinear_frame(std::size_t index, float dx, float dy, float fill) {
    require_loaded(index, "bilinear translation warp");
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(false);
    allocate_warp_coverage_if_needed();
    glass_warp_translation_bilinear_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        dx,
        dy,
        fill,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_translation_bilinear_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident bilinear translated frame)");
    ++warp_coverage_frame_count_;
  }

  void apply_matrix_bilinear_frame(std::size_t index, py::object matrix_obj, float fill) {
    require_loaded(index, "matrix bilinear warp");
    const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    allocate_warp_coverage_if_needed();
    check_cuda(
        cudaMemcpy(d_warp_inverse_, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident matrix warp inverse)");
    glass_warp_matrix_bilinear_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        d_warp_inverse_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        fill,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident matrix warped frame)");
    ++warp_coverage_frame_count_;
  }

  void apply_matrix_lanczos3_frame(
      std::size_t index,
      py::object matrix_obj,
      float fill,
      float clamping_threshold) {
    require_loaded(index, "matrix Lanczos3 warp");
    const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    allocate_warp_coverage_if_needed();
    check_cuda(
        cudaMemcpy(d_warp_inverse_, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident matrix Lanczos3 inverse)");
    glass_warp_matrix_lanczos3_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        d_warp_inverse_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        fill,
        clamping_threshold,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident matrix Lanczos3 warped frame)");
    ++warp_coverage_frame_count_;
  }

  py::dict apply_matrix_bilinear_frames_loop(py::object indices_obj, py::object matrices_obj, float fill) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "bilinear";
      result["timing_model"] = "native_loop_batched_inverse_one_sync";
      result["inverse_upload_mode"] = "single_device_batch";
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["device_copy_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "loop batched matrix bilinear warp");
    }
    const auto total_start = Clock::now();
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    allocate_warp_coverage_if_needed();
    const auto inverse_prepare_start = Clock::now();
    std::vector<float> inverse_host(indices.size() * 9, 0.0f);
    for (std::size_t i = 0; i < matrices.size(); ++i) {
      const auto inverse = invert_matrix3x3(matrices[i]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(i * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);
    float* raw_inverse_batch = nullptr;
    const auto inverse_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&raw_inverse_batch, inverse_host.size() * sizeof(float)),
        "cudaMalloc(resident loop batched matrix warp inverses)");
    std::unique_ptr<float, CudaFloatFree> inverse_batch(raw_inverse_batch);
    const double inverse_alloc_s = seconds_since(inverse_alloc_start);
    const auto inverse_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            inverse_batch.get(),
            inverse_host.data(),
            inverse_host.size() * sizeof(float),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident loop batched matrix warp inverses)");
    double inverse_upload_s = seconds_since(inverse_upload_start);
    double kernel_enqueue_s = 0.0;
    double copy_enqueue_s = 0.0;
    for (std::size_t i = 0; i < indices.size(); ++i) {
      const std::size_t index = indices[i];
      const auto kernel_start = Clock::now();
      glass_warp_matrix_bilinear_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_warp_output_,
          d_warp_frame_coverage_,
          inverse_batch.get() + i * 9,
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill,
          d_warp_coverage_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frames_loop kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      const auto copy_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              d_stack_ + index * pixels_per_frame_,
              d_warp_output_,
              frame_bytes,
              cudaMemcpyDeviceToDevice,
              0),
          "cudaMemcpyAsync(resident loop batched matrix warped frame)");
      copy_enqueue_s += seconds_since(copy_start);
      ++warp_coverage_frame_count_;
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_bilinear_frames_loop synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "bilinear";
    result["timing_model"] = "native_loop_batched_inverse_one_sync";
    result["inverse_upload_mode"] = "single_device_batch";
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = inverse_alloc_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_host.size() * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["device_copy_enqueue_s"] = copy_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_matrix_lanczos3_frames_loop(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      float clamping_threshold) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "lanczos3";
      result["timing_model"] = "native_loop_batched_inverse_one_sync";
      result["inverse_upload_mode"] = "single_device_batch";
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["device_copy_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "loop batched matrix Lanczos3 warp");
    }
    const auto total_start = Clock::now();
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    allocate_warp_coverage_if_needed();
    const auto inverse_prepare_start = Clock::now();
    std::vector<float> inverse_host(indices.size() * 9, 0.0f);
    for (std::size_t i = 0; i < matrices.size(); ++i) {
      const auto inverse = invert_matrix3x3(matrices[i]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(i * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);
    float* raw_inverse_batch = nullptr;
    const auto inverse_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&raw_inverse_batch, inverse_host.size() * sizeof(float)),
        "cudaMalloc(resident loop batched matrix Lanczos3 inverses)");
    std::unique_ptr<float, CudaFloatFree> inverse_batch(raw_inverse_batch);
    const double inverse_alloc_s = seconds_since(inverse_alloc_start);
    const auto inverse_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            inverse_batch.get(),
            inverse_host.data(),
            inverse_host.size() * sizeof(float),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident loop batched matrix Lanczos3 inverses)");
    double inverse_upload_s = seconds_since(inverse_upload_start);
    double kernel_enqueue_s = 0.0;
    double copy_enqueue_s = 0.0;
    for (std::size_t i = 0; i < indices.size(); ++i) {
      const std::size_t index = indices[i];
      const auto kernel_start = Clock::now();
      glass_warp_matrix_lanczos3_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_warp_output_,
          d_warp_frame_coverage_,
          inverse_batch.get() + i * 9,
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill,
          clamping_threshold,
          d_warp_coverage_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames_loop kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      const auto copy_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              d_stack_ + index * pixels_per_frame_,
              d_warp_output_,
              frame_bytes,
              cudaMemcpyDeviceToDevice,
              0),
          "cudaMemcpyAsync(resident loop batched matrix Lanczos3 warped frame)");
      copy_enqueue_s += seconds_since(copy_start);
      ++warp_coverage_frame_count_;
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames_loop synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "lanczos3";
    result["timing_model"] = "native_loop_batched_inverse_one_sync";
    result["inverse_upload_mode"] = "single_device_batch";
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = inverse_alloc_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_host.size() * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["device_copy_enqueue_s"] = copy_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_matrix_bilinear_frames(py::object indices_obj, py::object matrices_obj, float fill) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "bilinear";
      result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
      result["inverse_upload_mode"] = "chunked_device_batch";
      result["batch_chunk_frames"] = 0;
      result["batch_chunk_count"] = 0;
      result["batch_workspace_bytes"] = 0;
      result["batch_output_bytes"] = 0;
      result["batch_coverage_bytes"] = 0;
      result["index_upload_s"] = 0.0;
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["coverage_reduce_enqueue_s"] = 0.0;
      result["scatter_enqueue_s"] = 0.0;
      result["warp_kernel_launches"] = 0;
      result["coverage_reduce_kernel_launches"] = 0;
      result["scatter_kernel_launches"] = 0;
      result["device_copy_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "batched matrix bilinear warp");
    }
    const auto total_start = Clock::now();
    allocate_warp_coverage_if_needed();
    auto workspace = allocate_batch_warp_workspace(indices.size());
    std::vector<unsigned long long> index_host(workspace.capacity_frames, 0ULL);
    std::vector<float> inverse_host(workspace.capacity_frames * 9, 0.0f);
    double inverse_prepare_s = 0.0;
    double index_upload_s = 0.0;
    double inverse_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double coverage_reduce_enqueue_s = 0.0;
    double scatter_enqueue_s = 0.0;
    std::size_t chunk_count = 0;
    std::size_t warp_kernel_launches = 0;
    std::size_t coverage_reduce_kernel_launches = 0;
    std::size_t scatter_kernel_launches = 0;
    for (std::size_t begin = 0; begin < indices.size(); begin += workspace.capacity_frames) {
      const std::size_t chunk_frames = std::min(workspace.capacity_frames, indices.size() - begin);
      const auto inverse_prepare_start = Clock::now();
      for (std::size_t j = 0; j < chunk_frames; ++j) {
        index_host[j] = static_cast<unsigned long long>(indices[begin + j]);
        const auto inverse = invert_matrix3x3(matrices[begin + j]);
        std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(j * 9));
      }
      inverse_prepare_s += seconds_since(inverse_prepare_start);
      const auto index_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              workspace.indices.get(),
              index_host.data(),
              chunk_frames * sizeof(unsigned long long),
              cudaMemcpyHostToDevice,
              0),
          "cudaMemcpyAsync(resident batched matrix warp indices)");
      index_upload_s += seconds_since(index_upload_start);
      const auto inverse_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              workspace.inverses.get(),
              inverse_host.data(),
              chunk_frames * 9 * sizeof(float),
              cudaMemcpyHostToDevice,
              0),
          "cudaMemcpyAsync(resident batched matrix warp inverses)");
      inverse_upload_s += seconds_since(inverse_upload_start);
      const auto kernel_start = Clock::now();
      glass_warp_matrix_bilinear_batch_f32_launch(
          d_stack_,
          workspace.output.get(),
          workspace.coverage.get(),
          workspace.indices.get(),
          workspace.inverses.get(),
          static_cast<int>(chunk_frames),
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frames kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      ++warp_kernel_launches;
      const auto coverage_start = Clock::now();
      glass_warp_batch_coverage_reduce_f32_launch(
          workspace.coverage.get(),
          d_warp_coverage_,
          static_cast<int>(chunk_frames),
          pixels_per_frame_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frames coverage reduce launch");
      coverage_reduce_enqueue_s += seconds_since(coverage_start);
      ++coverage_reduce_kernel_launches;
      const auto scatter_start = Clock::now();
      glass_warp_batch_scatter_f32_launch(
          workspace.output.get(),
          d_stack_,
          workspace.indices.get(),
          static_cast<int>(chunk_frames),
          pixels_per_frame_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frames scatter launch");
      scatter_enqueue_s += seconds_since(scatter_start);
      ++scatter_kernel_launches;
      warp_coverage_frame_count_ += chunk_frames;
      ++chunk_count;
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_bilinear_frames synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "bilinear";
    result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
    result["inverse_upload_mode"] = "chunked_device_batch";
    result["batch_chunk_frames"] = static_cast<unsigned long long>(workspace.capacity_frames);
    result["batch_chunk_count"] = static_cast<unsigned long long>(chunk_count);
    result["batch_workspace_bytes"] = static_cast<unsigned long long>(
        workspace.output_bytes + workspace.coverage_bytes + workspace.inverse_bytes + workspace.index_bytes);
    result["batch_output_bytes"] = static_cast<unsigned long long>(workspace.output_bytes);
    result["batch_coverage_bytes"] = static_cast<unsigned long long>(workspace.coverage_bytes);
    result["index_upload_s"] = index_upload_s;
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = workspace.allocation_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(indices.size() * 9 * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["coverage_reduce_enqueue_s"] = coverage_reduce_enqueue_s;
    result["scatter_enqueue_s"] = scatter_enqueue_s;
    result["warp_kernel_launches"] = static_cast<unsigned long long>(warp_kernel_launches);
    result["coverage_reduce_kernel_launches"] = static_cast<unsigned long long>(coverage_reduce_kernel_launches);
    result["scatter_kernel_launches"] = static_cast<unsigned long long>(scatter_kernel_launches);
    result["device_copy_enqueue_s"] = scatter_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_matrix_lanczos3_frames(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      float clamping_threshold) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "lanczos3";
      result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
      result["inverse_upload_mode"] = "chunked_device_batch";
      result["batch_chunk_frames"] = 0;
      result["batch_chunk_count"] = 0;
      result["batch_workspace_bytes"] = 0;
      result["batch_output_bytes"] = 0;
      result["batch_coverage_bytes"] = 0;
      result["index_upload_s"] = 0.0;
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["coverage_reduce_enqueue_s"] = 0.0;
      result["scatter_enqueue_s"] = 0.0;
      result["warp_kernel_launches"] = 0;
      result["coverage_reduce_kernel_launches"] = 0;
      result["scatter_kernel_launches"] = 0;
      result["device_copy_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "batched matrix Lanczos3 warp");
    }
    const auto total_start = Clock::now();
    allocate_warp_coverage_if_needed();
    auto workspace = allocate_batch_warp_workspace(indices.size());
    std::vector<unsigned long long> index_host(workspace.capacity_frames, 0ULL);
    std::vector<float> inverse_host(workspace.capacity_frames * 9, 0.0f);
    double inverse_prepare_s = 0.0;
    double index_upload_s = 0.0;
    double inverse_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double coverage_reduce_enqueue_s = 0.0;
    double scatter_enqueue_s = 0.0;
    std::size_t chunk_count = 0;
    std::size_t warp_kernel_launches = 0;
    std::size_t coverage_reduce_kernel_launches = 0;
    std::size_t scatter_kernel_launches = 0;
    for (std::size_t begin = 0; begin < indices.size(); begin += workspace.capacity_frames) {
      const std::size_t chunk_frames = std::min(workspace.capacity_frames, indices.size() - begin);
      const auto inverse_prepare_start = Clock::now();
      for (std::size_t j = 0; j < chunk_frames; ++j) {
        index_host[j] = static_cast<unsigned long long>(indices[begin + j]);
        const auto inverse = invert_matrix3x3(matrices[begin + j]);
        std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(j * 9));
      }
      inverse_prepare_s += seconds_since(inverse_prepare_start);
      const auto index_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              workspace.indices.get(),
              index_host.data(),
              chunk_frames * sizeof(unsigned long long),
              cudaMemcpyHostToDevice,
              0),
          "cudaMemcpyAsync(resident batched matrix Lanczos3 indices)");
      index_upload_s += seconds_since(index_upload_start);
      const auto inverse_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              workspace.inverses.get(),
              inverse_host.data(),
              chunk_frames * 9 * sizeof(float),
              cudaMemcpyHostToDevice,
              0),
          "cudaMemcpyAsync(resident batched matrix Lanczos3 inverses)");
      inverse_upload_s += seconds_since(inverse_upload_start);
      const auto kernel_start = Clock::now();
      glass_warp_matrix_lanczos3_batch_f32_launch(
          d_stack_,
          workspace.output.get(),
          workspace.coverage.get(),
          workspace.indices.get(),
          workspace.inverses.get(),
          static_cast<int>(chunk_frames),
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill,
          clamping_threshold);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      ++warp_kernel_launches;
      const auto coverage_start = Clock::now();
      glass_warp_batch_coverage_reduce_f32_launch(
          workspace.coverage.get(),
          d_warp_coverage_,
          static_cast<int>(chunk_frames),
          pixels_per_frame_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames coverage reduce launch");
      coverage_reduce_enqueue_s += seconds_since(coverage_start);
      ++coverage_reduce_kernel_launches;
      const auto scatter_start = Clock::now();
      glass_warp_batch_scatter_f32_launch(
          workspace.output.get(),
          d_stack_,
          workspace.indices.get(),
          static_cast<int>(chunk_frames),
          pixels_per_frame_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames scatter launch");
      scatter_enqueue_s += seconds_since(scatter_start);
      ++scatter_kernel_launches;
      warp_coverage_frame_count_ += chunk_frames;
      ++chunk_count;
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "lanczos3";
    result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
    result["inverse_upload_mode"] = "chunked_device_batch";
    result["batch_chunk_frames"] = static_cast<unsigned long long>(workspace.capacity_frames);
    result["batch_chunk_count"] = static_cast<unsigned long long>(chunk_count);
    result["batch_workspace_bytes"] = static_cast<unsigned long long>(
        workspace.output_bytes + workspace.coverage_bytes + workspace.inverse_bytes + workspace.index_bytes);
    result["batch_output_bytes"] = static_cast<unsigned long long>(workspace.output_bytes);
    result["batch_coverage_bytes"] = static_cast<unsigned long long>(workspace.coverage_bytes);
    result["index_upload_s"] = index_upload_s;
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = workspace.allocation_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(indices.size() * 9 * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["coverage_reduce_enqueue_s"] = coverage_reduce_enqueue_s;
    result["scatter_enqueue_s"] = scatter_enqueue_s;
    result["warp_kernel_launches"] = static_cast<unsigned long long>(warp_kernel_launches);
    result["coverage_reduce_kernel_launches"] = static_cast<unsigned long long>(coverage_reduce_kernel_launches);
    result["scatter_kernel_launches"] = static_cast<unsigned long long>(scatter_kernel_launches);
    result["device_copy_enqueue_s"] = scatter_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict matrix_alignment_metrics_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      py::object matrix_obj,
      int sample_stride) const {
    require_loaded(reference_index, "resident matrix alignment metrics");
    require_loaded(moving_index, "resident matrix alignment metrics");
    if (sample_stride <= 0) {
      throw std::invalid_argument("sample_stride must be positive");
    }
    const int stride = sample_stride > 1 ? sample_stride : 1;
    const int sample_width = static_cast<int>((width_ + static_cast<std::size_t>(stride) - 1) / static_cast<std::size_t>(stride));
    const int sample_height = static_cast<int>((height_ + static_cast<std::size_t>(stride) - 1) / static_cast<std::size_t>(stride));
    const int sampled_pixels = sample_width * sample_height;
    constexpr int threads = 256;
    const int blocks = std::max(1, std::min(1024, (sampled_pixels + threads - 1) / threads));
    const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
    std::vector<double> partial_stats(static_cast<std::size_t>(blocks) * 7, 0.0);
    std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);
    float* d_inverse = nullptr;
    double* d_partial_stats = nullptr;
    unsigned long long* d_partial_count = nullptr;
    try {
      check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(resident matrix metrics inverse)");
      check_cuda(
          cudaMalloc(&d_partial_stats, partial_stats.size() * sizeof(double)),
          "cudaMalloc(resident matrix metrics partial stats)");
      check_cuda(
          cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident matrix metrics partial count)");
      check_cuda(
          cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident matrix metrics inverse)");
      glass_matrix_alignment_metrics_f32_launch(
          d_stack_ + reference_index * pixels_per_frame_,
          d_stack_ + moving_index * pixels_per_frame_,
          d_inverse,
          d_partial_stats,
          d_partial_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          stride,
          blocks);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.matrix_alignment_metrics_to_reference kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.matrix_alignment_metrics_to_reference synchronize");
      check_cuda(
          cudaMemcpy(partial_stats.data(), d_partial_stats, partial_stats.size() * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident matrix metrics partial stats)");
      check_cuda(
          cudaMemcpy(
              partial_count.data(),
              d_partial_count,
              partial_count.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident matrix metrics partial count)");
    } catch (...) {
      cudaFree(d_inverse);
      cudaFree(d_partial_stats);
      cudaFree(d_partial_count);
      throw;
    }
    cudaFree(d_inverse);
    cudaFree(d_partial_stats);
    cudaFree(d_partial_count);

    double sum_ref = 0.0;
    double sum_mov = 0.0;
    double sum_ref2 = 0.0;
    double sum_mov2 = 0.0;
    double sum_cross = 0.0;
    double sum_diff2 = 0.0;
    double sum_abs_diff = 0.0;
    unsigned long long valid_pixels = 0ULL;
    for (int block = 0; block < blocks; ++block) {
      const std::size_t offset = static_cast<std::size_t>(block) * 7;
      sum_ref += partial_stats[offset + 0];
      sum_mov += partial_stats[offset + 1];
      sum_ref2 += partial_stats[offset + 2];
      sum_mov2 += partial_stats[offset + 3];
      sum_cross += partial_stats[offset + 4];
      sum_diff2 += partial_stats[offset + 5];
      sum_abs_diff += partial_stats[offset + 6];
      valid_pixels += partial_count[static_cast<std::size_t>(block)];
    }

    const double count = static_cast<double>(valid_pixels);
    double rms = std::numeric_limits<double>::quiet_NaN();
    double mean_abs_diff = std::numeric_limits<double>::quiet_NaN();
    double ncc = std::numeric_limits<double>::quiet_NaN();
    if (valid_pixels > 0ULL) {
      rms = std::sqrt(sum_diff2 / count);
      mean_abs_diff = sum_abs_diff / count;
    }
    if (valid_pixels > 1ULL) {
      const double numerator = sum_cross - (sum_ref * sum_mov / count);
      const double ref_var = std::max(sum_ref2 - (sum_ref * sum_ref / count), 0.0);
      const double mov_var = std::max(sum_mov2 - (sum_mov * sum_mov / count), 0.0);
      const double denominator = std::sqrt(ref_var * mov_var);
      if (denominator > 0.0) {
        ncc = numerator / denominator;
      }
    }

    py::dict result;
    result["valid_pixels"] = valid_pixels;
    result["sampled_pixels"] = sampled_pixels;
    result["sample_stride"] = stride;
    result["rms"] = rms;
    result["mean_abs_diff"] = mean_abs_diff;
    result["ncc"] = ncc;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_matrix_alignment_metrics_cuda";
    return result;
  }

  py::dict star_core_metrics_candidates_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      py::object matrices_obj,
      float threshold) const {
    require_loaded(reference_index, "resident star core candidate metrics");
    require_loaded(moving_index, "resident star core candidate metrics");
    const auto matrices = parse_matrix_stack(matrices_obj);
    const auto* d_reference = d_stack_ + reference_index * pixels_per_frame_;
    const auto* d_moving = d_stack_ + moving_index * pixels_per_frame_;
    const auto metrics = score_star_core_matrix_candidates_f32(
        d_reference,
        d_moving,
        matrices,
        static_cast<int>(width_),
        static_cast<int>(height_),
        threshold);

    py::list candidate_metrics;
    for (std::size_t index = 0; index < metrics.size(); ++index) {
      py::dict item;
      item["seed_index"] = static_cast<int>(index);
      item["metrics"] = matrix_candidate_to_dict(
          metrics[index],
          "resident_star_core_bilinear_metric_cuda_candidate");
      candidate_metrics.append(item);
    }

    py::dict result;
    result["candidate_count"] = static_cast<int>(metrics.size());
    result["threshold"] = threshold;
    result["sampled_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["candidate_metrics"] = candidate_metrics;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_star_core_bilinear_metric_cuda";
    return result;
  }

  py::dict refine_matrix_translation_candidates_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      py::object matrices_obj,
      float search_radius_px,
      float coarse_step_px,
      float fine_radius_px,
      float fine_step_px,
      int coarse_sample_stride,
      int final_sample_stride) const {
    require_loaded(reference_index, "resident matrix multi-refine");
    require_loaded(moving_index, "resident matrix multi-refine");
    if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
      throw std::invalid_argument("search radii must be non-negative");
    }
    if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
      throw std::invalid_argument("search steps must be positive");
    }
    if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
      throw std::invalid_argument("sample strides must be positive");
    }
    const auto seed_matrices = parse_matrix_stack(matrices_obj);
    const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
    const int coarse_candidates = static_cast<int>(coarse_offsets.size());
    const auto* d_reference = d_stack_ + reference_index * pixels_per_frame_;
    const auto* d_moving = d_stack_ + moving_index * pixels_per_frame_;
    MatrixCandidateMetrics best;
    bool have_best = false;
    int selected_index = -1;
    py::list seed_results;

    for (std::size_t seed_index = 0; seed_index < seed_matrices.size(); ++seed_index) {
      const auto& base_matrix = seed_matrices[seed_index];
      const MatrixCandidateMetrics coarse_best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          coarse_offsets,
          static_cast<int>(width_),
          static_cast<int>(height_),
          coarse_sample_stride);
      MatrixCandidateMetrics seed_best = coarse_best;
      int fine_candidates = 0;
      if (fine_radius_px > 0.0f) {
        const auto fine_offsets = translation_offsets(coarse_best.dx, coarse_best.dy, fine_radius_px, fine_step_px);
        fine_candidates = static_cast<int>(fine_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            fine_offsets,
            static_cast<int>(width_),
            static_cast<int>(height_),
            final_sample_stride);
      } else if (final_sample_stride != coarse_sample_stride) {
        const std::vector<std::pair<float, float>> final_offsets{{coarse_best.dx, coarse_best.dy}};
        fine_candidates = static_cast<int>(final_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            final_offsets,
            static_cast<int>(width_),
            static_cast<int>(height_),
            final_sample_stride);
      }

      py::dict seed_result;
      seed_result["seed_index"] = static_cast<int>(seed_index);
      seed_result["matrix"] = matrix3x3_to_pylist(seed_best.matrix);
      seed_result["dx_correction"] = seed_best.dx;
      seed_result["dy_correction"] = seed_best.dy;
      seed_result["metrics"] = matrix_candidate_to_dict(seed_best, "matrix_alignment_metrics_cuda_candidate_grid");
      seed_result["coarse_candidates"] = coarse_candidates;
      seed_result["fine_candidates"] = fine_candidates;
      seed_results.append(seed_result);

      if (!have_best || better_matrix_metric(seed_best, best)) {
        best = seed_best;
        selected_index = static_cast<int>(seed_index);
        have_best = true;
      }
    }
    if (!have_best) {
      throw std::runtime_error("resident matrix multi-refine produced no candidates");
    }
    py::dict result;
    result["matrix"] = matrix3x3_to_pylist(best.matrix);
    result["dx_correction"] = best.dx;
    result["dy_correction"] = best.dy;
    result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
    result["selected_index"] = selected_index;
    result["seed_count"] = static_cast<int>(seed_matrices.size());
    result["seed_results"] = seed_results;
    result["coarse_candidates_per_seed"] = coarse_candidates;
    result["search_radius_px"] = search_radius_px;
    result["coarse_step_px"] = coarse_step_px;
    result["fine_radius_px"] = fine_radius_px;
    result["fine_step_px"] = fine_step_px;
    result["coarse_sample_stride"] = coarse_sample_stride;
    result["final_sample_stride"] = final_sample_stride;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_cuda_matrix_metric_translation_multi_seed_refine_grid";
    return result;
  }

  py::list refine_matrix_translation_candidates_batch_to_reference(
      std::size_t reference_index,
      const std::vector<std::size_t>& moving_indices,
      py::object matrices_obj,
      float search_radius_px,
      float coarse_step_px,
      float fine_radius_px,
      float fine_step_px,
      int coarse_sample_stride,
      int final_sample_stride) const {
    require_loaded(reference_index, "resident matrix batch refine");
    if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
      throw std::invalid_argument("search radii must be non-negative");
    }
    if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
      throw std::invalid_argument("search steps must be positive");
    }
    if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
      throw std::invalid_argument("sample strides must be positive");
    }
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (moving_indices.empty()) {
      return py::list();
    }
    if (matrices.size() != moving_indices.size()) {
      throw std::invalid_argument("batch refine requires one seed matrix per moving frame");
    }
    for (const auto moving_index : moving_indices) {
      require_loaded(moving_index, "resident matrix batch refine");
    }
    const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
    const int coarse_candidates = static_cast<int>(coarse_offsets.size());
    const int fine_candidate_capacity =
        fine_radius_px > 0.0f ? static_cast<int>(translation_offsets(0.0f, 0.0f, fine_radius_px, fine_step_px).size())
                              : final_sample_stride != coarse_sample_stride ? 1
                                                                            : 0;
    const std::size_t moving_count = moving_indices.size();
    const std::size_t coarse_total_candidate_capacity =
        moving_count * static_cast<std::size_t>(coarse_candidates);
    const std::size_t fine_total_candidate_capacity =
        moving_count * static_cast<std::size_t>(fine_candidate_capacity);
    const std::size_t workspace_candidate_capacity_size =
        std::max(coarse_total_candidate_capacity, fine_total_candidate_capacity);
    if (workspace_candidate_capacity_size > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("too many resident matrix refine candidates for one native batch");
    }
    const int workspace_candidate_capacity = static_cast<int>(workspace_candidate_capacity_size);
    const std::size_t workspace_bytes = matrix_refine_workspace_bytes(workspace_candidate_capacity);
    const auto* d_reference = d_stack_ + reference_index * pixels_per_frame_;
    py::list results;
    MatrixRefineWorkspace workspace;
    workspace.candidate_capacity = workspace_candidate_capacity;
    double native_coarse_total_s = 0.0;
    double native_fine_total_s = 0.0;

    try {
      check_cuda(
          cudaMalloc(
              &workspace.d_inverses,
              static_cast<std::size_t>(workspace_candidate_capacity) * 9 * sizeof(float)),
          "cudaMalloc(resident batch matrix refine candidate inverses)");
      check_cuda(
          cudaMalloc(
              &workspace.d_partial_stats,
              static_cast<std::size_t>(workspace_candidate_capacity) * 7 * sizeof(double)),
          "cudaMalloc(resident batch matrix refine partial stats)");
      check_cuda(
          cudaMalloc(
              &workspace.d_partial_count,
              static_cast<std::size_t>(workspace_candidate_capacity) * sizeof(unsigned long long)),
          "cudaMalloc(resident batch matrix refine partial count)");
      check_cuda(
          cudaMalloc(
              &workspace.d_moving_frame_indices,
              static_cast<std::size_t>(workspace_candidate_capacity) * sizeof(int)),
          "cudaMalloc(resident batch matrix refine moving frame indices)");
    } catch (...) {
      cudaFree(workspace.d_inverses);
      cudaFree(workspace.d_partial_stats);
      cudaFree(workspace.d_partial_count);
      cudaFree(workspace.d_moving_frame_indices);
      throw;
    }
    try {
      const std::vector<std::vector<std::pair<float, float>>> coarse_offsets_by_frame(moving_count, coarse_offsets);
      const auto coarse_start = Clock::now();
      const auto coarse_bests = score_matrix_translation_candidates_batch_f32_workspace(
          d_reference,
          d_stack_,
          pixels_per_frame_,
          moving_indices,
          matrices,
          coarse_offsets_by_frame,
          static_cast<int>(width_),
          static_cast<int>(height_),
          coarse_sample_stride,
          workspace);
      native_coarse_total_s = seconds_since(coarse_start);

      std::vector<std::vector<std::pair<float, float>>> fine_offsets_by_frame(moving_count);
      std::vector<int> fine_candidate_counts(moving_count, 0);
      bool run_fine_metric = false;
      for (std::size_t batch_index = 0; batch_index < moving_indices.size(); ++batch_index) {
        if (fine_radius_px > 0.0f) {
          fine_offsets_by_frame[batch_index] =
              translation_offsets(coarse_bests[batch_index].dx, coarse_bests[batch_index].dy, fine_radius_px, fine_step_px);
          run_fine_metric = true;
        } else if (final_sample_stride != coarse_sample_stride) {
          fine_offsets_by_frame[batch_index] = {{coarse_bests[batch_index].dx, coarse_bests[batch_index].dy}};
          run_fine_metric = true;
        }
        fine_candidate_counts[batch_index] = static_cast<int>(fine_offsets_by_frame[batch_index].size());
      }

      std::vector<MatrixCandidateMetrics> bests = coarse_bests;
      int fine_total_candidates = 0;
      for (const int count : fine_candidate_counts) {
        fine_total_candidates += count;
      }
      if (run_fine_metric) {
        const auto fine_start = Clock::now();
        bests = score_matrix_translation_candidates_batch_f32_workspace(
            d_reference,
            d_stack_,
            pixels_per_frame_,
            moving_indices,
            matrices,
            fine_offsets_by_frame,
            static_cast<int>(width_),
            static_cast<int>(height_),
            final_sample_stride,
            workspace);
        native_fine_total_s = seconds_since(fine_start);
      }

      const double per_frame_coarse_s = native_coarse_total_s / static_cast<double>(moving_count);
      const double per_frame_fine_s =
          run_fine_metric ? native_fine_total_s / static_cast<double>(moving_count) : 0.0;
      const int batch_metric_kernel_launches = run_fine_metric ? 2 : 1;
      const int coarse_total_candidates = static_cast<int>(coarse_total_candidate_capacity);
      const int coarse_stride = coarse_sample_stride > 1 ? coarse_sample_stride : 1;
      const int fine_stride = final_sample_stride > 1 ? final_sample_stride : 1;
      const unsigned long long coarse_sampled_pixels_per_candidate =
          static_cast<unsigned long long>((width_ + coarse_stride - 1) / coarse_stride) *
          static_cast<unsigned long long>((height_ + coarse_stride - 1) / coarse_stride);
      const unsigned long long fine_sampled_pixels_per_candidate =
          static_cast<unsigned long long>((width_ + fine_stride - 1) / fine_stride) *
          static_cast<unsigned long long>((height_ + fine_stride - 1) / fine_stride);
      const unsigned long long coarse_metric_sample_evaluations =
          static_cast<unsigned long long>(coarse_total_candidates) * coarse_sampled_pixels_per_candidate;
      const unsigned long long fine_metric_sample_evaluations =
          static_cast<unsigned long long>(fine_total_candidates) * fine_sampled_pixels_per_candidate;
      const double coarse_metric_megasamples_per_s =
          native_coarse_total_s > 0.0
              ? static_cast<double>(coarse_metric_sample_evaluations) / (native_coarse_total_s * 1.0e6)
              : 0.0;
      const double fine_metric_megasamples_per_s =
          native_fine_total_s > 0.0
              ? static_cast<double>(fine_metric_sample_evaluations) / (native_fine_total_s * 1.0e6)
              : 0.0;

      for (std::size_t batch_index = 0; batch_index < moving_indices.size(); ++batch_index) {
        const std::size_t moving_index = moving_indices[batch_index];
        const MatrixCandidateMetrics& best = bests[batch_index];
        const int fine_candidates = fine_candidate_counts[batch_index];
        py::dict seed_result;
        seed_result["seed_index"] = 0;
        seed_result["matrix"] = matrix3x3_to_pylist(best.matrix);
        seed_result["dx_correction"] = best.dx;
        seed_result["dy_correction"] = best.dy;
        seed_result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
        seed_result["coarse_candidates"] = coarse_candidates;
        seed_result["fine_candidates"] = fine_candidates;

        py::list seed_results;
        seed_results.append(seed_result);

        py::dict result;
        result["matrix"] = matrix3x3_to_pylist(best.matrix);
        result["dx_correction"] = best.dx;
        result["dy_correction"] = best.dy;
        result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
        result["selected_index"] = 0;
        result["seed_count"] = 1;
        result["seed_results"] = seed_results;
        result["coarse_candidates_per_seed"] = coarse_candidates;
        result["search_radius_px"] = search_radius_px;
        result["coarse_step_px"] = coarse_step_px;
        result["fine_radius_px"] = fine_radius_px;
        result["fine_step_px"] = fine_step_px;
        result["coarse_sample_stride"] = coarse_sample_stride;
        result["final_sample_stride"] = final_sample_stride;
        result["reference_index"] = reference_index;
        result["moving_index"] = moving_index;
        result["batch_index"] = static_cast<int>(batch_index);
        result["batch_count"] = static_cast<int>(moving_indices.size());
        result["batch_model"] = "resident_cuda_matrix_metric_translation_batch_refine_grid";
        result["batch_metric_mode"] = "flattened_frame_candidate_grid";
        result["batch_metric_kernel_launches"] = batch_metric_kernel_launches;
        result["metric_workload_model"] = "candidate_count_x_sampled_pixels";
        result["coarse_total_candidates"] = coarse_total_candidates;
        result["fine_total_candidates"] = fine_total_candidates;
        result["coarse_sampled_pixels_per_candidate"] = coarse_sampled_pixels_per_candidate;
        result["fine_sampled_pixels_per_candidate"] = fine_sampled_pixels_per_candidate;
        result["coarse_metric_sample_evaluations"] = coarse_metric_sample_evaluations;
        result["fine_metric_sample_evaluations"] = fine_metric_sample_evaluations;
        result["coarse_metric_megasamples_per_s"] = coarse_metric_megasamples_per_s;
        result["fine_metric_megasamples_per_s"] = fine_metric_megasamples_per_s;
        result["workspace_mode"] = "shared_flattened_candidate_metric_buffers";
        result["workspace_candidate_capacity"] = workspace_candidate_capacity;
        result["workspace_bytes"] = static_cast<unsigned long long>(workspace_bytes);
        result["coarse_metric_s"] = per_frame_coarse_s;
        result["fine_metric_s"] = per_frame_fine_s;
        result["native_coarse_total_s"] = native_coarse_total_s;
        result["native_fine_total_s"] = native_fine_total_s;
        result["model"] = "resident_cuda_matrix_metric_translation_multi_seed_refine_grid";
        results.append(result);
      }
    } catch (...) {
      cudaFree(workspace.d_inverses);
      cudaFree(workspace.d_partial_stats);
      cudaFree(workspace.d_partial_count);
      cudaFree(workspace.d_moving_frame_indices);
      throw;
    }
    cudaFree(workspace.d_inverses);
    cudaFree(workspace.d_partial_stats);
    cudaFree(workspace.d_partial_count);
    cudaFree(workspace.d_moving_frame_indices);
    return results;
  }

  py::dict estimate_translation_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      int max_shift_x,
      int max_shift_y,
      int sample_stride) const {
    require_loaded(reference_index, "resident translation search");
    require_loaded(moving_index, "resident translation search");
    if (max_shift_x < 0 || max_shift_y < 0) {
      throw std::invalid_argument("max shifts must be non-negative");
    }
    if (sample_stride <= 0) {
      throw std::invalid_argument("sample_stride must be positive");
    }
    const int shift_count = (2 * max_shift_x + 1) * (2 * max_shift_y + 1);
    float* d_scores = nullptr;
    int* d_best_dx = nullptr;
    int* d_best_dy = nullptr;
    float* d_best_score = nullptr;
    int best_dx = 0;
    int best_dy = 0;
    float best_score = 0.0f;
    try {
      check_cuda(cudaMalloc(&d_scores, static_cast<std::size_t>(shift_count) * sizeof(float)), "cudaMalloc(resident translation scores)");
      check_cuda(cudaMalloc(&d_best_dx, sizeof(int)), "cudaMalloc(resident translation best dx)");
      check_cuda(cudaMalloc(&d_best_dy, sizeof(int)), "cudaMalloc(resident translation best dy)");
      check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(resident translation best score)");
      glass_estimate_translation_search_f32_launch(
          d_stack_ + reference_index * pixels_per_frame_,
          d_stack_ + moving_index * pixels_per_frame_,
          d_scores,
          d_best_dx,
          d_best_dy,
          d_best_score,
          static_cast<int>(width_),
          static_cast<int>(height_),
          max_shift_x,
          max_shift_y,
          sample_stride);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.estimate_translation_to_reference kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.estimate_translation_to_reference synchronize");
      check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(resident best dx)");
      check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(resident best dy)");
      check_cuda(
          cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident best score)");
    } catch (...) {
      cudaFree(d_scores);
      cudaFree(d_best_dx);
      cudaFree(d_best_dy);
      cudaFree(d_best_score);
      throw;
    }
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);

    py::dict result;
    result["dx"] = best_dx;
    result["dy"] = best_dy;
    result["score"] = best_score;
    result["search_count"] = shift_count;
    result["sample_stride"] = sample_stride;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_translation_integer_ncc";
    return result;
  }

  py::dict estimate_translation_subpixel_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      float center_dx,
      float center_dy,
      int radius_steps,
      float step,
      int sample_stride) const {
    require_loaded(reference_index, "resident subpixel translation search");
    require_loaded(moving_index, "resident subpixel translation search");
    if (radius_steps < 0) {
      throw std::invalid_argument("radius_steps must be non-negative");
    }
    if (step <= 0.0f) {
      throw std::invalid_argument("step must be positive");
    }
    if (sample_stride <= 0) {
      throw std::invalid_argument("sample_stride must be positive");
    }
    const int candidate_count = (2 * radius_steps + 1) * (2 * radius_steps + 1);
    float* d_scores = nullptr;
    float* d_best_dx = nullptr;
    float* d_best_dy = nullptr;
    float* d_best_score = nullptr;
    float best_dx = 0.0f;
    float best_dy = 0.0f;
    float best_score = 0.0f;
    try {
      check_cuda(cudaMalloc(&d_scores, static_cast<std::size_t>(candidate_count) * sizeof(float)), "cudaMalloc(resident subpixel scores)");
      check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(resident subpixel best dx)");
      check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(resident subpixel best dy)");
      check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(resident subpixel best score)");
      glass_estimate_translation_subpixel_ncc_f32_launch(
          d_stack_ + reference_index * pixels_per_frame_,
          d_stack_ + moving_index * pixels_per_frame_,
          d_scores,
          d_best_dx,
          d_best_dy,
          d_best_score,
          static_cast<int>(width_),
          static_cast<int>(height_),
          center_dx,
          center_dy,
          radius_steps,
          step,
          sample_stride);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.estimate_translation_subpixel_to_reference kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.estimate_translation_subpixel_to_reference synchronize");
      check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident subpixel best dx)");
      check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident subpixel best dy)");
      check_cuda(
          cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident subpixel best score)");
    } catch (...) {
      cudaFree(d_scores);
      cudaFree(d_best_dx);
      cudaFree(d_best_dy);
      cudaFree(d_best_score);
      throw;
    }
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);

    py::dict result;
    result["dx"] = best_dx;
    result["dy"] = best_dy;
    result["score"] = best_score;
    result["candidate_count"] = candidate_count;
    result["center_dx"] = center_dx;
    result["center_dy"] = center_dy;
    result["radius_steps"] = radius_steps;
    result["step"] = step;
    result["sample_stride"] = sample_stride;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_translation_subpixel_ncc";
    return result;
  }

  py::dict frame_global_stats(std::size_t index) const {
    require_loaded(index, "global frame statistics");
    constexpr int threads = 256;
    const int blocks = std::min<int>(
        4096,
        static_cast<int>((pixels_per_frame_ + static_cast<std::size_t>(threads) - 1) / threads));
    double* d_partial_sum = nullptr;
    double* d_partial_sum2 = nullptr;
    unsigned long long* d_partial_count = nullptr;
    std::vector<double> partial_sum(static_cast<std::size_t>(blocks), 0.0);
    std::vector<double> partial_sum2(static_cast<std::size_t>(blocks), 0.0);
    std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);
    try {
      check_cuda(cudaMalloc(&d_partial_sum, partial_sum.size() * sizeof(double)), "cudaMalloc(resident stats sum)");
      check_cuda(cudaMalloc(&d_partial_sum2, partial_sum2.size() * sizeof(double)), "cudaMalloc(resident stats sum2)");
      check_cuda(
          cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident stats count)");
      glass_frame_sum_stats_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_partial_sum,
          d_partial_sum2,
          d_partial_count,
          pixels_per_frame_,
          blocks);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.frame_global_stats kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.frame_global_stats synchronize");
      check_cuda(
          cudaMemcpy(partial_sum.data(), d_partial_sum, partial_sum.size() * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident stats sum)");
      check_cuda(
          cudaMemcpy(partial_sum2.data(), d_partial_sum2, partial_sum2.size() * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident stats sum2)");
      check_cuda(
          cudaMemcpy(
              partial_count.data(),
              d_partial_count,
              partial_count.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident stats count)");
    } catch (...) {
      cudaFree(d_partial_sum);
      cudaFree(d_partial_sum2);
      cudaFree(d_partial_count);
      throw;
    }
    cudaFree(d_partial_sum);
    cudaFree(d_partial_sum2);
    cudaFree(d_partial_count);

    double sum = 0.0;
    double sum2 = 0.0;
    unsigned long long count = 0;
    for (int i = 0; i < blocks; ++i) {
      sum += partial_sum[static_cast<std::size_t>(i)];
      sum2 += partial_sum2[static_cast<std::size_t>(i)];
      count += partial_count[static_cast<std::size_t>(i)];
    }
    const double mean = count > 0 ? sum / static_cast<double>(count) : 0.0;
    double variance = 0.0;
    if (count > 0) {
      variance = sum2 / static_cast<double>(count) - mean * mean;
      if (variance < 0.0) {
        variance = 0.0;
      }
    }
    py::dict result;
    result["mean"] = mean;
    result["std"] = std::sqrt(variance);
    result["valid_pixels"] = count;
    result["total_pixels"] = pixels_per_frame_;
    result["nonfinite_pixels"] = pixels_per_frame_ - static_cast<std::size_t>(count);
    result["model"] = "resident_global_mean_std";
    return result;
  }

  py::dict frame_pair_grid_stats(
      std::size_t reference_index,
      std::size_t source_index,
      int tile_height,
      int tile_width) const {
    require_loaded(reference_index, "grid local normalization reference statistics");
    require_loaded(source_index, "grid local normalization source statistics");
    if (tile_height <= 0 || tile_width <= 0) {
      throw std::invalid_argument("tile dimensions must be positive");
    }
    const int grid_rows =
        (static_cast<int>(height_) + tile_height - 1) / tile_height;
    const int grid_cols =
        (static_cast<int>(width_) + tile_width - 1) / tile_width;
    if (grid_rows <= 0 || grid_cols <= 0) {
      throw std::runtime_error("resident frame shape produced an empty local-normalization grid");
    }
    const std::size_t grid_count =
        static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
    double* d_source_sum = nullptr;
    double* d_source_sum2 = nullptr;
    double* d_reference_sum = nullptr;
    double* d_reference_sum2 = nullptr;
    unsigned long long* d_count = nullptr;
    std::vector<double> source_sum(grid_count, 0.0);
    std::vector<double> source_sum2(grid_count, 0.0);
    std::vector<double> reference_sum(grid_count, 0.0);
    std::vector<double> reference_sum2(grid_count, 0.0);
    std::vector<unsigned long long> count(grid_count, 0);
    try {
      check_cuda(cudaMalloc(&d_source_sum, grid_count * sizeof(double)), "cudaMalloc(resident grid source sum)");
      check_cuda(cudaMalloc(&d_source_sum2, grid_count * sizeof(double)), "cudaMalloc(resident grid source sum2)");
      check_cuda(
          cudaMalloc(&d_reference_sum, grid_count * sizeof(double)),
          "cudaMalloc(resident grid reference sum)");
      check_cuda(
          cudaMalloc(&d_reference_sum2, grid_count * sizeof(double)),
          "cudaMalloc(resident grid reference sum2)");
      check_cuda(
          cudaMalloc(&d_count, grid_count * sizeof(unsigned long long)),
          "cudaMalloc(resident grid valid count)");
      glass_pair_grid_sum_stats_f32_launch(
          d_stack_ + source_index * pixels_per_frame_,
          d_stack_ + reference_index * pixels_per_frame_,
          d_source_sum,
          d_source_sum2,
          d_reference_sum,
          d_reference_sum2,
          d_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          tile_width,
          tile_height,
          grid_cols,
          grid_rows);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.frame_pair_grid_stats kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.frame_pair_grid_stats synchronize");
      check_cuda(
          cudaMemcpy(source_sum.data(), d_source_sum, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid source sum)");
      check_cuda(
          cudaMemcpy(source_sum2.data(), d_source_sum2, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid source sum2)");
      check_cuda(
          cudaMemcpy(reference_sum.data(), d_reference_sum, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid reference sum)");
      check_cuda(
          cudaMemcpy(reference_sum2.data(), d_reference_sum2, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid reference sum2)");
      check_cuda(
          cudaMemcpy(count.data(), d_count, grid_count * sizeof(unsigned long long), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid valid count)");
    } catch (...) {
      cudaFree(d_source_sum);
      cudaFree(d_source_sum2);
      cudaFree(d_reference_sum);
      cudaFree(d_reference_sum2);
      cudaFree(d_count);
      throw;
    }
    cudaFree(d_source_sum);
    cudaFree(d_source_sum2);
    cudaFree(d_reference_sum);
    cudaFree(d_reference_sum2);
    cudaFree(d_count);

    py::array_t<float> source_mean({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<float> source_std({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<float> reference_mean({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<float> reference_std({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<unsigned long long> valid_pixels(
        {static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    float* source_mean_ptr = static_cast<float*>(source_mean.request().ptr);
    float* source_std_ptr = static_cast<float*>(source_std.request().ptr);
    float* reference_mean_ptr = static_cast<float*>(reference_mean.request().ptr);
    float* reference_std_ptr = static_cast<float*>(reference_std.request().ptr);
    auto* valid_ptr = static_cast<unsigned long long*>(valid_pixels.request().ptr);
    unsigned long long total_count = 0;
    for (std::size_t i = 0; i < grid_count; ++i) {
      const unsigned long long c = count[i];
      total_count += c;
      valid_ptr[i] = c;
      if (c == 0) {
        source_mean_ptr[i] = 0.0f;
        source_std_ptr[i] = 0.0f;
        reference_mean_ptr[i] = 0.0f;
        reference_std_ptr[i] = 0.0f;
        continue;
      }
      const double inv_count = 1.0 / static_cast<double>(c);
      const double s_mean = source_sum[i] * inv_count;
      const double r_mean = reference_sum[i] * inv_count;
      double s_var = source_sum2[i] * inv_count - s_mean * s_mean;
      double r_var = reference_sum2[i] * inv_count - r_mean * r_mean;
      if (s_var < 0.0) {
        s_var = 0.0;
      }
      if (r_var < 0.0) {
        r_var = 0.0;
      }
      source_mean_ptr[i] = static_cast<float>(s_mean);
      source_std_ptr[i] = static_cast<float>(std::sqrt(s_var));
      reference_mean_ptr[i] = static_cast<float>(r_mean);
      reference_std_ptr[i] = static_cast<float>(std::sqrt(r_var));
    }

    py::dict result;
    result["source_mean"] = source_mean;
    result["source_std"] = source_std;
    result["reference_mean"] = reference_mean;
    result["reference_std"] = reference_std;
    result["valid_pixels"] = valid_pixels;
    result["grid_rows"] = grid_rows;
    result["grid_cols"] = grid_cols;
    result["tile_height"] = tile_height;
    result["tile_width"] = tile_width;
    result["valid_pixel_total"] = total_count;
    result["model"] = "resident_grid_pair_mean_std";
    return result;
  }

  void apply_global_normalization_frame(std::size_t index, float scale, float offset) {
    require_loaded(index, "global local normalization");
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    float* d_output = nullptr;
    try {
      check_cuda(cudaMalloc(&d_output, frame_bytes), "cudaMalloc(resident global normalization output)");
      glass_local_norm_apply_f32_launch(d_stack_ + index * pixels_per_frame_, d_output, pixels_per_frame_, scale, offset);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_global_normalization_frame kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_global_normalization_frame synchronize");
      check_cuda(
          cudaMemcpy(d_stack_ + index * pixels_per_frame_, d_output, frame_bytes, cudaMemcpyDeviceToDevice),
          "cudaMemcpy(resident global normalized frame)");
    } catch (...) {
      cudaFree(d_output);
      throw;
    }
    cudaFree(d_output);
  }

  void apply_grid_normalization_frame(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> scales,
      py::array_t<float, py::array::c_style | py::array::forcecast> offsets,
      int tile_height,
      int tile_width) {
    require_loaded(index, "grid local normalization");
    const py::buffer_info scales_info = scales.request();
    const py::buffer_info offsets_info = offsets.request();
    if (scales_info.ndim != 2 || offsets_info.ndim != 2) {
      throw std::invalid_argument("scales and offsets must have shape (grid_rows, grid_cols)");
    }
    if (scales_info.shape[0] != offsets_info.shape[0] || scales_info.shape[1] != offsets_info.shape[1]) {
      throw std::invalid_argument("scales and offsets shapes must match");
    }
    if (tile_height <= 0 || tile_width <= 0) {
      throw std::invalid_argument("tile dimensions must be positive");
    }
    const int grid_rows = static_cast<int>(scales_info.shape[0]);
    const int grid_cols = static_cast<int>(scales_info.shape[1]);
    if (grid_rows <= 0 || grid_cols <= 0) {
      throw std::invalid_argument("coefficient grid must not be empty");
    }
    const int expected_rows =
        (static_cast<int>(height_) + tile_height - 1) / tile_height;
    const int expected_cols =
        (static_cast<int>(width_) + tile_width - 1) / tile_width;
    if (grid_rows != expected_rows || grid_cols != expected_cols) {
      throw std::invalid_argument("coefficient grid shape does not match resident frame shape and tile dimensions");
    }
    const std::size_t coefficient_count =
        static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    float* d_output = nullptr;
    float* d_scales = nullptr;
    float* d_offsets = nullptr;
    try {
      check_cuda(cudaMalloc(&d_output, frame_bytes), "cudaMalloc(resident grid normalization output)");
      check_cuda(
          cudaMalloc(&d_scales, coefficient_count * sizeof(float)),
          "cudaMalloc(resident grid normalization scales)");
      check_cuda(
          cudaMalloc(&d_offsets, coefficient_count * sizeof(float)),
          "cudaMalloc(resident grid normalization offsets)");
      check_cuda(
          cudaMemcpy(d_scales, scales_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident grid normalization scales)");
      check_cuda(
          cudaMemcpy(d_offsets, offsets_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident grid normalization offsets)");
      glass_local_norm_apply_grid_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_output,
          d_scales,
          d_offsets,
          static_cast<int>(width_),
          static_cast<int>(height_),
          tile_width,
          tile_height,
          grid_cols,
          grid_rows);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_grid_normalization_frame kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_grid_normalization_frame synchronize");
      check_cuda(
          cudaMemcpy(d_stack_ + index * pixels_per_frame_, d_output, frame_bytes, cudaMemcpyDeviceToDevice),
          "cudaMemcpy(resident grid normalized frame)");
    } catch (...) {
      cudaFree(d_output);
      cudaFree(d_scales);
      cudaFree(d_offsets);
      throw;
    }
    cudaFree(d_output);
    cudaFree(d_scales);
    cudaFree(d_offsets);
  }

  py::array_t<unsigned char> star_local_max_mask(std::size_t index, float threshold) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    py::array_t<unsigned char> mask({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info mask_info = mask.request();
    unsigned char* d_mask = nullptr;
    try {
      check_cuda(cudaMalloc(&d_mask, pixels_per_frame_ * sizeof(unsigned char)), "cudaMalloc(resident star mask)");
      glass_star_local_max_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_mask,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_local_max_mask kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_local_max_mask synchronize");
      check_cuda(
          cudaMemcpy(mask_info.ptr, d_mask, pixels_per_frame_ * sizeof(unsigned char), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident star mask)");
    } catch (...) {
      cudaFree(d_mask);
      throw;
    }
    cudaFree(d_mask);
    return mask;
  }

  py::dict star_candidates(std::size_t index, float threshold, int max_candidates) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (max_candidates <= 0) {
      throw std::invalid_argument("max_candidates must be positive");
    }
    py::array_t<float> xs({max_candidates});
    py::array_t<float> ys({max_candidates});
    py::array_t<float> fluxes({max_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int total_count = 0;
    try {
      check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star xs)");
      check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
          "cudaMalloc(star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(star count)");
      glass_star_candidates_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_xs,
          d_ys,
          d_fluxes,
          d_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold,
          max_candidates);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_candidates synchronize");
      check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(star count)");
      const int stored_count = total_count < max_candidates ? total_count : max_candidates;
      check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star xs)");
      check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star ys)");
      check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      return result;
    } catch (...) {
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      throw;
    }
  }

  py::dict star_top_candidates(std::size_t index, float threshold, int max_candidates) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (max_candidates <= 0) {
      throw std::invalid_argument("max_candidates must be positive");
    }
    py::array_t<float> xs({max_candidates});
    py::array_t<float> ys({max_candidates});
    py::array_t<float> fluxes({max_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_lock = nullptr;
    int total_count = 0;
    try {
      check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star xs)");
      check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
          "cudaMalloc(top star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(top star count)");
      check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(top star lock)");
      glass_star_top_candidates_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_xs,
          d_ys,
          d_fluxes,
          d_count,
          d_lock,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold,
          max_candidates);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_top_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_top_candidates synchronize");
      check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(top star count)");
      const int stored_count = total_count < max_candidates ? total_count : max_candidates;
      check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star xs)");
      check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star ys)");
      check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      return result;
    } catch (...) {
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      throw;
    }
  }

  py::dict star_top_nms_candidates(
      std::size_t index,
      float threshold,
      int scan_candidates,
      int max_output_candidates,
      float min_separation_px) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (scan_candidates <= 0 || max_output_candidates <= 0) {
      throw std::invalid_argument("candidate counts must be positive");
    }
    if (scan_candidates < max_output_candidates) {
      throw std::invalid_argument("scan_candidates must be greater than or equal to max_output_candidates");
    }
    if (min_separation_px < 0.0f) {
      throw std::invalid_argument("min_separation_px must be non-negative");
    }
    py::array_t<float> xs({max_output_candidates});
    py::array_t<float> ys({max_output_candidates});
    py::array_t<float> fluxes({max_output_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_scan_xs = nullptr;
    float* d_scan_ys = nullptr;
    float* d_scan_fluxes = nullptr;
    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_lock = nullptr;
    int* d_stored_count = nullptr;
    int total_count = 0;
    int stored_count = 0;
    try {
      check_cuda(
          cudaMalloc(&d_scan_xs, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan xs)");
      check_cuda(
          cudaMalloc(&d_scan_ys, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan ys)");
      check_cuda(
          cudaMalloc(&d_scan_fluxes, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan fluxes)");
      check_cuda(
          cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star xs)");
      check_cuda(
          cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(resident top nms star count)");
      check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(resident top nms star lock)");
      check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(resident top nms stored count)");
      glass_star_top_nms_candidates_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_scan_xs,
          d_scan_ys,
          d_scan_fluxes,
          d_xs,
          d_ys,
          d_fluxes,
          d_count,
          d_lock,
          d_stored_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold,
          scan_candidates,
          max_output_candidates,
          min_separation_px);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_top_nms_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_top_nms_candidates synchronize");
      check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(resident top nms count)");
      check_cuda(
          cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms stored count)");
      check_cuda(
          cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms star xs)");
      check_cuda(
          cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms star ys)");
      check_cuda(
          cudaMemcpy(
              flux_info.ptr,
              d_fluxes,
              static_cast<std::size_t>(stored_count) * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["scan_candidates"] = scan_candidates;
      result["max_output_candidates"] = max_output_candidates;
      result["min_separation_px"] = min_separation_px;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_scan_xs);
      cudaFree(d_scan_ys);
      cudaFree(d_scan_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      cudaFree(d_stored_count);
      return result;
    } catch (...) {
      cudaFree(d_scan_xs);
      cudaFree(d_scan_ys);
      cudaFree(d_scan_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      cudaFree(d_stored_count);
      throw;
    }
  }

  py::dict star_grid_top_nms_candidates_impl(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      bool deterministic) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (grid_cols <= 0 || grid_rows <= 0 || candidates_per_cell <= 0 || max_output_candidates <= 0) {
      throw std::invalid_argument("grid dimensions and candidate counts must be positive");
    }
    if (min_separation_px < 0.0f) {
      throw std::invalid_argument("min_separation_px must be non-negative");
    }
    const int cell_count = grid_cols * grid_rows;
    const int grid_capacity = cell_count * candidates_per_cell;
    py::array_t<float> xs({max_output_candidates});
    py::array_t<float> ys({max_output_candidates});
    py::array_t<float> fluxes({max_output_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_grid_xs = nullptr;
    float* d_grid_ys = nullptr;
    float* d_grid_fluxes = nullptr;
    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_locks = nullptr;
    int* d_cell_counts = nullptr;
    int* d_stored_count = nullptr;
    int total_count = 0;
    int stored_count = 0;
    try {
      check_cuda(
          cudaMalloc(&d_grid_xs, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident grid top nms grid xs)");
      check_cuda(
          cudaMalloc(&d_grid_ys, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident grid top nms grid ys)");
      check_cuda(
          cudaMalloc(&d_grid_fluxes, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident grid top nms grid fluxes)");
      check_cuda(
          cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident grid top nms star xs)");
      check_cuda(
          cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident grid top nms star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident grid top nms star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(resident grid top nms star count)");
      check_cuda(
          cudaMalloc(&d_locks, static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident grid top nms locks)");
      check_cuda(
          cudaMalloc(&d_cell_counts, static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident grid top nms cell counts)");
      check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(resident grid top nms stored count)");
      if (deterministic) {
        glass_star_grid_top_nms_candidates_deterministic_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_grid_xs,
            d_grid_ys,
            d_grid_fluxes,
            d_xs,
            d_ys,
            d_fluxes,
            d_count,
            d_stored_count,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows,
            candidates_per_cell,
            max_output_candidates,
            min_separation_px);
      } else {
        glass_star_grid_top_nms_candidates_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_grid_xs,
            d_grid_ys,
            d_grid_fluxes,
            d_xs,
            d_ys,
            d_fluxes,
            d_count,
            d_locks,
            d_cell_counts,
            d_stored_count,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows,
            candidates_per_cell,
            max_output_candidates,
            min_separation_px);
      }
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_grid_top_nms_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_grid_top_nms_candidates synchronize");
      check_cuda(
          cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms count)");
      check_cuda(
          cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms stored count)");
      check_cuda(
          cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms star xs)");
      check_cuda(
          cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms star ys)");
      check_cuda(
          cudaMemcpy(
              flux_info.ptr,
              d_fluxes,
              static_cast<std::size_t>(stored_count) * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["grid_cols"] = grid_cols;
      result["grid_rows"] = grid_rows;
      result["candidates_per_cell"] = candidates_per_cell;
      result["max_output_candidates"] = max_output_candidates;
      result["min_separation_px"] = min_separation_px;
      result["catalog_sort_mode"] = grid_catalog_sort_mode(grid_capacity);
      result["catalog_topk_mode"] = grid_catalog_topk_mode(deterministic, candidates_per_cell);
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_grid_xs);
      cudaFree(d_grid_ys);
      cudaFree(d_grid_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      return result;
    } catch (...) {
      cudaFree(d_grid_xs);
      cudaFree(d_grid_ys);
      cudaFree(d_grid_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      throw;
    }
  }

  py::dict star_grid_top_nms_candidates(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_impl(
        index, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, false);
  }

  py::dict star_grid_top_nms_candidates_deterministic(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_impl(
        index, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, true);
  }

  py::list star_grid_top_nms_candidates_batch_impl(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      bool deterministic) const {
    if (grid_cols <= 0 || grid_rows <= 0 || candidates_per_cell <= 0 || max_output_candidates <= 0) {
      throw std::invalid_argument("grid dimensions and candidate counts must be positive");
    }
    if (min_separation_px < 0.0f) {
      throw std::invalid_argument("min_separation_px must be non-negative");
    }
    for (const std::size_t index : indices) {
      require_index(index);
      if (!loaded_[index]) {
        throw std::runtime_error("resident frame must be loaded before batched star detection");
      }
    }

    const int cell_count = grid_cols * grid_rows;
    const int grid_capacity = cell_count * candidates_per_cell;
    py::list results;
    float* d_grid_xs = nullptr;
    float* d_grid_ys = nullptr;
    float* d_grid_fluxes = nullptr;
    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_locks = nullptr;
    int* d_cell_counts = nullptr;
    int* d_stored_count = nullptr;
    try {
      check_cuda(
          cudaMalloc(&d_grid_xs, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident batch grid top nms grid xs)");
      check_cuda(
          cudaMalloc(&d_grid_ys, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident batch grid top nms grid ys)");
      check_cuda(
          cudaMalloc(&d_grid_fluxes, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident batch grid top nms grid fluxes)");
      check_cuda(
          cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident batch grid top nms star xs)");
      check_cuda(
          cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident batch grid top nms star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident batch grid top nms star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(resident batch grid top nms star count)");
      check_cuda(
          cudaMalloc(&d_locks, static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident batch grid top nms locks)");
      check_cuda(
          cudaMalloc(&d_cell_counts, static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident batch grid top nms cell counts)");
      check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(resident batch grid top nms stored count)");

      for (const std::size_t index : indices) {
        py::array_t<float> xs({max_output_candidates});
        py::array_t<float> ys({max_output_candidates});
        py::array_t<float> fluxes({max_output_candidates});
        const py::buffer_info xs_info = xs.request();
        const py::buffer_info ys_info = ys.request();
        const py::buffer_info flux_info = fluxes.request();
        int total_count = 0;
        int stored_count = 0;

        const auto enqueue_start = std::chrono::steady_clock::now();
        if (deterministic) {
          glass_star_grid_top_nms_candidates_deterministic_f32_launch(
              d_stack_ + index * pixels_per_frame_,
              d_grid_xs,
              d_grid_ys,
              d_grid_fluxes,
              d_xs,
              d_ys,
              d_fluxes,
              d_count,
              d_stored_count,
              static_cast<int>(width_),
              static_cast<int>(height_),
              threshold,
              grid_cols,
              grid_rows,
              candidates_per_cell,
              max_output_candidates,
              min_separation_px);
        } else {
          glass_star_grid_top_nms_candidates_f32_launch(
              d_stack_ + index * pixels_per_frame_,
              d_grid_xs,
              d_grid_ys,
              d_grid_fluxes,
              d_xs,
              d_ys,
              d_fluxes,
              d_count,
              d_locks,
              d_cell_counts,
              d_stored_count,
              static_cast<int>(width_),
              static_cast<int>(height_),
              threshold,
              grid_cols,
              grid_rows,
              candidates_per_cell,
              max_output_candidates,
              min_separation_px);
        }
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_grid_top_nms_candidates_batch kernel launch");
        const auto enqueue_end = std::chrono::steady_clock::now();
        check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_grid_top_nms_candidates_batch synchronize");
        const auto sync_end = std::chrono::steady_clock::now();
        check_cuda(
            cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid top nms count)");
        check_cuda(
            cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid top nms stored count)");
        const auto count_download_end = std::chrono::steady_clock::now();
        check_cuda(
            cudaMemcpy(
                xs_info.ptr,
                d_xs,
                static_cast<std::size_t>(stored_count) * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid top nms star xs)");
        check_cuda(
            cudaMemcpy(
                ys_info.ptr,
                d_ys,
                static_cast<std::size_t>(stored_count) * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid top nms star ys)");
        check_cuda(
            cudaMemcpy(
                flux_info.ptr,
                d_fluxes,
                static_cast<std::size_t>(stored_count) * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid top nms star fluxes)");
        const auto catalog_download_end = std::chrono::steady_clock::now();

        const double enqueue_s = std::chrono::duration<double>(enqueue_end - enqueue_start).count();
        const double sync_s = std::chrono::duration<double>(sync_end - enqueue_end).count();
        const double count_download_s =
            std::chrono::duration<double>(count_download_end - sync_end).count();
        const double catalog_download_s =
            std::chrono::duration<double>(catalog_download_end - count_download_end).count();
        const double native_s =
            std::chrono::duration<double>(catalog_download_end - enqueue_start).count();

        py::dict result;
        result["frame_index"] = index;
        result["count"] = total_count;
        result["stored_count"] = stored_count;
        result["grid_cols"] = grid_cols;
        result["grid_rows"] = grid_rows;
        result["candidates_per_cell"] = candidates_per_cell;
        result["max_output_candidates"] = max_output_candidates;
        result["min_separation_px"] = min_separation_px;
        result["catalog_sort_mode"] = grid_catalog_sort_mode(grid_capacity);
        result["catalog_topk_mode"] = grid_catalog_topk_mode(deterministic, candidates_per_cell);
        result["catalog_timing_model"] = "per_frame_launch_sync_download";
        result["catalog_enqueue_s"] = enqueue_s;
        result["catalog_sync_s"] = sync_s;
        result["catalog_count_download_s"] = count_download_s;
        result["catalog_output_download_s"] = catalog_download_s;
        result["catalog_native_s"] = native_s;
        result["x"] = xs[py::slice(0, stored_count, 1)];
        result["y"] = ys[py::slice(0, stored_count, 1)];
        result["flux"] = fluxes[py::slice(0, stored_count, 1)];
        results.append(result);
      }

      cudaFree(d_grid_xs);
      cudaFree(d_grid_ys);
      cudaFree(d_grid_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      return results;
    } catch (...) {
      cudaFree(d_grid_xs);
      cudaFree(d_grid_ys);
      cudaFree(d_grid_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      throw;
    }
  }

  py::list star_grid_top_nms_candidates_batch(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_batch_impl(
        indices, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, false);
  }

  py::list star_grid_top_nms_candidates_batch_deterministic(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_batch_impl(
        indices, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, true);
  }

  py::dict estimate_translation_from_stars_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      float threshold,
      int max_candidates,
      float tolerance_px,
      float max_abs_dx,
      float max_abs_dy,
      float prior_dx,
      float prior_dy,
      float prior_radius_px,
      int grid_cols,
      int grid_rows) const {
    require_loaded(reference_index, "resident star-catalog reference registration");
    require_loaded(moving_index, "resident star-catalog moving registration");
    if (max_candidates <= 0) {
      throw std::invalid_argument("max_candidates must be positive");
    }
    if (tolerance_px < 0.0f) {
      throw std::invalid_argument("tolerance_px must be non-negative");
    }
    if (max_abs_dx < 0.0f) {
      max_abs_dx = -1.0f;
    }
    if (max_abs_dy < 0.0f) {
      max_abs_dy = max_abs_dx;
    }
    if (prior_radius_px < 0.0f) {
      prior_radius_px = -1.0f;
    }
    const bool use_grid_candidates = grid_cols > 0 || grid_rows > 0;
    if (use_grid_candidates && (grid_cols <= 0 || grid_rows <= 0)) {
      throw std::invalid_argument("resident star grid dimensions must both be positive");
    }
    const int catalog_capacity = use_grid_candidates ? grid_cols * grid_rows : max_candidates;

    float* d_reference_x = nullptr;
    float* d_reference_y = nullptr;
    float* d_reference_flux = nullptr;
    float* d_moving_x = nullptr;
    float* d_moving_y = nullptr;
    float* d_moving_flux = nullptr;
    int* d_reference_count = nullptr;
    int* d_moving_count = nullptr;
    int* d_reference_lock = nullptr;
    int* d_moving_lock = nullptr;
    float* d_candidate_dx = nullptr;
    float* d_candidate_dy = nullptr;
    int* d_scores = nullptr;
    float* d_best_dx = nullptr;
    float* d_best_dy = nullptr;
    int* d_best_inliers = nullptr;
    int* d_moving_best_reference = nullptr;
    int* d_reference_best_moving = nullptr;
    float* d_refine_sums = nullptr;
    int* d_mutual_inliers = nullptr;
    float* d_refined_dx = nullptr;
    float* d_refined_dy = nullptr;
    float* d_rms_px = nullptr;
    int reference_total_count = 0;
    int moving_total_count = 0;
    float best_dx = 0.0f;
    float best_dy = 0.0f;
    int best_inliers = 0;
    int mutual_inliers = 0;
    float refined_dx = 0.0f;
    float refined_dy = 0.0f;
    float rms_px = 0.0f;

    try {
      const std::size_t catalog_bytes = static_cast<std::size_t>(catalog_capacity) * sizeof(float);
      check_cuda(cudaMalloc(&d_reference_x, catalog_bytes), "cudaMalloc(resident reference star xs)");
      check_cuda(cudaMalloc(&d_reference_y, catalog_bytes), "cudaMalloc(resident reference star ys)");
      check_cuda(cudaMalloc(&d_reference_flux, catalog_bytes), "cudaMalloc(resident reference star flux)");
      check_cuda(cudaMalloc(&d_moving_x, catalog_bytes), "cudaMalloc(resident moving star xs)");
      check_cuda(cudaMalloc(&d_moving_y, catalog_bytes), "cudaMalloc(resident moving star ys)");
      check_cuda(cudaMalloc(&d_moving_flux, catalog_bytes), "cudaMalloc(resident moving star flux)");
      check_cuda(cudaMalloc(&d_reference_count, sizeof(int)), "cudaMalloc(resident reference star count)");
      check_cuda(cudaMalloc(&d_moving_count, sizeof(int)), "cudaMalloc(resident moving star count)");
      const std::size_t lock_count = use_grid_candidates ? static_cast<std::size_t>(catalog_capacity) : 1ULL;
      check_cuda(cudaMalloc(&d_reference_lock, lock_count * sizeof(int)), "cudaMalloc(resident reference star locks)");
      check_cuda(cudaMalloc(&d_moving_lock, lock_count * sizeof(int)), "cudaMalloc(resident moving star locks)");
      if (use_grid_candidates) {
        glass_star_grid_candidates_f32_launch(
            d_stack_ + reference_index * pixels_per_frame_,
            d_reference_x,
            d_reference_y,
            d_reference_flux,
            d_reference_count,
            d_reference_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows);
        glass_star_grid_candidates_f32_launch(
            d_stack_ + moving_index * pixels_per_frame_,
            d_moving_x,
            d_moving_y,
            d_moving_flux,
            d_moving_count,
            d_moving_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows);
      } else {
        glass_star_top_candidates_f32_launch(
            d_stack_ + reference_index * pixels_per_frame_,
            d_reference_x,
            d_reference_y,
            d_reference_flux,
            d_reference_count,
            d_reference_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            max_candidates);
        glass_star_top_candidates_f32_launch(
            d_stack_ + moving_index * pixels_per_frame_,
            d_moving_x,
            d_moving_y,
            d_moving_flux,
            d_moving_count,
            d_moving_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            max_candidates);
      }
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star-catalog detection kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star-catalog detection synchronize");
      check_cuda(
          cudaMemcpy(&reference_total_count, d_reference_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident reference star count)");
      check_cuda(
          cudaMemcpy(&moving_total_count, d_moving_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident moving star count)");
      const int reference_count = std::min(reference_total_count, catalog_capacity);
      const int moving_count = std::min(moving_total_count, catalog_capacity);
      if (reference_count <= 0 || moving_count <= 0) {
        throw std::runtime_error("resident star-catalog registration found no stars");
      }
      const int pair_count = reference_count * moving_count;
      check_cuda(
          cudaMalloc(&d_candidate_dx, static_cast<std::size_t>(pair_count) * sizeof(float)),
          "cudaMalloc(resident catalog candidate dx)");
      check_cuda(
          cudaMalloc(&d_candidate_dy, static_cast<std::size_t>(pair_count) * sizeof(float)),
          "cudaMalloc(resident catalog candidate dy)");
      check_cuda(
          cudaMalloc(&d_scores, static_cast<std::size_t>(pair_count) * sizeof(int)),
          "cudaMalloc(resident catalog scores)");
      check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(resident catalog best dx)");
      check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(resident catalog best dy)");
      check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(resident catalog best inliers)");
      check_cuda(
          cudaMalloc(&d_moving_best_reference, static_cast<std::size_t>(moving_count) * sizeof(int)),
          "cudaMalloc(resident catalog moving best reference)");
      check_cuda(
          cudaMalloc(&d_reference_best_moving, static_cast<std::size_t>(reference_count) * sizeof(int)),
          "cudaMalloc(resident catalog reference best moving)");
      check_cuda(cudaMalloc(&d_refine_sums, 3 * sizeof(float)), "cudaMalloc(resident catalog refine sums)");
      check_cuda(cudaMalloc(&d_mutual_inliers, sizeof(int)), "cudaMalloc(resident catalog mutual inliers)");
      check_cuda(cudaMalloc(&d_refined_dx, sizeof(float)), "cudaMalloc(resident catalog refined dx)");
      check_cuda(cudaMalloc(&d_refined_dy, sizeof(float)), "cudaMalloc(resident catalog refined dy)");
      check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(resident catalog rms)");
      glass_estimate_translation_from_catalogs_f32_launch(
          d_reference_x,
          d_reference_y,
          d_moving_x,
          d_moving_y,
          d_candidate_dx,
          d_candidate_dy,
          d_scores,
          d_best_dx,
          d_best_dy,
          d_best_inliers,
          d_moving_best_reference,
          d_reference_best_moving,
          d_refine_sums,
          d_mutual_inliers,
          d_refined_dx,
          d_refined_dy,
          d_rms_px,
          reference_count,
          moving_count,
          tolerance_px,
          max_abs_dx,
          max_abs_dy,
          prior_dx,
          prior_dy,
          prior_radius_px);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star-catalog translation kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star-catalog translation synchronize");
      check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog best dx)");
      check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog best dy)");
      check_cuda(
          cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident catalog best inliers)");
      check_cuda(
          cudaMemcpy(&mutual_inliers, d_mutual_inliers, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident catalog mutual inliers)");
      check_cuda(cudaMemcpy(&refined_dx, d_refined_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog refined dx)");
      check_cuda(cudaMemcpy(&refined_dy, d_refined_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog refined dy)");
      check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog rms)");
    } catch (...) {
      cudaFree(d_reference_x);
      cudaFree(d_reference_y);
      cudaFree(d_reference_flux);
      cudaFree(d_moving_x);
      cudaFree(d_moving_y);
      cudaFree(d_moving_flux);
      cudaFree(d_reference_count);
      cudaFree(d_moving_count);
      cudaFree(d_reference_lock);
      cudaFree(d_moving_lock);
      cudaFree(d_candidate_dx);
      cudaFree(d_candidate_dy);
      cudaFree(d_scores);
      cudaFree(d_best_dx);
      cudaFree(d_best_dy);
      cudaFree(d_best_inliers);
      cudaFree(d_moving_best_reference);
      cudaFree(d_reference_best_moving);
      cudaFree(d_refine_sums);
      cudaFree(d_mutual_inliers);
      cudaFree(d_refined_dx);
      cudaFree(d_refined_dy);
      cudaFree(d_rms_px);
      throw;
    }
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_reference_flux);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_moving_flux);
    cudaFree(d_reference_count);
    cudaFree(d_moving_count);
    cudaFree(d_reference_lock);
    cudaFree(d_moving_lock);
    cudaFree(d_candidate_dx);
    cudaFree(d_candidate_dy);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_inliers);
    cudaFree(d_moving_best_reference);
    cudaFree(d_reference_best_moving);
    cudaFree(d_refine_sums);
    cudaFree(d_mutual_inliers);
    cudaFree(d_refined_dx);
    cudaFree(d_refined_dy);
    cudaFree(d_rms_px);

    const int reference_count = std::min(reference_total_count, catalog_capacity);
    const int moving_count = std::min(moving_total_count, catalog_capacity);
    py::dict result;
    result["dx"] = best_dx;
    result["dy"] = best_dy;
    result["inliers"] = best_inliers;
    result["refined_dx"] = refined_dx;
    result["refined_dy"] = refined_dy;
    result["mutual_inliers"] = mutual_inliers;
    result["rms_px"] = rms_px;
    result["candidate_count"] = reference_count * moving_count;
    result["reference_count"] = reference_count;
    result["moving_count"] = moving_count;
    result["reference_total_count"] = reference_total_count;
    result["moving_total_count"] = moving_total_count;
    result["threshold"] = threshold;
    result["max_candidates"] = max_candidates;
    result["catalog_capacity"] = catalog_capacity;
    result["candidate_selection"] = use_grid_candidates ? "grid_brightest_per_cell" : "top_flux";
    result["grid_cols"] = grid_cols;
    result["grid_rows"] = grid_rows;
    result["tolerance_px"] = tolerance_px;
    result["max_abs_dx"] = max_abs_dx;
    result["max_abs_dy"] = max_abs_dy;
    result["prior_dx"] = prior_dx;
    result["prior_dy"] = prior_dy;
    result["prior_radius_px"] = prior_radius_px;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_star_catalog_pair_offset_translation";
    return result;
  }

  py::tuple integrate_mean(py::object weights_obj) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before integration");
    }

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info master_info = master.request();
    const py::buffer_info weight_map_info = weight_map.request();

    float* d_weights = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    try {
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(resident weights)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident master)");
      check_cuda(cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident weight map)");
      check_cuda(
          cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident weights)");
      glass_integrate_resident_weighted_mean_f32_launch(
          d_stack_,
          d_weights,
          d_master,
          d_weight_map,
          frame_count_,
          pixels_per_frame_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_mean kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_mean synchronize");
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident master)");
      check_cuda(
          cudaMemcpy(
              weight_map_info.ptr,
              d_weight_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident weight map)");
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    return py::make_tuple(master, weight_map);
  }

  py::tuple integrate_sigma_clip(
      py::object weights_obj,
      float low_sigma,
      float high_sigma,
      bool winsorize) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before integration");
    }
    if (low_sigma <= 0.0f || high_sigma <= 0.0f) {
      throw std::invalid_argument("sigma thresholds must be positive");
    }

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> coverage_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> low_rejection_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> high_rejection_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info master_info = master.request();
    const py::buffer_info weight_map_info = weight_map.request();
    const py::buffer_info coverage_info = coverage_map.request();
    const py::buffer_info low_info = low_rejection_map.request();
    const py::buffer_info high_info = high_rejection_map.request();

    float* d_weights = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    float* d_coverage_map = nullptr;
    float* d_low_rejection_map = nullptr;
    float* d_high_rejection_map = nullptr;
    try {
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(resident sigma weights)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident sigma master)");
      check_cuda(
          cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident sigma weight map)");
      check_cuda(
          cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident sigma coverage map)");
      check_cuda(
          cudaMalloc(&d_low_rejection_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident sigma low rejection map)");
      check_cuda(
          cudaMalloc(&d_high_rejection_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident sigma high rejection map)");
      check_cuda(
          cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident sigma weights)");
      glass_integrate_resident_sigma_clip_f32_launch(
          d_stack_,
          d_weights,
          d_master,
          d_weight_map,
          d_coverage_map,
          d_low_rejection_map,
          d_high_rejection_map,
          frame_count_,
          pixels_per_frame_,
          low_sigma,
          high_sigma,
          winsorize);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_sigma_clip kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_sigma_clip synchronize");
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident sigma master)");
      check_cuda(
          cudaMemcpy(
              weight_map_info.ptr,
              d_weight_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident sigma weight map)");
      check_cuda(
          cudaMemcpy(
              coverage_info.ptr,
              d_coverage_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident sigma coverage map)");
      check_cuda(
          cudaMemcpy(
              low_info.ptr,
              d_low_rejection_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident sigma low rejection map)");
      check_cuda(
          cudaMemcpy(
              high_info.ptr,
              d_high_rejection_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident sigma high rejection map)");
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_low_rejection_map);
      cudaFree(d_high_rejection_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    cudaFree(d_coverage_map);
    cudaFree(d_low_rejection_map);
    cudaFree(d_high_rejection_map);
    return py::make_tuple(master, weight_map, coverage_map, low_rejection_map, high_rejection_map);
  }

  py::tuple integrate_matrix_warped_mean(
      py::object matrices_obj,
      py::object weights_obj,
      const std::string& interpolation,
      float clamping_threshold) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before fused matrix-warped integration");
    }
    if (interpolation != "bilinear" && interpolation != "lanczos3") {
      throw std::invalid_argument("interpolation must be bilinear or lanczos3");
    }
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (matrices.size() != frame_count_) {
      throw std::invalid_argument("matrices must have shape (frame_count, 3, 3)");
    }

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> coverage_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> geometric_coverage_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info master_info = master.request();
    const py::buffer_info weight_map_info = weight_map.request();
    const py::buffer_info coverage_info = coverage_map.request();
    const py::buffer_info geometric_info = geometric_coverage_map.request();

    const auto total_start = Clock::now();
    const auto inverse_prepare_start = Clock::now();
    std::vector<float> inverse_host(frame_count_ * 9, 0.0f);
    for (std::size_t frame = 0; frame < frame_count_; ++frame) {
      const auto inverse = invert_matrix3x3(matrices[frame]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(frame * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);

    float* d_weights = nullptr;
    float* d_inverses = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    float* d_coverage_map = nullptr;
    float* d_geometric_coverage_map = nullptr;
    double device_alloc_s = 0.0;
    double weights_upload_s = 0.0;
    double inverse_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    double download_s = 0.0;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(fused matrix weights)");
      check_cuda(cudaMalloc(&d_inverses, inverse_host.size() * sizeof(float)), "cudaMalloc(fused matrix inverses)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(fused matrix master)");
      check_cuda(cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)), "cudaMalloc(fused matrix weight map)");
      check_cuda(cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(float)), "cudaMalloc(fused matrix coverage)");
      check_cuda(
          cudaMalloc(&d_geometric_coverage_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(fused matrix geometric coverage)");
      device_alloc_s = seconds_since(alloc_start);

      const auto weights_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice, 0),
          "cudaMemcpyAsync(fused matrix weights)");
      weights_upload_s = seconds_since(weights_upload_start);

      const auto inverse_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              d_inverses,
              inverse_host.data(),
              inverse_host.size() * sizeof(float),
              cudaMemcpyHostToDevice,
              0),
          "cudaMemcpyAsync(fused matrix inverses)");
      inverse_upload_s = seconds_since(inverse_upload_start);

      const auto kernel_start = Clock::now();
      glass_integrate_matrix_warped_mean_f32_launch(
          d_stack_,
          d_weights,
          d_inverses,
          d_master,
          d_weight_map,
          d_coverage_map,
          d_geometric_coverage_map,
          frame_count_,
          static_cast<int>(width_),
          static_cast<int>(height_),
          interpolation == "lanczos3" ? 1 : 0,
          clamping_threshold);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_matrix_warped_mean kernel launch");
      kernel_enqueue_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_matrix_warped_mean synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(fused matrix master)");
      check_cuda(
          cudaMemcpy(
              weight_map_info.ptr,
              d_weight_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(fused matrix weight map)");
      check_cuda(
          cudaMemcpy(
              coverage_info.ptr,
              d_coverage_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(fused matrix coverage map)");
      check_cuda(
          cudaMemcpy(
              geometric_info.ptr,
              d_geometric_coverage_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(fused matrix geometric coverage map)");
      download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_inverses);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_geometric_coverage_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_inverses);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    cudaFree(d_coverage_map);
    cudaFree(d_geometric_coverage_map);

    py::dict timing;
    timing["schema_version"] = 1;
    timing["timing_model"] = "native_fused_matrix_warp_weighted_mean_one_sync";
    timing["interpolation"] = interpolation;
    timing["rejection"] = "none";
    timing["frame_count"] = static_cast<unsigned long long>(frame_count_);
    timing["inverse_prepare_s"] = inverse_prepare_s;
    timing["device_alloc_s"] = device_alloc_s;
    timing["weights_upload_s"] = weights_upload_s;
    timing["inverse_upload_s"] = inverse_upload_s;
    timing["kernel_enqueue_s"] = kernel_enqueue_s;
    timing["sync_s"] = sync_s;
    timing["download_s"] = download_s;
    timing["total_s"] = seconds_since(total_start);
    timing["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_host.size() * sizeof(float));
    timing["weights_bytes"] = static_cast<unsigned long long>(frame_count_ * sizeof(float));
    timing["output_bytes"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float) * 4);
    timing["avoids_stack_scatter"] = true;
    timing["modifies_resident_stack"] = false;
    return py::make_tuple(master, weight_map, coverage_map, geometric_coverage_map, timing);
  }

 private:
  void require_index(std::size_t index) const {
    if (index >= frame_count_) {
      throw std::out_of_range("resident frame index is out of range");
    }
  }

  void require_loaded(std::size_t index, const char* operation) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error(std::string("resident frame must be loaded before ") + operation);
    }
  }

  void mark_loaded(std::size_t index) {
    if (!loaded_[index]) {
      loaded_[index] = 1;
      ++loaded_count_;
    }
  }

  CalibrationParameters calibration_parameters(
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) const {
    py::dict policy;
    if (!policy_obj.is_none()) {
      policy = py::cast<py::dict>(policy_obj);
    }
    CalibrationParameters params;
    params.master_dark_includes_bias = dict_bool(policy, "master_dark_includes_bias", true);
    params.dark_scaling_enabled = dict_bool(policy, "dark_scaling_enabled", true);
    params.flat_floor = dict_float(policy, "flat_floor", 1.0e-6f);
    params.pedestal = dict_float(policy, "pedestal", 0.0f);
    if (has_dark_ && params.dark_scaling_enabled && !dark_exposure_obj.is_none()) {
      const float dark_exposure_s = py::cast<float>(dark_exposure_obj);
      if (dark_exposure_s != 0.0f) {
        params.dark_scale = light_exposure_s / dark_exposure_s;
      }
    }
    return params;
  }

  py::dict calibration_timing_dict(const ResidentCalibrationTiming& timing, const char* mode) const {
    py::dict out;
    out["schema_version"] = 1;
    out["h2d_mode"] = mode;
    out["event_mode"] = std::string(mode) == "pageable" ? "none" : "reused_stack_events";
    out["host_copy_s"] = timing.host_copy_s;
    out["h2d_s"] = timing.h2d_s;
    out["calibrate_store_s"] = timing.calibrate_store_s;
    out["total_s"] = timing.total_s;
    out["host_pinned_bytes"] = host_pinned_bytes();
    return out;
  }

  void ensure_pinned_light_buffer() {
    if (h_pinned_light_ != nullptr) {
      return;
    }
    check_cuda(
        cudaHostAlloc(
            reinterpret_cast<void**>(&h_pinned_light_),
            pixels_per_frame_ * sizeof(float),
            cudaHostAllocPortable),
        "cudaHostAlloc(resident pinned raw light buffer)");
  }

  void ensure_calibration_lanes(std::size_t lane_count) {
    if (lane_count == 0) {
      return;
    }
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    while (d_calibration_lane_lights_.size() < lane_count) {
      float* buffer = nullptr;
      cudaStream_t stream = nullptr;
      cudaEvent_t start_event = nullptr;
      cudaEvent_t stop_event = nullptr;
      try {
        check_cuda(cudaMalloc(&buffer, frame_bytes), "cudaMalloc(resident multistream raw light lane)");
        check_cuda(cudaStreamCreate(&stream), "cudaStreamCreate(resident multistream calibration lane)");
        check_cuda(cudaEventCreate(&start_event), "cudaEventCreate(resident multistream calibration lane start)");
        check_cuda(cudaEventCreate(&stop_event), "cudaEventCreate(resident multistream calibration lane stop)");
        cudaEvent_t h2d_start_event = nullptr;
        check_cuda(cudaEventCreate(&h2d_start_event), "cudaEventCreate(resident multistream calibration lane h2d start)");
        calibration_lane_h2d_start_events_.push_back(h2d_start_event);
        cudaEvent_t h2d_event = nullptr;
        check_cuda(cudaEventCreate(&h2d_event), "cudaEventCreate(resident multistream calibration lane h2d done)");
        calibration_lane_h2d_events_.push_back(h2d_event);
      } catch (...) {
        if (stop_event != nullptr) {
          cudaEventDestroy(stop_event);
        }
        if (start_event != nullptr) {
          cudaEventDestroy(start_event);
        }
        if (calibration_lane_h2d_start_events_.size() > d_calibration_lane_lights_.size()) {
          cudaEventDestroy(calibration_lane_h2d_start_events_.back());
          calibration_lane_h2d_start_events_.pop_back();
        }
        if (calibration_lane_h2d_events_.size() > d_calibration_lane_lights_.size()) {
          cudaEventDestroy(calibration_lane_h2d_events_.back());
          calibration_lane_h2d_events_.pop_back();
        }
        if (stream != nullptr) {
          cudaStreamDestroy(stream);
        }
        cudaFree(buffer);
        throw;
      }
      d_calibration_lane_lights_.push_back(buffer);
      calibration_lane_streams_.push_back(stream);
      calibration_lane_start_events_.push_back(start_event);
      calibration_lane_stop_events_.push_back(stop_event);
    }
  }

  ResidentCalibrationTiming calibrate_frame_pageable_impl(
      std::size_t index,
      void* light_ptr,
      const CalibrationParameters& params) {
    ResidentCalibrationTiming timing;
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    {
      py::gil_scoped_release release;
      const auto h2d_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_light_, light_ptr, frame_bytes, cudaMemcpyHostToDevice),
          "cudaMemcpy(resident raw light)");
      timing.h2d_s = seconds_since(h2d_start);

      const auto calibrate_start = Clock::now();
      glass_calibrate_tile_f32_launch(
          d_light_,
          d_bias_,
          d_dark_,
          d_flat_,
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          has_bias_,
          has_dark_,
          has_flat_,
          params.master_dark_includes_bias,
          params.dark_scale,
          params.flat_floor,
          params.pedestal);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frame kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.calibrate_frame synchronize");
      timing.calibrate_store_s = seconds_since(calibrate_start);
    }
    timing.total_s = seconds_since(total_start);
    return timing;
  }

  ResidentCalibrationTiming calibrate_frame_pinned_async_impl(
      std::size_t index,
      void* light_ptr,
      const CalibrationParameters& params) {
    ResidentCalibrationTiming timing;
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    {
      py::gil_scoped_release release;
      ensure_pinned_light_buffer();

      const auto host_copy_start = Clock::now();
      std::memcpy(h_pinned_light_, light_ptr, frame_bytes);
      timing.host_copy_s = seconds_since(host_copy_start);

      check_cuda(cudaEventRecord(calibrate_h2d_start_, calibrate_stream_), "cudaEventRecord(resident pinned h2d start)");
      check_cuda(
          cudaMemcpyAsync(
              d_light_,
              h_pinned_light_,
              frame_bytes,
              cudaMemcpyHostToDevice,
              calibrate_stream_),
          "cudaMemcpyAsync(resident pinned raw light)");
      check_cuda(cudaEventRecord(calibrate_h2d_stop_, calibrate_stream_), "cudaEventRecord(resident pinned h2d stop)");
      check_cuda(
          cudaEventRecord(calibrate_kernel_start_, calibrate_stream_),
          "cudaEventRecord(resident calibration start)");
      glass_calibrate_tile_f32_launch_stream(
          d_light_,
          d_bias_,
          d_dark_,
          d_flat_,
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          has_bias_,
          has_dark_,
          has_flat_,
          params.master_dark_includes_bias,
          params.dark_scale,
          params.flat_floor,
          params.pedestal,
          calibrate_stream_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frame_pinned_async kernel launch");
      check_cuda(
          cudaEventRecord(calibrate_kernel_stop_, calibrate_stream_),
          "cudaEventRecord(resident calibration stop)");
      check_cuda(
          cudaStreamSynchronize(calibrate_stream_),
          "ResidentCalibratedStack.calibrate_frame_pinned_async synchronize");
      timing.h2d_s = cuda_event_elapsed_s(
          calibrate_h2d_start_,
          calibrate_h2d_stop_,
          "cudaEventElapsedTime(resident pinned h2d)");
      timing.calibrate_store_s =
          cuda_event_elapsed_s(
              calibrate_kernel_start_,
              calibrate_kernel_stop_,
              "cudaEventElapsedTime(resident calibration)");
    }
    timing.total_s = seconds_since(total_start);
    return timing;
  }

  ResidentCalibrationTiming calibrate_frame_host_async_impl(
      std::size_t index,
      void* light_ptr,
      const CalibrationParameters& params) {
    ResidentCalibrationTiming timing;
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    {
      py::gil_scoped_release release;
      check_cuda(
          cudaEventRecord(calibrate_h2d_start_, calibrate_stream_),
          "cudaEventRecord(resident host async h2d start)");
      check_cuda(
          cudaMemcpyAsync(
              d_light_,
              light_ptr,
              frame_bytes,
              cudaMemcpyHostToDevice,
              calibrate_stream_),
          "cudaMemcpyAsync(resident host raw light)");
      check_cuda(
          cudaEventRecord(calibrate_h2d_stop_, calibrate_stream_),
          "cudaEventRecord(resident host async h2d stop)");
      check_cuda(
          cudaEventRecord(calibrate_kernel_start_, calibrate_stream_),
          "cudaEventRecord(resident host async calibration start)");
      glass_calibrate_tile_f32_launch_stream(
          d_light_,
          d_bias_,
          d_dark_,
          d_flat_,
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          has_bias_,
          has_dark_,
          has_flat_,
          params.master_dark_includes_bias,
          params.dark_scale,
          params.flat_floor,
          params.pedestal,
          calibrate_stream_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frame_host_async kernel launch");
      check_cuda(
          cudaEventRecord(calibrate_kernel_stop_, calibrate_stream_),
          "cudaEventRecord(resident host async calibration stop)");
      check_cuda(
          cudaStreamSynchronize(calibrate_stream_),
          "ResidentCalibratedStack.calibrate_frame_host_async synchronize");
      timing.h2d_s = cuda_event_elapsed_s(
          calibrate_h2d_start_,
          calibrate_h2d_stop_,
          "cudaEventElapsedTime(resident host async h2d)");
      timing.calibrate_store_s =
          cuda_event_elapsed_s(
              calibrate_kernel_start_,
              calibrate_kernel_stop_,
              "cudaEventElapsedTime(resident host async calibration)");
    }
    timing.total_s = seconds_since(total_start);
    return timing;
  }

  void upload_optional_master(py::object obj, float** destination, bool* present, const char* name) {
    cudaFree(*destination);
    *destination = nullptr;
    *present = false;
    if (obj.is_none()) {
      return;
    }
    py::array_t<float, py::array::c_style | py::array::forcecast> array =
        py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(obj);
    const py::buffer_info info = array.request();
    require_frame_shape(info, height_, width_);
    check_cuda(cudaMalloc(destination, pixels_per_frame_ * sizeof(float)), name);
    check_cuda(
        cudaMemcpy(*destination, info.ptr, pixels_per_frame_ * sizeof(float), cudaMemcpyHostToDevice),
        name);
    *present = true;
  }

  void allocate_warp_coverage_if_needed() {
    if (d_warp_coverage_ != nullptr) {
      return;
    }
    check_cuda(
        cudaMalloc(&d_warp_coverage_, pixels_per_frame_ * sizeof(float)),
        "cudaMalloc(resident warp coverage accumulator)");
    check_cuda(
        cudaMemset(d_warp_coverage_, 0, pixels_per_frame_ * sizeof(float)),
        "cudaMemset(resident warp coverage accumulator)");
    warp_coverage_frame_count_ = 0;
  }

  struct BatchWarpWorkspace {
    std::unique_ptr<float, CudaFloatFree> output;
    std::unique_ptr<unsigned char, CudaUCharFree> coverage;
    std::unique_ptr<float, CudaFloatFree> inverses;
    std::unique_ptr<unsigned long long, CudaUllFree> indices;
    std::size_t capacity_frames = 0;
    std::size_t output_bytes = 0;
    std::size_t coverage_bytes = 0;
    std::size_t inverse_bytes = 0;
    std::size_t index_bytes = 0;
    double allocation_s = 0.0;
  };

  BatchWarpWorkspace allocate_batch_warp_workspace(std::size_t requested_frames) {
    if (requested_frames == 0) {
      throw std::invalid_argument("batch warp workspace requires at least one frame");
    }
    constexpr std::size_t preferred_frames = 8;
    std::size_t capacity = std::min(requested_frames, preferred_frames);
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    cudaError_t last_error = cudaSuccess;
    const auto alloc_start = Clock::now();
    while (capacity > 0) {
      float* raw_output = nullptr;
      unsigned char* raw_coverage = nullptr;
      float* raw_inverses = nullptr;
      unsigned long long* raw_indices = nullptr;
      const std::size_t output_bytes = capacity * frame_bytes;
      const std::size_t coverage_bytes = capacity * pixels_per_frame_ * sizeof(unsigned char);
      const std::size_t inverse_bytes = capacity * 9 * sizeof(float);
      const std::size_t index_bytes = capacity * sizeof(unsigned long long);
      last_error = cudaMalloc(&raw_output, output_bytes);
      if (last_error == cudaSuccess) {
        last_error = cudaMalloc(&raw_coverage, coverage_bytes);
      }
      if (last_error == cudaSuccess) {
        last_error = cudaMalloc(&raw_inverses, inverse_bytes);
      }
      if (last_error == cudaSuccess) {
        last_error = cudaMalloc(&raw_indices, index_bytes);
      }
      if (last_error == cudaSuccess) {
        BatchWarpWorkspace workspace;
        workspace.output.reset(raw_output);
        workspace.coverage.reset(raw_coverage);
        workspace.inverses.reset(raw_inverses);
        workspace.indices.reset(raw_indices);
        workspace.capacity_frames = capacity;
        workspace.output_bytes = output_bytes;
        workspace.coverage_bytes = coverage_bytes;
        workspace.inverse_bytes = inverse_bytes;
        workspace.index_bytes = index_bytes;
        workspace.allocation_s = seconds_since(alloc_start);
        return workspace;
      }
      if (raw_output != nullptr) {
        (void)cudaFree(raw_output);
      }
      if (raw_coverage != nullptr) {
        (void)cudaFree(raw_coverage);
      }
      if (raw_inverses != nullptr) {
        (void)cudaFree(raw_inverses);
      }
      if (raw_indices != nullptr) {
        (void)cudaFree(raw_indices);
      }
      (void)cudaGetLastError();
      capacity /= 2;
    }
    std::ostringstream message;
    message << "cudaMalloc(resident batch matrix warp workspace) failed: "
            << cudaGetErrorString(last_error);
    throw std::runtime_error(message.str());
  }

  void allocate_warp_scratch_if_needed(bool matrix_warp) {
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    if (d_warp_output_ == nullptr) {
      check_cuda(cudaMalloc(&d_warp_output_, frame_bytes), "cudaMalloc(resident warp scratch output)");
    }
    if (d_warp_frame_coverage_ == nullptr) {
      check_cuda(
          cudaMalloc(&d_warp_frame_coverage_, frame_bytes),
          "cudaMalloc(resident warp scratch coverage)");
    }
    if (matrix_warp && d_warp_inverse_ == nullptr) {
      check_cuda(cudaMalloc(&d_warp_inverse_, 9 * sizeof(float)), "cudaMalloc(resident warp scratch inverse)");
    }
  }

  std::size_t frame_count_;
  std::size_t height_;
  std::size_t width_;
  std::size_t pixels_per_frame_;
  std::size_t loaded_count_ = 0;
  std::size_t warp_coverage_frame_count_ = 0;
  std::vector<unsigned char> loaded_;
  float* d_stack_ = nullptr;
  float* d_light_ = nullptr;
  float* d_bias_ = nullptr;
  float* d_dark_ = nullptr;
  float* d_flat_ = nullptr;
  std::vector<float*> d_calibration_lane_lights_;
  std::vector<cudaStream_t> calibration_lane_streams_;
  std::vector<cudaEvent_t> calibration_lane_start_events_;
  std::vector<cudaEvent_t> calibration_lane_stop_events_;
  std::vector<cudaEvent_t> calibration_lane_h2d_start_events_;
  std::vector<cudaEvent_t> calibration_lane_h2d_events_;
  bool pending_calibration_ = false;
  std::vector<std::size_t> pending_calibration_indices_;
  std::vector<unsigned char> pending_calibration_lane_used_;
  std::size_t pending_calibration_lane_count_ = 0;
  Clock::time_point pending_calibration_total_start_{};
  double pending_calibration_h2d_release_s_ = 0.0;
  double pending_calibration_h2d_event_sync_s_ = 0.0;
  double pending_calibration_h2d_event_elapsed_s_ = 0.0;
  float* d_warp_coverage_ = nullptr;
  float* d_warp_output_ = nullptr;
  float* d_warp_frame_coverage_ = nullptr;
  float* d_warp_inverse_ = nullptr;
  float* h_pinned_light_ = nullptr;
  cudaStream_t calibrate_stream_ = nullptr;
  cudaEvent_t calibrate_h2d_start_ = nullptr;
  cudaEvent_t calibrate_h2d_stop_ = nullptr;
  cudaEvent_t calibrate_kernel_start_ = nullptr;
  cudaEvent_t calibrate_kernel_stop_ = nullptr;
  bool has_bias_ = false;
  bool has_dark_ = false;
  bool has_flat_ = false;
};

}  // namespace

bool cuda_available() {
  int count = 0;
  const cudaError_t status = cudaGetDeviceCount(&count);
  return status == cudaSuccess && count > 0;
}

py::list list_devices() {
  int count = 0;
  check_cuda(cudaGetDeviceCount(&count), "cudaGetDeviceCount");
  py::list devices;
  for (int i = 0; i < count; ++i) {
    devices.append(device_info_dict(i));
  }
  return devices;
}

py::dict get_device_info(int device_id) {
  int count = 0;
  check_cuda(cudaGetDeviceCount(&count), "cudaGetDeviceCount");
  if (device_id < 0 || device_id >= count) {
    throw std::out_of_range("CUDA device id is out of range");
  }
  return device_info_dict(device_id);
}

py::array_t<float> smoke_add_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> a,
    py::array_t<float, py::array::c_style | py::array::forcecast> b) {
  const py::buffer_info a_info = a.request();
  const py::buffer_info b_info = b.request();
  require_same_shape(a_info, b_info);
  const std::size_t n = element_count(a_info);
  py::array_t<float> out(a_info.shape);
  const py::buffer_info out_info = out.request();

  float* d_a = nullptr;
  float* d_b = nullptr;
  float* d_out = nullptr;
  try {
    check_cuda(cudaMalloc(&d_a, n * sizeof(float)), "cudaMalloc(a)");
    check_cuda(cudaMalloc(&d_b, n * sizeof(float)), "cudaMalloc(b)");
    check_cuda(cudaMalloc(&d_out, n * sizeof(float)), "cudaMalloc(out)");
    check_cuda(cudaMemcpy(d_a, a_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(a)");
    check_cuda(cudaMemcpy(d_b, b_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(b)");
    glass_smoke_add_f32_launch(d_a, d_b, d_out, n);
    check_cuda(cudaGetLastError(), "smoke_add_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "smoke_add_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_info.ptr, d_out, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(out)");
  } catch (...) {
    cudaFree(d_a);
    cudaFree(d_b);
    cudaFree(d_out);
    throw;
  }
  cudaFree(d_a);
  cudaFree(d_b);
  cudaFree(d_out);
  return out;
}

float reduce_mean_tile_f32(py::array_t<float, py::array::c_style | py::array::forcecast> tile) {
  const py::buffer_info info = tile.request();
  const auto* ptr = static_cast<const float*>(info.ptr);
  const std::size_t n = element_count(info);
  if (n == 0) {
    throw std::invalid_argument("cannot reduce an empty tile");
  }
  double sum = 0.0;
  for (std::size_t i = 0; i < n; ++i) {
    sum += ptr[i];
  }
  return static_cast<float>(sum / static_cast<double>(n));
}

py::array_t<float> calibrate_tile_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> light,
    py::object bias_obj,
    py::object dark_obj,
    py::object flat_obj,
    float light_exposure_s,
    py::object dark_exposure_obj,
    py::object policy_obj) {
  const py::buffer_info light_info = light.request();
  const std::size_t n = element_count(light_info);
  py::array_t<float> out(light_info.shape);
  const py::buffer_info out_info = out.request();

  py::array_t<float, py::array::c_style | py::array::forcecast> bias;
  py::array_t<float, py::array::c_style | py::array::forcecast> dark;
  py::array_t<float, py::array::c_style | py::array::forcecast> flat;
  py::buffer_info bias_info;
  py::buffer_info dark_info;
  py::buffer_info flat_info;

  const bool has_bias = !bias_obj.is_none();
  const bool has_dark = !dark_obj.is_none();
  const bool has_flat = !flat_obj.is_none();

  if (has_bias) {
    bias = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(bias_obj);
    bias_info = bias.request();
    require_same_shape(light_info, bias_info);
  }
  if (has_dark) {
    dark = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(dark_obj);
    dark_info = dark.request();
    require_same_shape(light_info, dark_info);
  }
  if (has_flat) {
    flat = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(flat_obj);
    flat_info = flat.request();
    require_same_shape(light_info, flat_info);
  }

  py::dict policy;
  if (!policy_obj.is_none()) {
    policy = py::cast<py::dict>(policy_obj);
  }
  const bool master_dark_includes_bias =
      dict_bool(policy, "master_dark_includes_bias", true);
  const bool dark_scaling_enabled = dict_bool(policy, "dark_scaling_enabled", true);
  const float flat_floor = dict_float(policy, "flat_floor", 1.0e-6f);
  const float pedestal = dict_float(policy, "pedestal", 0.0f);

  float dark_scale = 1.0f;
  if (has_dark && dark_scaling_enabled && !dark_exposure_obj.is_none()) {
    const float dark_exposure_s = py::cast<float>(dark_exposure_obj);
    if (dark_exposure_s != 0.0f) {
      dark_scale = light_exposure_s / dark_exposure_s;
    }
  }

  float* d_light = nullptr;
  float* d_bias = nullptr;
  float* d_dark = nullptr;
  float* d_flat = nullptr;
  float* d_out = nullptr;

  try {
    check_cuda(cudaMalloc(&d_light, n * sizeof(float)), "cudaMalloc(light)");
    check_cuda(cudaMalloc(&d_out, n * sizeof(float)), "cudaMalloc(out)");
    check_cuda(
        cudaMemcpy(d_light, light_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(light)");
    if (has_bias) {
      check_cuda(cudaMalloc(&d_bias, n * sizeof(float)), "cudaMalloc(bias)");
      check_cuda(
          cudaMemcpy(d_bias, bias_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(bias)");
    }
    if (has_dark) {
      check_cuda(cudaMalloc(&d_dark, n * sizeof(float)), "cudaMalloc(dark)");
      check_cuda(
          cudaMemcpy(d_dark, dark_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(dark)");
    }
    if (has_flat) {
      check_cuda(cudaMalloc(&d_flat, n * sizeof(float)), "cudaMalloc(flat)");
      check_cuda(
          cudaMemcpy(d_flat, flat_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(flat)");
    }
    glass_calibrate_tile_f32_launch(
        d_light,
        d_bias,
        d_dark,
        d_flat,
        d_out,
        n,
        has_bias,
        has_dark,
        has_flat,
        master_dark_includes_bias,
        dark_scale,
        flat_floor,
        pedestal);
    check_cuda(cudaGetLastError(), "calibrate_tile_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "calibrate_tile_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_info.ptr, d_out, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(calibrated)");
  } catch (...) {
    cudaFree(d_light);
    cudaFree(d_bias);
    cudaFree(d_dark);
    cudaFree(d_flat);
    cudaFree(d_out);
    throw;
  }

  cudaFree(d_light);
  cudaFree(d_bias);
  cudaFree(d_dark);
  cudaFree(d_flat);
  cudaFree(d_out);
  return out;
}

py::array_t<float> mean_stack_tiles_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> stack) {
  const py::buffer_info stack_info = stack.request();
  if (stack_info.ndim != 3) {
    throw std::invalid_argument("stack must have shape (frame_count, height, width)");
  }
  const auto frame_count = static_cast<std::size_t>(stack_info.shape[0]);
  const auto height = static_cast<py::ssize_t>(stack_info.shape[1]);
  const auto width = static_cast<py::ssize_t>(stack_info.shape[2]);
  if (frame_count == 0 || height <= 0 || width <= 0) {
    throw std::invalid_argument("stack dimensions must be non-empty");
  }
  const std::size_t pixels_per_frame = static_cast<std::size_t>(height * width);
  const std::size_t n = frame_count * pixels_per_frame;
  py::array_t<float> out({height, width});
  const py::buffer_info out_info = out.request();

  float* d_stack = nullptr;
  float* d_out = nullptr;
  try {
    check_cuda(cudaMalloc(&d_stack, n * sizeof(float)), "cudaMalloc(stack)");
    check_cuda(cudaMalloc(&d_out, pixels_per_frame * sizeof(float)), "cudaMalloc(out)");
    check_cuda(
        cudaMemcpy(d_stack, stack_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(stack)");
    glass_mean_stack_tiles_f32_launch(d_stack, d_out, frame_count, pixels_per_frame);
    check_cuda(cudaGetLastError(), "mean_stack_tiles_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "mean_stack_tiles_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_info.ptr, d_out, pixels_per_frame * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(mean tile)");
  } catch (...) {
    cudaFree(d_stack);
    cudaFree(d_out);
    throw;
  }

  cudaFree(d_stack);
  cudaFree(d_out);
  return out;
}

py::tuple warp_translation_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float dx,
    float dy,
    float fill) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(warp coverage)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(warp input)");
    glass_warp_translation_f32_launch(
        d_input,
        d_output,
        d_coverage,
        width,
        height,
        static_cast<int>(std::lround(dx)),
        static_cast<int>(std::lround(dy)),
        fill,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_translation_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_translation_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  return py::make_tuple(output, coverage);
}

py::tuple warp_translation_bilinear_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float dx,
    float dy,
    float fill) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(bilinear warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(bilinear warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(bilinear warp coverage)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(bilinear warp input)");
    glass_warp_translation_bilinear_f32_launch(
        d_input,
        d_output,
        d_coverage,
        width,
        height,
        dx,
        dy,
        fill,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_translation_bilinear_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_translation_bilinear_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(bilinear warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(bilinear warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  return py::make_tuple(output, coverage);
}

py::tuple warp_matrix_bilinear_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    py::object matrix_obj,
    float fill) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  float* d_inverse = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(matrix warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(matrix warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(matrix warp coverage)");
    check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(matrix warp inverse)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix warp input)");
    check_cuda(
        cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix warp inverse)");
    glass_warp_matrix_bilinear_f32_launch(
        d_input,
        d_output,
        d_coverage,
        d_inverse,
        width,
        height,
        fill,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_matrix_bilinear_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_matrix_bilinear_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    cudaFree(d_inverse);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  cudaFree(d_inverse);
  return py::make_tuple(output, coverage);
}

py::tuple warp_matrix_lanczos3_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    py::object matrix_obj,
    float fill,
    float clamping_threshold) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  float* d_inverse = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp coverage)");
    check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp inverse)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix Lanczos3 warp input)");
    check_cuda(
        cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix Lanczos3 warp inverse)");
    glass_warp_matrix_lanczos3_f32_launch(
        d_input,
        d_output,
        d_coverage,
        d_inverse,
        width,
        height,
        fill,
        clamping_threshold,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_matrix_lanczos3_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_matrix_lanczos3_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix Lanczos3 warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix Lanczos3 warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    cudaFree(d_inverse);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  cudaFree(d_inverse);
  return py::make_tuple(output, coverage);
}

py::dict matrix_alignment_metrics_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    py::object matrix_obj,
    int sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (sample_stride <= 0) {
    throw std::invalid_argument("sample_stride must be positive");
  }
  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sampled_pixels = sample_width * sample_height;
  const int blocks = std::max(1, std::min(1024, (sampled_pixels + 255) / 256));
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
  std::vector<double> partial_stats(static_cast<std::size_t>(blocks) * 7, 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  float* d_inverse = nullptr;
  double* d_partial_stats = nullptr;
  unsigned long long* d_partial_count = nullptr;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(matrix metrics reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(matrix metrics moving)");
    check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(matrix metrics inverse)");
    check_cuda(
        cudaMalloc(&d_partial_stats, partial_stats.size() * sizeof(double)),
        "cudaMalloc(matrix metrics partial stats)");
    check_cuda(
        cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
        "cudaMalloc(matrix metrics partial count)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix metrics reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix metrics moving)");
    check_cuda(
        cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix metrics inverse)");
    glass_matrix_alignment_metrics_f32_launch(
        d_reference,
        d_moving,
        d_inverse,
        d_partial_stats,
        d_partial_count,
        width,
        height,
        stride,
        blocks);
    check_cuda(cudaGetLastError(), "matrix_alignment_metrics_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "matrix_alignment_metrics_f32 synchronize");
    check_cuda(
        cudaMemcpy(partial_stats.data(), d_partial_stats, partial_stats.size() * sizeof(double), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix metrics partial stats)");
    check_cuda(
        cudaMemcpy(
            partial_count.data(),
            d_partial_count,
            partial_count.size() * sizeof(unsigned long long),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix metrics partial count)");
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    cudaFree(d_inverse);
    cudaFree(d_partial_stats);
    cudaFree(d_partial_count);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);
  cudaFree(d_inverse);
  cudaFree(d_partial_stats);
  cudaFree(d_partial_count);

  double sum_ref = 0.0;
  double sum_mov = 0.0;
  double sum_ref2 = 0.0;
  double sum_mov2 = 0.0;
  double sum_cross = 0.0;
  double sum_diff2 = 0.0;
  double sum_abs_diff = 0.0;
  unsigned long long valid_pixels = 0ULL;
  for (int block = 0; block < blocks; ++block) {
    const std::size_t offset = static_cast<std::size_t>(block) * 7;
    sum_ref += partial_stats[offset + 0];
    sum_mov += partial_stats[offset + 1];
    sum_ref2 += partial_stats[offset + 2];
    sum_mov2 += partial_stats[offset + 3];
    sum_cross += partial_stats[offset + 4];
    sum_diff2 += partial_stats[offset + 5];
    sum_abs_diff += partial_stats[offset + 6];
    valid_pixels += partial_count[static_cast<std::size_t>(block)];
  }

  const double count = static_cast<double>(valid_pixels);
  double rms = std::numeric_limits<double>::quiet_NaN();
  double mean_abs_diff = std::numeric_limits<double>::quiet_NaN();
  double ncc = std::numeric_limits<double>::quiet_NaN();
  if (valid_pixels > 0ULL) {
    rms = std::sqrt(sum_diff2 / count);
    mean_abs_diff = sum_abs_diff / count;
  }
  if (valid_pixels > 1ULL) {
    const double numerator = sum_cross - (sum_ref * sum_mov / count);
    const double ref_var = std::max(sum_ref2 - (sum_ref * sum_ref / count), 0.0);
    const double mov_var = std::max(sum_mov2 - (sum_mov * sum_mov / count), 0.0);
    const double denominator = std::sqrt(ref_var * mov_var);
    if (denominator > 0.0) {
      ncc = numerator / denominator;
    }
  }

  py::dict result;
  result["valid_pixels"] = valid_pixels;
  result["sampled_pixels"] = sampled_pixels;
  result["sample_stride"] = stride;
  result["rms"] = rms;
  result["mean_abs_diff"] = mean_abs_diff;
  result["ncc"] = ncc;
  result["model"] = "matrix_alignment_metrics_cuda";
  return result;
}

py::dict refine_matrix_translation_with_metrics_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    py::object matrix_obj,
    float search_radius_px,
    float coarse_step_px,
    float fine_radius_px,
    float fine_step_px,
    int coarse_sample_stride,
    int final_sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
    throw std::invalid_argument("search radii must be non-negative");
  }
  if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
    throw std::invalid_argument("search steps must be positive");
  }
  if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
    throw std::invalid_argument("sample strides must be positive");
  }

  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto base_matrix = parse_matrix3x3(matrix_obj);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  MatrixCandidateMetrics coarse_best;
  MatrixCandidateMetrics best;
  int coarse_candidates = 0;
  int fine_candidates = 0;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(matrix refine reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(matrix refine moving)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix refine reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix refine moving)");

    const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
    coarse_candidates = static_cast<int>(coarse_offsets.size());
    coarse_best = score_matrix_translation_candidates_f32(
        d_reference,
        d_moving,
        base_matrix,
        coarse_offsets,
        width,
        height,
        coarse_sample_stride);
    best = coarse_best;

    if (fine_radius_px > 0.0f) {
      const auto fine_offsets = translation_offsets(coarse_best.dx, coarse_best.dy, fine_radius_px, fine_step_px);
      fine_candidates = static_cast<int>(fine_offsets.size());
      best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          fine_offsets,
          width,
          height,
          final_sample_stride);
    } else if (final_sample_stride != coarse_sample_stride) {
      const std::vector<std::pair<float, float>> final_offsets{{coarse_best.dx, coarse_best.dy}};
      best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          final_offsets,
          width,
          height,
          final_sample_stride);
    }
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list values;
    for (int col = 0; col < 3; ++col) {
      values.append(best.matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(values);
  }

  py::dict result;
  result["matrix"] = matrix_rows;
  result["dx_correction"] = best.dx;
  result["dy_correction"] = best.dy;
  result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
  result["coarse_candidates"] = coarse_candidates;
  result["fine_candidates"] = fine_candidates;
  result["search_radius_px"] = search_radius_px;
  result["coarse_step_px"] = coarse_step_px;
  result["fine_radius_px"] = fine_radius_px;
  result["fine_step_px"] = fine_step_px;
  result["coarse_sample_stride"] = coarse_sample_stride;
  result["final_sample_stride"] = final_sample_stride;
  result["model"] = "cuda_matrix_metric_translation_refine_grid";
  return result;
}

py::dict refine_matrix_translation_candidates_with_metrics_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    py::object matrices_obj,
    float search_radius_px,
    float coarse_step_px,
    float fine_radius_px,
    float fine_step_px,
    int coarse_sample_stride,
    int final_sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
    throw std::invalid_argument("search radii must be non-negative");
  }
  if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
    throw std::invalid_argument("search steps must be positive");
  }
  if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
    throw std::invalid_argument("sample strides must be positive");
  }

  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto seed_matrices = parse_matrix_stack(matrices_obj);
  const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
  const int coarse_candidates = static_cast<int>(coarse_offsets.size());

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  MatrixCandidateMetrics best;
  bool have_best = false;
  int selected_index = -1;
  py::list seed_results;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(matrix multi-refine reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(matrix multi-refine moving)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix multi-refine reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix multi-refine moving)");

    for (std::size_t seed_index = 0; seed_index < seed_matrices.size(); ++seed_index) {
      const auto& base_matrix = seed_matrices[seed_index];
      const MatrixCandidateMetrics coarse_best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          coarse_offsets,
          width,
          height,
          coarse_sample_stride);
      MatrixCandidateMetrics seed_best = coarse_best;
      int fine_candidates = 0;
      if (fine_radius_px > 0.0f) {
        const auto fine_offsets = translation_offsets(coarse_best.dx, coarse_best.dy, fine_radius_px, fine_step_px);
        fine_candidates = static_cast<int>(fine_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            fine_offsets,
            width,
            height,
            final_sample_stride);
      } else if (final_sample_stride != coarse_sample_stride) {
        const std::vector<std::pair<float, float>> final_offsets{{coarse_best.dx, coarse_best.dy}};
        fine_candidates = static_cast<int>(final_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            final_offsets,
            width,
            height,
            final_sample_stride);
      }

      py::dict seed_result;
      seed_result["seed_index"] = static_cast<int>(seed_index);
      seed_result["matrix"] = matrix3x3_to_pylist(seed_best.matrix);
      seed_result["dx_correction"] = seed_best.dx;
      seed_result["dy_correction"] = seed_best.dy;
      seed_result["metrics"] = matrix_candidate_to_dict(seed_best, "matrix_alignment_metrics_cuda_candidate_grid");
      seed_result["coarse_candidates"] = coarse_candidates;
      seed_result["fine_candidates"] = fine_candidates;
      seed_results.append(seed_result);

      if (!have_best || better_matrix_metric(seed_best, best)) {
        best = seed_best;
        selected_index = static_cast<int>(seed_index);
        have_best = true;
      }
    }
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);

  if (!have_best) {
    throw std::runtime_error("matrix multi-refine produced no candidates");
  }
  py::dict result;
  result["matrix"] = matrix3x3_to_pylist(best.matrix);
  result["dx_correction"] = best.dx;
  result["dy_correction"] = best.dy;
  result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
  result["selected_index"] = selected_index;
  result["seed_count"] = static_cast<int>(seed_matrices.size());
  result["seed_results"] = seed_results;
  result["coarse_candidates_per_seed"] = coarse_candidates;
  result["search_radius_px"] = search_radius_px;
  result["coarse_step_px"] = coarse_step_px;
  result["fine_radius_px"] = fine_radius_px;
  result["fine_step_px"] = fine_step_px;
  result["coarse_sample_stride"] = coarse_sample_stride;
  result["final_sample_stride"] = final_sample_stride;
  result["model"] = "cuda_matrix_metric_translation_multi_seed_refine_grid";
  return result;
}

py::dict estimate_translation_search_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    int max_shift_x,
    int max_shift_y,
    int sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (max_shift_x < 0 || max_shift_y < 0) {
    throw std::invalid_argument("max_shift values must be non-negative");
  }
  if (sample_stride <= 0) {
    throw std::invalid_argument("sample_stride must be positive");
  }
  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  if (height <= 0 || width <= 0) {
    throw std::invalid_argument("reference and moving images must be non-empty");
  }
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const int shift_count = (2 * max_shift_x + 1) * (2 * max_shift_y + 1);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  float* d_scores = nullptr;
  int* d_best_dx = nullptr;
  int* d_best_dy = nullptr;
  float* d_best_score = nullptr;
  int best_dx = 0;
  int best_dy = 0;
  float best_score = 0.0f;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(registration reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(registration moving)");
    check_cuda(
        cudaMalloc(&d_scores, static_cast<std::size_t>(shift_count) * sizeof(float)),
        "cudaMalloc(registration scores)");
    check_cuda(cudaMalloc(&d_best_dx, sizeof(int)), "cudaMalloc(registration best dx)");
    check_cuda(cudaMalloc(&d_best_dy, sizeof(int)), "cudaMalloc(registration best dy)");
    check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(registration best score)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(registration reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(registration moving)");
    glass_estimate_translation_search_f32_launch(
        d_reference,
        d_moving,
        d_scores,
        d_best_dx,
        d_best_dy,
        d_best_score,
        width,
        height,
        max_shift_x,
        max_shift_y,
        sample_stride);
    check_cuda(cudaGetLastError(), "estimate_translation_search_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_translation_search_f32 synchronize");
    check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(best dx)");
    check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(best dy)");
    check_cuda(
        cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(best score)");
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);
  cudaFree(d_scores);
  cudaFree(d_best_dx);
  cudaFree(d_best_dy);
  cudaFree(d_best_score);

  py::dict result;
  result["dx"] = best_dx;
  result["dy"] = best_dy;
  result["score"] = best_score;
  result["search_count"] = shift_count;
  result["sample_stride"] = sample_stride;
  result["model"] = "translation_integer_ncc";
  return result;
}

py::dict estimate_translation_subpixel_ncc_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    float center_dx,
    float center_dy,
    int radius_steps,
    float step,
    int sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (radius_steps < 0) {
    throw std::invalid_argument("radius_steps must be non-negative");
  }
  if (step <= 0.0f) {
    throw std::invalid_argument("step must be positive");
  }
  if (sample_stride <= 0) {
    throw std::invalid_argument("sample_stride must be positive");
  }
  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  if (height <= 0 || width <= 0) {
    throw std::invalid_argument("reference and moving images must be non-empty");
  }
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const int candidate_count = (2 * radius_steps + 1) * (2 * radius_steps + 1);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  float* d_scores = nullptr;
  float* d_best_dx = nullptr;
  float* d_best_dy = nullptr;
  float* d_best_score = nullptr;
  float best_dx = 0.0f;
  float best_dy = 0.0f;
  float best_score = 0.0f;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(subpixel reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(subpixel moving)");
    check_cuda(
        cudaMalloc(&d_scores, static_cast<std::size_t>(candidate_count) * sizeof(float)),
        "cudaMalloc(subpixel scores)");
    check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(subpixel best dx)");
    check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(subpixel best dy)");
    check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(subpixel best score)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(subpixel reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(subpixel moving)");
    glass_estimate_translation_subpixel_ncc_f32_launch(
        d_reference,
        d_moving,
        d_scores,
        d_best_dx,
        d_best_dy,
        d_best_score,
        width,
        height,
        center_dx,
        center_dy,
        radius_steps,
        step,
        sample_stride);
    check_cuda(cudaGetLastError(), "estimate_translation_subpixel_ncc_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_translation_subpixel_ncc_f32 synchronize");
    check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(subpixel best dx)");
    check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(subpixel best dy)");
    check_cuda(
        cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(subpixel best score)");
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);
  cudaFree(d_scores);
  cudaFree(d_best_dx);
  cudaFree(d_best_dy);
  cudaFree(d_best_score);

  py::dict result;
  result["dx"] = best_dx;
  result["dy"] = best_dy;
  result["score"] = best_score;
  result["candidate_count"] = candidate_count;
  result["center_dx"] = center_dx;
  result["center_dy"] = center_dy;
  result["radius_steps"] = radius_steps;
  result["step"] = step;
  result["sample_stride"] = sample_stride;
  result["model"] = "translation_subpixel_ncc";
  return result;
}

py::dict estimate_translation_from_catalogs_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y,
    float tolerance_px,
    float max_abs_dx,
    float max_abs_dy,
    float prior_dx,
    float prior_dy,
    float prior_radius_px) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(moving_x_info, moving_y_info);
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int moving_count = static_cast<int>(moving_x_info.shape[0]);
  if (reference_count <= 0 || moving_count <= 0) {
    throw std::invalid_argument("catalogs must be non-empty");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (max_abs_dx < 0.0f) {
    max_abs_dx = -1.0f;
  }
  if (max_abs_dy < 0.0f) {
    max_abs_dy = max_abs_dx;
  }
  if (prior_radius_px < 0.0f) {
    prior_radius_px = -1.0f;
  }
  const int pair_count = reference_count * moving_count;

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_candidate_dx = nullptr;
  float* d_candidate_dy = nullptr;
  int* d_scores = nullptr;
  float* d_best_dx = nullptr;
  float* d_best_dy = nullptr;
  int* d_best_inliers = nullptr;
  int* d_moving_best_reference = nullptr;
  int* d_reference_best_moving = nullptr;
  float* d_refine_sums = nullptr;
  int* d_mutual_inliers = nullptr;
  float* d_refined_dx = nullptr;
  float* d_refined_dy = nullptr;
  float* d_rms_px = nullptr;
  float best_dx = 0.0f;
  float best_dy = 0.0f;
  int best_inliers = 0;
  int mutual_inliers = 0;
  float refined_dx = 0.0f;
  float refined_dy = 0.0f;
  float rms_px = 0.0f;
  try {
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(catalog reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(catalog reference y)");
    check_cuda(
        cudaMalloc(&d_moving_x, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(catalog moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(catalog moving y)");
    check_cuda(
        cudaMalloc(&d_candidate_dx, static_cast<std::size_t>(pair_count) * sizeof(float)),
        "cudaMalloc(catalog candidate dx)");
    check_cuda(
        cudaMalloc(&d_candidate_dy, static_cast<std::size_t>(pair_count) * sizeof(float)),
        "cudaMalloc(catalog candidate dy)");
    check_cuda(cudaMalloc(&d_scores, static_cast<std::size_t>(pair_count) * sizeof(int)), "cudaMalloc(catalog scores)");
    check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(catalog best dx)");
    check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(catalog best dy)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(catalog best inliers)");
    check_cuda(
        cudaMalloc(&d_moving_best_reference, static_cast<std::size_t>(moving_count) * sizeof(int)),
        "cudaMalloc(catalog moving best reference)");
    check_cuda(
        cudaMalloc(&d_reference_best_moving, static_cast<std::size_t>(reference_count) * sizeof(int)),
        "cudaMalloc(catalog reference best moving)");
    check_cuda(cudaMalloc(&d_refine_sums, 3 * sizeof(float)), "cudaMalloc(catalog refine sums)");
    check_cuda(cudaMalloc(&d_mutual_inliers, sizeof(int)), "cudaMalloc(catalog mutual inliers)");
    check_cuda(cudaMalloc(&d_refined_dx, sizeof(float)), "cudaMalloc(catalog refined dx)");
    check_cuda(cudaMalloc(&d_refined_dy, sizeof(float)), "cudaMalloc(catalog refined dy)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(catalog rms)");
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog reference y)");
    check_cuda(
        cudaMemcpy(
            d_moving_x,
            moving_x_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog moving x)");
    check_cuda(
        cudaMemcpy(
            d_moving_y,
            moving_y_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog moving y)");
    glass_estimate_translation_from_catalogs_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_candidate_dx,
        d_candidate_dy,
        d_scores,
        d_best_dx,
        d_best_dy,
        d_best_inliers,
        d_moving_best_reference,
        d_reference_best_moving,
        d_refine_sums,
        d_mutual_inliers,
        d_refined_dx,
        d_refined_dy,
        d_rms_px,
        reference_count,
        moving_count,
        tolerance_px,
        max_abs_dx,
        max_abs_dy,
        prior_dx,
        prior_dy,
        prior_radius_px);
    check_cuda(cudaGetLastError(), "estimate_translation_from_catalogs_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_translation_from_catalogs_f32 synchronize");
    check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(catalog best dx)");
    check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(catalog best dy)");
    check_cuda(
        cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog best inliers)");
    check_cuda(
        cudaMemcpy(&mutual_inliers, d_mutual_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog mutual inliers)");
    check_cuda(
        cudaMemcpy(&refined_dx, d_refined_dx, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog refined dx)");
    check_cuda(
        cudaMemcpy(&refined_dy, d_refined_dy, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog refined dy)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(catalog rms)");
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_candidate_dx);
    cudaFree(d_candidate_dy);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_inliers);
    cudaFree(d_moving_best_reference);
    cudaFree(d_reference_best_moving);
    cudaFree(d_refine_sums);
    cudaFree(d_mutual_inliers);
    cudaFree(d_refined_dx);
    cudaFree(d_refined_dy);
    cudaFree(d_rms_px);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_candidate_dx);
  cudaFree(d_candidate_dy);
  cudaFree(d_scores);
  cudaFree(d_best_dx);
  cudaFree(d_best_dy);
  cudaFree(d_best_inliers);
  cudaFree(d_moving_best_reference);
  cudaFree(d_reference_best_moving);
  cudaFree(d_refine_sums);
  cudaFree(d_mutual_inliers);
  cudaFree(d_refined_dx);
  cudaFree(d_refined_dy);
  cudaFree(d_rms_px);

  py::dict result;
  result["dx"] = best_dx;
  result["dy"] = best_dy;
  result["inliers"] = best_inliers;
  result["refined_dx"] = refined_dx;
  result["refined_dy"] = refined_dy;
  result["mutual_inliers"] = mutual_inliers;
  result["rms_px"] = rms_px;
  result["candidate_count"] = pair_count;
  result["reference_count"] = reference_count;
  result["moving_count"] = moving_count;
  result["tolerance_px"] = tolerance_px;
  result["max_abs_dx"] = max_abs_dx;
  result["max_abs_dy"] = max_abs_dy;
  result["prior_dx"] = prior_dx;
  result["prior_dy"] = prior_dy;
  result["prior_radius_px"] = prior_radius_px;
  result["model"] = "catalog_pair_offset_translation";
  return result;
}

py::dict estimate_similarity_from_pairs_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("matched coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(reference_x_info, moving_x_info);
  require_same_shape(reference_x_info, moving_y_info);
  const int count = static_cast<int>(reference_x_info.shape[0]);
  if (count <= 0) {
    throw std::invalid_argument("matched coordinate arrays must be non-empty");
  }

  constexpr int threads = 256;
  const int blocks = std::min(4096, std::max(1, (count + threads - 1) / threads));
  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_valid_count = nullptr;
  int* d_status = nullptr;
  double* d_partial_sums = nullptr;
  unsigned long long* d_partial_count = nullptr;
  double* d_partial_residual_sums = nullptr;
  std::array<float, 9> host_matrix{};
  float scale = 1.0f;
  float rotation_rad = 0.0f;
  float rms_px = std::numeric_limits<float>::quiet_NaN();
  int valid_count = 0;
  int status = 1;

  try {
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity reference y)");
    check_cuda(
        cudaMalloc(&d_moving_x, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity moving y)");
    check_cuda(cudaMalloc(&d_matrix, host_matrix.size() * sizeof(float)), "cudaMalloc(similarity matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(similarity scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(similarity rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(similarity rms)");
    check_cuda(cudaMalloc(&d_valid_count, sizeof(int)), "cudaMalloc(similarity valid count)");
    check_cuda(cudaMalloc(&d_status, sizeof(int)), "cudaMalloc(similarity status)");
    check_cuda(
        cudaMalloc(&d_partial_sums, static_cast<std::size_t>(blocks) * 7 * sizeof(double)),
        "cudaMalloc(similarity partial sums)");
    check_cuda(
        cudaMalloc(&d_partial_count, static_cast<std::size_t>(blocks) * sizeof(unsigned long long)),
        "cudaMalloc(similarity partial count)");
    check_cuda(
        cudaMalloc(&d_partial_residual_sums, static_cast<std::size_t>(blocks) * sizeof(double)),
        "cudaMalloc(similarity partial residual sums)");
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity reference y)");
    check_cuda(
        cudaMemcpy(
            d_moving_x,
            moving_x_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity moving x)");
    check_cuda(
        cudaMemcpy(
            d_moving_y,
            moving_y_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity moving y)");
    glass_estimate_similarity_from_pairs_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_matrix,
        d_scale,
        d_rotation_rad,
        d_rms_px,
        d_valid_count,
        d_status,
        d_partial_sums,
        d_partial_count,
        d_partial_residual_sums,
        count,
        blocks);
    check_cuda(cudaGetLastError(), "estimate_similarity_from_pairs_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_pairs_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity matrix)");
    check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity scale)");
    check_cuda(
        cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity rotation)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity rms)");
    check_cuda(
        cudaMemcpy(&valid_count, d_valid_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity valid count)");
    check_cuda(cudaMemcpy(&status, d_status, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity status)");
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_valid_count);
    cudaFree(d_status);
    cudaFree(d_partial_sums);
    cudaFree(d_partial_count);
    cudaFree(d_partial_residual_sums);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_valid_count);
  cudaFree(d_status);
  cudaFree(d_partial_sums);
  cudaFree(d_partial_count);
  cudaFree(d_partial_residual_sums);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list matrix_row;
    for (int col = 0; col < 3; ++col) {
      matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(matrix_row);
  }
  py::dict result;
  result["matrix"] = matrix_rows;
  result["scale"] = scale;
  result["rotation_rad"] = rotation_rad;
  result["rms_px"] = rms_px;
  result["valid_pairs"] = valid_count;
  result["input_pairs"] = count;
  result["status"] = status == 0 ? "ok" : "failed";
  result["status_code"] = status;
  result["model"] = "matched_pair_similarity_cuda";
  return result;
}

py::dict triangle_asterism_descriptors_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> x,
    py::array_t<float, py::array::c_style | py::array::forcecast> y,
    int max_stars,
    int neighbors,
    int max_descriptors) {
  const py::buffer_info x_info = x.request();
  const py::buffer_info y_info = y.request();
  if (x_info.ndim != 1 || y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(x_info, y_info);
  if (max_stars < 0) {
    throw std::invalid_argument("max_stars must be non-negative");
  }
  if (max_descriptors < 0) {
    throw std::invalid_argument("max_descriptors must be non-negative");
  }
  const int input_count = static_cast<int>(x_info.shape[0]);
  const int count = std::min(input_count, max_stars);
  int neighbor_count = std::min(count, neighbors);
  neighbor_count = std::max(3, neighbor_count);
  neighbor_count = std::min(16, neighbor_count);
  const int combos_per_anchor = neighbor_count * (neighbor_count - 1) * (neighbor_count - 2) / 6;
  const int raw_count = count >= 3 ? count * combos_per_anchor : 0;

  py::array_t<float> descriptor_array({0, 2});
  py::array_t<int> index_array({0, 3});
  py::array_t<float> area_array({0});
  py::dict empty_result;
  if (count < 3 || max_descriptors == 0 || raw_count == 0) {
    empty_result["count"] = 0;
    empty_result["raw_count"] = raw_count;
    empty_result["max_stars"] = max_stars;
    empty_result["neighbors"] = neighbor_count;
    empty_result["descriptors"] = descriptor_array;
    empty_result["indices"] = index_array;
    empty_result["areas"] = area_array;
    empty_result["model"] = "triangle_asterism_descriptors_cuda";
    return empty_result;
  }

  float* d_x = nullptr;
  float* d_y = nullptr;
  float* d_descriptors = nullptr;
  int* d_indices = nullptr;
  float* d_areas = nullptr;
  unsigned char* d_valid = nullptr;
  std::vector<float> host_descriptors(static_cast<std::size_t>(raw_count) * 2, std::numeric_limits<float>::quiet_NaN());
  std::vector<int> host_indices(static_cast<std::size_t>(raw_count) * 3, -1);
  std::vector<float> host_areas(static_cast<std::size_t>(raw_count), std::numeric_limits<float>::quiet_NaN());
  std::vector<unsigned char> host_valid(static_cast<std::size_t>(raw_count), 0);
  try {
    check_cuda(cudaMalloc(&d_x, static_cast<std::size_t>(count) * sizeof(float)), "cudaMalloc(triangle x)");
    check_cuda(cudaMalloc(&d_y, static_cast<std::size_t>(count) * sizeof(float)), "cudaMalloc(triangle y)");
    check_cuda(
        cudaMalloc(&d_descriptors, static_cast<std::size_t>(raw_count) * 2 * sizeof(float)),
        "cudaMalloc(triangle descriptors)");
    check_cuda(
        cudaMalloc(&d_indices, static_cast<std::size_t>(raw_count) * 3 * sizeof(int)),
        "cudaMalloc(triangle indices)");
    check_cuda(cudaMalloc(&d_areas, static_cast<std::size_t>(raw_count) * sizeof(float)), "cudaMalloc(triangle areas)");
    check_cuda(cudaMalloc(&d_valid, static_cast<std::size_t>(raw_count) * sizeof(unsigned char)), "cudaMalloc(triangle valid)");
    check_cuda(cudaMemcpy(d_x, x_info.ptr, static_cast<std::size_t>(count) * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(triangle x)");
    check_cuda(cudaMemcpy(d_y, y_info.ptr, static_cast<std::size_t>(count) * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(triangle y)");
    glass_triangle_asterism_descriptors_f32_launch(
        d_x,
        d_y,
        d_descriptors,
        d_indices,
        d_areas,
        d_valid,
        count,
        neighbor_count,
        raw_count);
    check_cuda(cudaGetLastError(), "triangle_asterism_descriptors_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "triangle_asterism_descriptors_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_descriptors.data(), d_descriptors, host_descriptors.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle descriptors)");
    check_cuda(
        cudaMemcpy(host_indices.data(), d_indices, host_indices.size() * sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle indices)");
    check_cuda(
        cudaMemcpy(host_areas.data(), d_areas, host_areas.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle areas)");
    check_cuda(
        cudaMemcpy(host_valid.data(), d_valid, host_valid.size() * sizeof(unsigned char), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle valid)");
  } catch (...) {
    cudaFree(d_x);
    cudaFree(d_y);
    cudaFree(d_descriptors);
    cudaFree(d_indices);
    cudaFree(d_areas);
    cudaFree(d_valid);
    throw;
  }
  cudaFree(d_x);
  cudaFree(d_y);
  cudaFree(d_descriptors);
  cudaFree(d_indices);
  cudaFree(d_areas);
  cudaFree(d_valid);

  struct TriangleDescriptor {
    int key0;
    int key1;
    int key2;
    float descriptor0;
    float descriptor1;
    int index0;
    int index1;
    int index2;
    float area;
  };
  std::vector<TriangleDescriptor> triangles;
  triangles.reserve(static_cast<std::size_t>(raw_count));
  for (int slot = 0; slot < raw_count; ++slot) {
    if (host_valid[static_cast<std::size_t>(slot)] == 0) {
      continue;
    }
    int index0 = host_indices[static_cast<std::size_t>(slot) * 3 + 0];
    int index1 = host_indices[static_cast<std::size_t>(slot) * 3 + 1];
    int index2 = host_indices[static_cast<std::size_t>(slot) * 3 + 2];
    if (index0 < 0 || index1 < 0 || index2 < 0) {
      continue;
    }
    std::array<int, 3> key{index0, index1, index2};
    std::sort(key.begin(), key.end());
    triangles.push_back(
        TriangleDescriptor{
            key[0],
            key[1],
            key[2],
            host_descriptors[static_cast<std::size_t>(slot) * 2 + 0],
            host_descriptors[static_cast<std::size_t>(slot) * 2 + 1],
            index0,
            index1,
            index2,
            host_areas[static_cast<std::size_t>(slot)]});
  }
  std::sort(triangles.begin(), triangles.end(), [](const TriangleDescriptor& left, const TriangleDescriptor& right) {
    if (left.key0 != right.key0) {
      return left.key0 < right.key0;
    }
    if (left.key1 != right.key1) {
      return left.key1 < right.key1;
    }
    return left.key2 < right.key2;
  });
  std::vector<TriangleDescriptor> unique_triangles;
  unique_triangles.reserve(triangles.size());
  for (const auto& triangle : triangles) {
    if (!unique_triangles.empty()) {
      const auto& previous = unique_triangles.back();
      if (previous.key0 == triangle.key0 && previous.key1 == triangle.key1 && previous.key2 == triangle.key2) {
        continue;
      }
    }
    unique_triangles.push_back(triangle);
  }
  std::sort(
      unique_triangles.begin(),
      unique_triangles.end(),
      [](const TriangleDescriptor& left, const TriangleDescriptor& right) {
        if (left.area != right.area) {
          return left.area > right.area;
        }
        if (left.key0 != right.key0) {
          return left.key0 < right.key0;
        }
        if (left.key1 != right.key1) {
          return left.key1 < right.key1;
        }
        return left.key2 < right.key2;
      });

  const int output_count =
      std::min(static_cast<int>(unique_triangles.size()), max_descriptors);
  descriptor_array = py::array_t<float>({output_count, 2});
  index_array = py::array_t<int>({output_count, 3});
  area_array = py::array_t<float>({output_count});
  auto descriptor_info = descriptor_array.request();
  auto index_info = index_array.request();
  auto area_info = area_array.request();
  float* descriptor_ptr = static_cast<float*>(descriptor_info.ptr);
  int* index_ptr = static_cast<int*>(index_info.ptr);
  float* area_ptr = static_cast<float*>(area_info.ptr);
  for (int i = 0; i < output_count; ++i) {
    const auto& triangle = unique_triangles[static_cast<std::size_t>(i)];
    descriptor_ptr[i * 2 + 0] = triangle.descriptor0;
    descriptor_ptr[i * 2 + 1] = triangle.descriptor1;
    index_ptr[i * 3 + 0] = triangle.index0;
    index_ptr[i * 3 + 1] = triangle.index1;
    index_ptr[i * 3 + 2] = triangle.index2;
    area_ptr[i] = triangle.area;
  }

  py::dict result;
  result["count"] = output_count;
  result["raw_count"] = raw_count;
  result["max_stars"] = max_stars;
  result["neighbors"] = neighbor_count;
  result["descriptors"] = descriptor_array;
  result["indices"] = index_array;
  result["areas"] = area_array;
  result["model"] = "triangle_asterism_descriptors_cuda";
  return result;
}

py::dict estimate_similarity_from_triangle_descriptors_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_descriptors,
    py::array_t<int, py::array::c_style | py::array::forcecast> reference_indices,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_descriptors,
    py::array_t<int, py::array::c_style | py::array::forcecast> moving_indices,
    float tolerance_px,
    float descriptor_radius) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  const py::buffer_info reference_descriptor_info = reference_descriptors.request();
  const py::buffer_info reference_index_info = reference_indices.request();
  const py::buffer_info moving_descriptor_info = moving_descriptors.request();
  const py::buffer_info moving_index_info = moving_indices.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(moving_x_info, moving_y_info);
  if (reference_descriptor_info.ndim != 2 || reference_descriptor_info.shape[1] != 2 ||
      moving_descriptor_info.ndim != 2 || moving_descriptor_info.shape[1] != 2) {
    throw std::invalid_argument("triangle descriptors must have shape (N, 2)");
  }
  if (reference_index_info.ndim != 2 || reference_index_info.shape[1] != 3 ||
      moving_index_info.ndim != 2 || moving_index_info.shape[1] != 3) {
    throw std::invalid_argument("triangle indices must have shape (N, 3)");
  }
  if (reference_descriptor_info.shape[0] != reference_index_info.shape[0] ||
      moving_descriptor_info.shape[0] != moving_index_info.shape[0]) {
    throw std::invalid_argument("descriptor and index row counts must match");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (descriptor_radius < 0.0f) {
    throw std::invalid_argument("descriptor_radius must be non-negative");
  }
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int moving_count = static_cast<int>(moving_x_info.shape[0]);
  const int reference_descriptor_count = static_cast<int>(reference_descriptor_info.shape[0]);
  const int moving_descriptor_count = static_cast<int>(moving_descriptor_info.shape[0]);
  if (reference_count < 3 || moving_count < 3 ||
      reference_descriptor_count == 0 || moving_descriptor_count == 0) {
    throw std::invalid_argument("triangle descriptor similarity requires at least one descriptor and three stars");
  }
  const int candidate_count = reference_descriptor_count * moving_descriptor_count * 2;

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_reference_descriptors = nullptr;
  int* d_reference_indices = nullptr;
  float* d_moving_descriptors = nullptr;
  int* d_moving_indices = nullptr;
  float* d_candidate_params = nullptr;
  int* d_candidate_scores = nullptr;
  float* d_candidate_rms = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_best_inliers = nullptr;
  int* d_best_index = nullptr;
  std::array<float, 9> host_matrix{};
  float scale = 1.0f;
  float rotation_rad = 0.0f;
  float rms_px = std::numeric_limits<float>::quiet_NaN();
  int best_inliers = 0;
  int best_index = -1;
  try {
    check_cuda(cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)), "cudaMalloc(triangle similarity reference x)");
    check_cuda(cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)), "cudaMalloc(triangle similarity reference y)");
    check_cuda(cudaMalloc(&d_moving_x, static_cast<std::size_t>(moving_count) * sizeof(float)), "cudaMalloc(triangle similarity moving x)");
    check_cuda(cudaMalloc(&d_moving_y, static_cast<std::size_t>(moving_count) * sizeof(float)), "cudaMalloc(triangle similarity moving y)");
    check_cuda(
        cudaMalloc(&d_reference_descriptors, static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float)),
        "cudaMalloc(triangle similarity reference descriptors)");
    check_cuda(
        cudaMalloc(&d_reference_indices, static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int)),
        "cudaMalloc(triangle similarity reference indices)");
    check_cuda(
        cudaMalloc(&d_moving_descriptors, static_cast<std::size_t>(moving_descriptor_count) * 2 * sizeof(float)),
        "cudaMalloc(triangle similarity moving descriptors)");
    check_cuda(
        cudaMalloc(&d_moving_indices, static_cast<std::size_t>(moving_descriptor_count) * 3 * sizeof(int)),
        "cudaMalloc(triangle similarity moving indices)");
    check_cuda(
        cudaMalloc(&d_candidate_params, static_cast<std::size_t>(candidate_count) * 4 * sizeof(float)),
        "cudaMalloc(triangle similarity candidate params)");
    check_cuda(
        cudaMalloc(&d_candidate_scores, static_cast<std::size_t>(candidate_count) * sizeof(int)),
        "cudaMalloc(triangle similarity candidate scores)");
    check_cuda(
        cudaMalloc(&d_candidate_rms, static_cast<std::size_t>(candidate_count) * sizeof(float)),
        "cudaMalloc(triangle similarity candidate rms)");
    check_cuda(cudaMalloc(&d_matrix, host_matrix.size() * sizeof(float)), "cudaMalloc(triangle similarity matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(triangle similarity scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(triangle similarity rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(triangle similarity rms)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(triangle similarity best inliers)");
    check_cuda(cudaMalloc(&d_best_index, sizeof(int)), "cudaMalloc(triangle similarity best index)");
    check_cuda(
        cudaMemcpy(d_reference_x, reference_x_info.ptr, static_cast<std::size_t>(reference_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference x)");
    check_cuda(
        cudaMemcpy(d_reference_y, reference_y_info.ptr, static_cast<std::size_t>(reference_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference y)");
    check_cuda(
        cudaMemcpy(d_moving_x, moving_x_info.ptr, static_cast<std::size_t>(moving_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving x)");
    check_cuda(
        cudaMemcpy(d_moving_y, moving_y_info.ptr, static_cast<std::size_t>(moving_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving y)");
    check_cuda(
        cudaMemcpy(
            d_reference_descriptors,
            reference_descriptor_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference descriptors)");
    check_cuda(
        cudaMemcpy(
            d_reference_indices,
            reference_index_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference indices)");
    check_cuda(
        cudaMemcpy(
            d_moving_descriptors,
            moving_descriptor_info.ptr,
            static_cast<std::size_t>(moving_descriptor_count) * 2 * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving descriptors)");
    check_cuda(
        cudaMemcpy(
            d_moving_indices,
            moving_index_info.ptr,
            static_cast<std::size_t>(moving_descriptor_count) * 3 * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving indices)");
    glass_estimate_similarity_from_triangle_descriptors_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_reference_descriptors,
        d_reference_indices,
        d_moving_descriptors,
        d_moving_indices,
        d_candidate_params,
        d_candidate_scores,
        d_candidate_rms,
        d_matrix,
        d_scale,
        d_rotation_rad,
        d_rms_px,
        d_best_inliers,
        d_best_index,
        reference_count,
        moving_count,
        reference_descriptor_count,
        moving_descriptor_count,
        candidate_count,
        tolerance_px,
        descriptor_radius);
    check_cuda(cudaGetLastError(), "estimate_similarity_from_triangle_descriptors_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_triangle_descriptors_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle similarity matrix)");
    check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(triangle similarity scale)");
    check_cuda(
        cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle similarity rotation)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(triangle similarity rms)");
    check_cuda(
        cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle similarity best inliers)");
    check_cuda(cudaMemcpy(&best_index, d_best_index, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(triangle similarity best index)");
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_reference_descriptors);
    cudaFree(d_reference_indices);
    cudaFree(d_moving_descriptors);
    cudaFree(d_moving_indices);
    cudaFree(d_candidate_params);
    cudaFree(d_candidate_scores);
    cudaFree(d_candidate_rms);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_best_inliers);
    cudaFree(d_best_index);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_reference_descriptors);
  cudaFree(d_reference_indices);
  cudaFree(d_moving_descriptors);
  cudaFree(d_moving_indices);
  cudaFree(d_candidate_params);
  cudaFree(d_candidate_scores);
  cudaFree(d_candidate_rms);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_best_inliers);
  cudaFree(d_best_index);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list matrix_row;
    for (int col = 0; col < 3; ++col) {
      matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(matrix_row);
  }
  py::dict result;
  result["matrix"] = matrix_rows;
  result["scale"] = scale;
  result["rotation_rad"] = rotation_rad;
  result["rms_px"] = rms_px;
  result["inliers"] = best_inliers;
  result["best_candidate_index"] = best_index;
  result["candidate_count"] = candidate_count;
  result["reference_count"] = reference_count;
  result["moving_count"] = moving_count;
  result["reference_descriptor_count"] = reference_descriptor_count;
  result["moving_descriptor_count"] = moving_descriptor_count;
  result["tolerance_px"] = tolerance_px;
  result["descriptor_radius"] = descriptor_radius;
  result["status"] = best_inliers > 0 ? "ok" : "failed";
  result["model"] = "triangle_descriptor_similarity_cuda";
  result["best_reduction_mode"] = "single_block_parallel_score_rms_index";
  return result;
}

py::list estimate_similarity_from_triangle_descriptors_batch_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_descriptors,
    py::array_t<int, py::array::c_style | py::array::forcecast> reference_indices,
    py::sequence moving_x_list,
    py::sequence moving_y_list,
    py::sequence moving_descriptors_list,
    py::sequence moving_indices_list,
    float tolerance_px,
    float descriptor_radius) {
  const auto batch_total_start = Clock::now();
  const py::ssize_t batch_count = py::len(moving_x_list);
  if (static_cast<py::ssize_t>(py::len(moving_y_list)) != batch_count ||
      static_cast<py::ssize_t>(py::len(moving_descriptors_list)) != batch_count ||
      static_cast<py::ssize_t>(py::len(moving_indices_list)) != batch_count) {
    throw std::invalid_argument("moving batch lists must have the same length");
  }
  py::list results;
  if (batch_count == 0) {
    return results;
  }
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info reference_descriptor_info = reference_descriptors.request();
  const py::buffer_info reference_index_info = reference_indices.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1) {
    throw std::invalid_argument("reference catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  if (reference_descriptor_info.ndim != 2 || reference_descriptor_info.shape[1] != 2) {
    throw std::invalid_argument("reference triangle descriptors must have shape (N, 2)");
  }
  if (reference_index_info.ndim != 2 || reference_index_info.shape[1] != 3) {
    throw std::invalid_argument("reference triangle indices must have shape (N, 3)");
  }
  if (reference_descriptor_info.shape[0] != reference_index_info.shape[0]) {
    throw std::invalid_argument("reference descriptor and index row counts must match");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (descriptor_radius < 0.0f) {
    throw std::invalid_argument("descriptor_radius must be non-negative");
  }
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int reference_descriptor_count = static_cast<int>(reference_descriptor_info.shape[0]);
  if (reference_count < 3 || reference_descriptor_count == 0) {
    throw std::invalid_argument("triangle descriptor batch similarity requires reference descriptors and three stars");
  }
  const std::size_t reference_device_bytes =
      static_cast<std::size_t>(reference_count) * 2 * sizeof(float) +
      static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float) +
      static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int);

  using FloatArray = py::array_t<float, py::array::c_style | py::array::forcecast>;
  using IntArray = py::array_t<int, py::array::c_style | py::array::forcecast>;
  const auto host_prepare_start = Clock::now();
  std::vector<FloatArray> moving_x_arrays;
  std::vector<FloatArray> moving_y_arrays;
  std::vector<FloatArray> moving_descriptor_arrays;
  std::vector<IntArray> moving_index_arrays;
  moving_x_arrays.reserve(static_cast<std::size_t>(batch_count));
  moving_y_arrays.reserve(static_cast<std::size_t>(batch_count));
  moving_descriptor_arrays.reserve(static_cast<std::size_t>(batch_count));
  moving_index_arrays.reserve(static_cast<std::size_t>(batch_count));
  std::size_t max_moving_count = 0;
  std::size_t max_moving_descriptor_count = 0;
  std::size_t max_candidate_count = 0;
  for (py::ssize_t batch_index = 0; batch_index < batch_count; ++batch_index) {
    auto moving_x = FloatArray::ensure(moving_x_list[batch_index]);
    auto moving_y = FloatArray::ensure(moving_y_list[batch_index]);
    auto moving_descriptors = FloatArray::ensure(moving_descriptors_list[batch_index]);
    auto moving_indices = IntArray::ensure(moving_indices_list[batch_index]);
    if (!moving_x || !moving_y || !moving_descriptors || !moving_indices) {
      throw std::invalid_argument("moving batch items must be convertible to arrays");
    }
    const py::buffer_info moving_x_info = moving_x.request();
    const py::buffer_info moving_y_info = moving_y.request();
    const py::buffer_info moving_descriptor_info = moving_descriptors.request();
    const py::buffer_info moving_index_info = moving_indices.request();
    if (moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
      throw std::invalid_argument("moving catalog coordinate arrays must be one-dimensional");
    }
    require_same_shape(moving_x_info, moving_y_info);
    if (moving_descriptor_info.ndim != 2 || moving_descriptor_info.shape[1] != 2) {
      throw std::invalid_argument("moving triangle descriptors must have shape (N, 2)");
    }
    if (moving_index_info.ndim != 2 || moving_index_info.shape[1] != 3) {
      throw std::invalid_argument("moving triangle indices must have shape (N, 3)");
    }
    if (moving_descriptor_info.shape[0] != moving_index_info.shape[0]) {
      throw std::invalid_argument("moving descriptor and index row counts must match");
    }
    const int moving_count = static_cast<int>(moving_x_info.shape[0]);
    const int moving_descriptor_count = static_cast<int>(moving_descriptor_info.shape[0]);
    if (moving_count < 3 || moving_descriptor_count == 0) {
      throw std::invalid_argument("triangle descriptor batch similarity requires moving descriptors and three stars");
    }
    max_moving_count = std::max(max_moving_count, static_cast<std::size_t>(moving_count));
    max_moving_descriptor_count =
        std::max(max_moving_descriptor_count, static_cast<std::size_t>(moving_descriptor_count));
    max_candidate_count = std::max(
        max_candidate_count,
        static_cast<std::size_t>(reference_descriptor_count) *
            static_cast<std::size_t>(moving_descriptor_count) * 2);
    moving_x_arrays.push_back(std::move(moving_x));
    moving_y_arrays.push_back(std::move(moving_y));
    moving_descriptor_arrays.push_back(std::move(moving_descriptors));
    moving_index_arrays.push_back(std::move(moving_indices));
  }
  const double host_prepare_s = seconds_since(host_prepare_start);
  const std::size_t moving_device_bytes =
      max_moving_count * 2 * sizeof(float) +
      max_moving_descriptor_count * 2 * sizeof(float) +
      max_moving_descriptor_count * 3 * sizeof(int);
  const std::size_t output_device_bytes =
      max_candidate_count * 4 * sizeof(float) +
      max_candidate_count * sizeof(int) +
      max_candidate_count * sizeof(float) +
      9 * sizeof(float) +
      sizeof(float) * 3 +
      sizeof(int) * 2;

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_reference_descriptors = nullptr;
  int* d_reference_indices = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_moving_descriptors = nullptr;
  int* d_moving_indices = nullptr;
  float* d_candidate_params = nullptr;
  int* d_candidate_scores = nullptr;
  float* d_candidate_rms = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_best_inliers = nullptr;
  int* d_best_index = nullptr;
  double reference_alloc_s = 0.0;
  double reference_upload_s = 0.0;
  double workspace_alloc_s = 0.0;
  try {
    const auto reference_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(batch triangle similarity reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(batch triangle similarity reference y)");
    check_cuda(
        cudaMalloc(
            &d_reference_descriptors,
            static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float)),
        "cudaMalloc(batch triangle similarity reference descriptors)");
    check_cuda(
        cudaMalloc(
            &d_reference_indices,
            static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int)),
        "cudaMalloc(batch triangle similarity reference indices)");
    reference_alloc_s = seconds_since(reference_alloc_start);
    const auto reference_upload_start = Clock::now();
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference y)");
    check_cuda(
        cudaMemcpy(
            d_reference_descriptors,
            reference_descriptor_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference descriptors)");
    check_cuda(
        cudaMemcpy(
            d_reference_indices,
            reference_index_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference indices)");
    reference_upload_s = seconds_since(reference_upload_start);
    const auto workspace_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&d_moving_x, max_moving_count * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, max_moving_count * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable moving y)");
    check_cuda(
        cudaMalloc(&d_moving_descriptors, max_moving_descriptor_count * 2 * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable moving descriptors)");
    check_cuda(
        cudaMalloc(&d_moving_indices, max_moving_descriptor_count * 3 * sizeof(int)),
        "cudaMalloc(batch triangle similarity reusable moving indices)");
    check_cuda(
        cudaMalloc(&d_candidate_params, max_candidate_count * 4 * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable candidate params)");
    check_cuda(
        cudaMalloc(&d_candidate_scores, max_candidate_count * sizeof(int)),
        "cudaMalloc(batch triangle similarity reusable candidate scores)");
    check_cuda(
        cudaMalloc(&d_candidate_rms, max_candidate_count * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable candidate rms)");
    check_cuda(cudaMalloc(&d_matrix, 9 * sizeof(float)), "cudaMalloc(batch triangle similarity reusable matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(batch triangle similarity reusable scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(batch triangle similarity reusable rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(batch triangle similarity reusable rms)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(batch triangle similarity reusable best inliers)");
    check_cuda(cudaMalloc(&d_best_index, sizeof(int)), "cudaMalloc(batch triangle similarity reusable best index)");
    workspace_alloc_s = seconds_since(workspace_alloc_start);

  for (py::ssize_t batch_index = 0; batch_index < batch_count; ++batch_index) {
    const auto frame_total_start = Clock::now();
    const auto& moving_x = moving_x_arrays[static_cast<std::size_t>(batch_index)];
    const auto& moving_y = moving_y_arrays[static_cast<std::size_t>(batch_index)];
    const auto& moving_descriptors = moving_descriptor_arrays[static_cast<std::size_t>(batch_index)];
    const auto& moving_indices = moving_index_arrays[static_cast<std::size_t>(batch_index)];
    const py::buffer_info moving_x_info = moving_x.request();
    const py::buffer_info moving_y_info = moving_y.request();
    const py::buffer_info moving_descriptor_info = moving_descriptors.request();
    const py::buffer_info moving_index_info = moving_indices.request();
    const int moving_count = static_cast<int>(moving_x_info.shape[0]);
    const int moving_descriptor_count = static_cast<int>(moving_descriptor_info.shape[0]);
    const int candidate_count = reference_descriptor_count * moving_descriptor_count * 2;

    std::array<float, 9> host_matrix{};
    float scale = 1.0f;
    float rotation_rad = 0.0f;
    float rms_px = std::numeric_limits<float>::quiet_NaN();
    int best_inliers = 0;
    int best_index = -1;
      const auto moving_upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              d_moving_x,
              moving_x_info.ptr,
              static_cast<std::size_t>(moving_count) * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving x)");
      check_cuda(
          cudaMemcpy(
              d_moving_y,
              moving_y_info.ptr,
              static_cast<std::size_t>(moving_count) * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving y)");
      check_cuda(
          cudaMemcpy(
              d_moving_descriptors,
              moving_descriptor_info.ptr,
              static_cast<std::size_t>(moving_descriptor_count) * 2 * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving descriptors)");
      check_cuda(
          cudaMemcpy(
              d_moving_indices,
              moving_index_info.ptr,
              static_cast<std::size_t>(moving_descriptor_count) * 3 * sizeof(int),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving indices)");
      const double moving_upload_s = seconds_since(moving_upload_start);
      const auto kernel_sync_start = Clock::now();
      glass_estimate_similarity_from_triangle_descriptors_f32_launch(
          d_reference_x,
          d_reference_y,
          d_moving_x,
          d_moving_y,
          d_reference_descriptors,
          d_reference_indices,
          d_moving_descriptors,
          d_moving_indices,
          d_candidate_params,
          d_candidate_scores,
          d_candidate_rms,
          d_matrix,
          d_scale,
          d_rotation_rad,
          d_rms_px,
          d_best_inliers,
          d_best_index,
          reference_count,
          moving_count,
          reference_descriptor_count,
          moving_descriptor_count,
          candidate_count,
          tolerance_px,
          descriptor_radius);
      check_cuda(cudaGetLastError(), "estimate_similarity_from_triangle_descriptors_batch_f32 kernel launch");
      check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_triangle_descriptors_batch_f32 synchronize");
      const double kernel_sync_s = seconds_since(kernel_sync_start);
      const auto output_download_start = Clock::now();
      check_cuda(
          cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(batch triangle similarity matrix)");
      check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(batch triangle similarity scale)");
      check_cuda(
          cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(batch triangle similarity rotation)");
      check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(batch triangle similarity rms)");
      check_cuda(
          cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(batch triangle similarity best inliers)");
      check_cuda(cudaMemcpy(&best_index, d_best_index, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(batch triangle similarity best index)");
      const double output_download_s = seconds_since(output_download_start);
      const double frame_total_s = seconds_since(frame_total_start);

    py::list matrix_rows;
    for (int row = 0; row < 3; ++row) {
      py::list matrix_row;
      for (int col = 0; col < 3; ++col) {
        matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
      }
      matrix_rows.append(matrix_row);
    }
    py::dict result;
    result["matrix"] = matrix_rows;
    result["scale"] = scale;
    result["rotation_rad"] = rotation_rad;
    result["rms_px"] = rms_px;
    result["inliers"] = best_inliers;
    result["best_candidate_index"] = best_index;
    result["candidate_count"] = candidate_count;
    result["reference_count"] = reference_count;
    result["moving_count"] = moving_count;
    result["reference_descriptor_count"] = reference_descriptor_count;
    result["moving_descriptor_count"] = moving_descriptor_count;
    result["tolerance_px"] = tolerance_px;
    result["descriptor_radius"] = descriptor_radius;
    result["status"] = best_inliers > 0 ? "ok" : "failed";
    result["model"] = "triangle_descriptor_similarity_cuda";
    result["best_reduction_mode"] = "single_block_parallel_score_rms_index";
    result["batch_index"] = static_cast<int>(batch_index);
    result["batch_count"] = static_cast<int>(batch_count);
    result["batch_model"] = "triangle_descriptor_similarity_cuda_batch_shared_reference_device";
    result["reference_device_reuse"] = true;
    result["reference_device_bytes"] = static_cast<unsigned long long>(reference_device_bytes);
    result["moving_device_reuse"] = true;
    result["moving_device_bytes"] = static_cast<unsigned long long>(moving_device_bytes);
    result["output_device_reuse"] = true;
    result["output_device_bytes"] = static_cast<unsigned long long>(output_device_bytes);
    result["batch_timing_model"] = "per_frame_reused_buffers_sync_timed";
    result["batch_host_prepare_s"] = host_prepare_s;
    result["batch_reference_alloc_s"] = reference_alloc_s;
    result["batch_reference_upload_s"] = reference_upload_s;
    result["batch_workspace_alloc_s"] = workspace_alloc_s;
    result["batch_frame_moving_upload_s"] = moving_upload_s;
    result["batch_frame_kernel_sync_s"] = kernel_sync_s;
    result["batch_frame_output_download_s"] = output_download_s;
    result["batch_frame_total_s"] = frame_total_s;
    result["batch_total_elapsed_s_at_result"] = seconds_since(batch_total_start);
    results.append(result);
  }
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_reference_descriptors);
    cudaFree(d_reference_indices);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_moving_descriptors);
    cudaFree(d_moving_indices);
    cudaFree(d_candidate_params);
    cudaFree(d_candidate_scores);
    cudaFree(d_candidate_rms);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_best_inliers);
    cudaFree(d_best_index);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_reference_descriptors);
  cudaFree(d_reference_indices);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_moving_descriptors);
  cudaFree(d_moving_indices);
  cudaFree(d_candidate_params);
  cudaFree(d_candidate_scores);
  cudaFree(d_candidate_rms);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_best_inliers);
  cudaFree(d_best_index);
  return results;
}

py::dict estimate_similarity_from_catalogs_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y,
    float tolerance_px,
    float min_pair_distance,
    float prior_dx,
    float prior_dy,
    float prior_radius_px,
    float min_scale,
    float max_scale,
    float max_abs_rotation_rad,
    int top_k) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(moving_x_info, moving_y_info);
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int moving_count = static_cast<int>(moving_x_info.shape[0]);
  if (reference_count < 2 || moving_count < 2) {
    throw std::invalid_argument("similarity catalog estimation requires at least two stars per catalog");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (min_pair_distance < 0.0f) {
    throw std::invalid_argument("min_pair_distance must be non-negative");
  }
  if (prior_radius_px < 0.0f) {
    prior_dx = 0.0f;
    prior_dy = 0.0f;
  }
  if (min_scale < 0.0f || max_scale < min_scale) {
    throw std::invalid_argument("scale constraints must satisfy 0 <= min_scale <= max_scale");
  }
  if (max_abs_rotation_rad < 0.0f) {
    max_abs_rotation_rad = -1.0f;
  }
  if (top_k < 0) {
    throw std::invalid_argument("top_k must be non-negative");
  }
  const int candidate_count =
      reference_count * (reference_count - 1) * moving_count * (moving_count - 1);

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_candidate_params = nullptr;
  int* d_candidate_scores = nullptr;
  float* d_candidate_rms = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_best_inliers = nullptr;
  int* d_best_index = nullptr;
  int* d_refit_inliers = nullptr;
  int* d_refit_status = nullptr;
  float* d_refit_matrix = nullptr;
  float* d_refit_scale = nullptr;
  float* d_refit_rotation_rad = nullptr;
  float* d_refit_rms_px = nullptr;
  double* d_refit_partial_sums = nullptr;
  unsigned long long* d_refit_partial_count = nullptr;
  double* d_refit_partial_residual_sums = nullptr;
  std::array<float, 9> host_matrix{};
  float scale = 1.0f;
  float rotation_rad = 0.0f;
  float rms_px = std::numeric_limits<float>::quiet_NaN();
  int best_inliers = 0;
  int best_index = -1;
  int refit_inliers = 0;
  int refit_status = 0;
  float refit_rms_px = std::numeric_limits<float>::quiet_NaN();
  py::list top_candidates;
  constexpr int refit_threads = 256;
  const int refit_blocks = std::max(1, (moving_count + refit_threads - 1) / refit_threads);
  try {
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(similarity catalog reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(similarity catalog reference y)");
    check_cuda(
        cudaMalloc(&d_moving_x, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(similarity catalog moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(similarity catalog moving y)");
    check_cuda(
        cudaMalloc(&d_candidate_params, static_cast<std::size_t>(candidate_count) * 4 * sizeof(float)),
        "cudaMalloc(similarity catalog candidate params)");
    check_cuda(
        cudaMalloc(&d_candidate_scores, static_cast<std::size_t>(candidate_count) * sizeof(int)),
        "cudaMalloc(similarity catalog candidate scores)");
    check_cuda(
        cudaMalloc(&d_candidate_rms, static_cast<std::size_t>(candidate_count) * sizeof(float)),
        "cudaMalloc(similarity catalog candidate rms)");
    check_cuda(cudaMalloc(&d_matrix, host_matrix.size() * sizeof(float)), "cudaMalloc(similarity catalog matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(similarity catalog scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(similarity catalog rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(similarity catalog rms)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(similarity catalog best inliers)");
    check_cuda(cudaMalloc(&d_best_index, sizeof(int)), "cudaMalloc(similarity catalog best index)");
    check_cuda(cudaMalloc(&d_refit_inliers, sizeof(int)), "cudaMalloc(similarity catalog refit inliers)");
    check_cuda(cudaMalloc(&d_refit_status, sizeof(int)), "cudaMalloc(similarity catalog refit status)");
    check_cuda(
        cudaMalloc(&d_refit_matrix, host_matrix.size() * sizeof(float)),
        "cudaMalloc(similarity catalog refit matrix)");
    check_cuda(cudaMalloc(&d_refit_scale, sizeof(float)), "cudaMalloc(similarity catalog refit scale)");
    check_cuda(
        cudaMalloc(&d_refit_rotation_rad, sizeof(float)),
        "cudaMalloc(similarity catalog refit rotation)");
    check_cuda(cudaMalloc(&d_refit_rms_px, sizeof(float)), "cudaMalloc(similarity catalog refit rms)");
    check_cuda(
        cudaMalloc(&d_refit_partial_sums, static_cast<std::size_t>(refit_blocks) * 7 * sizeof(double)),
        "cudaMalloc(similarity catalog refit partial sums)");
    check_cuda(
        cudaMalloc(
            &d_refit_partial_count,
            static_cast<std::size_t>(refit_blocks) * sizeof(unsigned long long)),
        "cudaMalloc(similarity catalog refit partial count)");
    check_cuda(
        cudaMalloc(
            &d_refit_partial_residual_sums,
            static_cast<std::size_t>(refit_blocks) * sizeof(double)),
        "cudaMalloc(similarity catalog refit partial residual sums)");
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog reference y)");
    check_cuda(
        cudaMemcpy(
            d_moving_x,
            moving_x_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog moving x)");
    check_cuda(
        cudaMemcpy(
            d_moving_y,
            moving_y_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog moving y)");
    glass_estimate_similarity_from_catalogs_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_candidate_params,
        d_candidate_scores,
        d_candidate_rms,
        d_matrix,
        d_scale,
        d_rotation_rad,
        d_rms_px,
        d_best_inliers,
        d_best_index,
        d_refit_inliers,
        d_refit_status,
        d_refit_matrix,
        d_refit_scale,
        d_refit_rotation_rad,
        d_refit_rms_px,
        d_refit_partial_sums,
        d_refit_partial_count,
        d_refit_partial_residual_sums,
        refit_blocks,
        reference_count,
        moving_count,
        candidate_count,
        tolerance_px,
        min_pair_distance,
        prior_dx,
        prior_dy,
        prior_radius_px,
        min_scale,
        max_scale,
        max_abs_rotation_rad);
    check_cuda(cudaGetLastError(), "estimate_similarity_from_catalogs_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_catalogs_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog matrix)");
    check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity catalog scale)");
    check_cuda(
        cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog rotation)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity catalog rms)");
    check_cuda(
        cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog best inliers)");
    check_cuda(cudaMemcpy(&best_index, d_best_index, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity catalog best index)");
    check_cuda(
        cudaMemcpy(&refit_inliers, d_refit_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog refit inliers)");
    check_cuda(
        cudaMemcpy(&refit_status, d_refit_status, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog refit status)");
    check_cuda(
        cudaMemcpy(&refit_rms_px, d_refit_rms_px, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog refit rms)");
    if (top_k > 0) {
      std::vector<float> candidate_params(static_cast<std::size_t>(candidate_count) * 4, 0.0f);
      std::vector<int> candidate_scores(static_cast<std::size_t>(candidate_count), -1);
      std::vector<float> candidate_rms(static_cast<std::size_t>(candidate_count), std::numeric_limits<float>::quiet_NaN());
      check_cuda(
          cudaMemcpy(
              candidate_params.data(),
              d_candidate_params,
              candidate_params.size() * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(similarity catalog candidate params)");
      check_cuda(
          cudaMemcpy(
              candidate_scores.data(),
              d_candidate_scores,
              candidate_scores.size() * sizeof(int),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(similarity catalog candidate scores)");
      check_cuda(
          cudaMemcpy(
              candidate_rms.data(),
              d_candidate_rms,
              candidate_rms.size() * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(similarity catalog candidate rms)");
      const int per_score_limit = std::max(1, (top_k + 3) / 4);
      const int score_bucket_count = std::max(reference_count, moving_count) + 1;
      std::vector<std::vector<int>> per_score_best(static_cast<std::size_t>(score_bucket_count));
      std::vector<int> global_best;
      global_best.reserve(static_cast<std::size_t>(std::min(top_k, candidate_count)));
      auto insert_limited = [&](std::vector<int>& selected, int candidate_index, int limit) {
        if (limit <= 0) {
          return;
        }
        if (static_cast<int>(selected.size()) < limit) {
          selected.push_back(candidate_index);
        } else {
          int worst_pos = 0;
          for (int pos = 1; pos < static_cast<int>(selected.size()); ++pos) {
            const int current = selected[static_cast<std::size_t>(pos)];
            const int worst = selected[static_cast<std::size_t>(worst_pos)];
            const int current_score = candidate_scores[static_cast<std::size_t>(current)];
            const int worst_score = candidate_scores[static_cast<std::size_t>(worst)];
            const float current_rms = candidate_rms[static_cast<std::size_t>(current)];
            const float worst_rms = candidate_rms[static_cast<std::size_t>(worst)];
            if (current_score < worst_score ||
                (current_score == worst_score && current_rms > worst_rms)) {
              worst_pos = pos;
            }
          }
          const int worst = selected[static_cast<std::size_t>(worst_pos)];
          const int worst_score = candidate_scores[static_cast<std::size_t>(worst)];
          const float worst_rms = candidate_rms[static_cast<std::size_t>(worst)];
          const int score = candidate_scores[static_cast<std::size_t>(candidate_index)];
          const float rms = candidate_rms[static_cast<std::size_t>(candidate_index)];
          if (score > worst_score || (score == worst_score && rms < worst_rms)) {
            selected[static_cast<std::size_t>(worst_pos)] = candidate_index;
          }
        }
      };
      for (int i = 0; i < candidate_count; ++i) {
        const int score = candidate_scores[static_cast<std::size_t>(i)];
        const float rms = candidate_rms[static_cast<std::size_t>(i)];
        if (score < 0 || !std::isfinite(rms)) {
          continue;
        }
        insert_limited(global_best, i, top_k);
        if (score < score_bucket_count) {
          insert_limited(per_score_best[static_cast<std::size_t>(score)], i, per_score_limit);
        }
      }
      std::vector<int> selected;
      selected.reserve(static_cast<std::size_t>(std::min(top_k, candidate_count)));
      for (int score = score_bucket_count - 1; score >= 0 && static_cast<int>(selected.size()) < top_k; --score) {
        auto& bucket = per_score_best[static_cast<std::size_t>(score)];
        std::sort(bucket.begin(), bucket.end(), [&](int left, int right) {
          const float left_rms = candidate_rms[static_cast<std::size_t>(left)];
          const float right_rms = candidate_rms[static_cast<std::size_t>(right)];
          if (left_rms != right_rms) {
            return left_rms < right_rms;
          }
          return left < right;
        });
        for (const int candidate_index : bucket) {
          if (static_cast<int>(selected.size()) >= top_k) {
            break;
          }
          if (std::find(selected.begin(), selected.end(), candidate_index) == selected.end()) {
            selected.push_back(candidate_index);
          }
        }
      }
      for (const int candidate_index : global_best) {
        if (static_cast<int>(selected.size()) >= top_k) {
          break;
        }
        if (std::find(selected.begin(), selected.end(), candidate_index) == selected.end()) {
          selected.push_back(candidate_index);
        }
      }
      std::sort(selected.begin(), selected.end(), [&](int left, int right) {
        const int left_score = candidate_scores[static_cast<std::size_t>(left)];
        const int right_score = candidate_scores[static_cast<std::size_t>(right)];
        if (left_score != right_score) {
          return left_score > right_score;
        }
        const float left_rms = candidate_rms[static_cast<std::size_t>(left)];
        const float right_rms = candidate_rms[static_cast<std::size_t>(right)];
        if (left_rms != right_rms) {
          return left_rms < right_rms;
        }
        return left < right;
      });
      for (const int candidate_index : selected) {
        const std::size_t param_offset = static_cast<std::size_t>(candidate_index) * 4;
        const float a = candidate_params[param_offset + 0];
        const float b = candidate_params[param_offset + 1];
        const float tx = candidate_params[param_offset + 2];
        const float ty = candidate_params[param_offset + 3];
        py::list matrix_rows_candidate;
        py::list row0;
        row0.append(a);
        row0.append(-b);
        row0.append(tx);
        py::list row1;
        row1.append(b);
        row1.append(a);
        row1.append(ty);
        py::list row2;
        row2.append(0.0f);
        row2.append(0.0f);
        row2.append(1.0f);
        matrix_rows_candidate.append(row0);
        matrix_rows_candidate.append(row1);
        matrix_rows_candidate.append(row2);
        py::dict candidate;
        candidate["candidate_index"] = candidate_index;
        candidate["inliers"] = candidate_scores[static_cast<std::size_t>(candidate_index)];
        candidate["rms_px"] = candidate_rms[static_cast<std::size_t>(candidate_index)];
        candidate["matrix"] = matrix_rows_candidate;
        candidate["scale"] = std::sqrt(a * a + b * b);
        candidate["rotation_rad"] = std::atan2(b, a);
        top_candidates.append(candidate);
      }
    }
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_candidate_params);
    cudaFree(d_candidate_scores);
    cudaFree(d_candidate_rms);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_best_inliers);
    cudaFree(d_best_index);
    cudaFree(d_refit_inliers);
    cudaFree(d_refit_status);
    cudaFree(d_refit_matrix);
    cudaFree(d_refit_scale);
    cudaFree(d_refit_rotation_rad);
    cudaFree(d_refit_rms_px);
    cudaFree(d_refit_partial_sums);
    cudaFree(d_refit_partial_count);
    cudaFree(d_refit_partial_residual_sums);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_candidate_params);
  cudaFree(d_candidate_scores);
  cudaFree(d_candidate_rms);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_best_inliers);
  cudaFree(d_best_index);
  cudaFree(d_refit_inliers);
  cudaFree(d_refit_status);
  cudaFree(d_refit_matrix);
  cudaFree(d_refit_scale);
  cudaFree(d_refit_rotation_rad);
  cudaFree(d_refit_rms_px);
  cudaFree(d_refit_partial_sums);
  cudaFree(d_refit_partial_count);
  cudaFree(d_refit_partial_residual_sums);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list matrix_row;
    for (int col = 0; col < 3; ++col) {
      matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(matrix_row);
  }
  py::dict result;
  result["matrix"] = matrix_rows;
  result["scale"] = scale;
  result["rotation_rad"] = rotation_rad;
  result["rms_px"] = rms_px;
  result["inliers"] = best_inliers;
  result["refined_inliers"] = refit_inliers;
  result["refit_status_code"] = refit_status;
  result["refit_status"] = refit_status == 0 ? "ok" : (refit_status == 3 ? "rejected" : "failed");
  result["refit_rms_px"] = refit_rms_px;
  result["best_candidate_index"] = best_index;
  result["candidate_count"] = candidate_count;
  result["reference_count"] = reference_count;
  result["moving_count"] = moving_count;
  result["tolerance_px"] = tolerance_px;
  result["min_pair_distance"] = min_pair_distance;
  result["prior_dx"] = prior_dx;
  result["prior_dy"] = prior_dy;
  result["prior_radius_px"] = prior_radius_px;
  result["min_scale"] = min_scale;
  result["max_scale"] = max_scale;
  result["max_abs_rotation_rad"] = max_abs_rotation_rad;
  result["top_k"] = top_k;
  result["top_candidates"] = top_candidates;
  result["status"] = best_inliers > 0 ? "ok" : "failed";
  result["model"] = "catalog_pair_similarity_cuda";
  return result;
}

py::array_t<float> local_norm_apply_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float scale,
    float offset) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const std::size_t n = static_cast<std::size_t>(info.shape[0]) * static_cast<std::size_t>(info.shape[1]);
  py::array_t<float> output({info.shape[0], info.shape[1]});
  const py::buffer_info output_info = output.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(local_norm input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(local_norm output)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm input)");
    glass_local_norm_apply_f32_launch(d_input, d_output, n, scale, offset);
    check_cuda(cudaGetLastError(), "local_norm_apply_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "local_norm_apply_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm output)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  return output;
}

py::array_t<float> local_norm_apply_grid_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    py::array_t<float, py::array::c_style | py::array::forcecast> scales,
    py::array_t<float, py::array::c_style | py::array::forcecast> offsets,
    int tile_height,
    int tile_width) {
  const py::buffer_info input_info = input.request();
  const py::buffer_info scales_info = scales.request();
  const py::buffer_info offsets_info = offsets.request();
  if (input_info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (scales_info.ndim != 2 || offsets_info.ndim != 2) {
    throw std::invalid_argument("scales and offsets must have shape (grid_rows, grid_cols)");
  }
  if (scales_info.shape[0] != offsets_info.shape[0] || scales_info.shape[1] != offsets_info.shape[1]) {
    throw std::invalid_argument("scales and offsets shapes must match");
  }
  if (tile_height <= 0 || tile_width <= 0) {
    throw std::invalid_argument("tile dimensions must be positive");
  }
  const int height = static_cast<int>(input_info.shape[0]);
  const int width = static_cast<int>(input_info.shape[1]);
  const int grid_rows = static_cast<int>(scales_info.shape[0]);
  const int grid_cols = static_cast<int>(scales_info.shape[1]);
  if (grid_rows <= 0 || grid_cols <= 0) {
    throw std::invalid_argument("coefficient grid must not be empty");
  }
  const int expected_rows = (height + tile_height - 1) / tile_height;
  const int expected_cols = (width + tile_width - 1) / tile_width;
  if (grid_rows != expected_rows || grid_cols != expected_cols) {
    throw std::invalid_argument("coefficient grid shape does not match image shape and tile dimensions");
  }

  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const std::size_t coefficient_count =
      static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
  py::array_t<float> output({input_info.shape[0], input_info.shape[1]});
  const py::buffer_info output_info = output.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_scales = nullptr;
  float* d_offsets = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(local_norm_grid input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(local_norm_grid output)");
    check_cuda(
        cudaMalloc(&d_scales, coefficient_count * sizeof(float)),
        "cudaMalloc(local_norm_grid scales)");
    check_cuda(
        cudaMalloc(&d_offsets, coefficient_count * sizeof(float)),
        "cudaMalloc(local_norm_grid offsets)");
    check_cuda(
        cudaMemcpy(d_input, input_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm_grid input)");
    check_cuda(
        cudaMemcpy(d_scales, scales_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm_grid scales)");
    check_cuda(
        cudaMemcpy(d_offsets, offsets_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm_grid offsets)");
    glass_local_norm_apply_grid_f32_launch(
        d_input,
        d_output,
        d_scales,
        d_offsets,
        width,
        height,
        tile_width,
        tile_height,
        grid_cols,
        grid_rows);
    check_cuda(cudaGetLastError(), "local_norm_apply_grid_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "local_norm_apply_grid_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm_grid output)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_scales);
    cudaFree(d_offsets);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_scales);
  cudaFree(d_offsets);
  return output;
}

py::dict local_norm_pair_stats_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> source,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference) {
  const py::buffer_info source_info = source.request();
  const py::buffer_info reference_info = reference.request();
  if (source_info.ndim != 2 || reference_info.ndim != 2) {
    throw std::invalid_argument("source and reference must have shape (height, width)");
  }
  if (source_info.shape[0] != reference_info.shape[0] || source_info.shape[1] != reference_info.shape[1]) {
    throw std::invalid_argument("source and reference shapes must match");
  }
  const std::size_t n =
      static_cast<std::size_t>(source_info.shape[0]) * static_cast<std::size_t>(source_info.shape[1]);
  if (n == 0) {
    throw std::invalid_argument("cannot compute local normalization stats for an empty tile");
  }

  constexpr int threads = 256;
  const int blocks = std::min<int>(
      4096,
      static_cast<int>((n + static_cast<std::size_t>(threads) - 1) / threads));
  std::vector<double> partial_source_sum(static_cast<std::size_t>(blocks), 0.0);
  std::vector<double> partial_source_sum2(static_cast<std::size_t>(blocks), 0.0);
  std::vector<double> partial_reference_sum(static_cast<std::size_t>(blocks), 0.0);
  std::vector<double> partial_reference_sum2(static_cast<std::size_t>(blocks), 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);

  float* d_source = nullptr;
  float* d_reference = nullptr;
  double* d_partial_source_sum = nullptr;
  double* d_partial_source_sum2 = nullptr;
  double* d_partial_reference_sum = nullptr;
  double* d_partial_reference_sum2 = nullptr;
  unsigned long long* d_partial_count = nullptr;
  try {
    check_cuda(cudaMalloc(&d_source, n * sizeof(float)), "cudaMalloc(local_norm source)");
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(local_norm reference)");
    check_cuda(
        cudaMemcpy(d_source, source_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm source)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm reference)");
    check_cuda(
        cudaMalloc(&d_partial_source_sum, partial_source_sum.size() * sizeof(double)),
        "cudaMalloc(local_norm source sum)");
    check_cuda(
        cudaMalloc(&d_partial_source_sum2, partial_source_sum2.size() * sizeof(double)),
        "cudaMalloc(local_norm source sum2)");
    check_cuda(
        cudaMalloc(&d_partial_reference_sum, partial_reference_sum.size() * sizeof(double)),
        "cudaMalloc(local_norm reference sum)");
    check_cuda(
        cudaMalloc(&d_partial_reference_sum2, partial_reference_sum2.size() * sizeof(double)),
        "cudaMalloc(local_norm reference sum2)");
    check_cuda(
        cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
        "cudaMalloc(local_norm count)");
    glass_pair_sum_stats_f32_launch(
        d_source,
        d_reference,
        d_partial_source_sum,
        d_partial_source_sum2,
        d_partial_reference_sum,
        d_partial_reference_sum2,
        d_partial_count,
        n,
        blocks);
    check_cuda(cudaGetLastError(), "local_norm_pair_stats_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "local_norm_pair_stats_f32 synchronize");
    check_cuda(
        cudaMemcpy(
            partial_source_sum.data(),
            d_partial_source_sum,
            partial_source_sum.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm source sum)");
    check_cuda(
        cudaMemcpy(
            partial_source_sum2.data(),
            d_partial_source_sum2,
            partial_source_sum2.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm source sum2)");
    check_cuda(
        cudaMemcpy(
            partial_reference_sum.data(),
            d_partial_reference_sum,
            partial_reference_sum.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm reference sum)");
    check_cuda(
        cudaMemcpy(
            partial_reference_sum2.data(),
            d_partial_reference_sum2,
            partial_reference_sum2.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm reference sum2)");
    check_cuda(
        cudaMemcpy(
            partial_count.data(),
            d_partial_count,
            partial_count.size() * sizeof(unsigned long long),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm count)");
  } catch (...) {
    cudaFree(d_source);
    cudaFree(d_reference);
    cudaFree(d_partial_source_sum);
    cudaFree(d_partial_source_sum2);
    cudaFree(d_partial_reference_sum);
    cudaFree(d_partial_reference_sum2);
    cudaFree(d_partial_count);
    throw;
  }
  cudaFree(d_source);
  cudaFree(d_reference);
  cudaFree(d_partial_source_sum);
  cudaFree(d_partial_source_sum2);
  cudaFree(d_partial_reference_sum);
  cudaFree(d_partial_reference_sum2);
  cudaFree(d_partial_count);

  double source_sum = 0.0;
  double source_sum2 = 0.0;
  double reference_sum = 0.0;
  double reference_sum2 = 0.0;
  unsigned long long count = 0;
  for (std::size_t i = 0; i < partial_count.size(); ++i) {
    source_sum += partial_source_sum[i];
    source_sum2 += partial_source_sum2[i];
    reference_sum += partial_reference_sum[i];
    reference_sum2 += partial_reference_sum2[i];
    count += partial_count[i];
  }
  py::dict result;
  result["valid_pixels"] = static_cast<unsigned long long>(count);
  result["total_pixels"] = static_cast<unsigned long long>(n);
  result["model"] = "cuda_pair_mean_std";
  if (count == 0) {
    result["source_mean"] = py::none();
    result["reference_mean"] = py::none();
    result["source_std"] = py::none();
    result["reference_std"] = py::none();
    return result;
  }
  const double inv_count = 1.0 / static_cast<double>(count);
  const double source_mean = source_sum * inv_count;
  const double reference_mean = reference_sum * inv_count;
  const double source_var = std::max(0.0, source_sum2 * inv_count - source_mean * source_mean);
  const double reference_var = std::max(0.0, reference_sum2 * inv_count - reference_mean * reference_mean);
  result["source_mean"] = source_mean;
  result["reference_mean"] = reference_mean;
  result["source_std"] = std::sqrt(source_var);
  result["reference_std"] = std::sqrt(reference_var);
  return result;
}

py::tuple integrate_accumulate_mean_tile_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> frame_tile,
    py::array_t<float, py::array::c_style | py::array::forcecast> weight_tile,
    py::array_t<float, py::array::c_style | py::array::forcecast> sum_tile,
    py::array_t<float, py::array::c_style | py::array::forcecast> weight_sum_tile) {
  const py::buffer_info frame_info = frame_tile.request();
  const py::buffer_info weight_info = weight_tile.request();
  const py::buffer_info sum_info = sum_tile.request();
  const py::buffer_info weight_sum_info = weight_sum_tile.request();
  if (frame_info.ndim != 2 || weight_info.ndim != 2 || sum_info.ndim != 2 || weight_sum_info.ndim != 2) {
    throw std::invalid_argument("integration tiles must have shape (height, width)");
  }
  if (frame_info.shape != weight_info.shape || frame_info.shape != sum_info.shape ||
      frame_info.shape != weight_sum_info.shape) {
    throw std::invalid_argument("integration tile shapes must match");
  }
  const std::size_t n = static_cast<std::size_t>(frame_info.shape[0]) *
      static_cast<std::size_t>(frame_info.shape[1]);
  py::array_t<float> out_sum({frame_info.shape[0], frame_info.shape[1]});
  py::array_t<float> out_weight({frame_info.shape[0], frame_info.shape[1]});
  const py::buffer_info out_sum_info = out_sum.request();
  const py::buffer_info out_weight_info = out_weight.request();

  float* d_frame = nullptr;
  float* d_weight = nullptr;
  float* d_sum = nullptr;
  float* d_weight_sum = nullptr;
  try {
    check_cuda(cudaMalloc(&d_frame, n * sizeof(float)), "cudaMalloc(integration frame)");
    check_cuda(cudaMalloc(&d_weight, n * sizeof(float)), "cudaMalloc(integration weight)");
    check_cuda(cudaMalloc(&d_sum, n * sizeof(float)), "cudaMalloc(integration sum)");
    check_cuda(cudaMalloc(&d_weight_sum, n * sizeof(float)), "cudaMalloc(integration weight sum)");
    check_cuda(cudaMemcpy(d_frame, frame_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(frame)");
    check_cuda(cudaMemcpy(d_weight, weight_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(weight)");
    check_cuda(cudaMemcpy(d_sum, sum_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(sum)");
    check_cuda(
        cudaMemcpy(d_weight_sum, weight_sum_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(weight sum)");
    glass_integrate_accumulate_mean_tile_f32_launch(d_frame, d_weight, d_sum, d_weight_sum, n);
    check_cuda(cudaGetLastError(), "integrate_accumulate_mean_tile_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "integrate_accumulate_mean_tile_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_sum_info.ptr, d_sum, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(out sum)");
    check_cuda(
        cudaMemcpy(out_weight_info.ptr, d_weight_sum, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(out weight sum)");
  } catch (...) {
    cudaFree(d_frame);
    cudaFree(d_weight);
    cudaFree(d_sum);
    cudaFree(d_weight_sum);
    throw;
  }
  cudaFree(d_frame);
  cudaFree(d_weight);
  cudaFree(d_sum);
  cudaFree(d_weight_sum);
  return py::make_tuple(out_sum, out_weight);
}

py::array_t<unsigned char> star_local_max_mask_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<unsigned char> mask({info.shape[0], info.shape[1]});
  const py::buffer_info mask_info = mask.request();

  float* d_input = nullptr;
  unsigned char* d_mask = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(star input)");
    check_cuda(cudaMalloc(&d_mask, n * sizeof(unsigned char)), "cudaMalloc(star mask)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(star input)");
    glass_star_local_max_mask_f32_launch(d_input, d_mask, width, height, threshold);
    check_cuda(cudaGetLastError(), "star_local_max_mask_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_local_max_mask_f32 synchronize");
    check_cuda(
        cudaMemcpy(mask_info.ptr, d_mask, n * sizeof(unsigned char), cudaMemcpyDeviceToHost),
        "cudaMemcpy(star mask)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_mask);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_mask);
  return mask;
}

py::dict star_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int max_candidates) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (max_candidates <= 0) {
    throw std::invalid_argument("max_candidates must be positive");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_candidates});
  py::array_t<float> ys({max_candidates});
  py::array_t<float> fluxes({max_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int total_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(star input)");
    check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star xs)");
    check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
        "cudaMalloc(star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(star count)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(star input)");
    glass_star_candidates_f32_launch(
        d_input, d_xs, d_ys, d_fluxes, d_count, width, height, threshold, max_candidates);
    check_cuda(cudaGetLastError(), "star_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(star count)");
    const int stored_count = total_count < max_candidates ? total_count : max_candidates;
    check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star xs)");
    check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star ys)");
    check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    throw;
  }
}

py::dict star_top_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int max_candidates) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (max_candidates <= 0) {
    throw std::invalid_argument("max_candidates must be positive");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_candidates});
  py::array_t<float> ys({max_candidates});
  py::array_t<float> fluxes({max_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_lock = nullptr;
  int total_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(top star input)");
    check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star xs)");
    check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
        "cudaMalloc(top star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(top star count)");
    check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(top star lock)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(top star input)");
    glass_star_top_candidates_f32_launch(
        d_input, d_xs, d_ys, d_fluxes, d_count, d_lock, width, height, threshold, max_candidates);
    check_cuda(cudaGetLastError(), "star_top_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_top_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(top star count)");
    const int stored_count = total_count < max_candidates ? total_count : max_candidates;
    check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star xs)");
    check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star ys)");
    check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    throw;
  }
}

py::dict star_top_nms_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int scan_candidates,
    int max_output_candidates,
    float min_separation_px) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (scan_candidates <= 0 || max_output_candidates <= 0) {
    throw std::invalid_argument("candidate counts must be positive");
  }
  if (scan_candidates < max_output_candidates) {
    throw std::invalid_argument("scan_candidates must be greater than or equal to max_output_candidates");
  }
  if (min_separation_px < 0.0f) {
    throw std::invalid_argument("min_separation_px must be non-negative");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_output_candidates});
  py::array_t<float> ys({max_output_candidates});
  py::array_t<float> fluxes({max_output_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_scan_xs = nullptr;
  float* d_scan_ys = nullptr;
  float* d_scan_fluxes = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_lock = nullptr;
  int* d_stored_count = nullptr;
  int total_count = 0;
  int stored_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(top nms star input)");
    check_cuda(
        cudaMalloc(&d_scan_xs, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
        "cudaMalloc(top nms scan xs)");
    check_cuda(
        cudaMalloc(&d_scan_ys, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
        "cudaMalloc(top nms scan ys)");
    check_cuda(
        cudaMalloc(&d_scan_fluxes, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
        "cudaMalloc(top nms scan fluxes)");
    check_cuda(
        cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(top nms star xs)");
    check_cuda(
        cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(top nms star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(top nms star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(top nms star count)");
    check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(top nms star lock)");
    check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(top nms stored count)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(top nms star input)");
    glass_star_top_nms_candidates_f32_launch(
        d_input,
        d_scan_xs,
        d_scan_ys,
        d_scan_fluxes,
        d_xs,
        d_ys,
        d_fluxes,
        d_count,
        d_lock,
        d_stored_count,
        width,
        height,
        threshold,
        scan_candidates,
        max_output_candidates,
        min_separation_px);
    check_cuda(cudaGetLastError(), "star_top_nms_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_top_nms_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(top nms count)");
    check_cuda(
        cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms stored count)");
    check_cuda(
        cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms star xs)");
    check_cuda(
        cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms star ys)");
    check_cuda(
        cudaMemcpy(
            flux_info.ptr,
            d_fluxes,
            static_cast<std::size_t>(stored_count) * sizeof(float),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["scan_candidates"] = scan_candidates;
    result["max_output_candidates"] = max_output_candidates;
    result["min_separation_px"] = min_separation_px;
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_scan_xs);
    cudaFree(d_scan_ys);
    cudaFree(d_scan_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    cudaFree(d_stored_count);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_scan_xs);
    cudaFree(d_scan_ys);
    cudaFree(d_scan_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    cudaFree(d_stored_count);
    throw;
  }
}

py::dict star_grid_top_nms_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (grid_cols <= 0 || grid_rows <= 0 || candidates_per_cell <= 0 || max_output_candidates <= 0) {
    throw std::invalid_argument("grid dimensions and candidate counts must be positive");
  }
  if (min_separation_px < 0.0f) {
    throw std::invalid_argument("min_separation_px must be non-negative");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const int cell_count = grid_cols * grid_rows;
  const int grid_capacity = cell_count * candidates_per_cell;
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_output_candidates});
  py::array_t<float> ys({max_output_candidates});
  py::array_t<float> fluxes({max_output_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_grid_xs = nullptr;
  float* d_grid_ys = nullptr;
  float* d_grid_fluxes = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_locks = nullptr;
  int* d_cell_counts = nullptr;
  int* d_stored_count = nullptr;
  int total_count = 0;
  int stored_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(grid top nms input)");
    check_cuda(
        cudaMalloc(&d_grid_xs, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
        "cudaMalloc(grid top nms grid xs)");
    check_cuda(
        cudaMalloc(&d_grid_ys, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
        "cudaMalloc(grid top nms grid ys)");
    check_cuda(
        cudaMalloc(&d_grid_fluxes, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
        "cudaMalloc(grid top nms grid fluxes)");
    check_cuda(
        cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(grid top nms star xs)");
    check_cuda(
        cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(grid top nms star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(grid top nms star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(grid top nms star count)");
    check_cuda(cudaMalloc(&d_locks, static_cast<std::size_t>(cell_count) * sizeof(int)), "cudaMalloc(grid top nms locks)");
    check_cuda(
        cudaMalloc(&d_cell_counts, static_cast<std::size_t>(cell_count) * sizeof(int)),
        "cudaMalloc(grid top nms cell counts)");
    check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(grid top nms stored count)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(grid top nms input)");
    glass_star_grid_top_nms_candidates_f32_launch(
        d_input,
        d_grid_xs,
        d_grid_ys,
        d_grid_fluxes,
        d_xs,
        d_ys,
        d_fluxes,
        d_count,
        d_locks,
        d_cell_counts,
        d_stored_count,
        width,
        height,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell,
        max_output_candidates,
        min_separation_px);
    check_cuda(cudaGetLastError(), "star_grid_top_nms_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_grid_top_nms_candidates_f32 synchronize");
    check_cuda(
        cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms count)");
    check_cuda(
        cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms stored count)");
    check_cuda(
        cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms star xs)");
    check_cuda(
        cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms star ys)");
    check_cuda(
        cudaMemcpy(
            flux_info.ptr,
            d_fluxes,
            static_cast<std::size_t>(stored_count) * sizeof(float),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["grid_cols"] = grid_cols;
    result["grid_rows"] = grid_rows;
    result["candidates_per_cell"] = candidates_per_cell;
    result["grid_capacity"] = grid_capacity;
    result["max_output_candidates"] = max_output_candidates;
    result["min_separation_px"] = min_separation_px;
    result["catalog_sort_mode"] = grid_catalog_sort_mode(grid_capacity);
    result["catalog_topk_mode"] = grid_catalog_topk_mode();
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_grid_xs);
    cudaFree(d_grid_ys);
    cudaFree(d_grid_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_locks);
    cudaFree(d_cell_counts);
    cudaFree(d_stored_count);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_grid_xs);
    cudaFree(d_grid_ys);
    cudaFree(d_grid_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_locks);
    cudaFree(d_cell_counts);
    cudaFree(d_stored_count);
    throw;
  }
}

py::dict star_grid_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int grid_cols,
    int grid_rows) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (grid_cols <= 0 || grid_rows <= 0) {
    throw std::invalid_argument("grid dimensions must be positive");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const int cell_count = grid_cols * grid_rows;
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({cell_count});
  py::array_t<float> ys({cell_count});
  py::array_t<float> fluxes({cell_count});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_locks = nullptr;
  int total_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(grid star input)");
    check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(cell_count) * sizeof(float)), "cudaMalloc(grid star xs)");
    check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(cell_count) * sizeof(float)), "cudaMalloc(grid star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(cell_count) * sizeof(float)),
        "cudaMalloc(grid star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(grid star count)");
    check_cuda(cudaMalloc(&d_locks, static_cast<std::size_t>(cell_count) * sizeof(int)), "cudaMalloc(grid star locks)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(grid star input)");
    glass_star_grid_candidates_f32_launch(
        d_input,
        d_xs,
        d_ys,
        d_fluxes,
        d_count,
        d_locks,
        width,
        height,
        threshold,
        grid_cols,
        grid_rows);
    check_cuda(cudaGetLastError(), "star_grid_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_grid_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(grid star count)");
    check_cuda(
        cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(cell_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid star xs)");
    check_cuda(
        cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(cell_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid star ys)");
    check_cuda(
        cudaMemcpy(
            flux_info.ptr,
            d_fluxes,
            static_cast<std::size_t>(cell_count) * sizeof(float),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid star fluxes)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_locks);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_xs);
  cudaFree(d_ys);
  cudaFree(d_fluxes);
  cudaFree(d_count);
  cudaFree(d_locks);

  int stored_count = 0;
  const auto* flux_ptr = static_cast<const float*>(flux_info.ptr);
  while (stored_count < cell_count && flux_ptr[stored_count] > -1.0e30f) {
    ++stored_count;
  }
  py::dict result;
  result["count"] = total_count;
  result["stored_count"] = stored_count;
  result["x"] = xs[py::slice(0, stored_count, 1)];
  result["y"] = ys[py::slice(0, stored_count, 1)];
  result["flux"] = fluxes[py::slice(0, stored_count, 1)];
  result["grid_cols"] = grid_cols;
  result["grid_rows"] = grid_rows;
  return result;
}

PYBIND11_MODULE(_glass_cuda_native, m) {
  m.doc() = "Native CUDA backend for GLASS";
  m.def("cuda_available", &cuda_available);
  m.def("list_devices", &list_devices);
  m.def("get_device_info", &get_device_info);
  m.def("host_pinned_empty_f32", &host_pinned_empty_f32, py::arg("height"), py::arg("width"));
  m.def("smoke_add_f32", &smoke_add_f32);
  m.def("reduce_mean_tile_f32", &reduce_mean_tile_f32);
  m.def("calibrate_tile_f32", &calibrate_tile_f32);
  m.def("mean_stack_tiles_f32", &mean_stack_tiles_f32);
  m.def("warp_translation_f32", &warp_translation_f32);
  m.def("warp_translation_bilinear_f32", &warp_translation_bilinear_f32);
  m.def("warp_matrix_bilinear_f32", &warp_matrix_bilinear_f32);
  m.def(
      "warp_matrix_lanczos3_f32",
      &warp_matrix_lanczos3_f32,
      py::arg("input"),
      py::arg("matrix"),
      py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
      py::arg("clamping_threshold") = -1.0f);
  m.def(
      "matrix_alignment_metrics_f32",
      &matrix_alignment_metrics_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("matrix"),
      py::arg("sample_stride") = 1);
  m.def(
      "refine_matrix_translation_with_metrics_f32",
      &refine_matrix_translation_with_metrics_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("matrix"),
      py::arg("search_radius_px") = 1.0f,
      py::arg("coarse_step_px") = 0.25f,
      py::arg("fine_radius_px") = 0.25f,
      py::arg("fine_step_px") = 0.0625f,
      py::arg("coarse_sample_stride") = 4,
      py::arg("final_sample_stride") = 1);
  m.def(
      "refine_matrix_translation_candidates_with_metrics_f32",
      &refine_matrix_translation_candidates_with_metrics_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("matrices"),
      py::arg("search_radius_px") = 1.0f,
      py::arg("coarse_step_px") = 0.25f,
      py::arg("fine_radius_px") = 0.25f,
      py::arg("fine_step_px") = 0.0625f,
      py::arg("coarse_sample_stride") = 4,
      py::arg("final_sample_stride") = 1);
  m.def(
      "estimate_translation_search_f32",
      &estimate_translation_search_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("max_shift_x"),
      py::arg("max_shift_y"),
      py::arg("sample_stride") = 1);
  m.def(
      "estimate_translation_subpixel_ncc_f32",
      &estimate_translation_subpixel_ncc_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("center_dx"),
      py::arg("center_dy"),
      py::arg("radius_steps"),
      py::arg("step"),
      py::arg("sample_stride") = 1);
  m.def(
      "estimate_translation_from_catalogs_f32",
      &estimate_translation_from_catalogs_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"),
      py::arg("tolerance_px") = 1.0f,
      py::arg("max_abs_dx") = -1.0f,
      py::arg("max_abs_dy") = -1.0f,
      py::arg("prior_dx") = 0.0f,
      py::arg("prior_dy") = 0.0f,
      py::arg("prior_radius_px") = -1.0f);
  m.def(
      "estimate_similarity_from_pairs_f32",
      &estimate_similarity_from_pairs_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"));
  m.def(
      "triangle_asterism_descriptors_f32",
      &triangle_asterism_descriptors_f32,
      py::arg("x"),
      py::arg("y"),
      py::arg("max_stars") = 80,
      py::arg("neighbors") = 5,
      py::arg("max_descriptors") = 1200);
  m.def(
      "estimate_similarity_from_triangle_descriptors_f32",
      &estimate_similarity_from_triangle_descriptors_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"),
      py::arg("reference_descriptors"),
      py::arg("reference_indices"),
      py::arg("moving_descriptors"),
      py::arg("moving_indices"),
      py::arg("tolerance_px") = 2.0f,
      py::arg("descriptor_radius") = 0.1f);
  m.def(
      "estimate_similarity_from_triangle_descriptors_batch_f32",
      &estimate_similarity_from_triangle_descriptors_batch_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("reference_descriptors"),
      py::arg("reference_indices"),
      py::arg("moving_x_list"),
      py::arg("moving_y_list"),
      py::arg("moving_descriptors_list"),
      py::arg("moving_indices_list"),
      py::arg("tolerance_px") = 2.0f,
      py::arg("descriptor_radius") = 0.1f);
  m.def(
      "estimate_similarity_from_catalogs_f32",
      &estimate_similarity_from_catalogs_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"),
      py::arg("tolerance_px") = 2.0f,
      py::arg("min_pair_distance") = 2.0f,
      py::arg("prior_dx") = 0.0f,
      py::arg("prior_dy") = 0.0f,
      py::arg("prior_radius_px") = -1.0f,
      py::arg("min_scale") = 0.0f,
      py::arg("max_scale") = std::numeric_limits<float>::max(),
      py::arg("max_abs_rotation_rad") = -1.0f,
      py::arg("top_k") = 0);
  m.def("local_norm_apply_f32", &local_norm_apply_f32);
  m.def(
      "local_norm_apply_grid_f32",
      &local_norm_apply_grid_f32,
      py::arg("input"),
      py::arg("scales"),
      py::arg("offsets"),
      py::arg("tile_height"),
      py::arg("tile_width"));
  m.def("local_norm_pair_stats_f32", &local_norm_pair_stats_f32);
  m.def("integrate_accumulate_mean_tile_f32", &integrate_accumulate_mean_tile_f32);
  m.def("star_local_max_mask_f32", &star_local_max_mask_f32);
  m.def("star_candidates_f32", &star_candidates_f32);
  m.def("star_top_candidates_f32", &star_top_candidates_f32);
  m.def(
      "star_top_nms_candidates_f32",
      &star_top_nms_candidates_f32,
      py::arg("input"),
      py::arg("threshold"),
      py::arg("scan_candidates"),
      py::arg("max_output_candidates"),
      py::arg("min_separation_px"));
  m.def(
      "star_grid_top_nms_candidates_f32",
      &star_grid_top_nms_candidates_f32,
      py::arg("input"),
      py::arg("threshold"),
      py::arg("grid_cols"),
      py::arg("grid_rows"),
      py::arg("candidates_per_cell"),
      py::arg("max_output_candidates"),
      py::arg("min_separation_px"));
  m.def("star_grid_candidates_f32", &star_grid_candidates_f32);
  py::class_<ResidentCalibratedStack>(m, "ResidentCalibratedStack")
      .def(py::init<std::size_t, std::size_t, std::size_t>())
      .def_property_readonly("frame_count", &ResidentCalibratedStack::frame_count)
      .def_property_readonly("height", &ResidentCalibratedStack::height)
      .def_property_readonly("width", &ResidentCalibratedStack::width)
      .def_property_readonly("pixels_per_frame", &ResidentCalibratedStack::pixels_per_frame)
      .def_property_readonly("loaded_count", &ResidentCalibratedStack::loaded_count)
      .def_property_readonly("host_pinned_bytes", &ResidentCalibratedStack::host_pinned_bytes)
      .def_property_readonly("calibration_lane_count", &ResidentCalibratedStack::calibration_lane_count)
      .def_property_readonly(
          "calibration_lane_buffer_bytes",
          &ResidentCalibratedStack::calibration_lane_buffer_bytes)
      .def_property_readonly("warp_scratch_bytes", &ResidentCalibratedStack::warp_scratch_bytes)
      .def_property_readonly("warp_copy_mode", &ResidentCalibratedStack::warp_copy_mode)
      .def_property_readonly("bytes_allocated", &ResidentCalibratedStack::bytes_allocated)
      .def_property_readonly("warp_coverage_frame_count", &ResidentCalibratedStack::warp_coverage_frame_count)
      .def(
          "set_calibration_masters",
          &ResidentCalibratedStack::set_calibration_masters,
          py::arg("bias") = py::none(),
          py::arg("dark") = py::none(),
          py::arg("flat") = py::none())
      .def("reset_warp_coverage", &ResidentCalibratedStack::reset_warp_coverage)
      .def("accumulate_full_warp_coverage_frame", &ResidentCalibratedStack::accumulate_full_warp_coverage_frame)
      .def("warp_coverage_map", &ResidentCalibratedStack::warp_coverage_map)
      .def("upload_calibrated_frame", &ResidentCalibratedStack::upload_calibrated_frame)
      .def(
          "calibrate_frame",
          &ResidentCalibratedStack::calibrate_frame,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_timed",
          &ResidentCalibratedStack::calibrate_frame_timed,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_pinned_async",
          &ResidentCalibratedStack::calibrate_frame_pinned_async,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_pinned_async_timed",
          &ResidentCalibratedStack::calibrate_frame_pinned_async_timed,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_host_async_timed",
          &ResidentCalibratedStack::calibrate_frame_host_async_timed,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_host_async_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_host_async_multistream_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_multistream_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_host_async_multistream_h2d_release_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_multistream_h2d_release_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("policy") = py::none())
      .def(
          "finish_pending_calibration_timed",
          &ResidentCalibratedStack::finish_pending_calibration_timed)
      .def(
          "calibrate_frames_host_async_multistream_callback_release_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_multistream_callback_release_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("wave_frames"),
          py::arg("release_callback"),
          py::arg("policy") = py::none())
      .def(
          "apply_translation_frame",
          &ResidentCalibratedStack::apply_translation_frame,
          py::arg("index"),
          py::arg("dx"),
          py::arg("dy"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_translation_bilinear_frame",
          &ResidentCalibratedStack::apply_translation_bilinear_frame,
          py::arg("index"),
          py::arg("dx"),
          py::arg("dy"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_matrix_bilinear_frame",
          &ResidentCalibratedStack::apply_matrix_bilinear_frame,
          py::arg("index"),
          py::arg("matrix"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_matrix_lanczos3_frame",
          &ResidentCalibratedStack::apply_matrix_lanczos3_frame,
          py::arg("index"),
          py::arg("matrix"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("clamping_threshold") = -1.0f)
      .def(
          "apply_matrix_bilinear_frames",
          &ResidentCalibratedStack::apply_matrix_bilinear_frames,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_matrix_bilinear_frames_loop",
          &ResidentCalibratedStack::apply_matrix_bilinear_frames_loop,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_matrix_lanczos3_frames",
          &ResidentCalibratedStack::apply_matrix_lanczos3_frames,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("clamping_threshold") = -1.0f)
      .def(
          "apply_matrix_lanczos3_frames_loop",
          &ResidentCalibratedStack::apply_matrix_lanczos3_frames_loop,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("clamping_threshold") = -1.0f)
      .def(
          "matrix_alignment_metrics_to_reference",
          &ResidentCalibratedStack::matrix_alignment_metrics_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("matrix"),
          py::arg("sample_stride") = 1)
      .def(
          "star_core_metrics_candidates_to_reference",
          &ResidentCalibratedStack::star_core_metrics_candidates_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("matrices"),
          py::arg("threshold"))
      .def(
          "refine_matrix_translation_candidates_to_reference",
          &ResidentCalibratedStack::refine_matrix_translation_candidates_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("matrices"),
          py::arg("search_radius_px") = 1.0f,
          py::arg("coarse_step_px") = 0.25f,
          py::arg("fine_radius_px") = 0.25f,
          py::arg("fine_step_px") = 0.0625f,
          py::arg("coarse_sample_stride") = 4,
          py::arg("final_sample_stride") = 1)
      .def(
          "refine_matrix_translation_candidates_batch_to_reference",
          &ResidentCalibratedStack::refine_matrix_translation_candidates_batch_to_reference,
          py::arg("reference_index"),
          py::arg("moving_indices"),
          py::arg("matrices"),
          py::arg("search_radius_px") = 1.0f,
          py::arg("coarse_step_px") = 0.25f,
          py::arg("fine_radius_px") = 0.25f,
          py::arg("fine_step_px") = 0.0625f,
          py::arg("coarse_sample_stride") = 4,
          py::arg("final_sample_stride") = 1)
      .def(
          "estimate_translation_to_reference",
          &ResidentCalibratedStack::estimate_translation_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("max_shift_x"),
          py::arg("max_shift_y"),
          py::arg("sample_stride") = 1)
      .def(
          "estimate_translation_subpixel_to_reference",
          &ResidentCalibratedStack::estimate_translation_subpixel_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("center_dx"),
          py::arg("center_dy"),
          py::arg("radius_steps"),
          py::arg("step"),
          py::arg("sample_stride") = 1)
      .def("frame_global_stats", &ResidentCalibratedStack::frame_global_stats)
      .def(
          "frame_pair_grid_stats",
          &ResidentCalibratedStack::frame_pair_grid_stats,
          py::arg("reference_index"),
          py::arg("source_index"),
          py::arg("tile_height"),
          py::arg("tile_width"))
      .def(
          "apply_global_normalization_frame",
          &ResidentCalibratedStack::apply_global_normalization_frame,
          py::arg("index"),
          py::arg("scale"),
          py::arg("offset"))
      .def(
          "apply_grid_normalization_frame",
          &ResidentCalibratedStack::apply_grid_normalization_frame,
          py::arg("index"),
          py::arg("scales"),
          py::arg("offsets"),
          py::arg("tile_height"),
          py::arg("tile_width"))
      .def("star_local_max_mask", &ResidentCalibratedStack::star_local_max_mask)
      .def("star_candidates", &ResidentCalibratedStack::star_candidates)
      .def("star_top_candidates", &ResidentCalibratedStack::star_top_candidates)
      .def("star_top_nms_candidates", &ResidentCalibratedStack::star_top_nms_candidates)
      .def("star_grid_top_nms_candidates", &ResidentCalibratedStack::star_grid_top_nms_candidates)
      .def(
          "star_grid_top_nms_candidates_deterministic",
          &ResidentCalibratedStack::star_grid_top_nms_candidates_deterministic)
      .def("star_grid_top_nms_candidates_batch", &ResidentCalibratedStack::star_grid_top_nms_candidates_batch)
      .def(
          "star_grid_top_nms_candidates_batch_deterministic",
          &ResidentCalibratedStack::star_grid_top_nms_candidates_batch_deterministic)
      .def(
          "estimate_translation_from_stars_to_reference",
          &ResidentCalibratedStack::estimate_translation_from_stars_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("threshold"),
          py::arg("max_candidates"),
          py::arg("tolerance_px"),
          py::arg("max_abs_dx"),
          py::arg("max_abs_dy"),
          py::arg("prior_dx") = 0.0f,
          py::arg("prior_dy") = 0.0f,
          py::arg("prior_radius_px") = -1.0f,
          py::arg("grid_cols") = 0,
          py::arg("grid_rows") = 0)
      .def("integrate_mean", &ResidentCalibratedStack::integrate_mean, py::arg("weights") = py::none())
      .def(
          "integrate_sigma_clip",
          &ResidentCalibratedStack::integrate_sigma_clip,
          py::arg("weights") = py::none(),
          py::arg("low_sigma") = 3.0f,
          py::arg("high_sigma") = 3.0f,
          py::arg("winsorize") = true)
      .def(
          "integrate_matrix_warped_mean",
          &ResidentCalibratedStack::integrate_matrix_warped_mean,
          py::arg("matrices"),
          py::arg("weights") = py::none(),
          py::arg("interpolation") = "bilinear",
          py::arg("clamping_threshold") = -1.0f);
}
