#pragma once

#ifdef __CUDACC__
#define GLASS_DEVICE __device__
#else
#define GLASS_DEVICE
#endif

