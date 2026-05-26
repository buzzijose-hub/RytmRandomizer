/**
 * Public types surface.
 *
 * Re-exports the wire-protocol types and the store slices so consumers
 * (notably `src/cockpit/**`, owned by WS-J) can import from one place.
 */

export type {
  // Domain enums
  DeviceKind,
  ProfileKind,
  TransitionCurve,
  SafetyStatus,
  SendPlanReadinessReason,
  HistoryEntryKind,
  HistoryVia,
  SessionMode,
  ExportTarget,

  // Core data
  PadState,
  Snapshot,
  StyleTrait,
  TraitPadWeight,
  ProfileModel,
  PadDelta,
  MutationCandidate,
  SendPlanPacket,
  CockpitSendPlan,
  HistoryEntry,
  History,

  // Events
  Event,
  EventType,
  SnapshotChangedEvent,
  MutationPreviewedEvent,
  SendPlanChangedEvent,
  HistoryUpdatedEvent,
  ProfileChangedEvent,
  SessionStatusEvent,

  // Commands
  Command,
  CommandType,
  CommandEnvelope,
  CommandAck,
  SelectProfileCommand,
  SetDepthCommand,
  SetPadLockCommand,
  TogglePreviewCommand,
  RegenCommand,
  PrepareSendPlanCommand,
  SendCommand,
  SaveCommand,
  LoadSnapshotCommand,
  UndoCommand,
  ExportProfileModelCommand,
} from '../ws/protocol';

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
  LiveReadinessModel,
  LiveReadinessPanelProps,
} from './live_gui_protocol';

export type {
  CockpitState,
  CockpitActions,
  CockpitStore,
  SessionStatus,
} from '../state/store';

export type {
  CockpitClient,
  CockpitClientOptions,
  ClientLogger,
  ConnectionStatus,
  EventHandler,
  Unsubscribe,
  WebSocketLike,
  WebSocketFactory,
} from '../ws/client';
