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
add_files [glob $src/*.v]
create_bd_design dfe_equ
set_param general.maxThreads 4
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
ip equalizer xdfe_equalizer:1.0 CONFIG.NUM_CHANNELS 1 CONFIG.SAMPLE_WIDTH 16 CONFIG.COMPLEX_MODE true CONFIG.NUM_TAPS 4 CONFIG.TUSER_WIDTH 1 CONFIG.MAX_SAMPLE_RATE 100.0
create_bd_cell -type module -reference pattern_frame frame
ip dma axi_dma:7.1 CONFIG.c_include_sg 0 CONFIG.c_addr_width 40 CONFIG.c_m_axi_mm2s_data_width 128 CONFIG.c_m_axi_s2mm_data_width 128 CONFIG.c_m_axis_mm2s_tdata_width 32 CONFIG.c_s_axis_s2mm_tdata_width 32 CONFIG.c_sg_length_width 16
ip ctrl smartconnect:1.0 CONFIG.NUM_SI 1 CONFIG.NUM_MI 2
ip mem smartconnect:1.0 CONFIG.NUM_SI 2 CONFIG.NUM_MI 1
bus zynq_ultra_ps_e_0/M_AXI_HPM0_LPD ctrl/S00_AXI
bus ctrl/M00_AXI dma/S_AXI_LITE
bus ctrl/M01_AXI equalizer/S_AXI_CTRL
bus dma/M_AXI_MM2S mem/S00_AXI
bus dma/M_AXI_S2MM mem/S01_AXI
bus mem/M00_AXI zynq_ultra_ps_e_0/S_AXI_HP0_FPD
assign_bd_address
ip rst proc_sys_reset:5.0 CONFIG.C_EXT_RESET_HIGH 0 CONFIG.C_AUX_RESET_HIGH 1
ip one xlconstant:1.1
ip zero xlconstant:1.1 CONFIG.CONST_VAL 0
ip keep xlconstant:1.1 CONFIG.CONST_WIDTH 4 CONFIG.CONST_VAL 15
wire zynq_ultra_ps_e_0/pl_clk0 zynq_ultra_ps_e_0/maxihpm0_lpd_aclk zynq_ultra_ps_e_0/saxihp0_fpd_aclk rst/slowest_sync_clk ctrl/aclk mem/aclk dma/s_axi_lite_aclk dma/m_axi_mm2s_aclk dma/m_axi_s2mm_aclk equalizer/s_axi_aclk equalizer/s_axis_aclk frame/clk
wire zynq_ultra_ps_e_0/pl_resetn0 rst/ext_reset_in
wire one/dout rst/dcm_locked equalizer/s_axis_din_tvalid
wire zero/dout rst/aux_reset_in rst/mb_debug_sys_rst equalizer/s_axis_din_tlast
wire rst/peripheral_aresetn ctrl/aresetn mem/aresetn dma/axi_resetn equalizer/s_axi_aresetn equalizer/s_axis_aresetn frame/resetn
foreach {src dst} {
    dma/m_axis_mm2s_tdata frame/tx_data
    dma/m_axis_mm2s_tvalid frame/tx_valid
    dma/m_axis_mm2s_tlast frame/tx_last
    frame/tx_ready dma/m_axis_mm2s_tready
    frame/eq_in equalizer/s_axis_din_tdata
    frame/trigger equalizer/s_axis_din_tuser
    equalizer/s_axis_din_tready frame/eq_ready
    equalizer/m_axis_dout_tdata frame/eq_out
    equalizer/m_axis_dout_tvalid frame/eq_valid
    frame/rx_data dma/s_axis_s2mm_tdata
    frame/rx_valid dma/s_axis_s2mm_tvalid
    frame/rx_last dma/s_axis_s2mm_tlast
    dma/s_axis_s2mm_tready frame/rx_ready
    keep/dout dma/s_axis_s2mm_tkeep
} {wire $src $dst}
validate_bd_design
save_bd_design
set bd [get_files dfe_equ.bd]
add_files [make_wrapper -files $bd -top]
set_property top dfe_equ_wrapper [current_fileset]
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
file copy [lindex [glob work/dfe.runs/impl_1/*.bit] 0] dfe_equ.bit
file copy work/dfe.gen/sources_1/bd/dfe_equ/hw_handoff/dfe_equ.hwh .
write_hw_platform -fixed -include_bit -force dfe_equ.xsa
set manifest [open artifacts.sha256 w]
puts $manifest [exec sha256sum dfe_equ.bit dfe_equ.hwh dfe_equ.xsa]
close $manifest
puts "DFE_BUILD_PASS WNS=$wns WHS=$whs"
