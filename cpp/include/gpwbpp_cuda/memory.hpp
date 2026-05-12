#pragma once

#include <cstddef>

namespace gpwbpp_cuda {
struct MemoryBudget {
  std::size_t ram_bytes;
  std::size_t vram_bytes;
};
}

