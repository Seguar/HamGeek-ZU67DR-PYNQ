`timescale 1ns/1ps
module tb_tone;
    reg clk = 0, resetn = 0, ready = 1;
    reg [4:0] control = 0;
    wire [255:0] samples;
    wire [1:0] status;

    dac_tone dut(clk, resetn, ready, control, samples, status);
    always #0.8 clk = ~clk;

    integer mode, phase, lane, sample, expected, stalls = 0;
    real angle, value;
    reg [255:0] previous;

    initial begin
        repeat (5) @(negedge clk);
        if (samples !== 0 || status !== 0) $fatal;
        resetn = 1;
        for (mode = 0; mode < 4; mode = mode + 1) begin
            control = mode << 3;
            repeat (5) @(negedge clk);
            control[0] = 1;
            wait (samples != 0);
            for (phase = 0; phase < 16; phase = phase + 1) begin
                @(negedge clk);
                if (status !== 1) $fatal(1, "playback not active");
                for (lane = 0; lane < 16; lane = lane + 1) begin
                    angle = 6.283185307179586 * (16 * phase + lane) / 256;
                    case (mode)
                        0: value = 8192 * $sin(2*angle);
                        1: value = 8192 * $sin(angle);
                        2: value = 8192 * $sin(3*angle);
                        3: value = 4096 * ($sin(angle) + $sin(3*angle));
                    endcase
                    expected = $rtoi(value + (value < 0 ? -0.5 : 0.5));
                    sample = $signed(samples[16*lane+:16]);
                    if (sample != expected) $fatal(1, "mode/phase/lane %0d/%0d/%0d", mode, phase, lane);
                end
                if (phase % 3 == 1) begin
                    ready = 0;
                    previous = samples;
                    repeat (4) begin
                        @(negedge clk);
                        if (samples !== previous) $fatal(1, "changed during stall");
                    end
                    stalls = stalls + 1;
                    ready = 1;
                end
            end
            control = 0;
            repeat (5) @(negedge clk);
            if (samples !== 0 || status !== 0) $fatal(1, "not idle");
        end
        ready = 0;
        control = 1;
        wait (status[0]);
        repeat (65535) @(posedge clk);
        @(negedge clk);
        if (status[1]) $fatal(1, "early timeout");
        @(negedge clk);
        if (status !== 3) $fatal(1, "missing timeout");
        control = 0;
        repeat (5) @(negedge clk);
        if (status !== 2) $fatal(1, "fault should persist at idle");
        resetn = 0;
        @(negedge clk);
        if (status !== 0) $fatal(1, "reset did not clear fault");
        $display("PASS: four waveforms, %0d stalls, busy, sticky fault and reset", stalls);
        $finish;
    end

    initial begin
        #110000;
        $fatal(1, "timeout");
    end
endmodule
