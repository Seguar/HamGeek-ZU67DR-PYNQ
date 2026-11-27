// SPDX-License-Identifier: BSD-3-Clause
#include "mmio.h"

// PYNQ owns the mapped buffer. libmetal retains the physical address pointer.
struct xrfdc_mapping {
    struct metal_io_region io;
    metal_phys_addr_t phys;
};

struct xrfdc_mapping *xrfdc_attach(XRFdc *instance, XRFdc_Config *config,
                                   void *base, size_t length)
{
    if (!base || length < XRFDC_REGION_SIZE)
        return NULL;
    struct xrfdc_mapping *mapping = calloc(1, sizeof(*mapping));
    if (!mapping)
        return NULL;
    mapping->phys = config->BaseAddr;
    metal_io_init(&mapping->io, base, &mapping->phys, length, (unsigned)-1, 0, NULL);
    instance->io = &mapping->io;
    if (XRFdc_CfgInitialize(instance, config) != XRFDC_SUCCESS) {
        instance->io = NULL;
        xrfdc_detach(mapping);
        return NULL;
    }
    return mapping;
}

void xrfdc_detach(struct xrfdc_mapping *mapping)
{
    metal_io_finish(&mapping->io);
    free(mapping);
}

// The archive is private to this library. Direct MMIO needs no device discovery.
__attribute__((constructor)) static void xrfdc_logging(void)
{
    metal_set_log_handler(metal_default_log_handler);
    metal_set_log_level(METAL_LOG_WARNING);
}
