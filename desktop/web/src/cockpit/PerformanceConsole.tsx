import { useEffect, useMemo, useRef, useState } from 'react';

import type {
  LiveGuiDeviceInventoryCardDict,
  LiveGuiPerformanceConsoleLiveKitOperatorPackageDict,
  LiveGuiPerformanceConsoleLiveKitOperatorPackageSlotBindingDict,
  LiveGuiPerformanceConsoleLiveKitOperatorPackageStepDict,
  LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerDict,
  LiveGuiPerformanceConsoleMacroActionCardDict,
  LiveGuiPerformanceConsoleModelDict,
  LiveGuiPerformanceConsoleRytmMacroPolicyRowDict,
  LiveGuiRytmPadSurfaceCardDict,
  LiveGuiSnapshotHistoryEntryDict,
} from '../types/live_gui_protocol';
import type {
  StyleCrateRehearsalCrateCardDict,
  StyleCrateRehearsalQueueCardDict,
} from '../types/style_crate_rehearsal_deck';
import type {
  BuildOperatorPackageReceiptCommand,
  CommandAck,
  MockApplyOperatorPackageCommand,
  OperatorPackageApplyPreview,
  OperatorPackageMockApply,
  OperatorPackageReceipt,
  PreviewOperatorPackageApplyCommand,
  RehearseOperatorPackageSequenceCommand,
  RehearseOperatorPackageStepCommand,
} from '../ws/protocol';
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID } from './devices';
import { PanelHost } from './panels/PanelHost';
import { RYTM_PARAMETER_GROUPS } from './parameterGroups';

export interface PerformanceConsoleProps {
  model: LiveGuiPerformanceConsoleModelDict;
  packetSource?: string;
  onRehearseOperatorPackageStep?: (
    command: RehearseOperatorPackageStepCommand,
  ) => Promise<CommandAck>;
  onRehearseOperatorPackageSequence?: (
    command: RehearseOperatorPackageSequenceCommand,
  ) => Promise<CommandAck>;
  onPreviewOperatorPackageApply?: (
    command: PreviewOperatorPackageApplyCommand,
  ) => Promise<CommandAck>;
  onMockApplyOperatorPackage?: (
    command: MockApplyOperatorPackageCommand,
  ) => Promise<CommandAck>;
  onBuildOperatorPackageReceipt?: (
    command: BuildOperatorPackageReceiptCommand,
  ) => Promise<CommandAck>;
}

const SNAPSHOT_DECK_PREVIEW_PARAMETER_COUNT = 3;
const PREVIEW_DEPTH_MIN = 10;
const PREVIEW_DEPTH_MAX = 90;
const LOCAL_REHEARSAL_STORAGE_KEY = 'rytmrandomizer.performanceConsole.localRehearsal.v1';
const LOCAL_REHEARSAL_STORAGE_VERSION = 1;
const LOCAL_REHEARSAL_PACKAGE_KIND = 'rytmrandomizer.cockpit.local-rehearsal-package';
const LOCAL_REHEARSAL_PACKAGE_VERSION = 1;

const LEGACY_OPERATOR_PACKAGE_FALLBACK: LiveGuiPerformanceConsoleLiveKitOperatorPackageDict = {
  operator_package_version: 'legacy-missing',
  operator_package_id: 'live-kit-operator-package-unavailable',
  operator_package_status: 'unavailable',
  title: 'Live Kit Operator Package',
  summary: 'Operator package metadata is not present on this older console packet.',
  source_audition_id: 'unavailable',
  source_workbench_id: 'unavailable',
  source_package_manifest_version: 'unavailable',
  package_manifest: {
    manifest_version: 'legacy-missing',
    package_kind: 'legacy-missing',
    package_id: 'live-kit-operator-package-unavailable',
    source_audition_id: 'unavailable',
    source_workbench_id: 'unavailable',
    source_package_manifest_version: 'unavailable',
    slot_count: 0,
    queue_count: 0,
    recovery_count: 0,
    journal_preview_count: 0,
    exports_files: false,
    includes: [],
  },
  operator_steps: [],
  slot_bindings: [],
  recovery_requirements: [],
  journal_commit_preview: {
    name: 'Operator package unavailable',
    seed: 'unavailable',
    tags: [],
    pads: [],
    depth: 'none',
    guardrail_mode: 'passive',
    value_summary: 'No operator package metadata was supplied by this packet.',
    notes: 'Load a newer live-gui-performance-console packet for package staging.',
    replay_policy: 'unavailable',
    commit_status: 'unavailable',
    write_policy: 'no-write',
  },
  local_export_preview: {
    export_kind: 'unavailable',
    export_status: 'unavailable',
    writes_files: false,
    extra_fields: [],
    source_audition_id: 'unavailable',
    selected_slot_policy: 'unavailable',
  },
  disabled_controls: ['Send Operator Package'],
  blocked_actions: ['operator package unavailable on this console packet'],
  safety_lines: ['legacy packet: no operator package metadata present'],
  replay_commands: [],
};

const LEGACY_OPERATOR_REVIEW_LEDGER_FALLBACK: LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerDict = {
  ledger_version: 'legacy-missing',
  ledger_id: 'operator-package-review-ledger-unavailable',
  ledger_status: 'unavailable',
  title: 'Operator Package Review Ledger',
  operator_package_id: 'live-kit-operator-package-unavailable',
  source_audition_id: 'unavailable',
  source_workbench_id: 'unavailable',
  review_stage_count: 0,
  step_count: 0,
  review_stages: [],
  step_rows: [],
  readiness_summary: {
    mock_safe: true,
    opened_midi_port: false,
    sent_midi: false,
    writes_files: false,
    mutated_snapshot: false,
    applied_send_plan: false,
    events_emitted: false,
    required_recovery_count: 0,
  },
  blocked_actions: ['operator package review ledger unavailable on this console packet'],
  safety_lines: ['legacy packet: no operator package review ledger present'],
  replay_commands: [],
};

type LegacyPerformanceConsoleModelDict = LiveGuiPerformanceConsoleModelDict & {
  readonly live_kit_operator_package?: LiveGuiPerformanceConsoleLiveKitOperatorPackageDict;
  readonly operator_package_review_ledger?: LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerDict;
};

interface LocalJournalEntry {
  readonly id: string;
  readonly crateName: string;
  readonly moveName: string;
  readonly snapshotId: string;
  readonly depth: number;
}

interface LocalSetPlanEntry {
  readonly id: string;
  readonly crateName: string;
  readonly moveName: string;
  readonly snapshotId: string;
  readonly depth: number;
  readonly status: string;
}

interface LocalOperatorEvent {
  readonly id: string;
  readonly label: string;
  readonly detail: string;
  readonly status: string;
}

interface LocalRehearsalSnapshot {
  readonly version: number;
  readonly selectedCrateKey: string | null;
  readonly selectedQueueKey: string | null;
  readonly selectedSnapshotId: string | null;
  readonly selectedOperatorPackageSlotKey: string | null;
  readonly previewDepth: number | null;
  readonly lastDryRunSummary: string;
  readonly localJournalEntries: ReadonlyArray<LocalJournalEntry>;
  readonly localSetPlanEntries: ReadonlyArray<LocalSetPlanEntry>;
  readonly currentSetPlanStep: LocalSetPlanEntry | null;
  readonly localOperatorEvents: ReadonlyArray<LocalOperatorEvent>;
  readonly lastSetPlanAction: string;
  readonly nextLocalSetPlanIndex: number;
  readonly localAutosaveEnabled: boolean;
}

interface LocalRehearsalPackageManifest {
  readonly sessionLabel: string;
  readonly packetSource: string;
  readonly selectedCrateName: string;
  readonly selectedMoveName: string;
  readonly selectedSnapshotId: string;
  readonly queuedStepCount: number;
  readonly currentStepId: string | null;
  readonly journalTakeCount: number;
  readonly hardwareMode: string;
}

interface LocalRehearsalPackageCompatibility {
  readonly status: string;
  readonly checks: ReadonlyArray<string>;
}

interface LocalRehearsalPackageSafety {
  readonly devices: ReadonlyArray<string>;
  readonly checklist: ReadonlyArray<string>;
}

interface LocalRehearsalPackageAuditionSource {
  readonly sourceAuditionId: string;
  readonly sourceWorkbenchId: string;
  readonly slotKey: string;
  readonly slotLabel: string;
  readonly styleCrate: string;
  readonly journalSeed: string;
  readonly recoveryCommand: string;
}

interface LocalRehearsalPackageOperatorPackage {
  readonly operatorPackageId: string;
  readonly packageExportKey: string;
  readonly cockpitBinding: string;
  readonly localAction: string;
  readonly stageTarget: string;
  readonly safetyStatus: string;
}

interface LocalRehearsalPackage {
  readonly kind: string;
  readonly version: number;
  readonly manifest: LocalRehearsalPackageManifest;
  readonly compatibility: LocalRehearsalPackageCompatibility;
  readonly safety: LocalRehearsalPackageSafety;
  readonly auditionSource?: LocalRehearsalPackageAuditionSource;
  readonly operatorPackage?: LocalRehearsalPackageOperatorPackage;
  readonly blockedActions: ReadonlyArray<string>;
  readonly recoveryNotes: ReadonlyArray<string>;
  readonly rehearsal: LocalRehearsalSnapshot;
}

interface LocalRehearsalImport {
  readonly snapshot: LocalRehearsalSnapshot;
  readonly rehearsalPackage: LocalRehearsalPackage | null;
}

interface LocalRehearsalPackageReviewRow {
  readonly label: string;
  readonly packageValue: string;
  readonly currentValue: string;
  readonly status: string;
}

interface LocalRehearsalPackageReview {
  readonly status: string;
  readonly summary: string;
  readonly rows: ReadonlyArray<LocalRehearsalPackageReviewRow>;
}

function orderedDevices(
  devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>,
): ReadonlyArray<LiveGuiDeviceInventoryCardDict> {
  return [...devices].sort((left, right) => left.order - right.order);
}

function orderedPads(
  pads: ReadonlyArray<LiveGuiRytmPadSurfaceCardDict>,
): ReadonlyArray<LiveGuiRytmPadSurfaceCardDict> {
  return [...pads].sort((left, right) => left.pad - right.pad);
}

function orderedMacroActions(
  cards: ReadonlyArray<LiveGuiPerformanceConsoleMacroActionCardDict>,
): ReadonlyArray<LiveGuiPerformanceConsoleMacroActionCardDict> {
  return [...cards].sort((left, right) => left.order - right.order);
}

function orderedRytmMacroPolicies(
  rows: ReadonlyArray<LiveGuiPerformanceConsoleRytmMacroPolicyRowDict>,
): ReadonlyArray<LiveGuiPerformanceConsoleRytmMacroPolicyRowDict> {
  return [...rows].sort((left, right) => left.order - right.order);
}

function toTestIdKey(value: string): string {
  return value.toLowerCase().replaceAll('_', '-').replaceAll('/', '-').replaceAll(' ', '-');
}

function toReferenceKey(value: string): string {
  return value.toLowerCase().replaceAll('-', '_');
}

function sameReferenceKey(left: string, right: string): boolean {
  return toReferenceKey(left) === toReferenceKey(right);
}

function toHumanLabel(value: string): string {
  return value
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function toStatusLabel(value: string): string {
  return toHumanLabel(value).toUpperCase();
}

function uniqueText(values: ReadonlyArray<string>): ReadonlyArray<string> {
  return [...new Set(values.filter((value) => value.trim().length > 0))];
}

function deviceTrackLabel(device: LiveGuiDeviceInventoryCardDict, index: number): string | number {
  if (device.device_id === ANALOG_FOUR_DEVICE_ID) {
    return `T${index + 1}`;
  }
  if (device.device_id === RYTM_DEVICE_ID) {
    return index + 1;
  }
  return `${device.default_midi_channel_label}:${index + 1}`;
}

function portSummary(
  devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>,
  model: LiveGuiPerformanceConsoleModelDict,
): string {
  const armGate = model.safety_checklist.arm_gate;
  if (armGate.midi_port_name !== null) {
    return armGate.midi_port_name;
  }
  if (armGate.midi_port_open) {
    return 'MIDI port open';
  }
  const portStates = uniqueText(devices.map((device) => device.port_state));
  if (portStates.every((state) => ['closed', 'not_open', 'none'].includes(state))) {
    return 'No MIDI Port Open';
  }
  return portStates.map(toHumanLabel).join(' / ');
}

function mockSummary(devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>): string {
  return uniqueText(devices.map((device) => device.mock_state)).map(toHumanLabel).join(' / ') || 'mock state unknown';
}

function armSummary(model: LiveGuiPerformanceConsoleModelDict): string {
  if (model.command_queue.hardware_armed) {
    return 'ARMED';
  }
  return toStatusLabel(model.safety_checklist.arm_gate.state);
}

function dryRunSummary(model: LiveGuiPerformanceConsoleModelDict): string {
  return model.command_queue.dry_run_active ? 'dry-run active' : 'dry-run inactive';
}

function snapshotSceneLabel(snapshot: LiveGuiSnapshotHistoryEntryDict | undefined): string {
  if (snapshot === undefined || snapshot.scene_slot === null) {
    return 'Scene not set';
  }
  return `Scene ${snapshot.scene_slot}`;
}

function snapshotIdentityLabel(snapshot: LiveGuiSnapshotHistoryEntryDict | undefined): string {
  return snapshot === undefined ? 'No current snapshot' : `Snapshot ${snapshot.snapshot_id}`;
}

function snapshotBpmLabel(snapshot: LiveGuiSnapshotHistoryEntryDict | undefined): string {
  if (snapshot === undefined) {
    return 'BPM unknown';
  }
  return snapshot.bpm_label;
}

function profileLabels(
  model: LiveGuiPerformanceConsoleModelDict,
  currentMove: { readonly risk_status: string; readonly status: string } | undefined,
  currentMacro: LiveGuiPerformanceConsoleMacroActionCardDict | undefined,
): ReadonlyArray<string> {
  const labels = [model.macro_action_deck.deck_status];
  if (currentMove !== undefined) {
    labels.push(currentMove.risk_status, currentMove.status);
  }
  if (currentMacro !== undefined) {
    labels.push(currentMacro.risk_label);
  }
  return uniqueText(labels);
}

function companionTrackCount(devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>): number {
  return devices
    .filter((device) => device.device_id !== RYTM_DEVICE_ID)
    .reduce((total, device) => total + device.track_count, 0);
}

function deviceListLabel(devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>): string {
  if (devices.length === 0) {
    return 'none';
  }
  return devices.map((device) => device.display_name).join(' + ');
}

function queuedCommandButtonLabel(
  command: { readonly label: string } | undefined,
  queueStatus: string,
): string {
  if (command === undefined) {
    return `Queue ${queueStatus}`;
  }
  return `Queue ${command.label}`;
}

function clampPreviewDepth(value: number): number {
  return Math.min(PREVIEW_DEPTH_MAX, Math.max(PREVIEW_DEPTH_MIN, Math.round(value)));
}

function inputDepthValue(depth: number): number {
  return depth === 0 ? PREVIEW_DEPTH_MIN : clampPreviewDepth(depth);
}

function localTakeId(index: number): string {
  return `local-take-${String(index + 1).padStart(2, '0')}`;
}

function localSetPlanId(index: number): string {
  return `local-step-${String(index + 1).padStart(2, '0')}`;
}

function localSetPlanEntrySummary(entry: LocalSetPlanEntry): string {
  return `${entry.moveName} / ${entry.crateName} / ${entry.snapshotId} / ${entry.depth}%`;
}

function localSetPlanStatusSummary(
  current: LocalSetPlanEntry | null,
  queued: ReadonlyArray<LocalSetPlanEntry>,
  lastAction: string,
): string {
  if (current === null && queued.length === 0) {
    return `${lastAction} No active local set plan. Local only; no MIDI sent.`;
  }
  const currentLabel = current === null ? 'no current step' : `current ${current.id}`;
  return `${lastAction} ${currentLabel}; ${queued.length} queued. Local only; no MIDI sent.`;
}

function localSetPlanHandoffLine(
  label: string,
  entry: LocalSetPlanEntry | null | undefined,
): string {
  if (entry === null || entry === undefined) {
    return `${label}: none`;
  }
  return `${label}: ${entry.id} / ${entry.moveName} / ${entry.crateName} / ${entry.snapshotId} / ${entry.depth}%`;
}

function localOperatorRecentLine(events: ReadonlyArray<LocalOperatorEvent>): string {
  const lastEvent = events.at(-1);
  if (lastEvent === undefined) {
    return 'Recent: no local operator activity.';
  }
  return `Recent: ${lastEvent.label}`;
}

function localOperatorEventId(index: number): string {
  return `local-event-${String(index + 1).padStart(2, '0')}`;
}

function isKeyboardActivation(key: string): boolean {
  return key === 'Enter' || key === ' ';
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function stringField(record: Readonly<Record<string, unknown>>, key: string): string | null {
  const value = record[key];
  return typeof value === 'string' ? value : null;
}

function nullableStringField(
  record: Readonly<Record<string, unknown>>,
  key: string,
): string | null {
  const value = record[key];
  return value === null || typeof value === 'undefined' ? null : stringField(record, key);
}

function numberField(record: Readonly<Record<string, unknown>>, key: string): number | null {
  const value = record[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function booleanField(record: Readonly<Record<string, unknown>>, key: string): boolean | null {
  const value = record[key];
  return typeof value === 'boolean' ? value : null;
}

function localJournalEntryFromUnknown(value: unknown): LocalJournalEntry | null {
  if (!isRecord(value)) {
    return null;
  }
  const id = stringField(value, 'id');
  const crateName = stringField(value, 'crateName');
  const moveName = stringField(value, 'moveName');
  const snapshotId = stringField(value, 'snapshotId');
  const depth = numberField(value, 'depth');
  if (id === null || crateName === null || moveName === null || snapshotId === null || depth === null) {
    return null;
  }
  return {
    id,
    crateName,
    moveName,
    snapshotId,
    depth: clampPreviewDepth(depth),
  };
}

function localSetPlanEntryFromUnknown(value: unknown): LocalSetPlanEntry | null {
  if (!isRecord(value)) {
    return null;
  }
  const id = stringField(value, 'id');
  const crateName = stringField(value, 'crateName');
  const moveName = stringField(value, 'moveName');
  const snapshotId = stringField(value, 'snapshotId');
  const depth = numberField(value, 'depth');
  if (id === null || crateName === null || moveName === null || snapshotId === null || depth === null) {
    return null;
  }
  return {
    id,
    crateName,
    moveName,
    snapshotId,
    depth: clampPreviewDepth(depth),
    status: stringField(value, 'status') ?? 'Local only',
  };
}

function localOperatorEventFromUnknown(value: unknown): LocalOperatorEvent | null {
  if (!isRecord(value)) {
    return null;
  }
  const id = stringField(value, 'id');
  const label = stringField(value, 'label');
  const detail = stringField(value, 'detail');
  if (id === null || label === null || detail === null) {
    return null;
  }
  return {
    id,
    label,
    detail,
    status: stringField(value, 'status') ?? 'Local only',
  };
}

function localArrayFromUnknown<T>(
  value: unknown,
  parser: (candidate: unknown) => T | null,
): ReadonlyArray<T> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.flatMap((candidate) => {
    const parsed = parser(candidate);
    return parsed === null ? [] : [parsed];
  });
}

function localRehearsalSnapshotFromUnknown(value: unknown): LocalRehearsalSnapshot | null {
  if (!isRecord(value) || numberField(value, 'version') !== LOCAL_REHEARSAL_STORAGE_VERSION) {
    return null;
  }
  const currentSetPlanStep = localSetPlanEntryFromUnknown(value.currentSetPlanStep);
  const importedPreviewDepth = numberField(value, 'previewDepth');
  return {
    version: LOCAL_REHEARSAL_STORAGE_VERSION,
    selectedCrateKey: nullableStringField(value, 'selectedCrateKey'),
    selectedQueueKey: nullableStringField(value, 'selectedQueueKey'),
    selectedSnapshotId: nullableStringField(value, 'selectedSnapshotId'),
    selectedOperatorPackageSlotKey: nullableStringField(value, 'selectedOperatorPackageSlotKey'),
    previewDepth: importedPreviewDepth === null ? null : clampPreviewDepth(importedPreviewDepth),
    lastDryRunSummary:
      stringField(value, 'lastDryRunSummary') ?? 'No local dry-run performed.',
    localJournalEntries: localArrayFromUnknown(value.localJournalEntries, localJournalEntryFromUnknown),
    localSetPlanEntries: localArrayFromUnknown(value.localSetPlanEntries, localSetPlanEntryFromUnknown),
    currentSetPlanStep,
    localOperatorEvents: localArrayFromUnknown(value.localOperatorEvents, localOperatorEventFromUnknown),
    lastSetPlanAction: stringField(value, 'lastSetPlanAction') ?? 'No local set-plan action yet.',
    nextLocalSetPlanIndex: Math.max(0, Math.round(numberField(value, 'nextLocalSetPlanIndex') ?? 0)),
    localAutosaveEnabled: booleanField(value, 'localAutosaveEnabled') ?? true,
  };
}

function stringArrayFromUnknown(value: unknown): ReadonlyArray<string> {
  return localArrayFromUnknown(value, (candidate) =>
    typeof candidate === 'string' ? candidate : null,
  );
}

function liveKitOperatorPackageForModel(
  model: LiveGuiPerformanceConsoleModelDict,
): LiveGuiPerformanceConsoleLiveKitOperatorPackageDict {
  return (
    (model as LegacyPerformanceConsoleModelDict).live_kit_operator_package ??
    LEGACY_OPERATOR_PACKAGE_FALLBACK
  );
}

function operatorPackageReviewLedgerForModel(
  model: LiveGuiPerformanceConsoleModelDict,
): LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerDict {
  return (
    (model as LegacyPerformanceConsoleModelDict).operator_package_review_ledger ??
    LEGACY_OPERATOR_REVIEW_LEDGER_FALLBACK
  );
}

function localRehearsalPackageManifestFromUnknown(
  value: unknown,
): LocalRehearsalPackageManifest | null {
  if (!isRecord(value)) {
    return null;
  }
  const sessionLabel = stringField(value, 'sessionLabel');
  const packetSource = stringField(value, 'packetSource');
  const selectedCrateName = stringField(value, 'selectedCrateName');
  const selectedMoveName = stringField(value, 'selectedMoveName');
  const selectedSnapshotId = stringField(value, 'selectedSnapshotId');
  const queuedStepCount = numberField(value, 'queuedStepCount');
  const journalTakeCount = numberField(value, 'journalTakeCount');
  const hardwareMode = stringField(value, 'hardwareMode');
  if (
    sessionLabel === null ||
    packetSource === null ||
    selectedCrateName === null ||
    selectedMoveName === null ||
    selectedSnapshotId === null ||
    queuedStepCount === null ||
    journalTakeCount === null ||
    hardwareMode === null
  ) {
    return null;
  }
  return {
    sessionLabel,
    packetSource,
    selectedCrateName,
    selectedMoveName,
    selectedSnapshotId,
    queuedStepCount: Math.max(0, Math.round(queuedStepCount)),
    currentStepId: nullableStringField(value, 'currentStepId'),
    journalTakeCount: Math.max(0, Math.round(journalTakeCount)),
    hardwareMode,
  };
}

function localRehearsalPackageCompatibilityFromUnknown(
  value: unknown,
): LocalRehearsalPackageCompatibility | null {
  if (!isRecord(value)) {
    return null;
  }
  const status = stringField(value, 'status');
  if (status === null) {
    return null;
  }
  return {
    status,
    checks: stringArrayFromUnknown(value.checks),
  };
}

function localRehearsalPackageSafetyFromUnknown(
  value: unknown,
): LocalRehearsalPackageSafety | null {
  if (!isRecord(value)) {
    return null;
  }
  return {
    devices: stringArrayFromUnknown(value.devices),
    checklist: stringArrayFromUnknown(value.checklist),
  };
}

function localRehearsalPackageAuditionSourceFromUnknown(
  value: unknown,
): LocalRehearsalPackageAuditionSource | null {
  if (!isRecord(value)) {
    return null;
  }
  const sourceAuditionId = stringField(value, 'sourceAuditionId');
  const sourceWorkbenchId = stringField(value, 'sourceWorkbenchId');
  const slotKey = stringField(value, 'slotKey');
  const slotLabel = stringField(value, 'slotLabel');
  const styleCrate = stringField(value, 'styleCrate');
  const journalSeed = stringField(value, 'journalSeed');
  const recoveryCommand = stringField(value, 'recoveryCommand');
  if (
    sourceAuditionId === null ||
    sourceWorkbenchId === null ||
    slotKey === null ||
    slotLabel === null ||
    styleCrate === null ||
    journalSeed === null ||
    recoveryCommand === null
  ) {
    return null;
  }
  return {
    sourceAuditionId,
    sourceWorkbenchId,
    slotKey,
    slotLabel,
    styleCrate,
    journalSeed,
    recoveryCommand,
  };
}

function localRehearsalPackageOperatorPackageFromUnknown(
  value: unknown,
): LocalRehearsalPackageOperatorPackage | null {
  if (!isRecord(value)) {
    return null;
  }
  const operatorPackageId = stringField(value, 'operatorPackageId');
  const packageExportKey = stringField(value, 'packageExportKey');
  const cockpitBinding = stringField(value, 'cockpitBinding');
  const localAction = stringField(value, 'localAction');
  const stageTarget = stringField(value, 'stageTarget');
  const safetyStatus = stringField(value, 'safetyStatus');
  if (
    operatorPackageId === null ||
    packageExportKey === null ||
    cockpitBinding === null ||
    localAction === null ||
    stageTarget === null ||
    safetyStatus === null
  ) {
    return null;
  }
  return {
    operatorPackageId,
    packageExportKey,
    cockpitBinding,
    localAction,
    stageTarget,
    safetyStatus,
  };
}

function localRehearsalPackageFromUnknown(value: unknown): LocalRehearsalPackage | null {
  if (
    !isRecord(value) ||
    stringField(value, 'kind') !== LOCAL_REHEARSAL_PACKAGE_KIND ||
    numberField(value, 'version') !== LOCAL_REHEARSAL_PACKAGE_VERSION
  ) {
    return null;
  }
  const manifest = localRehearsalPackageManifestFromUnknown(value.manifest);
  const compatibility = localRehearsalPackageCompatibilityFromUnknown(value.compatibility);
  const safety = localRehearsalPackageSafetyFromUnknown(value.safety);
  const rehearsal = localRehearsalSnapshotFromUnknown(value.rehearsal);
  if (
    manifest === null ||
    compatibility === null ||
    safety === null ||
    rehearsal === null
  ) {
    return null;
  }
  return {
    kind: LOCAL_REHEARSAL_PACKAGE_KIND,
    version: LOCAL_REHEARSAL_PACKAGE_VERSION,
    manifest,
    compatibility,
    safety,
    auditionSource: localRehearsalPackageAuditionSourceFromUnknown(value.auditionSource) ?? undefined,
    operatorPackage:
      localRehearsalPackageOperatorPackageFromUnknown(value.operatorPackage) ?? undefined,
    blockedActions: stringArrayFromUnknown(value.blockedActions),
    recoveryNotes: stringArrayFromUnknown(value.recoveryNotes),
    rehearsal,
  };
}

function localRehearsalImportFromUnknown(value: unknown): LocalRehearsalImport | null {
  const rehearsalPackage = localRehearsalPackageFromUnknown(value);
  if (rehearsalPackage !== null) {
    return {
      snapshot: rehearsalPackage.rehearsal,
      rehearsalPackage,
    };
  }
  const snapshot = localRehearsalSnapshotFromUnknown(value);
  if (snapshot === null) {
    return null;
  }
  return {
    snapshot,
    rehearsalPackage: null,
  };
}

function packageCompatibilityForSnapshot(
  model: LiveGuiPerformanceConsoleModelDict,
  snapshot: LocalRehearsalSnapshot,
): LocalRehearsalPackageCompatibility {
  const referencedQueueMove =
    snapshot.selectedQueueKey === null
      ? undefined
      : model.style_queue.queue_cards.find((move) => move.queue_key === snapshot.selectedQueueKey);
  const selectedCrateKey = snapshot.selectedCrateKey;
  const crateExists =
    selectedCrateKey === null
      ? true
      : model.style_queue.crate_cards.some((crate) =>
          sameReferenceKey(crate.crate_key, selectedCrateKey),
        );
  const queueExists =
    snapshot.selectedQueueKey === null ||
    referencedQueueMove !== undefined;
  const snapshotExists =
    snapshot.selectedSnapshotId === null ||
    model.snapshot_history.entries.some(
      (entry) => entry.snapshot_id === snapshot.selectedSnapshotId,
    );
  const operatorPackageSlotExists =
    snapshot.selectedOperatorPackageSlotKey === null ||
    (operatorPackageStepBySlot(model, snapshot.selectedOperatorPackageSlotKey) !== undefined &&
      operatorPackageBindingBySlot(model, snapshot.selectedOperatorPackageSlotKey) !== undefined);
  const checks = [
    crateExists
      ? 'selected crate exists in current packet'
      : 'selected crate missing from current packet',
    queueExists
      ? 'selected queued move exists in current packet'
      : 'selected queued move missing from current packet',
    snapshotExists
      ? 'selected snapshot exists in current packet'
      : 'selected snapshot missing from current packet',
    snapshot.selectedOperatorPackageSlotKey === null
      ? 'operator package slot not selected'
      : operatorPackageSlotExists
        ? 'operator package slot exists in current packet'
        : 'operator package slot missing from current packet',
  ];
  return {
    status: checks.some((check) => check.includes('missing')) ? 'needs review' : 'compatible',
    checks,
  };
}

function packageSafetyForModel(
  model: LiveGuiPerformanceConsoleModelDict,
  devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>,
): LocalRehearsalPackageSafety {
  return {
    devices: devices.map((device) => device.display_name),
    checklist: uniqueText([
      ...model.safety_checklist.items.map(
        (item) => `${item.label}: ${toStatusLabel(item.status)}`,
      ),
      `${model.safety_checklist.arm_gate.label}: ${toStatusLabel(
        model.safety_checklist.arm_gate.state,
      )}`,
      ...model.safety_checklist.safety_lines,
      ...model.live_kit_capture_workbench.safety_lines,
      ...model.live_kit_package_audition.safety_lines,
      ...liveKitOperatorPackageForModel(model).safety_lines,
      ...model.safety_lines,
    ]),
  };
}

function packageBlockedActionsForModel(
  model: LiveGuiPerformanceConsoleModelDict,
): ReadonlyArray<string> {
  return uniqueText([
    ...model.blocked_actions,
    ...model.device_inventory.blocked_actions,
    ...model.rytm_pad_surface.blocked_actions,
    ...model.rytm_lane_policy_matrix.blocked_actions,
    ...model.performance_flow.blocked_actions,
    ...model.performance_flow.analog_four_set_plan.blocked_active_actions,
    ...model.macro_action_deck.blocked_actions,
    ...model.rehearsal_board.blocked_actions,
    ...model.controller_brain_panel.blocked_actions,
    ...model.live_kit_capture_panel.blocked_actions,
    ...model.live_kit_capture_workbench.blocked_actions,
    ...model.live_kit_capture_workbench.package_manifest.blocked_actions,
    ...model.live_kit_package_audition.blocked_actions,
    ...liveKitOperatorPackageForModel(model).blocked_actions,
    ...model.analog_four_review_surface.blocked_actions,
    ...model.analyzer_panel.blocked_actions,
    ...model.snapshot_history.blocked_actions,
    ...model.command_queue.blocked_actions,
    ...model.safety_checklist.blocked_actions,
  ]);
}

function packageRecoveryNotesForModel(
  model: LiveGuiPerformanceConsoleModelDict,
  currentMove: StyleCrateRehearsalQueueCardDict | undefined,
  localHandoffLines: ReadonlyArray<string>,
): ReadonlyArray<string> {
  return uniqueText([
    'use Z + send from the armed snapshot shell',
    ...(currentMove === undefined ? [] : [`queue recovery: ${currentMove.recovery_action}`]),
    ...model.analog_four_review_surface.recovery_notes,
    ...model.rehearsal_board.recovery_checks,
    ...model.live_kit_capture_panel.recovery_commands,
    ...model.live_kit_capture_workbench.recovery_gates.map((gate) => gate.operator_sequence),
    ...model.live_kit_package_audition.audition_slots.map((slot) => slot.recovery_command),
    ...model.live_kit_package_audition.audition_queue.map((queueItem) => queueItem.recovery_command),
    ...liveKitOperatorPackageForModel(model).recovery_requirements.map(
      (requirement) => requirement.command,
    ),
    ...localHandoffLines,
  ]);
}

function operatorPackageStepBySlot(
  model: LiveGuiPerformanceConsoleModelDict,
  slotKey: string | null,
): LiveGuiPerformanceConsoleLiveKitOperatorPackageStepDict | undefined {
  if (slotKey === null) {
    return undefined;
  }
  return liveKitOperatorPackageForModel(model).operator_steps.find(
    (step) => step.slot_key === slotKey,
  );
}

function operatorPackageBindingBySlot(
  model: LiveGuiPerformanceConsoleModelDict,
  slotKey: string | null,
): LiveGuiPerformanceConsoleLiveKitOperatorPackageSlotBindingDict | undefined {
  if (slotKey === null) {
    return undefined;
  }
  return liveKitOperatorPackageForModel(model).slot_bindings.find(
    (binding) => binding.slot_key === slotKey,
  );
}

function operatorPackageExportKeysByStep(
  model: LiveGuiPerformanceConsoleModelDict,
  operatorPackage: LiveGuiPerformanceConsoleLiveKitOperatorPackageDict,
): Record<string, string> {
  const packageExportKeys: Record<string, string> = {};
  for (const step of operatorPackage.operator_steps) {
    const binding = operatorPackageBindingBySlot(model, step.slot_key);
    packageExportKeys[step.step_key] =
      binding?.package_export_key ?? `operator-package-${step.slot_key}`;
  }
  return packageExportKeys;
}

function operatorPackageApplyPreviewSummaryText(
  summary: OperatorPackageApplyPreview['dry_run_summary'],
): string {
  return [
    summary.apply_policy,
    `would apply ${summary.would_apply_steps} steps`,
    `open MIDI port ${String(summary.would_open_midi_port)}`,
    `send MIDI ${String(summary.would_send_midi)}`,
    `write files ${String(summary.would_write_files)}`,
    `mutate snapshot ${String(summary.would_mutate_snapshot)}`,
    `events emitted ${String(summary.events_emitted)}`,
  ].join(' / ');
}

function operatorPackageMockApplySummaryText(
  summary: OperatorPackageMockApply['dry_run_summary'],
): string {
  return [
    summary.apply_policy,
    `mock applied ${summary.mock_applied_steps} steps`,
    `open MIDI port ${String(summary.opened_midi_port)}`,
    `send MIDI ${String(summary.sent_midi)}`,
    `write files ${String(summary.writes_files)}`,
    `mutate snapshot ${String(summary.mutated_snapshot)}`,
    `apply send plan ${String(summary.applied_send_plan)}`,
    `events emitted ${String(summary.events_emitted)}`,
  ].join(' / ');
}

function operatorPackageApplyPreviewReadinessEvidence(
  check:
    | OperatorPackageApplyPreview['readiness_checks'][number]
    | OperatorPackageMockApply['readiness_checks'][number],
): string {
  const evidence: string[] = [];
  if (check.required !== undefined) {
    evidence.push(`required ${String(check.required)}`);
  }
  if (check.operator_package_id !== undefined) {
    evidence.push(`operator package ${check.operator_package_id}`);
  }
  if (check.step_count !== undefined) {
    evidence.push(`step count ${check.step_count}`);
  }
  if (check.binding_count !== undefined) {
    evidence.push(`binding count ${check.binding_count}`);
  }
  return evidence.length === 0 ? 'no extra evidence' : evidence.join(' / ');
}

function operatorPackageReceiptSummaryText(
  summary: OperatorPackageReceipt['audit_summary'],
): string {
  return [
    summary.receipt_policy,
    `recorded ${summary.recorded_steps} steps`,
    `records apply preview ${String(summary.records_apply_preview)}`,
    `open MIDI port ${String(summary.would_open_midi_port)}`,
    `send MIDI ${String(summary.would_send_midi)}`,
    `write files ${String(summary.would_write_files)}`,
    `mutate snapshot ${String(summary.would_mutate_snapshot)}`,
    `apply send plan ${String(summary.would_apply_send_plan)}`,
    `events emitted ${String(summary.events_emitted)}`,
  ].join(' / ');
}

function operatorPackageReceiptReadinessEvidence(
  check: OperatorPackageReceipt['readiness_checks'][number],
): string {
  const evidence = operatorPackageApplyPreviewReadinessEvidence(check);
  const receiptEvidence: string[] = [];
  if (check.writes_files !== undefined) {
    receiptEvidence.push(`writes files ${String(check.writes_files)}`);
  }
  if (check.events_emitted !== undefined) {
    receiptEvidence.push(`events emitted ${String(check.events_emitted)}`);
  }
  if (receiptEvidence.length === 0) {
    return evidence;
  }
  return evidence === 'no extra evidence'
    ? receiptEvidence.join(' / ')
    : `${evidence} / ${receiptEvidence.join(' / ')}`;
}

function operatorPackageAuditionSource(
  model: LiveGuiPerformanceConsoleModelDict,
  slotKey: string | null,
): LocalRehearsalPackageAuditionSource | undefined {
  if (slotKey === null) {
    return undefined;
  }
  const slot = model.live_kit_package_audition.audition_slots.find(
    (candidate) => candidate.slot_key === slotKey,
  );
  const binding = operatorPackageBindingBySlot(model, slotKey);
  if (slot === undefined || binding === undefined) {
    return undefined;
  }
  const operatorPackage = liveKitOperatorPackageForModel(model);
  return {
    sourceAuditionId: operatorPackage.source_audition_id,
    sourceWorkbenchId: operatorPackage.source_workbench_id,
    slotKey: slot.slot_key,
    slotLabel: slot.label,
    styleCrate: slot.style_crate,
    journalSeed: binding.journal_seed,
    recoveryCommand: slot.recovery_command,
  };
}

function operatorPackageExportEvidence(
  model: LiveGuiPerformanceConsoleModelDict,
  slotKey: string | null,
): LocalRehearsalPackageOperatorPackage | undefined {
  const step = operatorPackageStepBySlot(model, slotKey);
  const binding = operatorPackageBindingBySlot(model, slotKey);
  if (step === undefined || binding === undefined) {
    return undefined;
  }
  return {
    operatorPackageId: liveKitOperatorPackageForModel(model).operator_package_id,
    packageExportKey: binding.package_export_key,
    cockpitBinding: step.cockpit_binding,
    localAction: step.local_action,
    stageTarget: step.stage_target,
    safetyStatus: step.safety_status,
  };
}

function buildLocalRehearsalPackage({
  model,
  packetSource,
  localRehearsalSnapshot,
  selectedCrate,
  currentQueueMove,
  selectedSnapshotIdLabel,
  currentSetPlanStep,
  localSetPlanEntries,
  localJournalEntries,
  sortedDevices,
  localHandoffLines,
  selectedOperatorPackageSlotKey,
}: {
  readonly model: LiveGuiPerformanceConsoleModelDict;
  readonly packetSource: string;
  readonly localRehearsalSnapshot: LocalRehearsalSnapshot;
  readonly selectedCrate: StyleCrateRehearsalCrateCardDict | undefined;
  readonly currentQueueMove: StyleCrateRehearsalQueueCardDict | undefined;
  readonly selectedSnapshotIdLabel: string;
  readonly currentSetPlanStep: LocalSetPlanEntry | null;
  readonly localSetPlanEntries: ReadonlyArray<LocalSetPlanEntry>;
  readonly localJournalEntries: ReadonlyArray<LocalJournalEntry>;
  readonly sortedDevices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>;
  readonly localHandoffLines: ReadonlyArray<string>;
  readonly selectedOperatorPackageSlotKey: string | null;
}): LocalRehearsalPackage {
  return {
    kind: LOCAL_REHEARSAL_PACKAGE_KIND,
    version: LOCAL_REHEARSAL_PACKAGE_VERSION,
    manifest: {
      sessionLabel: model.session_label,
      packetSource,
      selectedCrateName: selectedCrate?.crate_name ?? 'none',
      selectedMoveName: currentQueueMove?.move_name ?? 'none',
      selectedSnapshotId: selectedSnapshotIdLabel,
      queuedStepCount: localSetPlanEntries.length,
      currentStepId: currentSetPlanStep?.id ?? null,
      journalTakeCount: localJournalEntries.length,
      hardwareMode: model.hardware_mode,
    },
    compatibility: packageCompatibilityForSnapshot(model, localRehearsalSnapshot),
    safety: packageSafetyForModel(model, sortedDevices),
    auditionSource: operatorPackageAuditionSource(model, selectedOperatorPackageSlotKey),
    operatorPackage: operatorPackageExportEvidence(model, selectedOperatorPackageSlotKey),
    blockedActions: packageBlockedActionsForModel(model),
    recoveryNotes: packageRecoveryNotesForModel(model, currentQueueMove, localHandoffLines),
    rehearsal: localRehearsalSnapshot,
  };
}

function packageWithCurrentCompatibility(
  model: LiveGuiPerformanceConsoleModelDict,
  rehearsalPackage: LocalRehearsalPackage,
): LocalRehearsalPackage {
  return {
    ...rehearsalPackage,
    compatibility: packageCompatibilityForSnapshot(model, rehearsalPackage.rehearsal),
  };
}

function compatibilityStatusFor(
  compatibility: LocalRehearsalPackageCompatibility,
  needle: string,
): string {
  return compatibility.checks.some((entry) => entry.includes(needle) && entry.includes('missing'))
    ? 'missing'
    : 'match';
}

function comparisonStatus(packageValue: string, currentValue: string): string {
  return packageValue === currentValue ? 'match' : 'changed';
}

function currentReferenceValue(
  status: string,
  fallbackLabel: string,
  referenceLabel: string,
): string {
  if (status === 'missing') {
    return referenceLabel;
  }
  return fallbackLabel;
}

function countLabel(values: ReadonlyArray<string>): string {
  return String(values.length);
}

function localPackageReviewForCurrentPacket({
  model,
  localPackage,
  selectedCrate,
  currentQueueMove,
  selectedSnapshotIdLabel,
  currentDepth,
  currentSetPlanStep,
  localSetPlanEntries,
  localJournalEntries,
  localHandoffLines,
}: {
  readonly model: LiveGuiPerformanceConsoleModelDict;
  readonly localPackage: LocalRehearsalPackage | null;
  readonly selectedCrate: StyleCrateRehearsalCrateCardDict | undefined;
  readonly currentQueueMove: StyleCrateRehearsalQueueCardDict | undefined;
  readonly selectedSnapshotIdLabel: string;
  readonly currentDepth: number;
  readonly currentSetPlanStep: LocalSetPlanEntry | null;
  readonly localSetPlanEntries: ReadonlyArray<LocalSetPlanEntry>;
  readonly localJournalEntries: ReadonlyArray<LocalJournalEntry>;
  readonly localHandoffLines: ReadonlyArray<string>;
}): LocalRehearsalPackageReview | null {
  if (localPackage === null) {
    return null;
  }
  const crateStatus = compatibilityStatusFor(localPackage.compatibility, 'selected crate');
  const queueStatus = compatibilityStatusFor(localPackage.compatibility, 'selected queued move');
  const snapshotStatus = compatibilityStatusFor(localPackage.compatibility, 'selected snapshot');
  const operatorPackageSlotStatus = compatibilityStatusFor(
    localPackage.compatibility,
    'operator package slot',
  );
  const operatorPackageSlotKey = localPackage.rehearsal.selectedOperatorPackageSlotKey;
  const currentOperatorPackageSlot =
    operatorPackageSlotKey !== null &&
    operatorPackageStepBySlot(model, operatorPackageSlotKey) !== undefined &&
    operatorPackageBindingBySlot(model, operatorPackageSlotKey) !== undefined
      ? operatorPackageSlotKey
      : 'none';
  const currentBlockedActions = packageBlockedActionsForModel(model);
  const currentRecoveryNotes = packageRecoveryNotesForModel(
    model,
    currentQueueMove,
    localHandoffLines,
  );
  const rows: ReadonlyArray<LocalRehearsalPackageReviewRow> = [
    {
      label: 'Crate',
      packageValue: localPackage.manifest.selectedCrateName,
      currentValue: currentReferenceValue(
        crateStatus,
        selectedCrate?.crate_name ?? 'none',
        localPackage.rehearsal.selectedCrateKey ?? 'none',
      ),
      status: crateStatus,
    },
    {
      label: 'Queued move',
      packageValue: localPackage.manifest.selectedMoveName,
      currentValue: currentReferenceValue(
        queueStatus,
        currentQueueMove?.move_name ?? 'none',
        localPackage.rehearsal.selectedQueueKey ?? 'none',
      ),
      status: queueStatus,
    },
    {
      label: 'Snapshot',
      packageValue: localPackage.manifest.selectedSnapshotId,
      currentValue: currentReferenceValue(
        snapshotStatus,
        selectedSnapshotIdLabel,
        localPackage.rehearsal.selectedSnapshotId ?? 'none',
      ),
      status: snapshotStatus,
    },
    {
      label: 'Depth',
      packageValue: `${localPackage.rehearsal.previewDepth ?? 0}%`,
      currentValue: `${currentDepth}%`,
      status: comparisonStatus(`${localPackage.rehearsal.previewDepth ?? 0}%`, `${currentDepth}%`),
    },
    {
      label: 'Operator package slot',
      packageValue: operatorPackageSlotKey ?? 'none',
      currentValue: currentReferenceValue(
        operatorPackageSlotStatus,
        currentOperatorPackageSlot,
        operatorPackageSlotKey ?? 'none',
      ),
      status: operatorPackageSlotStatus,
    },
    {
      label: 'Current step',
      packageValue: localPackage.manifest.currentStepId ?? 'none',
      currentValue: currentSetPlanStep?.id ?? 'none',
      status: comparisonStatus(
        localPackage.manifest.currentStepId ?? 'none',
        currentSetPlanStep?.id ?? 'none',
      ),
    },
    {
      label: 'Queued steps',
      packageValue: String(localPackage.manifest.queuedStepCount),
      currentValue: String(localSetPlanEntries.length),
      status: comparisonStatus(
        String(localPackage.manifest.queuedStepCount),
        String(localSetPlanEntries.length),
      ),
    },
    {
      label: 'Journal takes',
      packageValue: String(localPackage.manifest.journalTakeCount),
      currentValue: String(localJournalEntries.length),
      status: comparisonStatus(
        String(localPackage.manifest.journalTakeCount),
        String(localJournalEntries.length),
      ),
    },
    {
      label: 'Blocked actions',
      packageValue: countLabel(localPackage.blockedActions),
      currentValue: countLabel(currentBlockedActions),
      status: comparisonStatus(
        countLabel(localPackage.blockedActions),
        countLabel(currentBlockedActions),
      ),
    },
    {
      label: 'Recovery notes',
      packageValue: countLabel(localPackage.recoveryNotes),
      currentValue: countLabel(currentRecoveryNotes),
      status: comparisonStatus(
        countLabel(localPackage.recoveryNotes),
        countLabel(currentRecoveryNotes),
      ),
    },
  ];
  const status =
    localPackage.compatibility.status === 'needs review' ||
    rows.some((row) => row.status === 'missing')
      ? 'needs review'
      : 'compatible';
  return {
    status,
    summary:
      status === 'compatible'
        ? 'Package can be rehearsed with the current cockpit packet.'
        : 'Package needs operator review before reuse.',
    rows,
  };
}

function localPackageReviewDetail(review: LocalRehearsalPackageReview): string {
  const rowEvidence = review.rows
    .map(
      (row) =>
        `${row.label}: package ${row.packageValue}; current ${row.currentValue}; status ${row.status}`,
    )
    .join(' | ');
  return `${review.summary} ${rowEvidence}`;
}

function localStorageHandle(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function readLocalRehearsalSnapshot(): LocalRehearsalSnapshot | null {
  const storage = localStorageHandle();
  if (storage === null) {
    return null;
  }
  const stored = storage.getItem(LOCAL_REHEARSAL_STORAGE_KEY);
  if (stored === null) {
    return null;
  }
  try {
    return localRehearsalSnapshotFromUnknown(JSON.parse(stored));
  } catch {
    return null;
  }
}

function writeLocalRehearsalSnapshot(snapshot: LocalRehearsalSnapshot): void {
  const storage = localStorageHandle();
  if (storage !== null) {
    storage.setItem(LOCAL_REHEARSAL_STORAGE_KEY, JSON.stringify(snapshot));
  }
}

function removeLocalRehearsalSnapshot(): void {
  const storage = localStorageHandle();
  if (storage !== null) {
    storage.removeItem(LOCAL_REHEARSAL_STORAGE_KEY);
  }
}


function formatLanePolicies(lanes: Readonly<Record<string, string>>): string {
  const entries = Object.entries(lanes).sort(([left], [right]) => left.localeCompare(right));
  return entries.map(([key, value]) => `${key}=${value}`).join(', ') || 'default lanes';
}

function formatSectionAllowlists(
  allowlists: Readonly<Record<string, ReadonlyArray<string>>>,
): string {
  const entries = Object.entries(allowlists).sort(([left], [right]) => left.localeCompare(right));
  return (
    entries
      .map(([section, families]) => `${section}: ${[...families].sort().join(', ')}`)
      .join(' / ') || 'all allowed families'
  );
}

export function PerformanceConsole({
  model,
  packetSource = 'passive packet',
  onRehearseOperatorPackageStep,
  onRehearseOperatorPackageSequence,
  onPreviewOperatorPackageApply,
  onMockApplyOperatorPackage,
  onBuildOperatorPackageReceipt,
}: PerformanceConsoleProps): JSX.Element {
  const initialLocalRehearsal = useMemo(() => readLocalRehearsalSnapshot(), []);
  const [selectedCrateKey, setSelectedCrateKey] = useState<string | null>(
    initialLocalRehearsal?.selectedCrateKey ?? null,
  );
  const [selectedQueueKey, setSelectedQueueKey] = useState<string | null>(
    initialLocalRehearsal?.selectedQueueKey ?? null,
  );
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(
    initialLocalRehearsal?.selectedSnapshotId ?? null,
  );
  const [selectedOperatorPackageSlotKey, setSelectedOperatorPackageSlotKey] = useState<
    string | null
  >(initialLocalRehearsal?.selectedOperatorPackageSlotKey ?? null);
  const [previewDepth, setPreviewDepth] = useState<number | null>(
    initialLocalRehearsal?.previewDepth ?? null,
  );
  const [lastDryRunSummary, setLastDryRunSummary] = useState<string>(
    initialLocalRehearsal?.lastDryRunSummary ?? 'No local dry-run performed.',
  );
  const [localJournalEntries, setLocalJournalEntries] = useState<ReadonlyArray<LocalJournalEntry>>(
    initialLocalRehearsal?.localJournalEntries ?? [],
  );
  const [localSetPlanEntries, setLocalSetPlanEntries] = useState<ReadonlyArray<LocalSetPlanEntry>>(
    initialLocalRehearsal?.localSetPlanEntries ?? [],
  );
  const [currentSetPlanStep, setCurrentSetPlanStep] = useState<LocalSetPlanEntry | null>(
    initialLocalRehearsal?.currentSetPlanStep ?? null,
  );
  const [localOperatorEvents, setLocalOperatorEvents] = useState<ReadonlyArray<LocalOperatorEvent>>(
    initialLocalRehearsal?.localOperatorEvents ?? [],
  );
  const [localAutosaveEnabled, setLocalAutosaveEnabled] = useState<boolean>(
    initialLocalRehearsal?.localAutosaveEnabled ?? true,
  );
  const [localPersistenceSummary, setLocalPersistenceSummary] = useState<string>(
    initialLocalRehearsal === null
      ? 'Local auto-save on. No saved local rehearsal loaded.'
      : 'Local auto-save on. Restored saved local rehearsal.',
  );
  const [localExportPayload, setLocalExportPayload] = useState<string>('');
  const [localImportPayload, setLocalImportPayload] = useState<string>('');
  const [localPackage, setLocalPackage] = useState<LocalRehearsalPackage | null>(null);
  const [localPackagePayload, setLocalPackagePayload] = useState<string>('');
  const [operatorPackageApplyPreview, setOperatorPackageApplyPreview] =
    useState<OperatorPackageApplyPreview | null>(null);
  const [operatorPackageMockApply, setOperatorPackageMockApply] =
    useState<OperatorPackageMockApply | null>(null);
  const [operatorPackageReceipt, setOperatorPackageReceipt] =
    useState<OperatorPackageReceipt | null>(null);
  const nextLocalSetPlanIndex = useRef<number>(initialLocalRehearsal?.nextLocalSetPlanIndex ?? 0);
  const [lastSetPlanAction, setLastSetPlanAction] = useState<string>(
    initialLocalRehearsal?.lastSetPlanAction ?? 'No local set-plan action yet.',
  );
  const a4SetPlan = model.performance_flow.analog_four_set_plan;
  const a4ReviewSurface = model.analog_four_review_surface;
  const a4ReviewFocus = a4ReviewSurface.review_focus;
  const liveKitOperatorPackage = liveKitOperatorPackageForModel(model);
  const operatorPackageReviewLedger = operatorPackageReviewLedgerForModel(model);
  const macroPath = [a4SetPlan.current_macro, ...a4SetPlan.up_next_macros].join(' -> ');
  const sortedDevices = useMemo(
    () => orderedDevices(model.device_inventory.cards),
    [model.device_inventory.cards],
  );
  const sortedPads = useMemo(() => orderedPads(model.rytm_pad_surface.cards), [model.rytm_pad_surface.cards]);
  const sortedMacros = useMemo(
    () => orderedMacroActions(model.macro_action_deck.cards),
    [model.macro_action_deck.cards],
  );
  const sortedRytmPolicies = useMemo(
    () => orderedRytmMacroPolicies(model.rytm_lane_policy_matrix.macro_rows),
    [model.rytm_lane_policy_matrix.macro_rows],
  );
  const sortedQueue = useMemo(
    () => [...model.style_queue.queue_cards].sort((left, right) => left.order - right.order),
    [model.style_queue.queue_cards],
  );
  const currentQueueMove =
    sortedQueue.find((move) => move.queue_key === selectedQueueKey) ?? sortedQueue[0];
  const currentSnapshot =
    model.snapshot_history.entries.find((entry) => entry.snapshot_id === selectedSnapshotId) ??
    model.snapshot_history.entries.find((entry) => entry.snapshot_id === model.snapshot_history.current_id) ??
    model.snapshot_history.entries[0];
  const selectedCrate =
    model.style_queue.crate_cards.find(
      (crate) => selectedCrateKey !== null && sameReferenceKey(crate.crate_key, selectedCrateKey),
    ) ??
    model.style_queue.crate_cards.find((crate) => crate.crate_key === currentQueueMove?.crate_key) ??
    model.style_queue.crate_cards[0];
  const currentMacro =
    sortedMacros.find((card) => card.macro_key === model.macro_action_deck.current_macro_key) ??
    sortedMacros[0];
  const currentDepth = previewDepth ?? currentQueueMove?.mutation_amount_percent ?? 0;
  const mutationPadCount = currentMacro?.affected_pads.length ?? 0;
  const analogFourDevice = sortedDevices.find((device) => device.device_id === ANALOG_FOUR_DEVICE_ID);
  const rytmDevice = sortedDevices.find((device) => device.device_id === RYTM_DEVICE_ID);
  const currentSceneLabel = snapshotSceneLabel(currentSnapshot);
  const currentSnapshotLabel = snapshotIdentityLabel(currentSnapshot);
  const portState = portSummary(sortedDevices, model);
  const mutationProfileLabels = profileLabels(model, currentQueueMove, currentMacro);
  const synthTrackCount = analogFourDevice?.track_count ?? companionTrackCount(sortedDevices);
  const previewParameters = RYTM_PARAMETER_GROUPS[0]!.params.slice(
    0,
    SNAPSHOT_DECK_PREVIEW_PARAMETER_COUNT,
  );
  const queuedCommand = model.command_queue.queued_commands[0];
  const selectedSnapshotIdLabel = currentSnapshot?.snapshot_id ?? 'none';
  const localSetPlanSummary = localSetPlanStatusSummary(
    currentSetPlanStep,
    localSetPlanEntries,
    lastSetPlanAction,
  );
  const nextLocalSetPlanStep = localSetPlanEntries[0];
  const localHandoffLines = useMemo(
    () => [
      localSetPlanHandoffLine('Current', currentSetPlanStep),
      localSetPlanHandoffLine('Next', nextLocalSetPlanStep),
      localOperatorRecentLine(localOperatorEvents),
      'Recovery: use Z + send from the armed snapshot shell.',
      'Local handoff only: no WebSocket command, sidecar action, MIDI port, arm, or send.',
    ],
    [currentSetPlanStep, nextLocalSetPlanStep, localOperatorEvents],
  );
  const localRehearsalSnapshot = useMemo<LocalRehearsalSnapshot>(
    () => ({
      version: LOCAL_REHEARSAL_STORAGE_VERSION,
      selectedCrateKey,
      selectedQueueKey,
      selectedSnapshotId,
      selectedOperatorPackageSlotKey,
      previewDepth,
      lastDryRunSummary,
      localJournalEntries,
      localSetPlanEntries,
      currentSetPlanStep,
      localOperatorEvents,
      lastSetPlanAction,
      nextLocalSetPlanIndex: nextLocalSetPlanIndex.current,
      localAutosaveEnabled,
    }),
    [
      selectedCrateKey,
      selectedQueueKey,
      selectedSnapshotId,
      selectedOperatorPackageSlotKey,
      previewDepth,
      lastDryRunSummary,
      localJournalEntries,
      localSetPlanEntries,
      currentSetPlanStep,
      localOperatorEvents,
      lastSetPlanAction,
      localAutosaveEnabled,
    ],
  );
  const localPackageReview = useMemo(
    () =>
      localPackageReviewForCurrentPacket({
        model,
        localPackage,
        selectedCrate,
        currentQueueMove,
        selectedSnapshotIdLabel,
        currentDepth,
        currentSetPlanStep,
        localSetPlanEntries,
        localJournalEntries,
        localHandoffLines,
      }),
    [
      model,
      localPackage,
      selectedCrate,
      currentQueueMove,
      selectedSnapshotIdLabel,
      currentDepth,
      currentSetPlanStep,
      localSetPlanEntries,
      localJournalEntries,
      localHandoffLines,
    ],
  );
  const visiblePackageReview = localPackageReview as LocalRehearsalPackageReview;

  useEffect(() => {
    if (localAutosaveEnabled) {
      writeLocalRehearsalSnapshot(localRehearsalSnapshot);
    }
  }, [localAutosaveEnabled, localRehearsalSnapshot]);

  const appendLocalOperatorEvent = (label: string, detail: string): void => {
    setLocalOperatorEvents((events) => [
      ...events,
      {
        id: localOperatorEventId(events.length),
        label,
        detail,
        status: 'Local only',
      },
    ]);
  };

  const toggleLocalAutosave = (enabled: boolean): void => {
    setLocalAutosaveEnabled(enabled);
    setLocalPersistenceSummary(
      enabled
        ? 'Local auto-save on. Local rehearsal changes are saved in this browser.'
        : 'Local auto-save off. Local rehearsal changes stay in memory only.',
    );
    appendLocalOperatorEvent(
      enabled ? 'Enabled local auto-save' : 'Disabled local auto-save',
      'Browser-local persistence only; no sidecar or MIDI action.',
    );
  };

  const applyLocalRehearsalSnapshot = (
    importedSnapshot: LocalRehearsalSnapshot,
    eventLabel: string,
    eventDetail: string,
  ): void => {
    setSelectedCrateKey(importedSnapshot.selectedCrateKey);
    setSelectedQueueKey(importedSnapshot.selectedQueueKey);
    setSelectedSnapshotId(importedSnapshot.selectedSnapshotId);
    setSelectedOperatorPackageSlotKey(importedSnapshot.selectedOperatorPackageSlotKey);
    setPreviewDepth(importedSnapshot.previewDepth);
    setLastDryRunSummary(importedSnapshot.lastDryRunSummary);
    setLocalJournalEntries(importedSnapshot.localJournalEntries);
    setLocalSetPlanEntries(importedSnapshot.localSetPlanEntries);
    setCurrentSetPlanStep(importedSnapshot.currentSetPlanStep);
    setLastSetPlanAction(importedSnapshot.lastSetPlanAction);
    setLocalAutosaveEnabled(importedSnapshot.localAutosaveEnabled);
    nextLocalSetPlanIndex.current = importedSnapshot.nextLocalSetPlanIndex;
    setLocalOperatorEvents([
      ...importedSnapshot.localOperatorEvents,
      {
        id: localOperatorEventId(importedSnapshot.localOperatorEvents.length),
        label: eventLabel,
        detail: eventDetail,
        status: 'Local only',
      },
    ]);
  };

  const exportLocalRehearsalJson = (): void => {
    const payload = JSON.stringify(localRehearsalSnapshot, null, 2);
    setLocalExportPayload(payload);
    setLocalPersistenceSummary('Exported local rehearsal JSON. Local only; no MIDI sent.');
    appendLocalOperatorEvent(
      'Exported local rehearsal JSON',
      `${localJournalEntries.length} journal take(s), ${localSetPlanEntries.length} queued step(s).`,
    );
  };

  const exportLocalRehearsalPackage = (): void => {
    const rehearsalPackage = buildLocalRehearsalPackage({
      model,
      packetSource,
      localRehearsalSnapshot,
      selectedCrate,
      currentQueueMove,
      selectedSnapshotIdLabel,
      currentSetPlanStep,
      localSetPlanEntries,
      localJournalEntries,
      sortedDevices,
      localHandoffLines,
      selectedOperatorPackageSlotKey,
    });
    setLocalPackage(rehearsalPackage);
    setLocalPackagePayload(JSON.stringify(rehearsalPackage, null, 2));
    setLocalPersistenceSummary('Exported local rehearsal package. Local only; no MIDI sent.');
    appendLocalOperatorEvent(
      'Exported local rehearsal package',
      `${rehearsalPackage.manifest.sessionLabel} / ${rehearsalPackage.compatibility.status}.`,
    );
  };

  const importLocalRehearsalJson = (): void => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(localImportPayload);
    } catch {
      setLocalPersistenceSummary('Import failed: JSON could not be parsed. Local only; no MIDI sent.');
      appendLocalOperatorEvent('Import failed', 'JSON could not be parsed.');
      return;
    }
    const rehearsalImport = localRehearsalImportFromUnknown(parsed);
    if (rehearsalImport === null) {
      setLocalPersistenceSummary('Import failed: unsupported local rehearsal payload. Local only; no MIDI sent.');
      appendLocalOperatorEvent('Import failed', 'Unsupported local rehearsal payload.');
      return;
    }
    applyLocalRehearsalSnapshot(
      rehearsalImport.snapshot,
      'Imported local rehearsal JSON',
      'Loaded passive browser-local rehearsal state.',
    );
    if (rehearsalImport.rehearsalPackage === null) {
      setLocalPackage(null);
      setLocalPackagePayload('');
    } else {
      const rehearsalPackage = packageWithCurrentCompatibility(
        model,
        rehearsalImport.rehearsalPackage,
      );
      setLocalPackage(rehearsalPackage);
      setLocalPackagePayload(JSON.stringify(rehearsalPackage, null, 2));
    }
    setLocalPersistenceSummary('Imported local rehearsal JSON. Local only; no MIDI sent.');
  };

  const importLocalRehearsalPackage = (): void => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(localImportPayload);
    } catch {
      setLocalPersistenceSummary('Import failed: JSON could not be parsed. Local only; no MIDI sent.');
      appendLocalOperatorEvent('Import failed', 'JSON could not be parsed.');
      return;
    }
    const rehearsalPackage = localRehearsalPackageFromUnknown(parsed);
    if (rehearsalPackage === null) {
      setLocalPersistenceSummary('Import failed: unsupported local rehearsal package. Local only; no MIDI sent.');
      appendLocalOperatorEvent('Import failed', 'Unsupported local rehearsal package.');
      return;
    }
    const compatiblePackage = packageWithCurrentCompatibility(model, rehearsalPackage);
    applyLocalRehearsalSnapshot(
      compatiblePackage.rehearsal,
      'Imported local rehearsal package',
      `${compatiblePackage.manifest.sessionLabel} / ${compatiblePackage.compatibility.status}.`,
    );
    setLocalPackage(compatiblePackage);
    setLocalPackagePayload(JSON.stringify(compatiblePackage, null, 2));
    setLocalPersistenceSummary('Imported local rehearsal package. Local only; no MIDI sent.');
  };

  const stageLocalPackageReview = (review: LocalRehearsalPackageReview): void => {
    setLocalPersistenceSummary(
      `Staged local package review: ${review.status}. Local only; no MIDI sent.`,
    );
    appendLocalOperatorEvent('Staged package review', localPackageReviewDetail(review));
  };

  const clearSavedLocalRehearsal = (): void => {
    removeLocalRehearsalSnapshot();
    setLocalAutosaveEnabled(false);
    setLocalPersistenceSummary('Cleared saved local rehearsal. Local auto-save off; no MIDI sent.');
    appendLocalOperatorEvent(
      'Cleared saved local rehearsal',
      'Removed browser-local rehearsal state only.',
    );
  };

  const selectCrate = (crate: StyleCrateRehearsalCrateCardDict): void => {
    setSelectedCrateKey(crate.crate_key);
  };

  const selectQueueMove = (move: StyleCrateRehearsalQueueCardDict): void => {
    setSelectedQueueKey(move.queue_key);
    setPreviewDepth(clampPreviewDepth(move.mutation_amount_percent));
  };

  const selectSnapshot = (snapshot: LiveGuiSnapshotHistoryEntryDict): void => {
    setSelectedSnapshotId(snapshot.snapshot_id);
  };

  const runLocalDryRun = (): void => {
    const crateName = selectedCrate?.crate_name ?? 'No crate';
    const moveName = currentQueueMove?.move_name ?? 'No queued move';
    const summary = `${crateName} -> ${moveName} at ${currentDepth}% from ${selectedSnapshotIdLabel}`;
    setLastDryRunSummary(
      `Local dry-run: ${summary}. No MIDI port opened; no MIDI sent.`,
    );
    appendLocalOperatorEvent('Ran local dry-run', summary);
  };

  const saveLocalJournalTake = (): void => {
    const crateName = selectedCrate?.crate_name ?? 'No crate';
    const moveName = currentQueueMove?.move_name ?? 'No queued move';
    const snapshotId = selectedSnapshotIdLabel;
    setLocalJournalEntries((entries) => [
      ...entries,
      {
        id: localTakeId(entries.length),
        crateName,
        moveName,
        snapshotId,
        depth: currentDepth,
      },
    ]);
    appendLocalOperatorEvent(
      'Saved local journal take',
      `${moveName} / ${crateName} / ${snapshotId} / ${currentDepth}%`,
    );
  };

  const stageLocalSetPlanEntry = (): void => {
    const nextIndex = nextLocalSetPlanIndex.current;
    nextLocalSetPlanIndex.current = nextIndex + 1;
    const entry: LocalSetPlanEntry = {
      id: localSetPlanId(nextIndex),
      crateName: selectedCrate?.crate_name ?? 'No crate',
      moveName: currentQueueMove?.move_name ?? 'No queued move',
      snapshotId: selectedSnapshotIdLabel,
      depth: currentDepth,
      status: 'Local only',
    };
    setLocalSetPlanEntries((entries) => [...entries, entry]);
    setLastSetPlanAction(`Staged ${entry.id}: ${localSetPlanEntrySummary(entry)}. Local only; no MIDI sent.`);
    appendLocalOperatorEvent(`Staged ${entry.id}`, localSetPlanEntrySummary(entry));
  };

  const stageOperatorPackageStep = (
    step: LiveGuiPerformanceConsoleLiveKitOperatorPackageStepDict,
  ): void => {
    const binding = operatorPackageBindingBySlot(model, step.slot_key);
    const nextIndex = nextLocalSetPlanIndex.current;
    nextLocalSetPlanIndex.current = nextIndex + 1;
    setSelectedOperatorPackageSlotKey(step.slot_key);
    const entry: LocalSetPlanEntry = {
      id: localSetPlanId(nextIndex),
      crateName: 'Live Kit Operator Package',
      moveName: step.label,
      snapshotId: selectedSnapshotIdLabel,
      depth: clampPreviewDepth(binding?.depth_percent ?? currentDepth),
      status: 'Local only',
    };
    setLocalSetPlanEntries((entries) => [...entries, entry]);
    setLastSetPlanAction(
      `Staged operator package ${step.slot_key}: ${localSetPlanEntrySummary(entry)}. Local only; no MIDI sent.`,
    );
    appendLocalOperatorEvent(
      `Staged operator package ${step.slot_key}`,
      `${step.cockpit_binding} / ${step.local_action} / recovery ${step.recovery_command}.`,
    );
    if (onRehearseOperatorPackageStep !== undefined) {
      const command: RehearseOperatorPackageStepCommand = {
        type: 'rehearse_operator_package_step',
        operator_package_id: liveKitOperatorPackage.operator_package_id,
        step_key: step.step_key,
        slot_key: step.slot_key,
        package_export_key: binding?.package_export_key ?? `operator-package-${step.slot_key}`,
        snapshot_id: selectedSnapshotIdLabel,
        depth_percent: clampPreviewDepth(binding?.depth_percent ?? currentDepth),
        mock_safe: true,
      };
      void onRehearseOperatorPackageStep(command)
        .then((ack) => {
          if (ack.ok) {
            const rehearsal = ack.operator_package_rehearsal;
            appendLocalOperatorEvent(
              'Sidecar rehearsal acknowledged',
              rehearsal === undefined
                ? 'Mock-safe operator package rehearsal accepted; no MIDI sent.'
                : `${rehearsal.slot_key} / ${rehearsal.rehearsal_status} / sent MIDI ${String(
                    rehearsal.sent_midi,
                  )}.`,
            );
            return;
          }
          appendLocalOperatorEvent(
            'Sidecar rehearsal rejected',
            ack.message ?? ack.error ?? ack.code ?? 'Operator package rehearsal rejected.',
          );
        })
        .catch((error: unknown) => {
          appendLocalOperatorEvent(
            'Sidecar rehearsal failed',
            error instanceof Error ? error.message : 'Operator package rehearsal failed.',
          );
        });
    }
  };

  const rehearseOperatorPackageSequence = (): void => {
    const stepKeys = liveKitOperatorPackage.operator_steps.map((step) => step.step_key);
    const packageExportKeys = operatorPackageExportKeysByStep(model, liveKitOperatorPackage);
    const command: RehearseOperatorPackageSequenceCommand = {
      type: 'rehearse_operator_package_sequence',
      operator_package_id: liveKitOperatorPackage.operator_package_id,
      step_keys: stepKeys,
      package_export_keys: packageExportKeys,
      snapshot_id: selectedSnapshotIdLabel,
      mock_safe: true,
    };
    const rehearseSequence = onRehearseOperatorPackageSequence as (
      command: RehearseOperatorPackageSequenceCommand,
    ) => Promise<CommandAck>;
    void rehearseSequence(command)
      .then((ack) => {
        if (ack.ok) {
          const rehearsal = ack.operator_package_sequence_rehearsal;
          appendLocalOperatorEvent(
            'Operator package sequence acknowledged',
            rehearsal === undefined
              ? 'Mock-safe operator package sequence accepted; no MIDI sent.'
              : `${rehearsal.step_count} steps / ${rehearsal.rehearsal_status} / sent MIDI ${String(
                  rehearsal.sent_midi,
                )}.`,
          );
          return;
        }
        appendLocalOperatorEvent(
          'Operator package sequence rejected',
          ack.message ?? ack.error ?? ack.code ?? 'Operator package sequence rehearsal rejected.',
        );
      })
      .catch((error: unknown) => {
        appendLocalOperatorEvent(
          'Operator package sequence failed',
          error instanceof Error ? error.message : 'Operator package sequence rehearsal failed.',
        );
      });
  };

  const previewOperatorPackageApply = (): void => {
    const stepKeys = liveKitOperatorPackage.operator_steps.map((step) => step.step_key);
    const packageExportKeys = operatorPackageExportKeysByStep(model, liveKitOperatorPackage);
    const command: PreviewOperatorPackageApplyCommand = {
      type: 'preview_operator_package_apply',
      operator_package_id: liveKitOperatorPackage.operator_package_id,
      step_keys: stepKeys,
      package_export_keys: packageExportKeys,
      snapshot_id: selectedSnapshotIdLabel,
      mock_safe: true,
    };
    const previewApply = onPreviewOperatorPackageApply as (
      command: PreviewOperatorPackageApplyCommand,
    ) => Promise<CommandAck>;
    void previewApply(command)
      .then((ack) => {
        if (ack.ok) {
          const preview = ack.operator_package_apply_preview;
          setOperatorPackageApplyPreview(preview ?? null);
          appendLocalOperatorEvent(
            'Operator package apply preview acknowledged',
            preview === undefined
              ? 'Mock-safe operator package apply preview accepted; no MIDI sent.'
              : `${preview.step_count} steps / ${preview.preview_status} / sent MIDI ${String(
                  preview.sent_midi,
                )} / writes files ${String(preview.writes_files)}.`,
          );
          return;
        }
        setOperatorPackageApplyPreview(null);
        appendLocalOperatorEvent(
          'Operator package apply preview rejected',
          ack.message ?? ack.error ?? ack.code ?? 'Operator package apply preview rejected.',
        );
      })
      .catch((error: unknown) => {
        setOperatorPackageApplyPreview(null);
        appendLocalOperatorEvent(
          'Operator package apply preview failed',
          error instanceof Error ? error.message : 'Operator package apply preview failed.',
        );
      });
  };

  const mockApplyOperatorPackage = (): void => {
    const stepKeys = liveKitOperatorPackage.operator_steps.map((step) => step.step_key);
    const packageExportKeys = operatorPackageExportKeysByStep(model, liveKitOperatorPackage);
    const command: MockApplyOperatorPackageCommand = {
      type: 'mock_apply_operator_package',
      operator_package_id: liveKitOperatorPackage.operator_package_id,
      step_keys: stepKeys,
      package_export_keys: packageExportKeys,
      snapshot_id: selectedSnapshotIdLabel,
      mock_safe: true,
    };
    const mockApply = onMockApplyOperatorPackage as (
      command: MockApplyOperatorPackageCommand,
    ) => Promise<CommandAck>;
    void mockApply(command)
      .then((ack) => {
        if (ack.ok) {
          const mockApplyPayload = ack.operator_package_mock_apply;
          setOperatorPackageMockApply(mockApplyPayload ?? null);
          appendLocalOperatorEvent(
            'Operator package mock apply acknowledged',
            mockApplyPayload === undefined
              ? 'Mock-safe operator package mock apply accepted; no MIDI sent.'
              : `${mockApplyPayload.step_count} steps / ${
                  mockApplyPayload.mock_apply_status
                } / sent MIDI ${String(mockApplyPayload.sent_midi)} / writes files ${String(
                  mockApplyPayload.writes_files,
                )} / applied send plan ${String(mockApplyPayload.applied_send_plan)}.`,
          );
          return;
        }
        setOperatorPackageMockApply(null);
        appendLocalOperatorEvent(
          'Operator package mock apply rejected',
          ack.message ?? ack.error ?? ack.code ?? 'Operator package mock apply rejected.',
        );
      })
      .catch((error: unknown) => {
        setOperatorPackageMockApply(null);
        appendLocalOperatorEvent(
          'Operator package mock apply failed',
          error instanceof Error ? error.message : 'Operator package mock apply failed.',
        );
      });
  };

  const buildOperatorPackageReceipt = (): void => {
    const stepKeys = liveKitOperatorPackage.operator_steps.map((step) => step.step_key);
    const packageExportKeys = operatorPackageExportKeysByStep(model, liveKitOperatorPackage);
    const command: BuildOperatorPackageReceiptCommand = {
      type: 'build_operator_package_receipt',
      operator_package_id: liveKitOperatorPackage.operator_package_id,
      step_keys: stepKeys,
      package_export_keys: packageExportKeys,
      snapshot_id: selectedSnapshotIdLabel,
      mock_safe: true,
    };
    const buildReceipt = onBuildOperatorPackageReceipt as (
      command: BuildOperatorPackageReceiptCommand,
    ) => Promise<CommandAck>;
    void buildReceipt(command)
      .then((ack) => {
        if (ack.ok) {
          const receipt = ack.operator_package_receipt;
          setOperatorPackageReceipt(receipt ?? null);
          appendLocalOperatorEvent(
            'Operator package receipt acknowledged',
            receipt === undefined
              ? 'Mock-safe operator package receipt accepted; no MIDI sent.'
              : `${receipt.step_count} steps / ${receipt.receipt_status} / sent MIDI ${String(
                  receipt.sent_midi,
                )} / writes files ${String(receipt.writes_files)}.`,
          );
          return;
        }
        setOperatorPackageReceipt(null);
        appendLocalOperatorEvent(
          'Operator package receipt rejected',
          ack.message ?? ack.error ?? ack.code ?? 'Operator package receipt rejected.',
        );
      })
      .catch((error: unknown) => {
        setOperatorPackageReceipt(null);
        appendLocalOperatorEvent(
          'Operator package receipt failed',
          error instanceof Error ? error.message : 'Operator package receipt failed.',
        );
      });
  };

  const promoteNextLocalSetStep = (): void => {
    const nextEntry = localSetPlanEntries[0];
    if (nextEntry === undefined) {
      setLastSetPlanAction('No local set-plan steps to promote. Local only; no MIDI sent.');
      appendLocalOperatorEvent('Promote skipped', 'No local set-plan steps to promote.');
      return;
    }
    setCurrentSetPlanStep(nextEntry);
    setLocalSetPlanEntries(localSetPlanEntries.slice(1));
    setLastSetPlanAction(
      `Promoted ${nextEntry.id}: ${localSetPlanEntrySummary(nextEntry)}. Local only; no MIDI sent.`,
    );
    appendLocalOperatorEvent(`Promoted ${nextEntry.id}`, localSetPlanEntrySummary(nextEntry));
  };

  const skipNextLocalSetStep = (): void => {
    const nextEntry = localSetPlanEntries[0];
    if (nextEntry === undefined) {
      setLastSetPlanAction('No local set-plan steps to skip. Local only; no MIDI sent.');
      appendLocalOperatorEvent('Skip ignored', 'No local set-plan steps to skip.');
      return;
    }
    setLocalSetPlanEntries(localSetPlanEntries.slice(1));
    setLastSetPlanAction(
      `Skipped ${nextEntry.id}: ${localSetPlanEntrySummary(nextEntry)}. Local only; no MIDI sent.`,
    );
    appendLocalOperatorEvent(`Skipped ${nextEntry.id}`, localSetPlanEntrySummary(nextEntry));
  };

  const clearLocalSetPlan = (): void => {
    const stepCount = localSetPlanEntries.length;
    setLocalSetPlanEntries([]);
    setLastSetPlanAction(`Cleared ${stepCount} local set-plan step(s). Local only; no MIDI sent.`);
    appendLocalOperatorEvent(
      `Cleared ${stepCount} local set-plan step(s)`,
      currentSetPlanStep === null ? 'No current step changed.' : `Current step remains ${currentSetPlanStep.id}.`,
    );
  };

  const completeCurrentLocalSetStep = (): void => {
    const currentEntry = currentSetPlanStep;
    if (currentEntry === null) {
      setLastSetPlanAction('No current local set-plan step to complete. Local only; no MIDI sent.');
      appendLocalOperatorEvent(
        'Complete ignored',
        'No current local set-plan step to complete.',
      );
      return;
    }
    setCurrentSetPlanStep(null);
    setLastSetPlanAction(
      `Completed ${currentEntry.id}: ${localSetPlanEntrySummary(currentEntry)}. Local only; no MIDI sent.`,
    );
    appendLocalOperatorEvent(
      `Completed ${currentEntry.id}`,
      localSetPlanEntrySummary(currentEntry),
    );
  };

  const resetLocalSetPlan = (): void => {
    const currentEntry = currentSetPlanStep;
    const queuedCount = localSetPlanEntries.length;
    setCurrentSetPlanStep(null);
    setLocalSetPlanEntries([]);
    setLastSetPlanAction('Reset local set-plan. Local only; no MIDI sent.');
    appendLocalOperatorEvent(
      'Reset local set-plan',
      currentEntry === null
        ? `Cleared ${queuedCount} queued step(s).`
        : `Cleared current ${currentEntry.id} and ${queuedCount} queued step(s).`,
    );
  };

  return (
    <main
      className="performance-console"
      data-testid="performance-console"
      aria-labelledby="performance-console-title"
    >
      <header className="performance-console-topbar" data-testid="performance-console-topbar">
        <div className="performance-console-brand">
          <span aria-hidden="true" className="performance-console-brand-mark" />
          <h1 id="performance-console-title">RytmRandomizer Cockpit Performance Console</h1>
        </div>
        <div className="performance-console-status" aria-label="Console safety state">
          <span>{model.console_status}</span>
          <span>{model.hardware_mode}</span>
          <span>{packetSource}</span>
        </div>
        <div className="performance-console-topbar-controls" aria-label="Cockpit hardware state">
          <strong>
            {toStatusLabel(model.console_status)} - {portState}
          </strong>
          <span>MIDI Port</span>
          <span>{portState}</span>
          <span>Arm</span>
          <strong>{armSummary(model)}</strong>
          <span>{model.command_queue.queue_status}</span>
          <span>{dryRunSummary(model)}</span>
          <span>{currentSceneLabel}</span>
          <span>{snapshotBpmLabel(currentSnapshot)}</span>
          <button type="button" className="live-readiness-action" disabled>
            Tap Tempo
          </button>
        </div>
      </header>

      <aside className="performance-console-left-rail" data-testid="performance-console-left-rail">
        <section className="performance-console-surface" aria-labelledby="console-device-rail-title">
          <h2 id="console-device-rail-title">Device Rail</h2>
          <div className="performance-console-device-grid">
            {sortedDevices.map((device) => (
              <article
                key={device.device_id}
                className="performance-console-device performance-console-device-rail-card"
                data-testid={`performance-console-device-${device.device_id}`}
              >
                <header>
                  <strong>{device.display_name}</strong>
                  <span>{toStatusLabel(device.hardware_state)}</span>
                </header>
                <small>{device.role_summary}</small>
                <small>
                  {device.track_count} tracks / port {device.port_state} / mock {device.mock_state}
                </small>
                <div className="performance-console-device-chip-grid">
                  {Array.from({ length: device.track_count }, (_, index) => (
                    <span key={`${device.device_id}-${index + 1}`} className="performance-console-device-chip">
                      {deviceTrackLabel(device, index)}
                    </span>
                  ))}
                </div>
                <div className="live-chip-row">
                  {device.capability_badges.map((badge) => (
                    <span key={badge} className="live-chip">
                      {badge}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="performance-console-surface performance-console-readiness-card">
          <h2>Safety / Readiness</h2>
          <div className="performance-console-readiness-meter">
            <strong>{toStatusLabel(model.safety_checklist.checklist_status)}</strong>
            <span>{model.safety_checklist.arm_gate.reason}</span>
          </div>
          <div className="performance-console-list">
            {model.safety_checklist.items.map((item) => (
              <article key={item.key}>
                <strong>{item.label}</strong>
                <span>{item.status}</span>
                <small>{item.message}</small>
              </article>
            ))}
            <article>
              <strong>{model.safety_checklist.arm_gate.label}</strong>
              <span>{model.safety_checklist.arm_gate.state}</span>
              <small>{model.safety_checklist.arm_gate.reason}</small>
            </article>
          </div>
        </section>
      </aside>

      <section
        className="performance-console-snapshot-deck"
        data-testid="performance-console-snapshot-deck"
        aria-labelledby="console-pad-grid-title"
      >
        <header className="performance-console-deck-header">
          <div>
            <p className="panel-meta">SNAPSHOT - ANALOG RYTM MKII</p>
            <h2 id="console-pad-grid-title">Snapshot - Analog Rytm MKII</h2>
          </div>
          <div className="live-chip-row">
            <span className="live-chip">{currentSceneLabel}</span>
            <span className="live-chip">{model.session_label}</span>
            <span className="live-chip">{currentSnapshotLabel}</span>
            <span className="live-chip">{snapshotBpmLabel(currentSnapshot)}</span>
          </div>
        </header>
        <div className="performance-console-pad-grid">
          {sortedPads.map((pad) => (
            <article
              key={pad.pad}
              className={`performance-console-pad ${pad.surface_state}`}
              data-testid={`performance-console-pad-${pad.pad}`}
            >
              <header>
                <span>{pad.pad}</span>
                <small>{pad.track_code}</small>
              </header>
              <strong>{pad.label}</strong>
              <small>
                {pad.track_code} / {pad.default_role} / {pad.default_machine_label}
              </small>
              <div className="performance-console-pad-knobs" aria-label={`Pad ${pad.pad} preview controls`}>
                {previewParameters.map((parameter, index) => (
                  <span key={`${pad.pad}-${parameter.key}`} className={`performance-console-mini-knob knob-${index}`}>
                    <span aria-hidden="true" />
                    <small>{parameter.label}</small>
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
        <section
          className="performance-console-surface performance-console-snapshot-history-panel"
          data-testid="performance-console-snapshot-history"
          aria-labelledby="console-snapshot-history-title"
        >
          <header className="performance-console-section-header">
            <h2 id="console-snapshot-history-title">Snapshot History / Mutation Journal</h2>
            <span>{model.snapshot_history.entry_count} entries</span>
          </header>
          <div className="performance-console-history-rail">
            {model.snapshot_history.entries.map((entry) => (
              <article
                key={entry.key}
                className={entry.snapshot_id === currentSnapshot?.snapshot_id ? 'current' : undefined}
                data-testid={`performance-console-history-${entry.snapshot_id}`}
                role="button"
                tabIndex={0}
                aria-pressed={entry.snapshot_id === currentSnapshot?.snapshot_id}
                aria-label={`Select snapshot ${entry.snapshot_id}`}
                title="Load this snapshot into the local rehearsal preview only."
                onClick={() => {
                  selectSnapshot(entry);
                }}
                onKeyDown={(event) => {
                  if (isKeyboardActivation(event.key)) {
                    event.preventDefault();
                    selectSnapshot(entry);
                  }
                }}
              >
                <strong>{entry.snapshot_id}</strong>
                <span>{entry.label}</span>
                <small>{entry.summary}</small>
              </article>
            ))}
          </div>
        </section>
      </section>

      <section
        className="performance-console-mutation-panel"
        data-testid="performance-console-mutation-panel"
        aria-labelledby="console-mutation-panel-title"
      >
        <header className="performance-console-deck-header">
          <div>
            <p className="panel-meta">MUTATION PANEL</p>
            <h2 id="console-mutation-panel-title">Mutation Panel</h2>
          </div>
          <span className="live-chip">Queue ({sortedQueue.length})</span>
        </header>

        <section
          className="performance-console-surface"
          data-testid="performance-console-style-queue"
          aria-labelledby="console-style-queue-title"
        >
          <header className="performance-console-section-header">
            <h2 id="console-style-queue-title">Style Queue / Journal</h2>
            <span>{model.style_queue.deck_status}</span>
          </header>
          <h3 className="performance-console-subheading">Style Crates</h3>
          <div className="performance-console-list performance-console-crate-list" aria-label="Style crates">
            {model.style_queue.crate_cards.map((crate) => (
              <article
                key={crate.crate_key}
                data-testid={`style-crate-${toTestIdKey(crate.crate_key)}`}
                className={crate.crate_key === selectedCrate?.crate_key ? 'current' : undefined}
              >
                <strong>{crate.crate_name}</strong>
                <span>{crate.summary}</span>
                <small>
                  energy {crate.energy} / risk {crate.risk} / {crate.risk_status} / pads{' '}
                  {crate.target_pads.join(', ')}
                </small>
                <small>
                  primary move {crate.primary_move_name} / {crate.operator_action}
                </small>
                <div className="live-chip-row">
                  {crate.tags.map((tag) => (
                    <span key={`${crate.crate_key}-${tag}`} className="live-chip">
                      {tag}
                    </span>
                  ))}
                </div>
                <button
                  type="button"
                  className="live-readiness-action performance-console-local-control"
                  data-testid={`performance-console-style-crate-select-${toTestIdKey(crate.crate_key)}`}
                  aria-pressed={crate.crate_key === selectedCrate?.crate_key}
                  title="Select this crate in the local rehearsal preview only."
                  onClick={() => {
                    selectCrate(crate);
                  }}
                >
                  Select {crate.crate_name}
                </button>
                <button
                  type="button"
                  className="live-readiness-action"
                  disabled
                  title="Style crate staging remains passive in this console packet."
                >
                  Stage {crate.primary_move_name}
                </button>
              </article>
            ))}
          </div>
          <h3 className="performance-console-subheading">Queued Moves</h3>
          <div className="performance-console-list">
            {sortedQueue.map((move) => (
              <article
                key={move.queue_key}
                className={move.queue_key === currentQueueMove?.queue_key ? 'current' : undefined}
                data-testid={`style-queue-move-${toTestIdKey(move.queue_key)}`}
              >
                <strong>{move.move_name}</strong>
                <span>
                  {move.chapter} / {move.mutation_amount_percent}% / {move.risk_status}
                </span>
                <small>
                  pads {move.target_pads.join(', ')} / {move.operator_action} / recover{' '}
                  {move.recovery_action}
                </small>
                {move.dry_run_only ? (
                  <div className="live-chip-row">
                    <span className="live-chip">dry-run only</span>
                  </div>
                ) : null}
                <button
                  type="button"
                  className="live-readiness-action performance-console-local-control"
                  data-testid={`performance-console-queue-select-${toTestIdKey(move.queue_key)}`}
                  aria-pressed={move.queue_key === currentQueueMove?.queue_key}
                  title="Select this queued move in the local rehearsal preview only."
                  onClick={() => {
                    selectQueueMove(move);
                  }}
                >
                  Select {move.move_name}
                </button>
              </article>
            ))}
          </div>
          <section
            className="performance-console-local-panel"
            data-testid="performance-console-local-preview"
            aria-label="Local rehearsal preview"
          >
            <strong>Local rehearsal preview</strong>
            <span>Selected crate {selectedCrate?.crate_name ?? 'none'}</span>
            <span>Selected move {currentQueueMove?.move_name ?? 'none'}</span>
            <span>Selected snapshot {selectedSnapshotIdLabel}</span>
            <span data-testid="performance-console-depth-value">Depth {currentDepth}%</span>
            <small>Local only: no WebSocket dispatch, no sidecar command, no MIDI port, no MIDI send.</small>
          </section>
          <section
            className="performance-console-local-panel performance-console-local-persistence"
            data-testid="performance-console-local-persistence"
            aria-label="Local rehearsal persistence"
          >
            <strong>Local rehearsal persistence</strong>
            <label className="performance-console-local-toggle">
              <input
                type="checkbox"
                checked={localAutosaveEnabled}
                data-testid="performance-console-local-autosave"
                onChange={(event) => {
                  toggleLocalAutosave(event.currentTarget.checked);
                }}
              />
              <span>Local auto-save</span>
            </label>
            <span data-testid="performance-console-local-persistence-summary">
              {localPersistenceSummary}
            </span>
            <div className="performance-console-local-actions">
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Exports current local rehearsal state as copy-ready JSON only."
                onClick={exportLocalRehearsalJson}
              >
                Export local rehearsal JSON
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Imports copy-ready local rehearsal JSON without dispatching any command."
                onClick={importLocalRehearsalJson}
              >
                Import local rehearsal JSON
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Exports a portable rehearsal package with manifest, compatibility, and safety evidence."
                onClick={exportLocalRehearsalPackage}
              >
                Export local rehearsal package
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Imports a portable rehearsal package without dispatching any command."
                onClick={importLocalRehearsalPackage}
              >
                Import local rehearsal package
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Clears browser-local rehearsal storage only."
                onClick={clearSavedLocalRehearsal}
              >
                Clear saved local rehearsal
              </button>
            </div>
            <label className="performance-console-local-json">
              <span>Import JSON</span>
              <textarea
                data-testid="performance-console-local-import-input"
                value={localImportPayload}
                onChange={(event) => {
                  setLocalImportPayload(event.currentTarget.value);
                }}
              />
            </label>
            {localExportPayload.length === 0 ? null : (
              <pre data-testid="performance-console-local-export-payload">
                {localExportPayload}
              </pre>
            )}
            {localPackage === null ? null : (
              <section
                className="performance-console-local-package"
                data-testid="performance-console-local-package"
                aria-label="Local rehearsal package evidence"
              >
                <strong>Local rehearsal package</strong>
                <div className="performance-console-local-package-grid">
                  <span>{localPackage.compatibility.status}</span>
                  <span>{localPackage.manifest.sessionLabel}</span>
                  <span>{localPackage.manifest.packetSource}</span>
                  <span>{localPackage.manifest.selectedCrateName}</span>
                  <span>{localPackage.manifest.selectedMoveName}</span>
                  <span>{localPackage.manifest.selectedSnapshotId}</span>
                  <span>current {localPackage.manifest.currentStepId ?? 'none'}</span>
                  <span>queued {localPackage.manifest.queuedStepCount}</span>
                  <span>journal {localPackage.manifest.journalTakeCount}</span>
                </div>
                <div className="performance-console-local-package-list">
                  <strong>Compatibility</strong>
                  {localPackage.compatibility.checks.map((check) => (
                    <small key={check}>{check}</small>
                  ))}
                </div>
                <div className="performance-console-local-package-list">
                  <strong>Devices</strong>
                  {localPackage.safety.devices.map((device) => (
                    <small key={device}>{device}</small>
                  ))}
                </div>
                <div className="performance-console-local-package-list">
                  <strong>Safety</strong>
                  {localPackage.safety.checklist.map((item) => (
                    <small key={item}>{item}</small>
                  ))}
                </div>
                {localPackage.auditionSource === undefined ||
                localPackage.operatorPackage === undefined ? null : (
                  <div className="performance-console-local-package-list">
                    <strong>Operator package</strong>
                    <small>{localPackage.operatorPackage.operatorPackageId}</small>
                    <small>{localPackage.auditionSource.slotKey}</small>
                    <small>{localPackage.auditionSource.slotLabel}</small>
                    <small>{localPackage.auditionSource.styleCrate}</small>
                    <small>{localPackage.operatorPackage.packageExportKey}</small>
                    <small>{localPackage.operatorPackage.cockpitBinding}</small>
                    <small>{localPackage.auditionSource.recoveryCommand}</small>
                  </div>
                )}
                <div className="performance-console-local-package-list">
                  <strong>Blocked actions</strong>
                  {localPackage.blockedActions.map((action) => (
                    <small key={action}>{action}</small>
                  ))}
                </div>
                <div className="performance-console-local-package-list">
                  <strong>Recovery</strong>
                  {localPackage.recoveryNotes.map((note) => (
                    <small key={note}>{note}</small>
                  ))}
                </div>
                <section
                  className="performance-console-local-package-review"
                  data-testid="performance-console-local-package-review"
                  aria-label="Local rehearsal package review workbench"
                >
                  <strong>Package review workbench</strong>
                  <span>review status {visiblePackageReview.status}</span>
                  <small>{visiblePackageReview.summary}</small>
                  <div className="performance-console-local-package-review-rows">
                    {visiblePackageReview.rows.map((row) => (
                      <article
                        key={row.label}
                        className={`performance-console-local-package-review-row ${row.status}`}
                      >
                        <strong>{row.label}</strong>
                        <span>package {row.packageValue}</span>
                        <span>current {row.currentValue}</span>
                        <small>{row.status}</small>
                      </article>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="live-readiness-action performance-console-local-control"
                    title="Stages package-review evidence in the local operator log only."
                    onClick={() => {
                      stageLocalPackageReview(visiblePackageReview);
                    }}
                  >
                    Stage package review locally
                  </button>
                </section>
              </section>
            )}
            {localPackagePayload.length === 0 ? null : (
              <pre data-testid="performance-console-local-package-payload">
                {localPackagePayload}
              </pre>
            )}
            <small>
              Browser-local only: import/export does not read hardware, write project files,
              call the sidecar, open MIDI ports, arm hardware, or send MIDI.
            </small>
          </section>
          <h3 className="performance-console-subheading">Mutation Journal</h3>
          <div className="performance-console-list">
            {model.style_queue.journal_cards.map((entry) => (
              <article key={entry.journal_key}>
                <strong>{entry.name}</strong>
                <span>{entry.value_summary.join(', ')}</span>
              </article>
            ))}
          </div>
        </section>

        <section className="performance-console-surface performance-console-depth-panel">
          <header className="performance-console-section-header">
            <h2>Depth</h2>
            <span>{currentDepth}%</span>
          </header>
          <div className="performance-console-depth-track" aria-label="Mutation depth preview">
            <span data-testid="performance-console-depth-fill" style={{ width: `${currentDepth}%` }} />
          </div>
          <label className="performance-console-depth-input">
            <span>Local preview depth</span>
            <input
              type="range"
              aria-label="Local preview depth"
              min={PREVIEW_DEPTH_MIN}
              max={PREVIEW_DEPTH_MAX}
              value={inputDepthValue(currentDepth)}
              data-testid="performance-console-depth-input"
              onChange={(event) => {
                setPreviewDepth(clampPreviewDepth(Number(event.currentTarget.value)));
              }}
            />
          </label>
          <h3 className="performance-console-subheading">Profile</h3>
          <div className="performance-console-profile-row">
            {mutationProfileLabels.map((profile, index) => (
              <span key={profile} className={index === 0 ? 'active' : undefined}>
                {toHumanLabel(profile)}
              </span>
            ))}
          </div>
        </section>

        <section className="performance-console-surface performance-console-mutation-summary">
          <header className="performance-console-section-header">
            <h2>Mutation Summary</h2>
            <span>{model.macro_action_deck.deck_status}</span>
          </header>
          <p>
            {mutationPadCount} drum pads and {synthTrackCount} synth tracks
            represented in the passive console.
          </p>
          <div className="performance-console-radar" aria-label="Mutation summary radar">
            {['energy', 'density', 'chaos', 'space', 'grit', 'motion'].map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
        </section>

        <section className="performance-console-surface">
          <h2>Actions</h2>
          <div className="performance-console-action-grid">
            <button type="button" className="live-readiness-action" disabled>
              {currentQueueMove?.operator_action ?? model.style_queue.deck_status}
            </button>
            <button type="button" className="live-readiness-action" disabled>
              Review {currentMacro?.label ?? model.macro_action_deck.current_macro_key}
            </button>
            <button type="button" className="live-readiness-action live-readiness-action-locked" disabled>
              {queuedCommandButtonLabel(queuedCommand, model.command_queue.queue_status)}
            </button>
            <button type="button" className="live-readiness-action live-readiness-action-locked" disabled>
              {model.safety_checklist.arm_gate.label} {model.safety_checklist.arm_gate.state}
            </button>
          </div>
          <div className="performance-console-local-actions">
            <button
              type="button"
              className="live-readiness-action performance-console-local-control"
              title="Stages the current local rehearsal selection in memory only."
              onClick={stageLocalSetPlanEntry}
            >
              Stage local set-plan step
            </button>
            <button
              type="button"
              className="live-readiness-action performance-console-local-control"
              title="Runs a local-only dry-run summary. No command is dispatched."
              onClick={runLocalDryRun}
            >
              Run local dry-run
            </button>
            <button
              type="button"
              className="live-readiness-action performance-console-local-control"
              title="Saves the current local rehearsal selection in memory only."
              onClick={saveLocalJournalTake}
            >
              Save local journal take
            </button>
          </div>
          <section
            className="performance-console-local-panel"
            data-testid="performance-console-last-dry-run"
            aria-label="Last local dry-run result"
          >
            <strong>Last local dry-run result</strong>
            <span data-testid="performance-console-local-dry-run-summary">{lastDryRunSummary}</span>
          </section>
          <section
            className="performance-console-local-panel"
            data-testid="performance-console-local-journal"
            aria-label="Local mutation journal"
          >
            <strong>Local mutation journal</strong>
            {localJournalEntries.length === 0 ? <span>No local journal takes saved.</span> : null}
            {localJournalEntries.map((entry) => (
              <span key={entry.id} data-testid={`journal-take-${entry.id}`}>
                {entry.id}: {entry.moveName} / {entry.crateName} / {entry.snapshotId} / {entry.depth}%
              </span>
            ))}
          </section>
          <section
            className="performance-console-local-panel performance-console-local-set-plan"
            data-testid="performance-console-local-set-plan"
            aria-label="Local set-plan queue"
          >
            <strong>Local set-plan queue</strong>
            <span data-testid="performance-console-local-set-plan-summary">{localSetPlanSummary}</span>
            <article
              className="performance-console-local-current-step"
              data-testid="performance-console-current-set-plan-step"
            >
              <strong>Current local set-plan step</strong>
              {currentSetPlanStep === null ? (
                <span>No current local set-plan step.</span>
              ) : (
                <>
                  <span>
                    {currentSetPlanStep.id}: {currentSetPlanStep.moveName}
                  </span>
                  <small>
                    {currentSetPlanStep.crateName} / snapshot {currentSetPlanStep.snapshotId} /
                    depth {currentSetPlanStep.depth}% / {currentSetPlanStep.status}
                  </small>
                </>
              )}
            </article>
            {localSetPlanEntries.length === 0 ? <span>No local set-plan steps staged.</span> : null}
            <div className="performance-console-local-set-plan-list">
              {localSetPlanEntries.map((entry, index) => (
                <article key={entry.id} data-testid={`local-set-plan-step-${entry.id}`}>
                  <strong>
                    {entry.id}: {entry.moveName}
                  </strong>
                  <span>{index === 0 ? 'Up next' : `Queued ${index + 1}`}</span>
                  <span>{entry.crateName}</span>
                  <small>
                    snapshot {entry.snapshotId} / depth {entry.depth}% / {entry.status}
                  </small>
                </article>
              ))}
            </div>
            <article
              className="performance-console-local-handoff"
              data-testid="performance-console-local-handoff"
            >
              <strong>Operator handoff</strong>
              {localHandoffLines.map((line) => (
                <span key={line}>{line}</span>
              ))}
            </article>
            <div className="performance-console-local-actions">
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Promotes the next local set-plan step in memory only."
                onClick={promoteNextLocalSetStep}
              >
                Promote next local set-plan step
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Completes the current local set-plan step in memory only."
                onClick={completeCurrentLocalSetStep}
              >
                Complete current local set-plan step
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Skips the next local set-plan step in memory only."
                onClick={skipNextLocalSetStep}
              >
                Skip next local set-plan step
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Clears the local set-plan queue in memory only."
                onClick={clearLocalSetPlan}
              >
                Clear local set-plan
              </button>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Resets the current and queued local set-plan state in memory only."
                onClick={resetLocalSetPlan}
              >
                Reset local set-plan
              </button>
            </div>
            <small>
              Local only: this set plan does not dispatch WebSocket commands, execute sidecar
              actions, open MIDI ports, arm hardware, or send MIDI.
            </small>
          </section>
          <section
            className="performance-console-local-panel performance-console-local-operator-log"
            data-testid="performance-console-local-operator-log"
            aria-label="Local operator activity log"
          >
            <strong>Local operator activity</strong>
            {localOperatorEvents.length === 0 ? (
              <span>No local operator activity recorded.</span>
            ) : null}
            <div className="performance-console-local-operator-log-list">
              {localOperatorEvents.map((event) => (
                <article key={event.id} data-testid={`local-operator-event-${event.id}`}>
                  <strong>{event.label}</strong>
                  <span>{event.status}</span>
                  <small>{event.detail}</small>
                </article>
              ))}
            </div>
          </section>
        </section>

        <section
          className="performance-console-surface"
          data-testid="performance-console-blocked-actions"
          aria-labelledby="console-blocked-actions-title"
        >
          <h2 id="console-blocked-actions-title">Blocked Hardware Actions</h2>
          <div className="live-chip-row">
            {model.blocked_actions.map((action) => (
              <span key={action} className="live-chip live-chip-blocked">
                {action}
              </span>
            ))}
          </div>
          <div className="live-chip-row">
            {model.safety_lines.map((line) => (
              <span key={line} className="live-chip">
                {line}
              </span>
            ))}
          </div>
        </section>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-rytm-lane-policy-matrix"
        aria-labelledby="console-rytm-lane-policy-matrix-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-rytm-lane-policy-matrix-title">Rytm Lane Policy Matrix</h2>
          <span>
            {model.rytm_lane_policy_matrix.matrix_status} /{' '}
            {model.rytm_lane_policy_matrix.macro_count} macros
          </span>
        </header>
        <p className="panel-meta">{model.rytm_lane_policy_matrix.source_report}</p>

        <h3 className="performance-console-subheading">Pad Groups</h3>
        <div className="performance-console-list">
          {model.rytm_lane_policy_matrix.pad_groups.map((group) => (
            <article key={group.group_key} data-testid={`rytm-lane-policy-${group.group_key}`}>
              <strong>{group.group_key}</strong>
              <span>pads {group.pads.join(', ')}</span>
              <small>{group.summary}</small>
              <small>{group.lane_policy}</small>
              <small>{group.operator_note}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Macro Policies</h3>
        <div className="performance-console-list">
          {sortedRytmPolicies.map((row) => (
            <article key={row.macro_key} data-testid={`rytm-macro-policy-${row.macro_key}`}>
              <strong>{row.label}</strong>
              <span>
                {row.macro_key} / {row.style_crate} / {row.risk_label}
              </span>
              <small>pads {row.affected_pads.join(', ')}</small>
              <small>{row.lane_policy_summary}</small>
              <small>recover {row.recovery_action}</small>
              <small>{row.summary}</small>
              {Object.entries(row.pad_policy_cards).map(([pad, policy]) => (
                <small key={`${row.macro_key}-pad-${pad}`}>
                  Pad {pad}: amount {policy.amount ?? 'default'} / density{' '}
                  {policy.density ?? 'default'} / bias {policy.bias ?? 'default'} /{' '}
                  {formatLanePolicies(policy.lane_policies)} /{' '}
                  {formatSectionAllowlists(policy.section_family_allowlists)}
                </small>
              ))}
            </article>
          ))}
        </div>

        <div className="live-chip-row">
          {model.rytm_lane_policy_matrix.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
          {model.rytm_lane_policy_matrix.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Rytm lane policy dispatch remains blocked in this passive console."
          >
            Apply Rytm Lane Policy
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="Real Rytm sends remain in the explicitly armed snapshot shell."
          >
            Send Rytm Policy
          </button>
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-flow"
        aria-labelledby="console-flow-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-flow-title">Performance Flow</h2>
          <span>{model.performance_flow.flow_status}</span>
        </header>
        <div className="performance-console-flow-rail">
          {model.performance_flow.steps.map((step) => (
            <article
              key={step.key}
              className={`performance-console-step ${
                step.key === model.performance_flow.current_step_key ? 'current' : 'next'
              }`}
            >
              <strong>{step.key}</strong>
              <span>{step.label}</span>
              <small>
                Rytm {step.rytm_command} / A4 {step.analog_four_action} / {step.send_policy}
              </small>
            </article>
          ))}
        </div>
        <article className="performance-console-a4-plan">
          <strong>{a4SetPlan.set_name}</strong>
          <span>{macroPath}</span>
          <small>{a4SetPlan.summary}</small>
          <div className="live-chip-row">
            {a4SetPlan.blocked_active_actions.map((action) => (
              <span key={action} className="live-chip live-chip-blocked">
                {action}
              </span>
            ))}
          </div>
        </article>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-a4-review-surface"
        aria-labelledby="console-a4-review-surface-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-a4-review-surface-title">{a4ReviewSurface.title}</h2>
          <span>{a4ReviewSurface.surface_status}</span>
        </header>
        <p className="panel-meta">
          {a4ReviewSurface.set_name} / focus {a4ReviewFocus.macro_name} /{' '}
          {a4ReviewFocus.readiness}
        </p>
        <small>{a4ReviewSurface.preflight_command}</small>

        <h3 className="performance-console-subheading">A4 Set Review Path</h3>
        <div className="performance-console-list">
          {a4ReviewSurface.steps.map((step) => (
            <article key={`${step.order}-${step.macro_name}`}>
              <strong>{step.macro_label}</strong>
              <span>
                {step.macro_name} / seed {step.seed} / intensity {step.intensity} / energy{' '}
                {step.energy}
              </span>
              <small>{step.summary}</small>
              <small>
                {step.readiness} / ready {step.ready_count} / review {step.review_count} /
                blocked {step.blocked_count}
              </small>
              <small>{step.validation_command}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Readiness Events</h3>
        <div className="performance-console-list">
          {a4ReviewSurface.readiness_events.map((event) => (
            <article key={`${event.track}-${event.parameter}-${event.value}`}>
              <strong>
                Track {event.track} / {event.parameter}
              </strong>
              <span>
                {event.role} / {event.lane} / CC{event.control} to {event.value}
              </span>
              <small>{event.status}</small>
              <small>{event.validation_command}</small>
              <small>{event.reason}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Validation Workflow</h3>
        <div className="performance-console-list">
          <article>
            <strong>Preflight</strong>
            <span>{a4ReviewSurface.preflight_command}</span>
            {a4ReviewSurface.validation_steps.map((step) => (
              <small key={step}>{step}</small>
            ))}
          </article>
          <article>
            <strong>Promotion Gates</strong>
            {a4ReviewSurface.promotion_gates.map((gate) => (
              <small key={gate}>{gate}</small>
            ))}
          </article>
          <article>
            <strong>Recovery Notes</strong>
            {a4ReviewSurface.recovery_notes.map((note) => (
              <small key={note}>{note}</small>
            ))}
          </article>
        </div>

        <div className="live-chip-row">
          {a4ReviewSurface.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
          {a4ReviewSurface.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="A4 macro validation is a review-only Cockpit surface."
          >
            Review A4 {a4ReviewFocus.macro_name}
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="A4 full macro send remains blocked until hardware validation promotes it."
          >
            Promote A4 Macro
          </button>
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-macro-actions"
        aria-labelledby="console-macro-actions-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-macro-actions-title">Live Macro Actions</h2>
          <span>
            {model.macro_action_deck.deck_status} / current {model.macro_action_deck.current_macro_key}
          </span>
        </header>
        <div className="performance-console-macro-grid">
          {sortedMacros.map((card) => (
            <article
              key={card.macro_key}
              className={`performance-console-macro-card ${card.status}`}
              data-testid={card.test_id}
            >
              <header>
                <strong>{card.label}</strong>
                <span>{card.macro_key}</span>
              </header>
              <small>
                {card.shell_command} / {card.send_policy} / {card.risk_label}
              </small>
              <span>pads {card.affected_pads.join(', ')}</span>
              <div className="live-chip-row" aria-label={`Macro ${card.macro_key} boundary`}>
                <span className="live-chip">recover {card.recovery_action}</span>
                <span className="live-chip live-chip-blocked">
                  hardware {card.hardware_action_state}
                </span>
                {card.dry_run_only ? <span className="live-chip">dry-run only</span> : null}
              </div>
              <small>{card.operator_hint}</small>
              <div className="live-chip-row">
                {model.macro_action_deck.blocked_actions.map((action) => (
                  <span key={`${card.macro_key}-${action}`} className="live-chip live-chip-blocked">
                    {action}
                  </span>
                ))}
              </div>
              <div className="performance-console-macro-actions">
                <button
                  type="button"
                  className="live-readiness-action"
                  disabled
                  title="Macro preparation is blocked in this passive console packet."
                >
                  Prepare {card.macro_key}
                </button>
                <button
                  type="button"
                  className="live-readiness-action live-readiness-action-locked"
                  disabled
                  title="Real sends remain in the explicitly armed snapshot shell."
                >
                  Send {card.macro_key}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-rehearsal-board"
        aria-labelledby="console-rehearsal-board-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-rehearsal-board-title">Rehearsal Board</h2>
          <span>{model.rehearsal_board.board_status}</span>
        </header>
        <p className="panel-meta">{model.rehearsal_board.title}</p>
        <small>{model.rehearsal_board.launch_command}</small>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="The armed shell launch command is shown for operator review only."
          >
            Launch Armed Shell
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="Rehearsal cues cannot send hardware from this passive console."
          >
            Fire Cue
          </button>
        </div>

        <h3 className="performance-console-subheading">Live Chapters</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.chapters.map((chapter) => (
            <article key={chapter.name}>
              <strong>{chapter.label}</strong>
              <span>
                {chapter.rytm_command} / recover {chapter.recovery_action}
              </span>
              <small>{chapter.operator_intent}</small>
              <div className="live-chip-row">
                {chapter.macro_sequence.map((macro) => (
                  <span key={`${chapter.name}-${macro}`} className="live-chip">
                    {macro}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Operator Cues</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.operator_cues.map((cue) => (
            <article key={`${cue.chapter_name}-${cue.rytm_stage_command}`}>
              <strong>{cue.label}</strong>
              <span>
                OXI {cue.oxi_action} / Rytm {cue.rytm_stage_command}
              </span>
              <small>
                inspect {cue.inspect_command} / fire {cue.fire_command} / recover{' '}
                {cue.recovery_command}
              </small>
              <small>{cue.expected_result}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Pad Lane Checks</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.pad_lane_checks.map((lane) => (
            <article key={lane.summary}>
              <strong>{lane.summary}</strong>
              <span>pads {lane.pads.join(', ')}</span>
              <small>{lane.expected_motion}</small>
              <small>{lane.warning}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Next Hardware Validations</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.hardware_validation_runway.map((step) => (
            <article key={step.name}>
              <strong>{step.name}</strong>
              <span>
                {step.device} / {step.validation_mode}
              </span>
              <small>{step.operator_path}</small>
              <small>{step.expected_evidence}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">A4 Promotion Gates</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.promotion_criteria.map((criterion) => (
            <article key={criterion.name}>
              <strong>{toHumanLabel(criterion.name)}</strong>
              <span>
                {criterion.device} / {criterion.current_status}
              </span>
              <small>{criterion.required_evidence}</small>
              <small>{criterion.safety_note}</small>
            </article>
          ))}
        </div>

        <div className="live-chip-row">
          {model.rehearsal_board.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-controller-brain-panel"
        aria-labelledby="console-controller-brain-panel-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-controller-brain-panel-title">Controller Brain</h2>
          <span>{model.controller_brain_panel.panel_status}</span>
        </header>
        <p className="panel-meta">{model.controller_brain_panel.scenario_label}</p>
        <small>
          {model.controller_brain_panel.profile_key} / {model.controller_brain_panel.source_report}
        </small>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Controller input remains blocked until a separate hardware bridge is designed."
          >
            Open Controller Input
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="Controller gestures are passive intent rows and cannot dispatch Cockpit commands."
          >
            Dispatch Controller Cue
          </button>
        </div>

        <h3 className="performance-console-subheading">Template Export</h3>
        <div className="performance-console-list">
          <article>
            <strong>controller template rows {model.controller_brain_panel.template_row_count}</strong>
            <span>
              {model.controller_brain_panel.template_page_count} pages /{' '}
              {model.controller_brain_panel.gesture_count} rehearsed gestures
            </span>
            <small>{model.controller_brain_panel.scenario_summary}</small>
          </article>
          {model.controller_brain_panel.template_page_cards.map((page) => (
            <article key={page.page_key}>
              <strong>{page.page_key}</strong>
              <span>
                {page.row_count} rows / slots {page.first_slot}-{page.last_slot}
              </span>
              <small>{page.page_label}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Virtual Gesture Outcomes</h3>
        <div className="performance-console-list">
          {model.controller_brain_panel.gesture_outcomes.map((outcome) => (
            <article key={`${outcome.step}-${outcome.assignment_key}`}>
              <strong>
                {outcome.assignment_key} -&gt; {outcome.resolved_intent_key}
              </strong>
              <span>
                {outcome.gesture} / delta {outcome.value_delta} / {outcome.status}
              </span>
              <small>{outcome.notes}</small>
            </article>
          ))}
        </div>

        <div className="live-chip-row">
          {model.controller_brain_panel.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-live-kit-capture-panel"
        aria-labelledby="console-live-kit-capture-panel-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-live-kit-capture-panel-title">{model.live_kit_capture_panel.title}</h2>
          <span>{model.live_kit_capture_panel.panel_status}</span>
        </header>
        <p className="panel-meta">{model.live_kit_capture_panel.tagline}</p>
        <small>
          {model.live_kit_capture_panel.source_report} /{' '}
          {model.live_kit_capture_panel.launch_command}
        </small>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Passive Cockpit reports cannot receive SysEx or open MIDI input ports."
          >
            Receive Kit
          </button>
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Captured-kit mutation stays in the explicitly armed snapshot shell."
          >
            Mutate Captured Kit
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="Real sends remain blocked from this passive console."
          >
            Send Captured Plan
          </button>
        </div>

        <h3 className="performance-console-subheading">Live Capture Workflow</h3>
        <div className="performance-console-list">
          {model.live_kit_capture_panel.workflow_steps.map((step) => (
            <article key={step.step_key}>
              <strong>{step.label}</strong>
              <span>
                {step.step_key} / {step.operator_command}
              </span>
              <small>{step.description}</small>
              <small>{step.cockpit_state}</small>
              <small>{step.safety_note}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Why This Beats Fixed Mapping</h3>
        <div className="performance-console-list">
          {model.live_kit_capture_panel.differentiators.map((item) => (
            <article key={item.name}>
              <strong>{item.label}</strong>
              <span>{item.name}</span>
              <small>{item.summary}</small>
              <small>{item.controller_limit}</small>
              <small>{item.why_it_matters}</small>
            </article>
          ))}
        </div>

        <div className="live-chip-row" aria-label="Live kit capture recovery commands">
          {model.live_kit_capture_panel.recovery_commands.map((command) => (
            <span key={command} className="live-chip">
              {command}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit capture blocked actions">
          {model.live_kit_capture_panel.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit capture safety lines">
          {model.live_kit_capture_panel.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-live-kit-capture-workbench"
        aria-labelledby="console-live-kit-capture-workbench-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-live-kit-capture-workbench-title">
            {model.live_kit_capture_workbench.title}
          </h2>
          <span>{model.live_kit_capture_workbench.workbench_status}</span>
        </header>
        <p className="panel-meta">{model.live_kit_capture_workbench.summary}</p>
        <small>
          {model.live_kit_capture_workbench.source_panel_id} /{' '}
          {model.live_kit_capture_workbench.launch_command}
        </small>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Passive Cockpit workbench cannot receive SysEx."
          >
            Receive Kit
          </button>
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Mutation staging remains in the explicitly armed snapshot shell."
          >
            Stage Mutation
          </button>
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Captured-kit package apply is not active in this passive report."
          >
            Apply Package
          </button>
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="This workbench advertises package metadata only."
          >
            Export Package
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="Real sends remain blocked from this passive console."
          >
            Send Captured Plan
          </button>
        </div>

        <h3 className="performance-console-subheading">Capture Slots</h3>
        <div className="performance-console-list">
          {model.live_kit_capture_workbench.capture_slots.map((slot) => (
            <article key={slot.slot_key}>
              <strong>{slot.label}</strong>
              <span>
                {slot.slot_key} / {slot.operator_command} / {slot.slot_status}
              </span>
              <small>{slot.stores}</small>
              <small>{slot.source}</small>
              <small>{slot.safety_note}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Anchor Verification</h3>
        <div className="performance-console-list">
          <article>
            <strong>{model.live_kit_capture_workbench.anchor_verification.anchor_key}</strong>
            <span>
              {model.live_kit_capture_workbench.anchor_verification.expected_kit_label} /{' '}
              {model.live_kit_capture_workbench.anchor_verification.fingerprint_source}
            </span>
          </article>
          {model.live_kit_capture_workbench.anchor_verification.checks.map((check) => (
            <article key={check.check_key}>
              <strong>{check.label}</strong>
              <span>
                {check.check_key} / {check.status}
              </span>
              <small>{check.evidence}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Mutation Readiness</h3>
        <div className="performance-console-list">
          <article>
            <strong>{model.live_kit_capture_workbench.mutation_readiness.readiness_status}</strong>
            <span>
              ready {model.live_kit_capture_workbench.mutation_readiness.ready_gate_count} /
              blocked {model.live_kit_capture_workbench.mutation_readiness.blocked_gate_count}
            </span>
          </article>
          {model.live_kit_capture_workbench.mutation_readiness.gates.map((gate) => (
            <article key={gate.gate_key}>
              <strong>{gate.label}</strong>
              <span>
                {gate.gate_key} / {gate.operator_action} / {gate.status}
              </span>
              <small>
                {gate.cockpit_action_allowed ? 'cockpit allowed' : 'cockpit blocked'}
              </small>
              <small>{gate.blocked_action}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Recovery Gates</h3>
        <div className="performance-console-list">
          {model.live_kit_capture_workbench.recovery_gates.map((gate) => (
            <article key={gate.gate_key}>
              <strong>{gate.label}</strong>
              <span>
                {gate.gate_key} / {gate.operator_sequence}
              </span>
              <small>{gate.expected_result}</small>
              <small>{gate.required_before_fire ? 'required before fire' : 'fallback'}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Package Manifest</h3>
        <div className="performance-console-list">
          <article>
            <strong>
              {model.live_kit_capture_workbench.package_manifest.manifest_version}
            </strong>
            <span>
              {model.live_kit_capture_workbench.package_manifest.manifest_id} / exports{' '}
              {String(model.live_kit_capture_workbench.package_manifest.exports_files)}
            </span>
            <small>
              includes {model.live_kit_capture_workbench.package_manifest.includes.join(', ')}
            </small>
            <small>
              disabled{' '}
              {model.live_kit_capture_workbench.package_manifest.disabled_controls.join(', ')}
            </small>
          </article>
        </div>

        <div className="live-chip-row" aria-label="Live kit capture workbench blocked actions">
          {model.live_kit_capture_workbench.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit capture workbench package blocked actions">
          {model.live_kit_capture_workbench.package_manifest.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit capture workbench safety lines">
          {model.live_kit_capture_workbench.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-live-kit-package-audition"
        aria-labelledby="console-live-kit-package-audition-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-live-kit-package-audition-title">
            {model.live_kit_package_audition.title}
          </h2>
          <span>{model.live_kit_package_audition.audition_status}</span>
        </header>
        <p className="panel-meta">{model.live_kit_package_audition.summary}</p>
        <small>
          {model.live_kit_package_audition.source_workbench_id} /{' '}
          {model.live_kit_package_audition.source_package_manifest_version}
        </small>
        <div className="performance-console-macro-actions">
          {model.live_kit_package_audition.disabled_controls.map((control) => (
            <button
              key={control}
              type="button"
              className="live-readiness-action live-readiness-action-locked"
              disabled
              title="Live kit package audition is passive review metadata only."
            >
              {control}
            </button>
          ))}
        </div>

        <h3 className="performance-console-subheading">Audition Summary</h3>
        <div className="performance-console-list">
          <article>
            <strong>{model.live_kit_package_audition.audition_id}</strong>
            <span>
              slots {model.live_kit_package_audition.audition_summary.slot_count} /
              queue {model.live_kit_package_audition.audition_summary.queue_count} /
              checks {model.live_kit_package_audition.audition_summary.check_count} /
              journal {model.live_kit_package_audition.audition_summary.journal_preview_count}
            </span>
          </article>
        </div>

        <h3 className="performance-console-subheading">Audition Slots</h3>
        <div className="performance-console-list">
          {model.live_kit_package_audition.audition_slots.map((slot) => (
            <article key={slot.slot_key}>
              <strong>{slot.label}</strong>
              <span>
                {slot.slot_key} / {slot.style_crate} / {slot.slot_status}
              </span>
              <small>pads {slot.target_pads.join(', ')}</small>
              <small>sequence {slot.operator_sequence.join(' -> ')}</small>
              <small>
                energy {slot.energy} / risk {slot.risk} / seed {slot.seed}
              </small>
              <small>{slot.recovery_command}</small>
              <small>{slot.notes}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Audition Queue</h3>
        <div className="performance-console-list">
          {model.live_kit_package_audition.audition_queue.map((queueItem) => (
            <article key={queueItem.queue_key}>
              <strong>queue {queueItem.queue_key}</strong>
              <span>
                {queueItem.queue_status} / {queueItem.fire_command}
              </span>
              <small>{queueItem.review_command}</small>
              <small>{queueItem.recovery_command}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Package Checks</h3>
        <div className="performance-console-list">
          {model.live_kit_package_audition.package_checks.map((check) => (
            <article key={check.check_key}>
              <strong>{check.label}</strong>
              <span>
                {check.check_key} / {check.status}
              </span>
              <small>{check.required ? 'required' : 'optional'}</small>
              <small>{check.evidence}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Journal Preview</h3>
        <div className="performance-console-list">
          <article>
            <strong>{model.live_kit_package_audition.journal_preview.name}</strong>
            <span>
              {model.live_kit_package_audition.journal_preview.seed} /{' '}
              {model.live_kit_package_audition.journal_preview.depth} /{' '}
              {model.live_kit_package_audition.journal_preview.guardrail_mode}
            </span>
            <small>
              tags {model.live_kit_package_audition.journal_preview.tags.join(', ')}
            </small>
            <small>pads {model.live_kit_package_audition.journal_preview.pads.join(', ')}</small>
            <small>{model.live_kit_package_audition.journal_preview.value_summary}</small>
            <small>{model.live_kit_package_audition.journal_preview.notes}</small>
            <small>{model.live_kit_package_audition.journal_preview.replay_policy}</small>
          </article>
        </div>

        <div className="live-chip-row" aria-label="Live kit package audition replay commands">
          {model.live_kit_package_audition.replay_commands.map((command) => (
            <span key={command} className="live-chip">
              {command}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit package audition blocked actions">
          {model.live_kit_package_audition.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit package audition safety lines">
          {model.live_kit_package_audition.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-live-kit-operator-package"
        aria-labelledby="console-live-kit-operator-package-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-live-kit-operator-package-title">
            {liveKitOperatorPackage.title}
          </h2>
          <span>{liveKitOperatorPackage.operator_package_status}</span>
        </header>
        <p className="panel-meta">{liveKitOperatorPackage.summary}</p>
        <small>
          {liveKitOperatorPackage.operator_package_id} /{' '}
          {liveKitOperatorPackage.source_audition_id} /{' '}
          {liveKitOperatorPackage.source_workbench_id}
        </small>

        <h3 className="performance-console-subheading">Operator Manifest</h3>
        <div className="performance-console-list">
          <article>
            <strong>{liveKitOperatorPackage.package_manifest.package_kind}</strong>
            <span>
              slots {liveKitOperatorPackage.package_manifest.slot_count} /
              queue {liveKitOperatorPackage.package_manifest.queue_count} /
              recovery {liveKitOperatorPackage.package_manifest.recovery_count} /
              exports {String(liveKitOperatorPackage.package_manifest.exports_files)}
            </span>
            <small>
              includes {liveKitOperatorPackage.package_manifest.includes.join(', ')}
            </small>
          </article>
        </div>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action performance-console-local-control"
            disabled={
              onRehearseOperatorPackageSequence === undefined ||
              liveKitOperatorPackage.operator_steps.length === 0
            }
            title="Rehearses every operator package step through the mock-safe sidecar bridge."
            onClick={rehearseOperatorPackageSequence}
          >
            Rehearse operator package sequence
          </button>
          <button
            type="button"
            className="live-readiness-action performance-console-local-control"
            disabled={
              onPreviewOperatorPackageApply === undefined ||
              liveKitOperatorPackage.operator_steps.length === 0
            }
            title="Previews the operator package apply plan through the mock-safe sidecar bridge."
            onClick={previewOperatorPackageApply}
          >
            Preview operator package apply plan
          </button>
          <button
            type="button"
            className="live-readiness-action performance-console-local-control"
            disabled={
              onMockApplyOperatorPackage === undefined ||
              liveKitOperatorPackage.operator_steps.length === 0
            }
            title="Accepts the operator package in mock only through the sidecar bridge."
            onClick={mockApplyOperatorPackage}
          >
            Mock apply operator package
          </button>
          <button
            type="button"
            className="live-readiness-action performance-console-local-control"
            disabled={
              onBuildOperatorPackageReceipt === undefined ||
              liveKitOperatorPackage.operator_steps.length === 0
            }
            title="Builds a passive receipt for the current operator package preview evidence."
            onClick={buildOperatorPackageReceipt}
          >
            Build operator package receipt
          </button>
        </div>

        {operatorPackageApplyPreview === null ? null : (
          <section
            className="performance-console-local-package"
            data-testid="performance-console-operator-package-apply-preview"
            aria-label="Operator package apply preview review"
          >
            <strong>Operator package apply preview</strong>
            <div className="performance-console-local-package-grid">
              <span>{operatorPackageApplyPreview.preview_status}</span>
              <span>{operatorPackageApplyPreview.apply_policy}</span>
              <span>steps {operatorPackageApplyPreview.step_count}</span>
              <span>snapshot {operatorPackageApplyPreview.snapshot_id}</span>
              <span>mock safe {String(operatorPackageApplyPreview.mock_safe)}</span>
              <span>opened MIDI port {String(operatorPackageApplyPreview.opened_midi_port)}</span>
              <span>sent MIDI {String(operatorPackageApplyPreview.sent_midi)}</span>
              <span>writes files {String(operatorPackageApplyPreview.writes_files)}</span>
            </div>
            <small>
              {operatorPackageApplyPreviewSummaryText(
                operatorPackageApplyPreview.dry_run_summary,
              )}
            </small>

            <h3 className="performance-console-subheading">Apply Steps</h3>
            <div className="performance-console-list">
              {operatorPackageApplyPreview.apply_steps.map((step) => (
                <article key={`${step.order}-${step.step_key}`}>
                  <strong>{step.label}</strong>
                  <span>
                    {step.order} / {step.step_key} / {step.slot_key} /{' '}
                    {step.readiness_status}
                  </span>
                  <small>{step.package_export_key}</small>
                  <small>
                    {step.local_action} / {step.operator_command}
                  </small>
                  <small>{step.recovery_command}</small>
                  <small>{step.blocked_action}</small>
                </article>
              ))}
            </div>

            <h3 className="performance-console-subheading">Readiness Checks</h3>
            <div className="performance-console-list">
              {operatorPackageApplyPreview.readiness_checks.map((check) => (
                <article key={check.check}>
                  <strong>{check.check}</strong>
                  <span>
                    {check.check} / {check.status}
                  </span>
                  <small>
                    {check.required === undefined
                      ? 'requirement metadata unavailable'
                      : check.required
                        ? 'required'
                        : 'optional'}
                  </small>
                  <small>{operatorPackageApplyPreviewReadinessEvidence(check)}</small>
                </article>
              ))}
            </div>

            <h3 className="performance-console-subheading">Recovery Requirements</h3>
            <div className="performance-console-list">
              {operatorPackageApplyPreview.recovery_requirements.map((requirement) => (
                <article key={requirement.requirement_key}>
                  <strong>{requirement.label}</strong>
                  <span>
                    {requirement.requirement_key} / {requirement.command}
                  </span>
                  <small>
                    {requirement.required_before_send ? 'required before send' : 'optional'}
                  </small>
                  <small>{requirement.evidence}</small>
                </article>
              ))}
            </div>

            <div className="live-chip-row" aria-label="Operator package apply preview blocked actions">
              {operatorPackageApplyPreview.blocked_actions.map((action) => (
                <span key={action} className="live-chip live-chip-blocked">
                  {action}
                </span>
              ))}
            </div>
            <div className="live-chip-row" aria-label="Operator package apply preview safety lines">
              {operatorPackageApplyPreview.safety_lines.map((line) => (
                <span key={line} className="live-chip">
                  {line}
                </span>
              ))}
            </div>
          </section>
        )}

        {operatorPackageMockApply === null ? null : (
          <section
            className="performance-console-local-package"
            data-testid="performance-console-operator-package-mock-apply"
            aria-label="Operator package mock apply review"
          >
            <strong>Operator package mock apply</strong>
            <div className="performance-console-local-package-grid">
              <span>{operatorPackageMockApply.mock_apply_status}</span>
              <span>{operatorPackageMockApply.apply_policy}</span>
              <span>steps {operatorPackageMockApply.step_count}</span>
              <span>snapshot {operatorPackageMockApply.snapshot_id}</span>
              <span>mock safe {String(operatorPackageMockApply.mock_safe)}</span>
              <span>opened MIDI port {String(operatorPackageMockApply.opened_midi_port)}</span>
              <span>sent MIDI {String(operatorPackageMockApply.sent_midi)}</span>
              <span>writes files {String(operatorPackageMockApply.writes_files)}</span>
              <span>mutated snapshot {String(operatorPackageMockApply.mutated_snapshot)}</span>
              <span>
                applied send plan {String(operatorPackageMockApply.applied_send_plan)}
              </span>
              <span>emitted events {String(operatorPackageMockApply.emitted_events)}</span>
            </div>
            <small>
              {operatorPackageMockApplySummaryText(operatorPackageMockApply.dry_run_summary)}
            </small>

            <h3 className="performance-console-subheading">Mock Apply Steps</h3>
            <div className="performance-console-list">
              {operatorPackageMockApply.mock_apply_steps.map((step) => (
                <article key={`${step.order}-${step.step_key}`}>
                  <strong>{step.label}</strong>
                  <span>
                    {step.order} / {step.step_key} / {step.slot_key} /{' '}
                    {step.mock_apply_status}
                  </span>
                  <small>{step.package_export_key}</small>
                  <small>
                    {step.local_action} / {step.operator_command}
                  </small>
                  <small>{step.recovery_command}</small>
                  <small>{step.blocked_action}</small>
                </article>
              ))}
            </div>

            <h3 className="performance-console-subheading">Readiness Checks</h3>
            <div className="performance-console-list">
              {operatorPackageMockApply.readiness_checks.map((check) => (
                <article key={check.check}>
                  <strong>{check.check}</strong>
                  <span>
                    {check.check} / {check.status}
                  </span>
                  <small>
                    {check.required === undefined
                      ? 'requirement metadata unavailable'
                      : check.required
                        ? 'required'
                        : 'optional'}
                  </small>
                  <small>{operatorPackageApplyPreviewReadinessEvidence(check)}</small>
                </article>
              ))}
            </div>

            <h3 className="performance-console-subheading">Recovery Requirements</h3>
            <div className="performance-console-list">
              {operatorPackageMockApply.recovery_requirements.map((requirement) => (
                <article key={requirement.requirement_key}>
                  <strong>{requirement.label}</strong>
                  <span>
                    {requirement.requirement_key} / {requirement.command}
                  </span>
                  <small>
                    {requirement.required_before_send ? 'required before send' : 'optional'}
                  </small>
                  <small>{requirement.evidence}</small>
                </article>
              ))}
            </div>

            <div
              className="live-chip-row"
              aria-label="Operator package mock apply blocked actions"
            >
              {operatorPackageMockApply.blocked_actions.map((action) => (
                <span key={action} className="live-chip live-chip-blocked">
                  {action}
                </span>
              ))}
            </div>
            <div
              className="live-chip-row"
              aria-label="Operator package mock apply safety lines"
            >
              {operatorPackageMockApply.safety_lines.map((line) => (
                <span key={line} className="live-chip">
                  {line}
                </span>
              ))}
            </div>
          </section>
        )}

        {operatorPackageReceipt === null ? null : (
          <section
            className="performance-console-local-package"
            data-testid="performance-console-operator-package-receipt"
            aria-label="Operator package receipt audit"
          >
            <strong>Operator package receipt</strong>
            <div className="performance-console-local-package-grid">
              <span>{operatorPackageReceipt.receipt_status}</span>
              <span>{operatorPackageReceipt.receipt_policy}</span>
              <span>steps {operatorPackageReceipt.step_count}</span>
              <span>snapshot {operatorPackageReceipt.snapshot_id}</span>
              <span>receipt {operatorPackageReceipt.receipt_digest}</span>
              <span>mock safe {String(operatorPackageReceipt.mock_safe)}</span>
              <span>opened MIDI port {String(operatorPackageReceipt.opened_midi_port)}</span>
              <span>sent MIDI {String(operatorPackageReceipt.sent_midi)}</span>
              <span>writes files {String(operatorPackageReceipt.writes_files)}</span>
              <span>mutated snapshot {String(operatorPackageReceipt.mutated_snapshot)}</span>
              <span>applied send plan {String(operatorPackageReceipt.applied_send_plan)}</span>
              <span>events emitted {String(operatorPackageReceipt.events_emitted)}</span>
            </div>
            <small>{operatorPackageReceiptSummaryText(operatorPackageReceipt.audit_summary)}</small>

            <h3 className="performance-console-subheading">Receipt Steps</h3>
            <div className="performance-console-list">
              {operatorPackageReceipt.receipt_steps.map((step) => (
                <article key={`${step.order}-${step.step_key}`}>
                  <strong>{step.label}</strong>
                  <span>
                    {step.order} / {step.step_key} / {step.slot_key} /{' '}
                    {step.readiness_status}
                  </span>
                  <small>{step.package_export_key}</small>
                  <small>
                    {step.local_action} / {step.operator_command}
                  </small>
                  <small>{step.recovery_command}</small>
                  <small>{step.blocked_action}</small>
                  <small>{step.receipt_status}</small>
                </article>
              ))}
            </div>

            <h3 className="performance-console-subheading">Receipt Checks</h3>
            <div className="performance-console-list">
              {operatorPackageReceipt.readiness_checks.map((check) => (
                <article key={check.check}>
                  <strong>{check.check}</strong>
                  <span>
                    {check.check} / {check.status}
                  </span>
                  <small>
                    {check.required === undefined
                      ? 'requirement metadata unavailable'
                      : check.required
                        ? 'required'
                        : 'optional'}
                  </small>
                  <small>{operatorPackageReceiptReadinessEvidence(check)}</small>
                </article>
              ))}
            </div>

            <h3 className="performance-console-subheading">Recovery Requirements</h3>
            <div className="performance-console-list">
              {operatorPackageReceipt.recovery_requirements.map((requirement) => (
                <article key={requirement.requirement_key}>
                  <strong>{requirement.label}</strong>
                  <span>
                    {requirement.requirement_key} / {requirement.command}
                  </span>
                  <small>
                    {requirement.required_before_send ? 'required before send' : 'optional'}
                  </small>
                  <small>{requirement.evidence}</small>
                </article>
              ))}
            </div>

            <div className="live-chip-row" aria-label="Operator package receipt blocked actions">
              {operatorPackageReceipt.blocked_actions.map((action) => (
                <span key={action} className="live-chip live-chip-blocked">
                  {action}
                </span>
              ))}
            </div>
            <div className="live-chip-row" aria-label="Operator package receipt safety lines">
              {operatorPackageReceipt.safety_lines.map((line) => (
                <span key={line} className="live-chip">
                  {line}
                </span>
              ))}
            </div>
          </section>
        )}

        <section
          className="performance-console-local-package"
          data-testid="performance-console-operator-package-review-ledger"
          aria-label="Operator package review ledger"
        >
          <strong>{operatorPackageReviewLedger.title}</strong>
          <div className="performance-console-local-package-grid">
            <span>{operatorPackageReviewLedger.ledger_status}</span>
            <span>stages {operatorPackageReviewLedger.review_stage_count}</span>
            <span>steps {operatorPackageReviewLedger.step_count}</span>
            <span>mock safe {String(operatorPackageReviewLedger.readiness_summary.mock_safe)}</span>
            <span>
              opened MIDI port{' '}
              {String(operatorPackageReviewLedger.readiness_summary.opened_midi_port)}
            </span>
            <span>sent MIDI {String(operatorPackageReviewLedger.readiness_summary.sent_midi)}</span>
            <span>
              writes files {String(operatorPackageReviewLedger.readiness_summary.writes_files)}
            </span>
            <span>
              required recovery{' '}
              {operatorPackageReviewLedger.readiness_summary.required_recovery_count}
            </span>
          </div>
          <small>
            {operatorPackageReviewLedger.ledger_id} /{' '}
            {operatorPackageReviewLedger.operator_package_id}
          </small>

          <h3 className="performance-console-subheading">Review Stages</h3>
          <div className="performance-console-list">
            {operatorPackageReviewLedger.review_stages.map((stage) => (
              <article key={stage.stage_key}>
                <strong>{stage.label}</strong>
                <span>
                  {stage.stage_key} / {stage.policy} / {stage.status}
                </span>
                <small>{stage.summary}</small>
                <small>
                  sent MIDI {String(stage.sent_midi)} / writes files{' '}
                  {String(stage.writes_files)}
                </small>
              </article>
            ))}
          </div>

          <h3 className="performance-console-subheading">Step Ledger</h3>
          <div className="performance-console-list">
            {operatorPackageReviewLedger.step_rows.map((row) => (
              <article key={`${row.order}-${row.step_key}`}>
                <strong>{row.label}</strong>
                <span>
                  {row.slot_key} / {row.package_export_key} / {row.depth_percent}%
                </span>
                <small>
                  {row.queue_status} / {row.local_action} / {row.operator_command}
                </small>
                <small>
                  {row.preview_status} / {row.mock_apply_status} / {row.receipt_status}
                </small>
                <small>{row.recovery_command}</small>
              </article>
            ))}
          </div>

          <div className="performance-console-macro-actions">
            <button
              type="button"
              className="live-readiness-action live-readiness-action-locked"
              disabled
              title="Ledger apply remains blocked in the passive console."
            >
              Apply operator package ledger
            </button>
          </div>
          <div className="live-chip-row" aria-label="Operator package review ledger replay commands">
            {operatorPackageReviewLedger.replay_commands.map((command) => (
              <span key={command} className="live-chip">
                {command}
              </span>
            ))}
          </div>
          <div className="live-chip-row" aria-label="Operator package review ledger blocked actions">
            {operatorPackageReviewLedger.blocked_actions.map((action) => (
              <span key={action} className="live-chip live-chip-blocked">
                {action}
              </span>
            ))}
          </div>
          <div className="live-chip-row" aria-label="Operator package review ledger safety lines">
            {operatorPackageReviewLedger.safety_lines.map((line) => (
              <span key={line} className="live-chip">
                {line}
              </span>
            ))}
          </div>
        </section>

        <h3 className="performance-console-subheading">Operator Steps</h3>
        <div className="performance-console-list">
          {liveKitOperatorPackage.operator_steps.map((step) => (
            <article key={step.step_key}>
              <strong>{step.label}</strong>
              <span>
                {step.slot_key} / {step.local_action} / {step.operator_command}
              </span>
              <small>
                {step.queue_status} / {step.stage_target} / {step.cockpit_binding}
              </small>
              <small>{step.recovery_command}</small>
              <small>{step.safety_status}</small>
              <button
                type="button"
                className="live-readiness-action performance-console-local-control"
                title="Stages this operator package step in the browser-local set plan only."
                onClick={() => {
                  stageOperatorPackageStep(step);
                }}
              >
                Stage {step.label} operator package
              </button>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Slot Bindings</h3>
        <div className="performance-console-list">
          {liveKitOperatorPackage.slot_bindings.map((binding) => (
            <article key={binding.slot_key}>
              <strong>{binding.package_export_key}</strong>
              <span>
                {binding.slot_key} / {binding.style_crate} / {binding.depth_percent}%
              </span>
              <small>{binding.queue_key || 'reference'}</small>
              <small>{binding.journal_seed}</small>
              <small>{binding.value_source}</small>
              <small>{binding.action_preview}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Recovery Requirements</h3>
        <div className="performance-console-list">
          {liveKitOperatorPackage.recovery_requirements.map((requirement) => (
            <article key={requirement.requirement_key}>
              <strong>{requirement.label}</strong>
              <span>
                {requirement.requirement_key} / {requirement.command}
              </span>
              <small>
                {requirement.required_before_send ? 'required before send' : 'optional'}
              </small>
              <small>{requirement.evidence}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Journal And Export Preview</h3>
        <div className="performance-console-list">
          <article>
            <strong>{liveKitOperatorPackage.journal_commit_preview.name}</strong>
            <span>
              {liveKitOperatorPackage.journal_commit_preview.commit_status} /{' '}
              {liveKitOperatorPackage.journal_commit_preview.write_policy}
            </span>
            <small>{liveKitOperatorPackage.journal_commit_preview.seed}</small>
            <small>
              tags {liveKitOperatorPackage.journal_commit_preview.tags.join(', ')}
            </small>
          </article>
          <article>
            <strong>{liveKitOperatorPackage.local_export_preview.export_kind}</strong>
            <span>
              {liveKitOperatorPackage.local_export_preview.export_status} / writes{' '}
              {String(liveKitOperatorPackage.local_export_preview.writes_files)}
            </span>
            <small>
              fields {liveKitOperatorPackage.local_export_preview.extra_fields.join(', ')}
            </small>
          </article>
        </div>

        <div className="performance-console-macro-actions">
          {liveKitOperatorPackage.disabled_controls.map((control) => (
            <button
              key={control}
              type="button"
              className="live-readiness-action live-readiness-action-locked"
              disabled
              title="Operator package hardware actions remain blocked in this passive console."
            >
              {control}
            </button>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit operator package replay commands">
          {liveKitOperatorPackage.replay_commands.map((command) => (
            <span key={command} className="live-chip">
              {command}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit operator package blocked actions">
          {liveKitOperatorPackage.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Live kit operator package safety lines">
          {liveKitOperatorPackage.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
      </section>

      <PanelHost region="deck" model={model} />

      <section
        className="performance-console-surface"
        data-testid="performance-console-command-queue"
        aria-labelledby="console-command-queue-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-command-queue-title">Command Queue</h2>
          <span>{model.command_queue.queue_status}</span>
        </header>
        <div className="performance-console-list">
          {model.command_queue.queued_commands.map((command) => (
            <article key={command.key}>
              <strong>{command.label}</strong>
              <span>{command.target}</span>
              <small>
                {command.status} / {command.estimated_message_count} dry-run messages
              </small>
            </article>
          ))}
        </div>
        <button type="button" className="live-readiness-action" disabled>
          Dry-run SEND
        </button>
      </section>

      <section
        className="performance-console-surface"
        data-testid="performance-console-safety"
        aria-labelledby="console-safety-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-safety-title">Safety Checklist</h2>
          <span>
            {model.safety_checklist.passed_count} / {model.safety_checklist.total_count}
          </span>
        </header>
        <div className="performance-console-list">
          {model.safety_checklist.items.map((item) => (
            <article key={item.key}>
              <strong>{item.label}</strong>
              <span>{item.status}</span>
              <small>{item.message}</small>
            </article>
          ))}
        </div>
        <button
          type="button"
          className="live-readiness-action live-readiness-action-locked"
          disabled
          title={model.safety_checklist.arm_gate.reason}
        >
          {model.safety_checklist.arm_gate.label} / {model.safety_checklist.arm_gate.state}
        </button>
      </section>

      <footer className="performance-console-bottom-strip" data-testid="performance-console-bottom-strip">
        <span>Session {model.session_label}</span>
        <span>Devices {deviceListLabel(sortedDevices)}</span>
        <span>Mock {mockSummary(sortedDevices)}</span>
        <span>Rytm {rytmDevice?.hardware_state ?? 'not present'}</span>
        <span>A4 {analogFourDevice?.hardware_state ?? 'not present'}</span>
        <span>Journal entries {model.style_queue.journal_cards.length}</span>
        <span>Cockpit Mode {model.hardware_mode}</span>
      </footer>
    </main>
  );
}
