#include "common.cuh"

#include <cstddef>

__global__ void gpwbpp_warp_translation_f32_kernel(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    int dx,
    int dy,
    float fill) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  const int n = width * height;
  if (i >= n) {
    return;
  }
  const int x = i % width;
  const int y = i / width;
  const int sx = x - dx;
  const int sy = y - dy;
  if (sx >= 0 && sx < width && sy >= 0 && sy < height) {
    output[i] = input[sy * width + sx];
    coverage[i] = 1.0f;
  } else {
    output[i] = fill;
    coverage[i] = 0.0f;
  }
}

void gpwbpp_warp_translation_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    int dx,
    int dy,
    float fill) {
  constexpr int threads = 256;
  const int blocks = (width * height + threads - 1) / threads;
  gpwbpp_warp_translation_f32_kernel<<<blocks, threads>>>(
      input, output, coverage, width, height, dx, dy, fill);
}
