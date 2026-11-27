/******************************************************************************
* Copyright (C) 2021-2022 Xilinx, Inc.  All rights reserved.
* Copyright (C) 2022-2024 Advanced Micro Devices, Inc. All rights reserved.
* SPDX-License-Identifier: MIT
******************************************************************************/
typedef unsigned long metal_phys_addr_t;
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int32_t s32;
typedef int16_t s16;
typedef uint64_t u64;
typedef int64_t s64;
typedef int8_t s8;
typedef enum XDfeCcf_StateId {
 XDFECCF_STATE_NOT_READY = 0,
 XDFECCF_STATE_READY,
 XDFECCF_STATE_RESET,
 XDFECCF_STATE_CONFIGURED,
 XDFECCF_STATE_INITIALISED,
 XDFECCF_STATE_OPERATIONAL
} XDfeCcf_StateId;
typedef struct {
 u32 Major;
 u32 Minor;
 u32 Revision;
 u32 Patch;
} XDfeCcf_Version;
typedef struct {
 u32 TriggerEnable;
 u32 Mode;
 u32 TuserEdgeLevel;
 u32 StateOutput;
 u32 TUSERBit;
} XDfeCcf_Trigger;
typedef struct {
 XDfeCcf_Trigger Activate;
 XDfeCcf_Trigger LowPower;
 XDfeCcf_Trigger CCUpdate;
 XDfeCcf_Trigger Switch;
} XDfeCcf_TriggerCfg;
typedef struct {
 u32 Length;
 s32 CCID[(16)];
 s32 NotUsedCCID;
} XDfeCcf_CCSequence;
typedef struct {
 u32 NumAntenna;
 u32 NumCCPerAntenna;
 u32 AntennaInterleave;
 u32 Switchable;
} XDfeCcf_ModelParameters;
typedef struct {
 XDfeCcf_Version Version;
 XDfeCcf_ModelParameters ModelParams;
} XDfeCcf_Cfg;
typedef struct {
 XDfeCcf_CCSequence Sequence;
 u32 GainStage;
 u32 TuserSelect;
} XDfeCcf_Init;
typedef struct {
 u32 Num;
 u32 Symmetric;
 s16 Value[(128)];
} XDfeCcf_Coefficients;
typedef struct {
 u32 Gain;
 u32 ImagCoeffSet;
 u32 RealCoeffSet;
} XDfeCcf_CarrierCfg;
typedef struct {
 u32 Enable;
 u32 Flush;
 u32 MappedId;
 u32 Gain;
 u32 ImagCoeffSet;
 u32 RealCoeffSet;
} XDfeCcf_InternalCarrierCfg;
typedef struct {
 u32 Enable[(8)];
} XDfeCcf_AntennaCfg;
typedef struct {
 XDfeCcf_CCSequence Sequence;
 XDfeCcf_InternalCarrierCfg
  CarrierCfg[(16)];
 XDfeCcf_AntennaCfg AntennaCfg;
} XDfeCcf_CCCfg;
typedef struct {
 u32 OverflowBeforeGainReal;
 u32 OverflowBeforeGainImag;
 u32 OverflowAfterGainReal;
 u32 OverflowAfterGainImag;
 u32 OverflowAntenna;
 u32 OverflowCCID;
 u32 OverflowSwitch;
} XDfeCcf_OverflowStatus;
typedef struct {
 u32 Overflow;
 u32 CCUpdate;
 u32 CCSequenceError;
} XDfeCcf_Status;
typedef XDfeCcf_Status XDfeCcf_InterruptMask;
typedef struct {
 u32 DeviceId;
 metal_phys_addr_t BaseAddr;
 u32 NumAntenna;
 u32 NumCCPerAntenna;
 u32 AntennaInterleave;
 u32 Switchable;
} XDfeCcf_Config;
typedef struct {
 XDfeCcf_Config Config;
 XDfeCcf_StateId StateId;
 s32 NotUsedCCID;
 s32 NotUsedCCID_UL;
 u32 SequenceLength;
 char NodeName[(50)];
 struct metal_io_region *Io;
 struct metal_device *Device;
} XDfeCcf;
XDfeCcf *XDfeCcf_InstanceInit(const char *DeviceNodeName);
void XDfeCcf_InstanceClose(XDfeCcf *InstancePtr);
void XDfeCcf_WriteReg(const XDfeCcf *InstancePtr, u32 AddrOffset, u32 Data);
u32 XDfeCcf_ReadReg(const XDfeCcf *InstancePtr, u32 AddrOffset);
void XDfeCcf_Reset(XDfeCcf *InstancePtr);
void XDfeCcf_Configure(XDfeCcf *InstancePtr, XDfeCcf_Cfg *Cfg);
void XDfeCcf_Initialize(XDfeCcf *InstancePtr, XDfeCcf_Init *Init);
void XDfeCcf_Activate(XDfeCcf *InstancePtr, bool EnableLowPower);
void XDfeCcf_Deactivate(XDfeCcf *InstancePtr);
XDfeCcf_StateId XDfeCcf_GetStateID(XDfeCcf *InstancePtr);
void XDfeCcf_GetCurrentCCCfg(const XDfeCcf *InstancePtr, XDfeCcf_CCCfg *CCCfg);
void XDfeCcf_GetCurrentCCCfgSwitchable(const XDfeCcf *InstancePtr,
           XDfeCcf_CCCfg *CCCfgDownlink,
           XDfeCcf_CCCfg *CCCfgUplink);
void XDfeCcf_GetEmptyCCCfg(const XDfeCcf *InstancePtr, XDfeCcf_CCCfg *CCCfg);
void XDfeCcf_GetCarrierCfg(const XDfeCcf *InstancePtr, XDfeCcf_CCCfg *CCCfg,
      s32 CCID, u32 *CCSeqBitmap,
      XDfeCcf_CarrierCfg *CarrierCfg);
void XDfeCcf_SetAntennaCfgInCCCfg(const XDfeCcf *InstancePtr,
      XDfeCcf_CCCfg *CCCfg,
      XDfeCcf_AntennaCfg *AntennaCfg);
u32 XDfeCcf_AddCCtoCCCfg(XDfeCcf *InstancePtr, XDfeCcf_CCCfg *CCCfg, s32 CCID,
    u32 CCSeqBitmap, const XDfeCcf_CarrierCfg *CarrierCfg);
void XDfeCcf_RemoveCCfromCCCfg(XDfeCcf *InstancePtr, XDfeCcf_CCCfg *CCCfg,
          s32 CCID);
void XDfeCcf_UpdateCCinCCCfg(const XDfeCcf *InstancePtr, XDfeCcf_CCCfg *CCCfg,
        s32 CCID, const XDfeCcf_CarrierCfg *CarrierCfg);
u32 XDfeCcf_SetNextCCCfgAndTrigger(XDfeCcf *InstancePtr, XDfeCcf_CCCfg *CCCfg);
u32 XDfeCcf_SetNextCCCfgAndTriggerSwitchable(XDfeCcf *InstancePtr,
          XDfeCcf_CCCfg *CCCfgDownlink,
          XDfeCcf_CCCfg *CCCfgUplink);
u32 XDfeCcf_AddCC(XDfeCcf *InstancePtr, s32 CCID, u32 CCSeqBitmap,
    const XDfeCcf_CarrierCfg *CarrierCfg);
u32 XDfeCcf_RemoveCC(XDfeCcf *InstancePtr, s32 CCID);
u32 XDfeCcf_UpdateCC(XDfeCcf *InstancePtr, s32 CCID,
       const XDfeCcf_CarrierCfg *CarrierCfg);
u32 XDfeCcf_UpdateAntenna(XDfeCcf *InstancePtr, u32 Ant, bool Enabled);
u32 XDfeCcf_UpdateAntennaCfg(XDfeCcf *InstancePtr,
        XDfeCcf_AntennaCfg *AntennaCfg);
u32 XDfeCcf_UpdateAntennaCfgSwitchable(XDfeCcf *InstancePtr,
           XDfeCcf_AntennaCfg *AntennaCfgDownlink,
           XDfeCcf_AntennaCfg *AntennaCfgUplink);
void XDfeCcf_GetTriggersCfg(const XDfeCcf *InstancePtr,
       XDfeCcf_TriggerCfg *TriggerCfg);
void XDfeCcf_SetTriggersCfg(const XDfeCcf *InstancePtr,
       XDfeCcf_TriggerCfg *TriggerCfg);
void XDfeCcf_GetCC(const XDfeCcf *InstancePtr, s32 CCID,
     XDfeCcf_CarrierCfg *CarrierCfg);
void XDfeCcf_GetActiveSets(const XDfeCcf *InstancePtr, u32 *IsActive);
void XDfeCcf_LoadCoefficients(XDfeCcf *InstancePtr, u32 Set, u32 Shift,
         const XDfeCcf_Coefficients *Coeffs);
void XDfeCcf_GetOverflowStatus(const XDfeCcf *InstancePtr,
          XDfeCcf_OverflowStatus *Status);
void XDfeCcf_GetEventStatus(const XDfeCcf *InstancePtr, XDfeCcf_Status *Status);
void XDfeCcf_ClearEventStatus(const XDfeCcf *InstancePtr,
         const XDfeCcf_Status *Status);
void XDfeCcf_SetInterruptMask(const XDfeCcf *InstancePtr,
         const XDfeCcf_InterruptMask *Mask);
void XDfeCcf_GetInterruptMask(const XDfeCcf *InstancePtr,
         XDfeCcf_InterruptMask *Mask);
void XDfeCcf_SetTUserDelay(const XDfeCcf *InstancePtr, u32 Delay);
u32 XDfeCcf_GetTUserDelay(const XDfeCcf *InstancePtr);
u32 XDfeCcf_GetTDataDelay(XDfeCcf *InstancePtr, u32 Tap, s32 CCID,
     u32 Symmetric, u32 Num, u32 *TDataDelay);
u32 XDfeCcf_GetTDataDelayFromCCCfg(XDfeCcf *InstancePtr, u32 Tap, s32 CCID,
       XDfeCcf_CCCfg *CCCfg, u32 Symmetric, u32 Num,
       u32 *TDataDelay);
void XDfeCcf_SetRegBank(const XDfeCcf *InstancePtr, u32 RegBank);
void XDfeCcf_GetVersions(const XDfeCcf *InstancePtr, XDfeCcf_Version *SwVersion,
    XDfeCcf_Version *HwVersion);
XDfeCcf *xdfe_ccf_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_ccf_mmio_close(XDfeCcf *inst);
