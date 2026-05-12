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

namespace py = pybind11;

void gpwbpp_smoke_add_f32_launch(const float* a, const float* b, float* out, std::size_t n);
void gpwbpp_calibrate_tile_f32_launch(
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
void gpwbpp_mean_stack_tiles_f32_launch(
    const float* stack, float* out, std::size_t frame_count, std::size_t pixels_per_frame);
void gpwbpp_warp_translation_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    int dx,
    int dy,
    float fill);
void gpwbpp_warp_translation_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    float dx,
    float dy,
    float fill);
void gpwbpp_warp_matrix_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill);
void gpwbpp_estimate_translation_search_f32_launch(
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
void gpwbpp_estimate_translation_subpixel_ncc_f32_launch(
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
void gpwbpp_estimate_translation_from_catalogs_f32_launch(
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
void gpwbpp_estimate_similarity_from_pairs_f32_launch(
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
void gpwbpp_estimate_similarity_from_catalogs_f32_launch(
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
void gpwbpp_local_norm_apply_f32_launch(
    const float* input, float* output, std::size_t n, float scale, float offset);
void gpwbpp_frame_sum_stats_f32_launch(
    const float* input,
    double* partial_sum,
    double* partial_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks);
void gpwbpp_pair_sum_stats_f32_launch(
    const float* source,
    const float* reference,
    double* partial_source_sum,
    double* partial_source_sum2,
    double* partial_reference_sum,
    double* partial_reference_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks);
void gpwbpp_integrate_accumulate_mean_tile_f32_launch(
    const float* frame, const float* weight, float* sum, float* weight_sum, std::size_t n);
void gpwbpp_integrate_resident_weighted_mean_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame);
void gpwbpp_integrate_resident_sigma_clip_f32_launch(
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
void gpwbpp_star_local_max_mask_f32_launch(
    const float* input,
    unsigned char* mask,
    int width,
    int height,
    float threshold);
void gpwbpp_star_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int width,
    int height,
    float threshold,
    int max_candidates);
void gpwbpp_star_top_candidates_f32_launch(
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
void gpwbpp_star_top_nms_candidates_f32_launch(
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
void gpwbpp_star_grid_candidates_f32_launch(
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
  info["available_to_gpwbpp"] = true;
  return info;
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
  }

  ResidentCalibratedStack(const ResidentCalibratedStack&) = delete;
  ResidentCalibratedStack& operator=(const ResidentCalibratedStack&) = delete;

  ~ResidentCalibratedStack() {
    cudaFree(d_stack_);
    cudaFree(d_light_);
    cudaFree(d_bias_);
    cudaFree(d_dark_);
    cudaFree(d_flat_);
  }

  std::size_t frame_count() const { return frame_count_; }
  std::size_t height() const { return height_; }
  std::size_t width() const { return width_; }
  std::size_t pixels_per_frame() const { return pixels_per_frame_; }
  std::size_t loaded_count() const { return loaded_count_; }

  std::size_t bytes_allocated() const {
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    std::size_t total = frame_count_ * frame_bytes + frame_bytes;
    if (has_bias_) {
      total += frame_bytes;
    }
    if (has_dark_) {
      total += frame_bytes;
    }
    if (has_flat_) {
      total += frame_bytes;
    }
    return total;
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
    if (has_dark_ && dark_scaling_enabled && !dark_exposure_obj.is_none()) {
      const float dark_exposure_s = py::cast<float>(dark_exposure_obj);
      if (dark_exposure_s != 0.0f) {
        dark_scale = light_exposure_s / dark_exposure_s;
      }
    }

    check_cuda(
        cudaMemcpy(d_light_, light_info.ptr, pixels_per_frame_ * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident raw light)");
    gpwbpp_calibrate_tile_f32_launch(
        d_light_,
        d_bias_,
        d_dark_,
        d_flat_,
        d_stack_ + index * pixels_per_frame_,
        pixels_per_frame_,
        has_bias_,
        has_dark_,
        has_flat_,
        master_dark_includes_bias,
        dark_scale,
        flat_floor,
        pedestal);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frame kernel launch");
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.calibrate_frame synchronize");
    mark_loaded(index);
  }

  void apply_translation_frame(std::size_t index, int dx, int dy, float fill) {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before translation warp");
    }
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    float* d_output = nullptr;
    float* d_coverage = nullptr;
    try {
      check_cuda(cudaMalloc(&d_output, frame_bytes), "cudaMalloc(resident translation output)");
      check_cuda(cudaMalloc(&d_coverage, frame_bytes), "cudaMalloc(resident translation coverage)");
      gpwbpp_warp_translation_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_output,
          d_coverage,
          static_cast<int>(width_),
          static_cast<int>(height_),
          dx,
          dy,
          fill);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_translation_frame kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_translation_frame synchronize");
      check_cuda(
          cudaMemcpy(d_stack_ + index * pixels_per_frame_, d_output, frame_bytes, cudaMemcpyDeviceToDevice),
          "cudaMemcpy(resident translated frame)");
    } catch (...) {
      cudaFree(d_output);
      cudaFree(d_coverage);
      throw;
    }
    cudaFree(d_output);
    cudaFree(d_coverage);
  }

  void apply_translation_bilinear_frame(std::size_t index, float dx, float dy, float fill) {
    require_loaded(index, "bilinear translation warp");
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    float* d_output = nullptr;
    float* d_coverage = nullptr;
    try {
      check_cuda(cudaMalloc(&d_output, frame_bytes), "cudaMalloc(resident bilinear translation output)");
      check_cuda(cudaMalloc(&d_coverage, frame_bytes), "cudaMalloc(resident bilinear translation coverage)");
      gpwbpp_warp_translation_bilinear_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_output,
          d_coverage,
          static_cast<int>(width_),
          static_cast<int>(height_),
          dx,
          dy,
          fill);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_translation_bilinear_frame kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_translation_bilinear_frame synchronize");
      check_cuda(
          cudaMemcpy(d_stack_ + index * pixels_per_frame_, d_output, frame_bytes, cudaMemcpyDeviceToDevice),
          "cudaMemcpy(resident bilinear translated frame)");
    } catch (...) {
      cudaFree(d_output);
      cudaFree(d_coverage);
      throw;
    }
    cudaFree(d_output);
    cudaFree(d_coverage);
  }

  void apply_matrix_bilinear_frame(std::size_t index, py::object matrix_obj, float fill) {
    require_loaded(index, "matrix bilinear warp");
    const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    float* d_output = nullptr;
    float* d_coverage = nullptr;
    float* d_inverse = nullptr;
    try {
      check_cuda(cudaMalloc(&d_output, frame_bytes), "cudaMalloc(resident matrix warp output)");
      check_cuda(cudaMalloc(&d_coverage, frame_bytes), "cudaMalloc(resident matrix warp coverage)");
      check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(resident matrix warp inverse)");
      check_cuda(
          cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident matrix warp inverse)");
      gpwbpp_warp_matrix_bilinear_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_output,
          d_coverage,
          d_inverse,
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frame kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_bilinear_frame synchronize");
      check_cuda(
          cudaMemcpy(d_stack_ + index * pixels_per_frame_, d_output, frame_bytes, cudaMemcpyDeviceToDevice),
          "cudaMemcpy(resident matrix warped frame)");
    } catch (...) {
      cudaFree(d_output);
      cudaFree(d_coverage);
      cudaFree(d_inverse);
      throw;
    }
    cudaFree(d_output);
    cudaFree(d_coverage);
    cudaFree(d_inverse);
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
      gpwbpp_estimate_translation_search_f32_launch(
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
      gpwbpp_estimate_translation_subpixel_ncc_f32_launch(
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
      gpwbpp_frame_sum_stats_f32_launch(
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

  void apply_global_normalization_frame(std::size_t index, float scale, float offset) {
    require_loaded(index, "global local normalization");
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    float* d_output = nullptr;
    try {
      check_cuda(cudaMalloc(&d_output, frame_bytes), "cudaMalloc(resident global normalization output)");
      gpwbpp_local_norm_apply_f32_launch(d_stack_ + index * pixels_per_frame_, d_output, pixels_per_frame_, scale, offset);
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
      gpwbpp_star_local_max_mask_f32_launch(
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
      gpwbpp_star_candidates_f32_launch(
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
      gpwbpp_star_top_candidates_f32_launch(
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
        gpwbpp_star_grid_candidates_f32_launch(
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
        gpwbpp_star_grid_candidates_f32_launch(
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
        gpwbpp_star_top_candidates_f32_launch(
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
        gpwbpp_star_top_candidates_f32_launch(
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
      gpwbpp_estimate_translation_from_catalogs_f32_launch(
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
      gpwbpp_integrate_resident_weighted_mean_f32_launch(
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
      gpwbpp_integrate_resident_sigma_clip_f32_launch(
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

  std::size_t frame_count_;
  std::size_t height_;
  std::size_t width_;
  std::size_t pixels_per_frame_;
  std::size_t loaded_count_ = 0;
  std::vector<unsigned char> loaded_;
  float* d_stack_ = nullptr;
  float* d_light_ = nullptr;
  float* d_bias_ = nullptr;
  float* d_dark_ = nullptr;
  float* d_flat_ = nullptr;
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
    gpwbpp_smoke_add_f32_launch(d_a, d_b, d_out, n);
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
    gpwbpp_calibrate_tile_f32_launch(
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
    gpwbpp_mean_stack_tiles_f32_launch(d_stack, d_out, frame_count, pixels_per_frame);
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
    gpwbpp_warp_translation_f32_launch(
        d_input,
        d_output,
        d_coverage,
        width,
        height,
        static_cast<int>(std::lround(dx)),
        static_cast<int>(std::lround(dy)),
        fill);
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
    gpwbpp_warp_translation_bilinear_f32_launch(
        d_input,
        d_output,
        d_coverage,
        width,
        height,
        dx,
        dy,
        fill);
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
    gpwbpp_warp_matrix_bilinear_f32_launch(
        d_input,
        d_output,
        d_coverage,
        d_inverse,
        width,
        height,
        fill);
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
    gpwbpp_estimate_translation_search_f32_launch(
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
    gpwbpp_estimate_translation_subpixel_ncc_f32_launch(
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
    gpwbpp_estimate_translation_from_catalogs_f32_launch(
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
    gpwbpp_estimate_similarity_from_pairs_f32_launch(
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
    float max_abs_rotation_rad) {
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
  std::array<float, 9> host_matrix{};
  float scale = 1.0f;
  float rotation_rad = 0.0f;
  float rms_px = std::numeric_limits<float>::quiet_NaN();
  int best_inliers = 0;
  int best_index = -1;
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
    gpwbpp_estimate_similarity_from_catalogs_f32_launch(
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
  result["tolerance_px"] = tolerance_px;
  result["min_pair_distance"] = min_pair_distance;
  result["prior_dx"] = prior_dx;
  result["prior_dy"] = prior_dy;
  result["prior_radius_px"] = prior_radius_px;
  result["min_scale"] = min_scale;
  result["max_scale"] = max_scale;
  result["max_abs_rotation_rad"] = max_abs_rotation_rad;
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
    gpwbpp_local_norm_apply_f32_launch(d_input, d_output, n, scale, offset);
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
    gpwbpp_pair_sum_stats_f32_launch(
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
    gpwbpp_integrate_accumulate_mean_tile_f32_launch(d_frame, d_weight, d_sum, d_weight_sum, n);
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
    gpwbpp_star_local_max_mask_f32_launch(d_input, d_mask, width, height, threshold);
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
    gpwbpp_star_candidates_f32_launch(
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
    gpwbpp_star_top_candidates_f32_launch(
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
    gpwbpp_star_top_nms_candidates_f32_launch(
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
    gpwbpp_star_grid_candidates_f32_launch(
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

PYBIND11_MODULE(_gpwbpp_cuda_native, m) {
  m.doc() = "Native CUDA backend for GPWBPP";
  m.def("cuda_available", &cuda_available);
  m.def("list_devices", &list_devices);
  m.def("get_device_info", &get_device_info);
  m.def("smoke_add_f32", &smoke_add_f32);
  m.def("reduce_mean_tile_f32", &reduce_mean_tile_f32);
  m.def("calibrate_tile_f32", &calibrate_tile_f32);
  m.def("mean_stack_tiles_f32", &mean_stack_tiles_f32);
  m.def("warp_translation_f32", &warp_translation_f32);
  m.def("warp_translation_bilinear_f32", &warp_translation_bilinear_f32);
  m.def("warp_matrix_bilinear_f32", &warp_matrix_bilinear_f32);
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
      py::arg("max_abs_rotation_rad") = -1.0f);
  m.def("local_norm_apply_f32", &local_norm_apply_f32);
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
  m.def("star_grid_candidates_f32", &star_grid_candidates_f32);
  py::class_<ResidentCalibratedStack>(m, "ResidentCalibratedStack")
      .def(py::init<std::size_t, std::size_t, std::size_t>())
      .def_property_readonly("frame_count", &ResidentCalibratedStack::frame_count)
      .def_property_readonly("height", &ResidentCalibratedStack::height)
      .def_property_readonly("width", &ResidentCalibratedStack::width)
      .def_property_readonly("pixels_per_frame", &ResidentCalibratedStack::pixels_per_frame)
      .def_property_readonly("loaded_count", &ResidentCalibratedStack::loaded_count)
      .def_property_readonly("bytes_allocated", &ResidentCalibratedStack::bytes_allocated)
      .def(
          "set_calibration_masters",
          &ResidentCalibratedStack::set_calibration_masters,
          py::arg("bias") = py::none(),
          py::arg("dark") = py::none(),
          py::arg("flat") = py::none())
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
          "apply_global_normalization_frame",
          &ResidentCalibratedStack::apply_global_normalization_frame,
          py::arg("index"),
          py::arg("scale"),
          py::arg("offset"))
      .def("star_local_max_mask", &ResidentCalibratedStack::star_local_max_mask)
      .def("star_candidates", &ResidentCalibratedStack::star_candidates)
      .def("star_top_candidates", &ResidentCalibratedStack::star_top_candidates)
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
          py::arg("winsorize") = true);
}
