#include "common.cuh"

#include <cstddef>
#include <cstdint>
#include <cmath>

__device__ bool glass_fused_sample_matrix_bilinear_f32(
    const float* input,
    const float* inverse,
    int width,
    int height,
    std::size_t pixel,
    float* value_out) {
  const int x = static_cast<int>(pixel % static_cast<std::size_t>(width));
  const int y = static_cast<int>(pixel / static_cast<std::size_t>(width));
  const float fx = static_cast<float>(x);
  const float fy = static_cast<float>(y);
  const float denom = inverse[6] * fx + inverse[7] * fy + inverse[8];
  if (fabsf(denom) <= 1.0e-12f) {
    return false;
  }
  const float sx = (inverse[0] * fx + inverse[1] * fy + inverse[2]) / denom;
  const float sy = (inverse[3] * fx + inverse[4] * fy + inverse[5]) / denom;
  if (sx < 0.0f || sx > static_cast<float>(width - 1) ||
      sy < 0.0f || sy > static_cast<float>(height - 1)) {
    return false;
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
  *value_out = top * (1.0f - ty) + bottom * ty;
  return true;
}

__device__ float glass_fused_sinc_f32(float x) {
  const float ax = fabsf(x);
  if (ax < 1.0e-6f) {
    return 1.0f;
  }
  const float pix = 3.14159265358979323846f * x;
  return sinf(pix) / pix;
}

__device__ float glass_fused_lanczos3_weight_f32(float x) {
  const float ax = fabsf(x);
  if (ax >= 3.0f) {
    return 0.0f;
  }
  return glass_fused_sinc_f32(x) * glass_fused_sinc_f32(x / 3.0f);
}

__device__ bool glass_fused_sample_matrix_lanczos3_f32(
    const float* input,
    const float* inverse,
    int width,
    int height,
    std::size_t pixel,
    float clamping_threshold,
    float* value_out) {
  const int x = static_cast<int>(pixel % static_cast<std::size_t>(width));
  const int y = static_cast<int>(pixel / static_cast<std::size_t>(width));
  const float fx = static_cast<float>(x);
  const float fy = static_cast<float>(y);
  const float denom = inverse[6] * fx + inverse[7] * fy + inverse[8];
  if (fabsf(denom) <= 1.0e-12f) {
    return false;
  }

  const float sx = (inverse[0] * fx + inverse[1] * fy + inverse[2]) / denom;
  const float sy = (inverse[3] * fx + inverse[4] * fy + inverse[5]) / denom;
  if (sx < 2.0f || sx >= static_cast<float>(width - 3) ||
      sy < 2.0f || sy >= static_cast<float>(height - 3)) {
    return false;
  }

  const int x0 = static_cast<int>(floorf(sx));
  const int y0 = static_cast<int>(floorf(sy));
  float wx[6];
  float wy[6];
  for (int k = 0; k < 6; ++k) {
    wx[k] = glass_fused_lanczos3_weight_f32(sx - static_cast<float>(x0 - 2 + k));
    wy[k] = glass_fused_lanczos3_weight_f32(sy - static_cast<float>(y0 - 2 + k));
  }

  float weighted_sum = 0.0f;
  float weight_sum = 0.0f;
  const bool clamp_enabled = clamping_threshold >= 0.0f;
  float local_min = 3.402823466e+38f;
  float local_max = -3.402823466e+38f;
  for (int ky = 0; ky < 6; ++ky) {
    const int yy = y0 - 2 + ky;
    for (int kx = 0; kx < 6; ++kx) {
      const int xx = x0 - 2 + kx;
      const float w = wx[kx] * wy[ky];
      const float value = input[yy * width + xx];
      if (!isfinite(value)) {
        continue;
      }
      weighted_sum += value * w;
      weight_sum += w;
      if (clamp_enabled) {
        local_min = fminf(local_min, value);
        local_max = fmaxf(local_max, value);
      }
    }
  }

  if (fabsf(weight_sum) <= 1.0e-12f) {
    return false;
  }
  float value = weighted_sum / weight_sum;
  if (clamp_enabled && local_max >= local_min) {
    const float range = local_max - local_min;
    const float lo = local_min - clamping_threshold * range;
    const float hi = local_max + clamping_threshold * range;
    value = fminf(hi, fmaxf(lo, value));
  }
  *value_out = value;
  return true;
}

__global__ void glass_integrate_accumulate_mean_tile_f32_kernel(
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

void glass_integrate_accumulate_mean_tile_f32_launch(
    const float* frame,
    const float* weight,
    float* sum,
    float* weight_sum,
    std::size_t n) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_integrate_accumulate_mean_tile_f32_kernel<<<blocks, threads>>>(frame, weight, sum, weight_sum, n);
}

__global__ void glass_apply_invalid_mask_f32_kernel(
    float* frame,
    const unsigned char* invalid_mask,
    std::size_t n) {
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }
  if (invalid_mask[i] != 0) {
    frame[i] = nanf("");
  }
}

void glass_apply_invalid_mask_f32_launch(
    float* frame,
    const unsigned char* invalid_mask,
    std::size_t n) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_apply_invalid_mask_f32_kernel<<<blocks, threads>>>(frame, invalid_mask, n);
}

__global__ void glass_apply_cosmetic_threshold_mask_f32_kernel(
    float* frame,
    std::size_t n,
    float low_threshold,
    float high_threshold,
    unsigned long long* counts) {
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }

  const float value = frame[i];
  if (!isfinite(value)) {
    atomicAdd(&counts[2], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (value > high_threshold) {
    atomicAdd(&counts[0], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (value < low_threshold) {
    atomicAdd(&counts[1], 1ULL);
    frame[i] = nanf("");
  }
}

__global__ void glass_count_cosmetic_threshold_mask_f32_kernel(
    const float* frame,
    std::size_t n,
    float low_threshold,
    float high_threshold,
    unsigned long long* counts) {
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }

  const float value = frame[i];
  if (!isfinite(value)) {
    atomicAdd(&counts[2], 1ULL);
    return;
  }
  if (value > high_threshold) {
    atomicAdd(&counts[0], 1ULL);
    return;
  }
  if (value < low_threshold) {
    atomicAdd(&counts[1], 1ULL);
  }
}

void glass_apply_cosmetic_threshold_mask_f32_launch(
    float* frame,
    std::size_t n,
    float low_threshold,
    float high_threshold,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_apply_cosmetic_threshold_mask_f32_kernel<<<blocks, threads>>>(
      frame,
      n,
      low_threshold,
      high_threshold,
      counts);
}

void glass_count_cosmetic_threshold_mask_f32_launch(
    const float* frame,
    std::size_t n,
    float low_threshold,
    float high_threshold,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_count_cosmetic_threshold_mask_f32_kernel<<<blocks, threads>>>(
      frame,
      n,
      low_threshold,
      high_threshold,
      counts);
}

__global__ void glass_apply_cosmetic_threshold_mask_frames_f32_kernel(
    float* stack,
    std::size_t n,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    std::size_t frame_count,
    unsigned long long* counts) {
  const std::size_t frame_pos = static_cast<std::size_t>(blockIdx.y);
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (frame_pos >= frame_count || i >= n) {
    return;
  }

  const std::size_t frame_index = static_cast<std::size_t>(frame_indices[frame_pos]);
  float* frame = stack + frame_index * n;
  unsigned long long* frame_counts = counts + frame_pos * 3;
  const float value = frame[i];
  if (!isfinite(value)) {
    atomicAdd(&frame_counts[2], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (value > high_thresholds[frame_pos]) {
    atomicAdd(&frame_counts[0], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (value < low_thresholds[frame_pos]) {
    atomicAdd(&frame_counts[1], 1ULL);
    frame[i] = nanf("");
  }
}

__global__ void glass_count_cosmetic_threshold_mask_frames_f32_kernel(
    const float* stack,
    std::size_t n,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    std::size_t frame_count,
    unsigned long long* counts) {
  const std::size_t frame_pos = static_cast<std::size_t>(blockIdx.y);
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (frame_pos >= frame_count || i >= n) {
    return;
  }

  const std::size_t frame_index = static_cast<std::size_t>(frame_indices[frame_pos]);
  const float* frame = stack + frame_index * n;
  unsigned long long* frame_counts = counts + frame_pos * 3;
  const float value = frame[i];
  if (!isfinite(value)) {
    atomicAdd(&frame_counts[2], 1ULL);
    return;
  }
  if (value > high_thresholds[frame_pos]) {
    atomicAdd(&frame_counts[0], 1ULL);
    return;
  }
  if (value < low_thresholds[frame_pos]) {
    atomicAdd(&frame_counts[1], 1ULL);
  }
}

void glass_apply_cosmetic_threshold_mask_frames_f32_launch(
    float* stack,
    std::size_t n,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    std::size_t frame_count,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  const dim3 grid(blocks, static_cast<unsigned int>(frame_count));
  glass_apply_cosmetic_threshold_mask_frames_f32_kernel<<<grid, threads>>>(
      stack,
      n,
      frame_indices,
      low_thresholds,
      high_thresholds,
      frame_count,
      counts);
}

void glass_count_cosmetic_threshold_mask_frames_f32_launch(
    const float* stack,
    std::size_t n,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    std::size_t frame_count,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  const dim3 grid(blocks, static_cast<unsigned int>(frame_count));
  glass_count_cosmetic_threshold_mask_frames_f32_kernel<<<grid, threads>>>(
      stack,
      n,
      frame_indices,
      low_thresholds,
      high_thresholds,
      frame_count,
      counts);
}

__device__ float glass_median_finite_small(float* values, int count) {
  if (count <= 0) {
    return 0.0f;
  }
  for (int i = 1; i < count; ++i) {
    const float key = values[i];
    int j = i - 1;
    while (j >= 0 && values[j] > key) {
      values[j + 1] = values[j];
      --j;
    }
    values[j + 1] = key;
  }
  if ((count & 1) != 0) {
    return values[count / 2];
  }
  return 0.5f * (values[count / 2 - 1] + values[count / 2]);
}

__device__ void glass_isolated_cosmetic_classify_f32(
    const float* frame,
    std::size_t width,
    std::size_t height,
    std::size_t i,
    float low_threshold,
    float high_threshold,
    float median,
    float structure_sigma,
    float sigma,
    int min_neighbor_support,
    bool* is_hot,
    bool* is_cold,
    bool* is_nonfinite,
    bool* is_hot_candidate,
    bool* is_cold_candidate,
    bool* is_hot_protected,
    bool* is_cold_protected) {
  *is_hot = false;
  *is_cold = false;
  *is_nonfinite = false;
  *is_hot_candidate = false;
  *is_cold_candidate = false;
  *is_hot_protected = false;
  *is_cold_protected = false;

  const float value = frame[i];
  if (!isfinite(value)) {
    *is_nonfinite = true;
    return;
  }

  const std::size_t y = i / width;
  const std::size_t x = i - y * width;
  float neighbors[8];
  int neighbor_count = 0;
  int hot_support = 0;
  int cold_support = 0;
  const float support_sigma = fmaxf(0.0f, structure_sigma);
  const float support_high = median + support_sigma * sigma;
  const float support_low = median - support_sigma * sigma;
  for (int dy = -1; dy <= 1; ++dy) {
    for (int dx = -1; dx <= 1; ++dx) {
      if (dx == 0 && dy == 0) {
        continue;
      }
      int yy = static_cast<int>(y) + dy;
      int xx = static_cast<int>(x) + dx;
      yy = max(0, min(static_cast<int>(height) - 1, yy));
      xx = max(0, min(static_cast<int>(width) - 1, xx));
      const float neighbor = frame[static_cast<std::size_t>(yy) * width + static_cast<std::size_t>(xx)];
      if (isfinite(neighbor)) {
        neighbors[neighbor_count++] = neighbor;
        if (neighbor > support_high) {
          ++hot_support;
        }
        if (neighbor < support_low) {
          ++cold_support;
        }
      }
    }
  }
  const float local_median = neighbor_count > 0
      ? glass_median_finite_small(neighbors, neighbor_count)
      : median;
  const float hot_delta = fmaxf(0.0f, high_threshold - median);
  const float cold_delta = fmaxf(0.0f, median - low_threshold);
  const bool hot_candidate = value > high_threshold && (value - local_median) > hot_delta;
  const bool cold_candidate = value < low_threshold && (local_median - value) > cold_delta;
  *is_hot_candidate = hot_candidate;
  *is_cold_candidate = cold_candidate;
  const int support_required = max(0, min_neighbor_support);
  if (hot_candidate && hot_support < support_required) {
    *is_hot = true;
  } else if (hot_candidate) {
    *is_hot_protected = true;
  }
  if (cold_candidate && cold_support < support_required) {
    *is_cold = true;
  } else if (cold_candidate) {
    *is_cold_protected = true;
  }
}

__global__ void glass_apply_isolated_cosmetic_threshold_mask_f32_kernel(
    float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  const std::size_t n = width * height;
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }
  bool hot;
  bool cold;
  bool nonfinite;
  bool hot_candidate;
  bool cold_candidate;
  bool hot_protected;
  bool cold_protected;
  glass_isolated_cosmetic_classify_f32(
      frame,
      width,
      height,
      i,
      low_threshold,
      high_threshold,
      median,
      structure_sigma,
      sigma,
      min_neighbor_support,
      &hot,
      &cold,
      &nonfinite,
      &hot_candidate,
      &cold_candidate,
      &hot_protected,
      &cold_protected);
  if (hot_candidate) {
    atomicAdd(&counts[3], 1ULL);
  }
  if (cold_candidate) {
    atomicAdd(&counts[4], 1ULL);
  }
  if (hot_protected) {
    atomicAdd(&counts[5], 1ULL);
  }
  if (cold_protected) {
    atomicAdd(&counts[6], 1ULL);
  }
  if (nonfinite) {
    atomicAdd(&counts[2], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (hot) {
    atomicAdd(&counts[0], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (cold) {
    atomicAdd(&counts[1], 1ULL);
    frame[i] = nanf("");
  }
}

__global__ void glass_count_isolated_cosmetic_threshold_mask_f32_kernel(
    const float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  const std::size_t n = width * height;
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }
  bool hot;
  bool cold;
  bool nonfinite;
  bool hot_candidate;
  bool cold_candidate;
  bool hot_protected;
  bool cold_protected;
  glass_isolated_cosmetic_classify_f32(
      frame,
      width,
      height,
      i,
      low_threshold,
      high_threshold,
      median,
      structure_sigma,
      sigma,
      min_neighbor_support,
      &hot,
      &cold,
      &nonfinite,
      &hot_candidate,
      &cold_candidate,
      &hot_protected,
      &cold_protected);
  if (hot_candidate) {
    atomicAdd(&counts[3], 1ULL);
  }
  if (cold_candidate) {
    atomicAdd(&counts[4], 1ULL);
  }
  if (hot_protected) {
    atomicAdd(&counts[5], 1ULL);
  }
  if (cold_protected) {
    atomicAdd(&counts[6], 1ULL);
  }
  if (nonfinite) {
    atomicAdd(&counts[2], 1ULL);
    return;
  }
  if (hot) {
    atomicAdd(&counts[0], 1ULL);
    return;
  }
  if (cold) {
    atomicAdd(&counts[1], 1ULL);
  }
}

void glass_apply_isolated_cosmetic_threshold_mask_f32_launch(
    float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const std::size_t n = width * height;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_apply_isolated_cosmetic_threshold_mask_f32_kernel<<<blocks, threads>>>(
      frame,
      width,
      height,
      low_threshold,
      high_threshold,
      median,
      sigma,
      structure_sigma,
      min_neighbor_support,
      counts);
}

void glass_count_isolated_cosmetic_threshold_mask_f32_launch(
    const float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const std::size_t n = width * height;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_count_isolated_cosmetic_threshold_mask_f32_kernel<<<blocks, threads>>>(
      frame,
      width,
      height,
      low_threshold,
      high_threshold,
      median,
      sigma,
      structure_sigma,
      min_neighbor_support,
      counts);
}

__global__ void glass_apply_isolated_cosmetic_threshold_mask_frames_f32_kernel(
    float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  const std::size_t frame_pos = static_cast<std::size_t>(blockIdx.y);
  const std::size_t n = width * height;
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (frame_pos >= frame_count || i >= n) {
    return;
  }
  const std::size_t frame_index = static_cast<std::size_t>(frame_indices[frame_pos]);
  float* frame = stack + frame_index * n;
  unsigned long long* frame_counts = counts + frame_pos * 7ULL;
  bool hot;
  bool cold;
  bool nonfinite;
  bool hot_candidate;
  bool cold_candidate;
  bool hot_protected;
  bool cold_protected;
  glass_isolated_cosmetic_classify_f32(
      frame,
      width,
      height,
      i,
      low_thresholds[frame_pos],
      high_thresholds[frame_pos],
      medians[frame_pos],
      structure_sigma,
      sigmas[frame_pos],
      min_neighbor_support,
      &hot,
      &cold,
      &nonfinite,
      &hot_candidate,
      &cold_candidate,
      &hot_protected,
      &cold_protected);
  if (hot_candidate) {
    atomicAdd(&frame_counts[3], 1ULL);
  }
  if (cold_candidate) {
    atomicAdd(&frame_counts[4], 1ULL);
  }
  if (hot_protected) {
    atomicAdd(&frame_counts[5], 1ULL);
  }
  if (cold_protected) {
    atomicAdd(&frame_counts[6], 1ULL);
  }
  if (nonfinite) {
    atomicAdd(&frame_counts[2], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (hot) {
    atomicAdd(&frame_counts[0], 1ULL);
    frame[i] = nanf("");
    return;
  }
  if (cold) {
    atomicAdd(&frame_counts[1], 1ULL);
    frame[i] = nanf("");
  }
}

__global__ void glass_count_isolated_cosmetic_threshold_mask_frames_f32_kernel(
    const float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  const std::size_t frame_pos = static_cast<std::size_t>(blockIdx.y);
  const std::size_t n = width * height;
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (frame_pos >= frame_count || i >= n) {
    return;
  }
  const std::size_t frame_index = static_cast<std::size_t>(frame_indices[frame_pos]);
  const float* frame = stack + frame_index * n;
  unsigned long long* frame_counts = counts + frame_pos * 7ULL;
  bool hot;
  bool cold;
  bool nonfinite;
  bool hot_candidate;
  bool cold_candidate;
  bool hot_protected;
  bool cold_protected;
  glass_isolated_cosmetic_classify_f32(
      frame,
      width,
      height,
      i,
      low_thresholds[frame_pos],
      high_thresholds[frame_pos],
      medians[frame_pos],
      structure_sigma,
      sigmas[frame_pos],
      min_neighbor_support,
      &hot,
      &cold,
      &nonfinite,
      &hot_candidate,
      &cold_candidate,
      &hot_protected,
      &cold_protected);
  if (hot_candidate) {
    atomicAdd(&frame_counts[3], 1ULL);
  }
  if (cold_candidate) {
    atomicAdd(&frame_counts[4], 1ULL);
  }
  if (hot_protected) {
    atomicAdd(&frame_counts[5], 1ULL);
  }
  if (cold_protected) {
    atomicAdd(&frame_counts[6], 1ULL);
  }
  if (nonfinite) {
    atomicAdd(&frame_counts[2], 1ULL);
    return;
  }
  if (hot) {
    atomicAdd(&frame_counts[0], 1ULL);
    return;
  }
  if (cold) {
    atomicAdd(&frame_counts[1], 1ULL);
  }
}

void glass_apply_isolated_cosmetic_threshold_mask_frames_f32_launch(
    float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const std::size_t n = width * height;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  const dim3 grid(blocks, static_cast<unsigned int>(frame_count));
  glass_apply_isolated_cosmetic_threshold_mask_frames_f32_kernel<<<grid, threads>>>(
      stack,
      width,
      height,
      frame_indices,
      low_thresholds,
      high_thresholds,
      medians,
      sigmas,
      frame_count,
      structure_sigma,
      min_neighbor_support,
      counts);
}

void glass_count_isolated_cosmetic_threshold_mask_frames_f32_launch(
    const float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts) {
  constexpr int threads = 256;
  const std::size_t n = width * height;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  const dim3 grid(blocks, static_cast<unsigned int>(frame_count));
  glass_count_isolated_cosmetic_threshold_mask_frames_f32_kernel<<<grid, threads>>>(
      stack,
      width,
      height,
      frame_indices,
      low_thresholds,
      high_thresholds,
      medians,
      sigmas,
      frame_count,
      structure_sigma,
      min_neighbor_support,
      counts);
}

__global__ void glass_sample_frame_even_f32_kernel(
    const float* frame,
    float* sample,
    std::size_t n,
    std::size_t sample_count) {
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= sample_count) {
    return;
  }
  std::size_t source = i;
  if (sample_count < n) {
    source = static_cast<std::size_t>(
        (static_cast<unsigned long long>(i) * static_cast<unsigned long long>(n)) /
        static_cast<unsigned long long>(sample_count));
    if (source >= n) {
      source = n - 1;
    }
  }
  sample[i] = frame[source];
}

void glass_sample_frame_even_f32_launch(
    const float* frame,
    float* sample,
    std::size_t n,
    std::size_t sample_count) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((sample_count + threads - 1) / threads);
  glass_sample_frame_even_f32_kernel<<<blocks, threads>>>(frame, sample, n, sample_count);
}

__global__ void glass_frame_minmax_count_f32_kernel(
    const float* frame,
    float* partial_min,
    float* partial_max,
    unsigned long long* partial_count,
    std::size_t n) {
  constexpr int threads = 256;
  __shared__ float s_min[threads];
  __shared__ float s_max[threads];
  __shared__ unsigned long long s_count[threads];

  const int tid = threadIdx.x;
  float local_min = 3.402823466e+38f;
  float local_max = -3.402823466e+38f;
  unsigned long long local_count = 0ULL;
  const std::size_t stride = static_cast<std::size_t>(blockDim.x) * static_cast<std::size_t>(gridDim.x);
  for (std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + tid); i < n; i += stride) {
    const float value = frame[i];
    if (isfinite(value)) {
      local_min = fminf(local_min, value);
      local_max = fmaxf(local_max, value);
      ++local_count;
    }
  }
  s_min[tid] = local_min;
  s_max[tid] = local_max;
  s_count[tid] = local_count;
  __syncthreads();

  for (int offset = threads / 2; offset > 0; offset >>= 1) {
    if (tid < offset) {
      s_min[tid] = fminf(s_min[tid], s_min[tid + offset]);
      s_max[tid] = fmaxf(s_max[tid], s_max[tid + offset]);
      s_count[tid] += s_count[tid + offset];
    }
    __syncthreads();
  }
  if (tid == 0) {
    partial_min[blockIdx.x] = s_min[0];
    partial_max[blockIdx.x] = s_max[0];
    partial_count[blockIdx.x] = s_count[0];
  }
}

void glass_frame_minmax_count_f32_launch(
    const float* frame,
    float* partial_min,
    float* partial_max,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks) {
  constexpr int threads = 256;
  glass_frame_minmax_count_f32_kernel<<<blocks, threads>>>(
      frame,
      partial_min,
      partial_max,
      partial_count,
      n);
}

__global__ void glass_frame_histogram_f32_kernel(
    const float* frame,
    unsigned long long* histogram,
    std::size_t n,
    float min_value,
    float inv_bin_width,
    int bin_count) {
  const std::size_t stride = static_cast<std::size_t>(blockDim.x) * static_cast<std::size_t>(gridDim.x);
  for (std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x); i < n; i += stride) {
    const float value = frame[i];
    if (!isfinite(value)) {
      continue;
    }
    int bin = static_cast<int>((value - min_value) * inv_bin_width);
    if (bin < 0) {
      bin = 0;
    } else if (bin >= bin_count) {
      bin = bin_count - 1;
    }
    atomicAdd(&histogram[bin], 1ULL);
  }
}

void glass_frame_histogram_f32_launch(
    const float* frame,
    unsigned long long* histogram,
    std::size_t n,
    float min_value,
    float inv_bin_width,
    int bin_count,
    int blocks) {
  constexpr int threads = 256;
  glass_frame_histogram_f32_kernel<<<blocks, threads>>>(
      frame,
      histogram,
      n,
      min_value,
      inv_bin_width,
      bin_count);
}

__global__ void glass_frame_absdev_histogram_f32_kernel(
    const float* frame,
    unsigned long long* histogram,
    std::size_t n,
    float center,
    float inv_bin_width,
    int bin_count) {
  const std::size_t stride = static_cast<std::size_t>(blockDim.x) * static_cast<std::size_t>(gridDim.x);
  for (std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x); i < n; i += stride) {
    const float value = frame[i];
    if (!isfinite(value)) {
      continue;
    }
    int bin = static_cast<int>(fabsf(value - center) * inv_bin_width);
    if (bin < 0) {
      bin = 0;
    } else if (bin >= bin_count) {
      bin = bin_count - 1;
    }
    atomicAdd(&histogram[bin], 1ULL);
  }
}

void glass_frame_absdev_histogram_f32_launch(
    const float* frame,
    unsigned long long* histogram,
    std::size_t n,
    float center,
    float inv_bin_width,
    int bin_count,
    int blocks) {
  constexpr int threads = 256;
  glass_frame_absdev_histogram_f32_kernel<<<blocks, threads>>>(
      frame,
      histogram,
      n,
      center,
      inv_bin_width,
      bin_count);
}

__global__ void glass_integrate_resident_weighted_mean_f32_kernel(
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
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (!isfinite(value)) {
      continue;
    }
    sum += value * weight;
    weight_sum += weight;
  }
  weight_map[pixel] = weight_sum;
  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
}

void glass_integrate_resident_weighted_mean_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  glass_integrate_resident_weighted_mean_f32_kernel<<<blocks, threads>>>(
      stack,
      weights,
      master,
      weight_map,
      frame_count,
      pixels_per_frame);
}

__global__ void glass_integrate_resident_tile_local_weighted_mean_f32_kernel(
    const float* stack,
    const float* weights,
    const unsigned char* target_mask,
    const int* tile_extents,
    const float* tile_multipliers,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    int width,
    int height,
    int tile_count) {
  const std::size_t pixels_per_frame =
      static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (pixel >= pixels_per_frame) {
    return;
  }

  const int x = static_cast<int>(pixel % static_cast<std::size_t>(width));
  const int y = static_cast<int>(pixel / static_cast<std::size_t>(width));
  float tile_multiplier = 1.0f;
  for (int tile = 0; tile < tile_count; ++tile) {
    const int base = tile * 4;
    const int x0 = tile_extents[base + 0];
    const int y0 = tile_extents[base + 1];
    const int x1 = tile_extents[base + 2];
    const int y1 = tile_extents[base + 3];
    if (x >= x0 && x < x1 && y >= y0 && y < y1) {
      tile_multiplier = tile_multipliers[tile];
      break;
    }
  }

  float sum = 0.0f;
  float weight_sum = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    float weight = weights[frame];
    if (target_mask[frame] != 0) {
      weight *= tile_multiplier;
    }
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (!isfinite(value)) {
      continue;
    }
    sum += value * weight;
    weight_sum += weight;
  }
  weight_map[pixel] = weight_sum;
  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
}

void glass_integrate_resident_tile_local_weighted_mean_f32_launch(
    const float* stack,
    const float* weights,
    const unsigned char* target_mask,
    const int* tile_extents,
    const float* tile_multipliers,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    int width,
    int height,
    int tile_count) {
  const std::size_t pixels_per_frame =
      static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  glass_integrate_resident_tile_local_weighted_mean_f32_kernel<<<blocks, threads>>>(
      stack,
      weights,
      target_mask,
      tile_extents,
      tile_multipliers,
      master,
      weight_map,
      frame_count,
      width,
      height,
      tile_count);
}

__global__ void glass_integrate_resident_sigma_clip_f32_kernel(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    bool winsorize) {
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (pixel >= pixels_per_frame) {
    return;
  }

  float mean = 0.0f;
  float count = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (isfinite(value)) {
      mean += value;
      count += 1.0f;
    }
  }
  if (count <= 0.0f) {
    master[pixel] = 0.0f;
    if (weight_map != nullptr) {
      weight_map[pixel] = 0.0f;
    }
    if (coverage_map != nullptr) {
      coverage_map[pixel] = 0.0f;
    }
    if (low_rejection_map != nullptr) {
      low_rejection_map[pixel] = 0.0f;
    }
    if (high_rejection_map != nullptr) {
      high_rejection_map[pixel] = 0.0f;
    }
    return;
  }
  mean /= count;

  float variance = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (isfinite(value)) {
      const float delta = value - mean;
      variance += delta * delta;
    }
  }
  const float stddev = sqrtf(variance / count);
  float center = mean;
  float scale = stddev;
  float low_threshold = center - low_sigma * scale;
  float high_threshold = center + high_sigma * scale;
  if (winsorize) {
    float winsor_mean = 0.0f;
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < low_threshold) {
        value = low_threshold;
      } else if (value > high_threshold) {
        value = high_threshold;
      }
      winsor_mean += value;
    }
    winsor_mean /= count;

    float winsor_variance = 0.0f;
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < low_threshold) {
        value = low_threshold;
      } else if (value > high_threshold) {
        value = high_threshold;
      }
      const float delta = value - winsor_mean;
      winsor_variance += delta * delta;
    }
    center = winsor_mean;
    scale = sqrtf(winsor_variance / count);
    low_threshold = center - low_sigma * scale;
    high_threshold = center + high_sigma * scale;
  }

  float sum = 0.0f;
  float weight_sum = 0.0f;
  float coverage = 0.0f;
  float low_reject = 0.0f;
  float high_reject = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    float value = stack[frame * pixels_per_frame + pixel];
    if (!isfinite(value)) {
      continue;
    }
    bool rejected = false;
    if (value < low_threshold) {
      if (low_rejection_map != nullptr) {
        low_reject += 1.0f;
      }
      rejected = true;
    } else if (value > high_threshold) {
      if (high_rejection_map != nullptr) {
        high_reject += 1.0f;
      }
      rejected = true;
    }
    if (rejected) {
      continue;
    }
    sum += value * weight;
    weight_sum += weight;
    if (coverage_map != nullptr) {
      coverage += 1.0f;
    }
  }

  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
  if (weight_map != nullptr) {
    weight_map[pixel] = weight_sum;
  }
  if (coverage_map != nullptr) {
    coverage_map[pixel] = coverage;
  }
  if (low_rejection_map != nullptr) {
    low_rejection_map[pixel] = low_reject;
  }
  if (high_rejection_map != nullptr) {
    high_rejection_map[pixel] = high_reject;
  }
}

void glass_integrate_resident_sigma_clip_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    bool winsorize) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  glass_integrate_resident_sigma_clip_f32_kernel<<<blocks, threads>>>(
      stack,
      weights,
      master,
      weight_map,
      coverage_map,
      low_rejection_map,
      high_rejection_map,
      frame_count,
      pixels_per_frame,
      low_sigma,
      high_sigma,
      winsorize);
}

constexpr int kGlassHardenedWinsorizedSmallMaxFrames = 256;
constexpr int kGlassHardenedWinsorizedLargeMaxFrames = 512;

__device__ void glass_swap_f32(float& a, float& b) {
  const float tmp = a;
  a = b;
  b = tmp;
}

__device__ float glass_select_kth_range_f32(float* values, int left, int right, int k) {
  while (left < right) {
    const float pivot = values[(left + right) >> 1];
    int lower = left;
    int scan = left;
    int upper = right;
    while (scan <= upper) {
      const float value = values[scan];
      if (value < pivot) {
        glass_swap_f32(values[lower], values[scan]);
        ++lower;
        ++scan;
      } else if (value > pivot) {
        glass_swap_f32(values[scan], values[upper]);
        --upper;
      } else {
        ++scan;
      }
    }
    if (k < lower) {
      right = lower - 1;
    } else if (k > upper) {
      left = upper + 1;
    } else {
      return values[k];
    }
  }
  return values[left];
}

__device__ float glass_select_kth_f32(float* values, int count, int k) {
  return glass_select_kth_range_f32(values, 0, count - 1, k);
}

__device__ float glass_percentile_select_f32(float* values, int count, float fraction) {
  if (count <= 0) {
    return 0.0f;
  }
  if (count == 1) {
    return values[0];
  }
  const float position = static_cast<float>(count - 1) * fraction;
  const int lower = static_cast<int>(floorf(position));
  int upper = lower + 1;
  if (upper >= count) {
    upper = count - 1;
  }
  const float t = position - static_cast<float>(lower);
  const float lower_value = glass_select_kth_f32(values, count, lower);
  if (upper == lower) {
    return lower_value;
  }
  const float upper_value = glass_select_kth_f32(values, count, upper);
  return lower_value * (1.0f - t) + upper_value * t;
}

__device__ void glass_percentile_bounds_f32(
    int count,
    float fraction,
    int* lower,
    int* upper,
    float* t) {
  const float position = static_cast<float>(count - 1) * fraction;
  *lower = static_cast<int>(floorf(position));
  *upper = *lower + 1;
  if (*upper >= count) {
    *upper = count - 1;
  }
  *t = position - static_cast<float>(*lower);
}

__device__ void glass_add_unique_rank_sorted_f32(int rank, int* ranks, int* rank_count) {
  int count = *rank_count;
  int pos = 0;
  while (pos < count && ranks[pos] < rank) {
    ++pos;
  }
  if (pos < count && ranks[pos] == rank) {
    return;
  }
  for (int i = count; i > pos; --i) {
    ranks[i] = ranks[i - 1];
  }
  ranks[pos] = rank;
  *rank_count = count + 1;
}

__device__ float glass_lookup_selected_rank_f32(
    int rank,
    const int* ranks,
    const float* selected,
    int rank_count) {
  for (int i = 0; i < rank_count; ++i) {
    if (ranks[i] == rank) {
      return selected[i];
    }
  }
  return 0.0f;
}

__device__ float glass_interpolate_selected_percentile_f32(
    int lower,
    int upper,
    float t,
    const int* ranks,
    const float* selected,
    int rank_count) {
  const float lower_value = glass_lookup_selected_rank_f32(lower, ranks, selected, rank_count);
  if (upper == lower || t <= 0.0f) {
    return lower_value;
  }
  const float upper_value = glass_lookup_selected_rank_f32(upper, ranks, selected, rank_count);
  return lower_value * (1.0f - t) + upper_value * t;
}

__device__ void glass_select_quartiles_f32(
    float* values,
    int count,
    float* median,
    float* q25,
    float* q75) {
  if (count <= 0) {
    *median = 0.0f;
    *q25 = 0.0f;
    *q75 = 0.0f;
    return;
  }
  if (count == 1) {
    *median = values[0];
    *q25 = values[0];
    *q75 = values[0];
    return;
  }

  int q25_lower = 0;
  int q25_upper = 0;
  float q25_t = 0.0f;
  int median_lower = 0;
  int median_upper = 0;
  float median_t = 0.0f;
  int q75_lower = 0;
  int q75_upper = 0;
  float q75_t = 0.0f;
  glass_percentile_bounds_f32(count, 0.25f, &q25_lower, &q25_upper, &q25_t);
  glass_percentile_bounds_f32(count, 0.5f, &median_lower, &median_upper, &median_t);
  glass_percentile_bounds_f32(count, 0.75f, &q75_lower, &q75_upper, &q75_t);

  int ranks[6];
  float selected[6];
  int rank_count = 0;
  glass_add_unique_rank_sorted_f32(q25_lower, ranks, &rank_count);
  if (q25_upper != q25_lower && q25_t > 0.0f) {
    glass_add_unique_rank_sorted_f32(q25_upper, ranks, &rank_count);
  }
  glass_add_unique_rank_sorted_f32(median_lower, ranks, &rank_count);
  if (median_upper != median_lower && median_t > 0.0f) {
    glass_add_unique_rank_sorted_f32(median_upper, ranks, &rank_count);
  }
  glass_add_unique_rank_sorted_f32(q75_lower, ranks, &rank_count);
  if (q75_upper != q75_lower && q75_t > 0.0f) {
    glass_add_unique_rank_sorted_f32(q75_upper, ranks, &rank_count);
  }

  int search_left = 0;
  for (int i = 0; i < rank_count; ++i) {
    const int rank = ranks[i];
    selected[i] = glass_select_kth_range_f32(values, search_left, count - 1, rank);
    search_left = rank + 1;
  }

  *q25 = glass_interpolate_selected_percentile_f32(
      q25_lower, q25_upper, q25_t, ranks, selected, rank_count);
  *median = glass_interpolate_selected_percentile_f32(
      median_lower, median_upper, median_t, ranks, selected, rank_count);
  *q75 = glass_interpolate_selected_percentile_f32(
      q75_lower, q75_upper, q75_t, ranks, selected, rank_count);
}

__device__ float glass_count_map_value_f32(float value, const float*) {
  return value;
}

__device__ unsigned short glass_count_map_value_f32(float value, const unsigned short*) {
  if (!isfinite(value) || value <= 0.0f) {
    return 0;
  }
  const float clamped = fminf(value, 65535.0f);
  return static_cast<unsigned short>(clamped + 0.5f);
}

template <typename CountT, int MaxFrames, bool Enabled>
struct GlassOrderedSampleStore {
  __device__ void set(int, float) {}
  __device__ float get(int) const { return 0.0f; }
};

template <typename CountT, int MaxFrames>
struct GlassOrderedSampleStore<CountT, MaxFrames, true> {
  float values[MaxFrames];
  __device__ void set(int index, float value) { values[index] = value; }
  __device__ float get(int index) const { return values[index]; }
};

template <typename CountT, int MaxFrames, bool UnitPositiveWeights, bool ReuseLocalUnitSamples>
__global__ void glass_integrate_resident_hardened_winsorized_sigma_f32_kernel(
    const float* stack,
    const float* weights,
    const unsigned int* active_indices,
    float* master,
    float* weight_map,
    CountT* coverage_map,
    CountT* low_rejection_map,
    CountT* high_rejection_map,
    std::size_t frame_count,
    std::size_t active_frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction) {
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (pixel >= pixels_per_frame) {
    return;
  }

  float values[MaxFrames];
  GlassOrderedSampleStore<CountT, MaxFrames, ReuseLocalUnitSamples> ordered_values;
  int count = 0;
  const std::size_t sample_frame_count = UnitPositiveWeights ? active_frame_count : frame_count;
  for (std::size_t sample_pos = 0; sample_pos < sample_frame_count; ++sample_pos) {
    const std::size_t frame =
        UnitPositiveWeights ? static_cast<std::size_t>(active_indices[sample_pos]) : sample_pos;
    if (!UnitPositiveWeights) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (!isfinite(value)) {
      continue;
    }
    if (count < MaxFrames) {
      values[count] = value;
      ordered_values.set(count, value);
      ++count;
    }
  }
  if (count <= 0) {
    master[pixel] = 0.0f;
    if (weight_map != nullptr) {
      weight_map[pixel] = 0.0f;
    }
    if (coverage_map != nullptr) {
      coverage_map[pixel] = glass_count_map_value_f32(0.0f, coverage_map);
    }
    if (low_rejection_map != nullptr) {
      low_rejection_map[pixel] = glass_count_map_value_f32(0.0f, low_rejection_map);
    }
    if (high_rejection_map != nullptr) {
      high_rejection_map[pixel] = glass_count_map_value_f32(0.0f, high_rejection_map);
    }
    return;
  }

  float mean = 0.0f;
  for (int i = 0; i < count; ++i) {
    mean += values[i];
  }
  mean /= static_cast<float>(count);
  float variance = 0.0f;
  for (int i = 0; i < count; ++i) {
    const float delta = values[i] - mean;
    variance += delta * delta;
  }
  const float fallback_scale = sqrtf(variance / static_cast<float>(count));

  float center0 = 0.0f;
  float q25 = 0.0f;
  float q75 = 0.0f;
  glass_select_quartiles_f32(values, count, &center0, &q25, &q75);
  float first_scale = (q75 - q25) / 1.349f;
  if (!(first_scale > 0.0f) || !isfinite(first_scale)) {
    first_scale = fallback_scale;
  }
  const float first_low = center0 - low_sigma * first_scale;
  const float first_high = center0 + high_sigma * first_scale;

  float winsor_mean = 0.0f;
  if (ReuseLocalUnitSamples) {
    for (int i = 0; i < count; ++i) {
      float value = ordered_values.get(i);
      if (value < first_low) {
        value = first_low;
      } else if (value > first_high) {
        value = first_high;
      }
      winsor_mean += value;
    }
  } else if (UnitPositiveWeights) {
    for (std::size_t active_pos = 0; active_pos < active_frame_count; ++active_pos) {
      const std::size_t frame = static_cast<std::size_t>(active_indices[active_pos]);
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < first_low) {
        value = first_low;
      } else if (value > first_high) {
        value = first_high;
      }
      winsor_mean += value;
    }
  } else {
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < first_low) {
        value = first_low;
      } else if (value > first_high) {
        value = first_high;
      }
      winsor_mean += value;
    }
  }
  winsor_mean /= static_cast<float>(count);

  float winsor_variance = 0.0f;
  if (ReuseLocalUnitSamples) {
    for (int i = 0; i < count; ++i) {
      float value = ordered_values.get(i);
      if (value < first_low) {
        value = first_low;
      } else if (value > first_high) {
        value = first_high;
      }
      const float delta = value - winsor_mean;
      winsor_variance += delta * delta;
    }
  } else if (UnitPositiveWeights) {
    for (std::size_t active_pos = 0; active_pos < active_frame_count; ++active_pos) {
      const std::size_t frame = static_cast<std::size_t>(active_indices[active_pos]);
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < first_low) {
        value = first_low;
      } else if (value > first_high) {
        value = first_high;
      }
      const float delta = value - winsor_mean;
      winsor_variance += delta * delta;
    }
  } else {
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < first_low) {
        value = first_low;
      } else if (value > first_high) {
        value = first_high;
      }
      const float delta = value - winsor_mean;
      winsor_variance += delta * delta;
    }
  }
  float scale = sqrtf(winsor_variance / static_cast<float>(count));
  if (!(scale > 0.0f) || !isfinite(scale)) {
    scale = first_scale;
  }
  const float low_threshold = winsor_mean - low_sigma * scale;
  const float high_threshold = winsor_mean + high_sigma * scale;

  int low_reject_count = 0;
  int high_reject_count = 0;
  if (scale > 0.0f) {
    if (ReuseLocalUnitSamples) {
      for (int i = 0; i < count; ++i) {
        const float value = ordered_values.get(i);
        if (value < low_threshold) {
          ++low_reject_count;
        } else if (value > high_threshold) {
          ++high_reject_count;
        }
      }
    } else if (UnitPositiveWeights) {
      for (std::size_t active_pos = 0; active_pos < active_frame_count; ++active_pos) {
        const std::size_t frame = static_cast<std::size_t>(active_indices[active_pos]);
        const float value = stack[frame * pixels_per_frame + pixel];
        if (!isfinite(value)) {
          continue;
        }
        if (value < low_threshold) {
          ++low_reject_count;
        } else if (value > high_threshold) {
          ++high_reject_count;
        }
      }
    } else {
      for (std::size_t frame = 0; frame < frame_count; ++frame) {
        const float weight = weights[frame];
        if (weight <= 0.0f || !isfinite(weight)) {
          continue;
        }
        const float value = stack[frame * pixels_per_frame + pixel];
        if (!isfinite(value)) {
          continue;
        }
        if (value < low_threshold) {
          ++low_reject_count;
        } else if (value > high_threshold) {
          ++high_reject_count;
        }
      }
    }
  }
  const int reject_count = low_reject_count + high_reject_count;
  const int minimum_samples = min_samples < 1 ? 1 : min_samples;
  const float reject_fraction =
      count > 0 ? static_cast<float>(reject_count) / static_cast<float>(count) : 0.0f;
  const bool allow_rejection =
      reject_count > 0 &&
      (count - reject_count) >= minimum_samples &&
      reject_fraction <= max_reject_fraction;

  float sum = 0.0f;
  float weight_sum = 0.0f;
  float coverage = 0.0f;
  float low_reject = 0.0f;
  float high_reject = 0.0f;
  if (ReuseLocalUnitSamples) {
    for (int i = 0; i < count; ++i) {
      const float value = ordered_values.get(i);
      if (allow_rejection && value < low_threshold) {
        low_reject += 1.0f;
        continue;
      }
      if (allow_rejection && value > high_threshold) {
        high_reject += 1.0f;
        continue;
      }
      sum += value;
      weight_sum += 1.0f;
      coverage += 1.0f;
    }
  } else if (UnitPositiveWeights) {
    for (std::size_t active_pos = 0; active_pos < active_frame_count; ++active_pos) {
      const std::size_t frame = static_cast<std::size_t>(active_indices[active_pos]);
      const float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (allow_rejection && value < low_threshold) {
        low_reject += 1.0f;
        continue;
      }
      if (allow_rejection && value > high_threshold) {
        high_reject += 1.0f;
        continue;
      }
      sum += value;
      weight_sum += 1.0f;
      coverage += 1.0f;
    }
  } else {
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      const float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (allow_rejection && value < low_threshold) {
        low_reject += 1.0f;
        continue;
      }
      if (allow_rejection && value > high_threshold) {
        high_reject += 1.0f;
        continue;
      }
      sum += value * weight;
      weight_sum += weight;
      coverage += 1.0f;
    }
  }

  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
  if (weight_map != nullptr) {
    weight_map[pixel] = weight_sum;
  }
  if (coverage_map != nullptr) {
    coverage_map[pixel] = glass_count_map_value_f32(coverage, coverage_map);
  }
  if (low_rejection_map != nullptr) {
    low_rejection_map[pixel] = glass_count_map_value_f32(low_reject, low_rejection_map);
  }
  if (high_rejection_map != nullptr) {
    high_rejection_map[pixel] = glass_count_map_value_f32(high_reject, high_rejection_map);
  }
}

template <typename CountT>
void glass_integrate_resident_hardened_winsorized_sigma_f32_launch_typed(
    const float* stack,
    const float* weights,
    const unsigned int* active_indices,
    float* master,
    float* weight_map,
    CountT* coverage_map,
    CountT* low_rejection_map,
    CountT* high_rejection_map,
    std::size_t frame_count,
    std::size_t active_frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction,
    bool unit_positive_weights,
    bool unit_positive_local_reuse) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  const std::size_t capacity_frame_count =
      active_frame_count > 0 ? active_frame_count : frame_count;
  if (capacity_frame_count <= static_cast<std::size_t>(kGlassHardenedWinsorizedSmallMaxFrames)) {
    if (unit_positive_local_reuse) {
      glass_integrate_resident_hardened_winsorized_sigma_f32_kernel<
          CountT,
          kGlassHardenedWinsorizedSmallMaxFrames,
          false,
          true><<<blocks, threads>>>(
          stack,
          weights,
          active_indices,
          master,
          weight_map,
          coverage_map,
          low_rejection_map,
          high_rejection_map,
          frame_count,
          active_frame_count,
          pixels_per_frame,
          low_sigma,
          high_sigma,
          min_samples,
          max_reject_fraction);
    } else if (unit_positive_weights) {
      glass_integrate_resident_hardened_winsorized_sigma_f32_kernel<
          CountT,
          kGlassHardenedWinsorizedSmallMaxFrames,
          true,
          false><<<blocks, threads>>>(
          stack,
          weights,
          active_indices,
          master,
          weight_map,
          coverage_map,
          low_rejection_map,
          high_rejection_map,
          frame_count,
          active_frame_count,
          pixels_per_frame,
          low_sigma,
          high_sigma,
          min_samples,
          max_reject_fraction);
    } else {
      glass_integrate_resident_hardened_winsorized_sigma_f32_kernel<
          CountT,
          kGlassHardenedWinsorizedSmallMaxFrames,
          false,
          false><<<blocks, threads>>>(
          stack,
          weights,
          active_indices,
          master,
          weight_map,
          coverage_map,
          low_rejection_map,
          high_rejection_map,
          frame_count,
          active_frame_count,
          pixels_per_frame,
          low_sigma,
          high_sigma,
          min_samples,
          max_reject_fraction);
    }
    return;
  }
  if (unit_positive_local_reuse) {
    glass_integrate_resident_hardened_winsorized_sigma_f32_kernel<
        CountT,
        kGlassHardenedWinsorizedLargeMaxFrames,
        false,
        true><<<blocks, threads>>>(
        stack,
        weights,
        active_indices,
        master,
        weight_map,
        coverage_map,
        low_rejection_map,
        high_rejection_map,
        frame_count,
        active_frame_count,
        pixels_per_frame,
        low_sigma,
        high_sigma,
        min_samples,
        max_reject_fraction);
  } else if (unit_positive_weights) {
    glass_integrate_resident_hardened_winsorized_sigma_f32_kernel<
        CountT,
        kGlassHardenedWinsorizedLargeMaxFrames,
        true,
        false><<<blocks, threads>>>(
        stack,
        weights,
        active_indices,
        master,
        weight_map,
        coverage_map,
        low_rejection_map,
        high_rejection_map,
        frame_count,
        active_frame_count,
        pixels_per_frame,
        low_sigma,
        high_sigma,
        min_samples,
        max_reject_fraction);
  } else {
    glass_integrate_resident_hardened_winsorized_sigma_f32_kernel<
        CountT,
        kGlassHardenedWinsorizedLargeMaxFrames,
        false,
        false><<<blocks, threads>>>(
        stack,
        weights,
        active_indices,
        master,
        weight_map,
        coverage_map,
        low_rejection_map,
        high_rejection_map,
        frame_count,
        active_frame_count,
        pixels_per_frame,
        low_sigma,
        high_sigma,
        min_samples,
        max_reject_fraction);
  }
}

void glass_integrate_resident_hardened_winsorized_sigma_f32_launch(
    const float* stack,
    const float* weights,
    const unsigned int* active_indices,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    std::size_t active_frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction,
    bool unit_positive_weights,
    bool unit_positive_local_reuse) {
  glass_integrate_resident_hardened_winsorized_sigma_f32_launch_typed<float>(
      stack,
      weights,
      active_indices,
      master,
      weight_map,
      coverage_map,
      low_rejection_map,
      high_rejection_map,
      frame_count,
      active_frame_count,
      pixels_per_frame,
      low_sigma,
      high_sigma,
      min_samples,
      max_reject_fraction,
      unit_positive_weights,
      unit_positive_local_reuse);
}

void glass_integrate_resident_hardened_winsorized_sigma_f32_u16_counts_launch(
    const float* stack,
    const float* weights,
    const unsigned int* active_indices,
    float* master,
    float* weight_map,
    unsigned short* coverage_map,
    unsigned short* low_rejection_map,
    unsigned short* high_rejection_map,
    std::size_t frame_count,
    std::size_t active_frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction,
    bool unit_positive_weights,
    bool unit_positive_local_reuse) {
  glass_integrate_resident_hardened_winsorized_sigma_f32_launch_typed<unsigned short>(
      stack,
      weights,
      active_indices,
      master,
      weight_map,
      coverage_map,
      low_rejection_map,
      high_rejection_map,
      frame_count,
      active_frame_count,
      pixels_per_frame,
      low_sigma,
      high_sigma,
      min_samples,
      max_reject_fraction,
      unit_positive_weights,
      unit_positive_local_reuse);
}

__global__ void glass_integrate_resident_tile_local_sigma_clip_f32_kernel(
    const float* stack,
    const float* weights,
    const unsigned char* target_mask,
    const int* tile_extents,
    const float* tile_multipliers,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    int width,
    int height,
    int tile_count,
    float low_sigma,
    float high_sigma,
    bool winsorize) {
  const std::size_t pixels_per_frame =
      static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (pixel >= pixels_per_frame) {
    return;
  }

  const int x = static_cast<int>(pixel % static_cast<std::size_t>(width));
  const int y = static_cast<int>(pixel / static_cast<std::size_t>(width));
  float tile_multiplier = 1.0f;
  for (int tile = 0; tile < tile_count; ++tile) {
    const int base = tile * 4;
    const int x0 = tile_extents[base + 0];
    const int y0 = tile_extents[base + 1];
    const int x1 = tile_extents[base + 2];
    const int y1 = tile_extents[base + 3];
    if (x >= x0 && x < x1 && y >= y0 && y < y1) {
      tile_multiplier = tile_multipliers[tile];
      break;
    }
  }

  float mean = 0.0f;
  float count = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    float weight = weights[frame];
    if (target_mask[frame] != 0) {
      weight *= tile_multiplier;
    }
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (isfinite(value)) {
      mean += value;
      count += 1.0f;
    }
  }
  if (count <= 0.0f) {
    master[pixel] = 0.0f;
    weight_map[pixel] = 0.0f;
    coverage_map[pixel] = 0.0f;
    low_rejection_map[pixel] = 0.0f;
    high_rejection_map[pixel] = 0.0f;
    return;
  }
  mean /= count;

  float variance = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    float weight = weights[frame];
    if (target_mask[frame] != 0) {
      weight *= tile_multiplier;
    }
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (isfinite(value)) {
      const float delta = value - mean;
      variance += delta * delta;
    }
  }
  const float stddev = sqrtf(variance / count);
  float center = mean;
  float scale = stddev;
  float low_threshold = center - low_sigma * scale;
  float high_threshold = center + high_sigma * scale;
  if (winsorize) {
    float winsor_mean = 0.0f;
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      float weight = weights[frame];
      if (target_mask[frame] != 0) {
        weight *= tile_multiplier;
      }
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < low_threshold) {
        value = low_threshold;
      } else if (value > high_threshold) {
        value = high_threshold;
      }
      winsor_mean += value;
    }
    winsor_mean /= count;

    float winsor_variance = 0.0f;
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      float weight = weights[frame];
      if (target_mask[frame] != 0) {
        weight *= tile_multiplier;
      }
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = stack[frame * pixels_per_frame + pixel];
      if (!isfinite(value)) {
        continue;
      }
      if (value < low_threshold) {
        value = low_threshold;
      } else if (value > high_threshold) {
        value = high_threshold;
      }
      const float delta = value - winsor_mean;
      winsor_variance += delta * delta;
    }
    center = winsor_mean;
    scale = sqrtf(winsor_variance / count);
    low_threshold = center - low_sigma * scale;
    high_threshold = center + high_sigma * scale;
  }

  float sum = 0.0f;
  float weight_sum = 0.0f;
  float coverage = 0.0f;
  float low_reject = 0.0f;
  float high_reject = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    float weight = weights[frame];
    if (target_mask[frame] != 0) {
      weight *= tile_multiplier;
    }
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    float value = stack[frame * pixels_per_frame + pixel];
    if (!isfinite(value)) {
      continue;
    }
    bool rejected = false;
    if (value < low_threshold) {
      low_reject += 1.0f;
      rejected = true;
    } else if (value > high_threshold) {
      high_reject += 1.0f;
      rejected = true;
    }
    if (rejected) {
      continue;
    }
    sum += value * weight;
    weight_sum += weight;
    coverage += 1.0f;
  }

  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
  weight_map[pixel] = weight_sum;
  coverage_map[pixel] = coverage;
  low_rejection_map[pixel] = low_reject;
  high_rejection_map[pixel] = high_reject;
}

void glass_integrate_resident_tile_local_sigma_clip_f32_launch(
    const float* stack,
    const float* weights,
    const unsigned char* target_mask,
    const int* tile_extents,
    const float* tile_multipliers,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    int width,
    int height,
    int tile_count,
    float low_sigma,
    float high_sigma,
    bool winsorize) {
  const std::size_t pixels_per_frame =
      static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  glass_integrate_resident_tile_local_sigma_clip_f32_kernel<<<blocks, threads>>>(
      stack,
      weights,
      target_mask,
      tile_extents,
      tile_multipliers,
      master,
      weight_map,
      coverage_map,
      low_rejection_map,
      high_rejection_map,
      frame_count,
      width,
      height,
      tile_count,
      low_sigma,
      high_sigma,
      winsorize);
}

__global__ void glass_integrate_matrix_warped_mean_f32_kernel(
    const float* stack,
    const float* weights,
    const float* inverses,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* geometric_coverage_map,
    std::size_t frame_count,
    int width,
    int height,
    int interpolation,
    float clamping_threshold) {
  const std::size_t pixels_per_frame = static_cast<std::size_t>(width) * height;
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
  if (pixel >= pixels_per_frame) {
    return;
  }

  float sum = 0.0f;
  float weight_sum = 0.0f;
  float finite_coverage = 0.0f;
  float geometric_coverage = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    float value = 0.0f;
    const float* input = stack + frame * pixels_per_frame;
    const float* inverse = inverses + frame * 9;
    const bool footprint_valid = interpolation == 1
        ? glass_fused_sample_matrix_lanczos3_f32(
              input, inverse, width, height, pixel, clamping_threshold, &value)
        : glass_fused_sample_matrix_bilinear_f32(input, inverse, width, height, pixel, &value);
    if (!footprint_valid) {
      continue;
    }
    geometric_coverage += 1.0f;
    if (!isfinite(value)) {
      continue;
    }
    sum += value * weight;
    weight_sum += weight;
    finite_coverage += 1.0f;
  }
  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
  weight_map[pixel] = weight_sum;
  if (coverage_map != nullptr) {
    coverage_map[pixel] = finite_coverage;
  }
  if (geometric_coverage_map != nullptr) {
    geometric_coverage_map[pixel] = geometric_coverage;
  }
}

void glass_integrate_matrix_warped_mean_f32_launch(
    const float* stack,
    const float* weights,
    const float* inverses,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* geometric_coverage_map,
    std::size_t frame_count,
    int width,
    int height,
    int interpolation,
    float clamping_threshold) {
  constexpr int threads = 256;
  const std::size_t pixels_per_frame = static_cast<std::size_t>(width) * height;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  glass_integrate_matrix_warped_mean_f32_kernel<<<blocks, threads>>>(
      stack,
      weights,
      inverses,
      master,
      weight_map,
      coverage_map,
      geometric_coverage_map,
      frame_count,
      width,
      height,
      interpolation,
      clamping_threshold);
}

__global__ void glass_integrate_matrix_warped_sigma_clip_f32_kernel(
    const float* stack,
    const float* weights,
    const float* inverses,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    float* geometric_coverage_map,
    std::size_t frame_count,
    int width,
    int height,
    int interpolation,
    float clamping_threshold,
    float low_sigma,
    float high_sigma,
    bool winsorize) {
  const std::size_t pixels_per_frame = static_cast<std::size_t>(width) * height;
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
  if (pixel >= pixels_per_frame) {
    return;
  }

  float mean = 0.0f;
  float count = 0.0f;
  float geometric_coverage = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    float value = 0.0f;
    const float* input = stack + frame * pixels_per_frame;
    const float* inverse = inverses + frame * 9;
    const bool footprint_valid = interpolation == 1
        ? glass_fused_sample_matrix_lanczos3_f32(
              input, inverse, width, height, pixel, clamping_threshold, &value)
        : glass_fused_sample_matrix_bilinear_f32(input, inverse, width, height, pixel, &value);
    if (!footprint_valid) {
      continue;
    }
    geometric_coverage += 1.0f;
    if (isfinite(value)) {
      mean += value;
      count += 1.0f;
    }
  }
  if (count <= 0.0f) {
    master[pixel] = 0.0f;
    weight_map[pixel] = 0.0f;
    if (coverage_map != nullptr) {
      coverage_map[pixel] = 0.0f;
    }
    if (low_rejection_map != nullptr) {
      low_rejection_map[pixel] = 0.0f;
    }
    if (high_rejection_map != nullptr) {
      high_rejection_map[pixel] = 0.0f;
    }
    if (geometric_coverage_map != nullptr) {
      geometric_coverage_map[pixel] = geometric_coverage;
    }
    return;
  }
  mean /= count;

  float variance = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    float value = 0.0f;
    const float* input = stack + frame * pixels_per_frame;
    const float* inverse = inverses + frame * 9;
    const bool footprint_valid = interpolation == 1
        ? glass_fused_sample_matrix_lanczos3_f32(
              input, inverse, width, height, pixel, clamping_threshold, &value)
        : glass_fused_sample_matrix_bilinear_f32(input, inverse, width, height, pixel, &value);
    if (footprint_valid && isfinite(value)) {
      const float delta = value - mean;
      variance += delta * delta;
    }
  }
  const float stddev = sqrtf(variance / count);
  float center = mean;
  float scale = stddev;
  float low_threshold = center - low_sigma * scale;
  float high_threshold = center + high_sigma * scale;
  if (winsorize) {
    float winsor_mean = 0.0f;
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = 0.0f;
      const float* input = stack + frame * pixels_per_frame;
      const float* inverse = inverses + frame * 9;
      const bool footprint_valid = interpolation == 1
          ? glass_fused_sample_matrix_lanczos3_f32(
                input, inverse, width, height, pixel, clamping_threshold, &value)
          : glass_fused_sample_matrix_bilinear_f32(input, inverse, width, height, pixel, &value);
      if (!footprint_valid || !isfinite(value)) {
        continue;
      }
      if (value < low_threshold) {
        value = low_threshold;
      } else if (value > high_threshold) {
        value = high_threshold;
      }
      winsor_mean += value;
    }
    winsor_mean /= count;

    float winsor_variance = 0.0f;
    for (std::size_t frame = 0; frame < frame_count; ++frame) {
      const float weight = weights[frame];
      if (weight <= 0.0f || !isfinite(weight)) {
        continue;
      }
      float value = 0.0f;
      const float* input = stack + frame * pixels_per_frame;
      const float* inverse = inverses + frame * 9;
      const bool footprint_valid = interpolation == 1
          ? glass_fused_sample_matrix_lanczos3_f32(
                input, inverse, width, height, pixel, clamping_threshold, &value)
          : glass_fused_sample_matrix_bilinear_f32(input, inverse, width, height, pixel, &value);
      if (!footprint_valid || !isfinite(value)) {
        continue;
      }
      if (value < low_threshold) {
        value = low_threshold;
      } else if (value > high_threshold) {
        value = high_threshold;
      }
      const float delta = value - winsor_mean;
      winsor_variance += delta * delta;
    }
    center = winsor_mean;
    scale = sqrtf(winsor_variance / count);
    low_threshold = center - low_sigma * scale;
    high_threshold = center + high_sigma * scale;
  }

  float sum = 0.0f;
  float weight_sum = 0.0f;
  float coverage = 0.0f;
  float low_reject = 0.0f;
  float high_reject = 0.0f;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    float value = 0.0f;
    const float* input = stack + frame * pixels_per_frame;
    const float* inverse = inverses + frame * 9;
    const bool footprint_valid = interpolation == 1
        ? glass_fused_sample_matrix_lanczos3_f32(
              input, inverse, width, height, pixel, clamping_threshold, &value)
        : glass_fused_sample_matrix_bilinear_f32(input, inverse, width, height, pixel, &value);
    if (!footprint_valid || !isfinite(value)) {
      continue;
    }
    bool rejected = false;
    if (value < low_threshold) {
      low_reject += 1.0f;
      rejected = true;
    } else if (value > high_threshold) {
      high_reject += 1.0f;
      rejected = true;
    }
    if (rejected) {
      continue;
    }
    sum += value * weight;
    weight_sum += weight;
    coverage += 1.0f;
  }

  master[pixel] = weight_sum > 0.0f ? sum / weight_sum : 0.0f;
  weight_map[pixel] = weight_sum;
  if (coverage_map != nullptr) {
    coverage_map[pixel] = coverage;
  }
  if (low_rejection_map != nullptr) {
    low_rejection_map[pixel] = low_reject;
  }
  if (high_rejection_map != nullptr) {
    high_rejection_map[pixel] = high_reject;
  }
  if (geometric_coverage_map != nullptr) {
    geometric_coverage_map[pixel] = geometric_coverage;
  }
}

void glass_integrate_matrix_warped_sigma_clip_f32_launch(
    const float* stack,
    const float* weights,
    const float* inverses,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    float* geometric_coverage_map,
    std::size_t frame_count,
    int width,
    int height,
    int interpolation,
    float clamping_threshold,
    float low_sigma,
    float high_sigma,
    bool winsorize) {
  constexpr int threads = 256;
  const std::size_t pixels_per_frame = static_cast<std::size_t>(width) * height;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  glass_integrate_matrix_warped_sigma_clip_f32_kernel<<<blocks, threads>>>(
      stack,
      weights,
      inverses,
      master,
      weight_map,
      coverage_map,
      low_rejection_map,
      high_rejection_map,
      geometric_coverage_map,
      frame_count,
      width,
      height,
      interpolation,
      clamping_threshold,
      low_sigma,
      high_sigma,
      winsorize);
}
