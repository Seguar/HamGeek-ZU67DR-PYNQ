"""One 1024-beat periodic stimulus. The addressed IPs share one PL clock."""
import time
import numpy as np
from pynq import allocate


def signed(x, width):
    sign = 1 << (width - 1)
    return ((x.astype(np.int64) & (2 * sign - 1)) ^ sign) - sign


def capture(overlay, mode, x):
    lanes = (3, 1, 1)[mode]
    x = np.asarray(x).reshape(1024, lanes)
    words = ((x.real.astype(np.int64) & 65535)
             | ((x.imag.astype(np.int64) & 65535) << 16))
    with allocate((1024, 4), np.uint32) as tx, allocate((1024,), np.uint64) as rx:
        tx[:] = 0
        tx[:, :lanes] = words
        overlay.control.write(0, mode)
        dma = overlay.dma
        dma.recvchannel.transfer(rx)
        dma.sendchannel.transfer(tx)
        deadline = time.monotonic() + 5
        while not (dma.recvchannel.idle and dma.sendchannel.idle):
            if time.monotonic() >= deadline:
                raise TimeoutError(f"DMA MM2S/S2MM {dma.read(4):#x}/{dma.read(52):#x}, "
                                   f"frame status {overlay.control.read(8):#x}")
            time.sleep(.001)
        dma.sendchannel.wait()
        dma.recvchannel.wait()
        status = overlay.control.read(8)
        raw = np.array(rx)
    if mode == 2:
        y = signed(raw, 25) + 1j * signed(raw >> 25, 25)
    else:
        iq = raw.astype("<u8").view("<i2").reshape(-1, 2)
        y = iq[:, 0] + 1j * iq[:, 1]
    return y, (status >> 3) & 2047, status >> 15
