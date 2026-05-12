cmake_minimum_required(VERSION 3.24)
project(gpwbpp LANGUAGES CXX)

option(GPWBPP_BUILD_CUDA "Build optional CUDA extension" OFF)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(CompilerWarnings)

if(GPWBPP_BUILD_CUDA)
  enable_language(CUDA)
  add_subdirectory(cpp)
endif()

