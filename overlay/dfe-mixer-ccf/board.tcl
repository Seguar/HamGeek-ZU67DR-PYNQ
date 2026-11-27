# SPDX-License-Identifier: BSD-3-Clause
set ps [create_bd_cell -type ip -vlnv $ps_ip zynq_ultra_ps_e_0]
set_property -dict $vendor_config $ps
set_property -dict [list CONFIG.PSU__USE__M_AXI_GP0 0 CONFIG.PSU__USE__M_AXI_GP1 0 CONFIG.PSU__USE__M_AXI_GP2 1 \
    CONFIG.PSU__USE__S_AXI_GP2 1 CONFIG.PSU__SAXIGP2__DATA_WIDTH 128 \
    CONFIG.PSU__USE__IRQ0 0 CONFIG.PSU__GPIO_EMIO__PERIPHERAL__ENABLE 0] $ps

# ---------------------------------------------------------------- RF data converter
# Order matters (verified 2026-11-21): datapath mode, then rate, then reference.
set rf [create_bd_cell -type ip -vlnv xilinx.com:ip:usp_rf_data_converter:2.6 rfdc]
# ADC2 (bank 226) is the dual RF-ADC tile. Its PLL runs at twice
# the distributed sample clock used by quad tiles ADC0 and ADC1.
set quad_rate 2.5
set adc_ref 250.000
set source_rate [expr {2 * $quad_rate}]
set_property CONFIG.ADC_Slice20_Enable true $rf
set_property -dict [list CONFIG.ADC2_PLL_Enable true \
    CONFIG.ADC2_Sampling_Rate $source_rate \
    CONFIG.ADC2_Clock_Dist 2 CONFIG.ADC_Decimation_Mode20 2 CONFIG.ADC_Data_Width20 8] $rf
set_property CONFIG.ADC2_Refclk_Freq [format %.3f $adc_ref] $rf
foreach tile {1 0} {
    set p [list CONFIG.ADC${tile}_Clock_Source 2 \
        CONFIG.ADC${tile}_Refclk_Freq [format %.3f [expr {1000 * $quad_rate}]] CONFIG.ADC${tile}_Sampling_Rate $quad_rate]
    for {set ch 0} {$ch < 4} {incr ch} {
        lappend p CONFIG.ADC_Slice${tile}${ch}_Enable true CONFIG.ADC_Data_Type${tile}${ch} 1 \
            CONFIG.ADC_Data_Width${tile}${ch} 2 CONFIG.ADC_Decimation_Mode${tile}${ch} 8 \
            CONFIG.ADC_Mixer_Type${tile}${ch} 2 CONFIG.ADC_Mixer_Mode${tile}${ch} 0
    }
    set_property -dict $p $rf
}
# Keep the two unused ADC clock outputs at the r5 divider as well.
set_property -dict {CONFIG.ADC0_Outclk_Freq 312.500 CONFIG.ADC1_Outclk_Freq 312.500} $rf
# DAC1 (bank 228) forwards its 250 MHz reference to DAC0 (bank 227).
# Use each tile PLL to preserve 10 GS/s; forwarding the sample clock is derated.
foreach tile {1 0} {
    set p {}
    for {set ch 0} {$ch < 4} {incr ch} {
        lappend p CONFIG.DAC_Slice${tile}${ch}_Enable true CONFIG.DAC_Mode${tile}${ch} 3 \
            CONFIG.DAC_Data_Type${tile}${ch} 0 CONFIG.DAC_Data_Width${tile}${ch} 16 \
            CONFIG.DAC_Interpolation_Mode${tile}${ch} 1 CONFIG.DAC_Mixer_Type${tile}${ch} 1 \
            CONFIG.DAC_Coarse_Mixer_Freq${tile}${ch} 3 CONFIG.DAC_Mixer_Mode${tile}${ch} 2
    }
    lappend p CONFIG.DAC${tile}_Sampling_Rate 10.0 CONFIG.DAC${tile}_PLL_Enable true
    set_property -dict $p $rf
    set_property CONFIG.DAC${tile}_Refclk_Freq 250.000 $rf
}
set_property CONFIG.DAC1_Clock_Dist 1 $rf
set_property CONFIG.DAC0_Clock_Source 4 $rf
if {[get_property CONFIG.DAC1_Clock_Dist $rf] != 1 ||
    [get_property CONFIG.DAC0_Clock_Source $rf] != 4 ||
    ![get_property CONFIG.DAC0_PLL_Enable $rf]} {
    error "DAC reference forwarding was not configured"
}
set_property -dict {CONFIG.ADC0_Multi_Tile_Sync true CONFIG.ADC1_Multi_Tile_Sync true} $rf
puts "ADC MTS CONFIG: [get_property CONFIG.ADC0_Multi_Tile_Sync $rf] [get_property CONFIG.ADC1_Multi_Tile_Sync $rf]"
set_property -dict {CONFIG.DAC0_Multi_Tile_Sync true CONFIG.DAC1_Multi_Tile_Sync true} $rf
# TP17 measures 2.5 V. PG269 specifies fixed 20 mA for this rail.
set_property CONFIG.DAC_VOP_Mode 0 $rf
set_property CONFIG.DAC_Output_Current 0 $rf
foreach {name want} {DAC_VOP_Mode 0 DAC_Output_Current 0 DAC_VOP_RTS false} {
    set actual [get_property CONFIG.$name $rf]
    puts "RFDC DAC current: $name=$actual"
    if {$actual ne $want} { error "Unexpected RFDC $name=$actual (want $want)" }
}
set fab {}
foreach {g t want} {ADC 0 312.5 ADC 1 312.5 ADC 2 312.5 DAC 0 625.0 DAC 1 625.0} {
    set r [get_property CONFIG.${g}${t}_Fabric_Freq $rf]
    set s [get_property CONFIG.${g}${t}_Sampling_Rate $rf]
    set f [get_property CONFIG.${g}${t}_Refclk_Freq $rf]
    puts "RFDC $g$t: fs=$s GS/s refclk=$f MHz fabric=$r MHz"
    if {abs($r - $want) > 0.001} { error "Unexpected $g tile $t fabric clock $r (want $want)" }
    lappend fab "$g$t fs=$s refclk=$f fabric=$r"
}
foreach port {adc2_clk dac1_clk vin2_01 sysref_in} {
    make_bd_intf_pins_external [get_bd_intf_pins rfdc/$port]
}
foreach tile {0 1} {
    for {set ch 0} {$ch < 4} {incr ch} {
        foreach port [list vin${tile}${ch} vout${tile}${ch}] {
            make_bd_intf_pins_external [get_bd_intf_pins rfdc/$port]
        }
    }
}
foreach port {adc2_clk_0 dac1_clk_0} {
    set_property CONFIG.FREQ_HZ 250000000 [get_bd_intf_ports $port]
}
