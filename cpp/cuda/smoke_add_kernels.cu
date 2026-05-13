#include <cstddef>

__global__ void glass_smoke_add_f32_kernel(
    const float* a, const float* b, float* out, std::size_t n) {
  const std::size_t i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < n) {
    out[i] = a[i] + b[i];
  }
}

void glass_smoke_add_f32_launch(const float* a, const float* b, float* out, std::size_t n) {
  constexpr int threads = 256;
  const int blocks = static_cast<int>((n + threads - 1) / threads);
  glass_smoke_add_f32_kernel<<<blocks, threads>>>(a, b, out, n);
}

