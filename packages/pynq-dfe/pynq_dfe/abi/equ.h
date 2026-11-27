/******************************************************************************
* Copyright (C) 2021-2022 Xilinx, Inc.  All rights reserved.
* Copyright (C) 2023-2024 Advanced Micro Devices, Inc. All Rights Reserved.
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
typedef enum XDfeEqu_StateId {
 XDFEEQU_STATE_NOT_READY = 0,
 XDFEEQU_STATE_READY,
 XDFEEQU_STATE_RESET,
 XDFEEQU_STATE_CONFIGURED,
 XDFEEQU_STATE_INITIALISED,
 XDFEEQU_STATE_OPERATIONAL
} XDfeEqu_StateId;
typedef struct {
 u32 Major;
 u32 Minor;
 u32 Revision;
 u32 Patch;
} XDfeEqu_Version;
typedef struct {
 u32 TriggerEnable;
 u32 Mode;
 u32 TuserEdgeLevel;
 u32 StateOutput;
 u32 TUSERBit;
} XDfeEqu_Trigger;
typedef struct {
 XDfeEqu_Trigger Activate;
 XDfeEqu_Trigger LowPower;
 XDfeEqu_Trigger
  Update;
} XDfeEqu_TriggerCfg;
typedef struct {
 u32 NumChannels;
 u32 SampleWidth;
 u32 ComplexModel;
 u32 TuserWidth;
} XDfeEqu_ModelParameters;
typedef struct {
 XDfeEqu_Version Version;
 XDfeEqu_ModelParameters ModelParams;
} XDfeEqu_Cfg;
typedef struct {
 u32 Num;
 u32 Set;
 s16 Coefficients[(24)];
} XDfeEqu_Coefficients;
typedef struct {
 u32 Flush;
 u32 DatapathMode;
 u32 RealDatapathSet;
 u32 ImDatapathSet;
} XDfeEqu_EqConfig;
typedef struct {
 u32 IStatus[(8)];
 u32 QStatus[(8)];
} XDfeEqu_Status;
typedef struct {
 u32 Mask[(8)];
} XDfeEqu_InterruptMask;
typedef struct {
 u32 DeviceId;
 metal_phys_addr_t BaseAddr;
 u32 NumChannels;
 u32 SampleWidth;
 u32 ComplexModel;
 u32 TuserWidth;
} XDfeEqu_Config;
typedef struct {
 XDfeEqu_Config Config;
 XDfeEqu_StateId StateId;
 char NodeName[(50)];
 struct metal_io_region *Io;
 struct metal_device *Device;
} XDfeEqu;
XDfeEqu *XDfeEqu_InstanceInit(const char *DeviceNodeName);
void XDfeEqu_InstanceClose(XDfeEqu *InstancePtr);
void XDfeEqu_WriteReg(const XDfeEqu *InstancePtr, u32 AddrOffset, u32 Data);
u32 XDfeEqu_ReadReg(const XDfeEqu *InstancePtr, u32 AddrOffset);
void XDfeEqu_Reset(XDfeEqu *InstancePtr);
void XDfeEqu_Configure(XDfeEqu *InstancePtr, XDfeEqu_Cfg *Cfg);
void XDfeEqu_Initialize(XDfeEqu *InstancePtr, const XDfeEqu_EqConfig *Config);
void XDfeEqu_Activate(XDfeEqu *InstancePtr, bool EnableLowPower);
void XDfeEqu_Deactivate(XDfeEqu *InstancePtr);
XDfeEqu_StateId XDfeEqu_GetStateID(XDfeEqu *InstancePtr);
void XDfeEqu_Update(const XDfeEqu *InstancePtr, const XDfeEqu_EqConfig *Config);
void XDfeEqu_GetTriggersCfg(const XDfeEqu *InstancePtr,
       XDfeEqu_TriggerCfg *TriggerCfg);
void XDfeEqu_SetTriggersCfg(const XDfeEqu *InstancePtr,
       XDfeEqu_TriggerCfg *TriggerCfg);
void XDfeEqu_LoadCoefficients(const XDfeEqu *InstancePtr, u32 ChannelField,
         u32 Mode, u32 Shift,
         const XDfeEqu_Coefficients *EqCoeffs);
void XDfeEqu_GetEventStatus(const XDfeEqu *InstancePtr, XDfeEqu_Status *Status);
void XDfeEqu_ClearEventStatus(const XDfeEqu *InstancePtr,
         const XDfeEqu_Status *Status);
void XDfeEqu_SetInterruptMask(const XDfeEqu *InstancePtr,
         const XDfeEqu_InterruptMask *InterruptMask);
void XDfeEqu_GetInterruptMask(const XDfeEqu *InstancePtr,
         XDfeEqu_InterruptMask *InterruptMask);
void XDfeEqu_GetActiveSets(const XDfeEqu *InstancePtr, u32 *RealSet,
      u32 *ImagSet);
void XDfeEqu_SetTUserDelay(const XDfeEqu *InstancePtr, u32 Delay);
u32 XDfeEqu_GetTUserDelay(const XDfeEqu *InstancePtr);
u32 XDfeEqu_GetTDataDelay(const XDfeEqu *InstancePtr, u32 Tap);
void XDfeEqu_GetVersions(const XDfeEqu *InstancePtr, XDfeEqu_Version *SwVersion,
    XDfeEqu_Version *HwVersion);
XDfeEqu *xdfe_equ_mmio_open(const char *name, uint64_t phys_base, uint64_t size);
void xdfe_equ_mmio_close(XDfeEqu *inst);
