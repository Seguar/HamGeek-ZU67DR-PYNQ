// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module capture_tb;
    reg adc_clk = 0, host_clk = 0;
    always #2 adc_clk = ~adc_clk;
    always #5 host_clk = ~host_clk;
    reg adc_resetn = 0, host_resetn = 0;
    reg [127:0] sample_data = 0;
    reg sample_valid = 0, command = 0;
    reg [15:0] read_addr = 0;
    reg read_en = 0;
    wire [31:0] status, read_data;
    capture dut (.*);

    integer word_index, lane_index, frame;
    reg [31:0] value;
    initial begin
        #40;
        adc_resetn = 1;
        host_resetn = 1;
        for (frame = 0; frame < 2; frame = frame + 1) begin
            @(negedge host_clk);
            command = !command;
            repeat (4) @(negedge adc_clk);
            for (word_index = 0; word_index < 4096; word_index = word_index + 1) begin
                value = (frame << 20) | (word_index << 2);
                sample_data = {value + 32'd3, value + 32'd2, value + 32'd1, value};
                sample_valid = 1;
                @(negedge adc_clk);
                if (word_index == 1024) begin
                    sample_valid = 0;
                    repeat (7) @(negedge adc_clk);
                end
            end
            sample_valid = 0;
            wait (status[0] == command);
            for (lane_index = 0; lane_index < 16384; lane_index = lane_index + 1) begin
                @(negedge host_clk);
                read_en = 1;
                read_addr = lane_index << 2;
                @(posedge host_clk);
                #1;
                if (read_data !== ((frame << 20) | lane_index))
                    $fatal(1, "frame %d lane %d read %h", frame, lane_index, read_data);
            end
            read_en = 0;
        end
        $display("ADC00_RTL_PASS two frames, every 32-bit word, valid gaps");
        $finish;
    end
    initial #500000 $fatal(1, "Simulation timed out");
endmodule
