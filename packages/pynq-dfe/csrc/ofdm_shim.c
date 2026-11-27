#include "xdfeofdm.h"
#include "xdfeofdm_hw.h"

static void load_config(XDfeOfdm *inst)
{
    /* Linux LookupConfig sets only BaseAddr for OFDM. */
    (void)inst;
}

#define DRIVER XDfeOfdm
#define READY XDFEOFDM_STATE_READY
#define OPEN xdfe_ofdm_mmio_open
#define CLOSE xdfe_ofdm_mmio_close
#define OPEN_BUFFER xdfe_ofdm_mmio_open_buffer
#define MIN_SIZE 0x4000
#include "mmio_impl.h"
