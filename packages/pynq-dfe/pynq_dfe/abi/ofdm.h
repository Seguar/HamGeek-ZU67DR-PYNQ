/******************************************************************************
* Copyright (C) 2022 Xilinx, Inc.  All rights reserved.
* Copyright (C) 2022-2025 Advanced Micro Devices, Inc. All rights reserved.
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
typedef enum XDfeOfdm_StateId {
 XDFEOFDM_STATE_NOT_READY = 0,
 XDFEOFDM_STATE_READY,
 XDFEOFDM_STATE_RESET,
 XDFEOFDM_STATE_CONFIGURED,
 XDFEOFDM_STATE_INITIALISED,
 XDFEOFDM_STATE_OPERATIONAL
} XDfeOfdm_StateId;
typedef struct {
 u32 Major;
 u32 Minor;
 u32 Revision;
 u32 Patch;
} XDfeOfdm_Version;
typedef struct {
 u32 TriggerEnable;
 u32 Mode;
 u32 TuserEdgeLevel;
 u32 StateOutput;
 u32 TUSERBit;
} XDfeOfdm_Trigger;
typedef struct {
 XDfeOfdm_Trigger Activate;
 XDfeOfdm_Trigger LowPower;
 XDfeOfdm_Trigger CCUpdate;
} XDfeOfdm_TriggerCfg;
typedef struct {
 u32 Length;
 s32 CCID[(16)];
} XDfeOfdm_CCSequence;
typedef struct {
 u32 Length;
 s32 CCID[(16)];
} XDfeOfdm_FTSequence;
typedef struct {
 u32 NumAntenna;
 u32 AntennaInterleave;
 u32 PhaseCompensation;
} XDfeOfdm_ModelParameters;
typedef struct {
 XDfeOfdm_Version Version;
 XDfeOfdm_ModelParameters ModelParams;
} XDfeOfdm_Cfg;
typedef struct {
 u32 CCSequenceLength;
} XDfeOfdm_Init;
typedef struct {
 u32 Numerology;
 u32 FftSize;
 u32 NumSubcarriers;
 u32 ScaleFactor;
 u32 CommsStandard;
 u32 OutputDelay;
 u32 PhaseCompensation[(112)];
} XDfeOfdm_CarrierCfg;
typedef struct {
 u32 Enable;
 u32 Numerology;
 u32 FftSize;
 u32 NumSubcarriers;
 u32 ScaleFactor;
 u32 CommsStandard;
 u32 OutputDelay;
 u32 PhaseCompensation[(112)];
} XDfeOfdm_InternalCarrierCfg;
typedef struct {
 XDfeOfdm_CCSequence CCSequence;
 XDfeOfdm_FTSequence FTSequence;
 XDfeOfdm_InternalCarrierCfg
  CarrierCfg[(16)];
} XDfeOfdm_CCCfg;
typedef struct {
 u32 SaturationCCID;
 u32 SaturationCount;
 u32 CCUpdate;
 u32 FTCCSequenceError;
 u32 Saturation;
 u32 Overflow;
} XDfeOfdm_Status;
typedef struct {
 u32 CCUpdate;
 u32 FTCCSequenceError;
 u32 Saturation;
 u32 Overflow;
} XDfeOfdm_InterruptMask;
typedef struct {
 u32 DeviceId;
 metal_phys_addr_t BaseAddr;
 u32 FrequencyRange;
 u32 NumAntenna;
 u32 AntennaInterleave;
 u32 PhaseCompensation;
} XDfeOfdm_Config;
typedef struct {
 XDfeOfdm_Config Config;
 XDfeOfdm_StateId StateId;
 s32 NotUsedCCID;
 u32 CCSequenceLength;
 char NodeName[(50)];
 struct metal_io_region *Io;
 struct metal_device *Device;
} XDfeOfdm;
XDfeOfdm *XDfeOfdm_InstanceInit(const char *DeviceNodeName);
void XDfeOfdm_InstanceClose(XDfeOfdm *InstancePtr);
void XDfeOfdm_WriteReg(const XDfeOfdm *InstancePtr, u32 AddrOffset, u32 Data);
u32 XDfeOfdm_ReadReg(const XDfeOfdm *InstancePtr, u32 AddrOffset);
void XDfeOfdm_Reset(XDfeOfdm *InstancePtr);
void XDfeOfdm_Configure(XDfeOfdm *InstancePtr, XDfeOfdm_Cfg *Cfg);
void XDfeOfdm_Initialize(XDfeOfdm *InstancePtr, XDfeOfdm_Init *Init);
void XDfeOfdm_Activate(XDfeOfdm *InstancePtr, bool EnableLowPower);
void XDfeOfdm_Deactivate(XDfeOfdm *InstancePtr);
XDfeOfdm_StateId XDfeOfdm_GetStateID(XDfeOfdm *InstancePtr);
void XDfeOfdm_GetCurrentCCCfg(const XDfeOfdm *InstancePtr,
         XDfeOfdm_CCCfg *CCCfg);
void XDfeOfdm_GetEmptyCCCfg(const XDfeOfdm *InstancePtr, XDfeOfdm_CCCfg *CCCfg);
void XDfeOfdm_GetCarrierCfg(const XDfeOfdm *InstancePtr, XDfeOfdm_CCCfg *CCCfg,
       s32 CCID, u32 *CCSeqBitmap,
       XDfeOfdm_CarrierCfg *CarrierCfg);
u32 XDfeOfdm_AddCCtoCCCfg(XDfeOfdm *InstancePtr, XDfeOfdm_CCCfg *CCCfg,
     s32 CCID, u32 CCSeqBitmap,
     const XDfeOfdm_CarrierCfg *CarrierCfg,
     XDfeOfdm_FTSequence *FTSeq);
u32 XDfeOfdm_RemoveCCfromCCCfg(XDfeOfdm *InstancePtr, XDfeOfdm_CCCfg *CCCfg,
          s32 CCID, XDfeOfdm_FTSequence *FTSeq);
u32 XDfeOfdm_UpdateCCinCCCfg(XDfeOfdm *InstancePtr, XDfeOfdm_CCCfg *CCCfg,
        s32 CCID, const XDfeOfdm_CarrierCfg *CarrierCfg,
        XDfeOfdm_FTSequence *FTSeq);
void XDfeOfdm_SetNextCCCfg(const XDfeOfdm *InstancePtr,
      const XDfeOfdm_CCCfg *NextCCCfg);
u32 XDfeOfdm_EnableCCUpdateTrigger(const XDfeOfdm *InstancePtr);
u32 XDfeOfdm_SetNextCCCfgAndTrigger(const XDfeOfdm *InstancePtr,
        XDfeOfdm_CCCfg *CCCfg);
u32 XDfeOfdm_AddCC(XDfeOfdm *InstancePtr, s32 CCID, u32 CCSeqBitmap,
     const XDfeOfdm_CarrierCfg *CarrierCfg,
     XDfeOfdm_FTSequence *FTSeq);
u32 XDfeOfdm_RemoveCC(XDfeOfdm *InstancePtr, s32 CCID,
        XDfeOfdm_FTSequence *FTSeq);
u32 XDfeOfdm_UpdateCC(XDfeOfdm *InstancePtr, s32 CCID,
        const XDfeOfdm_CarrierCfg *CarrierCfg,
        XDfeOfdm_FTSequence *FTSeq);
void XDfeOfdm_GetTriggersCfg(const XDfeOfdm *InstancePtr,
        XDfeOfdm_TriggerCfg *TriggerCfg);
void XDfeOfdm_SetTriggersCfg(const XDfeOfdm *InstancePtr,
        XDfeOfdm_TriggerCfg *TriggerCfg);
void XDfeOfdm_SetTuserOutFrameLocation(const XDfeOfdm *InstancePtr,
           u32 TuserOutFrameLocation);
u32 XDfeOfdm_GetTuserOutFrameLocation(const XDfeOfdm *InstancePtr);
void XDfeOfdm_SetTuserCCUpdateTrigger(const XDfeOfdm *InstancePtr,
          u32 TuserCCUpdateTrigger);
u32 XDfeOfdm_GetTuserCCUpdateTrigger(const XDfeOfdm *InstancePtr);
void XDfeOfdm_GetEventStatus(const XDfeOfdm *InstancePtr,
        XDfeOfdm_Status *Status);
void XDfeOfdm_ClearEventStatus(const XDfeOfdm *InstancePtr,
          const XDfeOfdm_Status *Status);
void XDfeOfdm_SetInterruptMask(const XDfeOfdm *InstancePtr,
          const XDfeOfdm_InterruptMask *Mask);
void XDfeOfdm_GetInterruptMask(const XDfeOfdm *InstancePtr,
          XDfeOfdm_InterruptMask *Mask);
void XDfeOfdm_SetTUserDelay(const XDfeOfdm *InstancePtr, u32 Delay);
u32 XDfeOfdm_GetTUserDelay(const XDfeOfdm *InstancePtr);
u32 XDfeOfdm_GetDataLatency(const XDfeOfdm *InstancePtr);
void XDfeOfdm_GetVersions(const XDfeOfdm *InstancePtr,
     XDfeOfdm_Version *SwVersion,
     XDfeOfdm_Version *HwVersion);
XDfeOfdm *xdfe_ofdm_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_ofdm_mmio_close(XDfeOfdm *inst);
