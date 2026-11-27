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
create_bd_design dfe_fft
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
ip fft xdfe_fft:1.0 CONFIG.NUM_FFT 1 CONFIG.DEFAULT_MAX_POINT_SIZE 256 CONFIG.DOUT_HAS_TREADY true
ip dma axi_dma:7.1 CONFIG.c_include_sg 0 CONFIG.c_addr_width 40 CONFIG.c_m_axi_mm2s_data_width 128 CONFIG.c_m_axis_mm2s_tdata_width 32 CONFIG.c_m_axi_s2mm_data_width 128 CONFIG.c_s_axis_s2mm_tdata_width 64
ip ctrlword xlconstant:1.1 CONFIG.CONST_WIDTH 16 CONFIG.CONST_VAL 24
ip one xlconstant:1.1
ip zero xlconstant:1.1 CONFIG.CONST_VAL 0
ip reset proc_sys_reset:5.0 CONFIG.C_AUX_RESET_HIGH 1 CONFIG.C_EXT_RESET_HIGH 0
ip lite smartconnect:1.0 CONFIG.NUM_SI 1 CONFIG.NUM_MI 1
ip mem smartconnect:1.0 CONFIG.NUM_SI 2 CONFIG.NUM_MI 1
bus zynq_ultra_ps_e_0/M_AXI_HPM0_LPD lite/S00_AXI
bus lite/M00_AXI dma/S_AXI_LITE
bus dma/M_AXI_MM2S mem/S00_AXI
bus dma/M_AXI_S2MM mem/S01_AXI
bus mem/M00_AXI zynq_ultra_ps_e_0/S_AXI_HP0_FPD
wire zynq_ultra_ps_e_0/pl_clk0 reset/slowest_sync_clk lite/aclk mem/aclk zynq_ultra_ps_e_0/maxihpm0_lpd_aclk zynq_ultra_ps_e_0/saxihp0_fpd_aclk dma/s_axi_lite_aclk dma/m_axi_mm2s_aclk dma/m_axi_s2mm_aclk fft/s_axis_aclk
wire zynq_ultra_ps_e_0/pl_resetn0 reset/ext_reset_in
wire one/dout reset/dcm_locked fft/s_axis_ctrl_tvalid
wire zero/dout reset/aux_reset_in reset/mb_debug_sys_rst
wire reset/peripheral_aresetn lite/aresetn mem/aresetn dma/axi_resetn fft/s_axis_aresetn
wire ctrlword/dout fft/s_axis_ctrl_tdata
bus dma/M_AXIS_MM2S fft/S_AXIS_DIN
bus fft/M_AXIS_DOUT dma/S_AXIS_S2MM
assign_bd_address
validate_bd_design
save_bd_design
set bd [get_files dfe_fft.bd]
add_files [make_wrapper -files $bd -top]
set_property top dfe_fft_wrapper [current_fileset]
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
file copy [lindex [glob work/dfe.runs/impl_1/*.bit] 0] dfe_fft.bit
file copy work/dfe.gen/sources_1/bd/dfe_fft/hw_handoff/dfe_fft.hwh .
write_hw_platform -fixed -include_bit -force dfe_fft.xsa
set manifest [open artifacts.sha256 w]
puts $manifest [exec sha256sum dfe_fft.bit dfe_fft.hwh dfe_fft.xsa]
close $manifest
puts "DFE_BUILD_PASS WNS=$wns WHS=$whs"
