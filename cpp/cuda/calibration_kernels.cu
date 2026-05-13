#include "common.cuh"

#include <cstddef>

__global__ void glass_calibrate_tile_f32_kernel(
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
    float pedestal) {
  const std::size_t i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i >= n) {
    return;
  }

  float value = light[i];
  if (has_dark) {
    value -= dark[i] * dark_scale;
    if (!master_dark_includes_bias && has_bias) {
      value -= bias[i];
    }
  } else if (has_bias) {
    value -= bias[i];
  }

  if (has_flat) {
    float denom = flat[i];
    if (denom < flat_floor) {
      denom = flat_floor;
    }
    value /= denom;
  }

  out[i] = value + pedestal;
}

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
    float pedestal) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_calibrate_tile_f32_kernel<<<blocks, threads>>>(
      light,
      bias,
      dark,
      flat,
      out,
      n,
      has_bias,
      has_dark,
      has_flat,
      master_dark_includes_bias,
      dark_scale,
      flat_floor,
      pedestal);
}

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
    cudaStream_t stream) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_calibrate_tile_f32_kernel<<<blocks, threads, 0, stream>>>(
      light,
      bias,
      dark,
      flat,
      out,
      n,
      has_bias,
      has_dark,
      has_flat,
      master_dark_includes_bias,
      dark_scale,
      flat_floor,
      pedestal);
}
