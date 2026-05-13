#pragma once

#include <stdexcept>
#include <string>

namespace glass_cuda {
class cuda_error : public std::runtime_error {
 public:
  explicit cuda_error(const std::string& message) : std::runtime_error(message) {}
};
}

