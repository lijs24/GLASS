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
