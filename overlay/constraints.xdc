# SPDX-License-Identifier: BSD-3-Clause
create_clock -name lmk_adc2_ref -period 4.069 [get_ports adc2_clk_0_clk_p]

# The command and completion bits cross unrelated clock domains through
# two-stage synchronizers. Keep the path between stages timed.
set first_stage [get_cells -hierarchical -regexp {.*snapshot.*/(command_sync|done_sync)_reg\[0\]}]
set_false_path -to [get_pins -of_objects $first_stage -filter {REF_PIN_NAME == D}]
