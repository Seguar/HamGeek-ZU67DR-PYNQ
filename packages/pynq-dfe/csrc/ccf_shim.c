#include "xdfeccf.h"
#include "xdfeccf_hw.h"

extern u32 XDfeCcf_RdBitField(u32 width, u32 offset, u32 data);
#define FIELD(word, field) XDfeCcf_RdBitField(field##_WIDTH, field##_OFFSET, word)

static void load_config(XDfeCcf *inst)
{
    u32 word = XDfeCcf_ReadReg(inst, XDFECCF_MODEL_PARAM_OFFSET);
    inst->Config.NumAntenna = FIELD(word, XDFECCF_MODEL_PARAM_NUM_ANTENNA);
    inst->Config.NumCCPerAntenna = FIELD(word, XDFECCF_MODEL_PARAM_NUM_CC_PER_ANTENNA);
    inst->Config.AntennaInterleave = FIELD(word, XDFECCF_MODEL_PARAM_ANTENNA_INTERLEAVE);
    inst->Config.Switchable = FIELD(word, XDFECCF_MODEL_PARAM_SWITCHABLE);
}

#define DRIVER XDfeCcf
#define READY XDFECCF_STATE_READY
#define OPEN xdfe_ccf_mmio_open
#define CLOSE xdfe_ccf_mmio_close
#define OPEN_BUFFER xdfe_ccf_mmio_open_buffer
#define MIN_SIZE 0x4000
#include "mmio_impl.h"
