#include "xdfemix.h"
#include "xdfemix_hw.h"

extern u32 XDfeMix_RdBitField(u32 width, u32 offset, u32 data);
#define FIELD(word, field) XDfeMix_RdBitField(field##_WIDTH, field##_OFFSET, word)

static void load_config(XDfeMix *inst)
{
    u32 word = XDfeMix_ReadReg(inst, XDFEMIX_MODEL_PARAM_1_OFFSET);
    inst->Config.Mode = FIELD(word, XDFEMIX_MODEL_PARAM_1_MODE);
    inst->Config.NumAntenna = FIELD(word, XDFEMIX_MODEL_PARAM_1_NUM_ANTENNA);
    inst->Config.MaxUseableCcids = FIELD(word, XDFEMIX_MODEL_PARAM_1_MAX_USEABLE_CCIDS);
    inst->Config.Lanes = FIELD(word, XDFEMIX_MODEL_PARAM_1_LANES);
    inst->Config.AntennaInterleave = FIELD(word, XDFEMIX_MODEL_PARAM_1_ANTENNA_INTERLEAVE);
    inst->Config.MixerCps = FIELD(word, XDFEMIX_MODEL_PARAM_1_MIXER_CPS);
    inst->Config.NumAuxiliary = FIELD(word, XDFEMIX_MODEL_PARAM_1_NUM_AUXILIARY);
    word = XDfeMix_ReadReg(inst, XDFEMIX_MODEL_PARAM_2_OFFSET);
    inst->Config.DataIWidth = FIELD(word, XDFEMIX_MODEL_PARAM_2_DATA_IWIDTH);
    inst->Config.DataOWidth = FIELD(word, XDFEMIX_MODEL_PARAM_2_DATA_OWIDTH);
    inst->Config.TUserWidth = FIELD(word, XDFEMIX_MODEL_PARAM_2_TUSER_WIDTH);
}

#define DRIVER XDfeMix
#define READY XDFEMIX_STATE_READY
#define OPEN xdfe_mix_mmio_open
#define CLOSE xdfe_mix_mmio_close
#define OPEN_BUFFER xdfe_mix_mmio_open_buffer
#define MIN_SIZE 0x5000
#include "mmio_impl.h"
