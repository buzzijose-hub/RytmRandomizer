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
export type { StyleCrateQueueProps } from './StyleCrateQueue';
export {
  DEFAULT_STYLE_CRATE_QUEUE_MODEL,
  DEFAULT_STYLE_CRATE_REHEARSAL_DECK,
  toStyleCrateQueueModel,
} from './styleCrateQueueModel';
export type {
  StyleCrateQueueCrate,
  StyleCrateQueueModel,
  StyleCrateQueueMove,
  StyleCrateTone,
} from './styleCrateQueueModel';
export {
  PerformanceConsole,
} from './PerformanceConsole';
export type { PerformanceConsoleProps } from './PerformanceConsole';
export { performanceConsoleDemoModel } from './performanceConsoleDemoModel';
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
  LiveGuiPerformanceConsoleDeviceInventoryModelDict,
  LiveGuiPerformanceConsoleHardwareValidationStepDict,
  LiveGuiPerformanceConsoleMacroActionCardDict,
  LiveGuiPerformanceConsoleMacroActionDeckDict,
  LiveGuiPerformanceConsoleMacroCheckpointDict,
  LiveGuiPerformanceConsoleModelDict,
  LiveGuiPerformanceConsolePadLaneCheckDict,
  LiveGuiPerformanceConsolePromotionCriterionDict,
  LiveGuiPerformanceConsoleRehearsalBoardDict,
  LiveGuiPerformanceConsoleRehearsalChapterDict,
  LiveGuiPerformanceConsoleRehearsalCueDict,
  LiveGuiPerformanceConsoleReplayCommandDict,
  LiveGuiPerformanceConsoleRytmTwelvePadSurfaceModelDict,
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
