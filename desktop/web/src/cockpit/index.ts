/**
 * Public surface of the cockpit module.
 *
 * Re-exports the top-level `<Cockpit />` and every child component used by tests and the
 * future Tauri shell. Consumers should import from here rather than reaching into
 * individual files.
 */

export { Cockpit } from './Cockpit';
export type { CockpitProps } from './Cockpit';

export { HeaderBar } from './HeaderBar';
export { SnapshotPanel } from './SnapshotPanel';
export type { SnapshotPanelProps } from './SnapshotPanel';
export { PadCard } from './PadCard';
export type { PadCardProps } from './PadCard';
export { HistoryStrip } from './HistoryStrip';
export { MutationPanel } from './MutationPanel';
export type { MutationPanelProps } from './MutationPanel';
export { StyleCrateQueue } from './StyleCrateQueue';
export {
  DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL,
  DEFAULT_LIVE_READINESS_MODEL,
  LiveAnalyzerPanel,
  LiveCommandQueue,
  LiveDeviceInventory,
  LiveHardwareRail,
  LivePerformanceFlow,
  LiveReadinessPanel,
  LiveSafetyChecklist,
  LiveSceneQueue,
  LiveSnapshotCompatibility,
  LiveSnapshotHistory,
  LiveStatusFooter,
  LiveTwelvePadSurface,
} from './LiveReadinessPanel';
export type {
  LiveGuiAnalyzerPanelControlDict,
  LiveGuiAnalyzerPanelModelDict,
  LiveGuiAnalyzerSpectrumBandDict,
  LiveGuiAnalyzerWaveformBinDict,
  LiveGuiArmHardwareGateDict,
  LiveGuiCommandQueueModelDict,
  LiveGuiDeviceInventoryCardDict,
  LiveGuiDeviceInventoryModelDict,
  LiveGuiHardwareRailActionDict,
  LiveGuiHardwareRailCardDict,
  LiveGuiHardwareRailModelDict,
  LiveGuiHardwareRailSafetyCheckDict,
  LiveGuiLastActionDict,
  LiveGuiQueuedCommandDict,
  LiveGuiRytmPadSurfaceCardDict,
  LiveGuiRytmTwelvePadSurfaceModelDict,
  LiveGuiSafetyChecklistItemDict,
  LiveGuiSafetyChecklistModelDict,
  LiveGuiSceneCardDict,
  LiveGuiScenePreviewQueueItemDict,
  LiveGuiSceneQueueModelDict,
  LiveGuiSnapshotCompatibilityModelDict,
  LiveGuiSnapshotCompatibilityPadDict,
  LiveGuiSnapshotHistoryControlDict,
  LiveGuiSnapshotHistoryEntryDict,
  LiveGuiSnapshotHistoryModelDict,
  LiveGuiStatusFooterItemDict,
  LiveGuiStatusFooterModelDict,
  LiveGuiUndoStackEntryDict,
  LivePerformanceFlowModel,
  LivePerformanceFlowStepModel,
  LiveReadinessModel,
  LiveReadinessPanelProps,
  LiveReadinessPanelViewProps,
} from '../types/live_gui_protocol';
export { ProfileToggle } from './ProfileToggle';
export type { ProfileToggleProps } from './ProfileToggle';
export { ProfileChips } from './ProfileChips';
export type { ProfileChipsProps } from './ProfileChips';
export { DepthSlider } from './DepthSlider';
export type { DepthSliderProps } from './DepthSlider';
export { ActionBar } from './ActionBar';
export type { ActionBarProps } from './ActionBar';
export { Knob, valueToAngle } from './Knob';
export type { KnobProps } from './Knob';
export { LockButton } from './LockButton';
export type { LockButtonProps } from './LockButton';

export { CockpitClientProvider, useCockpitClient } from './context';
export type { CockpitClientProviderProps } from './context';
export { usePadLocks } from './usePadLocks';
export type { PadLocksApi } from './usePadLocks';
