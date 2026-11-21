// SPDX-License-Identifier: BSD-3-Clause
// A finite snapshot. RFDC and memory reads have independent clocks.
module capture (
    input wire adc_clk, adc_resetn,
    input wire [127:0] sample_data,
    input wire sample_valid,
    input wire command,
    input wire host_clk, host_resetn,
    output wire [31:0] status,
    input wire [15:0] read_addr,
    input wire read_en,
    output wire [31:0] read_data
);
    (* ASYNC_REG = "TRUE" *) reg [1:0] command_sync = 0;
    (* ASYNC_REG = "TRUE" *) reg [1:0] done_sync = 0;
    reg done = 0;
    reg [11:0] write_index = 0;
    wire recording = command_sync[1] != done;

    (* ram_style = "block" *) reg [127:0] memory [0:4095];
    reg [127:0] read_word;
    reg [1:0] read_lane;

    always @(posedge adc_clk) begin
        if (!adc_resetn) begin
            command_sync <= 0;
            done <= 0;
            write_index <= 0;
        end else begin
            command_sync <= {command_sync[0], command};
            if (recording && sample_valid) begin
                write_index <= write_index + 1'b1;
                if (&write_index)
                    done <= command_sync[1];
            end
        end
        if (adc_resetn && recording && sample_valid)
            memory[write_index] <= sample_data;
    end

    always @(posedge host_clk) begin
        if (!host_resetn)
            done_sync <= 0;
        else
            done_sync <= {done_sync[0], done};

        if (read_en) begin
            read_word <= memory[read_addr[15:4]];
            read_lane <= read_addr[3:2];
        end
    end

    assign status = {31'b0, done_sync[1]};
    assign read_data = read_word[read_lane * 32 +: 32];
endmodule
