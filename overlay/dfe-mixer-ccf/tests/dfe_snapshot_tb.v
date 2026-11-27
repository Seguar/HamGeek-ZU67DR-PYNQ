`timescale 1ns/1ps
module tb;
reg adc_clk=0, host_clk=0, resetn=0;
always #1.6 adc_clk=~adc_clk;
always #5 host_clk=~host_clk;
reg [4:0] ctl=0;
wire [7:0] marker;
reg [31:0] raw=0, filtered=0;
reg raw_valid=1, filtered_valid=0, ready=0;
wire [31:0] data;
wire valid,last;
snapshot dut(adc_clk,resetn,host_clk,resetn,ctl,2'b00,,marker,raw,filtered,raw_valid,filtered_valid,data,valid,ready,last);
integer cycles=0, previous_marker=-1, markers=0;
always @(negedge adc_clk) if (resetn) begin
 cycles=cycles+1;
 if(marker!=0) begin
   if(marker!=1 || (previous_marker>=0 && cycles-previous_marker!=16)) $fatal(1,"marker spacing");
   previous_marker=cycles; markers=markers+1;
 end
end
integer frame=0,n=0,h=0;
reg [31:0] prev;
always @(negedge adc_clk) begin
 raw<=raw+1;
 filtered_valid<=!filtered_valid;
 if(filtered_valid) filtered<=filtered+3;
end
always @(negedge host_clk) begin
 h=h+1; ready=(h%11<5);
end
always @(posedge host_clk) begin
 if(valid && ready) begin
   if(n>0 && data!==prev+(frame==0?1:3)) $fatal(1,"bad sequence");
   if(last !== (n==1023)) $fatal(1,"bad TLAST");
   prev=data;
   if(n==1023) begin n=0; frame=frame+1; end
   else n=n+1;
 end
end
initial begin
 #51 resetn=1; #50 ctl=4; #100 ctl=6;
 wait(frame==1); #100 ctl=2; #100 ctl=0;
 wait(frame==2); #100;
 if(markers<128) $fatal(1,"missing mixer triggers");
 $display("PASS: marker every 16 clocks, raw/filtered capture and stalls"); $finish;
end
initial begin #200000; $fatal(1,"timeout"); end
endmodule
