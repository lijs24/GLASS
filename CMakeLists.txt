cmake_minimum_required(VERSION 3.24)
project(glass LANGUAGES CXX)

option(GLASS_BUILD_CUDA "Build optional CUDA extension" OFF)
option(GLASS_BUILD_PYTHON_CUDA "Build native Python CUDA module" OFF)
set(GLASS_CUDA_RUNTIME_LIBRARY "Shared" CACHE STRING "CUDA runtime linkage for the native module")
set_property(CACHE GLASS_CUDA_RUNTIME_LIBRARY PROPERTY STRINGS Shared Static)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(CompilerWarnings)

if(GLASS_BUILD_CUDA OR GLASS_BUILD_PYTHON_CUDA)
  enable_language(CUDA)
endif()

if(GLASS_BUILD_CUDA)
  add_subdirectory(cpp)
endif()

if(GLASS_BUILD_PYTHON_CUDA)
  find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)
  find_package(pybind11 CONFIG REQUIRED)
  find_package(CUDAToolkit REQUIRED)

  pybind11_add_module(_glass_cuda_native MODULE
    cpp/src/native_bindings.cpp
    cpp/cuda/smoke_add_kernels.cu
    cpp/cuda/calibration_kernels.cu
    cpp/cuda/master_frame_kernels.cu
    cpp/cuda/warp_kernels.cu
    cpp/cuda/local_norm_kernels.cu
    cpp/cuda/integration_kernels.cu
    cpp/cuda/star_detect_kernels.cu
    cpp/cuda/registration_kernels.cu
  )
  target_include_directories(_glass_cuda_native PRIVATE cpp/include)
  target_link_libraries(_glass_cuda_native PRIVATE CUDA::cudart)
  target_compile_features(_glass_cuda_native PRIVATE cxx_std_17)
  set_target_properties(_glass_cuda_native PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src"
    CUDA_RUNTIME_LIBRARY "${GLASS_CUDA_RUNTIME_LIBRARY}"
    CUDA_SEPARABLE_COMPILATION OFF
  )
  glass_enable_warnings(_glass_cuda_native)
endif()
