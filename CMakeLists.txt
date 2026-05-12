cmake_minimum_required(VERSION 3.24)
project(gpwbpp LANGUAGES CXX)

option(GPWBPP_BUILD_CUDA "Build optional CUDA extension" OFF)
option(GPWBPP_BUILD_PYTHON_CUDA "Build native Python CUDA module" OFF)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(CompilerWarnings)

if(GPWBPP_BUILD_CUDA OR GPWBPP_BUILD_PYTHON_CUDA)
  enable_language(CUDA)
endif()

if(GPWBPP_BUILD_CUDA)
  add_subdirectory(cpp)
endif()

if(GPWBPP_BUILD_PYTHON_CUDA)
  find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)
  find_package(pybind11 CONFIG REQUIRED)
  find_package(CUDAToolkit REQUIRED)

  pybind11_add_module(_gpwbpp_cuda_native MODULE
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
  target_include_directories(_gpwbpp_cuda_native PRIVATE cpp/include)
  target_link_libraries(_gpwbpp_cuda_native PRIVATE CUDA::cudart)
  target_compile_features(_gpwbpp_cuda_native PRIVATE cxx_std_17)
  set_target_properties(_gpwbpp_cuda_native PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src"
    CUDA_RUNTIME_LIBRARY Shared
    CUDA_SEPARABLE_COMPILATION OFF
  )
  gpwbpp_enable_warnings(_gpwbpp_cuda_native)
endif()
