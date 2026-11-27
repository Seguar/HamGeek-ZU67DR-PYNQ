// SPDX-License-Identifier: BSD-3-Clause
module harness_tb;
  bit clk, resetn, tx_valid, tx_last, rx_ready;
  logic [31:0] tx, din, status;
  logic [63:0] rx;
  logic [7:0] control, tag, userbits;
  logic tx_ready, rx_last, rx_valid, last, valid;
  int rx_count = 0;
  int cycle = 0;
  always #2 clk = ~clk;
  // Independent output source, one beat every 64 clocks.
  prach_harness dut(.clk(clk), .resetn(resetn), .control(control), .status(status),
      .s_axis_tvalid(tx_valid), .s_axis_tdata(tx), .s_axis_tlast(tx_last),
      .s_axis_tready(tx_ready), .m_axis_tvalid(rx_valid), .m_axis_tlast(rx_last),
      .m_axis_tdata(rx), .m_axis_tready(rx_ready), .din(din), .carrier_tag(tag),
      .userbits(userbits), .last(last), .valid(valid), .ready(1'b1),
      .dout(cycle), .out_last(1'b0), .out_valid(cycle % 64 == 0), .out_id(8'h30));

  always @(posedge clk) begin
    if (!resetn) cycle <= 0;
    else begin
      if (control[0] && cycle % 16 == 0 &&
          din !== ((cycle / 16) % 1024)) $fatal(1, "stimulus index %d: %h",cycle,din);
      if (tag !== ((cycle % 16 == 0) ? 0 : 16)) $fatal(1, "CC tag");
      if (rx_ready && rx_valid) begin
        if (rx[31:0] !== 131072 + 64*rx_count ||
            rx[53:32] !== rx[21:0] || rx[61:54] !== 8'h30 ||
            rx_last !== (rx_count == 1023)) $fatal(1, "capture record %d",rx_count);
        rx_count <= rx_count + 1;
      end
      cycle <= cycle + 1;
    end
  end
  initial begin
    control = 0;
    repeat(5) @(negedge clk);
    resetn = 1;
    tx_valid = 1;
    for (int n=0; n<1024; n++) begin
      tx = n; tx_last = n==1023;
      @(negedge clk);
    end
    tx_valid = 0; control = 3;
    repeat(200000) begin
      @(negedge clk);
      rx_ready = (cycle % 7) < 3;
    end
    if (rx_count != 1024 || status !== ((1<<17) + 1024)) $fatal(1, "window/count");
    $display("HARNESS_PASS 1024 tagged timestamped beats under backpressure");
    $finish;
  end
endmodule
