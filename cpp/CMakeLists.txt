cmake_minimum_required(VERSION 3.24)

add_library(glass_cuda_core STATIC
  src/api.cpp
  src/device.cpp
  src/errors.cpp
  src/memory.cpp
)
target_include_directories(glass_cuda_core PUBLIC include)
target_compile_features(glass_cuda_core PUBLIC cxx_std_17)
glass_enable_warnings(glass_cuda_core)

