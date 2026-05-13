#include "common.cuh"

#include <cstddef>
#include <math.h>

__global__ void glass_warp_translation_f32_kernel(
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

void glass_warp_translation_f32_launch(
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
  glass_warp_translation_f32_kernel<<<blocks, threads>>>(
      input, output, coverage, width, height, dx, dy, fill);
}

__global__ void glass_warp_translation_bilinear_f32_kernel(
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

void glass_warp_translation_bilinear_f32_launch(
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
  glass_warp_translation_bilinear_f32_kernel<<<blocks, threads>>>(
      input, output, coverage, width, height, dx, dy, fill);
}

__global__ void glass_warp_matrix_bilinear_f32_kernel(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  const int n = width * height;
  if (i >= n) {
    return;
  }
  const int x = i % width;
  const int y = i / width;
  const float fx = static_cast<float>(x);
  const float fy = static_cast<float>(y);
  const float denom = inverse[6] * fx + inverse[7] * fy + inverse[8];
  if (fabsf(denom) <= 1.0e-12f) {
    output[i] = fill;
    coverage[i] = 0.0f;
    return;
  }
  const float sx = (inverse[0] * fx + inverse[1] * fy + inverse[2]) / denom;
  const float sy = (inverse[3] * fx + inverse[4] * fy + inverse[5]) / denom;
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

void glass_warp_matrix_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill) {
  constexpr int threads = 256;
  const int blocks = (width * height + threads - 1) / threads;
  glass_warp_matrix_bilinear_f32_kernel<<<blocks, threads>>>(
      input, output, coverage, inverse, width, height, fill);
}

__device__ float glass_sinc_f32(float x) {
  const float ax = fabsf(x);
  if (ax < 1.0e-6f) {
    return 1.0f;
  }
  const float pix = 3.14159265358979323846f * x;
  return sinf(pix) / pix;
}

__device__ float glass_lanczos3_weight_f32(float x) {
  const float ax = fabsf(x);
  if (ax >= 3.0f) {
    return 0.0f;
  }
  return glass_sinc_f32(x) * glass_sinc_f32(x / 3.0f);
}

__global__ void glass_warp_matrix_lanczos3_f32_kernel(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill,
    float clamping_threshold) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  const int n = width * height;
  if (i >= n) {
    return;
  }
  const int x = i % width;
  const int y = i / width;
  const float fx = static_cast<float>(x);
  const float fy = static_cast<float>(y);
  const float denom = inverse[6] * fx + inverse[7] * fy + inverse[8];
  if (fabsf(denom) <= 1.0e-12f) {
    output[i] = fill;
    coverage[i] = 0.0f;
    return;
  }

  const float sx = (inverse[0] * fx + inverse[1] * fy + inverse[2]) / denom;
  const float sy = (inverse[3] * fx + inverse[4] * fy + inverse[5]) / denom;
  if (sx < 2.0f || sx >= static_cast<float>(width - 3) ||
      sy < 2.0f || sy >= static_cast<float>(height - 3)) {
    output[i] = fill;
    coverage[i] = 0.0f;
    return;
  }

  const int x0 = static_cast<int>(floorf(sx));
  const int y0 = static_cast<int>(floorf(sy));
  float wx[6];
  float wy[6];
  for (int k = 0; k < 6; ++k) {
    wx[k] = glass_lanczos3_weight_f32(sx - static_cast<float>(x0 - 2 + k));
    wy[k] = glass_lanczos3_weight_f32(sy - static_cast<float>(y0 - 2 + k));
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
    output[i] = fill;
    coverage[i] = 0.0f;
    return;
  }
  float value = weighted_sum / weight_sum;
  if (clamping_threshold >= 0.0f && local_max >= local_min) {
    const float range = local_max - local_min;
    const float lo = local_min - clamping_threshold * range;
    const float hi = local_max + clamping_threshold * range;
    value = fminf(hi, fmaxf(lo, value));
  }
  output[i] = value;
  coverage[i] = 1.0f;
}

void glass_warp_matrix_lanczos3_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill,
    float clamping_threshold) {
  constexpr int threads = 256;
  const int blocks = (width * height + threads - 1) / threads;
  glass_warp_matrix_lanczos3_f32_kernel<<<blocks, threads>>>(
      input, output, coverage, inverse, width, height, fill, clamping_threshold);
}

__global__ void glass_matrix_alignment_metrics_f32_kernel(
    const float* reference,
    const float* moving,
    const float* inverse,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride) {
  extern __shared__ unsigned char raw_scratch[];
  auto* scratch = reinterpret_cast<double*>(raw_scratch);
  double* sum_ref = scratch;
  double* sum_mov = scratch + blockDim.x;
  double* sum_ref2 = scratch + 2 * blockDim.x;
  double* sum_mov2 = scratch + 3 * blockDim.x;
  double* sum_cross = scratch + 4 * blockDim.x;
  double* sum_diff2 = scratch + 5 * blockDim.x;
  double* sum_abs_diff = scratch + 6 * blockDim.x;
  auto* count = reinterpret_cast<unsigned long long*>(scratch + 7 * blockDim.x);

  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sample_count = sample_width * sample_height;

  double local_ref = 0.0;
  double local_mov = 0.0;
  double local_ref2 = 0.0;
  double local_mov2 = 0.0;
  double local_cross = 0.0;
  double local_diff2 = 0.0;
  double local_abs_diff = 0.0;
  unsigned long long local_count = 0;

  for (int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
       i < sample_count;
       i += static_cast<int>(gridDim.x * blockDim.x)) {
    const int x = (i % sample_width) * stride;
    const int y = (i / sample_width) * stride;
    const float fx = static_cast<float>(x);
    const float fy = static_cast<float>(y);
    const float denom = inverse[6] * fx + inverse[7] * fy + inverse[8];
    if (fabsf(denom) <= 1.0e-12f) {
      continue;
    }
    const float sx = (inverse[0] * fx + inverse[1] * fy + inverse[2]) / denom;
    const float sy = (inverse[3] * fx + inverse[4] * fy + inverse[5]) / denom;
    if (sx < 0.0f || sx > static_cast<float>(width - 1) ||
        sy < 0.0f || sy > static_cast<float>(height - 1)) {
      continue;
    }
    const int x0 = static_cast<int>(floorf(sx));
    const int y0 = static_cast<int>(floorf(sy));
    const int x1 = x0 + 1 < width ? x0 + 1 : x0;
    const int y1 = y0 + 1 < height ? y0 + 1 : y0;
    const float tx = sx - static_cast<float>(x0);
    const float ty = sy - static_cast<float>(y0);
    const float v00 = moving[y0 * width + x0];
    const float v10 = moving[y0 * width + x1];
    const float v01 = moving[y1 * width + x0];
    const float v11 = moving[y1 * width + x1];
    const float top = v00 * (1.0f - tx) + v10 * tx;
    const float bottom = v01 * (1.0f - tx) + v11 * tx;
    const float warped = top * (1.0f - ty) + bottom * ty;
    const float ref_value = reference[y * width + x];
    if (!isfinite(ref_value) || !isfinite(warped)) {
      continue;
    }
    const double r = static_cast<double>(ref_value);
    const double m = static_cast<double>(warped);
    const double diff = m - r;
    local_ref += r;
    local_mov += m;
    local_ref2 += r * r;
    local_mov2 += m * m;
    local_cross += r * m;
    local_diff2 += diff * diff;
    local_abs_diff += fabs(diff);
    local_count += 1ULL;
  }

  const int lane = static_cast<int>(threadIdx.x);
  sum_ref[lane] = local_ref;
  sum_mov[lane] = local_mov;
  sum_ref2[lane] = local_ref2;
  sum_mov2[lane] = local_mov2;
  sum_cross[lane] = local_cross;
  sum_diff2[lane] = local_diff2;
  sum_abs_diff[lane] = local_abs_diff;
  count[lane] = local_count;
  __syncthreads();

  for (int reduce_stride = static_cast<int>(blockDim.x) / 2; reduce_stride > 0; reduce_stride >>= 1) {
    if (lane < reduce_stride) {
      sum_ref[lane] += sum_ref[lane + reduce_stride];
      sum_mov[lane] += sum_mov[lane + reduce_stride];
      sum_ref2[lane] += sum_ref2[lane + reduce_stride];
      sum_mov2[lane] += sum_mov2[lane + reduce_stride];
      sum_cross[lane] += sum_cross[lane + reduce_stride];
      sum_diff2[lane] += sum_diff2[lane + reduce_stride];
      sum_abs_diff[lane] += sum_abs_diff[lane + reduce_stride];
      count[lane] += count[lane + reduce_stride];
    }
    __syncthreads();
  }

  if (lane == 0) {
    const int offset = static_cast<int>(blockIdx.x) * 7;
    partial_stats[offset + 0] = sum_ref[0];
    partial_stats[offset + 1] = sum_mov[0];
    partial_stats[offset + 2] = sum_ref2[0];
    partial_stats[offset + 3] = sum_mov2[0];
    partial_stats[offset + 4] = sum_cross[0];
    partial_stats[offset + 5] = sum_diff2[0];
    partial_stats[offset + 6] = sum_abs_diff[0];
    partial_count[blockIdx.x] = count[0];
  }
}

void glass_matrix_alignment_metrics_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverse,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int blocks) {
  constexpr int threads = 256;
  const std::size_t shared_bytes = 7 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  glass_matrix_alignment_metrics_f32_kernel<<<blocks, threads, shared_bytes>>>(
      reference, moving, inverse, partial_stats, partial_count, width, height, sample_stride);
}

__global__ void glass_matrix_alignment_metrics_candidates_f32_kernel(
    const float* reference,
    const float* moving,
    const float* inverses,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int candidate_count) {
  extern __shared__ unsigned char raw_scratch[];
  auto* scratch = reinterpret_cast<double*>(raw_scratch);
  double* sum_ref = scratch;
  double* sum_mov = scratch + blockDim.x;
  double* sum_ref2 = scratch + 2 * blockDim.x;
  double* sum_mov2 = scratch + 3 * blockDim.x;
  double* sum_cross = scratch + 4 * blockDim.x;
  double* sum_diff2 = scratch + 5 * blockDim.x;
  double* sum_abs_diff = scratch + 6 * blockDim.x;
  auto* count = reinterpret_cast<unsigned long long*>(scratch + 7 * blockDim.x);

  const int candidate = static_cast<int>(blockIdx.x);
  if (candidate >= candidate_count) {
    return;
  }
  const float* inverse = inverses + candidate * 9;
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sample_count = sample_width * sample_height;

  double local_ref = 0.0;
  double local_mov = 0.0;
  double local_ref2 = 0.0;
  double local_mov2 = 0.0;
  double local_cross = 0.0;
  double local_diff2 = 0.0;
  double local_abs_diff = 0.0;
  unsigned long long local_count = 0;

  for (int i = static_cast<int>(threadIdx.x); i < sample_count; i += static_cast<int>(blockDim.x)) {
    const int x = (i % sample_width) * stride;
    const int y = (i / sample_width) * stride;
    const float fx = static_cast<float>(x);
    const float fy = static_cast<float>(y);
    const float denom = inverse[6] * fx + inverse[7] * fy + inverse[8];
    if (fabsf(denom) <= 1.0e-12f) {
      continue;
    }
    const float sx = (inverse[0] * fx + inverse[1] * fy + inverse[2]) / denom;
    const float sy = (inverse[3] * fx + inverse[4] * fy + inverse[5]) / denom;
    if (sx < 0.0f || sx > static_cast<float>(width - 1) ||
        sy < 0.0f || sy > static_cast<float>(height - 1)) {
      continue;
    }
    const int x0 = static_cast<int>(floorf(sx));
    const int y0 = static_cast<int>(floorf(sy));
    const int x1 = x0 + 1 < width ? x0 + 1 : x0;
    const int y1 = y0 + 1 < height ? y0 + 1 : y0;
    const float tx = sx - static_cast<float>(x0);
    const float ty = sy - static_cast<float>(y0);
    const float v00 = moving[y0 * width + x0];
    const float v10 = moving[y0 * width + x1];
    const float v01 = moving[y1 * width + x0];
    const float v11 = moving[y1 * width + x1];
    const float top = v00 * (1.0f - tx) + v10 * tx;
    const float bottom = v01 * (1.0f - tx) + v11 * tx;
    const float warped = top * (1.0f - ty) + bottom * ty;
    const float ref_value = reference[y * width + x];
    if (!isfinite(ref_value) || !isfinite(warped)) {
      continue;
    }
    const double r = static_cast<double>(ref_value);
    const double m = static_cast<double>(warped);
    const double diff = m - r;
    local_ref += r;
    local_mov += m;
    local_ref2 += r * r;
    local_mov2 += m * m;
    local_cross += r * m;
    local_diff2 += diff * diff;
    local_abs_diff += fabs(diff);
    local_count += 1ULL;
  }

  const int lane = static_cast<int>(threadIdx.x);
  sum_ref[lane] = local_ref;
  sum_mov[lane] = local_mov;
  sum_ref2[lane] = local_ref2;
  sum_mov2[lane] = local_mov2;
  sum_cross[lane] = local_cross;
  sum_diff2[lane] = local_diff2;
  sum_abs_diff[lane] = local_abs_diff;
  count[lane] = local_count;
  __syncthreads();

  for (int reduce_stride = static_cast<int>(blockDim.x) / 2; reduce_stride > 0; reduce_stride >>= 1) {
    if (lane < reduce_stride) {
      sum_ref[lane] += sum_ref[lane + reduce_stride];
      sum_mov[lane] += sum_mov[lane + reduce_stride];
      sum_ref2[lane] += sum_ref2[lane + reduce_stride];
      sum_mov2[lane] += sum_mov2[lane + reduce_stride];
      sum_cross[lane] += sum_cross[lane + reduce_stride];
      sum_diff2[lane] += sum_diff2[lane + reduce_stride];
      sum_abs_diff[lane] += sum_abs_diff[lane + reduce_stride];
      count[lane] += count[lane + reduce_stride];
    }
    __syncthreads();
  }

  if (lane == 0) {
    const int offset = candidate * 7;
    partial_stats[offset + 0] = sum_ref[0];
    partial_stats[offset + 1] = sum_mov[0];
    partial_stats[offset + 2] = sum_ref2[0];
    partial_stats[offset + 3] = sum_mov2[0];
    partial_stats[offset + 4] = sum_cross[0];
    partial_stats[offset + 5] = sum_diff2[0];
    partial_stats[offset + 6] = sum_abs_diff[0];
    partial_count[candidate] = count[0];
  }
}

void glass_matrix_alignment_metrics_candidates_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverses,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int candidate_count) {
  constexpr int threads = 256;
  const std::size_t shared_bytes = 7 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  glass_matrix_alignment_metrics_candidates_f32_kernel<<<candidate_count, threads, shared_bytes>>>(
      reference,
      moving,
      inverses,
      partial_stats,
      partial_count,
      width,
      height,
      sample_stride,
      candidate_count);
}

__global__ void glass_star_core_metrics_candidates_f32_kernel(
    const float* reference,
    const float* moving,
    const float* inverses,
    float threshold,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int candidate_count) {
  extern __shared__ unsigned char raw_scratch[];
  auto* scratch = reinterpret_cast<double*>(raw_scratch);
  double* sum_ref = scratch;
  double* sum_mov = scratch + blockDim.x;
  double* sum_ref2 = scratch + 2 * blockDim.x;
  double* sum_mov2 = scratch + 3 * blockDim.x;
  double* sum_cross = scratch + 4 * blockDim.x;
  double* sum_diff2 = scratch + 5 * blockDim.x;
  double* sum_abs_diff = scratch + 6 * blockDim.x;
  auto* count = reinterpret_cast<unsigned long long*>(scratch + 7 * blockDim.x);

  const int candidate = static_cast<int>(blockIdx.x);
  if (candidate >= candidate_count) {
    return;
  }
  const float* inverse = inverses + candidate * 9;
  const int pixel_count = width * height;

  double local_ref = 0.0;
  double local_mov = 0.0;
  double local_ref2 = 0.0;
  double local_mov2 = 0.0;
  double local_cross = 0.0;
  double local_diff2 = 0.0;
  double local_abs_diff = 0.0;
  unsigned long long local_count = 0;

  for (int i = static_cast<int>(threadIdx.x); i < pixel_count; i += static_cast<int>(blockDim.x)) {
    const float ref_value = reference[i];
    if (!isfinite(ref_value) || ref_value <= threshold) {
      continue;
    }
    const int x = i % width;
    const int y = i / width;
    const float fx = static_cast<float>(x);
    const float fy = static_cast<float>(y);
    const float denom = inverse[6] * fx + inverse[7] * fy + inverse[8];
    if (fabsf(denom) <= 1.0e-12f) {
      continue;
    }
    const float sx = (inverse[0] * fx + inverse[1] * fy + inverse[2]) / denom;
    const float sy = (inverse[3] * fx + inverse[4] * fy + inverse[5]) / denom;
    if (sx < 0.0f || sx > static_cast<float>(width - 1) ||
        sy < 0.0f || sy > static_cast<float>(height - 1)) {
      continue;
    }
    const int x0 = static_cast<int>(floorf(sx));
    const int y0 = static_cast<int>(floorf(sy));
    const int x1 = x0 + 1 < width ? x0 + 1 : x0;
    const int y1 = y0 + 1 < height ? y0 + 1 : y0;
    const float tx = sx - static_cast<float>(x0);
    const float ty = sy - static_cast<float>(y0);
    const float v00 = moving[y0 * width + x0];
    const float v10 = moving[y0 * width + x1];
    const float v01 = moving[y1 * width + x0];
    const float v11 = moving[y1 * width + x1];
    const float top = v00 * (1.0f - tx) + v10 * tx;
    const float bottom = v01 * (1.0f - tx) + v11 * tx;
    const float warped = top * (1.0f - ty) + bottom * ty;
    if (!isfinite(warped)) {
      continue;
    }
    const double r = static_cast<double>(ref_value);
    const double m = static_cast<double>(warped);
    const double diff = m - r;
    local_ref += r;
    local_mov += m;
    local_ref2 += r * r;
    local_mov2 += m * m;
    local_cross += r * m;
    local_diff2 += diff * diff;
    local_abs_diff += fabs(diff);
    local_count += 1ULL;
  }

  const int lane = static_cast<int>(threadIdx.x);
  sum_ref[lane] = local_ref;
  sum_mov[lane] = local_mov;
  sum_ref2[lane] = local_ref2;
  sum_mov2[lane] = local_mov2;
  sum_cross[lane] = local_cross;
  sum_diff2[lane] = local_diff2;
  sum_abs_diff[lane] = local_abs_diff;
  count[lane] = local_count;
  __syncthreads();

  for (int reduce_stride = static_cast<int>(blockDim.x) / 2; reduce_stride > 0; reduce_stride >>= 1) {
    if (lane < reduce_stride) {
      sum_ref[lane] += sum_ref[lane + reduce_stride];
      sum_mov[lane] += sum_mov[lane + reduce_stride];
      sum_ref2[lane] += sum_ref2[lane + reduce_stride];
      sum_mov2[lane] += sum_mov2[lane + reduce_stride];
      sum_cross[lane] += sum_cross[lane + reduce_stride];
      sum_diff2[lane] += sum_diff2[lane + reduce_stride];
      sum_abs_diff[lane] += sum_abs_diff[lane + reduce_stride];
      count[lane] += count[lane + reduce_stride];
    }
    __syncthreads();
  }

  if (lane == 0) {
    const int offset = candidate * 7;
    partial_stats[offset + 0] = sum_ref[0];
    partial_stats[offset + 1] = sum_mov[0];
    partial_stats[offset + 2] = sum_ref2[0];
    partial_stats[offset + 3] = sum_mov2[0];
    partial_stats[offset + 4] = sum_cross[0];
    partial_stats[offset + 5] = sum_diff2[0];
    partial_stats[offset + 6] = sum_abs_diff[0];
    partial_count[candidate] = count[0];
  }
}

void glass_star_core_metrics_candidates_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverses,
    float threshold,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int candidate_count) {
  constexpr int threads = 256;
  const std::size_t shared_bytes = 7 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  glass_star_core_metrics_candidates_f32_kernel<<<candidate_count, threads, shared_bytes>>>(
      reference,
      moving,
      inverses,
      threshold,
      partial_stats,
      partial_count,
      width,
      height,
      candidate_count);
}
