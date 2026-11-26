# Verified XCZU67DR PL DDR4 pinout

Applies to the tested HamGeek XCZU67DR PCIe V1 card, PCB rev 2.1. The map was recovered by JTAG boundary scan on the sister XCZU47DR and verified using the x32 controller on the XCZU67DR. The single-rank DDR4-2400 interface has 2 GiB total. Bank 65 DCI VRP is AL14. Bank 66 DCI VRP is AN3. The tested MIG reference is 200 MHz.

Balls are listed in ascending signal-index order. A14, A15 and A16 double as WE_n, CAS_n and RAS_n. CK and DQS use true/complement order. The reference clock uses positive/negative order.

| Signal | FPGA bank | FPGA balls |
| --- | --- | --- |
| `A[0:16]` | 65 | AF14 AK15 AM16 AK14 AF18 AN17 AF16 AM15 AL17 AM17 AJ13 AK18 AP15 AN18 AH14 AN14 AN15 |
| `BA` | 65 | AF13 AP16 |
| `BG` | 65 | AG14 |
| `CS_N` | 65 | AM14 |
| `CKE` | 65 | AH18 |
| `ODT` | 65 | AH13 |
| `ACT_n` | 65 | AJ18 |
| `RESET_n` | 65 | AE16 |
| `CK t/c` | 65 | AJ16 AJ15 |
| `MIG refclk p/n` | 65 | AJ17 AK16 |
| `DQ[0:7]` | 66 | AP6 AP5 AM6 AM5 AP3 AP2 AN2 AN1 |
| `DQS0 t/c, DM0_n` | 66 | AN5 AN4 AP8 |
| `DQ[8:15]` | 66 | AN13 AN12 AN8 AN7 AP11 AP10 AM10 AN10 |
| `DQS1 t/c, DM1_n` | 66 | AM8 AM7 AP13 |
| `DQ[16:23]` | 66 | AM12 AM11 AK13 AL13 AK10 AK9 AJ11 AK11 |
| `DQS2 t/c, DM2_n` | 66 | AL12 AL11 AL9 |
| `DQ[24:31]` | 66 | AH10 AH9 AG10 AG9 AF12 AF11 AE11 AF10 |
| `DQS3 t/c, DM3_n` | 66 | AJ10 AJ9 AG12 |

The model using the vendor PDF pinout timed out during memory calibration. With this pinout the controller calibrated, passed 31 address probes in each polarity and completed five full 2 GiB passes without mismatches. See the [bring-up report](https://seguar.github.io/hamgeek-zu67dr-bringup/#pl-ddr4) for the test conditions.
