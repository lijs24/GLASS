#include "common.cuh"

#include <cstddef>
#include <math.h>

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

__global__ void gpwbpp_warp_translation_bilinear_f32_kernel(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    float dx,
    float dy,
    float fill) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  const int n = width * height;
  if (i >= n) {
    return;
  }
  const int x = i % width;
  const int y = i / width;
  const float sx = static_cast<float>(x) - dx;
  const float sy = static_cast<float>(y) - dy;
  if (sx < 0.0f || sx > static_cast<float>(width - 1) ||
      sy < 0.0f || sy > static_cast<float>(height - 1)) {
    output[i] = fill;
    coverage[i] = 0.0f;
    return;
  }

  const int x0 = static_cast<int>(floorf(sx));
  const int y0 = static_cast<int>(floorf(sy));
  const int x1 = x0 + 1 < width ? x0 + 1 : x0;
  const int y1 = y0 + 1 < height ? y0 + 1 : y0;
  const float tx = sx - static_cast<float>(x0);
  const float ty = sy - static_cast<float>(y0);

  const float v00 = input[y0 * width + x0];
  const float v10 = input[y0 * width + x1];
  const float v01 = input[y1 * width + x0];
  const float v11 = input[y1 * width + x1];
  const float top = v00 * (1.0f - tx) + v10 * tx;
  const float bottom = v01 * (1.0f - tx) + v11 * tx;
  output[i] = top * (1.0f - ty) + bottom * ty;
  coverage[i] = 1.0f;
}

void gpwbpp_warp_translation_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    float dx,
    float dy,
    float fill) {
  constexpr int threads = 256;
  const int blocks = (width * height + threads - 1) / threads;
  gpwbpp_warp_translation_bilinear_f32_kernel<<<blocks, threads>>>(
      input, output, coverage, width, height, dx, dy, fill);
}
