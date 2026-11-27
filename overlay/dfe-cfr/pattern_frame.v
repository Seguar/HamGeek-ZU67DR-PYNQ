// SPDX-License-Identifier: BSD-3-Clause
// One fixed frame (16384 IQ words). Buffer both sides of the streaming CFR.
module pattern_frame(
    input clk, input resetn,
    input [31:0] tx_data, input tx_valid, input tx_last, output tx_ready,
    output [31:0] cfr_in, input cfr_ready,
    input [31:0] cfr_out, input cfr_valid,
    output [31:0] rx_data, output rx_valid, output rx_last, input rx_ready
);
    localparam LOAD=0, PRIME=1, PLAY=2, DRAIN=3;
    reg [1:0] state;
    reg [13:0] pos;
    reg [31:0] stimulus [0:16383];
    reg [31:0] capture [0:16383];
    reg [31:0] sample, result;
    wire taking = (state == PLAY && cfr_ready);
    wire sending = (state == DRAIN && rx_ready);
    assign tx_ready = state == LOAD;
    assign cfr_in = state == PLAY ? sample : 0;
    assign rx_valid = state == DRAIN;
    assign rx_data = result;
    assign rx_last = &pos;

    always @(posedge clk) begin
        if (tx_valid && tx_ready)
            stimulus[pos] <= tx_data;
        sample <= stimulus[state == PLAY ? pos + {13'b0,taking} : 14'd0];
        if (taking)
            capture[pos] <= cfr_valid ? cfr_out : 32'h80008000;
        result <= capture[state == DRAIN ? pos + {13'b0,sending} : 14'd0];
        if (!resetn) begin
            state <= LOAD;
            pos <= 0;
        end else begin
            case (state)
                LOAD: if (tx_valid) begin
                    pos <= pos + 1'b1;
                    if (tx_last) begin
                        pos <= 0;
                        if (&pos) state <= PRIME;
                    end
                end
                PRIME: state <= PLAY;
                PLAY: if (taking) begin
                    pos <= pos + 1'b1;
                    if (&pos) state <= DRAIN;
                end
                DRAIN: if (sending) begin
                    pos <= pos + 1'b1;
                    if (&pos) state <= LOAD;
                end
            endcase
        end
    end
endmodule
