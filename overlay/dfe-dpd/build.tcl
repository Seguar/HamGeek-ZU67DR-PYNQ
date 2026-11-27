# SPDX-License-Identifier: BSD-3-Clause
if {[version -short] ne "2025.2" || [llength $argv] != 2} {error "Use Vivado 2025.2, vendor-ps.tcl and a new output directory"}
set_param general.maxThreads 4
set src [file dirname [file normalize [info script]]]
set preset [file normalize [lindex $argv 0]]
if {[lindex [exec sha256sum $preset] 0] ne "05658b13f43acd66fa3a9b24c0bd484c0187d5a5edb4739dc1157fc3cb1c5b21"} {error "Unexpected PS preset"}
file mkdir [lindex $argv 1]
cd [lindex $argv 1]
source $preset
create_project dfe ./work -part $part
add_files $src/frame_engine.v
create_bd_design dfe_dpd
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
create_bd_cell -type module -reference frame_engine frame
ip nlf xdfe_nlf:1.1 CONFIG.NUM_PHASES 1 CONFIG.NUM_NLFs 1 CONFIG.LUT_AXIS_EN 0
ip pa xdfe_nlf:1.1 CONFIG.NUM_PHASES 1 CONFIG.NUM_NLFs 1 CONFIG.LUT_AXIS_EN 0
ip dma axi_dma:7.1 CONFIG.c_include_sg 0 CONFIG.c_addr_width 40 CONFIG.c_m_axi_mm2s_data_width 128 CONFIG.c_m_axis_mm2s_tdata_width 128 CONFIG.c_m_axi_s2mm_data_width 128 CONFIG.c_s_axis_s2mm_tdata_width 64 CONFIG.c_sg_length_width 20
ip control axi_gpio:2.0 CONFIG.C_IS_DUAL 1 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_GPIO_WIDTH 2 CONFIG.C_ALL_INPUTS_2 1 CONFIG.C_GPIO2_WIDTH 32
ip lite smartconnect:1.0 CONFIG.NUM_SI 1 CONFIG.NUM_MI 4
ip mem smartconnect:1.0 CONFIG.NUM_SI 2 CONFIG.NUM_MI 1
ip rst proc_sys_reset:5.0 CONFIG.C_AUX_RESET_HIGH 1
ip one xlconstant:1.1
ip zero xlconstant:1.1 CONFIG.CONST_VAL 0
wire frame/nlf_user nlf/s_axis_din_tuser
wire frame/pa_user pa/s_axis_din_tuser
wire frame/bank_select nlf/lut_bank_select
wire zero/dout pa/lut_bank_select rst/aux_reset_in rst/mb_debug_sys_rst
wire one/dout nlf/enable pa/enable rst/dcm_locked
wire zynq_ultra_ps_e_0/pl_resetn0 rst/ext_reset_in
wire control/gpio_io_o frame/mode
wire frame/status control/gpio2_io_i
bus zynq_ultra_ps_e_0/M_AXI_HPM0_LPD lite/S00_AXI
bus dma/M_AXI_MM2S mem/S00_AXI
bus dma/M_AXI_S2MM mem/S01_AXI
bus mem/M00_AXI zynq_ultra_ps_e_0/S_AXI_HP0_FPD
bus dma/M_AXIS_MM2S frame/s_axis
bus frame/m_axis dma/S_AXIS_S2MM
set space [get_bd_addr_spaces zynq_ultra_ps_e_0/Data]
foreach {mi slave offset} {00 dma/S_AXI_LITE 0x84000000 01 control/S_AXI 0x84010000 02 nlf/S_AXI_CTRL 0x84020000 03 pa/S_AXI_CTRL 0x84030000} {
    bus lite/M${mi}_AXI $slave
    assign_bd_address -target_address_space $space -offset $offset -range 64K [get_bd_addr_segs -of_objects [get_bd_intf_pins $slave]]
}
assign_bd_address
set clk zynq_ultra_ps_e_0/pl_clk0
wire $clk zynq_ultra_ps_e_0/maxihpm0_lpd_aclk zynq_ultra_ps_e_0/saxihp0_fpd_aclk lite/aclk mem/aclk rst/slowest_sync_clk frame/clk dma/s_axi_lite_aclk dma/m_axi_mm2s_aclk dma/m_axi_s2mm_aclk control/s_axi_aclk nlf/aclk nlf/s_axi_ctrl_aclk pa/aclk pa/s_axi_ctrl_aclk
wire rst/peripheral_aresetn lite/aresetn mem/aresetn frame/resetn dma/axi_resetn control/s_axi_aresetn nlf/aresetn nlf/s_axi_ctrl_aresetn pa/aresetn pa/s_axi_ctrl_aresetn
foreach cell {nlf pa} {
    wire frame/${cell}_valid $cell/s_axis_din_tvalid
    wire frame/${cell}_data $cell/s_axis_din_tdata
    wire $cell/s_axis_din_tready frame/${cell}_ready
    wire $cell/m_axis_dout_tvalid frame/${cell}_result_valid
    wire $cell/m_axis_dout_tdata frame/${cell}_result

}
validate_bd_design
save_bd_design
set bd [get_files dfe_dpd.bd]
add_files [make_wrapper -files $bd -top]
set_property top dfe_dpd_wrapper [current_fileset]
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
file mkdir run
set fd [open run/nlf-sites.txt w]
puts $fd [get_bels -of_objects [get_sites -filter {SITE_TYPE =~ DFE_*}] -filter {TYPE == DFE_NL_FIR}]
foreach c [get_cells -hier -filter {REF_NAME == DFE_NL_FIR}] {puts $fd "$c [get_bels -of_objects $c]"}
close $fd
report_timing_summary -report_unconstrained -max_paths 3 -file run/timing.rpt
report_utilization -file run/utilization.rpt
report_route_status -file run/route.rpt
report_cdc -details -file run/cdc.rpt
report_methodology -file run/methodology.rpt
report_drc -file run/drc.rpt
set wns [get_property SLACK [get_timing_paths -setup -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -hold -max_paths 1]]
if {$wns < 0 || $whs < 0} {error "WNS=$wns WHS=$whs"}
file copy [lindex [glob work/dfe.runs/impl_1/*.bit] 0] dfe_dpd.bit
file copy work/dfe.gen/sources_1/bd/dfe_dpd/hw_handoff/dfe_dpd.hwh .
write_hw_platform -fixed -include_bit -force dfe_dpd.xsa
set manifest [open artifacts.sha256 w]
puts $manifest [exec sha256sum dfe_dpd.bit dfe_dpd.hwh dfe_dpd.xsa]
close $manifest
puts "DFE_BUILD_PASS WNS=$wns WHS=$whs"
