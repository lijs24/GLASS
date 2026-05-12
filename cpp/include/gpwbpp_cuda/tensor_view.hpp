#pragma once

#include <cstddef>

namespace gpwbpp_cuda {
template <typename T>
struct TensorView2D {
  T* data;
  std::size_t height;
  std::size_t width;
  std::size_t stride;
};
}

