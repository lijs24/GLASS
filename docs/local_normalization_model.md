# Local Normalization Model

Local normalization is gated after registration and warp. The model records a
reference frame, tile/window radius, background mask policy, outlier policy, and
any crop box if future stages crop output.

Gate 10 implements tile/window background and scale matching. Current code only
contains a global CPU helper used as a baseline placeholder.

