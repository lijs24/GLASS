#include <cuda_runtime.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <cmath>

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
void gpwbpp_local_norm_apply_f32_launch(
    const float* input, float* output, std::size_t n, float scale, float offset);

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
  m.def("local_norm_apply_f32", &local_norm_apply_f32);
}
