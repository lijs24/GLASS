#include "common.cuh"

#include <cstddef>
#include <cmath>

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
