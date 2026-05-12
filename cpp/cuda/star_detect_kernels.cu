#include "common.cuh"

#include <cuda_runtime.h>

__global__ void star_local_max_mask_kernel(
    const float* input,
    unsigned char* mask,
    int width,
    int height,
    float threshold) {
  const int x = blockIdx.x * blockDim.x + threadIdx.x;
  const int y = blockIdx.y * blockDim.y + threadIdx.y;
  if (x >= width || y >= height) {
    return;
  }
  const int idx = y * width + x;
  if (x == 0 || y == 0 || x == width - 1 || y == height - 1) {
    mask[idx] = 0;
    return;
  }
  const float center = input[idx];
  if (!isfinite(center) || center <= threshold) {
    mask[idx] = 0;
    return;
  }
  for (int dy = -1; dy <= 1; ++dy) {
    for (int dx = -1; dx <= 1; ++dx) {
      if (dx == 0 && dy == 0) {
        continue;
      }
      const float neighbor = input[(y + dy) * width + (x + dx)];
      if (center < neighbor) {
        mask[idx] = 0;
        return;
      }
    }
  }
  mask[idx] = 1;
}

void gpwbpp_star_local_max_mask_f32_launch(
    const float* input,
    unsigned char* mask,
    int width,
    int height,
    float threshold) {
  const dim3 block(16, 16);
  const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
  star_local_max_mask_kernel<<<grid, block>>>(input, mask, width, height, threshold);
}
