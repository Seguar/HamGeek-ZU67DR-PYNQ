/******************************************************************************
* Copyright (C) 2021-2022 Xilinx, Inc.  All rights reserved.
* Copyright (C) 2022 - 2024 Advanced Micro Devices, Inc. All Rights Reserved.
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
typedef enum XDfeMix_StateId {
 XDFEMIX_STATE_NOT_READY = 0,
 XDFEMIX_STATE_READY,
 XDFEMIX_STATE_RESET,
 XDFEMIX_STATE_CONFIGURED,
 XDFEMIX_STATE_INITIALISED,
 XDFEMIX_STATE_OPERATIONAL
} XDfeMix_StateId;
typedef struct {
 u32 Major;
 u32 Minor;
 u32 Revision;
 u32 Patch;
} XDfeMix_Version;
typedef struct {
 u32 TriggerEnable;
 u32 Mode;
 u32 TuserEdgeLevel;
 u32 StateOutput;
 u32 TUSERBit;
} XDfeMix_Trigger;
typedef struct {
 XDfeMix_Trigger Activate;
 XDfeMix_Trigger LowPower;
 XDfeMix_Trigger CCUpdate;
 XDfeMix_Trigger Switch;
} XDfeMix_TriggerCfg;
typedef struct {
 u32 Length;
 s32 CCID[(16)];
 s32 NotUsedCCID;
} XDfeMix_CCSequence;
typedef struct {
 u32 Mode;
 u32 NumAntenna;
 u32 MaxUseableCcids;
 u32 Lanes;
 u32 AntennaInterleave;
 u32 MixerCps;
 u32 NumAuxiliary;
 u32 DataIWidth;
 u32 DataOWidth;
 u32 TUserWidth;
} XDfeMix_ModelParameters;
typedef struct {
 XDfeMix_Version Version;
 XDfeMix_ModelParameters ModelParams;
} XDfeMix_Cfg;
typedef struct {
 XDfeMix_CCSequence Sequence;
 u32 TuserSelect;
} XDfeMix_Init;
typedef struct {
 u32 PhaseOffset;
} XDfeMix_PhaseOffset;
typedef struct {
 u32 FrequencyControlWord;
 u32 SingleModCount;
 u32 DualModCount;
 XDfeMix_PhaseOffset PhaseOffset;
 u32 TriggerUpdateFlag;
} XDfeMix_Frequency;
typedef struct {
 u32 PhaseAcc;
 u32 DualModCount;
 u32 DualModSel;
 u32 TriggerUpdateFlag;
} XDfeMix_Phase;
typedef struct {
 XDfeMix_Frequency FrequencyCfg;
 XDfeMix_Phase PhaseCfg;
 u32 NCOGain;
} XDfeMix_NCO;
typedef struct {
 u32 NCOIdx;
 u32 Rate;
 u32 CCGain;
} XDfeMix_InternalDUCDDCCfg;
typedef struct {
 u32 NCOIdx;
 u32 CCGain;
} XDfeMix_DUCDDCCfg;
typedef struct {
 u32 Enable;
 u32 AuxGain;
} XDfeMix_AuxiliaryCfg;
typedef struct {
 XDfeMix_DUCDDCCfg DUCDDCCfg;
} XDfeMix_CarrierCfg;
typedef struct {
 u32 Gain[(8)];
} XDfeMix_AntennaCfg;
typedef struct {
 XDfeMix_CCSequence Sequence;
 XDfeMix_InternalDUCDDCCfg DUCDDCCfg[(16)];
 XDfeMix_NCO NCO[(20)];
 XDfeMix_AuxiliaryCfg AuxiliaryCfg[(4)];
 XDfeMix_AntennaCfg AntennaCfg;
} XDfeMix_CCCfg;
typedef struct {
 u32 Stage;
 u32 Antenna;
 u32 NcoId;
 u32 Mode;
} XDfeMix_DUCDDCStatus;
typedef struct {
 u32 Stage;
 u32 Antenna;
 u32 NcoId;
 u32 Mode;
} XDfeMix_MixerStatus;
typedef struct {
 u32 DUCDDCOverflow;
 u32 MixerOverflow;
 u32 CCUpdate;
 u32 LowPower;
 u32 Switchable;
 u32 CCSequenceError;
 u32 CCUpdateError;
 u32 LowPowerError;
 u32 SwitchableError;
} XDfeMix_Status;
typedef XDfeMix_Status XDfeMix_InterruptMask;
typedef struct {
 u32 DeviceId;
 metal_phys_addr_t BaseAddr;
 u32 Mode;
 u32 NumAntenna;
 u32 MaxUseableCcids;
 u32 Lanes;
 u32 AntennaInterleave;
 u32 MixerCps;
 u32 NumAuxiliary;
 u32 DataIWidth;
 u32 DataOWidth;
 u32 TUserWidth;
} XDfeMix_Config;
typedef struct {
 XDfeMix_Config Config;
 XDfeMix_StateId StateId;
 s32 NotUsedCCID;
 s32 NotUsedCCID_UL;
 u32 SequenceLength;
 char NodeName[(50)];
 struct metal_io_region *Io;
 struct metal_device *Device;
} XDfeMix;
XDfeMix *XDfeMix_InstanceInit(const char *DeviceNodeName);
void XDfeMix_InstanceClose(XDfeMix *InstancePtr);
void XDfeMix_WriteReg(const XDfeMix *InstancePtr, u32 AddrOffset, u32 Data);
u32 XDfeMix_ReadReg(const XDfeMix *InstancePtr, u32 AddrOffset);
void XDfeMix_Reset(XDfeMix *InstancePtr);
void XDfeMix_Configure(XDfeMix *InstancePtr, XDfeMix_Cfg *Cfg);
void XDfeMix_Initialize(XDfeMix *InstancePtr, XDfeMix_Init *Init);
void XDfeMix_Activate(XDfeMix *InstancePtr, bool EnableLowPower);
void XDfeMix_Deactivate(XDfeMix *InstancePtr);
XDfeMix_StateId XDfeMix_GetStateID(XDfeMix *InstancePtr);
void XDfeMix_GetCurrentCCCfg(const XDfeMix *InstancePtr, XDfeMix_CCCfg *CCCfg);
void XDfeMix_GetCurrentCCCfgSwitchable(const XDfeMix *InstancePtr,
           XDfeMix_CCCfg *CCCfgDownlink,
           XDfeMix_CCCfg *CCCfgUplink);
void XDfeMix_GetEmptyCCCfg(const XDfeMix *InstancePtr, XDfeMix_CCCfg *CCCfg);
void XDfeMix_GetCarrierCfgAndNCO(const XDfeMix *InstancePtr,
     XDfeMix_CCCfg *CCCfg, s32 CCID,
     u32 *CCSeqBitmap,
     XDfeMix_CarrierCfg *CarrierCfg,
     XDfeMix_NCO *NCO);
void XDfeMix_SetAntennaCfgInCCCfg(const XDfeMix *InstancePtr,
      XDfeMix_CCCfg *CCCfg,
      XDfeMix_AntennaCfg *AntennaCfg);
u32 XDfeMix_AddCCtoCCCfg(XDfeMix *InstancePtr, XDfeMix_CCCfg *CCCfg, s32 CCID,
    u32 CCSeqBitmap, const XDfeMix_CarrierCfg *CarrierCfg,
    const XDfeMix_NCO *NCO);
void XDfeMix_RemoveCCfromCCCfg(XDfeMix *InstancePtr, XDfeMix_CCCfg *CCCfg,
          s32 CCID);
void XDfeMix_AddAuxNCOtoCCCfg(XDfeMix *InstancePtr, XDfeMix_CCCfg *CCCfg,
         const s32 AuxId, const XDfeMix_NCO *NCO,
         const XDfeMix_AuxiliaryCfg *AuxCfg);
void XDfeMix_RemoveAuxNCOfromCCCfg(XDfeMix *InstancePtr, XDfeMix_CCCfg *CCCfg,
       const s32 AuxId);
u32 XDfeMix_UpdateCCinCCCfg(XDfeMix *InstancePtr, XDfeMix_CCCfg *CCCfg,
       s32 CCID, const XDfeMix_CarrierCfg *CarrierCfg);
u32 XDfeMix_SetNextCCCfgAndTrigger(XDfeMix *InstancePtr,
       const XDfeMix_CCCfg *CCCfg);
u32 XDfeMix_SetNextCCCfgAndTriggerSwitchable(XDfeMix *InstancePtr,
          XDfeMix_CCCfg *CCCfgDownlink,
          XDfeMix_CCCfg *CCCfgUplink);
u32 XDfeMix_AddCC(XDfeMix *InstancePtr, s32 CCID, u32 CCSeqBitmap,
    const XDfeMix_CarrierCfg *CarrierCfg, const XDfeMix_NCO *NCO);
u32 XDfeMix_RemoveCC(XDfeMix *InstancePtr, s32 CCID);
u32 XDfeMix_MoveCC(XDfeMix *InstancePtr, s32 CCID, u32 Rate, u32 FromNCO,
     u32 ToNCO);
u32 XDfeMix_UpdateCC(XDfeMix *InstancePtr, s32 CCID,
       const XDfeMix_CarrierCfg *CarrierCfg);
u32 XDfeMix_SetAntennaGain(XDfeMix *InstancePtr, u32 AntennaId,
      u32 AntennaGain);
u32 XDfeMix_UpdateAntennaCfg(XDfeMix *InstancePtr,
        XDfeMix_AntennaCfg *AntennaCfg);
void XDfeMix_GetTriggersCfg(const XDfeMix *InstancePtr,
       XDfeMix_TriggerCfg *TriggerCfg);
void XDfeMix_SetTriggersCfg(const XDfeMix *InstancePtr,
       XDfeMix_TriggerCfg *TriggerCfg);
void XDfeMix_GetDUCDDCStatus(const XDfeMix *InstancePtr,
        XDfeMix_DUCDDCStatus *DUCDDCStatus);
void XDfeMix_GetMixerStatus(const XDfeMix *InstancePtr,
       XDfeMix_MixerStatus *MixerStatus);
void XDfeMix_GetInterruptMask(const XDfeMix *InstancePtr,
         XDfeMix_InterruptMask *Mask);
void XDfeMix_SetInterruptMask(const XDfeMix *InstancePtr,
         const XDfeMix_InterruptMask *Mask);
void XDfeMix_GetEventStatus(const XDfeMix *InstancePtr, XDfeMix_Status *Status);
void XDfeMix_ClearEventStatus(const XDfeMix *InstancePtr,
         const XDfeMix_Status *Status);
void XDfeMix_SetTUserDelay(const XDfeMix *InstancePtr, u32 Delay);
u32 XDfeMix_GetTUserDelay(const XDfeMix *InstancePtr);
u32 XDfeMix_GetTDataDelay(const XDfeMix *InstancePtr, u32 Tap, u32 *TDataDelay);
u32 XDfeMix_GetCenterTap(const XDfeMix *InstancePtr, u32 Rate, u32 *CenterTap);
void XDfeMix_SetRegBank(const XDfeMix *InstancePtr, u32 RegBank);
void XDfeMix_GetVersions(const XDfeMix *InstancePtr, XDfeMix_Version *SwVersion,
    XDfeMix_Version *HwVersion);
XDfeMix *xdfe_mix_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_mix_mmio_close(XDfeMix *inst);
