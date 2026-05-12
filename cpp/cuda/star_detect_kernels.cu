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

__device__ bool is_local_maximum(
    const float* input,
    int x,
    int y,
    int width,
    int height,
    float threshold,
    float* center_out) {
  if (x == 0 || y == 0 || x == width - 1 || y == height - 1) {
    return false;
  }
  const int idx = y * width + x;
  const float center = input[idx];
  if (!isfinite(center) || center <= threshold) {
    return false;
  }
  for (int dy = -1; dy <= 1; ++dy) {
    for (int dx = -1; dx <= 1; ++dx) {
      if (dx == 0 && dy == 0) {
        continue;
      }
      if (center < input[(y + dy) * width + (x + dx)]) {
        return false;
      }
    }
  }
  *center_out = center;
  return true;
}

__global__ void star_candidate_compact_kernel(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int width,
    int height,
    float threshold,
    int max_candidates) {
  const int x = blockIdx.x * blockDim.x + threadIdx.x;
  const int y = blockIdx.y * blockDim.y + threadIdx.y;
  if (x >= width || y >= height) {
    return;
  }
  float center = 0.0f;
  if (!is_local_maximum(input, x, y, width, height, threshold, &center)) {
    return;
  }
  const int out_index = atomicAdd(count, 1);
  if (out_index >= max_candidates) {
    return;
  }
  xs[out_index] = static_cast<float>(x);
  ys[out_index] = static_cast<float>(y);
  fluxes[out_index] = center;
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

void gpwbpp_star_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int width,
    int height,
    float threshold,
    int max_candidates) {
  cudaMemset(count, 0, sizeof(int));
  const dim3 block(16, 16);
  const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
  star_candidate_compact_kernel<<<grid, block>>>(
      input, xs, ys, fluxes, count, width, height, threshold, max_candidates);
}
