# SPDX-License-Identifier: BSD-3-Clause
if {[version -short] ne "2025.2"} {error "Requires Vivado 2025.2"}
if {[llength $argv] != 2} {error "Provide the r5 vendor PS Tcl and a new output directory"}
set src [file dirname [file normalize [info script]]]
set preset [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
file mkdir $out
cd $out
if {[lindex [exec sha256sum $preset] 0] ne "05658b13f43acd66fa3a9b24c0bd484c0187d5a5edb4739dc1157fc3cb1c5b21"} {error "Expected the archived r5 PS preset"}
source $preset
create_project dfe ./work -part $part
if {[info exists ::env(DFE_IP_CACHE)]} {config_ip_cache -use_cache_location $::env(DFE_IP_CACHE)}
set_param general.maxThreads 4
add_files $src/symbol_io.v
create_bd_design dfe_ofdm
# SPDX-License-Identifier: BSD-3-Clause
set ps [create_bd_cell -type ip -vlnv $ps_ip zynq_ultra_ps_e_0]
set_property -dict $vendor_config $ps
set_property -dict [list CONFIG.PSU__USE__M_AXI_GP0 0 CONFIG.PSU__USE__M_AXI_GP1 0 CONFIG.PSU__USE__M_AXI_GP2 1 \
    CONFIG.PSU__USE__S_AXI_GP2 1 CONFIG.PSU__SAXIGP2__DATA_WIDTH 128 \
    CONFIG.PSU__USE__IRQ0 0 CONFIG.PSU__GPIO_EMIO__PERIPHERAL__ENABLE 0] $ps

proc ip {inst core args} {
    set def [get_ipdefs xilinx.com:ip:$core]
    if {[llength $def] != 1 || [get_property REQUIRES_LICENSE $def] || [get_property LICENSE_KEYS $def] ne ""} {error "Unavailable or separately licensed: $core"}
    set cell [create_bd_cell -type ip -vlnv $def $inst]
    if {[llength $args]} {set_property -dict $args $cell}
}
proc wire {args} {connect_bd_net {*}[lmap p $args {get_bd_pins $p}]}
proc bus {a b} {connect_bd_intf_net [get_bd_intf_pins $a] [get_bd_intf_pins $b]}
foreach {name mode} {dl DL ul UL} {
    ip $name xdfe_ofdm:2.2 CONFIG.OFDM_TYPE $mode CONFIG.NUM_ANTENNA 2 CONFIG.ANTENNA_INTERLEAVE 1 CONFIG.RE_ORDER 0 CONFIG.PHASE_COMPENSATION 0
}
create_bd_cell -type module -reference symbol_io io
ip arm axi_gpio:2.0 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_GPIO_WIDTH 1
ip clk96 clk_wiz:6.0 CONFIG.CLKOUT1_REQUESTED_OUT_FREQ 96.000 CONFIG.USE_RESET false
ip clk491 clk_wiz:6.0 CONFIG.PRIM_IN_FREQ 96.000 CONFIG.CLKOUT1_REQUESTED_OUT_FREQ 491.520 CONFIG.USE_RESET false
ip fast_reset proc_sys_reset:5.0 CONFIG.C_AUX_RESET_HIGH 1 CONFIG.C_EXT_RESET_HIGH 0
foreach name {load_fifo capture_fifo} {
    ip $name axis_data_fifo:2.0 CONFIG.IS_ACLK_ASYNC 1 CONFIG.FIFO_DEPTH 2048 CONFIG.TDATA_NUM_BYTES 8 CONFIG.HAS_TLAST 1
}
ip dma axi_dma:7.1 CONFIG.c_include_sg 0 CONFIG.c_addr_width 40 CONFIG.c_m_axi_mm2s_data_width 128 CONFIG.c_m_axis_mm2s_tdata_width 64 CONFIG.c_m_axi_s2mm_data_width 128 CONFIG.c_s_axis_s2mm_tdata_width 64
ip one xlconstant:1.1
ip zero xlconstant:1.1 CONFIG.CONST_VAL 0
ip reset proc_sys_reset:5.0 CONFIG.C_AUX_RESET_HIGH 1 CONFIG.C_EXT_RESET_HIGH 0
ip lite smartconnect:1.0 CONFIG.NUM_SI 1 CONFIG.NUM_MI 4
ip mem smartconnect:1.0 CONFIG.NUM_SI 2 CONFIG.NUM_MI 1
bus zynq_ultra_ps_e_0/M_AXI_HPM0_LPD lite/S00_AXI
bus lite/M00_AXI dma/S_AXI_LITE
bus lite/M01_AXI dl/S_AXI_CTRL
bus lite/M02_AXI ul/S_AXI_CTRL
bus lite/M03_AXI arm/S_AXI
bus dma/M_AXI_MM2S mem/S00_AXI
bus dma/M_AXI_S2MM mem/S01_AXI
bus mem/M00_AXI zynq_ultra_ps_e_0/S_AXI_HP0_FPD
wire zynq_ultra_ps_e_0/pl_clk0 reset/slowest_sync_clk lite/aclk mem/aclk zynq_ultra_ps_e_0/maxihpm0_lpd_aclk zynq_ultra_ps_e_0/saxihp0_fpd_aclk dma/s_axi_lite_aclk dma/m_axi_mm2s_aclk dma/m_axi_s2mm_aclk arm/s_axi_aclk dl/s_axi_aclk ul/s_axi_aclk clk96/clk_in1 load_fifo/s_axis_aclk capture_fifo/m_axis_aclk
wire zynq_ultra_ps_e_0/pl_resetn0 reset/ext_reset_in fast_reset/ext_reset_in
wire one/dout reset/dcm_locked dl/s_axis_tbase_tvalid
wire zero/dout reset/aux_reset_in reset/mb_debug_sys_rst fast_reset/aux_reset_in fast_reset/mb_debug_sys_rst
wire reset/peripheral_aresetn lite/aresetn mem/aresetn dma/axi_resetn arm/s_axi_aresetn dl/s_axi_aresetn ul/s_axi_aresetn load_fifo/s_axis_aresetn
wire clk96/clk_out1 clk491/clk_in1
wire clk491/locked fast_reset/dcm_locked
wire clk491/clk_out1 fast_reset/slowest_sync_clk dl/s_axis_aclk ul/s_axis_aclk io/clk load_fifo/m_axis_aclk capture_fifo/s_axis_aclk
wire fast_reset/peripheral_aresetn dl/s_axis_aresetn ul/s_axis_aresetn io/resetn capture_fifo/s_axis_aresetn
wire arm/gpio_io_o io/capture_request
wire io/frame dl/s_axis_tbase_tuser
ip zero8 xlconstant:1.1 CONFIG.CONST_VAL 0 CONFIG.CONST_WIDTH 8
wire zero8/dout dl/s_axis_dl_din_tid
bus dma/M_AXIS_MM2S load_fifo/S_AXIS
bus capture_fifo/M_AXIS dma/S_AXIS_S2MM
foreach {field suffix} {data tdata valid tvalid last tlast ready tready} {
    wire load_fifo/m_axis_$suffix io/load_$field
    wire io/ft_$field dl/s_axis_dl_din_$suffix
    wire ul/m_axis_ul_dout_$suffix io/ul_$field
    wire io/capture_$field capture_fifo/s_axis_$suffix
}
foreach suffix {tdata tvalid tid tuser} {
    wire dl/m_axis_dl_dout_$suffix ul/s_axis_ul_din_$suffix
}
assign_bd_address
validate_bd_design
save_bd_design
set bd [get_files dfe_ofdm.bd]
add_files [make_wrapper -files $bd -top]
set_property top dfe_ofdm_wrapper [current_fileset]
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
file mkdir run
report_timing_summary -report_unconstrained -max_paths 3 -file run/timing.rpt
report_utilization -file run/utilization.rpt
report_route_status -file run/route.rpt
report_cdc -details -file run/cdc.rpt
report_methodology -file run/methodology.rpt
report_drc -file run/drc.rpt
set wns [get_property SLACK [get_timing_paths -setup -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -hold -max_paths 1]]
if {$wns < 0 || $whs < 0} {error "WNS=$wns WHS=$whs"}
file copy [lindex [glob work/dfe.runs/impl_1/*.bit] 0] dfe_ofdm.bit
file copy work/dfe.gen/sources_1/bd/dfe_ofdm/hw_handoff/dfe_ofdm.hwh .
write_hw_platform -fixed -include_bit -force dfe_ofdm.xsa
set manifest [open artifacts.sha256 w]
puts $manifest [exec sha256sum dfe_ofdm.bit dfe_ofdm.hwh dfe_ofdm.xsa]
close $manifest
puts "DFE_BUILD_PASS WNS=$wns WHS=$whs"
