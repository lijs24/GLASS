#include "common.cuh"

#include <cuda_runtime.h>

#include <cstddef>
#include <math.h>

namespace {

__global__ void translation_search_score_kernel(
    const float* reference,
    const float* moving,
    float* scores,
    int width,
    int height,
    int max_shift_x,
    int max_shift_y,
    int sample_stride) {
  extern __shared__ float scratch[];
  float* sum_ref = scratch;
  float* sum_mov = scratch + blockDim.x;
  float* sum_ref2 = scratch + 2 * blockDim.x;
  float* sum_mov2 = scratch + 3 * blockDim.x;
  float* sum_cross = scratch + 4 * blockDim.x;
  float* sum_count = scratch + 5 * blockDim.x;

  const int shift_width = 2 * max_shift_x + 1;
  const int shift_index = static_cast<int>(blockIdx.x);
  const int dx = shift_index % shift_width - max_shift_x;
  const int dy = shift_index / shift_width - max_shift_y;
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int n = sample_width * sample_height;

  float local_ref = 0.0f;
  float local_mov = 0.0f;
  float local_ref2 = 0.0f;
  float local_mov2 = 0.0f;
  float local_cross = 0.0f;
  float local_count = 0.0f;

  for (int i = static_cast<int>(threadIdx.x); i < n; i += static_cast<int>(blockDim.x)) {
    const int x = (i % sample_width) * stride;
    const int y = (i / sample_width) * stride;
    const int pixel = y * width + x;
    const int sx = x - dx;
    const int sy = y - dy;
    if (sx < 0 || sx >= width || sy < 0 || sy >= height) {
      continue;
    }
    const float r = reference[pixel];
    const float m = moving[sy * width + sx];
    if (!isfinite(r) || !isfinite(m)) {
      continue;
    }
    local_ref += r;
    local_mov += m;
    local_ref2 += r * r;
    local_mov2 += m * m;
    local_cross += r * m;
    local_count += 1.0f;
  }

  const int lane = static_cast<int>(threadIdx.x);
  sum_ref[lane] = local_ref;
  sum_mov[lane] = local_mov;
  sum_ref2[lane] = local_ref2;
  sum_mov2[lane] = local_mov2;
  sum_cross[lane] = local_cross;
  sum_count[lane] = local_count;
  __syncthreads();

  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      sum_ref[lane] += sum_ref[lane + stride];
      sum_mov[lane] += sum_mov[lane + stride];
      sum_ref2[lane] += sum_ref2[lane + stride];
      sum_mov2[lane] += sum_mov2[lane + stride];
      sum_cross[lane] += sum_cross[lane + stride];
      sum_count[lane] += sum_count[lane + stride];
    }
    __syncthreads();
  }

  if (lane != 0) {
    return;
  }
  const float count = sum_count[0];
  if (count <= 1.0f) {
    scores[shift_index] = -3.402823466e+38F;
    return;
  }
  const float numerator = sum_cross[0] - (sum_ref[0] * sum_mov[0] / count);
  const float ref_var = fmaxf(sum_ref2[0] - (sum_ref[0] * sum_ref[0] / count), 0.0f);
  const float mov_var = fmaxf(sum_mov2[0] - (sum_mov[0] * sum_mov[0] / count), 0.0f);
  const float denominator = sqrtf(ref_var * mov_var);
  scores[shift_index] = denominator > 0.0f ? numerator / denominator : -3.402823466e+38F;
}

__global__ void translation_search_best_kernel(
    const float* scores,
    int* best_dx,
    int* best_dy,
    float* best_score,
    int max_shift_x,
    int max_shift_y,
    int shift_count) {
  if (threadIdx.x != 0 || blockIdx.x != 0) {
    return;
  }
  int best_index = 0;
  float best = scores[0];
  for (int i = 1; i < shift_count; ++i) {
    const float score = scores[i];
    if (score > best) {
      best = score;
      best_index = i;
    }
  }
  const int shift_width = 2 * max_shift_x + 1;
  *best_dx = best_index % shift_width - max_shift_x;
  *best_dy = best_index / shift_width - max_shift_y;
  *best_score = best;
}

__global__ void translation_subpixel_score_kernel(
    const float* reference,
    const float* moving,
    float* scores,
    int width,
    int height,
    float center_dx,
    float center_dy,
    int radius_steps,
    float step,
    int sample_stride) {
  extern __shared__ float scratch[];
  float* sum_ref = scratch;
  float* sum_mov = scratch + blockDim.x;
  float* sum_ref2 = scratch + 2 * blockDim.x;
  float* sum_mov2 = scratch + 3 * blockDim.x;
  float* sum_cross = scratch + 4 * blockDim.x;
  float* sum_count = scratch + 5 * blockDim.x;

  const int candidate_width = 2 * radius_steps + 1;
  const int candidate_index = static_cast<int>(blockIdx.x);
  const int offset_x = candidate_index % candidate_width - radius_steps;
  const int offset_y = candidate_index / candidate_width - radius_steps;
  const float dx = center_dx + static_cast<float>(offset_x) * step;
  const float dy = center_dy + static_cast<float>(offset_y) * step;
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int n = sample_width * sample_height;

  float local_ref = 0.0f;
  float local_mov = 0.0f;
  float local_ref2 = 0.0f;
  float local_mov2 = 0.0f;
  float local_cross = 0.0f;
  float local_count = 0.0f;

  for (int i = static_cast<int>(threadIdx.x); i < n; i += static_cast<int>(blockDim.x)) {
    const int x = (i % sample_width) * stride;
    const int y = (i / sample_width) * stride;
    const int pixel = y * width + x;
    const float sx = static_cast<float>(x) - dx;
    const float sy = static_cast<float>(y) - dy;
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
    const float m = top * (1.0f - ty) + bottom * ty;
    const float r = reference[pixel];
    if (!isfinite(r) || !isfinite(m)) {
      continue;
    }
    local_ref += r;
    local_mov += m;
    local_ref2 += r * r;
    local_mov2 += m * m;
    local_cross += r * m;
    local_count += 1.0f;
  }

  const int lane = static_cast<int>(threadIdx.x);
  sum_ref[lane] = local_ref;
  sum_mov[lane] = local_mov;
  sum_ref2[lane] = local_ref2;
  sum_mov2[lane] = local_mov2;
  sum_cross[lane] = local_cross;
  sum_count[lane] = local_count;
  __syncthreads();

  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      sum_ref[lane] += sum_ref[lane + stride];
      sum_mov[lane] += sum_mov[lane + stride];
      sum_ref2[lane] += sum_ref2[lane + stride];
      sum_mov2[lane] += sum_mov2[lane + stride];
      sum_cross[lane] += sum_cross[lane + stride];
      sum_count[lane] += sum_count[lane + stride];
    }
    __syncthreads();
  }

  if (lane != 0) {
    return;
  }
  const float count = sum_count[0];
  if (count <= 1.0f) {
    scores[candidate_index] = -3.402823466e+38F;
    return;
  }
  const float numerator = sum_cross[0] - (sum_ref[0] * sum_mov[0] / count);
  const float ref_var = fmaxf(sum_ref2[0] - (sum_ref[0] * sum_ref[0] / count), 0.0f);
  const float mov_var = fmaxf(sum_mov2[0] - (sum_mov[0] * sum_mov[0] / count), 0.0f);
  const float denominator = sqrtf(ref_var * mov_var);
  scores[candidate_index] = denominator > 0.0f ? numerator / denominator : -3.402823466e+38F;
}

__global__ void translation_subpixel_best_kernel(
    const float* scores,
    float* best_dx,
    float* best_dy,
    float* best_score,
    float center_dx,
    float center_dy,
    int radius_steps,
    float step,
    int candidate_count) {
  if (threadIdx.x != 0 || blockIdx.x != 0) {
    return;
  }
  int best_index = 0;
  float best = scores[0];
  for (int i = 1; i < candidate_count; ++i) {
    const float score = scores[i];
    if (score > best) {
      best = score;
      best_index = i;
    }
  }
  const int candidate_width = 2 * radius_steps + 1;
  const int offset_x = best_index % candidate_width - radius_steps;
  const int offset_y = best_index / candidate_width - radius_steps;
  *best_dx = center_dx + static_cast<float>(offset_x) * step;
  *best_dy = center_dy + static_cast<float>(offset_y) * step;
  *best_score = best;
}

__global__ void catalog_pair_offsets_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_dx,
    float* candidate_dy,
    int reference_count,
    int moving_count,
    int pair_count,
    float max_abs_dx,
    float max_abs_dy,
    float prior_dx,
    float prior_dy,
    float prior_radius_px) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= pair_count) {
    return;
  }
  const int reference_index = i / moving_count;
  const int moving_index = i % moving_count;
  const float dx = reference_x[reference_index] - moving_x[moving_index];
  const float dy = reference_y[reference_index] - moving_y[moving_index];
  if ((max_abs_dx >= 0.0f && fabsf(dx) > max_abs_dx) ||
      (max_abs_dy >= 0.0f && fabsf(dy) > max_abs_dy)) {
    candidate_dx[i] = NAN;
    candidate_dy[i] = NAN;
    return;
  }
  if (prior_radius_px >= 0.0f) {
    const float ddx = dx - prior_dx;
    const float ddy = dy - prior_dy;
    if (ddx * ddx + ddy * ddy > prior_radius_px * prior_radius_px) {
      candidate_dx[i] = NAN;
      candidate_dy[i] = NAN;
      return;
    }
  }
  candidate_dx[i] = dx;
  candidate_dy[i] = dy;
}

__global__ void catalog_offset_score_kernel(
    const float* candidate_dx,
    const float* candidate_dy,
    int* scores,
    int pair_count,
    float tolerance_px) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= pair_count) {
    return;
  }
  const float dx = candidate_dx[i];
  const float dy = candidate_dy[i];
  if (!isfinite(dx) || !isfinite(dy)) {
    scores[i] = -1;
    return;
  }
  const float tolerance2 = tolerance_px * tolerance_px;
  int score = 0;
  for (int j = 0; j < pair_count; ++j) {
    if (!isfinite(candidate_dx[j]) || !isfinite(candidate_dy[j])) {
      continue;
    }
    const float ddx = candidate_dx[j] - dx;
    const float ddy = candidate_dy[j] - dy;
    if (ddx * ddx + ddy * ddy <= tolerance2) {
      ++score;
    }
  }
  scores[i] = score;
}

__global__ void catalog_offset_best_kernel(
    const float* candidate_dx,
    const float* candidate_dy,
    const int* scores,
    float* best_dx,
    float* best_dy,
    int* best_inliers,
    int pair_count) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  int best_index = -1;
  int best_score = -1;
  for (int i = 0; i < pair_count; ++i) {
    const int score = scores[i];
    if (score > best_score) {
      best_score = score;
      best_index = i;
    }
  }
  if (best_index < 0 || best_score < 0) {
    *best_dx = NAN;
    *best_dy = NAN;
    *best_inliers = 0;
    return;
  }
  *best_dx = candidate_dx[best_index];
  *best_dy = candidate_dy[best_index];
  *best_inliers = best_score;
}

__global__ void catalog_moving_best_reference_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const float* best_dx,
    const float* best_dy,
    int* moving_best_reference,
    int reference_count,
    int moving_count,
    float tolerance_px) {
  const int moving_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (moving_index >= moving_count) {
    return;
  }
  const float transformed_x = moving_x[moving_index] + *best_dx;
  const float transformed_y = moving_y[moving_index] + *best_dy;
  const float tolerance2 = tolerance_px * tolerance_px;
  float best_distance2 = tolerance2;
  int best_reference = -1;
  for (int reference_index = 0; reference_index < reference_count; ++reference_index) {
    const float dx = reference_x[reference_index] - transformed_x;
    const float dy = reference_y[reference_index] - transformed_y;
    const float distance2 = dx * dx + dy * dy;
    if (distance2 <= best_distance2) {
      best_distance2 = distance2;
      best_reference = reference_index;
    }
  }
  moving_best_reference[moving_index] = best_reference;
}

__global__ void catalog_reference_best_moving_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const float* best_dx,
    const float* best_dy,
    int* reference_best_moving,
    int reference_count,
    int moving_count,
    float tolerance_px) {
  const int reference_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (reference_index >= reference_count) {
    return;
  }
  const float tolerance2 = tolerance_px * tolerance_px;
  float best_distance2 = tolerance2;
  int best_moving = -1;
  for (int moving_index = 0; moving_index < moving_count; ++moving_index) {
    const float transformed_x = moving_x[moving_index] + *best_dx;
    const float transformed_y = moving_y[moving_index] + *best_dy;
    const float dx = reference_x[reference_index] - transformed_x;
    const float dy = reference_y[reference_index] - transformed_y;
    const float distance2 = dx * dx + dy * dy;
    if (distance2 <= best_distance2) {
      best_distance2 = distance2;
      best_moving = moving_index;
    }
  }
  reference_best_moving[reference_index] = best_moving;
}

__global__ void catalog_mutual_refine_sums_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const int* moving_best_reference,
    const int* reference_best_moving,
    float* sums,
    int* mutual_inliers,
    int moving_count) {
  const int moving_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (moving_index >= moving_count) {
    return;
  }
  const int reference_index = moving_best_reference[moving_index];
  if (reference_index < 0 || reference_best_moving[reference_index] != moving_index) {
    return;
  }
  atomicAdd(sums + 0, reference_x[reference_index] - moving_x[moving_index]);
  atomicAdd(sums + 1, reference_y[reference_index] - moving_y[moving_index]);
  atomicAdd(mutual_inliers, 1);
}

__global__ void catalog_finalize_refinement_kernel(
    const float* best_dx,
    const float* best_dy,
    const float* sums,
    const int* mutual_inliers,
    float* refined_dx,
    float* refined_dy) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  const int count = *mutual_inliers;
  if (count <= 0) {
    *refined_dx = *best_dx;
    *refined_dy = *best_dy;
    return;
  }
  const float scale = 1.0f / static_cast<float>(count);
  *refined_dx = sums[0] * scale;
  *refined_dy = sums[1] * scale;
}

__global__ void catalog_mutual_rms_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const int* moving_best_reference,
    const int* reference_best_moving,
    const float* refined_dx,
    const float* refined_dy,
    float* sums,
    int moving_count) {
  const int moving_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (moving_index >= moving_count) {
    return;
  }
  const int reference_index = moving_best_reference[moving_index];
  if (reference_index < 0 || reference_best_moving[reference_index] != moving_index) {
    return;
  }
  const float dx = reference_x[reference_index] - (moving_x[moving_index] + *refined_dx);
  const float dy = reference_y[reference_index] - (moving_y[moving_index] + *refined_dy);
  atomicAdd(sums + 2, dx * dx + dy * dy);
}

__global__ void catalog_finalize_rms_kernel(
    const float* sums,
    const int* mutual_inliers,
    float* rms_px) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  const int count = *mutual_inliers;
  *rms_px = count > 0 ? sqrtf(sums[2] / static_cast<float>(count)) : NAN;
}

__global__ void similarity_pair_stats_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    double* partial_sums,
    unsigned long long* partial_count,
    int count) {
  extern __shared__ unsigned char similarity_scratch[];
  double* sum_mx = reinterpret_cast<double*>(similarity_scratch);
  double* sum_my = sum_mx + blockDim.x;
  double* sum_rx = sum_my + blockDim.x;
  double* sum_ry = sum_rx + blockDim.x;
  double* sum_moving_power = sum_ry + blockDim.x;
  double* sum_dot_same = sum_moving_power + blockDim.x;
  double* sum_dot_cross = sum_dot_same + blockDim.x;
  unsigned long long* valid_counts = reinterpret_cast<unsigned long long*>(sum_dot_cross + blockDim.x);

  const int lane = static_cast<int>(threadIdx.x);
  double local_mx = 0.0;
  double local_my = 0.0;
  double local_rx = 0.0;
  double local_ry = 0.0;
  double local_moving_power = 0.0;
  double local_dot_same = 0.0;
  double local_dot_cross = 0.0;
  unsigned long long local_count = 0;

  for (int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
       i < count;
       i += static_cast<int>(gridDim.x * blockDim.x)) {
    const float mx_f = moving_x[i];
    const float my_f = moving_y[i];
    const float rx_f = reference_x[i];
    const float ry_f = reference_y[i];
    if (!isfinite(mx_f) || !isfinite(my_f) || !isfinite(rx_f) || !isfinite(ry_f)) {
      continue;
    }
    const double mx = static_cast<double>(mx_f);
    const double my = static_cast<double>(my_f);
    const double rx = static_cast<double>(rx_f);
    const double ry = static_cast<double>(ry_f);
    local_mx += mx;
    local_my += my;
    local_rx += rx;
    local_ry += ry;
    local_moving_power += mx * mx + my * my;
    local_dot_same += mx * rx + my * ry;
    local_dot_cross += mx * ry - my * rx;
    ++local_count;
  }

  sum_mx[lane] = local_mx;
  sum_my[lane] = local_my;
  sum_rx[lane] = local_rx;
  sum_ry[lane] = local_ry;
  sum_moving_power[lane] = local_moving_power;
  sum_dot_same[lane] = local_dot_same;
  sum_dot_cross[lane] = local_dot_cross;
  valid_counts[lane] = local_count;
  __syncthreads();

  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      sum_mx[lane] += sum_mx[lane + stride];
      sum_my[lane] += sum_my[lane + stride];
      sum_rx[lane] += sum_rx[lane + stride];
      sum_ry[lane] += sum_ry[lane + stride];
      sum_moving_power[lane] += sum_moving_power[lane + stride];
      sum_dot_same[lane] += sum_dot_same[lane + stride];
      sum_dot_cross[lane] += sum_dot_cross[lane + stride];
      valid_counts[lane] += valid_counts[lane + stride];
    }
    __syncthreads();
  }

  if (lane == 0) {
    const int offset = static_cast<int>(blockIdx.x) * 7;
    partial_sums[offset + 0] = sum_mx[0];
    partial_sums[offset + 1] = sum_my[0];
    partial_sums[offset + 2] = sum_rx[0];
    partial_sums[offset + 3] = sum_ry[0];
    partial_sums[offset + 4] = sum_moving_power[0];
    partial_sums[offset + 5] = sum_dot_same[0];
    partial_sums[offset + 6] = sum_dot_cross[0];
    partial_count[blockIdx.x] = valid_counts[0];
  }
}

__global__ void similarity_finalize_matrix_kernel(
    const double* partial_sums,
    const unsigned long long* partial_count,
    float* matrix,
    float* scale,
    float* rotation_rad,
    int* valid_count,
    int* status,
    int blocks) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  double sum_mx = 0.0;
  double sum_my = 0.0;
  double sum_rx = 0.0;
  double sum_ry = 0.0;
  double sum_moving_power = 0.0;
  double sum_dot_same = 0.0;
  double sum_dot_cross = 0.0;
  unsigned long long count = 0;
  for (int block = 0; block < blocks; ++block) {
    const int offset = block * 7;
    sum_mx += partial_sums[offset + 0];
    sum_my += partial_sums[offset + 1];
    sum_rx += partial_sums[offset + 2];
    sum_ry += partial_sums[offset + 3];
    sum_moving_power += partial_sums[offset + 4];
    sum_dot_same += partial_sums[offset + 5];
    sum_dot_cross += partial_sums[offset + 6];
    count += partial_count[block];
  }
  *valid_count = static_cast<int>(count);
  matrix[0] = 1.0f;
  matrix[1] = 0.0f;
  matrix[2] = 0.0f;
  matrix[3] = 0.0f;
  matrix[4] = 1.0f;
  matrix[5] = 0.0f;
  matrix[6] = 0.0f;
  matrix[7] = 0.0f;
  matrix[8] = 1.0f;
  *scale = 1.0f;
  *rotation_rad = 0.0f;
  if (count < 2ULL) {
    *status = 1;
    return;
  }

  const double n = static_cast<double>(count);
  const double mean_mx = sum_mx / n;
  const double mean_my = sum_my / n;
  const double mean_rx = sum_rx / n;
  const double mean_ry = sum_ry / n;
  const double denominator = sum_moving_power - n * (mean_mx * mean_mx + mean_my * mean_my);
  if (denominator <= 1.0e-20) {
    *status = 2;
    return;
  }
  const double numer_a = sum_dot_same - n * (mean_mx * mean_rx + mean_my * mean_ry);
  const double numer_b = sum_dot_cross - n * (mean_mx * mean_ry - mean_my * mean_rx);
  const double a = numer_a / denominator;
  const double b = numer_b / denominator;
  const double tx = mean_rx - (a * mean_mx - b * mean_my);
  const double ty = mean_ry - (b * mean_mx + a * mean_my);

  matrix[0] = static_cast<float>(a);
  matrix[1] = static_cast<float>(-b);
  matrix[2] = static_cast<float>(tx);
  matrix[3] = static_cast<float>(b);
  matrix[4] = static_cast<float>(a);
  matrix[5] = static_cast<float>(ty);
  *scale = static_cast<float>(sqrt(a * a + b * b));
  *rotation_rad = static_cast<float>(atan2(b, a));
  *status = 0;
}

__global__ void similarity_residual_sums_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const float* matrix,
    const int* status,
    double* partial_residual_sums,
    int count) {
  extern __shared__ double residual_sums[];
  const int lane = static_cast<int>(threadIdx.x);
  double local_sum = 0.0;
  if (*status == 0) {
    const double m00 = static_cast<double>(matrix[0]);
    const double m01 = static_cast<double>(matrix[1]);
    const double m02 = static_cast<double>(matrix[2]);
    const double m10 = static_cast<double>(matrix[3]);
    const double m11 = static_cast<double>(matrix[4]);
    const double m12 = static_cast<double>(matrix[5]);
    for (int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
         i < count;
         i += static_cast<int>(gridDim.x * blockDim.x)) {
      const float mx_f = moving_x[i];
      const float my_f = moving_y[i];
      const float rx_f = reference_x[i];
      const float ry_f = reference_y[i];
      if (!isfinite(mx_f) || !isfinite(my_f) || !isfinite(rx_f) || !isfinite(ry_f)) {
        continue;
      }
      const double mx = static_cast<double>(mx_f);
      const double my = static_cast<double>(my_f);
      const double dx = (m00 * mx + m01 * my + m02) - static_cast<double>(rx_f);
      const double dy = (m10 * mx + m11 * my + m12) - static_cast<double>(ry_f);
      local_sum += dx * dx + dy * dy;
    }
  }
  residual_sums[lane] = local_sum;
  __syncthreads();
  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      residual_sums[lane] += residual_sums[lane + stride];
    }
    __syncthreads();
  }
  if (lane == 0) {
    partial_residual_sums[blockIdx.x] = residual_sums[0];
  }
}

__global__ void similarity_finalize_rms_kernel(
    const double* partial_residual_sums,
    const int* valid_count,
    const int* status,
    float* rms_px,
    int blocks) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  if (*status != 0 || *valid_count <= 0) {
    *rms_px = NAN;
    return;
  }
  double residual_sum = 0.0;
  for (int block = 0; block < blocks; ++block) {
    residual_sum += partial_residual_sums[block];
  }
  *rms_px = static_cast<float>(sqrt(residual_sum / static_cast<double>(*valid_count)));
}

__device__ int ordered_pair_first(int pair_index, int count) {
  return pair_index / (count - 1);
}

__device__ int ordered_pair_second(int pair_index, int count, int first) {
  const int second_offset = pair_index % (count - 1);
  return second_offset >= first ? second_offset + 1 : second_offset;
}

__global__ void catalog_similarity_score_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_params,
    int* candidate_scores,
    float* candidate_rms,
    int reference_count,
    int moving_count,
    int candidate_count,
    float tolerance_px,
    float min_pair_distance,
    float prior_dx,
    float prior_dy,
    float prior_radius_px,
    float min_scale,
    float max_scale,
    float max_abs_rotation_rad) {
  const int candidate_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (candidate_index >= candidate_count) {
    return;
  }
  const int moving_pair_count = moving_count * (moving_count - 1);
  const int reference_pair_index = candidate_index / moving_pair_count;
  const int moving_pair_index = candidate_index % moving_pair_count;
  const int reference_a = ordered_pair_first(reference_pair_index, reference_count);
  const int reference_b = ordered_pair_second(reference_pair_index, reference_count, reference_a);
  const int moving_a = ordered_pair_first(moving_pair_index, moving_count);
  const int moving_b = ordered_pair_second(moving_pair_index, moving_count, moving_a);

  const float rax = reference_x[reference_a];
  const float ray = reference_y[reference_a];
  const float rbx = reference_x[reference_b];
  const float rby = reference_y[reference_b];
  const float max = moving_x[moving_a];
  const float may = moving_y[moving_a];
  const float mbx = moving_x[moving_b];
  const float mby = moving_y[moving_b];
  const int param_offset = candidate_index * 4;
  candidate_params[param_offset + 0] = 1.0f;
  candidate_params[param_offset + 1] = 0.0f;
  candidate_params[param_offset + 2] = 0.0f;
  candidate_params[param_offset + 3] = 0.0f;
  candidate_scores[candidate_index] = -1;
  candidate_rms[candidate_index] = NAN;

  if (!isfinite(rax) || !isfinite(ray) || !isfinite(rbx) || !isfinite(rby) ||
      !isfinite(max) || !isfinite(may) || !isfinite(mbx) || !isfinite(mby)) {
    return;
  }
  const float mvx = mbx - max;
  const float mvy = mby - may;
  const float rvx = rbx - rax;
  const float rvy = rby - ray;
  const float moving_distance2 = mvx * mvx + mvy * mvy;
  const float reference_distance2 = rvx * rvx + rvy * rvy;
  const float min_pair_distance2 = min_pair_distance * min_pair_distance;
  if (moving_distance2 <= min_pair_distance2 || reference_distance2 <= min_pair_distance2) {
    return;
  }

  const float a = (mvx * rvx + mvy * rvy) / moving_distance2;
  const float b = (mvx * rvy - mvy * rvx) / moving_distance2;
  const float tx = rax - (a * max - b * may);
  const float ty = ray - (b * max + a * may);
  const float candidate_scale = sqrtf(a * a + b * b);
  const float candidate_rotation = atan2f(b, a);
  if (candidate_scale < min_scale || candidate_scale > max_scale) {
    return;
  }
  if (max_abs_rotation_rad >= 0.0f && fabsf(candidate_rotation) > max_abs_rotation_rad) {
    return;
  }
  if (prior_radius_px >= 0.0f) {
    const float prior_dx_error = tx - prior_dx;
    const float prior_dy_error = ty - prior_dy;
    if ((prior_dx_error * prior_dx_error + prior_dy_error * prior_dy_error) >
        prior_radius_px * prior_radius_px) {
      return;
    }
  }
  candidate_params[param_offset + 0] = a;
  candidate_params[param_offset + 1] = b;
  candidate_params[param_offset + 2] = tx;
  candidate_params[param_offset + 3] = ty;

  const float tolerance2 = tolerance_px * tolerance_px;
  int inliers = 0;
  float residual_sum = 0.0f;
  for (int moving_index = 0; moving_index < moving_count; ++moving_index) {
    const float mx = moving_x[moving_index];
    const float my = moving_y[moving_index];
    if (!isfinite(mx) || !isfinite(my)) {
      continue;
    }
    const float transformed_x = a * mx - b * my + tx;
    const float transformed_y = b * mx + a * my + ty;
    float best_distance2 = tolerance2;
    int best_reference = -1;
    for (int reference_index = 0; reference_index < reference_count; ++reference_index) {
      const float rx = reference_x[reference_index];
      const float ry = reference_y[reference_index];
      if (!isfinite(rx) || !isfinite(ry)) {
        continue;
      }
      const float dx = transformed_x - rx;
      const float dy = transformed_y - ry;
      const float distance2 = dx * dx + dy * dy;
      if (distance2 <= best_distance2) {
        best_distance2 = distance2;
        best_reference = reference_index;
      }
    }
    if (best_reference < 0) {
      continue;
    }
    const float best_rx = reference_x[best_reference];
    const float best_ry = reference_y[best_reference];
    float reverse_best_distance2 = tolerance2;
    int reverse_best_moving = -1;
    for (int other_moving_index = 0; other_moving_index < moving_count; ++other_moving_index) {
      const float other_mx = moving_x[other_moving_index];
      const float other_my = moving_y[other_moving_index];
      if (!isfinite(other_mx) || !isfinite(other_my)) {
        continue;
      }
      const float other_x = a * other_mx - b * other_my + tx;
      const float other_y = b * other_mx + a * other_my + ty;
      const float rdx = other_x - best_rx;
      const float rdy = other_y - best_ry;
      const float reverse_distance2 = rdx * rdx + rdy * rdy;
      if (reverse_distance2 <= reverse_best_distance2) {
        reverse_best_distance2 = reverse_distance2;
        reverse_best_moving = other_moving_index;
      }
    }
    if (reverse_best_moving == moving_index) {
      ++inliers;
      residual_sum += best_distance2;
    }
  }
  candidate_scores[candidate_index] = inliers;
  candidate_rms[candidate_index] =
      inliers > 0 ? sqrtf(residual_sum / static_cast<float>(inliers)) : NAN;
}

__global__ void catalog_similarity_best_kernel(
    const float* candidate_params,
    const int* candidate_scores,
    const float* candidate_rms,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* best_inliers,
    int* best_index,
    int candidate_count) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  int selected_index = -1;
  int selected_inliers = -1;
  float selected_rms = 3.402823466e+38F;
  for (int i = 0; i < candidate_count; ++i) {
    const int score = candidate_scores[i];
    const float rms = candidate_rms[i];
    if (score < 0 || !isfinite(rms)) {
      continue;
    }
    if (score > selected_inliers || (score == selected_inliers && rms < selected_rms)) {
      selected_index = i;
      selected_inliers = score;
      selected_rms = rms;
    }
  }

  matrix[0] = 1.0f;
  matrix[1] = 0.0f;
  matrix[2] = 0.0f;
  matrix[3] = 0.0f;
  matrix[4] = 1.0f;
  matrix[5] = 0.0f;
  matrix[6] = 0.0f;
  matrix[7] = 0.0f;
  matrix[8] = 1.0f;
  *scale = 1.0f;
  *rotation_rad = 0.0f;
  *rms_px = NAN;
  *best_inliers = selected_inliers > 0 ? selected_inliers : 0;
  *best_index = selected_index;
  if (selected_index < 0 || selected_inliers <= 0) {
    return;
  }

  const int param_offset = selected_index * 4;
  const float a = candidate_params[param_offset + 0];
  const float b = candidate_params[param_offset + 1];
  const float tx = candidate_params[param_offset + 2];
  const float ty = candidate_params[param_offset + 3];
  matrix[0] = a;
  matrix[1] = -b;
  matrix[2] = tx;
  matrix[3] = b;
  matrix[4] = a;
  matrix[5] = ty;
  *scale = sqrtf(a * a + b * b);
  *rotation_rad = atan2f(b, a);
  *rms_px = selected_rms;
}

__global__ void catalog_similarity_refit_stats_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const float* candidate_params,
    const int* best_index,
    double* partial_sums,
    unsigned long long* partial_count,
    int reference_count,
    int moving_count,
    float tolerance_px) {
  extern __shared__ unsigned char similarity_scratch[];
  double* sum_mx = reinterpret_cast<double*>(similarity_scratch);
  double* sum_my = sum_mx + blockDim.x;
  double* sum_rx = sum_my + blockDim.x;
  double* sum_ry = sum_rx + blockDim.x;
  double* sum_moving_power = sum_ry + blockDim.x;
  double* sum_dot_same = sum_moving_power + blockDim.x;
  double* sum_dot_cross = sum_dot_same + blockDim.x;
  unsigned long long* valid_counts = reinterpret_cast<unsigned long long*>(sum_dot_cross + blockDim.x);

  const int lane = static_cast<int>(threadIdx.x);
  double local_mx = 0.0;
  double local_my = 0.0;
  double local_rx = 0.0;
  double local_ry = 0.0;
  double local_moving_power = 0.0;
  double local_dot_same = 0.0;
  double local_dot_cross = 0.0;
  unsigned long long local_count = 0;

  const int selected_index = *best_index;
  if (selected_index >= 0) {
    const int param_offset = selected_index * 4;
    const float a = candidate_params[param_offset + 0];
    const float b = candidate_params[param_offset + 1];
    const float tx = candidate_params[param_offset + 2];
    const float ty = candidate_params[param_offset + 3];
    const float tolerance2 = tolerance_px * tolerance_px;
    if (isfinite(a) && isfinite(b) && isfinite(tx) && isfinite(ty)) {
      for (int moving_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
           moving_index < moving_count;
           moving_index += static_cast<int>(gridDim.x * blockDim.x)) {
        const float mx_f = moving_x[moving_index];
        const float my_f = moving_y[moving_index];
        if (!isfinite(mx_f) || !isfinite(my_f)) {
          continue;
        }
        const float transformed_x = a * mx_f - b * my_f + tx;
        const float transformed_y = b * mx_f + a * my_f + ty;
        float best_distance2 = tolerance2;
        int best_reference = -1;
        for (int reference_index = 0; reference_index < reference_count; ++reference_index) {
          const float rx_f = reference_x[reference_index];
          const float ry_f = reference_y[reference_index];
          if (!isfinite(rx_f) || !isfinite(ry_f)) {
            continue;
          }
          const float dx = transformed_x - rx_f;
          const float dy = transformed_y - ry_f;
          const float distance2 = dx * dx + dy * dy;
          if (distance2 <= best_distance2) {
            best_distance2 = distance2;
            best_reference = reference_index;
          }
        }
        if (best_reference < 0) {
          continue;
        }
        const double mx = static_cast<double>(mx_f);
        const double my = static_cast<double>(my_f);
        const double rx = static_cast<double>(reference_x[best_reference]);
        const double ry = static_cast<double>(reference_y[best_reference]);
        local_mx += mx;
        local_my += my;
        local_rx += rx;
        local_ry += ry;
        local_moving_power += mx * mx + my * my;
        local_dot_same += mx * rx + my * ry;
        local_dot_cross += mx * ry - my * rx;
        ++local_count;
      }
    }
  }

  sum_mx[lane] = local_mx;
  sum_my[lane] = local_my;
  sum_rx[lane] = local_rx;
  sum_ry[lane] = local_ry;
  sum_moving_power[lane] = local_moving_power;
  sum_dot_same[lane] = local_dot_same;
  sum_dot_cross[lane] = local_dot_cross;
  valid_counts[lane] = local_count;
  __syncthreads();

  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      sum_mx[lane] += sum_mx[lane + stride];
      sum_my[lane] += sum_my[lane + stride];
      sum_rx[lane] += sum_rx[lane + stride];
      sum_ry[lane] += sum_ry[lane + stride];
      sum_moving_power[lane] += sum_moving_power[lane + stride];
      sum_dot_same[lane] += sum_dot_same[lane + stride];
      sum_dot_cross[lane] += sum_dot_cross[lane + stride];
      valid_counts[lane] += valid_counts[lane + stride];
    }
    __syncthreads();
  }

  if (lane == 0) {
    const int offset = static_cast<int>(blockIdx.x) * 7;
    partial_sums[offset + 0] = sum_mx[0];
    partial_sums[offset + 1] = sum_my[0];
    partial_sums[offset + 2] = sum_rx[0];
    partial_sums[offset + 3] = sum_ry[0];
    partial_sums[offset + 4] = sum_moving_power[0];
    partial_sums[offset + 5] = sum_dot_same[0];
    partial_sums[offset + 6] = sum_dot_cross[0];
    partial_count[blockIdx.x] = valid_counts[0];
  }
}

__global__ void catalog_similarity_refit_finalize_matrix_kernel(
    const double* partial_sums,
    const unsigned long long* partial_count,
    float* refit_matrix,
    float* refit_scale,
    float* refit_rotation_rad,
    int* refit_inliers,
    int* refit_status,
    int blocks) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  double sum_mx = 0.0;
  double sum_my = 0.0;
  double sum_rx = 0.0;
  double sum_ry = 0.0;
  double sum_moving_power = 0.0;
  double sum_dot_same = 0.0;
  double sum_dot_cross = 0.0;
  unsigned long long count = 0;
  for (int block = 0; block < blocks; ++block) {
    const int offset = block * 7;
    sum_mx += partial_sums[offset + 0];
    sum_my += partial_sums[offset + 1];
    sum_rx += partial_sums[offset + 2];
    sum_ry += partial_sums[offset + 3];
    sum_moving_power += partial_sums[offset + 4];
    sum_dot_same += partial_sums[offset + 5];
    sum_dot_cross += partial_sums[offset + 6];
    count += partial_count[block];
  }
  *refit_inliers = static_cast<int>(count);
  if (count < 2ULL) {
    *refit_status = 1;
    return;
  }

  const double n = static_cast<double>(count);
  const double mean_mx = sum_mx / n;
  const double mean_my = sum_my / n;
  const double mean_rx = sum_rx / n;
  const double mean_ry = sum_ry / n;
  const double denominator = sum_moving_power - n * (mean_mx * mean_mx + mean_my * mean_my);
  if (denominator <= 1.0e-20) {
    *refit_status = 2;
    return;
  }
  const double numer_a = sum_dot_same - n * (mean_mx * mean_rx + mean_my * mean_ry);
  const double numer_b = sum_dot_cross - n * (mean_mx * mean_ry - mean_my * mean_rx);
  const double a = numer_a / denominator;
  const double b = numer_b / denominator;
  const double tx = mean_rx - (a * mean_mx - b * mean_my);
  const double ty = mean_ry - (b * mean_mx + a * mean_my);

  refit_matrix[0] = static_cast<float>(a);
  refit_matrix[1] = static_cast<float>(-b);
  refit_matrix[2] = static_cast<float>(tx);
  refit_matrix[3] = static_cast<float>(b);
  refit_matrix[4] = static_cast<float>(a);
  refit_matrix[5] = static_cast<float>(ty);
  refit_matrix[6] = 0.0f;
  refit_matrix[7] = 0.0f;
  refit_matrix[8] = 1.0f;
  *refit_scale = static_cast<float>(sqrt(a * a + b * b));
  *refit_rotation_rad = static_cast<float>(atan2(b, a));
  *refit_status = 0;
}

__global__ void catalog_similarity_refit_residual_sums_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const float* candidate_params,
    const int* best_index,
    const float* matrix,
    const int* refit_status,
    double* partial_residual_sums,
    int reference_count,
    int moving_count,
    float tolerance_px) {
  extern __shared__ double residual_sums[];
  const int lane = static_cast<int>(threadIdx.x);
  double local_sum = 0.0;
  const int selected_index = *best_index;
  if (*refit_status == 0 && selected_index >= 0) {
    const int param_offset = selected_index * 4;
    const float seed_a = candidate_params[param_offset + 0];
    const float seed_b = candidate_params[param_offset + 1];
    const float seed_tx = candidate_params[param_offset + 2];
    const float seed_ty = candidate_params[param_offset + 3];
    const double m00 = static_cast<double>(matrix[0]);
    const double m01 = static_cast<double>(matrix[1]);
    const double m02 = static_cast<double>(matrix[2]);
    const double m10 = static_cast<double>(matrix[3]);
    const double m11 = static_cast<double>(matrix[4]);
    const double m12 = static_cast<double>(matrix[5]);
    const float tolerance2 = tolerance_px * tolerance_px;
    if (isfinite(seed_a) && isfinite(seed_b) && isfinite(seed_tx) && isfinite(seed_ty)) {
      for (int moving_index = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
           moving_index < moving_count;
           moving_index += static_cast<int>(gridDim.x * blockDim.x)) {
        const float mx_f = moving_x[moving_index];
        const float my_f = moving_y[moving_index];
        if (!isfinite(mx_f) || !isfinite(my_f)) {
          continue;
        }
        const float seed_x = seed_a * mx_f - seed_b * my_f + seed_tx;
        const float seed_y = seed_b * mx_f + seed_a * my_f + seed_ty;
        float best_distance2 = tolerance2;
        int best_reference = -1;
        for (int reference_index = 0; reference_index < reference_count; ++reference_index) {
          const float rx_f = reference_x[reference_index];
          const float ry_f = reference_y[reference_index];
          if (!isfinite(rx_f) || !isfinite(ry_f)) {
            continue;
          }
          const float dx = seed_x - rx_f;
          const float dy = seed_y - ry_f;
          const float distance2 = dx * dx + dy * dy;
          if (distance2 <= best_distance2) {
            best_distance2 = distance2;
            best_reference = reference_index;
          }
        }
        if (best_reference < 0) {
          continue;
        }
        const double mx = static_cast<double>(mx_f);
        const double my = static_cast<double>(my_f);
        const double dx = (m00 * mx + m01 * my + m02) - static_cast<double>(reference_x[best_reference]);
        const double dy = (m10 * mx + m11 * my + m12) - static_cast<double>(reference_y[best_reference]);
        local_sum += dx * dx + dy * dy;
      }
    }
  }
  residual_sums[lane] = local_sum;
  __syncthreads();
  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      residual_sums[lane] += residual_sums[lane + stride];
    }
    __syncthreads();
  }
  if (lane == 0) {
    partial_residual_sums[blockIdx.x] = residual_sums[0];
  }
}

__global__ void catalog_similarity_refit_finalize_rms_kernel(
    const double* partial_residual_sums,
    const int* refit_inliers,
    const int* refit_status,
    float* refit_rms_px,
    int blocks) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  if (*refit_status != 0 || *refit_inliers <= 0) {
    *refit_rms_px = NAN;
    return;
  }
  double residual_sum = 0.0;
  for (int block = 0; block < blocks; ++block) {
    residual_sum += partial_residual_sums[block];
  }
  *refit_rms_px = static_cast<float>(sqrt(residual_sum / static_cast<double>(*refit_inliers)));
}

__global__ void catalog_similarity_refit_select_kernel(
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    const float* refit_matrix,
    const float* refit_scale,
    const float* refit_rotation_rad,
    const float* refit_rms_px,
    const int* best_inliers,
    const int* refit_inliers,
    int* refit_status) {
  if (blockIdx.x != 0 || threadIdx.x != 0) {
    return;
  }
  if (*refit_status != 0) {
    return;
  }
  if (*refit_inliers < *best_inliers || !isfinite(*refit_rms_px) || !isfinite(*rms_px) ||
      *refit_rms_px > *rms_px) {
    *refit_status = 3;
    return;
  }
  for (int i = 0; i < 9; ++i) {
    matrix[i] = refit_matrix[i];
  }
  *scale = *refit_scale;
  *rotation_rad = *refit_rotation_rad;
  *rms_px = *refit_rms_px;
}

}  // namespace

void gpwbpp_estimate_translation_search_f32_launch(
    const float* reference,
    const float* moving,
    float* scores,
    int* best_dx,
    int* best_dy,
    float* best_score,
    int width,
    int height,
    int max_shift_x,
    int max_shift_y,
    int sample_stride) {
  constexpr int threads = 256;
  const int shift_count = (2 * max_shift_x + 1) * (2 * max_shift_y + 1);
  const std::size_t shared_bytes = 6 * threads * sizeof(float);
  translation_search_score_kernel<<<shift_count, threads, shared_bytes>>>(
      reference, moving, scores, width, height, max_shift_x, max_shift_y, sample_stride);
  translation_search_best_kernel<<<1, 1>>>(
      scores, best_dx, best_dy, best_score, max_shift_x, max_shift_y, shift_count);
}

void gpwbpp_estimate_translation_subpixel_ncc_f32_launch(
    const float* reference,
    const float* moving,
    float* scores,
    float* best_dx,
    float* best_dy,
    float* best_score,
    int width,
    int height,
    float center_dx,
    float center_dy,
    int radius_steps,
    float step,
    int sample_stride) {
  constexpr int threads = 256;
  const int candidate_count = (2 * radius_steps + 1) * (2 * radius_steps + 1);
  const std::size_t shared_bytes = 6 * threads * sizeof(float);
  translation_subpixel_score_kernel<<<candidate_count, threads, shared_bytes>>>(
      reference, moving, scores, width, height, center_dx, center_dy, radius_steps, step, sample_stride);
  translation_subpixel_best_kernel<<<1, 1>>>(
      scores, best_dx, best_dy, best_score, center_dx, center_dy, radius_steps, step, candidate_count);
}

void gpwbpp_estimate_translation_from_catalogs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_dx,
    float* candidate_dy,
    int* scores,
    float* best_dx,
    float* best_dy,
    int* best_inliers,
    int* moving_best_reference,
    int* reference_best_moving,
    float* refine_sums,
    int* mutual_inliers,
    float* refined_dx,
    float* refined_dy,
    float* rms_px,
    int reference_count,
    int moving_count,
    float tolerance_px,
    float max_abs_dx,
    float max_abs_dy,
    float prior_dx,
    float prior_dy,
    float prior_radius_px) {
  constexpr int threads = 256;
  const int pair_count = reference_count * moving_count;
  const int blocks = (pair_count + threads - 1) / threads;
  const int reference_blocks = (reference_count + threads - 1) / threads;
  const int moving_blocks = (moving_count + threads - 1) / threads;
  catalog_pair_offsets_kernel<<<blocks, threads>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      candidate_dx,
      candidate_dy,
      reference_count,
      moving_count,
      pair_count,
      max_abs_dx,
      max_abs_dy,
      prior_dx,
      prior_dy,
      prior_radius_px);
  catalog_offset_score_kernel<<<blocks, threads>>>(candidate_dx, candidate_dy, scores, pair_count, tolerance_px);
  catalog_offset_best_kernel<<<1, 1>>>(candidate_dx, candidate_dy, scores, best_dx, best_dy, best_inliers, pair_count);
  cudaMemset(moving_best_reference, 0xff, static_cast<std::size_t>(moving_count) * sizeof(int));
  cudaMemset(reference_best_moving, 0xff, static_cast<std::size_t>(reference_count) * sizeof(int));
  cudaMemset(refine_sums, 0, 3 * sizeof(float));
  cudaMemset(mutual_inliers, 0, sizeof(int));
  catalog_moving_best_reference_kernel<<<moving_blocks, threads>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      best_dx,
      best_dy,
      moving_best_reference,
      reference_count,
      moving_count,
      tolerance_px);
  catalog_reference_best_moving_kernel<<<reference_blocks, threads>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      best_dx,
      best_dy,
      reference_best_moving,
      reference_count,
      moving_count,
      tolerance_px);
  catalog_mutual_refine_sums_kernel<<<moving_blocks, threads>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      moving_best_reference,
      reference_best_moving,
      refine_sums,
      mutual_inliers,
      moving_count);
  catalog_finalize_refinement_kernel<<<1, 1>>>(best_dx, best_dy, refine_sums, mutual_inliers, refined_dx, refined_dy);
  catalog_mutual_rms_kernel<<<moving_blocks, threads>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      moving_best_reference,
      reference_best_moving,
      refined_dx,
      refined_dy,
      refine_sums,
      moving_count);
  catalog_finalize_rms_kernel<<<1, 1>>>(refine_sums, mutual_inliers, rms_px);
}

void gpwbpp_estimate_similarity_from_pairs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* valid_count,
    int* status,
    double* partial_sums,
    unsigned long long* partial_count,
    double* partial_residual_sums,
    int count,
    int blocks) {
  constexpr int threads = 256;
  const std::size_t stats_shared_bytes =
      7 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  similarity_pair_stats_kernel<<<blocks, threads, stats_shared_bytes>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      partial_sums,
      partial_count,
      count);
  similarity_finalize_matrix_kernel<<<1, 1>>>(
      partial_sums,
      partial_count,
      matrix,
      scale,
      rotation_rad,
      valid_count,
      status,
      blocks);
  similarity_residual_sums_kernel<<<blocks, threads, threads * sizeof(double)>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      matrix,
      status,
      partial_residual_sums,
      count);
  similarity_finalize_rms_kernel<<<1, 1>>>(
      partial_residual_sums,
      valid_count,
      status,
      rms_px,
      blocks);
}

void gpwbpp_estimate_similarity_from_catalogs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_params,
    int* candidate_scores,
    float* candidate_rms,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* best_inliers,
    int* best_index,
    int* refit_inliers,
    int* refit_status,
    float* refit_matrix,
    float* refit_scale,
    float* refit_rotation_rad,
    float* refit_rms_px,
    double* refit_partial_sums,
    unsigned long long* refit_partial_count,
    double* refit_partial_residual_sums,
    int refit_blocks,
    int reference_count,
    int moving_count,
    int candidate_count,
    float tolerance_px,
    float min_pair_distance,
    float prior_dx,
    float prior_dy,
    float prior_radius_px,
    float min_scale,
    float max_scale,
    float max_abs_rotation_rad) {
  constexpr int threads = 256;
  const int blocks = (candidate_count + threads - 1) / threads;
  catalog_similarity_score_kernel<<<blocks, threads>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      candidate_params,
      candidate_scores,
      candidate_rms,
      reference_count,
      moving_count,
      candidate_count,
      tolerance_px,
      min_pair_distance,
      prior_dx,
      prior_dy,
      prior_radius_px,
      min_scale,
      max_scale,
      max_abs_rotation_rad);
  catalog_similarity_best_kernel<<<1, 1>>>(
      candidate_params,
      candidate_scores,
      candidate_rms,
      matrix,
      scale,
      rotation_rad,
      rms_px,
      best_inliers,
      best_index,
      candidate_count);
  const std::size_t stats_shared_bytes =
      7 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  catalog_similarity_refit_stats_kernel<<<refit_blocks, threads, stats_shared_bytes>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      candidate_params,
      best_index,
      refit_partial_sums,
      refit_partial_count,
      reference_count,
      moving_count,
      tolerance_px);
  catalog_similarity_refit_finalize_matrix_kernel<<<1, 1>>>(
      refit_partial_sums,
      refit_partial_count,
      refit_matrix,
      refit_scale,
      refit_rotation_rad,
      refit_inliers,
      refit_status,
      refit_blocks);
  catalog_similarity_refit_residual_sums_kernel<<<refit_blocks, threads, threads * sizeof(double)>>>(
      reference_x,
      reference_y,
      moving_x,
      moving_y,
      candidate_params,
      best_index,
      refit_matrix,
      refit_status,
      refit_partial_residual_sums,
      reference_count,
      moving_count,
      tolerance_px);
  catalog_similarity_refit_finalize_rms_kernel<<<1, 1>>>(
      refit_partial_residual_sums,
      refit_inliers,
      refit_status,
      refit_rms_px,
      refit_blocks);
  catalog_similarity_refit_select_kernel<<<1, 1>>>(
      matrix,
      scale,
      rotation_rad,
      rms_px,
      refit_matrix,
      refit_scale,
      refit_rotation_rad,
      refit_rms_px,
      best_inliers,
      refit_inliers,
      refit_status);
}
