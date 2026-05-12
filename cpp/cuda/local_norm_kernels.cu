#include "common.cuh"

#include <cstddef>

__global__ void gpwbpp_local_norm_apply_f32_kernel(
    const float* input,
    float* output,
    std::size_t n,
    float scale,
    float offset) {
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }
  output[i] = input[i] * scale + offset;
}

void gpwbpp_local_norm_apply_f32_launch(
    const float* input,
    float* output,
    std::size_t n,
    float scale,
    float offset) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  gpwbpp_local_norm_apply_f32_kernel<<<blocks, threads>>>(input, output, n, scale, offset);
}
