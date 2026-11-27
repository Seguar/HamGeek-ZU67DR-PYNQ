from time import monotonic, sleep
import numpy as np

N = 16384


def wait_for(check, what):
    until = monotonic() + 2
    while not check():
        if monotonic() >= until:
            raise TimeoutError(what)
        sleep(.001)


def transfer(dma, x):
    from pynq import allocate
    tx = allocate((N,), dtype=np.uint32)
    rx = allocate((N,), dtype=np.uint32)
    try:
        tx[:] = ((x.real.astype(np.int32) & 65535) |
                 (x.imag.astype(np.int32) << 16)).astype(np.uint32)
        dma.recvchannel.transfer(rx)
        dma.sendchannel.transfer(tx)
        for ch in (dma.sendchannel, dma.recvchannel):
            wait_for(lambda: ch.idle or ch.error, "DMA frame")
            ch.wait()
        if dma.recvchannel.transferred != rx.nbytes:
            raise RuntimeError("Short capture")
        words = np.asarray(rx)
        return (words.astype(np.int16).astype(float) +
                1j*(words >> 16).astype(np.int16).astype(float))
    except BaseException:
        dma.write(0, 4)
        wait_for(lambda: not dma.read(0) & 4, "DMA reset")
        raise
    finally:
        tx.freebuffer()
        rx.freebuffer()
