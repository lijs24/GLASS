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

__device__ bool star_candidate_better(float flux, float x, float y, float current_flux, float current_x, float current_y) {
  if (flux > current_flux) {
    return true;
  }
  if (flux < current_flux) {
    return false;
  }
  if (y < current_y) {
    return true;
  }
  if (y > current_y) {
    return false;
  }
  return x < current_x;
}

__device__ bool star_candidate_weaker(float flux, float x, float y, float current_flux, float current_x, float current_y) {
  if (flux < current_flux) {
    return true;
  }
  if (flux > current_flux) {
    return false;
  }
  if (y > current_y) {
    return true;
  }
  if (y < current_y) {
    return false;
  }
  return x > current_x;
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
    if (star_candidate_weaker(fluxes[i], xs[i], ys[i], weakest_flux, xs[weakest_index], ys[weakest_index])) {
      weakest_flux = fluxes[i];
      weakest_index = i;
    }
  }
  if (star_candidate_better(center, static_cast<float>(x), static_cast<float>(y), weakest_flux, xs[weakest_index], ys[weakest_index])) {
    xs[weakest_index] = static_cast<float>(x);
    ys[weakest_index] = static_cast<float>(y);
    fluxes[weakest_index] = center;
  }
  __threadfence();
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
  if (star_candidate_better(
          center,
          static_cast<float>(x),
          static_cast<float>(y),
          fluxes[cell_index],
          xs[cell_index],
          ys[cell_index])) {
    xs[cell_index] = static_cast<float>(x);
    ys[cell_index] = static_cast<float>(y);
    fluxes[cell_index] = center;
  }
  __threadfence();
  atomicExch(locks + cell_index, 0);
}

__global__ void star_candidate_grid_topk_kernel(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* locks,
    int* cell_counts,
    int* count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell) {
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
  const int base = cell_index * candidates_per_cell;

  const int filled_slots = atomicAdd(cell_counts + cell_index, 0);
  if (filled_slots >= candidates_per_cell) {
    // Equal-flux candidates still take the lock so the existing y/x tie-breaker
    // remains authoritative.
    bool strictly_weaker_than_cell = true;
    for (int i = 0; i < candidates_per_cell; ++i) {
      if (center >= fluxes[base + i]) {
        strictly_weaker_than_cell = false;
        break;
      }
    }
    if (strictly_weaker_than_cell) {
      return;
    }
  }

  while (atomicCAS(locks + cell_index, 0, 1) != 0) {
  }
  int weakest_index = base;
  float weakest_flux = fluxes[base];
  for (int i = 1; i < candidates_per_cell; ++i) {
    const int candidate_index = base + i;
    if (star_candidate_weaker(
            fluxes[candidate_index],
            xs[candidate_index],
            ys[candidate_index],
            weakest_flux,
            xs[weakest_index],
            ys[weakest_index])) {
      weakest_flux = fluxes[candidate_index];
      weakest_index = candidate_index;
    }
  }
  if (star_candidate_better(
          center,
          static_cast<float>(x),
          static_cast<float>(y),
          weakest_flux,
          xs[weakest_index],
            ys[weakest_index])) {
    const bool replacing_empty = weakest_flux <= -1.0e30f;
    xs[weakest_index] = static_cast<float>(x);
    ys[weakest_index] = static_cast<float>(y);
    fluxes[weakest_index] = center;
    if (replacing_empty) {
      atomicAdd(cell_counts + cell_index, 1);
    }
  }
  __threadfence();
  atomicExch(locks + cell_index, 0);
}

__global__ void star_candidate_grid_topk_deterministic_cell_kernel(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell) {
  const int cell_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  const int cell_count = grid_cols * grid_rows;
  if (cell_index >= cell_count) {
    return;
  }
  const int cell_x = cell_index % grid_cols;
  const int cell_y = cell_index / grid_cols;
  const int x0 = (cell_x * width) / grid_cols;
  const int x1 = ((cell_x + 1) * width) / grid_cols;
  const int y0 = (cell_y * height) / grid_rows;
  const int y1 = ((cell_y + 1) * height) / grid_rows;
  const int base = cell_index * candidates_per_cell;
  for (int y = y0; y < y1; ++y) {
    for (int x = x0; x < x1; ++x) {
      float center = 0.0f;
      if (!is_local_maximum(input, x, y, width, height, threshold, &center)) {
        continue;
      }
      atomicAdd(count, 1);
      int weakest_index = base;
      float weakest_flux = fluxes[base];
      for (int i = 1; i < candidates_per_cell; ++i) {
        const int candidate_index = base + i;
        if (star_candidate_weaker(
                fluxes[candidate_index],
                xs[candidate_index],
                ys[candidate_index],
                weakest_flux,
                xs[weakest_index],
                ys[weakest_index])) {
          weakest_flux = fluxes[candidate_index];
          weakest_index = candidate_index;
        }
      }
      if (star_candidate_better(
              center,
              static_cast<float>(x),
              static_cast<float>(y),
              weakest_flux,
              xs[weakest_index],
              ys[weakest_index])) {
        xs[weakest_index] = static_cast<float>(x);
        ys[weakest_index] = static_cast<float>(y);
        fluxes[weakest_index] = center;
      }
    }
  }
}

__global__ void star_candidate_grid_topk_deterministic_block_kernel(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell) {
  const int cell_index = static_cast<int>(blockIdx.x);
  const int cell_count = grid_cols * grid_rows;
  if (cell_index >= cell_count) {
    return;
  }

  extern __shared__ float shared_catalog[];
  const int local_capacity = static_cast<int>(blockDim.x) * candidates_per_cell;
  float* local_xs = shared_catalog;
  float* local_ys = local_xs + local_capacity;
  float* local_fluxes = local_ys + local_capacity;

  const int lane_base = static_cast<int>(threadIdx.x) * candidates_per_cell;
  for (int i = 0; i < candidates_per_cell; ++i) {
    const int local_index = lane_base + i;
    local_xs[local_index] = 0.0f;
    local_ys[local_index] = 0.0f;
    local_fluxes[local_index] = -1.0e30f;
  }
  __syncthreads();

  const int cell_x = cell_index % grid_cols;
  const int cell_y = cell_index / grid_cols;
  const int x0 = (cell_x * width) / grid_cols;
  const int x1 = ((cell_x + 1) * width) / grid_cols;
  const int y0 = (cell_y * height) / grid_rows;
  const int y1 = ((cell_y + 1) * height) / grid_rows;
  const int cell_width = x1 - x0;
  const int cell_pixels = cell_width * (y1 - y0);
  for (int offset = static_cast<int>(threadIdx.x); offset < cell_pixels; offset += static_cast<int>(blockDim.x)) {
    const int y = y0 + offset / cell_width;
    const int x = x0 + offset - (offset / cell_width) * cell_width;
    float center = 0.0f;
    if (!is_local_maximum(input, x, y, width, height, threshold, &center)) {
      continue;
    }
    atomicAdd(count, 1);
    int weakest_index = lane_base;
    float weakest_flux = local_fluxes[lane_base];
    for (int i = 1; i < candidates_per_cell; ++i) {
      const int candidate_index = lane_base + i;
      if (star_candidate_weaker(
              local_fluxes[candidate_index],
              local_xs[candidate_index],
              local_ys[candidate_index],
              weakest_flux,
              local_xs[weakest_index],
              local_ys[weakest_index])) {
        weakest_flux = local_fluxes[candidate_index];
        weakest_index = candidate_index;
      }
    }
    if (star_candidate_better(
            center,
            static_cast<float>(x),
            static_cast<float>(y),
            weakest_flux,
            local_xs[weakest_index],
            local_ys[weakest_index])) {
      local_xs[weakest_index] = static_cast<float>(x);
      local_ys[weakest_index] = static_cast<float>(y);
      local_fluxes[weakest_index] = center;
    }
  }
  __syncthreads();

  if (threadIdx.x != 0) {
    return;
  }
  const int output_base = cell_index * candidates_per_cell;
  for (int i = 0; i < candidates_per_cell; ++i) {
    const int output_index = output_base + i;
    xs[output_index] = 0.0f;
    ys[output_index] = 0.0f;
    fluxes[output_index] = -1.0e30f;
  }
  for (int local_index = 0; local_index < local_capacity; ++local_index) {
    const float candidate_flux = local_fluxes[local_index];
    if (!isfinite(candidate_flux) || candidate_flux <= -1.0e30f) {
      continue;
    }
    int weakest_index = output_base;
    float weakest_flux = fluxes[output_base];
    for (int i = 1; i < candidates_per_cell; ++i) {
      const int candidate_index = output_base + i;
      if (star_candidate_weaker(
              fluxes[candidate_index],
              xs[candidate_index],
              ys[candidate_index],
              weakest_flux,
              xs[weakest_index],
              ys[weakest_index])) {
        weakest_flux = fluxes[candidate_index];
        weakest_index = candidate_index;
      }
    }
    if (star_candidate_better(
            candidate_flux,
            local_xs[local_index],
            local_ys[local_index],
            weakest_flux,
            xs[weakest_index],
            ys[weakest_index])) {
      xs[weakest_index] = local_xs[local_index];
      ys[weakest_index] = local_ys[local_index];
      fluxes[weakest_index] = candidate_flux;
    }
  }
}

__global__ void star_catalog_sort_desc_kernel(float* xs, float* ys, float* fluxes, int max_candidates) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  for (int i = 0; i < max_candidates; ++i) {
    int best_index = i;
    float best_flux = fluxes[i];
    for (int j = i + 1; j < max_candidates; ++j) {
      if (star_candidate_better(fluxes[j], xs[j], ys[j], best_flux, xs[best_index], ys[best_index])) {
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

__global__ void star_catalog_sort_desc_shared_kernel(
    float* xs,
    float* ys,
    float* fluxes,
    int candidate_count,
    int sort_count) {
  extern __shared__ float shared_catalog[];
  float* shared_xs = shared_catalog;
  float* shared_ys = shared_xs + sort_count;
  float* shared_fluxes = shared_ys + sort_count;

  for (int i = threadIdx.x; i < sort_count; i += blockDim.x) {
    if (i < candidate_count) {
      shared_xs[i] = xs[i];
      shared_ys[i] = ys[i];
      shared_fluxes[i] = fluxes[i];
    } else {
      shared_xs[i] = 0.0f;
      shared_ys[i] = 0.0f;
      shared_fluxes[i] = -3.402823466e+38F;
    }
  }
  __syncthreads();

  for (int k = 2; k <= sort_count; k <<= 1) {
    for (int j = k >> 1; j > 0; j >>= 1) {
      for (int i = threadIdx.x; i < sort_count; i += blockDim.x) {
        const int peer = i ^ j;
        if (peer <= i || peer >= sort_count) {
          continue;
        }
        const bool ascending = (i & k) != 0;
        const bool should_swap =
            ascending
                ? star_candidate_better(
                      shared_fluxes[i],
                      shared_xs[i],
                      shared_ys[i],
                      shared_fluxes[peer],
                      shared_xs[peer],
                      shared_ys[peer])
                : star_candidate_better(
                      shared_fluxes[peer],
                      shared_xs[peer],
                      shared_ys[peer],
                      shared_fluxes[i],
                      shared_xs[i],
                      shared_ys[i]);
        if (should_swap) {
          const float tmp_x = shared_xs[i];
          const float tmp_y = shared_ys[i];
          const float tmp_flux = shared_fluxes[i];
          shared_xs[i] = shared_xs[peer];
          shared_ys[i] = shared_ys[peer];
          shared_fluxes[i] = shared_fluxes[peer];
          shared_xs[peer] = tmp_x;
          shared_ys[peer] = tmp_y;
          shared_fluxes[peer] = tmp_flux;
        }
      }
      __syncthreads();
    }
  }

  for (int i = threadIdx.x; i < candidate_count; i += blockDim.x) {
    xs[i] = shared_xs[i];
    ys[i] = shared_ys[i];
    fluxes[i] = shared_fluxes[i];
  }
}

int next_power_of_two_int(int value) {
  int result = 1;
  while (result < value) {
    result <<= 1;
  }
  return result;
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

__global__ void star_refine_centroids_kernel(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    unsigned char* statuses,
    int count,
    int width,
    int height,
    int radius) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= count) {
    return;
  }
  if (statuses != nullptr) {
    statuses[i] = 0;
  }
  const float candidate_flux = fluxes[i];
  if (!isfinite(candidate_flux) || candidate_flux <= -1.0e30f) {
    return;
  }
  const int center_x = static_cast<int>(floorf(xs[i] + 0.5f));
  const int center_y = static_cast<int>(floorf(ys[i] + 0.5f));
  if (center_x < 0 || center_x >= width || center_y < 0 || center_y >= height) {
    return;
  }
  constexpr int kMaxCentroidRadius = 8;
  constexpr int kMaxCentroidSamples = (2 * kMaxCentroidRadius + 1) * (2 * kMaxCentroidRadius + 1);
  const int window_radius = min(max(radius, 1), kMaxCentroidRadius);
  const int x0 = max(0, center_x - window_radius);
  const int x1 = min(width - 1, center_x + window_radius);
  const int y0 = max(0, center_y - window_radius);
  const int y1 = min(height - 1, center_y + window_radius);

  float samples[kMaxCentroidSamples];
  int sample_count = 0;
  for (int y = y0; y <= y1; ++y) {
    for (int x = x0; x <= x1; ++x) {
      const float value = input[y * width + x];
      if (isfinite(value) && sample_count < kMaxCentroidSamples) {
        samples[sample_count] = value;
        ++sample_count;
      }
    }
  }
  if (sample_count <= 0) {
    return;
  }
  for (int j = 1; j < sample_count; ++j) {
    const float value = samples[j];
    int k = j - 1;
    while (k >= 0 && samples[k] > value) {
      samples[k + 1] = samples[k];
      --k;
    }
    samples[k + 1] = value;
  }
  const float background = (sample_count & 1)
      ? samples[sample_count / 2]
      : 0.5f * (samples[sample_count / 2 - 1] + samples[sample_count / 2]);

  double sum_weight = 0.0;
  double sum_x = 0.0;
  double sum_y = 0.0;
  for (int y = y0; y <= y1; ++y) {
    for (int x = x0; x <= x1; ++x) {
      const float value = input[y * width + x];
      if (!isfinite(value)) {
        continue;
      }
      const float weight_f = fmaxf(value - background, 0.0f);
      if (weight_f <= 0.0f) {
        continue;
      }
      const double weight = static_cast<double>(weight_f);
      sum_weight += weight;
      sum_x += static_cast<double>(x) * weight;
      sum_y += static_cast<double>(y) * weight;
    }
  }
  if (sum_weight <= 0.0) {
    return;
  }
  xs[i] = static_cast<float>(sum_x / sum_weight);
  ys[i] = static_cast<float>(sum_y / sum_weight);
  if (statuses != nullptr) {
    statuses[i] = 1;
  }
}

void glass_star_local_max_mask_f32_launch(
    const float* input,
    unsigned char* mask,
    int width,
    int height,
    float threshold) {
  const dim3 block(16, 16);
  const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
  star_local_max_mask_kernel<<<grid, block>>>(input, mask, width, height, threshold);
}

void glass_star_candidates_f32_launch(
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

void glass_star_top_candidates_f32_launch(
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

void glass_star_top_nms_candidates_f32_launch(
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

void glass_star_grid_top_nms_candidates_f32_launch(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* locks,
    int* cell_counts,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px) {
  cudaMemset(count, 0, sizeof(int));
  cudaMemset(stored_count, 0, sizeof(int));
  const int cell_count = grid_cols * grid_rows;
  const int grid_capacity = cell_count * candidates_per_cell;
  constexpr int init_threads = 256;
  const int grid_init_blocks = (grid_capacity + init_threads - 1) / init_threads;
  star_catalog_init_kernel<<<grid_init_blocks, init_threads>>>(grid_xs, grid_ys, grid_fluxes, grid_capacity);
  const int out_init_blocks = (max_output_candidates + init_threads - 1) / init_threads;
  star_catalog_init_kernel<<<out_init_blocks, init_threads>>>(out_xs, out_ys, out_fluxes, max_output_candidates);
  cudaMemset(locks, 0, static_cast<std::size_t>(cell_count) * sizeof(int));
  cudaMemset(cell_counts, 0, static_cast<std::size_t>(cell_count) * sizeof(int));
  const dim3 block(16, 16);
  const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
  star_candidate_grid_topk_kernel<<<grid, block>>>(
      input,
      grid_xs,
      grid_ys,
      grid_fluxes,
      locks,
      cell_counts,
      count,
      width,
      height,
      threshold,
      grid_cols,
      grid_rows,
      candidates_per_cell);
  const int sort_count = next_power_of_two_int(grid_capacity);
  if (sort_count <= 4096) {
    constexpr int sort_threads = 256;
    const std::size_t shared_bytes = static_cast<std::size_t>(sort_count) * 3 * sizeof(float);
    star_catalog_sort_desc_shared_kernel<<<1, sort_threads, shared_bytes>>>(
        grid_xs, grid_ys, grid_fluxes, grid_capacity, sort_count);
  } else {
    star_catalog_sort_desc_kernel<<<1, 1>>>(grid_xs, grid_ys, grid_fluxes, grid_capacity);
  }
  star_catalog_nms_kernel<<<1, 1>>>(
      grid_xs,
      grid_ys,
      grid_fluxes,
      out_xs,
      out_ys,
      out_fluxes,
      stored_count,
      grid_capacity,
      max_output_candidates,
      min_separation_px);
}

void glass_star_grid_top_nms_candidates_deterministic_f32_launch(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px) {
  cudaMemset(count, 0, sizeof(int));
  cudaMemset(stored_count, 0, sizeof(int));
  const int cell_count = grid_cols * grid_rows;
  const int grid_capacity = cell_count * candidates_per_cell;
  constexpr int init_threads = 256;
  const int grid_init_blocks = (grid_capacity + init_threads - 1) / init_threads;
  star_catalog_init_kernel<<<grid_init_blocks, init_threads>>>(grid_xs, grid_ys, grid_fluxes, grid_capacity);
  const int out_init_blocks = (max_output_candidates + init_threads - 1) / init_threads;
  star_catalog_init_kernel<<<out_init_blocks, init_threads>>>(out_xs, out_ys, out_fluxes, max_output_candidates);
  if (candidates_per_cell <= 16) {
    constexpr int cell_threads = 128;
    const std::size_t shared_bytes =
        static_cast<std::size_t>(cell_threads) * static_cast<std::size_t>(candidates_per_cell) * 3 * sizeof(float);
    star_candidate_grid_topk_deterministic_block_kernel<<<cell_count, cell_threads, shared_bytes>>>(
        input,
        grid_xs,
        grid_ys,
        grid_fluxes,
        count,
        width,
        height,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell);
  } else {
    const int cell_blocks = (cell_count + init_threads - 1) / init_threads;
    star_candidate_grid_topk_deterministic_cell_kernel<<<cell_blocks, init_threads>>>(
        input,
        grid_xs,
        grid_ys,
        grid_fluxes,
        count,
        width,
        height,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell);
  }
  const int sort_count = next_power_of_two_int(grid_capacity);
  if (sort_count <= 4096) {
    constexpr int sort_threads = 256;
    const std::size_t shared_bytes = static_cast<std::size_t>(sort_count) * 3 * sizeof(float);
    star_catalog_sort_desc_shared_kernel<<<1, sort_threads, shared_bytes>>>(
        grid_xs, grid_ys, grid_fluxes, grid_capacity, sort_count);
  } else {
    star_catalog_sort_desc_kernel<<<1, 1>>>(grid_xs, grid_ys, grid_fluxes, grid_capacity);
  }
  star_catalog_nms_kernel<<<1, 1>>>(
      grid_xs,
      grid_ys,
      grid_fluxes,
      out_xs,
      out_ys,
      out_fluxes,
      stored_count,
      grid_capacity,
      max_output_candidates,
      min_separation_px);
}

void glass_star_refine_centroids_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    unsigned char* statuses,
    int count,
    int width,
    int height,
    int radius) {
  if (count <= 0 || radius <= 0) {
    return;
  }
  if (statuses != nullptr) {
    cudaMemset(statuses, 0, static_cast<std::size_t>(count) * sizeof(unsigned char));
  }
  constexpr int threads = 128;
  const int blocks = (count + threads - 1) / threads;
  star_refine_centroids_kernel<<<blocks, threads>>>(input, xs, ys, fluxes, statuses, count, width, height, radius);
}

void glass_star_grid_candidates_f32_launch(
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
