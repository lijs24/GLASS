#include "common.cuh"

#include <cstddef>
#include <cstdint>

__global__ void gpwbpp_local_norm_apply_f32_kernel(
    const float* input,
    float* output,
    std::size_t n,
    float scale,
    float offset) {
  const std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + threadIdx.x);
  if (i >= n) {
    return;
  }
  output[i] = input[i] * scale + offset;
}

void gpwbpp_local_norm_apply_f32_launch(
    const float* input,
    float* output,
    std::size_t n,
    float scale,
    float offset) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  gpwbpp_local_norm_apply_f32_kernel<<<blocks, threads>>>(input, output, n, scale, offset);
}

__global__ void gpwbpp_local_norm_apply_grid_f32_kernel(
    const float* input,
    float* output,
    const float* scales,
    const float* offsets,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows) {
  const int x = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
  const int y = static_cast<int>(blockIdx.y * blockDim.y + threadIdx.y);
  if (x >= width || y >= height) {
    return;
  }
  const int tile_x = min(x / tile_width, grid_cols - 1);
  const int tile_y = min(y / tile_height, grid_rows - 1);
  const int tile_index = tile_y * grid_cols + tile_x;
  const std::size_t pixel_index = static_cast<std::size_t>(y) * static_cast<std::size_t>(width) +
                                  static_cast<std::size_t>(x);
  output[pixel_index] = input[pixel_index] * scales[tile_index] + offsets[tile_index];
}

void gpwbpp_local_norm_apply_grid_f32_launch(
    const float* input,
    float* output,
    const float* scales,
    const float* offsets,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows) {
  dim3 threads(16, 16);
  dim3 blocks(
      static_cast<unsigned int>((width + static_cast<int>(threads.x) - 1) / static_cast<int>(threads.x)),
      static_cast<unsigned int>((height + static_cast<int>(threads.y) - 1) / static_cast<int>(threads.y)));
  gpwbpp_local_norm_apply_grid_f32_kernel<<<blocks, threads>>>(
      input, output, scales, offsets, width, height, tile_width, tile_height, grid_cols, grid_rows);
}

__global__ void gpwbpp_frame_sum_stats_f32_kernel(
    const float* input,
    double* partial_sum,
    double* partial_sum2,
    unsigned long long* partial_count,
    std::size_t n) {
  extern __shared__ unsigned char scratch[];
  double* sums = reinterpret_cast<double*>(scratch);
  double* sums2 = sums + blockDim.x;
  unsigned long long* counts = reinterpret_cast<unsigned long long*>(sums2 + blockDim.x);

  const int lane = static_cast<int>(threadIdx.x);
  double local_sum = 0.0;
  double local_sum2 = 0.0;
  unsigned long long local_count = 0;
  for (std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + lane);
       i < n;
       i += static_cast<std::size_t>(gridDim.x * blockDim.x)) {
    const float value = input[i];
    if (isfinite(value)) {
      const double v = static_cast<double>(value);
      local_sum += v;
      local_sum2 += v * v;
      ++local_count;
    }
  }
  sums[lane] = local_sum;
  sums2[lane] = local_sum2;
  counts[lane] = local_count;
  __syncthreads();

  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      sums[lane] += sums[lane + stride];
      sums2[lane] += sums2[lane + stride];
      counts[lane] += counts[lane + stride];
    }
    __syncthreads();
  }
  if (lane == 0) {
    partial_sum[blockIdx.x] = sums[0];
    partial_sum2[blockIdx.x] = sums2[0];
    partial_count[blockIdx.x] = counts[0];
  }
}

void gpwbpp_frame_sum_stats_f32_launch(
    const float* input,
    double* partial_sum,
    double* partial_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks) {
  constexpr int threads = 256;
  const std::size_t shared_bytes =
      2 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  gpwbpp_frame_sum_stats_f32_kernel<<<blocks, threads, shared_bytes>>>(
      input, partial_sum, partial_sum2, partial_count, n);
}

__global__ void gpwbpp_pair_sum_stats_f32_kernel(
    const float* source,
    const float* reference,
    double* partial_source_sum,
    double* partial_source_sum2,
    double* partial_reference_sum,
    double* partial_reference_sum2,
    unsigned long long* partial_count,
    std::size_t n) {
  extern __shared__ unsigned char scratch[];
  double* source_sums = reinterpret_cast<double*>(scratch);
  double* source_sums2 = source_sums + blockDim.x;
  double* reference_sums = source_sums2 + blockDim.x;
  double* reference_sums2 = reference_sums + blockDim.x;
  unsigned long long* counts = reinterpret_cast<unsigned long long*>(reference_sums2 + blockDim.x);

  const int lane = static_cast<int>(threadIdx.x);
  double local_source_sum = 0.0;
  double local_source_sum2 = 0.0;
  double local_reference_sum = 0.0;
  double local_reference_sum2 = 0.0;
  unsigned long long local_count = 0;
  for (std::size_t i = static_cast<std::size_t>(blockIdx.x * blockDim.x + lane);
       i < n;
       i += static_cast<std::size_t>(gridDim.x * blockDim.x)) {
    const float source_value = source[i];
    const float reference_value = reference[i];
    if (isfinite(source_value) && isfinite(reference_value)) {
      const double s = static_cast<double>(source_value);
      const double r = static_cast<double>(reference_value);
      local_source_sum += s;
      local_source_sum2 += s * s;
      local_reference_sum += r;
      local_reference_sum2 += r * r;
      ++local_count;
    }
  }
  source_sums[lane] = local_source_sum;
  source_sums2[lane] = local_source_sum2;
  reference_sums[lane] = local_reference_sum;
  reference_sums2[lane] = local_reference_sum2;
  counts[lane] = local_count;
  __syncthreads();

  for (int stride = static_cast<int>(blockDim.x) / 2; stride > 0; stride >>= 1) {
    if (lane < stride) {
      source_sums[lane] += source_sums[lane + stride];
      source_sums2[lane] += source_sums2[lane + stride];
      reference_sums[lane] += reference_sums[lane + stride];
      reference_sums2[lane] += reference_sums2[lane + stride];
      counts[lane] += counts[lane + stride];
    }
    __syncthreads();
  }
  if (lane == 0) {
    partial_source_sum[blockIdx.x] = source_sums[0];
    partial_source_sum2[blockIdx.x] = source_sums2[0];
    partial_reference_sum[blockIdx.x] = reference_sums[0];
    partial_reference_sum2[blockIdx.x] = reference_sums2[0];
    partial_count[blockIdx.x] = counts[0];
  }
}

void gpwbpp_pair_sum_stats_f32_launch(
    const float* source,
    const float* reference,
    double* partial_source_sum,
    double* partial_source_sum2,
    double* partial_reference_sum,
    double* partial_reference_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks) {
  constexpr int threads = 256;
  const std::size_t shared_bytes =
      4 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  gpwbpp_pair_sum_stats_f32_kernel<<<blocks, threads, shared_bytes>>>(
      source,
      reference,
      partial_source_sum,
      partial_source_sum2,
      partial_reference_sum,
      partial_reference_sum2,
      partial_count,
      n);
}
