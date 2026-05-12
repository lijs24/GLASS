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

__global__ void star_catalog_init_kernel(float* xs, float* ys, float* fluxes, int max_candidates) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= max_candidates) {
    return;
  }
  xs[i] = 0.0f;
  ys[i] = 0.0f;
  fluxes[i] = -3.402823466e+38F;
}

__global__ void star_grid_catalog_init_kernel(float* xs, float* ys, float* fluxes, int* locks, int cell_count) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= cell_count) {
    return;
  }
  xs[i] = 0.0f;
  ys[i] = 0.0f;
  fluxes[i] = -3.402823466e+38F;
  locks[i] = 0;
}

__global__ void star_candidate_topn_kernel(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int* lock,
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
  atomicAdd(count, 1);

  while (atomicCAS(lock, 0, 1) != 0) {
  }
  int weakest_index = 0;
  float weakest_flux = fluxes[0];
  for (int i = 1; i < max_candidates; ++i) {
    if (fluxes[i] < weakest_flux) {
      weakest_flux = fluxes[i];
      weakest_index = i;
    }
  }
  if (center > weakest_flux) {
    xs[weakest_index] = static_cast<float>(x);
    ys[weakest_index] = static_cast<float>(y);
    fluxes[weakest_index] = center;
  }
  atomicExch(lock, 0);
}

__global__ void star_candidate_grid_kernel(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* locks,
    int* count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows) {
  const int x = blockIdx.x * blockDim.x + threadIdx.x;
  const int y = blockIdx.y * blockDim.y + threadIdx.y;
  if (x >= width || y >= height) {
    return;
  }
  float center = 0.0f;
  if (!is_local_maximum(input, x, y, width, height, threshold, &center)) {
    return;
  }
  atomicAdd(count, 1);
  const int cell_x = min((x * grid_cols) / width, grid_cols - 1);
  const int cell_y = min((y * grid_rows) / height, grid_rows - 1);
  const int cell_index = cell_y * grid_cols + cell_x;

  while (atomicCAS(locks + cell_index, 0, 1) != 0) {
  }
  if (center > fluxes[cell_index]) {
    xs[cell_index] = static_cast<float>(x);
    ys[cell_index] = static_cast<float>(y);
    fluxes[cell_index] = center;
  }
  atomicExch(locks + cell_index, 0);
}

__global__ void star_catalog_sort_desc_kernel(float* xs, float* ys, float* fluxes, int max_candidates) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  for (int i = 0; i < max_candidates; ++i) {
    int best_index = i;
    float best_flux = fluxes[i];
    for (int j = i + 1; j < max_candidates; ++j) {
      if (fluxes[j] > best_flux) {
        best_flux = fluxes[j];
        best_index = j;
      }
    }
    if (best_index == i) {
      continue;
    }
    const float tmp_x = xs[i];
    const float tmp_y = ys[i];
    const float tmp_flux = fluxes[i];
    xs[i] = xs[best_index];
    ys[i] = ys[best_index];
    fluxes[i] = fluxes[best_index];
    xs[best_index] = tmp_x;
    ys[best_index] = tmp_y;
    fluxes[best_index] = tmp_flux;
  }
}

__global__ void star_catalog_nms_kernel(
    const float* scan_xs,
    const float* scan_ys,
    const float* scan_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* stored_count,
    int scan_candidates,
    int max_output_candidates,
    float min_separation_px) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  const float min_separation2 = min_separation_px * min_separation_px;
  int selected = 0;
  for (int i = 0; i < scan_candidates && selected < max_output_candidates; ++i) {
    const float flux = scan_fluxes[i];
    const float x = scan_xs[i];
    const float y = scan_ys[i];
    if (!isfinite(flux) || flux <= -1.0e30f || !isfinite(x) || !isfinite(y)) {
      continue;
    }
    bool keep = true;
    for (int j = 0; j < selected; ++j) {
      const float dx = x - out_xs[j];
      const float dy = y - out_ys[j];
      if (dx * dx + dy * dy < min_separation2) {
        keep = false;
        break;
      }
    }
    if (!keep) {
      continue;
    }
    out_xs[selected] = x;
    out_ys[selected] = y;
    out_fluxes[selected] = flux;
    ++selected;
  }
  *stored_count = selected;
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

void gpwbpp_star_top_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int* lock,
    int width,
    int height,
    float threshold,
    int max_candidates) {
  cudaMemset(count, 0, sizeof(int));
  cudaMemset(lock, 0, sizeof(int));
  constexpr int init_threads = 256;
  const int init_blocks = (max_candidates + init_threads - 1) / init_threads;
  star_catalog_init_kernel<<<init_blocks, init_threads>>>(xs, ys, fluxes, max_candidates);
  const dim3 block(16, 16);
  const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
  star_candidate_topn_kernel<<<grid, block>>>(
      input, xs, ys, fluxes, count, lock, width, height, threshold, max_candidates);
  star_catalog_sort_desc_kernel<<<1, 1>>>(xs, ys, fluxes, max_candidates);
}

void gpwbpp_star_top_nms_candidates_f32_launch(
    const float* input,
    float* scan_xs,
    float* scan_ys,
    float* scan_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* lock,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int scan_candidates,
    int max_output_candidates,
    float min_separation_px) {
  cudaMemset(count, 0, sizeof(int));
  cudaMemset(lock, 0, sizeof(int));
  cudaMemset(stored_count, 0, sizeof(int));
  constexpr int init_threads = 256;
  const int scan_init_blocks = (scan_candidates + init_threads - 1) / init_threads;
  star_catalog_init_kernel<<<scan_init_blocks, init_threads>>>(scan_xs, scan_ys, scan_fluxes, scan_candidates);
  const int out_init_blocks = (max_output_candidates + init_threads - 1) / init_threads;
  star_catalog_init_kernel<<<out_init_blocks, init_threads>>>(out_xs, out_ys, out_fluxes, max_output_candidates);
  const dim3 block(16, 16);
  const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
  star_candidate_topn_kernel<<<grid, block>>>(
      input, scan_xs, scan_ys, scan_fluxes, count, lock, width, height, threshold, scan_candidates);
  star_catalog_sort_desc_kernel<<<1, 1>>>(scan_xs, scan_ys, scan_fluxes, scan_candidates);
  star_catalog_nms_kernel<<<1, 1>>>(
      scan_xs,
      scan_ys,
      scan_fluxes,
      out_xs,
      out_ys,
      out_fluxes,
      stored_count,
      scan_candidates,
      max_output_candidates,
      min_separation_px);
}

void gpwbpp_star_grid_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int* locks,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows) {
  cudaMemset(count, 0, sizeof(int));
  const int cell_count = grid_cols * grid_rows;
  constexpr int init_threads = 256;
  const int init_blocks = (cell_count + init_threads - 1) / init_threads;
  star_grid_catalog_init_kernel<<<init_blocks, init_threads>>>(xs, ys, fluxes, locks, cell_count);
  const dim3 block(16, 16);
  const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
  star_candidate_grid_kernel<<<grid, block>>>(
      input, xs, ys, fluxes, locks, count, width, height, threshold, grid_cols, grid_rows);
  star_catalog_sort_desc_kernel<<<1, 1>>>(xs, ys, fluxes, cell_count);
}
