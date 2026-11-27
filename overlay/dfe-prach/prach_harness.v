// SPDX-License-Identifier: BSD-3-Clause
module prach_harness(
    (* X_INTERFACE_PARAMETER = "ASSOCIATED_BUSIF S_AXIS:M_AXIS, ASSOCIATED_RESET resetn" *)
    input wire clk, input wire resetn,
    input wire [31:0] s_axis_tdata, input wire s_axis_tvalid, s_axis_tlast,
    output wire s_axis_tready,
    output reg [63:0] m_axis_tdata, output reg m_axis_tvalid, m_axis_tlast,
    input wire m_axis_tready,
    input wire [7:0] control, output wire [31:0] status,
    output wire [31:0] din, output wire [7:0] carrier_tag, userbits,
    output wire last, valid, input wire ready,
    input wire [31:0] dout, input wire out_valid, out_last, input wire [7:0] out_id
);
    reg [21:0] tick;
    wire frame_end = tick == 2457599;
    wire active_slot = tick[3:0] == 0;
    reg [9:0] wr;
    reg [31:0] stimulus [0:1023];
    reg [31:0] iq;
    assign s_axis_tready = resetn && !control[0];
    always @(posedge clk) begin
        if (s_axis_tready && s_axis_tvalid) begin
            stimulus[wr] <= s_axis_tdata;
            wr <= s_axis_tlast ? 0 : wr + 1'b1;
        end
        if (!resetn) wr <= 0;
        // Read one cycle ahead of the active slot; frame length is 150 periods.
        iq <= stimulus[tick[13:4] + 10'd1];
    end
    assign din = active_slot && control[0] ? iq : 0;
    assign carrier_tag = active_slot ? 0 : 8'h10;
    assign valid = resetn;
    assign last = &tick[3:0];
    assign userbits = {5'b0, frame_end, tick == 1228799, last};
    always @(posedge clk)
        if (!resetn) tick <= 0;
        else if (ready) tick <= frame_end ? 0 : tick + 1'b1;

    // Observe an independent 65,536-clock window inside the scheduled slot.
    // Record its first 1024 valid beats. The counter also detects extra beats.
    reg capturing, sending, done;
    reg [16:0] count;
    reg [9:0] rd;
    reg [63:0] samples [0:1023];
    wire take = capturing && tick >= 131072 && tick < 196608 && out_valid;
    always @(posedge clk) begin
        if (take && count < 1024)
            samples[count[9:0]] <= {1'b0,out_last,out_id,tick,dout};
        if (!resetn || !control[1]) begin
            capturing <= 0;
            sending <= 0;
            done <= 0;
            count <= 0;
            rd <= 0;
            m_axis_tvalid <= 0;
            m_axis_tlast <= 0;
        end else begin
            if (tick == 131071 && !done) capturing <= 1;
            if (take) count <= count + 1'b1;
            if (capturing && tick == 196608) begin
                capturing <= 0;
                done <= 1;
                sending <= count >= 1024;
            end
            if (sending && (!m_axis_tvalid || m_axis_tready)) begin
                m_axis_tdata <= samples[rd];
                m_axis_tvalid <= 1;
                m_axis_tlast <= &rd;
                rd <= rd + 1'b1;
                if (&rd) sending <= 0;
            end else if (m_axis_tready) m_axis_tvalid <= 0;
        end
    end
    assign status = {14'b0,done,count};
endmodule
