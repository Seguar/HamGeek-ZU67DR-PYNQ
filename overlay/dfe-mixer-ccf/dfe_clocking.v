// SPDX-License-Identifier: BSD-3-Clause
module dfe_clocking (
    input  wire refclk_p, refclk_n,     // 250 MHz from LMK DCLKout8
    input  wire sysref_p, sysref_n,     // 6.25 MHz PL SYSREF from LMK SDCLKout11
    (* X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 clk625 CLK" *)
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME clk625, FREQ_HZ 625000000" *)
    output wire clk625,
    (* X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 clk312 CLK" *)
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME clk312, FREQ_HZ 312500000" *)
    output wire clk312,
    output wire locked,
    output reg  sysref_adc = 1'b0,      // PL SYSREF in the 312.5 MHz domain
    output reg  sysref_dac = 1'b0      // PL SYSREF in the 625 MHz domain
);
    wire refclk_ibuf, sysref_ibuf, fb, fb_buf, c0, c1, c2, c3, clk250, clk62;
    IBUFDS ref_ibuf (.I(refclk_p), .IB(refclk_n), .O(refclk_ibuf));
    IBUFDS sys_ibuf (.I(sysref_p), .IB(sysref_n), .O(sysref_ibuf));

    MMCME4_ADV #(
        .BANDWIDTH("OPTIMIZED"), .COMPENSATION("AUTO"),
        .CLKIN1_PERIOD(4.000), .REF_JITTER1(0.010), .DIVCLK_DIVIDE(1),
        .CLKFBOUT_MULT_F(5.000),            // VCO 1250 MHz
        .CLKOUT0_DIVIDE_F(2.000),           // 625 MHz
        .CLKOUT1_DIVIDE(4),                 // 312.5 MHz
        .CLKOUT2_DIVIDE(5),                 // 250 MHz
        .CLKOUT3_DIVIDE(20)                 // 62.5 MHz super-cycle clock
    ) mmcm (
        .CLKIN1(refclk_ibuf), .CLKIN2(1'b0), .CLKINSEL(1'b1),
        .CLKFBIN(fb_buf), .CLKFBOUT(fb), .CLKFBOUTB(),
        .CLKOUT0(c0), .CLKOUT0B(), .CLKOUT1(c1), .CLKOUT1B(), .CLKOUT2(c2), .CLKOUT2B(),
        .CLKOUT3(c3), .CLKOUT3B(), .CLKOUT4(), .CLKOUT5(), .CLKOUT6(),
        .RST(1'b0), .PWRDWN(1'b0), .LOCKED(locked),
        .DADDR(7'd0), .DCLK(1'b0), .DEN(1'b0), .DI(16'd0), .DWE(1'b0), .DO(), .DRDY(),
        .PSCLK(1'b0), .PSEN(1'b0), .PSINCDEC(1'b0), .PSDONE(),
        .CDDCREQ(1'b0), .CDDCDONE(), .CLKINSTOPPED(), .CLKFBSTOPPED()
    );
    BUFG fb_bufg   (.I(fb), .O(fb_buf));
    BUFG c625_bufg (.I(c0), .O(clk625));
    BUFG c312_bufg (.I(c1), .O(clk312));
    BUFG c250_bufg (.I(c2), .O(clk250));
    BUFG c62_bufg  (.I(c3), .O(clk62));

    // PL SYSREF: IOB register on the pin-aligned 250 MHz clock.
    (* IOB = "TRUE" *) reg sysref_iob = 1'b0;
    reg sysref250 = 1'b0;
    always @(posedge clk250) begin
        sysref_iob  <= sysref_ibuf;
        sysref250   <= sysref_iob;
    end

    // 250 -> 62.5 MHz (ratio 4, timed by STA): sample on the super-cycle edge.
    reg sys62 = 1'b0;
    always @(posedge clk62) begin
        sys62  <= sysref250;
    end

    // 62.5 -> 312.5 MHz (ratio 5, timed by STA).
    reg sysref312_a = 1'b0;
    always @(posedge clk312) begin
        sysref312_a <= sys62;
        sysref_adc  <= sysref312_a;
    end

    // 312.5 -> 625 MHz: integer ratio, timed by STA.
    reg sysref625_a = 1'b0;
    always @(posedge clk625) begin
        sysref625_a <= sysref312_a;
        sysref_dac  <= sysref625_a;
    end
endmodule
