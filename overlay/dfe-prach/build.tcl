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
set_param general.maxThreads 4
create_bd_design dfe_prach
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
ip prach xdfe_nr_prach:2.0 CONFIG.NUM_ANTENNA0 1 CONFIG.ANTENNA_INTERLEAVE0 1 CONFIG.MAX_USEABLE_CCIDS0 2 CONFIG.NUM_RACH_PER_ANTENNA 1 CONFIG.CLOCK_FREQUENCY 245.76
ip reference clk_wiz:6.0 CONFIG.PRIM_IN_FREQ 100 CONFIG.CLKOUT1_REQUESTED_OUT_FREQ 96 CONFIG.USE_RESET false
ip clock clk_wiz:6.0 CONFIG.PRIM_IN_FREQ 96 CONFIG.CLKOUT1_REQUESTED_OUT_FREQ 245.76 CONFIG.USE_RESET false
wire zynq_ultra_ps_e_0/pl_clk0 reference/clk_in1
wire reference/clk_out1 clock/clk_in1
ip rst proc_sys_reset:5.0 CONFIG.C_AUX_RESET_HIGH 1
wire clock/locked rst/dcm_locked
ip zero xlconstant:1.1 CONFIG.CONST_VAL 0
wire zero/dout rst/aux_reset_in rst/mb_debug_sys_rst
wire zynq_ultra_ps_e_0/pl_resetn0 rst/ext_reset_in
ip dma axi_dma:7.1 CONFIG.c_include_sg 0 CONFIG.c_addr_width 40 CONFIG.c_m_axis_mm2s_tdata_width 32 CONFIG.c_s_axis_s2mm_tdata_width 64 CONFIG.c_sg_length_width 20
ip control axi_gpio:2.0 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_GPIO_WIDTH 8 CONFIG.C_IS_DUAL 1 CONFIG.C_ALL_INPUTS_2 1 CONFIG.C_GPIO2_WIDTH 32
ip regs smartconnect:1.0 CONFIG.NUM_MI 3 CONFIG.NUM_SI 1
ip mem smartconnect:1.0 CONFIG.NUM_MI 1 CONFIG.NUM_SI 2
bus zynq_ultra_ps_e_0/M_AXI_HPM0_LPD regs/S00_AXI
bus dma/M_AXI_S2MM mem/S00_AXI
bus dma/M_AXI_MM2S mem/S01_AXI
bus mem/M00_AXI zynq_ultra_ps_e_0/S_AXI_HP0_FPD
foreach {mi slave offset range} {
    00 control/S_AXI 0x84000000 64K
    01 dma/S_AXI_LITE 0x84010000 64K
    02 prach/S_AXI_CTRL 0x84040000 256K
} {
    bus regs/M${mi}_AXI $slave
    assign_bd_address -target_address_space [get_bd_addr_spaces zynq_ultra_ps_e_0/Data] -offset $offset -range $range [get_bd_addr_segs -of_objects [get_bd_intf_pins $slave]]
}
assign_bd_address
create_bd_cell -type module -reference prach_harness harness
bus dma/M_AXIS_MM2S harness/S_AXIS
bus harness/M_AXIS dma/S_AXIS_S2MM
wire control/gpio_io_o harness/control
wire harness/status control/gpio2_io_i
foreach {port pin} {
    din s_axis_din0_tdata carrier_tag s_axis_din0_tid last s_axis_din0_tlast
    valid s_axis_din0_tvalid ready s_axis_din0_tready userbits s_axis_din0_tuser
    dout m_axis_dout_tdata out_valid m_axis_dout_tvalid out_id m_axis_dout_tid out_last m_axis_dout_tlast
} {wire harness/$port prach/$pin}
wire clock/clk_out1 harness/clk rst/slowest_sync_clk regs/aclk mem/aclk zynq_ultra_ps_e_0/maxihpm0_lpd_aclk zynq_ultra_ps_e_0/saxihp0_fpd_aclk dma/s_axi_lite_aclk dma/m_axi_mm2s_aclk dma/m_axi_s2mm_aclk control/s_axi_aclk prach/s_axi_aclk prach/s_axis_aclk
wire rst/peripheral_aresetn harness/resetn regs/aresetn mem/aresetn dma/axi_resetn control/s_axi_aresetn prach/s_axi_aresetn prach/s_axis_aresetn
validate_bd_design
save_bd_design
set bd [get_files dfe_prach.bd]
add_files [make_wrapper -files $bd -top]
set_property top dfe_prach_wrapper [current_fileset]
if {[info exists ::env(PRACH_VALIDATE_ONLY)]} {puts "PRACH_BD_PASS"; return}
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
file copy [lindex [glob work/dfe.runs/impl_1/*.bit] 0] dfe_prach.bit
file copy work/dfe.gen/sources_1/bd/dfe_prach/hw_handoff/dfe_prach.hwh .
write_hw_platform -fixed -include_bit -force dfe_prach.xsa
set manifest [open artifacts.sha256 w]
puts $manifest [exec sha256sum dfe_prach.bit dfe_prach.hwh dfe_prach.xsa]
close $manifest
puts "DFE_BUILD_PASS WNS=$wns WHS=$whs"
