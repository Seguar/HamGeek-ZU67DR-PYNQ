#include "xdfeprach.h"
#include "xdfeprach_hw.h"

extern u32 XDfePrach_RdBitField(u32 width, u32 offset, u32 data);
#define FIELD(word, field) XDfePrach_RdBitField(field##_WIDTH, field##_OFFSET, word)

static void load_config(XDfePrach *inst)
{
    u32 word = XDfePrach_ReadReg(inst, XDFEPRACH_MODEL_PARAM_OFFSET);
    inst->Config.NumAntenna[0] = FIELD(word, XDFEPRACH_MODEL_PARAM_NUM_ANTENNA0);
    inst->Config.NumCCPerAntenna[0] = FIELD(word, XDFEPRACH_MODEL_PARAM_NUM_CC_PER_ANTENNA0);
    inst->Config.NumAntennaChannels[0] = FIELD(word, XDFEPRACH_MODEL_PARAM_NUM_SLOT_CHANNELS0);
    inst->Config.NumAntennaSlots[0] = FIELD(word, XDFEPRACH_MODEL_PARAM_NUM_SLOTS0);
    inst->Config.NumRachLanes = FIELD(word, XDFEPRACH_MODEL_PARAM_NUM_RACH_LANES);
    inst->Config.NumRachChannels = FIELD(word, XDFEPRACH_MODEL_PARAM_NUM_RACH_CHANNELS);
    inst->Config.HasContinuousSched = FIELD(word, XDFEPRACH_MODEL_PARAM_HAS_CONTINUOUS_SCHED);
    inst->Config.HasAxisCtrl = FIELD(word, XDFEPRACH_MODEL_PARAM_HAS_AXIS_CTRL);
    inst->Config.HasIrq = FIELD(word, XDFEPRACH_MODEL_PARAM_HAS_IRQ);
    inst->Config.NumBands = FIELD(word, XDFEPRACH_MODEL_PARAM_NUM_BANDS);
    word = XDfePrach_ReadReg(inst, XDFEPRACH_MODEL_PARAM1_OFFSET);
    inst->Config.NumAntenna[1] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_ANTENNA1);
    inst->Config.NumCCPerAntenna[1] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_CC_PER_ANTENNA1);
    inst->Config.NumAntennaChannels[1] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_SLOT_CHANNELS1);
    inst->Config.NumAntennaSlots[1] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_SLOTS1);
    inst->Config.NumAntenna[2] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_ANTENNA2);
    inst->Config.NumCCPerAntenna[2] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_CC_PER_ANTENNA2);
    inst->Config.NumAntennaChannels[2] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_SLOT_CHANNELS2);
    inst->Config.NumAntennaSlots[2] = FIELD(word, XDFEPRACH_MODEL_PARAM1_NUM_SLOTS2);
    for (unsigned i = 0; i < XDFEPRACH_RC_NUM_MAX; ++i)
        XDfePrach_WriteReg(inst, XDFEPRACH_FREQUENCY_PHASE_OFFSET + i * XDFEPRACH_NCO_CTRL_ADDR_STEP, 0);
}

#define DRIVER XDfePrach
#define READY XDFEPRACH_STATE_READY
#define OPEN xdfe_prach_mmio_open
#define CLOSE xdfe_prach_mmio_close
#define OPEN_BUFFER xdfe_prach_mmio_open_buffer
#define MIN_SIZE 0x4000
#include "mmio_impl.h"
