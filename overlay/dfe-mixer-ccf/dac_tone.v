// SPDX-License-Identifier: BSD-3-Clause
// 128-sample sine ROM, 16 time-adjacent samples per converter beat.
module dac_tone(input wire dac_clk, dac_resetn, ready, input wire [2:0] control,
                output reg [255:0] samples = 0);
    (* ASYNC_REG="TRUE" *) reg [1:0] enable_sync = 0;
    reg [2:0] phase = 0;
    always @(posedge dac_clk) begin
        enable_sync <= {enable_sync[0],control[0]};
        if (!dac_resetn || !enable_sync[1]) begin
            phase <= 0;
            samples <= 0;
        end else if (ready) begin
            phase <= phase + 1'b1;
            case (phase)
                3'd0: samples <= 256'h157d144d131011c710740f160daf0c3f0ac8094a07c6063e04b2032301920000;
                3'd1: samples <= 256'h1ff61fd91fa71f631f0a1e9f1e211d901ced1c391b731a9b19b418bd17b616a1;
                3'd2: samples <= 256'h17b618bd19b41a9b1b731c391ced1d901e211e9f1f0a1f631fa71fd91ff62000;
                3'd3: samples <= 256'h0192032304b2063e07c6094a0ac80c3f0daf0f16107411c71310144d157d16a1;
                3'd4: samples <= 256'hea83ebb3ecf0ee39ef8cf0eaf251f3c1f538f6b6f83af9c2fb4efcddfe6e0000;
                3'd5: samples <= 256'he00ae027e059e09de0f6e161e1dfe270e313e3c7e48de565e64ce743e84ae95f;
                3'd6: samples <= 256'he84ae743e64ce565e48de3c7e313e270e1dfe161e0f6e09de059e027e00ae000;
                3'd7: samples <= 256'hfe6efcddfb4ef9c2f83af6b6f538f3c1f251f0eaef8cee39ecf0ebb3ea83e95f;
            endcase
        end
    end
endmodule
