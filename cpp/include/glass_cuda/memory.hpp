#pragma once

#include <cstddef>

namespace glass_cuda {
struct MemoryBudget {
  std::size_t ram_bytes;
  std::size_t vram_bytes;
};
}

