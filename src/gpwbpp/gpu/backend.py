from __future__ import annotations

from gpwbpp.capabilities import cuda_extension_available


def backend_available() -> bool:
    return cuda_extension_available()

