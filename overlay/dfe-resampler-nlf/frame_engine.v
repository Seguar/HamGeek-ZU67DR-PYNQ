// SPDX-License-Identifier: BSD-3-Clause
// DMA preloads 1024 padded beats. Replay two periods, capture the third.
// Count valid output beats independently over the third input period.
module frame_engine (
    (* X_INTERFACE_PARAMETER="ASSOCIATED_BUSIF s_axis:m_axis, ASSOCIATED_RESET resetn" *)
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 clk CLK" *) input wire clk,
    input wire resetn,
    input wire [1:0] mode,
    output wire [31:0] status,
    input wire [127:0] s_axis_tdata,
    input wire s_axis_tvalid, s_axis_tlast,
    output wire s_axis_tready,
    output reg [63:0] m_axis_tdata,
    output reg m_axis_tvalid, m_axis_tlast,
    input wire m_axis_tready,
    output wire [95:0] dec_data,
    output wire [31:0] int_data, nlf_data,
    output wire dec_valid, int_valid, nlf_valid,
    input wire dec_ready, int_ready, nlf_ready,
    input wire [63:0] dec_result, int_result,
    input wire [55:0] nlf_result,
    input wire dec_result_valid, int_result_valid, nlf_result_valid,
    input wire dec_error, int_error, dec_overflow, int_overflow
);
    localparam LOAD=0, PRIME=1, PLAY=2, DRAIN=3, FINISH=4;
    reg [2:0] state;
    reg [9:0] addr;
    reg [1:0] period;
    reg [10:0] captured;
    reg [3:0] faults;
    reg [95:0] sample;
    reg [95:0] stimulus [0:1023];
    reg [63:0] response [0:1023];
    assign status = {13'd0, faults, 1'b0, captured, state};
    assign s_axis_tready = state == LOAD;
    assign dec_data = sample;
    assign int_data = sample[31:0];
    assign nlf_data = sample[31:0];
    assign dec_valid = state == PLAY && mode == 0;
    assign int_valid = state == PLAY && mode == 1;
    assign nlf_valid = state == PLAY && mode == 2;
    wire ready = mode == 0 ? dec_ready : mode == 1 ? int_ready : nlf_ready;
    wire returned = mode == 0 ? dec_result_valid :
                    mode == 1 ? int_result_valid : nlf_result_valid;
    wire [63:0] result = mode == 0 ? dec_result :
                         mode == 1 ? int_result : {8'd0,nlf_result};
    wire accepted = state == PLAY && ready;
    wire record = state == PLAY && period == 2 && returned;
    always @(posedge clk) begin
        if (state == LOAD && s_axis_tvalid)
            stimulus[addr] <= s_axis_tdata[95:0];
        if (state == PRIME || accepted)
            sample <= stimulus[state == PRIME ? 10'd0 : addr + 10'd1];
        if (record && captured < 1024)
            response[captured[9:0]] <= result;
        if (state == DRAIN && (!m_axis_tvalid || m_axis_tready))
            m_axis_tdata <= response[addr];
        if (!resetn) begin
            state <= LOAD;
            addr <= 0;
            period <= 0;
            captured <= 0;
            faults <= 0;
            m_axis_tvalid <= 0;
            m_axis_tlast <= 0;
        end else case (state)
            LOAD: if (s_axis_tvalid) begin
                addr <= addr + 1'b1;
                if (s_axis_tlast) begin
                    faults <= {3'b0,!(&addr)};
                    addr <= 0;
                    period <= 0;
                    captured <= 0;
                    state <= PRIME;
                end
            end
            PRIME: state <= PLAY;
            PLAY: begin
                if (period == 2) begin
                    if (record && captured < 2047) captured <= captured + 1'b1;
                    if (!ready) faults[1] <= 1;
                    if ((mode == 0 && dec_error) || (mode == 1 && int_error)) faults[2] <= 1;
                    if ((mode == 0 && dec_overflow) || (mode == 1 && int_overflow)) faults[3] <= 1;
                end
                if (accepted) begin
                    addr <= addr + 1'b1;
                    if (&addr) begin
                        period <= period + 1'b1;
                        if (period == 2) state <= DRAIN;
                    end
                end
            end
            DRAIN: if (!m_axis_tvalid || m_axis_tready) begin
                addr <= addr + 1'b1;
                m_axis_tvalid <= 1;
                m_axis_tlast <= &addr;
                if (&addr) state <= FINISH;
            end
            FINISH: if (m_axis_tready) begin
                m_axis_tvalid <= 0;
                m_axis_tlast <= 0;
                state <= LOAD;
            end
        endcase
    end
endmodule
