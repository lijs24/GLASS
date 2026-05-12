cmake_minimum_required(VERSION 3.24)

add_library(gpwbpp_cuda_core STATIC
  src/api.cpp
  src/device.cpp
  src/errors.cpp
  src/memory.cpp
)
target_include_directories(gpwbpp_cuda_core PUBLIC include)
target_compile_features(gpwbpp_cuda_core PUBLIC cxx_std_17)
gpwbpp_enable_warnings(gpwbpp_cuda_core)

