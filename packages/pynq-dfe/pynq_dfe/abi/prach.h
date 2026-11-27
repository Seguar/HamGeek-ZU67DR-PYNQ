/******************************************************************************
* Copyright (C) 2021-2022 Xilinx, Inc. All rights reserved.
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
typedef enum XDfePrach_StateId {
 XDFEPRACH_STATE_NOT_READY = 0,
 XDFEPRACH_STATE_READY,
 XDFEPRACH_STATE_RESET,
 XDFEPRACH_STATE_CONFIGURED,
 XDFEPRACH_STATE_INITIALISED,
 XDFEPRACH_STATE_OPERATIONAL
} XDfePrach_StateId;
typedef struct {
 u32 Major;
 u32 Minor;
 u32 Revision;
 u32 Patch;
} XDfePrach_Version;
typedef struct {
 u32 TriggerEnable;
 u32 Mode;
 u32 TuserEdgeLevel;
 u32 StateOutput;
 u32 TUSERBit;
} XDfePrach_Trigger;
typedef struct {
 XDfePrach_Trigger Activate;
 XDfePrach_Trigger LowPower;
 XDfePrach_Trigger RachUpdate;
 XDfePrach_Trigger FrameInit[(3)];
} XDfePrach_TriggerCfg;
typedef struct {
 u32 Length;
 s32 CCID[(16)];
} XDfePrach_CCSequence;
typedef struct {
 u32 NumAntenna
  [(3)];
 u32 NumCCPerAntenna
  [(3)];
 u32 NumAntennaChannels
  [(3)];
 u32 NumAntennaSlots
  [(3)];
 u32 NumRachLanes;
 u32 NumRachChannels;
 u32 HasAxisCtrl;
 u32 HasIrq;
 u32 NumBands;
 u32 HasContinuousSched;
} XDfePrach_ModelParameters;
typedef struct {
 XDfePrach_Version Version;
 XDfePrach_ModelParameters ModelParams;
} XDfePrach_Cfg;
typedef struct {
 XDfePrach_CCSequence
  Sequence[(3)];
 bool EnableStaticSchedule;
 bool EnableUseFreqOffset;
} XDfePrach_Init;
typedef struct {
 u32 Enable;
 u32 SCS;
 u32 CCRate;
} XDfePrach_InternalCarrierCfg;
typedef struct {
 u32 SCS;
} XDfePrach_CarrierCfg;
typedef struct {
 XDfePrach_CCSequence Sequence
  [(3)];
 XDfePrach_InternalCarrierCfg CarrierCfg[(3)]
            [(16)];
 u32 AntennaCfg[(8)];
} XDfePrach_CCCfg;
typedef struct {
 u32 PhaseOffset;
 u32 PhaseAcc;
 u32 DualModCount;
 u32 DualModSel;
 s32 UserFreq;
 s32 Frequency;
 u32 FreqSingleModCount;
 u32 FreqDualModCount;
 u32 FreqPhaseOffset;
 u32 NcoGain;
} XDfePrach_NCO;
typedef struct {
 u32 DecimationRate;
 u32 UserSCS;
 u32 RachGain[6];
} XDfePrach_DDCCfg;
typedef struct {
 u32 PatternPeriod;
 u32 FrameID;
 u32 SubframeID;
 u32 SlotId;
 u32 Duration;
 u32 Repeats;
} XDfePrach_Schedule;
typedef struct {
 u32 Enable;
 u32 RCId;
 u32 RachChannel;
 s32 CCID;
 u32 BandId;
} XDfePrach_InternalChannelCfg;
typedef struct {
 u32 RCId;
 u32 RachChannel;
 s32 CCID;
 u32 BandId;
} XDfePrach_ChannelCfg;
typedef struct {
 XDfePrach_InternalChannelCfg InternalRCCfg
  [(16)];
 XDfePrach_NCO NcoCfg[(16)];
 XDfePrach_DDCCfg DdcCfg[(16)];
 XDfePrach_Schedule StaticSchedule
  [(16)];
} XDfePrach_RCCfg;
typedef struct {
 u32 MixerOverflow;
 u32 FirstAntennaOverflowing;
 u32 FirstRCIdOverflowing;
} XDfePrach_MixerStatusOverflow;
typedef struct {
 u32 DecimatorOverflow;
 u32 FirstAntennaOverflowing;
 u32 FirstRCIdOverflowing;
} XDfePrach_DecimatorStatusOverflow;
typedef struct {
 u32 MixerOverrun;
 u32 FirstAntennaOverruning;
 u32 FirstRCIdOverruning;
} XDfePrach_MixerStatusOverrun;
typedef struct {
 u32 DecimatorOverrun;
 u32 FirstAntennaOverruning;
 u32 FirstRCIdOverruning;
} XDfePrach_DecimatorStatusOverrun;
typedef struct {
 XDfePrach_MixerStatusOverflow MixerOverflow;
 XDfePrach_DecimatorStatusOverflow
  DecimatorOverflow;
 XDfePrach_MixerStatusOverrun MixerOverrun;
 XDfePrach_DecimatorStatusOverrun
  DecimatorOverrun;
} XDfePrach_Status;
typedef struct {
 u32 DecimatorOverflow;
 u32 MixerOverflow;
 u32 DecimatorOverrun;
 u32 SelectorOverrun;
 u32 RachUpdate;
 u32 CCSequenceError
  [(3)];
 u32 FrameInitTrigger
  [(3)];
 u32 FrameError[(3)];
} XDfePrach_StatusMask;
typedef XDfePrach_StatusMask XDfePrach_InterruptMask;
typedef struct {
 u32 DeviceId;
 metal_phys_addr_t BaseAddr;
 u32 NumAntenna
  [(3)];
 u32 NumCCPerAntenna
  [(3)];
 u32 NumAntennaChannels
  [(3)];
 u32 NumAntennaSlots
  [(3)];
 u32 NumRachLanes;
 u32 NumRachChannels;
 u32 HasAxisCtrl;
 u32 HasIrq;
 u32 NumBands;
 u32 HasContinuousSched;
} XDfePrach_Config;
typedef struct {
 XDfePrach_Config Config;
 XDfePrach_StateId StateId;
 s32 NotUsedCCID
  [(3)];
 u32 SequenceLength[(3)];
 char NodeName[(50)];
 struct metal_io_region *Io;
 struct metal_device *Device;
} XDfePrach;
XDfePrach *XDfePrach_InstanceInit(const char *DeviceNodeName);
void XDfePrach_InstanceClose(XDfePrach *InstancePtr);
void XDfePrach_WriteReg(const XDfePrach *InstancePtr, u32 AddrOffset, u32 Data);
u32 XDfePrach_ReadReg(const XDfePrach *InstancePtr, u32 AddrOffset);
void XDfePrach_Reset(XDfePrach *InstancePtr);
void XDfePrach_Configure(XDfePrach *InstancePtr, XDfePrach_Cfg *Cfg);
void XDfePrach_Initialize(XDfePrach *InstancePtr, XDfePrach_Init *Init);
void XDfePrach_Activate(XDfePrach *InstancePtr, bool EnableLowPower);
void XDfePrach_Deactivate(XDfePrach *InstancePtr);
XDfePrach_StateId XDfePrach_GetStateID(XDfePrach *InstancePtr);
void XDfePrach_GetCurrentCCCfg(const XDfePrach *InstancePtr,
          XDfePrach_CCCfg *CCCfg);
void XDfePrach_GetEmptyCCCfg(const XDfePrach *InstancePtr,
        XDfePrach_CCCfg *CCCfg);
void XDfePrach_GetCarrierCfgMB(const XDfePrach *InstancePtr,
          XDfePrach_CCCfg *CCCfg, s32 CCID,
          u32 *CCSeqBitmap,
          XDfePrach_CarrierCfg *CarrierCfg,
          const u32 BandId);
void XDfePrach_GetCarrierCfg(const XDfePrach *InstancePtr,
        XDfePrach_CCCfg *CCCfg, s32 CCID, u32 *CCSeqBitmap,
        XDfePrach_CarrierCfg *CarrierCfg);
void XDfePrach_SetAntennaCfgInCCCfg(const XDfePrach *InstancePtr,
        XDfePrach_CCCfg *CCCfg, u32 *AntennaCfg);
u32 XDfePrach_AddCCtoCCCfgMB(XDfePrach *InstancePtr, XDfePrach_CCCfg *CCCfg,
        s32 CCID, u32 CCSeqBitmap,
        const XDfePrach_CarrierCfg *CarrierCfg,
        const u32 BandId);
u32 XDfePrach_AddCCtoCCCfg(XDfePrach *InstancePtr, XDfePrach_CCCfg *CCCfg,
      s32 CCID, u32 CCSeqBitmap,
      const XDfePrach_CarrierCfg *CarrierCfg);
u32 XDfePrach_RemoveCCfromCCCfgMB(XDfePrach *InstancePtr,
      XDfePrach_CCCfg *CCCfg, s32 CCID,
      const u32 BandId);
u32 XDfePrach_RemoveCCfromCCCfg(XDfePrach *InstancePtr, XDfePrach_CCCfg *CCCfg,
    s32 CCID);
u32 XDfePrach_UpdateCCinCCCfgMB(const XDfePrach *InstancePtr,
    XDfePrach_CCCfg *CCCfg, s32 CCID,
    const XDfePrach_CarrierCfg *CarrierCfg,
    const u32 BandId);
u32 XDfePrach_UpdateCCinCCCfg(const XDfePrach *InstancePtr,
         XDfePrach_CCCfg *CCCfg, s32 CCID,
         const XDfePrach_CarrierCfg *CarrierCfg);
u32 XDfePrach_SetNextCfg(const XDfePrach *InstancePtr,
    const XDfePrach_CCCfg *NextCCCfg,
    XDfePrach_RCCfg *NextRCCfg);
u32 XDfePrach_AddCC(XDfePrach *InstancePtr, s32 CCID, u32 CCSeqBitmap,
      const XDfePrach_CarrierCfg *CarrierCfg);
u32 XDfePrach_RemoveCC(XDfePrach *InstancePtr, s32 CCID);
u32 XDfePrach_UpdateCC(const XDfePrach *InstancePtr, s32 CCID,
         const XDfePrach_CarrierCfg *CarrierCfg);
void XDfePrach_GetCurrentRCCfg(const XDfePrach *InstancePtr,
          XDfePrach_RCCfg *RCCfg);
void XDfePrach_GetEmptyRCCfg(const XDfePrach *InstancePtr,
        XDfePrach_RCCfg *RCCfg);
void XDfePrach_GetChannelCfg(const XDfePrach *InstancePtr,
        XDfePrach_RCCfg *RCCfg, s32 RCId,
        XDfePrach_ChannelCfg *ChannelCfg);
u32 XDfePrach_AddRCtoRCCfgMB(const XDfePrach *InstancePtr,
        XDfePrach_RCCfg *CurrentRCCfg, s32 CCID, u32 RCId,
        u32 RachChan, XDfePrach_DDCCfg *DdcCfg,
        XDfePrach_NCO *NcoCfg,
        XDfePrach_Schedule *StaticSchedule,
        XDfePrach_CCCfg *NextCCCfg, u32 BandId);
u32 XDfePrach_AddRCtoRCCfgMBDynamic(const XDfePrach *InstancePtr,
        XDfePrach_RCCfg *CurrentRCCfg, s32 CCID,
        u32 RCId, u32 RachChan,
        XDfePrach_CCCfg *NextCCCfg, u32 BandId);
u32 XDfePrach_AddRCtoRCCfg(const XDfePrach *InstancePtr,
      XDfePrach_RCCfg *CurrentRCCfg, s32 CCID, u32 RCId,
      u32 RachChan, XDfePrach_DDCCfg *DdcCfg,
      XDfePrach_NCO *NcoCfg,
      XDfePrach_Schedule *StaticSchedule,
      XDfePrach_CCCfg *NextCCCfg);
u32 XDfePrach_AddRCtoRCCfgDynamic(const XDfePrach *InstancePtr,
      XDfePrach_RCCfg *CurrentRCCfg, s32 CCID,
      u32 RCId, u32 RachChan,
      XDfePrach_CCCfg *NextCCCfg);
u32 XDfePrach_RemoveRCfromRCCfg(const XDfePrach *InstancePtr,
    XDfePrach_RCCfg *CurrentRCCfg, u32 RCId);
void XDfePrach_UpdateRCinRCCfgMB(const XDfePrach *InstancePtr,
     XDfePrach_RCCfg *CurrentRCCfg, s32 CCID,
     u32 RCId, u32 RachChan,
     XDfePrach_DDCCfg *DdcCfg,
     XDfePrach_NCO *NcoCfg,
     XDfePrach_Schedule *StaticSchedule,
     XDfePrach_CCCfg *NextCCCfg, u32 BandId);
void XDfePrach_UpdateRCinRCCfg(const XDfePrach *InstancePtr,
          XDfePrach_RCCfg *CurrentRCCfg, s32 CCID,
          u32 RCId, u32 RachChan, XDfePrach_DDCCfg *DdcCfg,
          XDfePrach_NCO *NcoCfg,
          XDfePrach_Schedule *StaticSchedule,
          XDfePrach_CCCfg *NextCCCfg);
u32 XDfePrach_AddRCCfg(const XDfePrach *InstancePtr, s32 CCID, u32 RCId,
         u32 RachChan, XDfePrach_DDCCfg *DdcCfg,
         XDfePrach_NCO *NcoCfg,
         XDfePrach_Schedule *StaticSchedule);
u32 XDfePrach_RemoveRC(const XDfePrach *InstancePtr, u32 RCId);
u32 XDfePrach_UpdateRCCfg(const XDfePrach *InstancePtr, s32 CCID, u32 RCId,
     u32 RachChan, XDfePrach_DDCCfg *DdcCfg,
     XDfePrach_NCO *NcoCfg,
     XDfePrach_Schedule *StaticSchedule);
u32 XDfePrach_MoveRC(const XDfePrach *InstancePtr, u32 RCId, u32 ToChannel);
void XDfePrach_GetTriggersCfg(const XDfePrach *InstancePtr,
         XDfePrach_TriggerCfg *TriggerCfg);
void XDfePrach_SetTriggersCfg(const XDfePrach *InstancePtr,
         XDfePrach_TriggerCfg *TriggerCfg);
void XDfePrach_GetCC(const XDfePrach *InstancePtr, bool Next, s32 CCID,
       XDfePrach_CarrierCfg *CarrierCfg);
void XDfePrach_GetCCMB(const XDfePrach *InstancePtr, bool Next, s32 CCID,
         XDfePrach_CarrierCfg *CarrierCfg, u32 BandId);
void XDfePrach_GetStatus(const XDfePrach *InstancePtr,
    XDfePrach_Status *Status);
void XDfePrach_ClearStatus(const XDfePrach *InstancePtr);
void XDfePrach_CapturePhase(const XDfePrach *InstancePtr);
void XDfePrach_GetCapturePhase(const XDfePrach *InstancePtr, u32 RachChan,
          XDfePrach_NCO *CapturedPhase);
void XDfePrach_GetInterruptMask(const XDfePrach *InstancePtr,
    XDfePrach_InterruptMask *Mask);
void XDfePrach_SetInterruptMask(const XDfePrach *InstancePtr,
    const XDfePrach_InterruptMask *Mask);
void XDfePrach_GetEventStatus(const XDfePrach *InstancePtr,
         XDfePrach_StatusMask *Status);
void XDfePrach_ClearEventStatus(const XDfePrach *InstancePtr,
    const XDfePrach_StatusMask *Status);
void XDfePrach_SetTUserDelay(const XDfePrach *InstancePtr, u32 Delay);
void XDfePrach_SetTUserDelayMB(const XDfePrach *InstancePtr, u32 Delay,
          u32 BandId);
u32 XDfePrach_GetTUserDelay(const XDfePrach *InstancePtr);
u32 XDfePrach_GetTUserDelayMB(const XDfePrach *InstancePtr, u32 BandId);
u32 XDfePrach_GetTDataDelay(const XDfePrach *InstancePtr);
u32 XDfePrach_GetTDataDelayMB(const XDfePrach *InstancePtr, u32 BandId);
void XDfePrach_GetVersions(const XDfePrach *InstancePtr,
      XDfePrach_Version *SwVersion,
      XDfePrach_Version *HwVersion);
XDfePrach *xdfe_prach_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_prach_mmio_close(XDfePrach *inst);
