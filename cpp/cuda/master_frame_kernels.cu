#include "common.cuh"

#include <cstddef>

__global__ void gpwbpp_mean_stack_tiles_f32_kernel(
    const float* stack, float* out, std::size_t frame_count, std::size_t pixels_per_frame) {
  const std::size_t i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i >= pixels_per_frame) {
    return;
  }

  double sum = 0.0;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    sum += static_cast<double>(stack[frame * pixels_per_frame + i]);
  }
  out[i] = static_cast<float>(sum / static_cast<double>(frame_count));
}

void gpwbpp_mean_stack_tiles_f32_launch(
    const float* stack, float* out, std::size_t frame_count, std::size_t pixels_per_frame) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  gpwbpp_mean_stack_tiles_f32_kernel<<<blocks, threads>>>(stack, out, frame_count, pixels_per_frame);
}
