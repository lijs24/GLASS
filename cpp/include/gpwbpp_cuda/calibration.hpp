#pragma once

namespace gpwbpp_cuda {
struct CalibrationPolicy {
  bool master_dark_includes_bias;
  bool dark_scaling_enabled;
  float flat_floor;
  float pedestal;
};
}

