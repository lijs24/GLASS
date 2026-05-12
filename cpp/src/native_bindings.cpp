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
    int max_shift_y);
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
    float tolerance_px);
void gpwbpp_local_norm_apply_f32_launch(
    const float* input, float* output, std::size_t n, float scale, float offset);
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

py::dict estimate_translation_search_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    int max_shift_x,
    int max_shift_y) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (max_shift_x < 0 || max_shift_y < 0) {
    throw std::invalid_argument("max_shift values must be non-negative");
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
        max_shift_y);
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
  result["model"] = "translation_integer_ncc";
  return result;
}

py::dict estimate_translation_from_catalogs_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y,
    float tolerance_px) {
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
        tolerance_px);
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
  result["model"] = "catalog_pair_offset_translation";
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
  m.def("estimate_translation_search_f32", &estimate_translation_search_f32);
  m.def("estimate_translation_from_catalogs_f32", &estimate_translation_from_catalogs_f32);
  m.def("local_norm_apply_f32", &local_norm_apply_f32);
  m.def("integrate_accumulate_mean_tile_f32", &integrate_accumulate_mean_tile_f32);
  m.def("star_local_max_mask_f32", &star_local_max_mask_f32);
  m.def("star_candidates_f32", &star_candidates_f32);
  m.def("star_top_candidates_f32", &star_top_candidates_f32);
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
      .def("star_local_max_mask", &ResidentCalibratedStack::star_local_max_mask)
      .def("star_candidates", &ResidentCalibratedStack::star_candidates)
      .def("star_top_candidates", &ResidentCalibratedStack::star_top_candidates)
      .def("integrate_mean", &ResidentCalibratedStack::integrate_mean, py::arg("weights") = py::none())
      .def(
          "integrate_sigma_clip",
          &ResidentCalibratedStack::integrate_sigma_clip,
          py::arg("weights") = py::none(),
          py::arg("low_sigma") = 3.0f,
          py::arg("high_sigma") = 3.0f,
          py::arg("winsorize") = true);
}
