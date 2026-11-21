# SPDX-License-Identifier: BSD-3-Clause
# Usage: vivado -mode batch -source build.tcl -tclargs /path/to/vendor-ps.tcl
if {[version -short] ne "2025.2"} {error "Vivado 2025.2 required"}
cd [file dirname [file normalize [info script]]]
if {[llength $argv] != 1} {error "Pass the board PS preset Tcl path"}
source [lindex $argv 0]
if {$part ne "xczu67dr-fsve1156-2-i"} { error "Wrong card PS preset" }
create_project -force adc00 ./work -part $part
add_files capture.v
add_files -fileset constrs_1 constraints.xdc
set_property PROCESSING_ORDER LATE [get_files constraints.xdc]
set_property USED_IN_SYNTHESIS false [get_files constraints.xdc]
create_bd_design adc00
set ps [create_bd_cell -type ip -vlnv $ps_ip zynq_ultra_ps_e_0]
set_property -dict $vendor_config $ps
set_property -dict [list CONFIG.PSU__USE__M_AXI_GP0 0 CONFIG.PSU__USE__M_AXI_GP1 0 CONFIG.PSU__USE__M_AXI_GP2 1 CONFIG.PSU__USE__IRQ0 0 CONFIG.PSU__GPIO_EMIO__PERIPHERAL__ENABLE 0] $ps

set rf [create_bd_cell -type ip -vlnv xilinx.com:ip:usp_rf_data_converter:2.6 rfdc]
# Tile 224 lacks a clock input. Enable the donor on tile 226 before requesting
# tile 224, so Vivado can expose the forwarded-clock route.
set_property CONFIG.ADC_Slice20_Enable true $rf
set_property -dict {
    CONFIG.ADC2_PLL_Enable true
    CONFIG.ADC2_Refclk_Freq 245.760
    CONFIG.ADC2_Sampling_Rate 4.9152
    CONFIG.ADC2_Clock_Dist 2
    CONFIG.ADC2_Outclk_Freq 307.200
    CONFIG.ADC_Decimation_Mode20 2
    CONFIG.ADC_Data_Width20 8
} $rf

set_property -dict {
    CONFIG.ADC_Slice10_Enable true
    CONFIG.ADC1_Clock_Source 2
    CONFIG.ADC1_Refclk_Freq 2457.600
    CONFIG.ADC1_Sampling_Rate 2.4576
    CONFIG.ADC1_Outclk_Freq 307.200
    CONFIG.ADC_Decimation_Mode10 1
    CONFIG.ADC_Mixer_Type10 1
} $rf
set_property -dict {
    CONFIG.ADC_Slice00_Enable true
    CONFIG.ADC0_Clock_Source 2
    CONFIG.ADC0_Refclk_Freq 2457.600
    CONFIG.ADC0_Sampling_Rate 2.4576
    CONFIG.ADC0_Outclk_Freq 307.200
    CONFIG.ADC_Data_Type00 0
    CONFIG.ADC_Data_Width00 8
    CONFIG.ADC_Decimation_Mode00 1
    CONFIG.ADC_Mixer_Type00 1
} $rf
puts "RFDC_PINS [get_bd_pins rfdc/*]"
foreach port {adc2_clk vin00 vin10 vin2_01 sysref_in} {
    set pin [get_bd_intf_pins -quiet rfdc/$port]
    if {[llength $pin] != 1} {error "Missing RFDC input $port"}
    make_bd_intf_pins_external $pin
}

set_property CONFIG.FREQ_HZ 245760000 [get_bd_intf_ports adc2_clk_0]

set gpio [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 command_status]
set_property -dict {CONFIG.C_IS_DUAL 1 CONFIG.C_GPIO_WIDTH 1 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_GPIO2_WIDTH 32 CONFIG.C_ALL_INPUTS_2 1} $gpio
set ram [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_bram_ctrl:4.1 sample_buffer]
set_property -dict {CONFIG.DATA_WIDTH 32 CONFIG.SINGLE_PORT_BRAM 1 CONFIG.PROTOCOL AXI4LITE} $ram
create_bd_cell -type module -reference capture snapshot
set ps_clk zynq_ultra_ps_e_0/pl_clk0
set ps_rst zynq_ultra_ps_e_0/pl_resetn0
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 axi_fabric
set_property -dict {CONFIG.NUM_MI 3 CONFIG.NUM_SI 1} [get_bd_cells axi_fabric]
connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/M_AXI_HPM0_LPD] [get_bd_intf_pins axi_fabric/S00_AXI]
foreach {port cell} {M00_AXI rfdc/s_axi M01_AXI command_status/S_AXI M02_AXI sample_buffer/S_AXI} {
    connect_bd_intf_net [get_bd_intf_pins axi_fabric/$port] [get_bd_intf_pins $cell]
}
proc wire {args} {
    connect_bd_net {*}[lmap pin $args {get_bd_pins $pin}]
}
wire $ps_clk zynq_ultra_ps_e_0/maxihpm0_lpd_aclk axi_fabric/aclk rfdc/s_axi_aclk command_status/s_axi_aclk sample_buffer/s_axi_aclk snapshot/host_clk
wire $ps_rst axi_fabric/aresetn rfdc/s_axi_aresetn command_status/s_axi_aresetn sample_buffer/s_axi_aresetn snapshot/host_resetn
create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 adc_reset
set_property -dict {CONFIG.C_AUX_RESET_HIGH 1} [get_bd_cells adc_reset]
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 one
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 zero
set_property CONFIG.CONST_VAL 0 [get_bd_cells zero]
wire $ps_rst adc_reset/ext_reset_in
wire one/dout adc_reset/dcm_locked
wire zero/dout adc_reset/aux_reset_in adc_reset/mb_debug_sys_rst
wire rfdc/clk_adc0 rfdc/m0_axis_aclk snapshot/adc_clk adc_reset/slowest_sync_clk
wire adc_reset/peripheral_aresetn rfdc/m0_axis_aresetn snapshot/adc_resetn
wire rfdc/m00_axis_tdata snapshot/sample_data
wire rfdc/m00_axis_tvalid snapshot/sample_valid
wire one/dout rfdc/m00_axis_tready
foreach tile {1 2} {
    set reset_tile [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 reset_adc${tile}]
    wire $ps_rst $reset_tile/ext_reset_in
    wire one/dout $reset_tile/dcm_locked
    wire zero/dout $reset_tile/aux_reset_in $reset_tile/mb_debug_sys_rst
    wire rfdc/clk_adc${tile} rfdc/m${tile}_axis_aclk $reset_tile/slowest_sync_clk
    wire $reset_tile/peripheral_aresetn rfdc/m${tile}_axis_aresetn
    foreach stream {0 1 2 3} {
        if {[llength [get_bd_pins -quiet rfdc/m${tile}${stream}_axis_tready]]} {
            wire one/dout rfdc/m${tile}${stream}_axis_tready
        }
    }
}
wire command_status/gpio_io_o snapshot/command
wire snapshot/status command_status/gpio2_io_i
wire sample_buffer/bram_addr_a snapshot/read_addr
wire sample_buffer/bram_en_a snapshot/read_en
wire snapshot/read_data sample_buffer/bram_rddata_a

set space [get_bd_addr_spaces zynq_ultra_ps_e_0/Data]
foreach {cell offset range} {rfdc 0x82000000 256K command_status 0x82040000 64K sample_buffer 0x82050000 64K} {
    set segment [get_bd_addr_segs -of_objects [get_bd_intf_pins -quiet [list $cell/*AXI $cell/s_axi]]]
    if {[llength $segment] != 1} { error "Could not determine address segment for $cell: $segment" }
    assign_bd_address -offset $offset -range $range -target_address_space $space $segment
}
validate_bd_design
save_bd_design
report_property $rf
foreach tile {0 1 2} {
    if {abs([get_property CONFIG.ADC${tile}_Fabric_Freq $rf] - 307.2) > 0.001} {
        error "Unexpected tile ${tile} AXI clock requirement"
    }
}
make_wrapper -files [get_files */adc00.bd] -top
add_files [glob ./work/adc00.gen/sources_1/bd/adc00/hdl/adc00_wrapper.*]
set_property top adc00_wrapper [current_fileset]
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation did not finish"}
open_run impl_1
if {[llength [get_cells -hierarchical -regexp {.*snapshot.*/(command_sync|done_sync)_reg\[0\]}]] != 2} {error "Capture synchronizer endpoints changed"}
report_exceptions -file exceptions.txt
report_timing_summary -file timing.txt
report_drc -file drc.txt
report_route_status -file route.txt
report_cdc -details -file cdc.txt
if {[get_property SLACK [lindex [get_timing_paths -max_paths 1] 0]] < 0} {error "Negative setup slack"}
if {[get_property SLACK [lindex [get_timing_paths -hold -max_paths 1] 0]] < 0} {error "Negative hold slack"}
file mkdir output
file copy -force [lindex [glob ./work/adc00.runs/impl_1/*.bit] 0] output/adc00.bit
file copy -force ./work/adc00.gen/sources_1/bd/adc00/hw_handoff/adc00.hwh output/adc00.hwh
puts ADC00_BUILD_PASS
