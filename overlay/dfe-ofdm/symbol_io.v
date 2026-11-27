// SPDX-License-Identifier: BSD-3-Clause
// One 20 MHz NR carrier at 15 kHz SCS. Load one 1272-RE symbol by DMA,
// repeat it on both parallel antenna lanes, and select one entire UL packet.
module symbol_io(
    input clk, resetn,
    input [63:0] load_data, input load_valid, load_last, output load_ready,
    output reg [63:0] ft_data, output reg ft_valid, ft_last, input ft_ready,
    output reg [7:0] frame,
    input capture_request, input [63:0] ul_data, input ul_valid, ul_last,
    output ul_ready, output [63:0] capture_data,
    output capture_valid, capture_last, input capture_ready
);
    reg [10:0] write_index, next_index;
    reg loaded;
    (* ram_style="block" *) reg [63:0] samples [0:2047];
    assign load_ready = 1'b1;
    always @(posedge clk) begin
        if (load_valid) samples[write_index] <= load_data;
        if (!resetn) begin
            write_index <= 0;
            loaded <= 0;
        end else if (load_valid) begin
            write_index <= load_last ? 0 : write_index + 1'b1;
            loaded <= load_last && write_index == 1271;
        end
    end
    reg [3:0] divider;
    reg [11:0] sample_index;
    reg [2:0] half_slot_symbol;
    reg [4:0] half_slot;
    reg end_symbol, first_symbol;
    always @(posedge clk) begin
        if (!resetn) begin
            divider <= 0;
            sample_index <= 0;
            half_slot_symbol <= 0;
            half_slot <= 0;
            end_symbol <= 0;
            first_symbol <= 1;
            frame <= 0;
        end else begin
            divider <= divider + 1'b1;
            frame <= {7'b0, first_symbol && divider == 0 && sample_index == 0};
            end_symbol <= sample_index == (half_slot_symbol == 0 ? 2207 : 2191);
            if (divider == 15) begin
                if (end_symbol) begin
                    sample_index <= 0;
                    half_slot_symbol <= half_slot_symbol == 6 ? 0 : half_slot_symbol + 1'b1;
                    if (half_slot_symbol == 6)
                        half_slot <= half_slot == 19 ? 0 : half_slot + 1'b1;
                    first_symbol <= half_slot == 19 && half_slot_symbol == 6;
                end else sample_index <= sample_index + 1'b1;
            end
        end
    end
    reg reading;
    always @(posedge clk) begin
        if (!resetn) begin
            ft_valid <= 0;
            ft_last <= 0;
            next_index <= 0;
            reading <= 0;
        end else begin
            if (loaded && sample_index == 4 && divider == 0)
                reading <= 1;
            if (!ft_valid || ft_ready) begin
                ft_valid <= reading;
                ft_data <= samples[next_index];
                ft_last <= next_index == 1271;
                if (reading) begin
                    next_index <= next_index + 1'b1;
                    if (next_index == 1271) begin
                        next_index <= 0;
                        reading <= 0;
                    end
                end
            end
        end
    end

    // Discard until a packet boundary, then forward exactly one full packet.
    wire request_sync;
    xpm_cdc_single #(.DEST_SYNC_FF(3), .SRC_INPUT_REG(0)) sync_request
        (.src_clk(1'b0), .src_in(capture_request), .dest_clk(clk), .dest_out(request_sync));
    reg capture, done;
    assign ul_ready = !capture || capture_ready;
    assign capture_data = ul_data;
    assign capture_valid = capture && ul_valid;
    assign capture_last = ul_last;
    always @(posedge clk) begin
        if (!resetn || !request_sync) begin
            capture <= 0;
            done <= 0;
        end else if (ul_valid && ul_ready && ul_last && !done) begin
            capture <= !capture;
            done <= capture;
        end
    end
endmodule
