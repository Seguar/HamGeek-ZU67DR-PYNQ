/* SPDX-License-Identifier: BSD-3-Clause */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#include <metal/io.h>
#include <xrfdc.h>

#include "adc_rfdc_config.h"

_Static_assert(RFDC_MMIO_SPAN >= XRFDC_REGION_SIZE, "RFDC register window is too small");

struct options {
    int tile;
    int block;
    unsigned zone;
    unsigned cal_mode;
};

static void usage(FILE *stream)
{
    fputs("Usage: adc-nyquist --get\n"
          "       adc-nyquist --set 1|2 [--tile 0..3 --block 0..3] [--cal-mode 1|2]\n"
          "       adc-nyquist --cal-mode 1|2 [--tile 0..3 --block 0..3]\n"
          "\n"
          "Zones 1 and 2 select odd and even Nyquist zones. Setters without a\n"
          "selector apply to all enabled analog ADC blocks. --cal-mode reruns\n"
          "foreground calibration on each selected tile. Mute its RF inputs\n"
          "and stop capture before using --cal-mode.\n",
          stream);
}

static int parse_options(int argc, char **argv, struct options *options)
{
    if (argc == 2 && strcmp(argv[1], "--get") == 0)
        return 0;

    for (int i = 1; i + 1 < argc; i += 2) {
        const char *value = argv[i + 1];
        if (value[0] < '0' || value[0] > '3' || value[1] != '\0')
            return -1;
        int number = value[0] - '0';

        if (strcmp(argv[i], "--set") == 0 && !options->zone && number >= 1 && number <= 2)
            options->zone = number;
        else if (strcmp(argv[i], "--cal-mode") == 0 && !options->cal_mode && number >= 1 && number <= 2)
            options->cal_mode = number;
        else if (strcmp(argv[i], "--tile") == 0 && options->tile < 0)
            options->tile = number;
        else if (strcmp(argv[i], "--block") == 0 && options->block < 0)
            options->block = number;
        else
            return -1;
    }

    if (argc % 2 == 0 || (!options->zone && !options->cal_mode) ||
        ((options->tile < 0) != (options->block < 0)))
        return -1;
    return 0;
}

static int select_blocks(XRFdc *rfdc, const struct options *options, unsigned *selected)
{
    for (int tile = 0; tile < 4; ++tile) {
        if (options->tile >= 0 && tile != options->tile)
            continue;
        XRFdc_ADCTile_Config *tile_config = &config.ADCTile_Config[tile];
        for (int block = 0; block < 4; ++block) {
            if (options->block >= 0 && block != options->block)
                continue;
            int expected = tile_config->Enable && block < (int)tile_config->NumSlices &&
                           tile_config->ADCBlock_Analog_Config[block].BlockAvailable;
            int enabled = XRFdc_CheckBlockEnabled(rfdc, XRFDC_ADC_TILE, tile, block) == XRFDC_SUCCESS;
            if (enabled != expected) {
                fprintf(stderr, "ADC%d%d: live analog enable (%d) differs from the HWH (%d)\n",
                        tile, block, enabled, expected);
                return -1;
            }
            if (enabled)
                selected[tile] |= 1U << block;
        }
    }
    if (!(selected[0] | selected[1] | selected[2] | selected[3])) {
        fputs("No enabled ADC blocks match the selection\n", stderr);
        return -1;
    }
    return 0;
}

static int operate_tile(XRFdc *rfdc, const struct options *options, int tile, unsigned blocks)
{
    for (unsigned block = 0; block < 4; ++block) {
        if (!(blocks & (1U << block)))
            continue;
        if (options->cal_mode &&
            XRFdc_SetCalibrationMode(rfdc, tile, block, options->cal_mode) != XRFDC_SUCCESS) {
            fprintf(stderr, "ADC%d%u: SetCalibrationMode failed\n", tile, block);
            return -1;
        }
        if (options->zone &&
            XRFdc_SetNyquistZone(rfdc, XRFDC_ADC_TILE, tile, block, options->zone) != XRFDC_SUCCESS) {
            fprintf(stderr, "ADC%d%u: SetNyquistZone failed\n", tile, block);
            return -1;
        }
    }

    if (options->cal_mode &&
        XRFdc_CustomStartUp(rfdc, XRFDC_ADC_TILE, tile, XRFDC_STATE_CAL, XRFDC_STATE_FULL) != XRFDC_SUCCESS) {
        fprintf(stderr, "ADC tile %d: foreground calibration restart failed\n", tile);
        return -1;
    }

    for (unsigned block = 0; block < 4; ++block) {
        if (!(blocks & (1U << block)))
            continue;
        u32 zone;
        u8 cal_mode;
        if (XRFdc_GetNyquistZone(rfdc, XRFDC_ADC_TILE, tile, block, &zone) != XRFDC_SUCCESS ||
            XRFdc_GetCalibrationMode(rfdc, tile, block, &cal_mode) != XRFDC_SUCCESS) {
            fprintf(stderr, "ADC%d%u: RFDC readback failed\n", tile, block);
            return -1;
        }
        printf("ADC%d%u zone %u cal-mode %u%s\n", tile, block, zone, (unsigned)cal_mode,
               cal_mode == XRFDC_CALIB_MODE_AUTO ? " (AutoCal)" : "");
        if (options->zone && zone != options->zone) {
            fprintf(stderr, "ADC%d%u: requested zone %u, read %u\n", tile, block, options->zone, zone);
            return -1;
        }
        if (options->cal_mode && cal_mode != options->cal_mode) {
            fprintf(stderr, "ADC%d%u: requested cal-mode %u, read %u\n",
                    tile, block, options->cal_mode, (unsigned)cal_mode);
            return -1;
        }
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        usage(stdout);
        return 0;
    }
    struct options options = {.tile = -1, .block = -1};
    if (parse_options(argc, argv, &options) != 0) {
        usage(stderr);
        return 2;
    }

    int writes = options.zone || options.cal_mode;
    int fd = open("/dev/mem", (writes ? O_RDWR : O_RDONLY) | O_SYNC | O_CLOEXEC);
    if (fd < 0) {
        perror("open /dev/mem for RFDC");
        return 1;
    }
    int prot = writes ? PROT_READ | PROT_WRITE : PROT_READ;
    void *base = mmap(NULL, RFDC_MMIO_SPAN, prot, MAP_SHARED, fd, config.BaseAddr);
    if (base == MAP_FAILED)
        perror("map RFDC registers");
    close(fd);
    if (base == MAP_FAILED)
        return 1;

    struct metal_io_region io;
    XRFdc rfdc = {0};
    metal_io_init(&io, base, &config.BaseAddr, RFDC_MMIO_SPAN, (unsigned)-1, 0, NULL);
    rfdc.io = &io;

    int result = 1;
    if (XRFdc_CfgInitialize(&rfdc, &config) != XRFDC_SUCCESS) {
        fputs("RFDC driver initialization failed\n", stderr);
        goto done;
    }

    unsigned selected[4] = {0};
    if (select_blocks(&rfdc, &options, selected) != 0)
        goto done;
    for (int tile = 0; tile < 4; ++tile) {
        if (selected[tile] && operate_tile(&rfdc, &options, tile, selected[tile]) != 0)
            goto done;
    }
    result = 0;

done:
    munmap(base, RFDC_MMIO_SPAN);
    return result;
}
