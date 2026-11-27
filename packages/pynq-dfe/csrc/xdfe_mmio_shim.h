#pragma once
#include <stdint.h>
#include "xdfemix.h"
#include "xdfeccf.h"
#include "xdfeequ.h"
#include "xdfeprach.h"
#include "xdfeofdm.h"

XDfeMix *xdfe_mix_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_mix_mmio_close(XDfeMix *inst);
XDfeCcf *xdfe_ccf_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_ccf_mmio_close(XDfeCcf *inst);
XDfeEqu *xdfe_equ_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_equ_mmio_close(XDfeEqu *inst);
XDfePrach *xdfe_prach_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_prach_mmio_close(XDfePrach *inst);
XDfeOfdm *xdfe_ofdm_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_ofdm_mmio_close(XDfeOfdm *inst);
