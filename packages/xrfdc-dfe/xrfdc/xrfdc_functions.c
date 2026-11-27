/* Copyright (C) 2021 Xilinx, Inc. All rights reserved.
 * SPDX-License-Identifier: MIT
 * Generated from embeddedsw v2025.2, Linux ABI. Load with pack=1.
 */
struct metal_io_region;
struct metal_device;
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;
typedef signed int s32;
typedef signed short s16;
typedef unsigned long long u64;
typedef signed long long s64;
typedef signed char s8;
typedef unsigned long metal_phys_addr_t;
typedef void (*XRFdc_StatusHandler)(void *CallBackRef, u32 Type, u32 Tile_Id, u32 Block_Id, u32 StatusEvent);
typedef struct {
 u32 Enabled;
 double RefClkFreq;
 double SampleRate;
 u32 RefClkDivider;
 u32 FeedbackDivider;
 u32 OutputDivider;
 u32 FractionalMode;
 u64 FractionalData;
 u32 FractWidth;
} XRFdc_PLL_Settings;
typedef struct {
 u8 SourceType;
 u8 SourceTile;
 u32 PLLEnable;
 double RefClkFreq;
 double SampleRate;
 u8 DivisionFactor;
 u8 DistributedClock;
 u8 Delay;
} XRFdc_Tile_Clock_Settings;
typedef struct {
 u8 MaxDelay;
 u8 MinDelay;
 u8 IsDelayBalanced;
 u8 Source;
 u8 UpperBound;
 u8 LowerBound;
 XRFdc_Tile_Clock_Settings ClkSettings[2][4];
} XRFdc_Distribution_Info;
typedef struct {
 u32 SourceType;
 u32 SourceTileId;
 u32 EdgeTileIds[2];
 u32 EdgeTypes[2];
 double DistRefClkFreq;
 u32 DistributedClock;
 double SampleRates[2][4];
 u32 ShutdownMode;
 XRFdc_Distribution_Info Info;
} XRFdc_Distribution_Settings;
typedef struct {
 XRFdc_Distribution_Settings Distributions[8];
} XRFdc_Distribution_System_Settings;
typedef struct {
 u32 RefTile;
 u32 IsPLL;
 int Target[4];
 int Scan_Mode;
 int DTC_Code[4];
 int Num_Windows[4];
 int Max_Gap[4];
 int Min_Gap[4];
 int Max_Overlap[4];
} XRFdc_MTS_DTC_Settings;
typedef struct {
 u32 RefTile;
 u32 Tiles;
 int Target_Latency;
 int Offset[4];
 int Latency[4];
 int Marker_Delay;
 int SysRef_Enable;
 XRFdc_MTS_DTC_Settings DTC_Set_PLL;
 XRFdc_MTS_DTC_Settings DTC_Set_T1;
} XRFdc_MultiConverter_Sync_Config;
typedef struct {
 u32 Count[4];
 u32 Loc[4];
} XRFdc_MTS_Marker;
typedef struct {
 u8 Mode;
 u8 TimeConstant;
 u8 Flush;
 u8 EnableIntegrator;
 u16 Threshold;
 u16 ThreshOnTriggerCnt;
 u16 ThreshOffTriggerCnt;
 u8 HysteresisEnable;
} XRFdc_Signal_Detector_Settings;
typedef struct {
 u32 EnablePhase;
 u32 EnableGain;
 double GainCorrectionFactor;
 double PhaseCorrectionFactor;
 s32 OffsetCorrectionFactor;
 u32 EventSource;
} XRFdc_QMC_Settings;
typedef struct {
 u32 CoarseDelay;
 u32 EventSource;
} XRFdc_CoarseDelay_Settings;
typedef struct {
 double Freq;
 double PhaseOffset;
 u32 EventSource;
 u32 CoarseMixFreq;
 u32 MixerMode;
 u8 FineMixerScale;
 u8 MixerType;
} XRFdc_Mixer_Settings;
typedef struct {
 u32 UpdateThreshold;
 u32 ThresholdMode[2];
 u32 ThresholdAvgVal[2];
 u32 ThresholdUnderVal[2];
 u32 ThresholdOverVal[2];
} XRFdc_Threshold_Settings;
typedef struct {
 u32 Coeff0;
 u32 Coeff1;
 u32 Coeff2;
 u32 Coeff3;
 u32 Coeff4;
 u32 Coeff5;
 u32 Coeff6;
 u32 Coeff7;
} XRFdc_Calibration_Coefficients;
typedef struct {
 u32 DisableIPControl;
 u32 PwrMode;
} XRFdc_Pwr_Mode_Settings;
typedef struct {
 u32 DisableRTS;
 float Attenuation;
} XRFdc_DSA_Settings;
typedef struct {
 u32 CalFrozen;
 u32 DisableFreezePin;
 u32 FreezeCalibration;
} XRFdc_Cal_Freeze_Settings;
typedef struct {
 u32 IsEnabled;
 u32 TileState;
 u8 BlockStatusMask;
 u32 PowerUpState;
 u32 PLLState;
} XRFdc_TileStatus;
typedef struct {
 XRFdc_TileStatus DACTileStatus[4];
 XRFdc_TileStatus ADCTileStatus[4];
 u32 State;
} XRFdc_IPStatus;
typedef struct {
 double SamplingFreq;
 u32 AnalogDataPathStatus;
 u32 DigitalDataPathStatus;
 u8 DataPathClocksStatus;
 u8 IsFIFOFlagsEnabled;
 u8 IsFIFOFlagsAsserted;
} XRFdc_BlockStatus;
typedef struct {
 u32 BlockAvailable;
 u32 InvSyncEnable;
 u32 MixMode;
 u32 DecoderMode;
} XRFdc_DACBlock_AnalogDataPath_Config;
typedef struct {
 u32 MixerInputDataType;
 u32 DataWidth;
 u32 InterpolationMode;
 u32 FifoEnable;
 u32 AdderEnable;
 u32 MixerType;
 double NCOFreq;
} XRFdc_DACBlock_DigitalDataPath_Config;
typedef struct {
 u32 BlockAvailable;
 u32 MixMode;
} XRFdc_ADCBlock_AnalogDataPath_Config;
typedef struct {
 u32 MixerInputDataType;
 u32 DataWidth;
 u32 DecimationMode;
 u32 FifoEnable;
 u32 MixerType;
 double NCOFreq;
} XRFdc_ADCBlock_DigitalDataPath_Config;
typedef struct {
 u32 Enable;
 u32 PLLEnable;
 double SamplingRate;
 double RefClkFreq;
 double FabClkFreq;
 u32 FeedbackDiv;
 u32 OutputDiv;
 u32 RefClkDiv;
 u32 MultibandConfig;
 double MaxSampleRate;
 u32 NumSlices;
 u32 LinkCoupling;
 XRFdc_DACBlock_AnalogDataPath_Config DACBlock_Analog_Config[4];
 XRFdc_DACBlock_DigitalDataPath_Config DACBlock_Digital_Config[4];
} XRFdc_DACTile_Config;
typedef struct {
 u32 Enable;
 u32 PLLEnable;
 double SamplingRate;
 double RefClkFreq;
 double FabClkFreq;
 u32 FeedbackDiv;
 u32 OutputDiv;
 u32 RefClkDiv;
 u32 MultibandConfig;
 double MaxSampleRate;
 u32 NumSlices;
 XRFdc_ADCBlock_AnalogDataPath_Config ADCBlock_Analog_Config[4];
 XRFdc_ADCBlock_DigitalDataPath_Config ADCBlock_Digital_Config[4];
} XRFdc_ADCTile_Config;
typedef struct {
 u32 DeviceId;
 metal_phys_addr_t BaseAddr;
 u32 ADCType;
 u32 MasterADCTile;
 u32 MasterDACTile;
 u32 ADCSysRefSource;
 u32 DACSysRefSource;
 u32 IPType;
 u32 SiRevision;
 XRFdc_DACTile_Config DACTile_Config[4];
 XRFdc_ADCTile_Config ADCTile_Config[4];
} XRFdc_Config;
typedef struct {
 u32 Enabled;
 u32 MixedMode;
 double TerminationVoltage;
 double OutputCurrent;
 u32 InverseSincFilterEnable;
 u32 DecoderMode;
 void *FuncHandler;
 u32 NyquistZone;
 u8 AnalogPathEnabled;
 u8 AnalogPathAvailable;
 XRFdc_QMC_Settings QMC_Settings;
 XRFdc_CoarseDelay_Settings CoarseDelay_Settings;
} XRFdc_DACBlock_AnalogDataPath;
typedef struct {
 u32 MixerInputDataType;
 u32 DataWidth;
 int ConnectedIData;
 int ConnectedQData;
 u32 InterpolationFactor;
 u8 DigitalPathEnabled;
 u8 DigitalPathAvailable;
 XRFdc_Mixer_Settings Mixer_Settings;
} XRFdc_DACBlock_DigitalDataPath;
typedef struct {
 u32 Enabled;
 XRFdc_QMC_Settings QMC_Settings;
 XRFdc_CoarseDelay_Settings CoarseDelay_Settings;
 XRFdc_Threshold_Settings Threshold_Settings;
 u32 NyquistZone;
 u8 CalibrationMode;
 u8 AnalogPathEnabled;
 u8 AnalogPathAvailable;
} XRFdc_ADCBlock_AnalogDataPath;
typedef struct {
 u32 MixerInputDataType;
 u32 DataWidth;
 u32 DecimationFactor;
 int ConnectedIData;
 int ConnectedQData;
 u8 DigitalPathEnabled;
 u8 DigitalPathAvailable;
 XRFdc_Mixer_Settings Mixer_Settings;
} XRFdc_ADCBlock_DigitalDataPath;
typedef struct {
 u32 TileBaseAddr;
 u32 NumOfDACBlocks;
 XRFdc_PLL_Settings PLL_Settings;
 u8 MultibandConfig;
 XRFdc_DACBlock_AnalogDataPath DACBlock_Analog_Datapath[4];
 XRFdc_DACBlock_DigitalDataPath DACBlock_Digital_Datapath[4];
} XRFdc_DAC_Tile;
typedef struct {
 u32 TileBaseAddr;
 u32 NumOfADCBlocks;
 XRFdc_PLL_Settings PLL_Settings;
 u8 MultibandConfig;
 XRFdc_ADCBlock_AnalogDataPath ADCBlock_Analog_Datapath[4];
 XRFdc_ADCBlock_DigitalDataPath ADCBlock_Digital_Datapath[4];
} XRFdc_ADC_Tile;
typedef struct {
 XRFdc_Config RFdc_Config;
 u32 IsReady;
 u32 ADC4GSPS;
 metal_phys_addr_t BaseAddr;
 struct metal_io_region *io;
 struct metal_device *device;
 XRFdc_DAC_Tile DAC_Tile[4];
 XRFdc_ADC_Tile ADC_Tile[4];
 XRFdc_StatusHandler StatusHandler;
 void *CallBackRef;
 u8 UpdateMixerScale;
} XRFdc;
XRFdc_Config *XRFdc_LookupConfig(u16 DeviceId);
u32 XRFdc_RegisterMetal(XRFdc *InstancePtr, u16 DeviceId, struct metal_device **DevicePtr);
u32 XRFdc_CfgInitialize(XRFdc *InstancePtr, XRFdc_Config *ConfigPtr);
u32 XRFdc_StartUp(XRFdc *InstancePtr, u32 Type, int Tile_Id);
u32 XRFdc_Shutdown(XRFdc *InstancePtr, u32 Type, int Tile_Id);
u32 XRFdc_Reset(XRFdc *InstancePtr, u32 Type, int Tile_Id);
u32 XRFdc_CustomStartUp(XRFdc *InstancePtr, u32 Type, int Tile_Id, u32 StartState, u32 EndState);
u32 XRFdc_WaitForState(XRFdc *InstancePtr, u32 Type, u32 Tile, u32 State);
u32 XRFdc_GetIPStatus(XRFdc *InstancePtr, XRFdc_IPStatus *IPStatusPtr);
u32 XRFdc_GetBlockStatus(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, XRFdc_BlockStatus *BlockStatusPtr);
u32 XRFdc_SetMixerSettings(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id,
      XRFdc_Mixer_Settings *MixerSettingsPtr);
u32 XRFdc_GetMixerSettings(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id,
      XRFdc_Mixer_Settings *MixerSettingsPtr);
u32 XRFdc_SetQMCSettings(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, XRFdc_QMC_Settings *QMCSettingsPtr);
u32 XRFdc_GetQMCSettings(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, XRFdc_QMC_Settings *QMCSettingsPtr);
u32 XRFdc_GetCoarseDelaySettings(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id,
     XRFdc_CoarseDelay_Settings *CoarseDelaySettingsPtr);
u32 XRFdc_SetCoarseDelaySettings(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id,
     XRFdc_CoarseDelay_Settings *CoarseDelaySettingsPtr);
u32 XRFdc_GetInterpolationFactor(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *InterpolationFactorPtr);
u32 XRFdc_GetDecimationFactor(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *DecimationFactorPtr);
u32 XRFdc_GetDecimationFactorObs(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *DecimationFactorPtr);
u32 XRFdc_GetFabWrVldWords(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *FabricDataRatePtr);
u32 XRFdc_GetFabWrVldWordsObs(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *FabricDataRatePtr);
u32 XRFdc_GetFabRdVldWords(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *FabricDataRatePtr);
u32 XRFdc_GetFabRdVldWordsObs(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *FabricDataRatePtr);
u32 XRFdc_SetFabRdVldWords(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 FabricRdVldWords);
u32 XRFdc_SetFabRdVldWordsObs(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 FabricRdVldWords);
u32 XRFdc_SetFabWrVldWords(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 FabricWrVldWords);
u32 XRFdc_GetThresholdSettings(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id,
          XRFdc_Threshold_Settings *ThresholdSettingsPtr);
u32 XRFdc_SetThresholdSettings(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id,
          XRFdc_Threshold_Settings *ThresholdSettingsPtr);
u32 XRFdc_SetDecoderMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 DecoderMode);
u32 XRFdc_UpdateEvent(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 Event);
u32 XRFdc_GetDecoderMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *DecoderModePtr);
u32 XRFdc_ResetNCOPhase(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
void XRFdc_DumpRegs(XRFdc *InstancePtr, u32 Type, int Tile_Id);
u32 XRFdc_MultiBand(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u8 DigitalDataPathMask, u32 MixerInOutDataType,
      u32 DataConverterMask);
int XRFdc_GetConnectedIData(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
int XRFdc_GetConnectedQData(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_GetConnectedIQData(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, int *ConnectedIData,
        int *ConnectedQData);
u32 XRFdc_IntrHandler(u32 Vector, void *XRFdcPtr);
u32 XRFdc_IntrClr(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 IntrMask);
u32 XRFdc_GetIntrStatus(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *IntrStsPtr);
u32 XRFdc_IntrDisable(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 IntrMask);
u32 XRFdc_IntrEnable(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 IntrMask);
u32 XRFdc_GetEnabledInterrupts(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *IntrMask);
u32 XRFdc_SetThresholdClrMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 ThresholdToUpdate, u32 ClrMode);
u32 XRFdc_ThresholdStickyClear(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 ThresholdToUpdate);
void XRFdc_SetStatusHandler(XRFdc *InstancePtr, void *CallBackRef, XRFdc_StatusHandler FunctionPtr);
u32 XRFdc_SetupFIFO(XRFdc *InstancePtr, u32 Type, int Tile_Id, u8 Enable);
u32 XRFdc_SetupFIFOObs(XRFdc *InstancePtr, u32 Type, int Tile_Id, u8 Enable);
u32 XRFdc_SetupFIFOBoth(XRFdc *InstancePtr, u32 Type, int Tile_Id, u8 Enable);
u32 XRFdc_GetFIFOStatus(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u8 *EnablePtr);
u32 XRFdc_GetFIFOStatusObs(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u8 *EnablePtr);
u32 XRFdc_SetNyquistZone(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 NyquistZone);
u32 XRFdc_GetNyquistZone(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *NyquistZonePtr);
u32 XRFdc_GetOutputCurr(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *OutputCurrPtr);
u32 XRFdc_SetDecimationFactor(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 DecimationFactor);
u32 XRFdc_SetDecimationFactorObs(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 DecimationFactor);
u32 XRFdc_SetInterpolationFactor(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 InterpolationFactor);
u32 XRFdc_SetFabClkOutDiv(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u16 FabClkDiv);
u32 XRFdc_SetCalibrationMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u8 CalibrationMode);
u32 XRFdc_GetCalibrationMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u8 *CalibrationModePtr);
u32 XRFdc_GetClockSource(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 *ClockSourcePtr);
u32 XRFdc_GetPLLLockStatus(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 *LockStatusPtr);
u32 XRFdc_GetPLLConfig(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, XRFdc_PLL_Settings *PLLSettings);
u32 XRFdc_DynamicPLLConfig(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u8 Source, double RefClkFreq,
      double SamplingRate);
u32 XRFdc_SetInvSincFIR(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u16 Mode);
u32 XRFdc_GetInvSincFIR(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u16 *ModePtr);
u32 XRFdc_GetCoupling(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, u32 *ModePtr);
u32 XRFdc_GetLinkCoupling(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *ModePtr);
u32 XRFdc_GetFabClkOutDiv(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u16 *FabClkDivPtr);
u32 XRFdc_SetDither(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 Mode);
u32 XRFdc_GetDither(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *ModePtr);
u32 XRFdc_SetClkDistribution(XRFdc *InstancePtr, XRFdc_Distribution_Settings *DistributionSettingsPtr);
u32 XRFdc_GetClkDistribution(XRFdc *InstancePtr, XRFdc_Distribution_System_Settings *DistributionArrayPtr);
u32 XRFdc_SetDataPathMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 Mode);
u32 XRFdc_GetDataPathMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *ModePtr);
u32 XRFdc_SetIMRPassMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 Mode);
u32 XRFdc_GetIMRPassMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *ModePtr);
u32 XRFdc_SetSignalDetector(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, XRFdc_Signal_Detector_Settings *SettingsPtr);
u32 XRFdc_GetSignalDetector(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, XRFdc_Signal_Detector_Settings *SettingsPtr);
u32 XRFdc_DisableCoefficientsOverride(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 CalibrationBlock);
u32 XRFdc_SetCalCoefficients(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 CalibrationBlock,
        XRFdc_Calibration_Coefficients *CoeffPtr);
u32 XRFdc_GetCalCoefficients(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 CalibrationBlock,
        XRFdc_Calibration_Coefficients *CoeffPtr);
u32 XRFdc_SetCalFreeze(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, XRFdc_Cal_Freeze_Settings *CalFreezePtr);
u32 XRFdc_GetCalFreeze(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, XRFdc_Cal_Freeze_Settings *CalFreezePtr);
u32 XRFdc_SetDACVOP(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 uACurrent);
u32 XRFdc_SetDACCompMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 Enable);
u32 XRFdc_GetDACCompMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *EnabledPtr);
u32 XRFdc_SetDSA(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, XRFdc_DSA_Settings *SettingsPtr);
u32 XRFdc_GetDSA(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, XRFdc_DSA_Settings *SettingsPtr);
u32 XRFdc_SetPwrMode(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, XRFdc_Pwr_Mode_Settings *SettingsPtr);
u32 XRFdc_GetPwrMode(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, XRFdc_Pwr_Mode_Settings *SettingsPtr);
u32 XRFdc_ResetInternalFIFOWidth(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_ResetInternalFIFOWidthObs(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id);
void XRFdc_ClrSetReg(XRFdc *InstancePtr, u32 BaseAddr, u32 RegAddr, u16 Mask, u16 Data);
void XRFdc_ClrReg(XRFdc *InstancePtr, u32 BaseAddr, u32 RegAddr, u16 Mask);
u16 XRFdc_RDReg(XRFdc *InstancePtr, u32 BaseAddr, u32 RegAddr, u16 Mask);
u32 XRFdc_IsHighSpeedADC(XRFdc *InstancePtr, u32 Tile);
u32 XRFdc_IsDACBlockEnabled(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_IsADCBlockEnabled(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_IsDACDigitalPathEnabled(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_IsADCDigitalPathEnabled(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_CheckDigitalPathEnabled(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_Get_IPBaseAddr(XRFdc *InstancePtr);
u32 XRFdc_Get_TileBaseAddr(XRFdc *InstancePtr, u32 Type, u32 Tile_Id);
u32 XRFdc_Get_BlockBaseAddr(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_GetNoOfDACBlock(XRFdc *InstancePtr, u32 Tile_Id);
u32 XRFdc_GetNoOfADCBlocks(XRFdc *InstancePtr, u32 Tile_Id);
u32 XRFdc_GetDataType(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_GetDataWidth(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_GetInverseSincFilter(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_GetMixedMode(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_GetMasterTile(XRFdc *InstancePtr, u32 Type);
u32 XRFdc_GetSysRefSource(XRFdc *InstancePtr, u32 Type);
double XRFdc_GetFabClkFreq(XRFdc *InstancePtr, u32 Type, u32 Tile_Id);
u32 XRFdc_IsFifoEnabled(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
void XRFdc_SetConnectedIQData(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id, int ConnectedIData,
         int ConnectedQData);
u32 XRFdc_GetMultibandConfig(XRFdc *InstancePtr, u32 Type, u32 Tile_Id);
u32 XRFdc_CheckBlockEnabled(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 Block_Id);
u32 XRFdc_CheckTileEnabled(XRFdc *InstancePtr, u32 Type, u32 Tile_Id);
u32 XRFdc_GetMaxSampleRate(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, double *MaxSampleRatePtr);
u32 XRFdc_GetMinSampleRate(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, double *MinSampleRatePtr);
double XRFdc_GetDriverVersion(void);
u32 XRFdc_MultiConverter_Sync(XRFdc *InstancePtr, u32 Type, XRFdc_MultiConverter_Sync_Config *ConfigPtr);
u32 XRFdc_MultiConverter_Init(XRFdc_MultiConverter_Sync_Config *ConfigPtr, int *PLL_CodesPtr, int *T1_CodesPtr,
         u32 RefTile);
u32 XRFdc_MTS_Sysref_Config(XRFdc *InstancePtr, XRFdc_MultiConverter_Sync_Config *DACSyncConfigPtr,
       XRFdc_MultiConverter_Sync_Config *ADCSyncConfigPtr, u32 SysRefEnable);
u32 XRFdc_GetMTSEnable(XRFdc *InstancePtr, u32 Type, u32 Tile, u32 *EnablePtr);
u32 XRFdc_SetDACDataScaler(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 Enable);
u32 XRFdc_GetDACDataScaler(XRFdc *InstancePtr, u32 Tile_Id, u32 Block_Id, u32 *EnablePtr);
u8 XRFdc_GetTileLayout(XRFdc *InstancePtr);
s32 XRFdc_GetDeviceNameByDeviceId(char *DevNamePtr, u16 DevId);
struct xrfdc_mapping;
struct xrfdc_mapping *xrfdc_attach(XRFdc *instance, XRFdc_Config *config,
                                   void *base, size_t length);
void xrfdc_detach(struct xrfdc_mapping *mapping);
#define XRFDC_3ADC_2DAC_TILES 1
#define XRFDC_4ADC_4DAC_TILES 0
#define XRFDC_ADC0_SUBDRP_ADDR_OFFSET 0x198
#define XRFDC_ADC0_SUBDRP_DAT_OFFSET 0x19C
#define XRFDC_ADC1_SUBDRP_ADDR_OFFSET 0x1A0
#define XRFDC_ADC1_SUBDRP_DAT_OFFSET 0x1A4
#define XRFDC_ADC2_SUBDRP_ADDR_OFFSET 0x1A8
#define XRFDC_ADC2_SUBDRP_DAT_OFFSET 0x1AC
#define XRFDC_ADC3_SUBDRP_ADDR_OFFSET 0x1B0
#define XRFDC_ADC3_SUBDRP_DAT_OFFSET 0x1B4
#define XRFDC_ADC_2G_SAMPLING_MAX 2058
#define XRFDC_ADC_2G_SAMPLING_MIN 500
#define XRFDC_ADC_4GSPS 1
#define XRFDC_ADC_4G_SAMPLING_MAX 4116
#define XRFDC_ADC_4G_SAMPLING_MIN 1000
#define XRFDC_ADC_CG_WAIT_CYCLES 1
#define XRFDC_ADC_CMODE_OVR_MASK 0x10000000
#define XRFDC_ADC_CMODE_SHIFT 10
#define XRFDC_ADC_CMODE_UNDR_MASK 0x20000000
#define XRFDC_ADC_CRSE_DLY_CFG_OFFSET 0x0E0
#define XRFDC_ADC_CRSE_DLY_UPDT_OFFSET 0x0DC
#define XRFDC_ADC_DAC_MC_CFG0_OFFSET 0x1C4
#define XRFDC_ADC_DAC_MC_CFG1_OFFSET 0x1C8
#define XRFDC_ADC_DAC_MC_CFG2_OFFSET 0x1CC
#define XRFDC_ADC_DAT_FIFO_OVR_SHIFT 16
#define XRFDC_ADC_DAT_IMR_MASK 0x000000FF
#define XRFDC_ADC_DAT_OVR_MASK 0x40000000
#define XRFDC_ADC_DAT_PATH_ISR_MASK 0x000000FF
#define XRFDC_ADC_DAT_SCAL_CFG_OFFSET 0x0E4
#define XRFDC_ADC_DEBUG_RST_OFFSET 0x004
#define XRFDC_ADC_DECI_CONFIG_OBS_OFFSET 0x048
#define XRFDC_ADC_DECI_CONFIG_OFFSET 0x040
#define XRFDC_ADC_DECI_MODE_OBS_OFFSET 0x04C
#define XRFDC_ADC_DECI_MODE_OFFSET 0x044
#define XRFDC_ADC_DEC_IMR_OFFSET 0x034
#define XRFDC_ADC_DEC_ISR_OFFSET 0x030
#define XRFDC_ADC_DSA_CODE_MASK 0x001F
#define XRFDC_ADC_DSA_RTS_PIN_MASK 0x0020
#define XRFDC_ADC_DSA_RTS_PIN_SHIFT 5
#define XRFDC_ADC_DSA_UPDT_MASK 0x0001
#define XRFDC_ADC_FABRIC_DBG_OBS_OFFSET 0x058
#define XRFDC_ADC_FABRIC_DBG_OFFSET 0x018
#define XRFDC_ADC_FABRIC_IMR_OBS_OFFSET 0x060
#define XRFDC_ADC_FABRIC_IMR_OFFSET 0x014
#define XRFDC_ADC_FABRIC_ISR_OBS_OFFSET 0x05C
#define XRFDC_ADC_FABRIC_ISR_OFFSET 0x010
#define XRFDC_ADC_FABRIC_OBS_OFFSET 0x054
#define XRFDC_ADC_FABRIC_OFFSET 0x00C
#define XRFDC_ADC_FABRIC_RATE_OBS_OFFSET 0x050
#define XRFDC_ADC_FABRIC_RATE_OFFSET 0x008
#define XRFDC_ADC_FAB_RATE_RD_MASK 0x00000F00
#define XRFDC_ADC_FAB_RATE_WR_MASK 0x0000000F
#define XRFDC_ADC_FEND_DAT_CRL_OFFSET 0x140
#define XRFDC_ADC_FIFO_DELAY_MASK 0x0000001C0
#define XRFDC_ADC_FIFO_DELAY_SHIFT 6
#define XRFDC_ADC_FIFO_LTNCY_LB_OFFSET 0x280
#define XRFDC_ADC_FIFO_LTNCY_MB_OFFSET 0x284
#define XRFDC_ADC_FIFO_LTNC_CRL_OBS_OFFSET 0x064
#define XRFDC_ADC_FIFO_LTNC_CRL_OFFSET 0x020
#define XRFDC_ADC_FIFO_OVR_MASK 0x80000000
#define XRFDC_ADC_IXR_DATAPATH_MASK 0x00000FF0
#define XRFDC_ADC_IXR_DMON_I_STG0_MASK 0x00000010
#define XRFDC_ADC_IXR_DMON_I_STG1_MASK 0x00000020
#define XRFDC_ADC_IXR_DMON_I_STG2_MASK 0x00000040
#define XRFDC_ADC_IXR_DMON_Q_STG0_MASK 0x00000080
#define XRFDC_ADC_IXR_DMON_Q_STG1_MASK 0x00000100
#define XRFDC_ADC_IXR_DMON_Q_STG2_MASK 0x00000200
#define XRFDC_ADC_IXR_DMON_STG_MASK 0x000003F0
#define XRFDC_ADC_MIXER_MODE_IQ 0x1
#define XRFDC_ADC_MXR_CFG0_OFFSET 0x080
#define XRFDC_ADC_MXR_CFG1_OFFSET 0x084
#define XRFDC_ADC_NCO_FQWD_LOW_OFFSET 0x09C
#define XRFDC_ADC_NCO_FQWD_MID_OFFSET 0x098
#define XRFDC_ADC_NCO_FQWD_UPP_OFFSET 0x094
#define XRFDC_ADC_NCO_PHASE_MOD_OFFSET 0x0A8
#define XRFDC_ADC_OVR_RANGE_MASK 0x08000000
#define XRFDC_ADC_OVR_VOLTAGE_MASK 0x04000000
#define XRFDC_ADC_OVR_VOL_RANGE_SHIFT 24
#define XRFDC_ADC_PATHS_ENABLED_OFFSET 0x00A4
#define XRFDC_ADC_RXPR_MC_CFG0_OFFSET 0x1D0
#define XRFDC_ADC_RXPR_MC_CFG1_OFFSET 0x1D4
#define XRFDC_ADC_RX_MC_PWRDWN_OFFSET 0x1C0
#define XRFDC_ADC_SIG_DETECT_CTRL_OFFSET 0x114
#define XRFDC_ADC_SIG_DETECT_FLUSH_MASK 0x02
#define XRFDC_ADC_SIG_DETECT_FLUSH_SHIFT 1
#define XRFDC_ADC_SIG_DETECT_HYST_MASK 0x80
#define XRFDC_ADC_SIG_DETECT_HYST_SHIFT 7
#define XRFDC_ADC_SIG_DETECT_INTG_MASK 0x01
#define XRFDC_ADC_SIG_DETECT_INTG_SHIFT 0
#define XRFDC_ADC_SIG_DETECT_MAGN_OFFSET 0x130
#define XRFDC_ADC_SIG_DETECT_MASK 0xFF
#define XRFDC_ADC_SIG_DETECT_MODE_MASK 0x60
#define XRFDC_ADC_SIG_DETECT_MODE_READ_SHIFT 6
#define XRFDC_ADC_SIG_DETECT_MODE_WRITE_SHIFT 5
#define XRFDC_ADC_SIG_DETECT_TCONST_MASK 0x1C
#define XRFDC_ADC_SIG_DETECT_TCONST_SHIFT 2
#define XRFDC_ADC_SIG_DETECT_THRESHOLD0_CNT_OFF_OFFSET 0x11C
#define XRFDC_ADC_SIG_DETECT_THRESHOLD0_CNT_ON_OFFSET 0x120
#define XRFDC_ADC_SIG_DETECT_THRESHOLD0_LEVEL_OFFSET 0x118
#define XRFDC_ADC_SIG_DETECT_THRESH_CNT_MASK 0xFFFF
#define XRFDC_ADC_SIG_DETECT_THRESH_MASK 0xFFFF
#define XRFDC_ADC_SUBADC_DCDR_SHIFT 16
#define XRFDC_ADC_SWITCH_MATRX_OFFSET 0x0E8
#define XRFDC_ADC_TDD_MODE0_OFFSET 0x068
#define XRFDC_ADC_TILE 0
#define XRFDC_ADC_TI_DCBSTS0_BG_OFFSET 0x200
#define XRFDC_ADC_TI_DCBSTS0_FG_OFFSET 0x204
#define XRFDC_ADC_TI_DCBSTS1_BG_OFFSET 0x208
#define XRFDC_ADC_TI_DCBSTS1_FG_OFFSET 0x20C
#define XRFDC_ADC_TI_DCBSTS2_BG_OFFSET 0x210
#define XRFDC_ADC_TI_DCBSTS2_FG_OFFSET 0x214
#define XRFDC_ADC_TI_DCBSTS3_BG_OFFSET 0x218
#define XRFDC_ADC_TI_DCBSTS3_FG_OFFSET 0x21C
#define XRFDC_ADC_TI_DCBSTS4_LB_OFFSET 0x224
#define XRFDC_ADC_TI_DCBSTS4_MB_OFFSET 0x220
#define XRFDC_ADC_TI_DCBSTS5_LB_OFFSET 0x22C
#define XRFDC_ADC_TI_DCBSTS5_MB_OFFSET 0x228
#define XRFDC_ADC_TI_DCBSTS6_LB_OFFSET 0x234
#define XRFDC_ADC_TI_DCBSTS6_MB_OFFSET 0x230
#define XRFDC_ADC_TI_DCBSTS7_LB_OFFSET 0x23C
#define XRFDC_ADC_TI_DCBSTS7_MB_OFFSET 0x238
#define XRFDC_ADC_TI_DCB_CRL0_OFFSET 0x144
#define XRFDC_ADC_TI_DCB_CRL1_OFFSET 0x148
#define XRFDC_ADC_TI_DCB_CRL2_OFFSET 0x14C
#define XRFDC_ADC_TI_DCB_CRL3_OFFSET 0x150
#define XRFDC_ADC_TI_TISK_CRL0_OFFSET 0x154
#define XRFDC_ADC_TI_TISK_CRL1_OFFSET 0x158
#define XRFDC_ADC_TI_TISK_CRL2_OFFSET 0x15C
#define XRFDC_ADC_TI_TISK_CRL3_OFFSET 0x160
#define XRFDC_ADC_TI_TISK_CRL4_OFFSET 0x164
#define XRFDC_ADC_TI_TISK_CRL5_OFFSET 0x168
#define XRFDC_ADC_TI_TISK_DAC0_OFFSET 0x168
#define XRFDC_ADC_TI_TISK_DAC1_OFFSET 0x16C
#define XRFDC_ADC_TI_TISK_DAC2_OFFSET 0x170
#define XRFDC_ADC_TI_TISK_DAC3_OFFSET 0x174
#define XRFDC_ADC_TI_TISK_DACP0_OFFSET 0x178
#define XRFDC_ADC_TI_TISK_DACP1_OFFSET 0x17C
#define XRFDC_ADC_TI_TISK_DACP2_OFFSET 0x180
#define XRFDC_ADC_TI_TISK_DACP3_OFFSET 0x184
#define XRFDC_ADC_TRSHD0_AVG_LO_OFFSET 0x0F4
#define XRFDC_ADC_TRSHD0_AVG_UP_OFFSET 0x0F0
#define XRFDC_ADC_TRSHD0_CFG_OFFSET 0x0EC
#define XRFDC_ADC_TRSHD0_OVER_OFFSET 0x0FC
#define XRFDC_ADC_TRSHD0_UNDER_OFFSET 0x0F8
#define XRFDC_ADC_TRSHD1_AVG_LO_OFFSET 0x108
#define XRFDC_ADC_TRSHD1_AVG_UP_OFFSET 0x104
#define XRFDC_ADC_TRSHD1_CFG_OFFSET 0x100
#define XRFDC_ADC_TRSHD1_OVER_OFFSET 0x110
#define XRFDC_ADC_TRSHD1_UNDER_OFFSET 0x10C
#define XRFDC_ADC_UPDATE_DYN_OFFSET 0x01C
#define XRFDC_ADC_UPDT_CRSE_DLY_MASK 0x00000008
#define XRFDC_ALT_BOND_CLKDP_MASK 0x4
#define XRFDC_ALT_BOND_CLKDP_SHIFT 2
#define XRFDC_ALT_BOND_MASK 0x0200
#define XRFDC_ALT_BOND_SHIFT 9
#define XRFDC_ANALOGPATH_ENABLE 0x1
#define XRFDC_BLK_ID0 0x0
#define XRFDC_BLK_ID1 0x1
#define XRFDC_BLK_ID2 0x2
#define XRFDC_BLK_ID3 0x3
#define XRFDC_BLK_ID4 0x4
#define XRFDC_BLK_ID_ALL -1
#define XRFDC_BLK_ID_INV 0x4
#define XRFDC_BLK_ID_NONE -1
#define XRFDC_BLOCK_ID_MAX 0x3
#define XRFDC_CALIB_MODE1 0x1
#define XRFDC_CALIB_MODE2 0x2
#define XRFDC_CALIB_MODE_ABS_DIFF 0x1
#define XRFDC_CALIB_MODE_AUTO 0x0
#define XRFDC_CALIB_MODE_MIXED 0x0
#define XRFDC_CALIB_MODE_NEG_ABS_SUM 0x2
#define XRFDC_CAL_BLOCK_GCB 2
#define XRFDC_CAL_BLOCK_OCB1 0
#define XRFDC_CAL_BLOCK_OCB2 1
#define XRFDC_CAL_BLOCK_TSCB 3
#define XRFDC_CAL_DIV_BYP_MASK 0x00000004
#define XRFDC_CAL_DIV_BYP_OFFSET 0x100
#define XRFDC_CAL_DLY_OFFSET 0x310
#define XRFDC_CAL_FREEZE_CALIB 1
#define XRFDC_CAL_FREEZE_CAL_MASK 0x1
#define XRFDC_CAL_FREEZE_CAL_SHIFT 0
#define XRFDC_CAL_FREEZE_PIN_MASK 0x4
#define XRFDC_CAL_FREEZE_PIN_SHIFT 2
#define XRFDC_CAL_FREEZE_STS_MASK 0x2
#define XRFDC_CAL_FREEZE_STS_SHIFT 1
#define XRFDC_CAL_FRZ_PIN_DISABLE 1
#define XRFDC_CAL_FRZ_PIN_ENABLE 0
#define XRFDC_CAL_GCB_ACEN_MASK 0x0800
#define XRFDC_CAL_GCB_ACEN_SHIFT 11
#define XRFDC_CAL_GCB_ENFL_MASK 0x1800
#define XRFDC_CAL_GCB_EN_MASK 0x2000
#define XRFDC_CAL_GCB_EN_SHIFT 13
#define XRFDC_CAL_GCB_FAB_MASK 0xFFF0
#define XRFDC_CAL_GCB_FLSH_MASK 0x1000
#define XRFDC_CAL_GCB_FLSH_SHIFT 12
#define XRFDC_CAL_GCB_MASK 0x0FFF
#define XRFDC_CAL_GCB_OFFSET_COEFF0 0x220
#define XRFDC_CAL_GCB_OFFSET_COEFF0_ALT 0x220
#define XRFDC_CAL_GCB_OFFSET_COEFF1 0x224
#define XRFDC_CAL_GCB_OFFSET_COEFF1_ALT 0x228
#define XRFDC_CAL_GCB_OFFSET_COEFF2 0x228
#define XRFDC_CAL_GCB_OFFSET_COEFF2_ALT 0x230
#define XRFDC_CAL_GCB_OFFSET_COEFF3 0x22C
#define XRFDC_CAL_GCB_OFFSET_COEFF3_ALT 0x238
#define XRFDC_CAL_MODES_MASK 0x0003
#define XRFDC_CAL_OCB1_OFFSET_COEFF0 0x200
#define XRFDC_CAL_OCB1_OFFSET_COEFF1 0x208
#define XRFDC_CAL_OCB1_OFFSET_COEFF2 0x210
#define XRFDC_CAL_OCB1_OFFSET_COEFF3 0x218
#define XRFDC_CAL_OCB2_OFFSET_COEFF0 0x204
#define XRFDC_CAL_OCB2_OFFSET_COEFF1 0x20C
#define XRFDC_CAL_OCB2_OFFSET_COEFF2 0x214
#define XRFDC_CAL_OCB2_OFFSET_COEFF3 0x21C
#define XRFDC_CAL_OCB_EN_MASK 0x0001
#define XRFDC_CAL_OCB_EN_SHIFT 0
#define XRFDC_CAL_OCB_MASK 0xFFFF
#define XRFDC_CAL_SLICE_SHIFT 16
#define XRFDC_CAL_TMR_MULT_OFFSET 0x30C
#define XRFDC_CAL_TSCB_EN_MASK 0x8000
#define XRFDC_CAL_TSCB_EN_SHIFT 15
#define XRFDC_CAL_TSCB_MASK 0x01FF
#define XRFDC_CAL_TSCB_OFFSET_COEFF0 0x170
#define XRFDC_CAL_TSCB_OFFSET_COEFF0_ALT 0x168
#define XRFDC_CAL_TSCB_OFFSET_COEFF1 0x174
#define XRFDC_CAL_TSCB_OFFSET_COEFF1_ALT 0x16C
#define XRFDC_CAL_TSCB_OFFSET_COEFF2 0x178
#define XRFDC_CAL_TSCB_OFFSET_COEFF2_ALT 0x170
#define XRFDC_CAL_TSCB_OFFSET_COEFF3 0x17C
#define XRFDC_CAL_TSCB_OFFSET_COEFF3_ALT 0x174
#define XRFDC_CAL_TSCB_OFFSET_COEFF4 0x180
#define XRFDC_CAL_TSCB_OFFSET_COEFF4_ALT 0x178
#define XRFDC_CAL_TSCB_OFFSET_COEFF5 0x184
#define XRFDC_CAL_TSCB_OFFSET_COEFF5_ALT 0x17C
#define XRFDC_CAL_TSCB_OFFSET_COEFF6 0x188
#define XRFDC_CAL_TSCB_OFFSET_COEFF6_ALT 0x180
#define XRFDC_CAL_TSCB_OFFSET_COEFF7 0x18C
#define XRFDC_CAL_TSCB_OFFSET_COEFF7_ALT 0x184
#define XRFDC_CAL_TSCB_TUNE_MASK 0x0FF0
#define XRFDC_CAL_UNFREEZE_CALIB 0
#define XRFDC_CG_CYCLES_KEPT_X16 1
#define XRFDC_CG_CYCLES_KEPT_X1_X2_X4_X8 1
#define XRFDC_CG_CYCLES_KEPT_X20 2
#define XRFDC_CG_CYCLES_KEPT_X24 1
#define XRFDC_CG_CYCLES_KEPT_X3_X6_X12 2
#define XRFDC_CG_CYCLES_KEPT_X40 1
#define XRFDC_CG_CYCLES_KEPT_X5_X10 4
#define XRFDC_CG_CYCLES_TOTAL_X16 2
#define XRFDC_CG_CYCLES_TOTAL_X1_X2_X4_X8 0
#define XRFDC_CG_CYCLES_TOTAL_X20 5
#define XRFDC_CG_CYCLES_TOTAL_X24 3
#define XRFDC_CG_CYCLES_TOTAL_X3_X6_X12 3
#define XRFDC_CG_CYCLES_TOTAL_X40 5
#define XRFDC_CG_CYCLES_TOTAL_X5_X10 5
#define XRFDC_CG_FIXED_OFS 2
#define XRFDC_CG_WAIT_CYCLES 3
#define XRFDC_CLK_DISTR_CONT_LEFT_EVEN 0x8208
#define XRFDC_CLK_DISTR_CONT_LEFT_ODD 0x8200
#define XRFDC_CLK_DISTR_CONT_RIGHT_EVEN 0x4080
#define XRFDC_CLK_DISTR_CONT_RIGHT_HWL_ODD 0x4088
#define XRFDC_CLK_DISTR_LEFTMOST_TILE 0x0000
#define XRFDC_CLK_DISTR_MUX4A_SRC_CLR 0x0008
#define XRFDC_CLK_DISTR_MUX4A_SRC_INT 0x0008
#define XRFDC_CLK_DISTR_MUX4A_SRC_STH 0x0000
#define XRFDC_CLK_DISTR_MUX5A_SRC_PLL 0x0800
#define XRFDC_CLK_DISTR_MUX5A_SRC_RX 0x0040
#define XRFDC_CLK_DISTR_MUX6_SRC_CLR 0x0180
#define XRFDC_CLK_DISTR_MUX6_SRC_INT 0x0100
#define XRFDC_CLK_DISTR_MUX6_SRC_NTH 0x0080
#define XRFDC_CLK_DISTR_MUX6_SRC_OFF 0x0000
#define XRFDC_CLK_DISTR_MUX7_SRC_CLR 0x0600
#define XRFDC_CLK_DISTR_MUX7_SRC_INT 0x0400
#define XRFDC_CLK_DISTR_MUX7_SRC_OFF 0x0000
#define XRFDC_CLK_DISTR_MUX7_SRC_STH 0x0200
#define XRFDC_CLK_DISTR_MUX8_SRC_CLR 0x8000
#define XRFDC_CLK_DISTR_MUX8_SRC_INT 0x8000
#define XRFDC_CLK_DISTR_MUX8_SRC_NTH 0x0000
#define XRFDC_CLK_DISTR_MUX9_SRC_CLR 0x4000
#define XRFDC_CLK_DISTR_MUX9_SRC_INT 0x0000
#define XRFDC_CLK_DISTR_MUX9_SRC_NTH 0x4000
#define XRFDC_CLK_DISTR_RIGHTMOST_TILE 0x4008
#define XRFDC_CLK_DIV_DP_FIRST_MODE 0x10
#define XRFDC_CLK_DIV_DP_OTHER_MODES 0x20
#define XRFDC_CLK_DST_INVALID 0xFF
#define XRFDC_CLK_DST_TILE_224 7
#define XRFDC_CLK_DST_TILE_225 6
#define XRFDC_CLK_DST_TILE_226 5
#define XRFDC_CLK_DST_TILE_227 4
#define XRFDC_CLK_DST_TILE_228 3
#define XRFDC_CLK_DST_TILE_229 2
#define XRFDC_CLK_DST_TILE_230 1
#define XRFDC_CLK_DST_TILE_231 0
#define XRFDC_CLK_EN_CAL_MASK 0x00000001
#define XRFDC_CLK_EN_DIG_MASK 0x00000002
#define XRFDC_CLK_EN_DP_MASK 0x00000004
#define XRFDC_CLK_EN_FAB_MASK 0x00000008
#define XRFDC_CLK_EN_LM_MASK 0x00000010
#define XRFDC_CLK_EN_OFFSET 0x000
#define XRFDC_CLK_NETWORK_CTRL0 0x8C
#define XRFDC_CLK_NETWORK_CTRL1 0x90
#define XRFDC_CLK_NETWORK_CTRL1_EN_SYNC_MASK 0x1000
#define XRFDC_CLK_NETWORK_CTRL1_REGS_MASK 0x3
#define XRFDC_CLK_NETWORK_CTRL1_USE_PLL_MASK 0x1
#define XRFDC_CLK_NETWORK_CTRL1_USE_RX_MASK 0x2
#define XRFDC_CLK_REG_EN_MASK 0x2000
#define XRFDC_CLOCK_DETECT_BOTH 0x3
#define XRFDC_CLOCK_DETECT_CLK 0x1
#define XRFDC_CLOCK_DETECT_DIST 0x2
#define XRFDC_CLOCK_DETECT_DST_SHIFT 1
#define XRFDC_CLOCK_DETECT_MASK 0x0000FFFF
#define XRFDC_CLOCK_DETECT_OFFSET 0x80
#define XRFDC_CLOCK_DETECT_SRC_MASK 0x00005555
#define XRFDC_COARSE_MIX_BYPASS 0x10
#define XRFDC_COARSE_MIX_MIN_SAMPLE_FREQ_BY_FOUR 0x8
#define XRFDC_COARSE_MIX_MODE_C2C_C2R 0x1
#define XRFDC_COARSE_MIX_MODE_R2C 0x2
#define XRFDC_COARSE_MIX_OFF 0x0
#define XRFDC_COARSE_MIX_SAMPLE_FREQ_BY_FOUR 0x4
#define XRFDC_COARSE_MIX_SAMPLE_FREQ_BY_TWO 0x2
#define XRFDC_COMMON_INTR_ENABLE 0x104
#define XRFDC_COMMON_INTR_STS 0x100
#define XRFDC_COMMON_MASK 0x01000000
#define XRFDC_COMMON_SHIFT 20
#define XRFDC_COMPONENT_IS_READY 0x11111111
#define XRFDC_CPL_TYPE_OFFSET 0x314
#define XRFDC_CRSEDLY_UPDT_DLY_MASK 0x00001FF8
#define XRFDC_CRSEDLY_UPDT_MODE_FABRIC 0x00000005
#define XRFDC_CRSEDLY_UPDT_MODE_GRP 0x00000000
#define XRFDC_CRSEDLY_UPDT_MODE_MARKER 0x00000004
#define XRFDC_CRSEDLY_UPDT_MODE_MASK 0x00000007
#define XRFDC_CRSEDLY_UPDT_MODE_SLICE 0x00000001
#define XRFDC_CRSEDLY_UPDT_MODE_SYSREF 0x00000003
#define XRFDC_CRSEDLY_UPDT_MODE_TILE 0x00000002
#define XRFDC_CRSE_4GSPS_ODD_FSBYTWO 0x492
#define XRFDC_CRSE_DLY_CFG_MASK 0x00000007
#define XRFDC_CRSE_DLY_CFG_MASK_EXT 0x0000003F
#define XRFDC_CRSE_DLY_MAX 0x7
#define XRFDC_CRSE_DLY_MAX_EXT 0x28
#define XRFDC_CRSE_MIX_BYPASS 0x0
#define XRFDC_CRSE_MIX_I_FSBYFOUR 0x298
#define XRFDC_CRSE_MIX_I_MINFSBYFOUR 0x688
#define XRFDC_CRSE_MIX_I_ODD_FSBYFOUR 0x2CB
#define XRFDC_CRSE_MIX_I_Q_FSBYTWO 0x410
#define XRFDC_CRSE_MIX_OFF 0x924
#define XRFDC_CRSE_MIX_Q_FSBYFOUR 0x688
#define XRFDC_CRSE_MIX_Q_MINFSBYFOUR 0x298
#define XRFDC_CRSE_MIX_Q_ODD_FSBYFOUR 0x659
#define XRFDC_CRSE_MIX_R_I_FSBYFOUR 0x8A0
#define XRFDC_CRSE_MIX_R_I_MINFSBYFOUR 0x8A0
#define XRFDC_CRSE_MIX_R_Q_FSBYFOUR 0x70C
#define XRFDC_CRSE_MIX_R_Q_MINFSBYFOUR 0x31C
#define XRFDC_CTRL_MASK 0x0440
#define XRFDC_CTRL_STATS_OFFSET 0x0
#define XRFDC_CURRENT_STATE_MASK 0x0000000F
#define XRFDC_CURRENT_STATE_OFFSET 0x0C
#define XRFDC_DAC_CRSE_DLY_CFG_OFFSET 0x0DC
#define XRFDC_DAC_CRSE_DLY_UPDT_OFFSET 0x0E0
#define XRFDC_DAC_DATAPATH_OFFSET 0x034
#define XRFDC_DAC_DAT_IMR_DP_SCALE_MASK 0x00000800
#define XRFDC_DAC_DAT_IMR_IMR_OV_MASK 0x00004000
#define XRFDC_DAC_DAT_IMR_INTR_IPATH3_MASK 0x00001000
#define XRFDC_DAC_DAT_IMR_INTR_QPATH3_MASK 0x00002000
#define XRFDC_DAC_DAT_IMR_INV_SINC_EVEN_NYQ_MASK 0x00008000
#define XRFDC_DAC_DAT_IMR_INV_SINC_MASK 0x00000100
#define XRFDC_DAC_DAT_IMR_MASK 0x0000FFFF
#define XRFDC_DAC_DAT_IMR_MXR_HLF_I_MASK 0x00000200
#define XRFDC_DAC_DAT_IMR_MXR_HLF_Q_MASK 0x00000400
#define XRFDC_DAC_DAT_ISR_INVSINC_MASK 0x00000100
#define XRFDC_DAC_DAT_PATH_ISR_MASK 0x0000FFFF
#define XRFDC_DAC_DECODER_CLK_OFFSET 0x184
#define XRFDC_DAC_DECODER_CTRL_OFFSET 0x180
#define XRFDC_DAC_FABRIC_IMR_OFFSET 0x018
#define XRFDC_DAC_FABRIC_ISR_OFFSET 0x014
#define XRFDC_DAC_FABRIC_RATE_OFFSET 0x008
#define XRFDC_DAC_FAB_RATE_RD_MASK 0x00001F00
#define XRFDC_DAC_FAB_RATE_WR_MASK 0x0000001F
#define XRFDC_DAC_FIFO_DELAY_MASK 0x000000FFF
#define XRFDC_DAC_FIFO_IMR_MASK 0x0000003F
#define XRFDC_DAC_FIFO_IMR_SUPP_MASK 0x00000030
#define XRFDC_DAC_FIFO_START_OFFSET 0x010
#define XRFDC_DAC_IMR_MODE_HIGHPASS 1
#define XRFDC_DAC_IMR_MODE_LOWPASS 0
#define XRFDC_DAC_INTERP_CTRL_OFFSET 0x040
#define XRFDC_DAC_INTERP_DATA_MASK 0x00000001
#define XRFDC_DAC_INT_MODE_FULL_BW 0
#define XRFDC_DAC_INT_MODE_FULL_BW_BYPASS 3
#define XRFDC_DAC_INT_MODE_HALF_BW_IMR 2
#define XRFDC_DAC_INVSINC_OFFSET 0x0C0
#define XRFDC_DAC_ITERP_DATA_OFFSET 0x044
#define XRFDC_DAC_IXR_DATAPATH_MASK 0x000FFFF0
#define XRFDC_DAC_IXR_DP_SCALE_MASK 0x00008000
#define XRFDC_DAC_IXR_FIFOACTIND_OF_MASK 0x20000000
#define XRFDC_DAC_IXR_FIFOACTIND_UF_MASK 0x10000000
#define XRFDC_DAC_IXR_FIFOUSRDAT_MASK 0x3000000F
#define XRFDC_DAC_IXR_FIFOUSRDAT_SUPP_MASK 0x30000000
#define XRFDC_DAC_IXR_FIFOUSRDAT_SUPP_SHIFT 24
#define XRFDC_DAC_IXR_IMR_OV_MASK 0x00040000
#define XRFDC_DAC_IXR_INTP_I_STG0_MASK 0x00000010
#define XRFDC_DAC_IXR_INTP_I_STG1_MASK 0x00000020
#define XRFDC_DAC_IXR_INTP_I_STG2_MASK 0x00000040
#define XRFDC_DAC_IXR_INTP_I_STG3_MASK 0x00010000
#define XRFDC_DAC_IXR_INTP_Q_STG0_MASK 0x00000080
#define XRFDC_DAC_IXR_INTP_Q_STG1_MASK 0x00000100
#define XRFDC_DAC_IXR_INTP_Q_STG2_MASK 0x00000200
#define XRFDC_DAC_IXR_INTP_Q_STG3_MASK 0x00020000
#define XRFDC_DAC_IXR_INTP_STG_MASK 0x000003F0
#define XRFDC_DAC_IXR_INVSNC_OF_MASK 0x00001000
#define XRFDC_DAC_IXR_INV_SINC_EVEN_NYQ_MASK 0x00080000
#define XRFDC_DAC_IXR_MXR_HLF_I_MASK 0x00002000
#define XRFDC_DAC_IXR_MXR_HLF_Q_MASK 0x00004000
#define XRFDC_DAC_MAX_WR_FAB_RATE 16
#define XRFDC_DAC_MB_CFG_OFFSET 0x0C4
#define XRFDC_DAC_MB_SEL_MASK 0x0003
#define XRFDC_DAC_MC_CFG0_CAS_BLDR_MASK 0xE000
#define XRFDC_DAC_MC_CFG0_OFFSET 0x1C4
#define XRFDC_DAC_MC_CFG2_BLDGAIN_MASK 0x0000FFC0
#define XRFDC_DAC_MC_CFG2_BLDGAIN_SHIFT 6
#define XRFDC_DAC_MC_CFG2_CAS_BIAS_MASK 0x001F
#define XRFDC_DAC_MC_CFG2_GEN1_COMP_MASK 0x0020
#define XRFDC_DAC_MC_CFG2_GEN1_COMP_SHIFT 5
#define XRFDC_DAC_MC_CFG2_OPCSCAS_20MA 0x00004858
#define XRFDC_DAC_MC_CFG2_OPCSCAS_32MA 0x0000A0D8
#define XRFDC_DAC_MC_CFG2_OPCSCAS_MASK 0x0000F8F8
#define XRFDC_DAC_MC_CFG3_CSGAIN_20MA 0x000087C0
#define XRFDC_DAC_MC_CFG3_CSGAIN_32MA 0x0000FFC0
#define XRFDC_DAC_MC_CFG3_CSGAIN_MASK 0x0000FFC0
#define XRFDC_DAC_MC_CFG3_CSGAIN_SHIFT 6
#define XRFDC_DAC_MC_CFG3_OFFSET 0x1D0
#define XRFDC_DAC_MC_CFG3_OPT_LUT_MASK 0x03F0
#define XRFDC_DAC_MC_CFG3_OPT_LUT_SHIFT 4
#define XRFDC_DAC_MC_CFG3_OPT_MASK 0x001F
#define XRFDC_DAC_MC_CFG3_UPDATE_MASK 0x0020
#define XRFDC_DAC_MIXER_MODE_REAL 0x2
#define XRFDC_DAC_PATHS_ENABLED_OFFSET 0x00A8
#define XRFDC_DAC_SAMPLING_MAX 6554
#define XRFDC_DAC_SAMPLING_MIN 500
#define XRFDC_DAC_TDD_MODE0_OFFSET 0x060
#define XRFDC_DAC_TILE 1
#define XRFDC_DAC_TILES_ENABLED_SHIFT 4
#define XRFDC_DAC_UPDATE_DYN_OFFSET 0x020
#define XRFDC_DAC_UPDT_CRSE_DLY_MASK 0x00000020
#define XRFDC_DAC_VOP_BLDR_LOW_BITS_MASK 0xF
#define XRFDC_DAC_VOP_CTRL_OFFSET 0x198
#define XRFDC_DAC_VOP_CTRL_REG_UPDT_MASK 0x2
#define XRFDC_DAC_VOP_CTRL_TST_BLD_MASK 0x1
#define XRFDC_DATAPATH_IMR_MASK 0x00000004
#define XRFDC_DATAPATH_IMR_SHIFT 2
#define XRFDC_DATAPATH_LATENCY_MASK 0x00000008
#define XRFDC_DATAPATH_MODE_DUC_0_FSDIVFOUR 2
#define XRFDC_DATAPATH_MODE_DUC_0_FSDIVTWO 1
#define XRFDC_DATAPATH_MODE_FSDIVFOUR_FSDIVTWO 3
#define XRFDC_DATAPATH_MODE_MASK 0x00000003
#define XRFDC_DATAPATH_MODE_NODUC_0_FSDIVTWO 4
#define XRFDC_DATA_PATH_SHIFT 4
#define XRFDC_DATA_SCALER_MASK 0x00000001
#define XRFDC_DATA_SCALER_OFFSET 0x190
#define XRFDC_DATA_TYPE_IQ 0x00000001
#define XRFDC_DATA_TYPE_REAL 0x00000000
#define XRFDC_DATPATH_IMR_OFFSET 0x03C
#define XRFDC_DATPATH_ISR_OFFSET 0x038
#define XRFDC_DAT_CLK_EN_MASK 0x0000000F
#define XRFDC_DAT_FIFO_OVR_SHIFT 16
#define XRFDC_DAT_IMR_DECI_IPATH_MASK 0x00000007
#define XRFDC_DAT_IMR_INTR_QPATH_MASK 0x00000038
#define XRFDC_DAT_IMR_QMC_GAIN_MASK 0x00000040
#define XRFDC_DAT_IMR_QMC_OFFST_MASK 0x00000080
#define XRFDC_DAT_ISR_DECI_IPATH_MASK 0x00000007
#define XRFDC_DAT_ISR_INTR_QPATH_MASK 0x00000038
#define XRFDC_DAT_ISR_QMC_GAIN_MASK 0x00000040
#define XRFDC_DAT_ISR_QMC_OFFST_MASK 0x00000080
#define XRFDC_DAT_OVR_MASK 0x40000000
#define XRFDC_DAT_SCALE_CFG_MASK 0x00000001
#define XRFDC_DBG_RST_CAL_MASK 0x00000001
#define XRFDC_DBG_RST_DIG_MASK 0x00000008
#define XRFDC_DBG_RST_DP_MASK 0x00000002
#define XRFDC_DBG_RST_DRP_CAL_MASK 0x00000010
#define XRFDC_DBG_RST_FAB_MASK 0x00000004
#define XRFDC_DBG_RST_LM_MASK 0x00000020
#define XRFDC_DECIM_2G_IQ_DATA_TYPE 0x2
#define XRFDC_DECIM_4G_DATA_TYPE 0x3
#define XRFDC_DECODER_MAX_LINEARITY_MODE 0x2
#define XRFDC_DECODER_MAX_SNR_MODE 0x1
#define XRFDC_DEC_CFG_4GSPS_MASK 0x00000003
#define XRFDC_DEC_CFG_CHA_MASK 0x00000000
#define XRFDC_DEC_CFG_CHB_MASK 0x00000001
#define XRFDC_DEC_CFG_IQ_MASK 0x00000002
#define XRFDC_DEC_CFG_MASK 0x00000003
#define XRFDC_DEC_CTRL_MODE_MASK 0x00000007
#define XRFDC_DEC_IMR_MASK 0x000000FF
#define XRFDC_DEC_IMR_SUBADC0_OVR_MASK 0x00000002
#define XRFDC_DEC_IMR_SUBADC0_UND_MASK 0x00000001
#define XRFDC_DEC_IMR_SUBADC1_OVR_MASK 0x00000008
#define XRFDC_DEC_IMR_SUBADC1_UND_MASK 0x00000004
#define XRFDC_DEC_IMR_SUBADC2_OVR_MASK 0x00000020
#define XRFDC_DEC_IMR_SUBADC2_UND_MASK 0x00000010
#define XRFDC_DEC_IMR_SUBADC3_OVR_MASK 0x00000080
#define XRFDC_DEC_IMR_SUBADC3_UND_MASK 0x00000040
#define XRFDC_DEC_ISR_SUBADC0_OVR_MASK 0x00000002
#define XRFDC_DEC_ISR_SUBADC0_UND_MASK 0x00000001
#define XRFDC_DEC_ISR_SUBADC1_OVR_MASK 0x00000008
#define XRFDC_DEC_ISR_SUBADC1_UND_MASK 0x00000004
#define XRFDC_DEC_ISR_SUBADC2_OVR_MASK 0x00000020
#define XRFDC_DEC_ISR_SUBADC2_UND_MASK 0x00000010
#define XRFDC_DEC_ISR_SUBADC3_OVR_MASK 0x00000080
#define XRFDC_DEC_ISR_SUBADC3_UND_MASK 0x00000040
#define XRFDC_DEC_ISR_SUBADC_MASK 0x000000FF
#define XRFDC_DEC_MOD_MASK 0x00000007
#define XRFDC_DEC_MOD_MASK_EXT 0x0000003F
#define XRFDC_DEVICE_ID_SIZE 4
#define XRFDC_DIGITALPATH_ENABLE 0x1
#define XRFDC_DIGITAL_PATH_ENABLED_SHIFT 16
#define XRFDC_DIGI_ANALOG_SHIFT12 12
#define XRFDC_DIGI_ANALOG_SHIFT4 4
#define XRFDC_DIGI_ANALOG_SHIFT8 8
#define XRFDC_DISABLED 0
#define XRFDC_DIST_CTRL_CLK_T1_SRC_LOCAL 0x1000
#define XRFDC_DIST_CTRL_DIST_SRC_LOCAL 0x40
#define XRFDC_DIST_CTRL_DIST_SRC_PLL 0x800
#define XRFDC_DIST_CTRL_TO_PLL_DIV 0x10
#define XRFDC_DIST_CTRL_TO_T1 0x20
#define XRFDC_DIST_MAX 8
#define XRFDC_DIST_OUT_NONE 0
#define XRFDC_DIST_OUT_OUTDIV 2
#define XRFDC_DIST_OUT_RX 1
#define XRFDC_DITH_DISABLE 0
#define XRFDC_DITH_ENABLE 1
#define XRFDC_DIVISION_FACTOR_MIN 1
#define XRFDC_DSA_UPDT_OFFSET 0x254
#define XRFDC_DUAL_TILE 2
#define XRFDC_ENABLED 1
#define XRFDC_EN_INTR_ADC_TILE0_MASK 0x00000010
#define XRFDC_EN_INTR_ADC_TILE1_MASK 0x00000020
#define XRFDC_EN_INTR_ADC_TILE2_MASK 0x00000040
#define XRFDC_EN_INTR_ADC_TILE3_MASK 0x00000080
#define XRFDC_EN_INTR_DAC_TILE0_MASK 0x00000001
#define XRFDC_EN_INTR_DAC_TILE1_MASK 0x00000002
#define XRFDC_EN_INTR_DAC_TILE2_MASK 0x00000004
#define XRFDC_EN_INTR_DAC_TILE3_MASK 0x00000008
#define XRFDC_EN_INTR_SLICE0_MASK 0x00000001
#define XRFDC_EN_INTR_SLICE1_MASK 0x00000002
#define XRFDC_EN_INTR_SLICE2_MASK 0x00000004
#define XRFDC_EN_INTR_SLICE3_MASK 0x00000008
#define XRFDC_EN_INTR_SLICE_MASK 0x0000000F
#define XRFDC_EN_INVSINC_MASK 0x00000001
#define XRFDC_EN_I_IQ 0x00000001
#define XRFDC_EN_I_IQ_MASK 0x00000003
#define XRFDC_EN_MB_MASK 0x00000008
#define XRFDC_EN_MB_SHIFT 3
#define XRFDC_EN_Q_IQ 0x00000004
#define XRFDC_EN_Q_IQ_MASK 0x0000000C
#define XRFDC_ES1_SI 0
#define XRFDC_EVENT_CRSE_DLY 0x00000002
#define XRFDC_EVENT_MIXER 0x00000001
#define XRFDC_EVENT_QMC 0x00000004
#define XRFDC_EVEN_NYQUIST_ZONE 0x2
#define XRFDC_EVNT_SRC_IMMEDIATE 0x00000000
#define XRFDC_EVNT_SRC_MARKER 0x00000004
#define XRFDC_EVNT_SRC_PL 0x00000005
#define XRFDC_EVNT_SRC_SLICE 0x00000001
#define XRFDC_EVNT_SRC_SYSREF 0x00000003
#define XRFDC_EVNT_SRC_TILE 0x00000002
#define XRFDC_EXPORTCTRL_CLKDIST 0x0400
#define XRFDC_EXPORTCTRL_DSA 0x0400
#define XRFDC_EXPORTCTRL_VOP 0x2000
#define XRFDC_EXTERNAL_CLK 0x0
#define XRFDC_FAB_CLK_DIV1 0x1
#define XRFDC_FAB_CLK_DIV16 0x5
#define XRFDC_FAB_CLK_DIV2 0x2
#define XRFDC_FAB_CLK_DIV4 0x3
#define XRFDC_FAB_CLK_DIV8 0x4
#define XRFDC_FAB_CLK_DIV_CAL_MASK 0x000000F0
#define XRFDC_FAB_CLK_DIV_MASK 0x0000000F
#define XRFDC_FAB_CLK_DIV_SYNC_PULSE_MASK 0x00000400
#define XRFDC_FAB_IMR_MARGIND_OVR_MASK 0x00000004
#define XRFDC_FAB_IMR_MARGIND_UND_MASK 0x00000008
#define XRFDC_FAB_IMR_USRDAT_MASK 0x00000003
#define XRFDC_FAB_IMR_USRDAT_OVR_MASK 0x00000001
#define XRFDC_FAB_IMR_USRDAT_UND_MASK 0x00000002
#define XRFDC_FAB_ISR_MARGIND_OVR_MASK 0x00000004
#define XRFDC_FAB_ISR_MARGIND_UND_MASK 0x00000008
#define XRFDC_FAB_ISR_USRDAT_MASK 0x00000003
#define XRFDC_FAB_ISR_USRDAT_OVR_MASK 0x00000001
#define XRFDC_FAB_ISR_USRDAT_UND_MASK 0x00000002
#define XRFDC_FAB_RATE_1 1
#define XRFDC_FAB_RATE_16 16
#define XRFDC_FAB_RATE_2 2
#define XRFDC_FAB_RATE_4 4
#define XRFDC_FAB_RATE_8 8
#define XRFDC_FAB_RATE_RD_SHIFT 8
#define XRFDC_FAB_RD_PTR_OFFST_MASK 0x0000003F
#define XRFDC_FAILURE 1
#define XRFDC_FEND_DAT_CTRL_MASK 0x000000FF
#define XRFDC_FIFO_ACTL_OF_MASK 0x00000010
#define XRFDC_FIFO_ACTL_UF_MASK 0x00000020
#define XRFDC_FIFO_CHANNEL_ACT 0
#define XRFDC_FIFO_CHANNEL_BOTH 2
#define XRFDC_FIFO_CHANNEL_OBS 1
#define XRFDC_FIFO_ENABLE 0x230
#define XRFDC_FIFO_EN_MASK 0x00000001
#define XRFDC_FIFO_EN_OBS_MASK 0x00000002
#define XRFDC_FIFO_EN_OBS_SHIFT 1
#define XRFDC_FIFO_LTNCY_DIS_MASK 0x000000010
#define XRFDC_FIFO_LTNCY_DONE_MASK 0x00008000
#define XRFDC_FIFO_LTNCY_KEY_MASK 0x00004000
#define XRFDC_FIFO_LTNCY_PRD_MASK 0x00000007
#define XRFDC_FIFO_LTNCY_RESTRT_MASK 0x00000008
#define XRFDC_FIFO_LTNCY_RES_MASK 0x00000FFF
#define XRFDC_FIFO_MRGN_OF_MASK 0x00000004
#define XRFDC_FIFO_MRGN_UF_MASK 0x00000008
#define XRFDC_FIFO_OVR_MASK 0x80000000
#define XRFDC_FIFO_USRD_OF_MASK 0x00000001
#define XRFDC_FIFO_USRD_UF_MASK 0x00000002
#define XRFDC_FINE_MIX_SCALE_MASK 0x00000010
#define XRFDC_FULL_BW_DIVISOR 1
#define XRFDC_GEN1_HIGH_I 32000
#define XRFDC_GEN1_LOW_I 20000
#define XRFDC_GEN3 2
#define XRFDC_GLBL_OFST_ADC 4
#define XRFDC_GLBL_OFST_DAC 0
#define XRFDC_HALF_BW_DIVISOR 2
#define XRFDC_HSCOM_ADDR 0x1C00
#define XRFDC_HSCOM_CLK_DIV_OFFSET 0xB0
#define XRFDC_HSCOM_CLK_DSTR_MASK 0xC788
#define XRFDC_HSCOM_CLK_DSTR_MASK_ALT 0x1870
#define XRFDC_HSCOM_CLK_DSTR_OFFSET 0x088
#define XRFDC_HSCOM_EFUSE_2_OFFSET 0x144
#define XRFDC_HSCOM_FIFO_START_OBS_EN_MASK 0x00000200
#define XRFDC_HSCOM_FIFO_START_OBS_EN_SHIFT 9
#define XRFDC_HSCOM_FIFO_START_OBS_OFFSET 0x0BC
#define XRFDC_HSCOM_FIFO_START_OFFSET 0x0C0
#define XRFDC_HSCOM_NETWORK_CTRL1_MASK 0x02F
#define XRFDC_HSCOM_PWR_OFFSET 0x094
#define XRFDC_HSCOM_PWR_STATE_MASK 0x0000FFFF
#define XRFDC_HSCOM_PWR_STATE_OFFSET 0xB4
#define XRFDC_HSCOM_PWR_STATS_DIST_EXT 0xF0FE
#define XRFDC_HSCOM_PWR_STATS_DIST_EXT_DIV 0xF0FE
#define XRFDC_HSCOM_PWR_STATS_DIST_EXT_DIV_SRC 0xF2FC
#define XRFDC_HSCOM_PWR_STATS_DIST_EXT_SRC 0xF2FC
#define XRFDC_HSCOM_PWR_STATS_DIST_PLL 0xFDFE
#define XRFDC_HSCOM_PWR_STATS_EXTERNAL 0xF240
#define XRFDC_HSCOM_PWR_STATS_PLL 0xFFC0
#define XRFDC_HSCOM_PWR_STATS_RX_EXT 0xF2FC
#define XRFDC_HSCOM_PWR_STATS_RX_EXT_DIV 0xF2FC
#define XRFDC_HSCOM_PWR_STATS_RX_PLL 0xFFFC
#define XRFDC_HSCOM_UPDT_DYN_OFFSET 0x0B8
#define XRFDC_INTERNAL_PLL_CLK 0x1
#define XRFDC_INTERP_DECIM_10X 0xA
#define XRFDC_INTERP_DECIM_12X 0xC
#define XRFDC_INTERP_DECIM_16X 0x10
#define XRFDC_INTERP_DECIM_1X 0x1
#define XRFDC_INTERP_DECIM_20X 0x14
#define XRFDC_INTERP_DECIM_24X 0x18
#define XRFDC_INTERP_DECIM_2X 0x2
#define XRFDC_INTERP_DECIM_3X 0x3
#define XRFDC_INTERP_DECIM_40X 0x28
#define XRFDC_INTERP_DECIM_4X 0x4
#define XRFDC_INTERP_DECIM_5X 0x5
#define XRFDC_INTERP_DECIM_6X 0x6
#define XRFDC_INTERP_DECIM_8X 0x8
#define XRFDC_INTERP_DECIM_OFF 0x0
#define XRFDC_INTERP_MODE_I_MASK 0x00000007
#define XRFDC_INTERP_MODE_I_MASK_EXT 0x0000003F
#define XRFDC_INTERP_MODE_MASK 0x00000077
#define XRFDC_INTERP_MODE_MASK_EXT 0x00003F3F
#define XRFDC_INTERP_MODE_Q_SHIFT 4
#define XRFDC_INTERP_MODE_Q_SHIFT_EXT 8
#define XRFDC_INTR_CMODE_OVR_MASK 0x00040000
#define XRFDC_INTR_CMODE_UNDR_MASK 0x00080000
#define XRFDC_INTR_COMMON_MASK 0x00000010
#define XRFDC_INTR_DAT_OVR_MASK 0x00004000
#define XRFDC_INTR_ENABLE 0x204
#define XRFDC_INTR_FIFO_OVR_MASK 0x00008000
#define XRFDC_INTR_OVR_RANGE_MASK 0x00000008
#define XRFDC_INTR_OVR_VOLTAGE_MASK 0x00000004
#define XRFDC_INTR_STS 0x200
#define XRFDC_INV_SYNC_EN_MAX 1
#define XRFDC_INV_SYNC_MODE_MAX 2
#define XRFDC_IP_BASE 0x0
#define XRFDC_IXR_FIFOMRGNIND_OF_MASK 0x00000004
#define XRFDC_IXR_FIFOMRGNIND_UF_MASK 0x00000008
#define XRFDC_IXR_FIFOUSRDAT_MASK 0x0000000F
#define XRFDC_IXR_FIFOUSRDAT_OBS_MASK 0x0000F000
#define XRFDC_IXR_FIFOUSRDAT_OBS_SHIFT 12
#define XRFDC_IXR_FIFOUSRDAT_OF_MASK 0x00000001
#define XRFDC_IXR_FIFOUSRDAT_UF_MASK 0x00000002
#define XRFDC_IXR_QMC_GAIN_PHASE_MASK 0x00000400
#define XRFDC_IXR_QMC_OFFST_MASK 0x00000800
#define XRFDC_I_IQ_COS_MINSIN 0x00000C00
#define XRFDC_LINK_COUPLING_AC 0x1
#define XRFDC_LINK_COUPLING_DC 0x0
#define XRFDC_MB_C2C_BLK0 0x5E
#define XRFDC_MB_C2C_BLK1 0x5D
#define XRFDC_MB_C2R_BLK0 0x5C
#define XRFDC_MB_C2R_BLK1 0x0
#define XRFDC_MB_CFG_MASK 0x000001FF
#define XRFDC_MB_CONFIG_MASK 0x00000007
#define XRFDC_MB_CONFIG_OFFSET 0x308
#define XRFDC_MB_DATATYPE_C2C 0x1
#define XRFDC_MB_DATATYPE_C2R 0x4
#define XRFDC_MB_DATATYPE_R2C 0x2
#define XRFDC_MB_DUAL_BAND 2
#define XRFDC_MB_EN_4X_MASK 0x00000100
#define XRFDC_MB_MODE_2X_BLK01 0x1
#define XRFDC_MB_MODE_2X_BLK01_BLK23 0x3
#define XRFDC_MB_MODE_2X_BLK01_BLK23_ALT 0x5
#define XRFDC_MB_MODE_2X_BLK23 0x2
#define XRFDC_MB_MODE_4X 0x4
#define XRFDC_MB_MODE_SB 0x0
#define XRFDC_MB_QUAD_BAND 4
#define XRFDC_MC_CFG0_MIX_MODE_MASK 0x00000002
#define XRFDC_MC_CFG0_MIX_MODE_SHIFT 1
#define XRFDC_MICRO 1000000
#define XRFDC_MILLI 1000
#define XRFDC_MIN_ATTEN 0
#define XRFDC_MIXER_MODE_BYPASS 0x2
#define XRFDC_MIXER_MODE_C2C 0x1
#define XRFDC_MIXER_MODE_C2C_MASK 0x0000000F
#define XRFDC_MIXER_MODE_C2R 0x2
#define XRFDC_MIXER_MODE_C2R_MASK 0x00000003
#define XRFDC_MIXER_MODE_IQ 0x1
#define XRFDC_MIXER_MODE_OFF 0x0
#define XRFDC_MIXER_MODE_OFF_MASK 0x00000000
#define XRFDC_MIXER_MODE_R2C 0x3
#define XRFDC_MIXER_MODE_R2C_MASK 0x00000005
#define XRFDC_MIXER_MODE_R2R 0x4
#define XRFDC_MIXER_SCALE_0P7 0x2
#define XRFDC_MIXER_SCALE_1P0 0x1
#define XRFDC_MIXER_SCALE_AUTO 0x0
#define XRFDC_MIXER_TYPE_COARSE 0x1
#define XRFDC_MIXER_TYPE_DISABLED 0x3
#define XRFDC_MIXER_TYPE_FINE 0x2
#define XRFDC_MIXER_TYPE_OFF 0x0
#define XRFDC_MIX_CFG0_MASK 0x00000FFF
#define XRFDC_MIX_CFG1_MASK 0x00000FFF
#define XRFDC_MIX_I_DAT_WRD0_MASK 0x00000007
#define XRFDC_MIX_I_DAT_WRD1_MASK 0x00000038
#define XRFDC_MIX_I_DAT_WRD2_MASK 0x000001C0
#define XRFDC_MIX_I_DAT_WRD3_MASK 0x00000E00
#define XRFDC_MIX_Q_DAT_WRD0_MASK 0x00000007
#define XRFDC_MIX_Q_DAT_WRD1_MASK 0x00000038
#define XRFDC_MIX_Q_DAT_WRD2_MASK 0x000001C0
#define XRFDC_MIX_Q_DAT_WRD3_MASK 0x00000E00
#define XRFDC_MODE_INVSINC_MASK 0x00000003
#define XRFDC_MTS_ADC_MARKER 0x0018
#define XRFDC_MTS_ADC_MARKER_CNT 0x0010
#define XRFDC_MTS_AMARK_CNT_M 0x00FF
#define XRFDC_MTS_AMARK_DONE_M 0x100000
#define XRFDC_MTS_AMARK_LOC_M 0x0F0000
#define XRFDC_MTS_BAD_REF_TILE 8192
#define XRFDC_MTS_DAC_FABRIC_OFFSET 0x0C
#define XRFDC_MTS_DAC_MARKER_CTRL 0x0048
#define XRFDC_MTS_DELAY_CTRL 0x0028
#define XRFDC_MTS_DELAY_OVER 16
#define XRFDC_MTS_DELAY_VAL_M 0x041F
#define XRFDC_MTS_DTC_INVALID 128
#define XRFDC_MTS_FIFO_CTRL_ADC 0x0010
#define XRFDC_MTS_FIFO_CTRL_DAC 0x0014
#define XRFDC_MTS_IP_NOT_READY 64
#define XRFDC_MTS_MARKER_MISM 8
#define XRFDC_MTS_MARKER_RUN 4
#define XRFDC_MTS_NOT_ENABLED 512
#define XRFDC_MTS_NOT_SUPPORTED 1
#define XRFDC_MTS_OK 0
#define XRFDC_MTS_PLLEN_M 0x0001
#define XRFDC_MTS_SCAN_INIT 0
#define XRFDC_MTS_SCAN_RELOAD 1
#define XRFDC_MTS_SRCAP_DIG_M 0x0100
#define XRFDC_MTS_SRCAP_EN_TRX_M 0x0400
#define XRFDC_MTS_SRCAP_INIT_M 0x8200
#define XRFDC_MTS_SRCAP_PLL_M 0x0100
#define XRFDC_MTS_SRCLR_PLL_M 0x0200
#define XRFDC_MTS_SRCLR_T1_M 0x2000
#define XRFDC_MTS_SRCOUNT_CTRL 0x004C
#define XRFDC_MTS_SRCOUNT_M 0x00FF
#define XRFDC_MTS_SRCOUNT_VAL 0x0050
#define XRFDC_MTS_SRDIST 0x1CA0
#define XRFDC_MTS_SRFREQ_VAL 0x0054
#define XRFDC_MTS_SYSREF_DISABLE 0
#define XRFDC_MTS_SYSREF_ENABLE 1
#define XRFDC_MTS_SYSREF_FREQ_NDONE 4096
#define XRFDC_MTS_SYSREF_GATE_ERROR 2048
#define XRFDC_MTS_TARGET_LOW 32
#define XRFDC_MTS_TIMEOUT 2
#define XRFDC_MULTIBAND_MODE_2X 0x2
#define XRFDC_MULTIBAND_MODE_4X 0x4
#define XRFDC_MXR_MODE_OFFSET 0x088
#define XRFDC_NCO_FQWD_LOW_MASK 0x0000FFFF
#define XRFDC_NCO_FQWD_MASK 0x0000FFFFFFFFFFFF
#define XRFDC_NCO_FQWD_MID_MASK 0x0000FFFF
#define XRFDC_NCO_FQWD_MID_SHIFT 16
#define XRFDC_NCO_FQWD_UPP_MASK 0x0000FFFF
#define XRFDC_NCO_FQWD_UPP_SHIFT 32
#define XRFDC_NCO_PHASE_LOW_MASK 0x0000FFFF
#define XRFDC_NCO_PHASE_LOW_OFFSET 0x0A4
#define XRFDC_NCO_PHASE_MASK 0x0003FFFF
#define XRFDC_NCO_PHASE_MODE_ODD 0x00000002
#define XRFDC_NCO_PHASE_MOD_4PHASE 0x00000003
#define XRFDC_NCO_PHASE_MOD_EVEN 0x00000001
#define XRFDC_NCO_PHASE_MOD_MASK 0x00000003
#define XRFDC_NCO_PHASE_RST_MASK 0x00000001
#define XRFDC_NCO_PHASE_UPP_MASK 0x00000003
#define XRFDC_NCO_PHASE_UPP_OFFSET 0x0A0
#define XRFDC_NCO_PHASE_UPP_SHIFT 16
#define XRFDC_NCO_RST_OFFSET 0x090
#define XRFDC_NCO_UPDT_DLY_MASK 0x00001FF8
#define XRFDC_NCO_UPDT_MODE_FABRIC 0x00000005
#define XRFDC_NCO_UPDT_MODE_GRP 0x00000000
#define XRFDC_NCO_UPDT_MODE_MARKER 0x00000004
#define XRFDC_NCO_UPDT_MODE_MASK 0x00000007
#define XRFDC_NCO_UPDT_MODE_SLICE 0x00000001
#define XRFDC_NCO_UPDT_MODE_SYSREF 0x00000003
#define XRFDC_NCO_UPDT_MODE_TILE 0x00000002
#define XRFDC_NCO_UPDT_OFFSET 0x08C
#define XRFDC_NCO_UPDT_RST_DLY_MASK 0x0000D000
#define XRFDC_NET_CTRL_CLK_INPUT_DIST 0x20
#define XRFDC_NET_CTRL_CLK_REC_DIST_T1 0x2
#define XRFDC_NET_CTRL_CLK_REC_PLL 0x1
#define XRFDC_NET_CTRL_CLK_T1_SRC_DIST 0x8
#define XRFDC_NET_CTRL_CLK_T1_SRC_LOCAL 0x4
#define XRFDC_NUM_INST_SIZE 4
#define XRFDC_NUM_OF_BLKS1 0x1
#define XRFDC_NUM_OF_BLKS2 0x2
#define XRFDC_NUM_OF_BLKS3 0x3
#define XRFDC_NUM_OF_BLKS4 0x4
#define XRFDC_NUM_OF_TILES1 0x1
#define XRFDC_NUM_OF_TILES2 0x2
#define XRFDC_NUM_OF_TILES3 0x3
#define XRFDC_NUM_OF_TILES4 0x4
#define XRFDC_NUM_SLICES_HSADC 2
#define XRFDC_NUM_SLICES_LSADC 4
#define XRFDC_ODD_NYQUIST_ZONE 0x1
#define XRFDC_OUTPUT_CURRENT_20MA 20
#define XRFDC_OUTPUT_CURRENT_32MA 32
#define XRFDC_PATH_ENABLED_TILE_SHIFT 4
#define XRFDC_PLLOPDIV_INPUT_DIST_LOCAL 0x800
#define XRFDC_PLLREFDIV_INPUT_DIST 0x40
#define XRFDC_PLLREFDIV_INPUT_FABRIC 0x60
#define XRFDC_PLLREFDIV_INPUT_OFF 0x20
#define XRFDC_PLL_CHARGEPUMP 0x48
#define XRFDC_PLL_CRS1 0x28
#define XRFDC_PLL_CRS1_VCO_SEL_MASK 0x00008001
#define XRFDC_PLL_CRS2 0x2C
#define XRFDC_PLL_CRS2_VAL 0x7008
#define XRFDC_PLL_DIVIDER0 0x30
#define XRFDC_PLL_DIVIDER0_ALT_MASK 0xC00
#define XRFDC_PLL_DIVIDER0_BYPDIV_MASK 0x400
#define XRFDC_PLL_DIVIDER0_BYPPLL_MASK 0x800
#define XRFDC_PLL_DIVIDER0_BYP_OPDIV_MASK 0x0400
#define XRFDC_PLL_DIVIDER0_BYP_PLL_MASK 0x0800
#define XRFDC_PLL_DIVIDER0_MASK 0x0CFF
#define XRFDC_PLL_DIVIDER0_MODE_MASK 0x00C0
#define XRFDC_PLL_DIVIDER0_SHIFT 6
#define XRFDC_PLL_DIVIDER0_VALUE_MASK 0x003F
#define XRFDC_PLL_DIVIDER1 0x34
#define XRFDC_PLL_FPDIV 0x5C
#define XRFDC_PLL_FREQ 0x300
#define XRFDC_PLL_FS 0x304
#define XRFDC_PLL_LOCKED 0x2
#define XRFDC_PLL_LOCKED_MASK 0x00000008
#define XRFDC_PLL_LOCKED_SHIFT 3
#define XRFDC_PLL_LOCK_DLY_CNT 1000
#define XRFDC_PLL_LOCK_WAIT 1000
#define XRFDC_PLL_LPF0 0x4C
#define XRFDC_PLL_LPF1 0x50
#define XRFDC_PLL_LPF1_VAL 0x6
#define XRFDC_PLL_OUTDIV_MODE_1 0x0
#define XRFDC_PLL_OUTDIV_MODE_2 0x1
#define XRFDC_PLL_OUTDIV_MODE_3 0x2
#define XRFDC_PLL_OUTDIV_MODE_3_VAL 0x1
#define XRFDC_PLL_OUTDIV_MODE_N 0x3
#define XRFDC_PLL_REFDIV 0x40
#define XRFDC_PLL_REFDIV_MASK 0x0E0
#define XRFDC_PLL_SDM_CFG0 0x00
#define XRFDC_PLL_SDM_SEED0 0x18
#define XRFDC_PLL_SDM_SEED1 0x1C
#define XRFDC_PLL_SOURCE_NONE 0
#define XRFDC_PLL_SOURCE_OUTDIV 2
#define XRFDC_PLL_SOURCE_RX 1
#define XRFDC_PLL_SPARE0 0x38
#define XRFDC_PLL_SPARE1 0x3C
#define XRFDC_PLL_UNLOCKED 0x1
#define XRFDC_PLL_VCO0 0x54
#define XRFDC_PLL_VCO1 0x58
#define XRFDC_PLL_VCO_SEL_AUTO_MASK 0x00008000
#define XRFDC_PLL_VREG 0x44
#define XRFDC_PREMIUMCTRL_CLKDIST 0x0040
#define XRFDC_PROD_SI 1
#define XRFDC_PWR_MODE_OFF 0
#define XRFDC_PWR_MODE_ON 1
#define XRFDC_PWR_STATE_MASK 0x0000FFFF
#define XRFDC_PWR_UP_STAT_MASK 0x00000004
#define XRFDC_PWR_UP_STAT_SHIFT 2
#define XRFDC_QMC_CFG_EN_GAIN_MASK 0x00000001
#define XRFDC_QMC_CFG_EN_PHASE_MASK 0x00000002
#define XRFDC_QMC_CFG_OFFSET 0x0CC
#define XRFDC_QMC_CFG_PHASE_SHIFT 1
#define XRFDC_QMC_GAIN_CRCTN_MASK 0x00003FFF
#define XRFDC_QMC_GAIN_OFFSET 0x0D4
#define XRFDC_QMC_OFFST_CRCTN_MASK 0x00000FFF
#define XRFDC_QMC_OFFST_CRCTN_SIGN_MASK 0x00000800
#define XRFDC_QMC_OFF_OFFSET 0x0D0
#define XRFDC_QMC_PHASE_CRCTN_MASK 0x00000FFF
#define XRFDC_QMC_PHASE_CRCTN_SIGN_MASK 0x00000800
#define XRFDC_QMC_PHASE_OFFSET 0x0D8
#define XRFDC_QMC_UPDT_DLY_MASK 0x00001FF8
#define XRFDC_QMC_UPDT_MODE_FABRIC 0x00000005
#define XRFDC_QMC_UPDT_MODE_GRP 0x00000000
#define XRFDC_QMC_UPDT_MODE_MARKER 0x00000004
#define XRFDC_QMC_UPDT_MODE_MASK 0x00000007
#define XRFDC_QMC_UPDT_MODE_SLICE 0x00000001
#define XRFDC_QMC_UPDT_MODE_SYSREF 0x00000003
#define XRFDC_QMC_UPDT_MODE_TILE 0x00000002
#define XRFDC_QMC_UPDT_OFFSET 0x0C8
#define XRFDC_QUAD_TILE 4
#define XRFDC_Q_IQ_SIN_COS 0x00001000
#define XRFDC_REFCLK_DIV_1_MASK 0x10
#define XRFDC_REFCLK_DIV_2_MASK 0x0
#define XRFDC_REFCLK_DIV_3_MASK 0x1
#define XRFDC_REFCLK_DIV_4_MASK 0x2
#define XRFDC_REFCLK_DIV_MASK 0x1F
#define XRFDC_REF_CLK_DIV_1 0x1
#define XRFDC_REF_CLK_DIV_2 0x2
#define XRFDC_REF_CLK_DIV_3 0x3
#define XRFDC_REF_CLK_DIV_4 0x4
#define XRFDC_REGION_SIZE 0x40000
#define XRFDC_RESET_OFFSET 0x00
#define XRFDC_RESTART_CLR_DLY_CNT 1000
#define XRFDC_RESTART_CLR_WAIT 1000
#define XRFDC_RESTART_MASK 0x00000001
#define XRFDC_RESTART_OFFSET 0x04
#define XRFDC_RESTART_STATE_OFFSET 0x08
#define XRFDC_RSR_START_SHIFT 8
#define XRFDC_RX_MC_CFG0_CM_MASK 0x00000040
#define XRFDC_RX_MC_CFG0_IM3_DITH_MASK 0x00000020
#define XRFDC_RX_MC_CFG0_IM3_DITH_SHIFT 5
#define XRFDC_RX_MC_CFG0_MASK 0x0000FFFF
#define XRFDC_RX_MC_CFG1_MASK 0x0000FFFF
#define XRFDC_RX_MC_CFG2_MASK 0x0000FFFF
#define XRFDC_RX_MC_PWRDWN_MASK 0x0000FFFF
#define XRFDC_RX_PR_MC_CFG0_IDIV_MASK 0x00000010
#define XRFDC_RX_PR_MC_CFG0_MASK 0x0000FFFF
#define XRFDC_RX_PR_MC_CFG0_PSNK_MASK 0x00002000
#define XRFDC_RX_PR_MC_CFG1_MASK 0x0000FFFF
#define XRFDC_SB_C2C_BLK0 0x82
#define XRFDC_SB_C2C_BLK1 0x64
#define XRFDC_SB_C2R 0x40
#define XRFDC_SELECT_ALL_TILES -1
#define XRFDC_SEL_CB_TO_DECI_MASK 0x00000020
#define XRFDC_SEL_CB_TO_MIX0_MASK 0x0000000C
#define XRFDC_SEL_CB_TO_MIX0_SHIFT 2
#define XRFDC_SEL_CB_TO_MIX1_MASK 0x00000003
#define XRFDC_SEL_CB_TO_QMC_MASK 0x00000010
#define XRFDC_SEL_I_IQ_MASK 0x00000F00
#define XRFDC_SEL_Q_IQ_MASK 0x0000F000
#define XRFDC_SIGDET_MODE_AVG 0
#define XRFDC_SIGDET_MODE_RNDM 1
#define XRFDC_SIGDET_TC_2_0 0
#define XRFDC_SIGDET_TC_2_12 4
#define XRFDC_SIGDET_TC_2_14 5
#define XRFDC_SIGDET_TC_2_16 6
#define XRFDC_SIGDET_TC_2_18 7
#define XRFDC_SIGDET_TC_2_2 1
#define XRFDC_SIGDET_TC_2_4 2
#define XRFDC_SIGDET_TC_2_8 3
#define XRFDC_SINGLEBAND_MODE 0x1
#define XRFDC_SI_REV_ES 0
#define XRFDC_SI_REV_PROD 1
#define XRFDC_SM_STATE0 0x0
#define XRFDC_SM_STATE1 0x1
#define XRFDC_SM_STATE15 0xF
#define XRFDC_SM_STATE3 0x3
#define XRFDC_SM_STATE7 0x7
#define XRFDC_STATE_CAL 0xB
#define XRFDC_STATE_CLK_DET 0x6
#define XRFDC_STATE_FULL 0xF
#define XRFDC_STATE_OFF 0x0
#define XRFDC_STATE_PWRUP 0x3
#define XRFDC_STATE_SHUTDOWN 0x1
#define XRFDC_STATE_WAIT 100
#define XRFDC_STATUS_OFFSET 0x228
#define XRFDC_SUBADC0_IXR_DCDR_OF_MASK 0x00010000
#define XRFDC_SUBADC0_IXR_DCDR_UF_MASK 0x00020000
#define XRFDC_SUBADC1_IXR_DCDR_OF_MASK 0x00040000
#define XRFDC_SUBADC1_IXR_DCDR_UF_MASK 0x00080000
#define XRFDC_SUBADC2_IXR_DCDR_OF_MASK 0x00100000
#define XRFDC_SUBADC2_IXR_DCDR_UF_MASK 0x00200000
#define XRFDC_SUBADC3_IXR_DCDR_OF_MASK 0x00400000
#define XRFDC_SUBADC3_IXR_DCDR_UF_MASK 0x00800000
#define XRFDC_SUBADC_IXR_DCDR_MASK 0x00FF0000
#define XRFDC_SUBDRP_ADC0_ADDR_MASK 0x000000FF
#define XRFDC_SUBDRP_ADC0_DAT_MASK 0x0000FFFF
#define XRFDC_SUBDRP_ADC1_ADDR_MASK 0x000000FF
#define XRFDC_SUBDRP_ADC1_DAT_MASK 0x0000FFFF
#define XRFDC_SUBDRP_ADC2_ADDR_MASK 0x000000FF
#define XRFDC_SUBDRP_ADC2_DAT_MASK 0x0000FFFF
#define XRFDC_SUBDRP_ADC3_ADDR_MASK 0x000000FF
#define XRFDC_SUBDRP_ADC3_DAT_MASK 0x0000FFFF
#define XRFDC_SUCCESS 0
#define XRFDC_SWITCH_MTRX_MASK 0x0000003F
#define XRFDC_TDD_CTRL_MASK 0x0000001F
#define XRFDC_TDD_CTRL_MODE01_MASK 0x00000003
#define XRFDC_TDD_CTRL_MODE0_MASK 0x00000001
#define XRFDC_TDD_CTRL_MODE1_MASK 0x00000002
#define XRFDC_TDD_CTRL_MODE1_SHIFT 1
#define XRFDC_TDD_CTRL_OBS_EN_MASK 0x00000008
#define XRFDC_TDD_CTRL_OBS_EN_SHIFT 3
#define XRFDC_TDD_CTRL_RTP_MASK 0x00000004
#define XRFDC_TDD_CTRL_RTP_OBS_MASK 0x00000010
#define XRFDC_TDD_CTRL_RTP_OBS_SHIFT 4
#define XRFDC_TDD_CTRL_RTP_SHIFT 2
#define XRFDC_THRESHOLD_CLRMD_AUTO_CLR 0x2
#define XRFDC_THRESHOLD_CLRMD_MANUAL_CLR 0x1
#define XRFDC_TILES_ENABLED_OFFSET 0x00A0
#define XRFDC_TILE_DRP_OFFSET 0x2000
#define XRFDC_TILE_ID0 0x0
#define XRFDC_TILE_ID1 0x1
#define XRFDC_TILE_ID2 0x2
#define XRFDC_TILE_ID3 0x3
#define XRFDC_TILE_ID4 0x4
#define XRFDC_TILE_ID_INV 0x4
#define XRFDC_TILE_ID_MAX 0x3
#define XRFDC_TILE_RESET_MASK 0x00000001
#define XRFDC_TILE_SOURCE_DIST 1
#define XRFDC_TILE_SOURCE_FABRIC 2
#define XRFDC_TILE_SOURCE_RX 0
#define XRFDC_TISK_BYPASS0_MASK 0x00000080
#define XRFDC_TISK_BYPASS1_MASK 0x00008000
#define XRFDC_TISK_CAL_PRI_MASK 0x00000001
#define XRFDC_TISK_CHOP_EN_MASK 0x00000008
#define XRFDC_TISK_DAC0_CODE_MASK 0x000000FF
#define XRFDC_TISK_DAC0_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DAC1_CODE_MASK 0x000000FF
#define XRFDC_TISK_DAC1_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DAC2_CODE_MASK 0x000000FF
#define XRFDC_TISK_DAC2_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DAC3_CODE_MASK 0x000000FF
#define XRFDC_TISK_DAC3_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DACP0_CODE_MASK 0x000000FF
#define XRFDC_TISK_DACP0_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DACP1_CODE_MASK 0x000000FF
#define XRFDC_TISK_DACP1_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DACP2_CODE_MASK 0x000000FF
#define XRFDC_TISK_DACP2_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DACP3_CODE_MASK 0x000000FF
#define XRFDC_TISK_DACP3_OVRID_EN_MASK 0x00008000
#define XRFDC_TISK_DBG_CTRL_MASK 0x0000F000
#define XRFDC_TISK_DBG_UPDT_RT_MASK 0x00001000
#define XRFDC_TISK_DITH_DLY_MASK 0x0000E000
#define XRFDC_TISK_DITH_INV_MASK 0x00000FF0
#define XRFDC_TISK_DZ_MAX_VAL_MASK 0x0000FF00
#define XRFDC_TISK_DZ_MIN_VAL_MASK 0x000000FF
#define XRFDC_TISK_EN_MASK 0x00000001
#define XRFDC_TISK_MODE_MASK 0x00000002
#define XRFDC_TISK_MU0_MASK 0x0000000F
#define XRFDC_TISK_MU1_MASK 0x00000F00
#define XRFDC_TISK_MU_CM_MASK 0x000000F0
#define XRFDC_TISK_MU_DF_MASK 0x00000F00
#define XRFDC_TISK_SETTLE_MASK 0x000000FF
#define XRFDC_TISK_ZONE_MASK 0x00000004
#define XRFDC_TISK_ZONE_SHIFT 2
#define XRFDC_TI_DCB_CTRL0_MASK 0x0000FFFF
#define XRFDC_TI_DCB_CTRL1_MASK 0x00001FFF
#define XRFDC_TI_DCB_CTRL2_MASK 0x00001FFF
#define XRFDC_TI_DCB_MODE1_2GSPS 0x00005000
#define XRFDC_TI_DCB_MODE1_4GSPS 0x00007800
#define XRFDC_TI_DCB_MODE_MASK 0x00007800
#define XRFDC_TI_DCB_STS0_BG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS0_FG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS1_BG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS1_FG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS2_BG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS2_FG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS3_BG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS3_FG_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS4_LSB_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS4_MSB_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS5_LSB_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS5_MSB_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS6_LSB_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS6_MSB_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS7_LSB_MASK 0x0000FFFF
#define XRFDC_TI_DCB_STS7_MSB_MASK 0x0000FFFF
#define XRFDC_TI_TISK_CHOP_EN_MASK 0x00000008
#define XRFDC_TI_TISK_DBG_CTRL_MASK 0x0000F000
#define XRFDC_TI_TISK_DBG_UPDT_RT_MASK 0x00001000
#define XRFDC_TI_TISK_DITH_DLY_MASK 0x0000E000
#define XRFDC_TI_TISK_EN_MASK 0x00000001
#define XRFDC_TI_TISK_MODE_MASK 0x00000002
#define XRFDC_TI_TISK_MU_CM_MASK 0x000000F0
#define XRFDC_TI_TISK_MU_DF_MASK 0x00000F00
#define XRFDC_TI_TISK_ZONE_MASK 0x00000004
#define XRFDC_TRSHD0_AVG_LOW_MASK 0x0000FFFF
#define XRFDC_TRSHD0_AVG_UPP_MASK 0x0000FFFF
#define XRFDC_TRSHD0_AVG_UPP_SHIFT 16
#define XRFDC_TRSHD0_CLR_MOD_MASK 0x00000004
#define XRFDC_TRSHD0_EN_MOD_MASK 0x00000003
#define XRFDC_TRSHD0_OVER_MASK 0x00003FFF
#define XRFDC_TRSHD0_STIKY_CLR_MASK 0x00000008
#define XRFDC_TRSHD0_UNDER_MASK 0x00003FFF
#define XRFDC_TRSHD1_AVG_LOW_MASK 0x0000FFFF
#define XRFDC_TRSHD1_AVG_UPP_MASK 0x0000FFFF
#define XRFDC_TRSHD1_AVG_UPP_SHIFT 16
#define XRFDC_TRSHD1_CLR_MOD_MASK 0x00000004
#define XRFDC_TRSHD1_EN_MOD_MASK 0x00000003
#define XRFDC_TRSHD1_OVER_MASK 0x00003FFF
#define XRFDC_TRSHD1_STIKY_CLR_MASK 0x00000008
#define XRFDC_TRSHD1_UNDER_MASK 0x00003FFF
#define XRFDC_TRSHD_HYSTERISIS 0x00000003
#define XRFDC_TRSHD_OFF 0x0
#define XRFDC_TRSHD_STICKY_OVER 0x00000001
#define XRFDC_TRSHD_STICKY_UNDER 0x00000002
#define XRFDC_TSCB_TUNE_AUTOCAL 0x0550
#define XRFDC_TSCB_TUNE_NOT_AUTOCAL 0x0440
#define XRFDC_UPDATE_THRESHOLD_0 0x1
#define XRFDC_UPDATE_THRESHOLD_1 0x2
#define XRFDC_UPDATE_THRESHOLD_BOTH 0x4
#define XRFDC_UPDT_EVNT_MASK 0x0000000F
#define XRFDC_UPDT_EVNT_NCO_MASK 0x00000002
#define XRFDC_UPDT_EVNT_QMC_MASK 0x00000004
#define XRFDC_UPDT_EVNT_SLICE_MASK 0x00000001
#define XRFDC_VCO_LOWER_BAND 0x1
#define XRFDC_VCO_UPPER_BAND 0x0
#define XRFDC_WAIT_ATTEMPTS_CNT 10000
