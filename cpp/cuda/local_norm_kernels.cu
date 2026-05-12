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
