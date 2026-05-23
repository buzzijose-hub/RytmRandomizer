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
  HistoryEntry,
  History,

  // Events
  Event,
  EventType,
  SnapshotChangedEvent,
  MutationPreviewedEvent,
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
  SendCommand,
  SaveCommand,
  LoadSnapshotCommand,
  UndoCommand,
  ExportProfileModelCommand,
} from '../ws/protocol';

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
