#include "common.cuh"

#include <cstddef>
#include <cstdint>

__global__ void glass_local_norm_apply_f32_kernel(
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

void glass_local_norm_apply_f32_launch(
    const float* input,
    float* output,
    std::size_t n,
    float scale,
    float offset) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_local_norm_apply_f32_kernel<<<blocks, threads>>>(input, output, n, scale, offset);
}

__global__ void glass_local_norm_apply_grid_f32_kernel(
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

void glass_local_norm_apply_grid_f32_launch(
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
  glass_local_norm_apply_grid_f32_kernel<<<blocks, threads>>>(
      input, output, scales, offsets, width, height, tile_width, tile_height, grid_cols, grid_rows);
}

__global__ void glass_frame_sum_stats_f32_kernel(
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

void glass_frame_sum_stats_f32_launch(
    const float* input,
    double* partial_sum,
    double* partial_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks) {
  constexpr int threads = 256;
  const std::size_t shared_bytes =
      2 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  glass_frame_sum_stats_f32_kernel<<<blocks, threads, shared_bytes>>>(
      input, partial_sum, partial_sum2, partial_count, n);
}

__global__ void glass_pair_sum_stats_f32_kernel(
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

void glass_pair_sum_stats_f32_launch(
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
  glass_pair_sum_stats_f32_kernel<<<blocks, threads, shared_bytes>>>(
      source,
      reference,
      partial_source_sum,
      partial_source_sum2,
      partial_reference_sum,
      partial_reference_sum2,
      partial_count,
      n);
}

__global__ void glass_pair_grid_sum_stats_f32_kernel(
    const float* source,
    const float* reference,
    double* source_sum,
    double* source_sum2,
    double* reference_sum,
    double* reference_sum2,
    unsigned long long* count,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows) {
  extern __shared__ unsigned char scratch[];
  double* source_sums = reinterpret_cast<double*>(scratch);
  double* source_sums2 = source_sums + blockDim.x;
  double* reference_sums = source_sums2 + blockDim.x;
  double* reference_sums2 = reference_sums + blockDim.x;
  unsigned long long* counts = reinterpret_cast<unsigned long long*>(reference_sums2 + blockDim.x);

  const int tile_index = static_cast<int>(blockIdx.x);
  if (tile_index >= grid_cols * grid_rows) {
    return;
  }
  const int tile_x = tile_index % grid_cols;
  const int tile_y = tile_index / grid_cols;
  const int x0 = tile_x * tile_width;
  const int y0 = tile_y * tile_height;
  const int x1 = min(x0 + tile_width, width);
  const int y1 = min(y0 + tile_height, height);
  const int actual_width = max(0, x1 - x0);
  const int actual_height = max(0, y1 - y0);
  const int actual_pixels = actual_width * actual_height;
  const int lane = static_cast<int>(threadIdx.x);

  double local_source_sum = 0.0;
  double local_source_sum2 = 0.0;
  double local_reference_sum = 0.0;
  double local_reference_sum2 = 0.0;
  unsigned long long local_count = 0;
  for (int offset = lane; offset < actual_pixels; offset += static_cast<int>(blockDim.x)) {
    const int y = y0 + offset / actual_width;
    const int x = x0 + offset - (offset / actual_width) * actual_width;
    const std::size_t pixel_index =
        static_cast<std::size_t>(y) * static_cast<std::size_t>(width) + static_cast<std::size_t>(x);
    const float source_value = source[pixel_index];
    const float reference_value = reference[pixel_index];
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
    source_sum[tile_index] = source_sums[0];
    source_sum2[tile_index] = source_sums2[0];
    reference_sum[tile_index] = reference_sums[0];
    reference_sum2[tile_index] = reference_sums2[0];
    count[tile_index] = counts[0];
  }
}

void glass_pair_grid_sum_stats_f32_launch(
    const float* source,
    const float* reference,
    double* source_sum,
    double* source_sum2,
    double* reference_sum,
    double* reference_sum2,
    unsigned long long* count,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows) {
  constexpr int threads = 256;
  const int blocks = grid_cols * grid_rows;
  const std::size_t shared_bytes =
      4 * threads * sizeof(double) + threads * sizeof(unsigned long long);
  glass_pair_grid_sum_stats_f32_kernel<<<blocks, threads, shared_bytes>>>(
      source,
      reference,
      source_sum,
      source_sum2,
      reference_sum,
      reference_sum2,
      count,
      width,
      height,
      tile_width,
      tile_height,
      grid_cols,
      grid_rows);
}
