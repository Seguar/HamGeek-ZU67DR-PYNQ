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
add_files -fileset constrs_1 $src/constraints.xdc
set_property USED_IN_SYNTHESIS false [get_files constraints.xdc]
set_property PROCESSING_ORDER LATE [get_files constraints.xdc]
create_bd_design dfe_mixer_ccf
source $src/board.tcl
proc ip {inst core args} {
    set def [get_ipdefs xilinx.com:ip:$core]
    if {[llength $def] != 1 || [get_property REQUIRES_LICENSE $def] || [get_property LICENSE_KEYS $def] ne ""} {error "Unavailable or separately licensed: $core"}
    set cell [create_bd_cell -type ip -vlnv $def $inst]
    if {[llength $args]} {set_property -dict $args $cell}
}
ip mixer xdfe_cc_mixer:2.0 CONFIG.MODE Uplink CONFIG.CLOCK_FREQUENCY 312.50 CONFIG.MAX_USEABLE_CCIDS 4 CONFIG.N_CH_X1 1 CONFIG.N_CH_X16 0
ip ccf xdfe_cc_filter:1.1 CONFIG.CLOCK_FREQUENCY 312.50 CONFIG.MAX_USEABLE_CCIDS 2 CONFIG.NUM_TAPS 16
proc wire {args} {connect_bd_net {*}[lmap p $args {get_bd_pins $p}]}
proc bus {a b} {connect_bd_intf_net [get_bd_intf_pins $a] [get_bd_intf_pins $b]}
foreach {module name} {dfe_clocking clk_gen snapshot capture dac_tone tone} {
    create_bd_cell -type module -reference $module $name
}
foreach {port pin} {pl_refclk_p refclk_p pl_refclk_n refclk_n pl_sysref_p sysref_p pl_sysref_n sysref_n} {
    create_bd_port -dir I $port
    connect_bd_net [get_bd_ports $port] [get_bd_pins clk_gen/$pin]
}
ip dma axi_dma:7.1 CONFIG.c_include_sg 0 CONFIG.c_include_mm2s 0 CONFIG.c_addr_width 40 CONFIG.c_m_axi_s2mm_data_width 128 CONFIG.c_s_axis_s2mm_tdata_width 32
ip control axi_gpio:2.0 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_GPIO_WIDTH 3 CONFIG.C_DOUT_DEFAULT 0x00000000
ip axi_lite smartconnect:1.0 CONFIG.NUM_MI 5 CONFIG.NUM_SI 1
ip axi_mem smartconnect:1.0 CONFIG.NUM_MI 1 CONFIG.NUM_SI 1
bus zynq_ultra_ps_e_0/M_AXI_HPM0_LPD axi_lite/S00_AXI
bus dma/M_AXI_S2MM axi_mem/S00_AXI
bus axi_mem/M00_AXI zynq_ultra_ps_e_0/S_AXI_HP0_FPD
set space [get_bd_addr_spaces zynq_ultra_ps_e_0/Data]
foreach {mi slave offset range} {
    00 rfdc/s_axi      0x82000000 256K
    01 control/S_AXI   0x84000000 64K
    02 dma/S_AXI_LITE  0x84010000 64K
    03 mixer/S_AXI_CTRL 0x84040000 256K
    04 ccf/S_AXI_CTRL   0x84080000 256K
} {
    bus axi_lite/M${mi}_AXI $slave
    assign_bd_address -target_address_space $space -offset $offset -range $range [get_bd_addr_segs -of_objects [get_bd_intf_pins $slave]]
}
assign_bd_address
ip one xlconstant:1.1
ip zero xlconstant:1.1 CONFIG.CONST_VAL 0
ip zero8 xlconstant:1.1 CONFIG.CONST_VAL 0 CONFIG.CONST_WIDTH 8
ip silence xlconstant:1.1 CONFIG.CONST_VAL 0 CONFIG.CONST_WIDTH 256
set host zynq_ultra_ps_e_0/pl_clk0
foreach {name clk locked} [list host_reset $host one/dout adc_reset clk_gen/clk312 clk_gen/locked dac_reset clk_gen/clk625 clk_gen/locked] {
    ip $name proc_sys_reset:5.0 CONFIG.C_AUX_RESET_HIGH 1
    wire $clk $name/slowest_sync_clk
    wire zynq_ultra_ps_e_0/pl_resetn0 $name/ext_reset_in
    wire $locked $name/dcm_locked
    wire zero/dout $name/aux_reset_in $name/mb_debug_sys_rst
}
wire $host zynq_ultra_ps_e_0/maxihpm0_lpd_aclk zynq_ultra_ps_e_0/saxihp0_fpd_aclk axi_lite/aclk axi_mem/aclk dma/s_axi_lite_aclk dma/m_axi_s2mm_aclk rfdc/s_axi_aclk control/s_axi_aclk mixer/s_axi_aclk ccf/s_axi_aclk capture/host_clk
wire host_reset/peripheral_aresetn axi_lite/aresetn axi_mem/aresetn dma/axi_resetn rfdc/s_axi_aresetn control/s_axi_aresetn mixer/s_axi_aresetn ccf/s_axi_aresetn capture/host_resetn
wire clk_gen/clk312 mixer/s_axis_aclk ccf/s_axis_aclk capture/adc_clk rfdc/m0_axis_aclk rfdc/m1_axis_aclk rfdc/m2_axis_aclk
wire adc_reset/peripheral_aresetn mixer/s_axis_aresetn ccf/s_axis_aresetn capture/adc_resetn rfdc/m0_axis_aresetn rfdc/m1_axis_aresetn rfdc/m2_axis_aresetn
wire clk_gen/clk625 tone/dac_clk rfdc/s0_axis_aclk rfdc/s1_axis_aclk
wire dac_reset/peripheral_aresetn tone/dac_resetn rfdc/s0_axis_aresetn rfdc/s1_axis_aresetn
wire clk_gen/sysref_adc rfdc/user_sysref_adc
wire clk_gen/sysref_dac rfdc/user_sysref_dac
wire control/gpio_io_o capture/control tone/control
wire rfdc/m00_axis_tdata mixer/s_axis_ul_din_tdata capture/raw_data
wire rfdc/m00_axis_tvalid mixer/s_axis_ul_din_tvalid capture/raw_valid
wire one/dout mixer/s_axis_ul_din_tlast
wire zero8/dout mixer/s_axis_ul_din_tuser
wire mixer/s_axis_ul_din_tready rfdc/m00_axis_tready
bus mixer/M_AXIS_UL_DOUT ccf/S_AXIS_DIN
wire ccf/m_axis_dout_tdata capture/filtered_data
wire ccf/m_axis_dout_tvalid capture/filtered_valid
bus capture/M_AXIS dma/S_AXIS_S2MM
wire tone/samples rfdc/s00_axis_tdata
wire rfdc/s00_axis_tready tone/ready
foreach pin [get_bd_pins -regexp {rfdc/s[01][0-3]_axis_tvalid}] {wire one/dout $pin}
foreach pin [get_bd_pins -regexp {rfdc/s[01][0-3]_axis_tdata}] {
    if {$pin ne "/rfdc/s00_axis_tdata"} {wire silence/dout $pin}
}
foreach pin [get_bd_pins -regexp {rfdc/m[0-2][0-3]_axis_tready}] {
    if {$pin ne "/rfdc/m00_axis_tready"} {wire one/dout $pin}
}
validate_bd_design
save_bd_design
set bd [get_files dfe_mixer_ccf.bd]
add_files [make_wrapper -files $bd -top]
set_property top dfe_mixer_ccf_wrapper [current_fileset]
launch_runs impl_1 -to_step write_bitstream -jobs 3
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
file mkdir run
report_timing_summary -report_unconstrained -max_paths 3 -file run/timing.rpt
report_utilization -file run/utilization.rpt
report_route_status -file run/route.rpt
report_drc -file run/drc.rpt
set wns [get_property SLACK [get_timing_paths -setup -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -hold -max_paths 1]]
if {$wns < 0 || $whs < 0} {error "WNS=$wns WHS=$whs"}
file copy [lindex [glob work/dfe.runs/impl_1/*.bit] 0] dfe_mixer_ccf.bit
file copy work/dfe.gen/sources_1/bd/dfe_mixer_ccf/hw_handoff/dfe_mixer_ccf.hwh .
write_hw_platform -fixed -include_bit -force dfe_mixer_ccf.xsa
puts "DFE_BUILD_PASS WNS=$wns WHS=$whs"
