#include "xdfeequ.h"
#include "xdfeequ_hw.h"

extern u32 XDfeEqu_RdBitField(u32 width, u32 offset, u32 data);
#define FIELD(word, field) XDfeEqu_RdBitField(field##_WIDTH, field##_OFFSET, word)

static void load_config(XDfeEqu *inst)
{
    u32 word = XDfeEqu_ReadReg(inst, XDFEEQU_MODEL_PARAM_OFFSET);
    inst->Config.NumChannels = FIELD(word, XDFEEQU_MODEL_PARAM_NUM_CHANNELS);
    inst->Config.SampleWidth = FIELD(word, XDFEEQU_MODEL_PARAM_SAMPLE_WIDTH);
    inst->Config.ComplexModel = FIELD(word, XDFEEQU_MODEL_PARAM_COMPLEX_MODE);
    inst->Config.TuserWidth = FIELD(word, XDFEEQU_MODEL_PARAM_TUSER_WIDTH);
}

#define DRIVER XDfeEqu
#define READY XDFEEQU_STATE_READY
#define OPEN xdfe_equ_mmio_open
#define CLOSE xdfe_equ_mmio_close
#define OPEN_BUFFER xdfe_equ_mmio_open_buffer
#define MIN_SIZE 0x4000
#include "mmio_impl.h"
