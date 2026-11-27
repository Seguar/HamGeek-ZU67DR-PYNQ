#pragma once
#include "../xdfe_mmio_shim.h"

XDfeMix *xdfe_mix_mmio_open_buffer(const char *name, void *buffer, uint64_t size);
XDfeCcf *xdfe_ccf_mmio_open_buffer(const char *name, void *buffer, uint64_t size);
XDfeEqu *xdfe_equ_mmio_open_buffer(const char *name, void *buffer, uint64_t size);
XDfePrach *xdfe_prach_mmio_open_buffer(const char *name, void *buffer, uint64_t size);
XDfeOfdm *xdfe_ofdm_mmio_open_buffer(const char *name, void *buffer, uint64_t size);
