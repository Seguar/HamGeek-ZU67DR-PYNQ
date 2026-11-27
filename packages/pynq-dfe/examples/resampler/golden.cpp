// Build with the PG392 v1.0 bit-accurate C model on x86-64.
// stdin/stdout hold signed 16-bit little-endian I,Q pairs.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "xdfe_resampler_v1_0_bitacc_cmodel.h"

int main(int argc, char** argv) {
    if (argc != 2) return 1;
    bool uplink = std::strcmp(argv[1], "dec") == 0;
    if (!uplink && std::strcmp(argv[1], "intp") != 0) return 1;
    xdfe_resampler_v1_0_config config;
    xdfe_resampler_v1_0_default_config(&config);
    config.sample_width = 16;
    config.resample_mode = uplink ? XDFE_RESAMPLER_V1_0_RESAMPLER_MODE_UL
                                  : XDFE_RESAMPLER_V1_0_RESAMPLER_MODE_DL;
    config.rate_change = uplink ? XDFE_RESAMPLER_V1_0_RATE_CHANGE_UL_2_3
                                : XDFE_RESAMPLER_V1_0_RATE_CHANGE_DL_2;
    auto model = xdfe_resampler_v1_0_create(&config, nullptr, nullptr);
    if (!model) return 2;
    std::vector<int16_t> iq;
    int16_t sample;
    while (std::fread(&sample, sizeof(sample), 1, stdin)) iq.push_back(sample);
    if (iq.empty() || iq.size() % (uplink ? 6 : 2)) return 3;
    auto input = xip_array_complex_create();
    auto output = xip_array_complex_create();
    if (xip_array_complex_reserve_dim(input, 1) ||
        xip_array_complex_reserve_data(input, iq.size() / 2)) return 4;
    input->dim_size = 1;
    input->dim[0] = input->data_size = iq.size() / 2;
    for (size_t i = 0; i < input->data_size; ++i) {
        input->data[i].re = iq[2*i];
        input->data[i].im = iq[2*i+1];
    }
    xdfe_resampler_v1_0_status status;
    if (xdfe_resampler_v1_0_do(model, input, output, &status) ||
        status.ouflow_re >= 0 || status.ouflow_im >= 0) return 5;
    for (size_t i = 0; i < output->data_size; ++i) {
        int16_t pair[] = {int16_t(output->data[i].re), int16_t(output->data[i].im)};
        if (std::fwrite(pair, sizeof(pair), 1, stdout) != 1) return 6;
    }
    xip_array_complex_destroy(input);
    xip_array_complex_destroy(output);
    return xdfe_resampler_v1_0_destroy(model);
}
