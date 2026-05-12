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
    int max_shift_y) {
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
  const int n = width * height;

  float local_ref = 0.0f;
  float local_mov = 0.0f;
  float local_ref2 = 0.0f;
  float local_mov2 = 0.0f;
  float local_cross = 0.0f;
  float local_count = 0.0f;

  for (int i = static_cast<int>(threadIdx.x); i < n; i += static_cast<int>(blockDim.x)) {
    const int x = i % width;
    const int y = i / width;
    const int sx = x - dx;
    const int sy = y - dy;
    if (sx < 0 || sx >= width || sy < 0 || sy >= height) {
      continue;
    }
    const float r = reference[i];
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

__global__ void catalog_pair_offsets_kernel(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_dx,
    float* candidate_dy,
    int reference_count,
    int moving_count,
    int pair_count) {
  const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= pair_count) {
    return;
  }
  const int reference_index = i / moving_count;
  const int moving_index = i % moving_count;
  candidate_dx[i] = reference_x[reference_index] - moving_x[moving_index];
  candidate_dy[i] = reference_y[reference_index] - moving_y[moving_index];
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
  const float tolerance2 = tolerance_px * tolerance_px;
  int score = 0;
  for (int j = 0; j < pair_count; ++j) {
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
  int best_index = 0;
  int best_score = scores[0];
  for (int i = 1; i < pair_count; ++i) {
    const int score = scores[i];
    if (score > best_score) {
      best_score = score;
      best_index = i;
    }
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
    int max_shift_y) {
  constexpr int threads = 256;
  const int shift_count = (2 * max_shift_x + 1) * (2 * max_shift_y + 1);
  const std::size_t shared_bytes = 6 * threads * sizeof(float);
  translation_search_score_kernel<<<shift_count, threads, shared_bytes>>>(
      reference, moving, scores, width, height, max_shift_x, max_shift_y);
  translation_search_best_kernel<<<1, 1>>>(
      scores, best_dx, best_dy, best_score, max_shift_x, max_shift_y, shift_count);
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
    float tolerance_px) {
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
      pair_count);
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
