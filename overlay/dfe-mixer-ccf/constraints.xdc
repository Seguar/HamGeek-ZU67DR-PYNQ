# SPDX-License-Identifier: BSD-3-Clause
# rowtiming250 pin and timing constraints (HamGeek XCZU67DR PCIe V1).
# Single 250 MHz reference: LMK04828 VCO 3000 MHz /12 on every clock output;
# SYSREF 3000/480 = 6.25 MHz (analog DAC SYSREF on SDCLKout7, PL SYSREF on SDCLKout11).

# PL clock (LMK DCLKout8) and PL SYSREF (LMK SDCLKout11), bank 67
set_property -dict {PACKAGE_PIN E12 IOSTANDARD LVDS} [get_ports pl_refclk_p]
set_property -dict {PACKAGE_PIN D12 IOSTANDARD LVDS} [get_ports pl_refclk_n]
set_property -dict {PACKAGE_PIN E14 IOSTANDARD LVDS} [get_ports pl_sysref_p]
set_property -dict {PACKAGE_PIN D14 IOSTANDARD LVDS} [get_ports pl_sysref_n]
create_clock -name lmk_pl -period 4.000 [get_ports pl_refclk_p]

# RFDC tile references (LMK DCLKout2 -> ADC 226, DCLKout12 -> DAC 228)
create_clock -name lmk_adc226_ref -period 4.000 [get_ports adc2_clk_0_clk_p]
create_clock -name lmk_dac228_ref -period 4.000 [get_ports dac1_clk_0_clk_p]
# PL SYSREF arrival at the pins. The LMK profile delays SDCLKout11 by 4 VCO cycles
# (SDCLKout11_DDLY code 3) against DCLKout8: 4 x 0.333 ns - 0.08 ns = 1.25 ns [CALC],
# which centres the IOB capture window of the deskewed 250 MHz clock.
# Board and output skew budget +-0.4 ns [ASSUMED]; trim with the LMK on the bench.
set_input_delay -clock lmk_pl -min 0.850 [get_ports pl_sysref_p]
set_input_delay -clock lmk_pl -max 1.650 [get_ports pl_sysref_p]

# Host (PS pl_clk0, 100 MHz) <-> fabric clocks: quasi-static configuration registers,
# toggle/2-FF synchronizers and XPM FIFOs. Bound the data path instead of cutting it,
# so XPM's own (more specific) CDC constraints still apply.
set c312 [get_clocks -of_objects [get_pins -hierarchical -filter {NAME =~ *clk_gen*/mmcm/CLKOUT1}]]
set c625 [get_clocks -of_objects [get_pins -hierarchical -filter {NAME =~ *clk_gen*/mmcm/CLKOUT0}]]
set_max_delay -datapath_only 3.200 -from [get_clocks clk_pl_0] -to $c312
set_max_delay -datapath_only 3.200 -from $c312 -to [get_clocks clk_pl_0]
set_max_delay -datapath_only 3.200 -from [get_clocks clk_pl_0] -to $c625
set_max_delay -datapath_only 3.200 -from $c625 -to [get_clocks clk_pl_0]

# The MMCM outputs exchange data synchronously (250 -> 62.5 -> 312.5 -> 625 MHz):
# match their insertion delays.
set_property CLOCK_DELAY_GROUP rt250_mmcm [get_nets -of_objects [get_pins -hierarchical -filter {NAME =~ *clk_gen*/c625_bufg/O || NAME =~ *clk_gen*/c312_bufg/O || NAME =~ *clk_gen*/c250_bufg/O || NAME =~ *clk_gen*/c62_bufg/O}]]
