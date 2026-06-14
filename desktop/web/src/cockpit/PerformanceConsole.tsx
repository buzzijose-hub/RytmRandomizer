import { useEffect, useMemo, useRef, useState } from 'react';

import type {
  LiveGuiAnalyzerPanelControlDict,
  LiveGuiDeviceInventoryCardDict,
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
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID } from './devices';
import { RYTM_PARAMETER_GROUPS } from './parameterGroups';

export interface PerformanceConsoleProps {
  model: LiveGuiPerformanceConsoleModelDict;
  packetSource?: string;
}

const ANALYZER_CONTROL_ORDER: ReadonlyArray<string> = ['preview', 'dry_run', 'arm_hardware'];
const SNAPSHOT_DECK_PREVIEW_PARAMETER_COUNT = 3;
const PREVIEW_DEPTH_MIN = 10;
const PREVIEW_DEPTH_MAX = 90;
const LOCAL_REHEARSAL_STORAGE_KEY = 'rytmrandomizer.performanceConsole.localRehearsal.v1';
const LOCAL_REHEARSAL_STORAGE_VERSION = 1;

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

function orderedAnalyzerControls(
  controls: Readonly<Record<string, LiveGuiAnalyzerPanelControlDict>>,
): ReadonlyArray<LiveGuiAnalyzerPanelControlDict> {
  const ordered = ANALYZER_CONTROL_ORDER.map((key) => controls[key]).filter(
    (control): control is LiveGuiAnalyzerPanelControlDict => control !== undefined,
  );
  const remaining = Object.values(controls).filter(
    (control) => !ANALYZER_CONTROL_ORDER.includes(control.key),
  );
  return [...ordered, ...remaining];
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
  const nextLocalSetPlanIndex = useRef<number>(initialLocalRehearsal?.nextLocalSetPlanIndex ?? 0);
  const [lastSetPlanAction, setLastSetPlanAction] = useState<string>(
    initialLocalRehearsal?.lastSetPlanAction ?? 'No local set-plan action yet.',
  );
  const a4SetPlan = model.performance_flow.analog_four_set_plan;
  const a4ReviewSurface = model.analog_four_review_surface;
  const a4ReviewFocus = a4ReviewSurface.review_focus;
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
    model.style_queue.crate_cards.find((crate) => crate.crate_key === selectedCrateKey) ??
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
  const localHandoffLines = [
    localSetPlanHandoffLine('Current', currentSetPlanStep),
    localSetPlanHandoffLine('Next', nextLocalSetPlanStep),
    localOperatorRecentLine(localOperatorEvents),
    'Recovery: use Z + send from the armed snapshot shell.',
    'Local handoff only: no WebSocket command, sidecar action, MIDI port, arm, or send.',
  ];
  const localRehearsalSnapshot = useMemo<LocalRehearsalSnapshot>(
    () => ({
      version: LOCAL_REHEARSAL_STORAGE_VERSION,
      selectedCrateKey,
      selectedQueueKey,
      selectedSnapshotId,
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

  const exportLocalRehearsalJson = (): void => {
    const payload = JSON.stringify(localRehearsalSnapshot, null, 2);
    setLocalExportPayload(payload);
    setLocalPersistenceSummary('Exported local rehearsal JSON. Local only; no MIDI sent.');
    appendLocalOperatorEvent(
      'Exported local rehearsal JSON',
      `${localJournalEntries.length} journal take(s), ${localSetPlanEntries.length} queued step(s).`,
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
    const importedSnapshot = localRehearsalSnapshotFromUnknown(parsed);
    if (importedSnapshot === null) {
      setLocalPersistenceSummary('Import failed: unsupported local rehearsal payload. Local only; no MIDI sent.');
      appendLocalOperatorEvent('Import failed', 'Unsupported local rehearsal payload.');
      return;
    }
    setSelectedCrateKey(importedSnapshot.selectedCrateKey);
    setSelectedQueueKey(importedSnapshot.selectedQueueKey);
    setSelectedSnapshotId(importedSnapshot.selectedSnapshotId);
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
        label: 'Imported local rehearsal JSON',
        detail: 'Loaded passive browser-local rehearsal state.',
        status: 'Local only',
      },
    ]);
    setLocalPersistenceSummary('Imported local rehearsal JSON. Local only; no MIDI sent.');
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
        className="performance-console-surface"
        data-testid="performance-console-analyzer-panel"
        aria-labelledby="console-analyzer-panel-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-analyzer-panel-title">{model.analyzer_panel.title}</h2>
          <span>
            {model.analyzer_panel.panel_status} / {model.analyzer_panel.panel_mode}
          </span>
        </header>
        <p className="panel-meta">{model.analyzer_panel.reference_label}</p>
        <div className="performance-console-list" aria-label="Analyzer spectrum">
          {model.analyzer_panel.spectrum_bands.map((band) => (
            <article key={band.key}>
              <strong>{band.label}</strong>
              <span>
                {band.low_hz}-{band.high_hz} Hz / {band.status}
              </span>
              <small>{band.value_percent}%</small>
            </article>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Analyzer required actions">
          {model.analyzer_panel.required_actions.map((action) => (
            <span key={action} className="live-chip">
              {action}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Analyzer blocked actions">
          {model.analyzer_panel.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
        <div className="performance-console-macro-actions">
          {orderedAnalyzerControls(model.analyzer_panel.controls).map((control) => (
            <button
              key={control.key}
              type="button"
              className="live-readiness-action"
              disabled={!control.enabled}
              title={control.status}
            >
              {control.label} analyzer
            </button>
          ))}
        </div>
      </section>

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
