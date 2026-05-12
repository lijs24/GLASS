#include "common.cuh"

#include <cstddef>

__global__ void gpwbpp_integrate_accumulate_mean_tile_f32_kernel(
    const float* frame,
    const float* weight,
    float* sum,
    float* weight_sum,
    std::size_t n) {
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }
  const float w = weight[i];
  sum[i] += frame[i] * w;
  weight_sum[i] += w;
}

void gpwbpp_integrate_accumulate_mean_tile_f32_launch(
    const float* frame,
    const float* weight,
    float* sum,
    float* weight_sum,
    std::size_t n) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  gpwbpp_integrate_accumulate_mean_tile_f32_kernel<<<blocks, threads>>>(frame, weight, sum, weight_sum, n);
}

__global__ void gpwbpp_integrate_resident_weighted_mean_f32_kernel(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame) {
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (pixel >= pixels_per_frame) {
    return;
  }

  float sum = 0.0f;
  float weight_sum = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    sum += stack[frame * pixels_per_frame + pixel] * weight;
    weight_sum += weight;
  }
  weight_map[pixel] = weight_sum;
  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
}

void gpwbpp_integrate_resident_weighted_mean_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  gpwbpp_integrate_resident_weighted_mean_f32_kernel<<<blocks, threads>>>(
      stack,
      weights,
      master,
      weight_map,
      frame_count,
      pixels_per_frame);
}
