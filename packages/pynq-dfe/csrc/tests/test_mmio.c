#include "xdfe_buffer.h"
#include HW_HEADER
#include <metal/io.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#define JOIN_(a,b) a##b
#define JOIN(a,b) JOIN_(a,b)
#define REG(suffix) JOIN(PREFIX,suffix)
#define API(suffix) JOIN(TYPE,suffix)

int main(void)
{
    const size_t size = 65536;
    uint32_t *regs = mmap(NULL, size, PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    assert(regs != MAP_FAILED);
    assert(!OPEN_BUFFER("test", regs, 8));
    regs[REG(_VERSION_OFFSET)/4] = 0x12345678;
    regs[REG(_RESET_OFFSET)/4] = 99;
#if defined(TEST_PRACH)
    // One antenna, CC, channel, slot, RACH channel, lane and band.
    regs[XDFEPRACH_MODEL_PARAM_OFFSET/4] = 0x41011211;
    regs[XDFEPRACH_FREQUENCY_PHASE_OFFSET/4] = 99;
#endif
#if defined(TEST_MIX)
    regs[XDFEMIX_MODEL_PARAM_1_OFFSET/4] = 4u << XDFEMIX_MODEL_PARAM_1_NUM_ANTENNA_OFFSET;
#elif defined(TEST_CCF)
    regs[XDFECCF_MODEL_PARAM_OFFSET/4] = 4u << XDFECCF_MODEL_PARAM_NUM_ANTENNA_OFFSET;
#elif defined(TEST_EQU)
    regs[XDFEEQU_MODEL_PARAM_OFFSET/4] = 4u << XDFEEQU_MODEL_PARAM_NUM_CHANNELS_OFFSET;
#endif
    TYPE *inst = OPEN_BUFFER("test", regs, size);
    assert(inst && inst->StateId == REG(_STATE_READY));
    assert(!strcmp(inst->NodeName, "test"));
    assert(regs[REG(_RESET_OFFSET)/4] == 99);
#if defined(TEST_PRACH)
    assert(inst->Config.NumBands == 1 && !regs[XDFEPRACH_FREQUENCY_PHASE_OFFSET/4]);
#endif
#if defined(TEST_MIX) || defined(TEST_CCF)
    assert(inst->Config.NumAntenna == 4);
#elif defined(TEST_EQU)
    assert(inst->Config.NumChannels == 4);
#endif
    API(_Reset)(inst);
    assert(inst->StateId == REG(_STATE_RESET));
#if defined(TEST_PRACH)
    assert(regs[REG(_RESET_OFFSET)/4] == REG(_RESET_OFF));
#else
    assert(regs[REG(_RESET_OFFSET)/4] == REG(_RESET_ON));
#endif
    API(_Cfg) cfg = {0};
    API(_Configure)(inst, &cfg);
    assert(inst->StateId == REG(_STATE_CONFIGURED));
    assert(cfg.Version.Major == 0x12 && regs[REG(_RESET_OFFSET)/4] == REG(_RESET_OFF));
    CLOSE(inst);
    assert(regs[0] == 0x12345678);
    assert(munmap(regs, size) == 0);
    // Exercise open with a non-page-aligned base above 4 GiB.
    const uint64_t base = UINT64_C(0x100000014);
    inst = OPEN("file-backed", base, size);
    assert(inst && inst->Config.BaseAddr == base);
    assert(metal_io_phys(inst->Io, 8) == base + 8);
    API(_WriteReg)(inst, 0, 0x89abcdef);
    CLOSE(inst);
    FILE *file = fopen(getenv("DFE_TEST_FILE"), "rb");
    uint32_t value;
    assert(file && fseeko(file, base, SEEK_SET) == 0);
    assert(fread(&value, sizeof(value), 1, file) == 1 && value == 0x89abcdef);
    fclose(file);
    printf("%s READY -> RESET -> CONFIGURED, version major 0x12: PASS\n", HEADER);
}
