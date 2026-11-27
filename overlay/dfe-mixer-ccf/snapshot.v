// SPDX-License-Identifier: BSD-3-Clause
// One outstanding 1024-word snapshot. Software waits for DMA completion
// before issuing another request. RAM stays stable while the host drains it.
module snapshot (
    input wire adc_clk, adc_resetn,
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 host_clk CLK", X_INTERFACE_PARAMETER="XIL_INTERFACENAME host_clk, ASSOCIATED_BUSIF M_AXIS, ASSOCIATED_RESET host_resetn" *)
    input wire host_clk,
    input wire host_resetn,
    input wire [4:0] control,
    input wire [1:0] tone_status, output wire [1:0] host_status,
    output wire [7:0] mix_tuser,
    input wire [31:0] raw_data, filtered_data,
    input wire raw_valid, filtered_valid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 M_AXIS TDATA" *)
    output reg [31:0] m_axis_tdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 M_AXIS TVALID" *)
    output reg m_axis_tvalid = 0,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 M_AXIS TREADY" *)
    input wire m_axis_tready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 M_AXIS TLAST" *)
    output reg m_axis_tlast = 0
);
    (* ASYNC_REG="TRUE" *) reg [1:0] request_sync = 0, raw_sync = 0;
    (* ASYNC_REG="TRUE" *) reg [1:0] complete_sync = 0;
    (* ASYNC_REG="TRUE" *) reg [1:0] status_meta = 0, status_sync = 0;
    always @(posedge host_clk) begin
        status_meta <= tone_status;
        status_sync <= status_meta;
    end
    assign host_status = status_sync;
    // PG393: activation and carrier updates share a 16*CPS clock boundary.
    reg [3:0] mixer_cycle = 0;
    always @(posedge adc_clk) begin
        if (!adc_resetn) mixer_cycle <= 0;
        else mixer_cycle <= mixer_cycle + 1'b1;
    end
    assign mix_tuser = {7'b0, mixer_cycle == 0};
    reg complete = 0, drained = 0;
    reg [9:0] wr = 0, rd = 0;
    (* ram_style="block" *) reg [31:0] ram [0:1023];
    wire store = adc_resetn && request_sync[1] != complete &&
                 (raw_sync[1] ? raw_valid : filtered_valid);

    always @(posedge adc_clk) begin
        request_sync <= {request_sync[0],control[1]};
        raw_sync <= {raw_sync[0],control[2]};
        if (store)
            ram[wr] <= raw_sync[1] ? raw_data : filtered_data;
        if (!adc_resetn) begin
            wr <= 0;
            complete <= 0;
        end else if (store) begin
            wr <= wr + 1'b1;
            if (&wr) complete <= request_sync[1];
        end
    end

    wire fetch = complete_sync[1] != drained && (!m_axis_tvalid || m_axis_tready);
    always @(posedge host_clk) begin
        complete_sync <= {complete_sync[0],complete};
        if (fetch) m_axis_tdata <= ram[rd];
        if (!host_resetn) begin
            rd <= 0;
            drained <= 0;
            m_axis_tvalid <= 0;
            m_axis_tlast <= 0;
        end else if (fetch) begin
            rd <= rd + 1'b1;
            m_axis_tvalid <= 1;
            m_axis_tlast <= &rd;
            if (&rd) drained <= complete_sync[1];
        end else if (m_axis_tready) begin
            m_axis_tvalid <= 0;
        end
    end
endmodule
