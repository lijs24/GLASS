#include "common.cuh"

#include <cstddef>
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
      local_min = fminf(local_min, value);
      local_max = fmaxf(local_max, value);
    }
  }

  if (fabsf(weight_sum) <= 1.0e-12f) {
    return false;
  }
  float value = weighted_sum / weight_sum;
  if (clamping_threshold >= 0.0f && local_max >= local_min) {
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
    weight_map[pixel] = 0.0f;
    coverage_map[pixel] = 0.0f;
    low_rejection_map[pixel] = 0.0f;
    high_rejection_map[pixel] = 0.0f;
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

constexpr int kGlassHardenedWinsorizedMaxFrames = 256;

__device__ float glass_percentile_sorted_f32(const float* values, int count, float fraction) {
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
  return values[lower] * (1.0f - t) + values[upper] * t;
}

__global__ void glass_integrate_resident_hardened_winsorized_sigma_f32_kernel(
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
    float high_sigma) {
  const std::size_t pixel = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (pixel >= pixels_per_frame) {
    return;
  }

  float values[kGlassHardenedWinsorizedMaxFrames];
  int count = 0;
  for (std::size_t frame = 0; frame < frame_count; ++frame) {
    const float weight = weights[frame];
    if (weight <= 0.0f || !isfinite(weight)) {
      continue;
    }
    const float value = stack[frame * pixels_per_frame + pixel];
    if (!isfinite(value)) {
      continue;
    }
    if (count < kGlassHardenedWinsorizedMaxFrames) {
      values[count] = value;
      ++count;
    }
  }
  if (count <= 0) {
    master[pixel] = 0.0f;
    weight_map[pixel] = 0.0f;
    coverage_map[pixel] = 0.0f;
    low_rejection_map[pixel] = 0.0f;
    high_rejection_map[pixel] = 0.0f;
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

  for (int i = 1; i < count; ++i) {
    const float item = values[i];
    int j = i - 1;
    while (j >= 0 && values[j] > item) {
      values[j + 1] = values[j];
      --j;
    }
    values[j + 1] = item;
  }

  const float center0 = glass_percentile_sorted_f32(values, count, 0.5f);
  const float q25 = glass_percentile_sorted_f32(values, count, 0.25f);
  const float q75 = glass_percentile_sorted_f32(values, count, 0.75f);
  float first_scale = (q75 - q25) / 1.349f;
  if (!(first_scale > 0.0f) || !isfinite(first_scale)) {
    first_scale = fallback_scale;
  }
  const float first_low = center0 - low_sigma * first_scale;
  const float first_high = center0 + high_sigma * first_scale;

  float winsor_mean = 0.0f;
  for (int i = 0; i < count; ++i) {
    float value = values[i];
    if (value < first_low) {
      value = first_low;
    } else if (value > first_high) {
      value = first_high;
    }
    winsor_mean += value;
  }
  winsor_mean /= static_cast<float>(count);

  float winsor_variance = 0.0f;
  for (int i = 0; i < count; ++i) {
    float value = values[i];
    if (value < first_low) {
      value = first_low;
    } else if (value > first_high) {
      value = first_high;
    }
    const float delta = value - winsor_mean;
    winsor_variance += delta * delta;
  }
  float scale = sqrtf(winsor_variance / static_cast<float>(count));
  if (!(scale > 0.0f) || !isfinite(scale)) {
    scale = first_scale;
  }
  const float low_threshold = winsor_mean - low_sigma * scale;
  const float high_threshold = winsor_mean + high_sigma * scale;

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
    const float value = stack[frame * pixels_per_frame + pixel];
    if (!isfinite(value)) {
      continue;
    }
    if (scale > 0.0f && value < low_threshold) {
      low_reject += 1.0f;
      continue;
    }
    if (scale > 0.0f && value > high_threshold) {
      high_reject += 1.0f;
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

void glass_integrate_resident_hardened_winsorized_sigma_f32_launch(
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
    float high_sigma) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((pixels_per_frame + threads - 1) / threads);
  glass_integrate_resident_hardened_winsorized_sigma_f32_kernel<<<blocks, threads>>>(
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
      high_sigma);
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
