#pragma once

#ifdef __CUDACC__
#define GPWBPP_DEVICE __device__
#else
#define GPWBPP_DEVICE
#endif

