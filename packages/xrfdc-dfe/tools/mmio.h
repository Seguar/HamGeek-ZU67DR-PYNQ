// SPDX-License-Identifier: BSD-3-Clause
#include "xrfdc.h"

struct xrfdc_mapping;
struct xrfdc_mapping *xrfdc_attach(XRFdc *instance, XRFdc_Config *config,
                                   void *base, size_t length);
void xrfdc_detach(struct xrfdc_mapping *mapping);
