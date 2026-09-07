import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';

import { announce } from '../../a11y';
import { selectCanSend, useCockpitStore } from '../../state';
import type {
  Command,
  CommandAck,
  CommandType,
  KitCaptureDeviceId,
  KitCaptureResult,
  ShowBank,
  ShowBankEntry,
  ShowCaptureReference,
} from '../../ws/protocol';
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID } from '../devices';
import { ExactRytmSendDialog, useExactRytmSend } from '../ExactRytmSend';
import { LockButton } from '../LockButton';
import { PanelRenderer } from '../panels/PanelRenderer';
import { useCockpitClient } from '../context';
import { useMutationTargets } from '../useMutationTargets';
import { usePadLocks } from '../usePadLocks';
import { A4PreparationPanel } from './A4PreparationPanel';

import {
  applyEntryMove,
  findActiveBank,
  findEntry,
  fingerprintMatchLabel,
  mismatchMessages,
  normalizePackId,
  SHOW_STATUS_LABELS,
  shouldAdoptServerDraft,
  showReadinessPanelSpec,
} from './showKitForgeModel';

const SAFE_ARTIFACT_NAME = /^[a-z0-9][a-z0-9_-]{0,95}$/;
const CANDIDATE_COUNTS = [2, 3, 4, 5] as const;
const SLOT_MIN = 1;
const SLOT_MAX = 128;

function displaySlot(slot: number | null): string {
  return slot === null ? 'Not reported' : String(slot);
}

function boundedSlot(value: number): number {
  return Math.min(SLOT_MAX, Math.max(SLOT_MIN, Math.round(value)));
}

function errorDetail(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function notesFromText(value: string): string[] {
  return value
    .split('\n')
    .map((note) => note.trim())
    .filter((note) => note !== '');
}

function idList(ids: readonly number[], item: string): string {
  return ids.length === 0 ? `All ${item}s` : ids.map((id) => `${item[0]?.toUpperCase()}${id}`).join(', ');
}

function hardwareSaveSummary(entry: ShowBankEntry, stale: boolean): string {
  const rytmSaved = entry.rytm_hardware_save !== null;
  const a4Saved = entry.analog_four_hardware_save !== null;
  if (!rytmSaved && !a4Saved) {
    return 'Marked favorite in Cockpit; neither instrument has a manual save attestation.';
  }
  if (rytmSaved && !a4Saved) {
    return 'Rytm is attested/unverified. Save the favorite manually on Analog Four, then recapture both instruments.';
  }
  if (!rytmSaved && a4Saved) {
    return 'Analog Four is attested/unverified. Save the favorite manually on Rytm, then recapture both instruments.';
  }
  if (
    entry.rytm_recapture?.matches_candidate === true &&
    entry.analog_four_recapture?.matches_candidate === true
  ) {
    return !stale && entry.status === 'show-ready'
      ? 'Paired recaptures and the latest show-time preflight match.'
      : 'Paired recaptures match. Load both favorite slots and run a fresh show-time preflight.';
  }
  return 'Both manual saves are attested/unverified. Recapture both current KITs to verify them.';
}

function auditionStatusLabel(entry: ShowBankEntry): string {
  if (entry.rytm_audition_status === 'live_unsaved_hardware') return 'Live unsaved hardware';
  if (entry.rytm_audition_status === 'historical_audition_hardware_unknown') {
    return 'Historical audition — hardware state unknown';
  }
  return 'Not auditioned';
}

function ScopeGrid({
  label,
  itemIds,
  itemLabel,
  isTargeted,
  toggleTarget,
  clearTargets,
  hasExplicitTargets,
  isLocked,
  toggleLock,
  disabled,
}: {
  label: string;
  itemIds: readonly number[];
  itemLabel: 'pad' | 'track';
  isTargeted: (id: number) => boolean;
  toggleTarget: (id: number) => void;
  clearTargets: () => void;
  hasExplicitTargets: boolean;
  isLocked: (id: number) => boolean;
  toggleLock: (id: number) => void;
  disabled: boolean;
}): JSX.Element {
  return (
    <fieldset className="show-kit-forge-scope" disabled={disabled || itemIds.length === 0}>
      <legend>{label}</legend>
      {itemIds.length === 0 ? (
        <p className="show-kit-forge-help">Capture this device’s KIT to load its available {itemLabel}s.</p>
      ) : (
        <>
          <p className="show-kit-forge-help">Effective scope is targets minus locks.</p>
          <button type="button" className="show-kit-forge-link-button" onClick={clearTargets}>
            {hasExplicitTargets ? `Target all ${itemLabel}s` : `All ${itemLabel}s targeted`}
          </button>
        </>
      )}
      <div className="show-kit-forge-scope-grid">
        {itemIds.map((id) => (
          <div className="show-kit-forge-scope-item" key={id}>
            <label>
              <input
                type="checkbox"
                checked={isTargeted(id)}
                onChange={() => toggleTarget(id)}
              />
              <span>{itemLabel === 'pad' ? `P${id}` : `T${id}`}</span>
            </label>
            <LockButton
              locked={isLocked(id)}
              onToggle={() => toggleLock(id)}
              padId={id}
              itemLabel={itemLabel}
            />
          </div>
        ))}
      </div>
    </fieldset>
  );
}

/** Interactive, server-authoritative Show Kit Forge store-slice panel. */
export function ShowKitForgePanel(): JSX.Element {
  const client = useCockpitClient();
  const showBankState = useCockpitStore((state) => state.showBank);
  const showBankStale = useCockpitStore((state) => state.showBankStale);
  const currentCandidate = useCockpitStore((state) => state.previewCandidate);
  const captures = useCockpitStore((state) => state.kitCaptures);
  const profile = useCockpitStore((state) => state.profile);
  const connectionStatus = useCockpitStore((state) => state.connectionStatus);
  const sessionStatus = useCockpitStore((state) => state.sessionStatus);
  const sessionStatusStale = useCockpitStore((state) => state.sessionStatusStale);
  const sessionGeneration = useCockpitStore((state) => state.sessionGeneration);
  const sendPlan = useCockpitStore((state) => state.sendPlan);
  const canSend = useCockpitStore(selectCanSend);
  const rytmTargetIds = useCockpitStore((state) => state.rytmPadTargets);
  const a4TargetIds = useCockpitStore((state) => state.a4TrackTargets);
  const rytmLockIds = useCockpitStore((state) => state.rytmPadLocks);
  const a4LockIds = useCockpitStore((state) => state.a4TrackLocks);

  const rytmTargets = useMutationTargets(RYTM_DEVICE_ID);
  const a4Targets = useMutationTargets(ANALOG_FOUR_DEVICE_ID);
  const rytmLocks = usePadLocks(RYTM_DEVICE_ID);
  const a4Locks = usePadLocks(ANALOG_FOUR_DEVICE_ID);

  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  const [pendingCommand, setPendingCommand] = useState<CommandType | null>(null);
  const [feedback, setFeedback] = useState('');
  const [removePendingKey, setRemovePendingKey] = useState<string | null>(null);
  const [favoriteReplacementKey, setFavoriteReplacementKey] = useState<
    string | null
  >(null);

  const [newBankName, setNewBankName] = useState('');
  const [newBankDescription, setNewBankDescription] = useState('');
  const [newBankNotes, setNewBankNotes] = useState('');
  const [bankName, setBankName] = useState('');
  const [bankDescription, setBankDescription] = useState('');
  const [bankNotes, setBankNotes] = useState('');
  const [bankDraftDirty, setBankDraftDirty] = useState(false);

  const [entryName, setEntryName] = useState('');
  const [entryDescription, setEntryDescription] = useState('');
  const [auditionNotes, setAuditionNotes] = useState('');
  const [energyLevel, setEnergyLevel] = useState<number | null>(null);
  const [energyNotes, setEnergyNotes] = useState('');
  const [transitionNotes, setTransitionNotes] = useState('');
  const [recoveryNotes, setRecoveryNotes] = useState('');
  const [oxiProject, setOxiProject] = useState('');
  const [oxiPattern, setOxiPattern] = useState('');
  const [oxiChapter, setOxiChapter] = useState('');
  const [entryDraftDirty, setEntryDraftDirty] = useState(false);

  const [depthPreset, setDepthPreset] = useState<'small' | 'medium' | 'large' | 'custom'>(
    'medium',
  );
  const [depth, setDepth] = useState(0.5);
  const [candidateCount, setCandidateCount] = useState(3);
  const [seed, setSeed] = useState(1);
  const [rytmSlot, setRytmSlot] = useState(1);
  const [a4Slot, setA4Slot] = useState(1);
  const [rytmSavedSlot, setRytmSavedSlot] = useState(1);
  const [a4SavedSlot, setA4SavedSlot] = useState(1);
  const [packName, setPackName] = useState('');
  const [artifactName, setArtifactName] = useState('');
  const observedBankVersion = useRef<string | null>(null);
  const observedBankIdentity = useRef<string | null>(null);
  const observedEntryVersion = useRef<string | null>(null);
  const observedEntryIdentity = useRef<string | null>(null);
  const artifactBankIdentity = useRef<string | null>(null);
  const commandGeneration = useRef(0);
  const requestedSessionGeneration = useRef<number | null>(null);

  const activeBank = useMemo(() => findActiveBank(showBankState), [showBankState]);
  const activeEntry = useMemo(
    () => findEntry(activeBank, selectedEntryId),
    [activeBank, selectedEntryId],
  );
  useEffect(() => {
    setSelectedEntryId(null);
  }, [activeBank?.bank_id, activeBank?.active_entry_id]);
  const readinessSpec = useMemo(
    () => showReadinessPanelSpec(activeBank, activeEntry, showBankStale),
    [activeBank, activeEntry, showBankStale],
  );
  const mismatches = useMemo(() => mismatchMessages(activeEntry), [activeEntry]);
  const hasMismatch = mismatches.length > 0;

  const rytmCapture = captures.find((capture) => capture.device_id === RYTM_DEVICE_ID);
  const a4Capture = captures.find((capture) => capture.device_id === ANALOG_FOUR_DEVICE_ID);
  const rytmScopeIds = rytmCapture?.layout_items.map((item) => item.index) ?? [];
  const a4ScopeIds = a4Capture?.layout_items.map((item) => item.index) ?? [];
  const pairedCaptureReady =
    rytmCapture?.round_trip_verified === true &&
    a4Capture?.round_trip_verified === true &&
    a4Capture.parameter_readiness === 'filter1_frequency_offline_ready';
  const connected = connectionStatus === 'connected';
  const sessionReady = connected && sessionStatus !== null &&
    !sessionStatusStale;
  const busy = pendingCommand !== null;
  const selectedCandidate = activeEntry?.candidates.find(
    (candidate) => candidate.candidate_id === activeEntry.selected_candidate_id,
  );
  const selectedCandidateIsCurrent = selectedCandidate !== undefined &&
    activeBank?.active_entry_id === activeEntry?.entry_id &&
    selectedCandidate.rytm_candidate.candidate_id === currentCandidate?.candidate_id;

  const issue = useCallback(
    async (
      command: Command,
      action: string,
      announceResult = true,
      successMessage?: (ack: CommandAck) => string,
    ): Promise<CommandAck | null> => {
      const generation = ++commandGeneration.current;
      setPendingCommand(command.type);
      setFeedback(`${action} requested; waiting for the server.`);
      try {
        const ack = await client.send(command);
        if (generation !== commandGeneration.current) return ack;
        if (!ack.ok) {
          const detail = ack.message ?? ack.error ?? 'command rejected';
          setFeedback(`${action} failed: ${detail}`);
          if (announceResult) announce(`${action} failed: ${detail}`);
          return ack;
        }
        const message =
          successMessage?.(ack) ??
          `${action} accepted; waiting for authoritative show bank state.`;
        setFeedback(message);
        if (announceResult) announce(message);
        return ack;
      } catch (error: unknown) {
        if (generation !== commandGeneration.current) return null;
        const message = `${action} failed: ${errorDetail(error)}`;
        setFeedback(message);
        if (announceResult) announce(message);
        return null;
      } finally {
        if (generation === commandGeneration.current) setPendingCommand(null);
      }
    },
    [client],
  );

  const sendExactRytm = useCallback(
    (command: Extract<Command, { type: 'send' }>): void => {
      const live = command.confirm === true;
      void issue(
        command,
        live ? 'Send exact Rytm plan' : 'Dry-run exact Rytm plan',
      );
    },
    [issue],
  );
  const exactSend = useExactRytmSend({
    canSend: canSend && selectedCandidateIsCurrent && sessionReady && !showBankStale && !busy,
    onSend: sendExactRytm,
    sendPlan,
    session: sessionStatus,
    sourceReload: activeEntry === null ? undefined : {
      fingerprint: activeEntry.rytm_source.fingerprint,
      slot: activeEntry.rytm_source.hardware_slot,
    },
  });

  useEffect(() => {
    if (!sessionReady) {
      commandGeneration.current += 1;
      setPendingCommand(null);
      return;
    }
    // Store-owned freshness survives panel remounts and React batching of
    // disconnect/reconnect updates; socket-open alone never authenticates.
    if (requestedSessionGeneration.current !== sessionGeneration) {
      requestedSessionGeneration.current = sessionGeneration;
      void issue({ type: 'show_bank_list' }, 'Show bank refresh', false);
    }
  }, [issue, sessionGeneration, sessionReady]);

  useEffect(() => {
    if (activeBank === null) {
      observedBankVersion.current = null;
      observedBankIdentity.current = null;
      setBankDraftDirty(false);
      return;
    }
    const version = `${showBankState?.revision}:${activeBank.bank_id}:${activeBank.revision}`;
    if (observedBankVersion.current === version) return;
    const identityChanged = observedBankIdentity.current !== activeBank.bank_id;
    observedBankVersion.current = version;
    observedBankIdentity.current = activeBank.bank_id;
    const serverSignature = JSON.stringify([
      activeBank.name,
      activeBank.description,
      activeBank.notes,
    ]);
    const draftSignature = JSON.stringify([
      bankName.trim(),
      bankDescription.trim(),
      notesFromText(bankNotes),
    ]);
    if (shouldAdoptServerDraft(identityChanged, bankDraftDirty, serverSignature === draftSignature)) {
      setBankName(activeBank.name);
      setBankDescription(activeBank.description);
      setBankNotes(activeBank.notes.join('\n'));
      setBankDraftDirty(false);
    }
  }, [activeBank, bankDescription, bankDraftDirty, bankName, bankNotes, showBankState?.revision]);

  useEffect(() => {
    if (activeBank === null) {
      artifactBankIdentity.current = null;
      return;
    }
    if (artifactBankIdentity.current === activeBank.bank_id) return;
    artifactBankIdentity.current = activeBank.bank_id;
    setArtifactName(normalizePackId(activeBank.name));
  }, [activeBank]);

  useEffect(() => {
    if (activeEntry === null) {
      observedEntryVersion.current = null;
      observedEntryIdentity.current = null;
      setEntryDraftDirty(false);
      return;
    }
    const version = `${showBankState?.revision}:${activeEntry.entry_id}:${activeEntry.updated_at}`;
    if (observedEntryVersion.current === version) return;
    const identityChanged = observedEntryIdentity.current !== activeEntry.entry_id;
    observedEntryVersion.current = version;
    observedEntryIdentity.current = activeEntry.entry_id;
    const serverSignature = JSON.stringify([
      activeEntry.name,
      activeEntry.description,
      activeEntry.audition_notes,
      activeEntry.energy_level,
      activeEntry.energy_notes,
      activeEntry.transition_notes,
      activeEntry.recovery_notes,
      activeEntry.oxi.project,
      activeEntry.oxi.pattern,
      activeEntry.oxi.chapter,
    ]);
    const draftSignature = JSON.stringify([
      entryName.trim(),
      entryDescription.trim(),
      notesFromText(auditionNotes),
      energyLevel,
      notesFromText(energyNotes),
      notesFromText(transitionNotes),
      notesFromText(recoveryNotes),
      oxiProject.trim(),
      oxiPattern.trim(),
      oxiChapter.trim(),
    ]);
    if (shouldAdoptServerDraft(identityChanged, entryDraftDirty, serverSignature === draftSignature)) {
      setFavoriteReplacementKey(null);
      setEntryName(activeEntry.name);
      setEntryDescription(activeEntry.description);
      setAuditionNotes(activeEntry.audition_notes.join('\n'));
      setEnergyLevel(activeEntry.energy_level);
      setEnergyNotes(activeEntry.energy_notes.join('\n'));
      setTransitionNotes(activeEntry.transition_notes.join('\n'));
      setRecoveryNotes(activeEntry.recovery_notes.join('\n'));
      setOxiProject(activeEntry.oxi.project);
      setOxiPattern(activeEntry.oxi.pattern);
      setOxiChapter(activeEntry.oxi.chapter);
      setEntryDraftDirty(false);
      const recipe =
        activeEntry.candidates.find(
          (candidate) => candidate.candidate_id === activeEntry.selected_candidate_id,
        )?.recipe ?? activeEntry.candidates.at(-1)?.recipe;
      if (recipe !== undefined) {
        setDepthPreset(recipe.depth_preset);
        setDepth(recipe.depth);
        setSeed(recipe.seed);
      }
    }
  }, [
    activeEntry,
    auditionNotes,
    energyLevel,
    energyNotes,
    entryDescription,
    entryDraftDirty,
    entryName,
    oxiChapter,
    oxiPattern,
    oxiProject,
    recoveryNotes,
    showBankState?.revision,
    transitionNotes,
  ]);

  useEffect(() => {
    setRytmSavedSlot(activeEntry?.rytm_hardware_save?.hardware_slot ?? 1);
    setA4SavedSlot(activeEntry?.analog_four_hardware_save?.hardware_slot ?? 1);
  }, [
    activeEntry?.analog_four_hardware_save?.hardware_slot,
    activeEntry?.entry_id,
    activeEntry?.rytm_hardware_save?.hardware_slot,
  ]);

  useEffect(() => {
    if (rytmCapture?.slot !== null && rytmCapture?.slot !== undefined) {
      setRytmSlot(boundedSlot(rytmCapture.slot));
    }
    if (a4Capture?.slot !== null && a4Capture?.slot !== undefined) {
      setA4Slot(boundedSlot(a4Capture.slot));
    }
  }, [a4Capture, rytmCapture]);

  const chooseDepthPreset = (preset: 'small' | 'medium' | 'large', presetValue: number): void => {
    setDepthPreset(preset);
    setDepth(presetValue);
  };

  const handleDepthShortcut = (event: KeyboardEvent<HTMLElement>): void => {
    const target = event.target;
    if (
      target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target instanceof HTMLSelectElement ||
      target instanceof HTMLButtonElement ||
      (target instanceof HTMLElement && target.isContentEditable)
    ) {
      return;
    }
    const preset = event.key === '1' ? 'small' : event.key === '2' ? 'medium' : event.key === '3' ? 'large' : null;
    if (preset === null) return;
    const presetValue = showBankState?.depth_presets[preset];
    if (presetValue === undefined) return;
    event.preventDefault();
    chooseDepthPreset(preset, presetValue);
    announce(`${preset} forge depth selected, ${Math.round(presetValue * 100)} percent`);
  };

  const submitCreateBank = (event: FormEvent): void => {
    event.preventDefault();
    void issue(
      {
        type: 'show_bank_create',
        name: newBankName.trim(),
        description: newBankDescription.trim(),
        notes: notesFromText(newBankNotes),
      },
      'Create show bank',
    );
  };

  const updateBank = (event: FormEvent, bank: ShowBank): void => {
    event.preventDefault();
    void issue(
      {
        type: 'show_bank_update',
        bank_id: bank.bank_id,
        expected_revision: bank.revision,
        name: bankName.trim(),
        description: bankDescription.trim(),
        notes: notesFromText(bankNotes),
      },
      'Update bank metadata',
    );
  };

  const adoptSources = (
    bank: ShowBank,
    currentRytm: KitCaptureResult,
    currentA4: KitCaptureResult,
  ): void => {
    void issue(
      {
        type: 'show_bank_adopt_sources',
        bank_id: bank.bank_id,
        expected_revision: bank.revision,
        rytm_fingerprint: currentRytm.fingerprint,
        a4_fingerprint: currentA4.fingerprint,
        rytm_slot: boundedSlot(rytmSlot),
        a4_slot: boundedSlot(a4Slot),
      },
      'Adopt paired source anchors',
    );
  };

  const updateEntry = (event: FormEvent, bank: ShowBank, entry: ShowBankEntry): void => {
    event.preventDefault();
    void issue(
      {
        type: 'show_bank_update_entry',
        bank_id: bank.bank_id,
        entry_id: entry.entry_id,
        expected_revision: bank.revision,
        name: entryName.trim(),
        description: entryDescription.trim(),
        audition_notes: notesFromText(auditionNotes),
        energy_level: energyLevel,
        energy_notes: notesFromText(energyNotes),
        transition_notes: notesFromText(transitionNotes),
        recovery_notes: notesFromText(recoveryNotes),
        oxi: {
          project: oxiProject.trim(),
          pattern: oxiPattern.trim(),
          chapter: oxiChapter.trim(),
          direct_oxi_control: false,
        },
      },
      'Update cue metadata',
    );
  };

  const generateCandidates = (bank: ShowBank, entry: ShowBankEntry, profileId: string): void => {
    void issue(
      {
        type: 'show_bank_generate_candidates',
        bank_id: bank.bank_id,
        entry_id: entry.entry_id,
        expected_revision: bank.revision,
        depth_preset: depthPreset,
        depth,
        candidate_count: candidateCount,
        seed,
        profile_id: profileId,
        rytm_targets: rytmTargetIds,
        rytm_locks: rytmLockIds,
        a4_targets: a4TargetIds,
        a4_locks: a4LockIds,
      },
      'Forge candidate pairs',
    );
  };

  const markFavorite = (
    bank: ShowBank,
    entry: ShowBankEntry,
    candidateId: string,
    replaceExisting = false,
  ): void => {
    if (
      !replaceExisting &&
      entry.favorite !== null &&
      entry.favorite.candidate_id !== candidateId
    ) {
      setFavoriteReplacementKey(`${bank.bank_id}:${bank.revision}:${entry.entry_id}:${candidateId}`);
      return;
    }
    setFavoriteReplacementKey(null);
    void issue(
      {
        type: 'show_bank_mark_favorite',
        bank_id: bank.bank_id,
        entry_id: entry.entry_id,
        candidate_id: candidateId,
        expected_revision: bank.revision,
        ...(replaceExisting ? { replace_existing: true } : {}),
      },
      replaceExisting ? 'Replace show-kit favorite' : 'Mark candidate favorite',
    );
  };

  const entryCommand = (
    bank: ShowBank,
    entry: ShowBankEntry,
    command:
      | 'show_bank_verify_recapture'
      | 'show_bank_run_preflight'
      | 'show_bank_duplicate_entry',
    label: string,
  ): void => {
    void issue(
      {
        type: command,
        bank_id: bank.bank_id,
        entry_id: entry.entry_id,
        expected_revision: bank.revision,
      },
      label,
    );
  };

  const reorderEntries = (bank: ShowBank, entryIds: string[]): void => {
    void issue(
      {
        type: 'show_bank_reorder_entries',
        bank_id: bank.bank_id,
        entry_ids: entryIds,
        expected_revision: bank.revision,
      },
      'Reorder cue sheet',
    );
  };

  const attestSaved = (
    bank: ShowBank,
    entry: ShowBankEntry,
    deviceId: KitCaptureDeviceId,
    slot: number,
  ): void => {
    void issue(
      {
        type: 'show_bank_attest_hardware_saved',
        bank_id: bank.bank_id,
        entry_id: entry.entry_id,
        device_id: deviceId,
        slot: boundedSlot(slot),
        expected_revision: bank.revision,
      },
      `${deviceId === RYTM_DEVICE_ID ? 'Rytm' : 'Analog Four'} manual save attestation`,
    );
  };

  const retainCapture = (
    bank: ShowBank,
    entry: ShowBankEntry,
    captureKind: 'source' | 'candidate' | 'favorite',
    deviceId: KitCaptureDeviceId,
  ): void => {
    void issue(
      {
        type: 'show_bank_retain_capture',
        bank_id: bank.bank_id,
        entry_id: entry.entry_id,
        capture_kind: captureKind,
        device_id: deviceId,
        expected_revision: bank.revision,
      },
      `Retain ${captureKind} capture`,
    );
  };

  const sortedEntries = [...(activeBank?.entries ?? [])].sort(
    (left, right) => left.cue_index - right.cue_index,
  );
  const sourceCaptureRows: ReadonlyArray<{
    label: string;
    capture: KitCaptureResult | undefined;
    slot: number;
    setSlot: (value: number) => void;
  }> = [
    { label: 'Rytm', capture: rytmCapture, slot: rytmSlot, setSlot: setRytmSlot },
    { label: 'Analog Four', capture: a4Capture, slot: a4Slot, setSlot: setA4Slot },
  ];
  const sourceRows: ReadonlyArray<{ label: string; source: ShowCaptureReference }> =
    activeEntry === null
      ? []
      : [
          { label: 'Rytm', source: activeEntry.rytm_source },
          { label: 'A4', source: activeEntry.analog_four_source },
        ];
  const hardwareSaveRows: ReadonlyArray<{
    label: string;
    deviceId: KitCaptureDeviceId;
    slot: number;
    setSlot: (value: number) => void;
  }> = [
    {
      label: 'Rytm',
      deviceId: RYTM_DEVICE_ID,
      slot: rytmSavedSlot,
      setSlot: setRytmSavedSlot,
    },
    {
      label: 'Analog Four',
      deviceId: ANALOG_FOUR_DEVICE_ID,
      slot: a4SavedSlot,
      setSlot: setA4SavedSlot,
    },
  ];
  const favorite = activeEntry?.candidates.find(
    (candidate) => candidate.candidate_id === activeEntry.favorite?.candidate_id,
  );
  const hasFavorite = favorite !== undefined;
  const stale = !sessionReady || showBankStale;
  const actionDisabled = stale || busy;
  const validPackName = SAFE_ARTIFACT_NAME.test(packName);
  const validArtifactName = SAFE_ARTIFACT_NAME.test(artifactName);
  const statusLabel = (status: ShowBank['status']): string =>
    stale && status === 'show-ready' ? 'Historical preflight — refresh required' : SHOW_STATUS_LABELS[status];

  return (
    <section
      className="performance-console-surface show-kit-forge"
      data-testid="show-kit-forge"
      aria-labelledby="show-kit-forge-title"
      onKeyDown={handleDepthShortcut}
    >
      <header className="show-kit-forge-header">
        <div>
          <p className="show-kit-forge-eyebrow">Paired performance-bank workflow</p>
          <h2 id="show-kit-forge-title">Show Kit Forge</h2>
          <p>
            Source anchors stay immutable. Cockpit keeps OXI in charge and never issues a
            persistent hardware save.
          </p>
        </div>
        <div className="show-kit-forge-authority" aria-label="Show Kit Forge authority">
          <strong>OXI owns sequencing</strong>
          <span>Direct OXI control: disabled</span>
          <span>A4 SEND: blocked — offline saved-KIT only</span>
        </div>
      </header>

      {stale && (
        <p className="show-kit-forge-stale">
          Last known server state is read-only while the sidecar reconnects. Forge actions are
          disabled until a fresh show-bank packet arrives.
        </p>
      )}
      {feedback !== '' && <p className="show-kit-forge-feedback">{feedback}</p>}

      <div className="show-kit-forge-bank-row">
        <form className="show-kit-forge-form-card" onSubmit={submitCreateBank}>
          <h3>Create bank</h3>
          <label>
            Bank name
            <input
              value={newBankName}
              onChange={(event) => setNewBankName(event.currentTarget.value)}
              maxLength={80}
              required
            />
          </label>
          <label>
            Description
            <input
              value={newBankDescription}
              onChange={(event) => setNewBankDescription(event.currentTarget.value)}
              maxLength={160}
            />
          </label>
          <label>
            Notes
            <textarea
              value={newBankNotes}
              onChange={(event) => setNewBankNotes(event.currentTarget.value)}
              maxLength={1000}
              rows={2}
            />
          </label>
          <button type="submit" disabled={actionDisabled || newBankName.trim() === ''}>
            Create show bank
          </button>
        </form>

        <div className="show-kit-forge-form-card">
          <h3>Select bank</h3>
          <label>
            Server banks
            <select
              value={showBankState?.active_bank_id ?? ''}
              onChange={(event) =>
                void issue(
                  { type: 'show_bank_select', bank_id: event.currentTarget.value },
                  'Select show bank',
                )
              }
              disabled={actionDisabled || (showBankState?.banks.length ?? 0) === 0}
            >
              <option value="">No bank selected</option>
              {(showBankState?.banks ?? []).map((bank) => (
                <option key={bank.bank_id} value={bank.bank_id}>
                  {bank.name}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => void issue({ type: 'show_bank_list' }, 'Show bank refresh')}
            disabled={!sessionReady || busy}
          >
            Refresh from server
          </button>
          <p className="show-kit-forge-help">
            Revision {showBankState?.revision ?? '—'} · no browser persistence
          </p>
        </div>
      </div>

      {activeBank !== null && (
        <>
          <form
            className="show-kit-forge-form-card show-kit-forge-bank-editor"
            onSubmit={(event) => updateBank(event, activeBank)}
          >
            <h3>Bank details</h3>
            <label>
              Name
              <input
                value={bankName}
                onChange={(event) => {
                  setBankDraftDirty(true);
                  setBankName(event.currentTarget.value);
                }}
                maxLength={80}
                required
              />
            </label>
            <label>
              Description
              <input
                value={bankDescription}
                onChange={(event) => {
                  setBankDraftDirty(true);
                  setBankDescription(event.currentTarget.value);
                }}
                maxLength={160}
              />
            </label>
            <label>
              Notes
              <textarea
                value={bankNotes}
                onChange={(event) => {
                  setBankDraftDirty(true);
                  setBankNotes(event.currentTarget.value);
                }}
                maxLength={1000}
                rows={2}
              />
            </label>
            <button type="submit" disabled={actionDisabled || bankName.trim() === ''}>
              Save bank details
            </button>
          </form>

          <nav className="show-kit-forge-entry-tabs" aria-label="Show bank entries">
            {sortedEntries.map((entry) => (
              <button
                type="button"
                key={entry.entry_id}
                aria-current={activeEntry?.entry_id === entry.entry_id ? 'page' : undefined}
                onClick={() => setSelectedEntryId(entry.entry_id)}
              >
                {entry.cue_index}. {entry.name} · {statusLabel(entry.status)}
              </button>
            ))}
          </nav>

          <section className="show-kit-forge-section" aria-labelledby="show-kit-source-title">
            <div className="show-kit-forge-section-heading">
              <div>
                <p className="show-kit-forge-step">Step 1</p>
                <h3 id="show-kit-source-title">Adopt immutable paired sources</h3>
              </div>
              <span>{pairedCaptureReady ? 'Ready to adopt' : 'Two verified captures required'}</span>
            </div>
            <p className="show-kit-forge-help">Use each device rail’s input-only KIT capture: manually load the source slot on the instrument, start capture, then send its current KIT dump from the instrument. Save A4 edits on the instrument before dumping; unsaved edits may not appear in its current-KIT dump.</p>
            <div className="show-kit-forge-source-grid">
              {sourceCaptureRows.map(({ label, capture, slot, setSlot }) => {
                return (
                  <article key={label} className="show-kit-forge-source-card">
                    <h4>{label}</h4>
                    {capture === undefined ? (
                      <p>No current capture.</p>
                    ) : (
                      <>
                        <p>{capture.kit_name}</p>
                        <dl>
                          <div>
                            <dt>Captured slot</dt>
                            <dd>{displaySlot(capture.slot)}</dd>
                          </div>
                          <div>
                            <dt>Fingerprint</dt>
                            <dd><code>{capture.fingerprint}</code></dd>
                          </div>
                          <div>
                            <dt>Evidence</dt>
                            <dd>{capture.parameter_readiness}</dd>
                          </div>
                        </dl>
                      </>
                    )}
                    <label>
                      Source hardware slot (1–128)
                      <input
                        type="number"
                        min={SLOT_MIN}
                        max={SLOT_MAX}
                        value={slot}
                        onChange={(event) => setSlot(Number(event.currentTarget.value))}
                      />
                    </label>
                  </article>
                );
              })}
            </div>
            <div className="show-kit-forge-actions">
              <button
                type="button"
                onClick={
                  rytmCapture === undefined || a4Capture === undefined
                    ? undefined
                    : () => adoptSources(activeBank, rytmCapture, a4Capture)
                }
                disabled={actionDisabled || !pairedCaptureReady}
              >
                Adopt current captures as a new source pair
              </button>
              {activeEntry !== null && (
                <>
                  {activeEntry.rytm_source.sysex.retained === null && (
                    <button
                      type="button"
                      onClick={() => retainCapture(activeBank, activeEntry, 'source', RYTM_DEVICE_ID)}
                      disabled={actionDisabled}
                    >
                      Retain Rytm source
                    </button>
                  )}
                  {activeEntry.analog_four_source.sysex.retained === null && (
                    <button
                      type="button"
                      onClick={() =>
                        retainCapture(activeBank, activeEntry, 'source', ANALOG_FOUR_DEVICE_ID)
                      }
                      disabled={actionDisabled}
                    >
                      Retain A4 source
                    </button>
                  )}
                </>
              )}
            </div>
            {activeEntry !== null && (
              <div className="show-kit-forge-anchor-proof">
                <p><strong>Immutable source fingerprints</strong></p>
                {sourceRows.map(({ label, source }) => {
                  return (
                    <div key={label}>
                      <strong>{label} source: {source.kit_name}</strong>
                      <code>
                        {label} slot {displaySlot(source.hardware_slot)} ·{' '}
                        {source.fingerprint}
                      </code>
                      <span>{source.device_id} · captured <time dateTime={source.captured_at}>{source.captured_at}</time></span>
                      <span>
                        {source.sysex.retained === null ? (
                          'Not retained locally.'
                        ) : (
                          <>
                            Retained as <code>{source.sysex.retained.artifact_name}</code>
                            {' · '}<code>{source.sysex.retained.sha256}</code>{' · '}
                            {source.sysex.retained.byte_count} bytes
                          </>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {activeEntry !== null && (
            <>
              <form
                className="show-kit-forge-section"
                onChange={() => setEntryDraftDirty(true)}
                onSubmit={(event) => updateEntry(event, activeBank, activeEntry)}
              >
                <div className="show-kit-forge-section-heading">
                  <div>
                    <p className="show-kit-forge-step">Cue metadata</p>
                    <h3>Shape the show moment</h3>
                  </div>
                  <span>OXI fields are metadata only</span>
                </div>
                <div className="show-kit-forge-fields-grid">
                  <label>Name<input value={entryName} onChange={(event) => setEntryName(event.currentTarget.value)} maxLength={80} required /></label>
                  <label>Description<input value={entryDescription} onChange={(event) => setEntryDescription(event.currentTarget.value)} maxLength={160} /></label>
                  <label>OXI project<input value={oxiProject} onChange={(event) => setOxiProject(event.currentTarget.value)} maxLength={80} /></label>
                  <label>OXI pattern<input value={oxiPattern} onChange={(event) => setOxiPattern(event.currentTarget.value)} maxLength={80} /></label>
                   <label>OXI chapter<input value={oxiChapter} onChange={(event) => setOxiChapter(event.currentTarget.value)} maxLength={80} /></label>
                   <label>Audition notes<textarea value={auditionNotes} onChange={(event) => setAuditionNotes(event.currentTarget.value)} maxLength={1000} rows={3} /></label>
                   <label>
                     Energy level
                     <select
                       value={energyLevel ?? ''}
                       onChange={(event) =>
                         setEnergyLevel(event.currentTarget.value === '' ? null : Number(event.currentTarget.value))
                       }
                     >
                       <option value="">Not set</option>
                       {[1, 2, 3, 4, 5].map((level) => <option key={level} value={level}>{level} / 5</option>)}
                     </select>
                   </label>
                   <label>Energy notes<textarea value={energyNotes} onChange={(event) => setEnergyNotes(event.currentTarget.value)} maxLength={1000} rows={3} /></label>
                  <label>Transition notes<textarea value={transitionNotes} onChange={(event) => setTransitionNotes(event.currentTarget.value)} maxLength={1000} rows={3} /></label>
                  <label>Recovery notes<textarea value={recoveryNotes} onChange={(event) => setRecoveryNotes(event.currentTarget.value)} maxLength={1000} rows={3} /></label>
                </div>
                <p className="show-kit-forge-help">Direct OXI control is fixed false; no OXI command is emitted.</p>
                <button type="submit" disabled={actionDisabled || entryName.trim() === ''}>Save cue metadata</button>
              </form>

              <section className="show-kit-forge-section" aria-labelledby="show-kit-forge-controls-title">
                <div className="show-kit-forge-section-heading">
                  <div>
                    <p className="show-kit-forge-step">Step 2</p>
                    <h3 id="show-kit-forge-controls-title">Forge candidate pairs</h3>
                  </div>
                  <span>Deterministic seed + profile</span>
                </div>
                <fieldset className="show-kit-forge-depth">
                  <legend>Mutation depth</legend>
                  <div className="show-kit-forge-depth-presets">
                    {(['small', 'medium', 'large'] as const).map((preset, index) => {
                      const presetValue = showBankState?.depth_presets[preset];
                      return (
                        <button
                          type="button"
                          key={preset}
                          aria-pressed={depthPreset === preset}
                          aria-keyshortcuts={String(index + 1)}
                          onClick={presetValue === undefined ? undefined : () => chooseDepthPreset(preset, presetValue)}
                          disabled={presetValue === undefined}
                        >
                          {preset[0]?.toUpperCase()}{preset.slice(1)} ·{' '}
                          {presetValue === undefined ? 'Unavailable' : `${Math.round(presetValue * 100)}%`}
                        </button>
                      );
                    })}
                  </div>
                  <label>
                    Custom depth: {Math.round(depth * 100)}%
                    <input
                      type="range"
                      min="0.1"
                      max="0.9"
                      step="0.01"
                      value={depth}
                      aria-valuetext={`${Math.round(depth * 100)} percent`}
                      onChange={(event) => {
                        setDepthPreset('custom');
                        setDepth(Number(event.currentTarget.value));
                      }}
                    />
                  </label>
                  <p className="show-kit-forge-help">Shortcuts while focused in this panel: 1 small, 2 medium, 3 large.</p>
                </fieldset>
                <div className="show-kit-forge-inline-fields">
                  <label>Starting seed<input type="number" value={seed} min={0} max={2147483647} onChange={(event) => setSeed(Number(event.currentTarget.value))} /></label>
                  <label>Candidate count<select value={candidateCount} onChange={(event) => setCandidateCount(Number(event.currentTarget.value))}>{CANDIDATE_COUNTS.map((count) => <option key={count} value={count}>{count}</option>)}</select></label>
                  <p>Profile: <strong>{profile?.name ?? 'Select a Cockpit profile first'}</strong></p>
                </div>
                <div className="show-kit-forge-scope-columns">
                  <ScopeGrid disabled={actionDisabled} label="Rytm pads" itemIds={rytmScopeIds} itemLabel="pad" isTargeted={rytmTargets.isTargeted} toggleTarget={rytmTargets.toggleTarget} clearTargets={rytmTargets.clearTargets} hasExplicitTargets={rytmTargets.hasExplicitTargets} isLocked={rytmLocks.isLocked} toggleLock={rytmLocks.toggleLock} />
                  <ScopeGrid disabled={actionDisabled} label="Analog Four tracks" itemIds={a4ScopeIds} itemLabel="track" isTargeted={a4Targets.isTargeted} toggleTarget={a4Targets.toggleTarget} clearTargets={a4Targets.clearTargets} hasExplicitTargets={a4Targets.hasExplicitTargets} isLocked={a4Locks.isLocked} toggleLock={a4Locks.toggleLock} />
                </div>
                <button
                  type="button"
                  onClick={
                    profile === null
                      ? undefined
                      : () => generateCandidates(activeBank, activeEntry, profile.profile_id)
                  }
                  disabled={actionDisabled || profile === null}
                >
                  Forge {candidateCount} candidate pairs
                </button>
              </section>

              <section className="show-kit-forge-section" aria-labelledby="show-kit-candidates-title">
                <div className="show-kit-forge-section-heading">
                  <div><p className="show-kit-forge-step">Step 3</p><h3 id="show-kit-candidates-title">Compare candidates</h3></div>
                  <span>{activeEntry.candidates.length} server candidates</span>
                </div>
                {activeEntry.candidates.length === 0 ? (
                  <p>No candidates yet. Source state remains unchanged.</p>
                ) : (
                  <div className="show-kit-forge-candidates">
                     {activeEntry.candidates.map((candidate, index) => {
                       const selected = candidate.candidate_id === activeEntry.selected_candidate_id;
                       const isFavorite = candidate.candidate_id === activeEntry.favorite?.candidate_id;
                       const a4Artifact = candidate.analog_four_candidate.sysex;
                       const rytmChanges = candidate.rytm_candidate.pad_deltas.filter(
                         (delta) => delta.changed_keys.length > 0,
                       );
                       return (
                         <article key={candidate.candidate_id} className="show-kit-forge-candidate" aria-label={`Candidate ${index + 1}`}>
                           <header><h4>Candidate {index + 1}</h4><span>{isFavorite ? 'Favorite' : selected ? 'Selected for audition' : 'In-memory candidate'}</span></header>
                           <p>Profile {candidate.recipe.profile_id}</p>
                           <dl><div><dt>Depth</dt><dd>{candidate.recipe.depth_preset} · {Math.round(candidate.recipe.depth * 100)}%</dd></div><div><dt>Seed</dt><dd>{candidate.recipe.seed}</dd></div><div><dt>Rytm semantic fingerprint</dt><dd><code>{candidate.rytm_semantic_fingerprint}</code></dd></div><div><dt>A4 semantic fingerprint</dt><dd><code>{candidate.analog_four_candidate.semantic_fingerprint}</code></dd></div><div><dt>A4 artifact fingerprint</dt><dd><code>{candidate.analog_four_candidate.artifact_fingerprint}</code></dd></div></dl>
                           <details className="show-kit-forge-candidate-details">
                             <summary>Compare musical changes</summary>
                             <h5>Rytm mapped changes</h5>
                             {rytmChanges.length === 0 ? (
                               <p>No mapped Rytm parameter changes.</p>
                             ) : (
                               <ul>
                                 {rytmChanges.map((delta) => (
                                   <li key={delta.pad_id}>
                                     Pad {delta.pad_id}: {delta.changed_keys.map((key) => `${key} ${delta.proposed_params[key] ?? '—'}`).join(', ')}
                                   </li>
                                 ))}
                               </ul>
                             )}
                             <h5>Analog Four offline values</h5>
                             {candidate.analog_four_candidate.values.length === 0 ? (
                               <p>No mapped A4 parameter changes. Source bytes preserved.</p>
                             ) : <ul>
                               {candidate.analog_four_candidate.values.map((value) => (
                                 <li key={`${value.track_id}-${value.parameter}`}>
                                   Track {value.track_id} {value.parameter}: {value.screen_value}
                                 </li>
                               ))}
                             </ul>}
                             <p>
                               Rytm scope: {idList(candidate.recipe.rytm_scope.target_ids, 'pad')}; locks:{' '}
                               {candidate.recipe.rytm_scope.locked_ids.length === 0
                                 ? 'none'
                                 : idList(candidate.recipe.rytm_scope.locked_ids, 'pad')}.
                             </p>
                             <p>
                               A4 scope: {idList(candidate.recipe.analog_four_scope.target_ids, 'track')}; locks:{' '}
                               {candidate.recipe.analog_four_scope.locked_ids.length === 0
                                 ? 'none'
                                 : idList(candidate.recipe.analog_four_scope.locked_ids, 'track')}.
                             </p>
                           </details>
                           <section className="show-kit-forge-artifact" aria-label={`Candidate ${index + 1} Analog Four offline artifact`}>
                             <h5>A4 offline saved-KIT-format artifact</h5>
                             <dl>
                               <div><dt>Artifact ID</dt><dd><code>{a4Artifact.artifact_id}</code></dd></div>
                               <div><dt>Frame SHA-256</dt><dd><code>{a4Artifact.frame_sha256}</code></dd></div>
                               <div><dt>Bytes</dt><dd>{a4Artifact.frame_bytes}</dd></div>
                               <div><dt>Local retention</dt><dd>{a4Artifact.retained === null ? 'In memory only' : <>Retained as <code>{a4Artifact.retained.artifact_name}</code> · <code>{a4Artifact.retained.sha256}</code> · {a4Artifact.retained.byte_count} bytes</>}</dd></div>
                             </dl>
                             <p>{candidate.analog_four_candidate.evidence_status}</p>
                             <p>Local file only. Cockpit cannot SEND this artifact to Analog Four and has not saved it on hardware. Only Filter 1 Frequency is available here; Amp Attack and every other unsupported captured-KIT field remain mapping-blocked.</p>
                             {a4Artifact.retained === null ? (
                               <button
                                 type="button"
                                 disabled={actionDisabled || !selected}
                                 title={selected ? undefined : 'Select this candidate before retaining its offline A4 bytes.'}
                                 onClick={() => retainCapture(activeBank, activeEntry, 'candidate', ANALOG_FOUR_DEVICE_ID)}
                               >
                                 Retain selected A4 offline artifact
                               </button>
                             ) : (
                               <p><strong>Retained locally and included in show-pack export.</strong></p>
                             )}
                           </section>
                           <p>Rytm candidate remains in memory until exact-plan audition.</p>
                           <div className="show-kit-forge-actions">
                             <button type="button" aria-pressed={selected && selectedCandidateIsCurrent} disabled={actionDisabled || (selected && selectedCandidateIsCurrent)} onClick={() => void issue({ type: 'show_bank_select_candidate', bank_id: activeBank.bank_id, entry_id: activeEntry.entry_id, candidate_id: candidate.candidate_id, expected_revision: activeBank.revision }, 'Select candidate for audition')}>Select for audition</button>
                             <button type="button" aria-pressed={isFavorite} disabled={actionDisabled || isFavorite} onClick={() => markFavorite(activeBank, activeEntry, candidate.candidate_id)}>Mark favorite</button>
                           </div>
                           {favoriteReplacementKey === `${activeBank.bank_id}:${activeBank.revision}:${activeEntry.entry_id}:${candidate.candidate_id}` && (
                             <div className="show-kit-forge-replace-favorite" role="group" aria-label={`Replace favorite with candidate ${index + 1}`}>
                               <p>
                                 Replace the existing favorite? Its hardware-save attestations, recapture verification, and show-time readiness will be cleared.
                               </p>
                               <div className="show-kit-forge-actions">
                                 <button type="button" autoFocus onClick={() => setFavoriteReplacementKey(null)}>Keep current favorite</button>
                                 <button type="button" disabled={actionDisabled} onClick={() => markFavorite(activeBank, activeEntry, candidate.candidate_id, true)}>Replace favorite</button>
                               </div>
                             </div>
                           )}
                         </article>
                      );
                    })}
                  </div>
                )}
              </section>

              <A4PreparationPanel bank={activeBank} entry={activeEntry} disabled={actionDisabled} />

              <section className="show-kit-forge-section" aria-labelledby="show-kit-audition-title">
                <div className="show-kit-forge-section-heading"><div><p className="show-kit-forge-step">Rytm audition</p><h3 id="show-kit-audition-title">Existing exact-plan safety path</h3></div><span>{auditionStatusLabel(activeEntry)}</span></div>
                <p>Selected: <strong>{selectedCandidate === undefined ? 'No candidate selected' : `Candidate ${activeEntry.candidates.indexOf(selectedCandidate) + 1}`}</strong></p>
                {activeEntry.rytm_live_auditioned_candidate_id !== null && (
                  <p>
                    Entry audition record: candidate <code>{activeEntry.rytm_live_auditioned_candidate_id}</code>
                    {activeEntry.rytm_live_auditioned_at === null ? '' : ` at ${activeEntry.rytm_live_auditioned_at}`}.
                  </p>
                )}
                {activeEntry.rytm_audition_status !== 'live_unsaved_hardware' &&
                  (sessionStatus?.unsaved_sends ?? 0) > 0 && (
                    <p className="show-kit-forge-help">
                      This Cockpit session has {sessionStatus?.unsaved_sends} unsaved send(s), but the server does not attribute live unsaved hardware to this cue.
                    </p>
                  )}
                <div className="show-kit-forge-actions">
                  <button type="button" disabled={actionDisabled || !selectedCandidateIsCurrent} onClick={() => void issue({ type: 'toggle_preview', on: true }, 'Preview active Rytm candidate')}>Preview Rytm</button>
                  <button type="button" disabled={actionDisabled || !selectedCandidateIsCurrent} onClick={() => void issue({ type: 'prepare_send_plan' }, 'Prepare exact Rytm plan')}>Prepare exact plan</button>
                  <button ref={exactSend.triggerRef} type="button" disabled={actionDisabled || exactSend.disabled} onClick={exactSend.request}>
                    {exactSend.label === 'SEND' ? 'Send exact Rytm plan' : 'Dry-run exact Rytm plan'}
                  </button>
                  <button type="button" disabled title="Analog Four SEND is not implemented; retain or export the offline saved-KIT-format artifact.">A4 SEND blocked — offline only</button>
                </div>
                <p className="show-kit-forge-help">Before each hardware audition, manually reload Rytm source slot {displaySlot(activeEntry.rytm_source.hardware_slot)}, capture its current KIT in the device rail, then select the candidate again and prepare its exact plan. This prevents earlier audition changes from carrying into the next candidate.</p>
                <ExactRytmSendDialog
                  className="arm-dialog show-kit-forge-confirm"
                  controller={exactSend}
                  sendPlan={sendPlan}
                  session={sessionStatus}
                />
              </section>

              <section className="show-kit-forge-section" aria-labelledby="show-kit-save-title">
                <div className="show-kit-forge-section-heading"><div><p className="show-kit-forge-step">Steps 4–5</p><h3 id="show-kit-save-title">Favorite, manual save, recapture</h3></div><span>{statusLabel(activeEntry.status)}</span></div>
                <ol className="show-kit-forge-lifecycle">
                  {(['source', 'candidate', 'favorite', 'hardware-saved', 'verified', 'show-ready'] as const).map((status) => <li key={status} aria-current={activeEntry.status === status ? 'step' : undefined}><span aria-hidden="true">{activeEntry.status === status ? '●' : '○'}</span> {SHOW_STATUS_LABELS[status]}</li>)}
                </ol>
                {hasFavorite ? (
                  <p className="show-kit-forge-save-instruction">
                    <strong>
                      {activeEntry.status === 'verified' || activeEntry.status === 'show-ready'
                        ? 'Recapture verified'
                        : 'Save on instrument, then recapture'}
                    </strong>
                    <br />
                    {hardwareSaveSummary(activeEntry, stale)}
                  </p>
                ) : (
                  <p>Select a candidate and mark it favorite before recording any hardware-save attestation.</p>
                )}
                <div className="show-kit-forge-save-grid">
                  {hardwareSaveRows.map(({ label, deviceId, slot, setSlot }) => {
                    const save = deviceId === RYTM_DEVICE_ID ? activeEntry.rytm_hardware_save : activeEntry.analog_four_hardware_save;
                    const recapture = deviceId === RYTM_DEVICE_ID ? activeEntry.rytm_recapture : activeEntry.analog_four_recapture;
                    const retainedRecapture = recapture?.capture.sysex.retained ?? null;
                    return (
                      <article key={deviceId}>
                        <h4>{label}</h4>
                        {save === null ? (
                          <>
                            <p>Hardware save: Not attested</p>
                            <label>
                              Saved hardware slot (1–128)
                              <input
                                type="number"
                                min={SLOT_MIN}
                                max={SLOT_MAX}
                                value={slot}
                                onChange={(event) =>
                                  setSlot(Number(event.currentTarget.value))
                                }
                              />
                            </label>
                            <button
                              type="button"
                              disabled={actionDisabled || !hasFavorite}
                              onClick={() => attestSaved(activeBank, activeEntry, deviceId, slot)}
                            >
                              Attest: I manually saved this on {label}
                            </button>
                          </>
                        ) : (
                          <>
                          <dl>
                            <div><dt>Hardware save</dt><dd>Manually saved — attested/unverified</dd></div>
                            <div><dt>Authoritative saved slot</dt><dd>{save.hardware_slot}</dd></div>
                            <div><dt>Attested at</dt><dd><time dateTime={save.attested_at}>{save.attested_at}</time></dd></div>
                            <div><dt>Attestation</dt><dd>{save.note}</dd></div>
                          </dl>
                          <details>
                            <summary>Correct a recorded hardware slot</summary>
                            <label>
                              Corrected {label} slot (1–128)
                              <input type="number" min={SLOT_MIN} max={SLOT_MAX} value={slot} onChange={(event) => setSlot(Number(event.currentTarget.value))} />
                            </label>
                            <p>Confirm only after manually saving this favorite at the corrected slot. A new attestation clears this instrument’s recapture and requires a fresh show-time preflight.</p>
                            <button type="button" disabled={actionDisabled || slot === save.hardware_slot} onClick={() => attestSaved(activeBank, activeEntry, deviceId, slot)}>Re-attest {label} saved slot</button>
                          </details>
                          </>
                        )}
                        {recapture === null ? (
                          <p>Recapture: Not verified</p>
                        ) : (
                          <>
                            <dl>
                              <div><dt>Semantic result</dt><dd>{fingerprintMatchLabel(recapture.matches_candidate)}</dd></div>
                              <div><dt>Expected semantic fingerprint</dt><dd><code>{recapture.expected_semantic_fingerprint}</code></dd></div>
                              <div><dt>Immutable source semantic fingerprint</dt><dd><code>{recapture.source_semantic_fingerprint}</code></dd></div>
                              <div><dt>Observed semantic fingerprint</dt><dd><code>{recapture.observed_semantic_fingerprint ?? 'Unavailable'}</code></dd></div>
                              <div><dt>Matches favorite candidate</dt><dd>{recapture.matches_candidate ? 'Yes' : 'No'}</dd></div>
                              <div><dt>Matches immutable source</dt><dd>{recapture.matches_source ? 'Yes' : 'No'}</dd></div>
                              <div><dt>Favorite capture fingerprint</dt><dd><code>{recapture.capture.fingerprint}</code></dd></div>
                              <div><dt>Favorite capture slot</dt><dd>{displaySlot(recapture.capture.hardware_slot)}</dd></div>
                              <div><dt>Recorded at</dt><dd><time dateTime={recapture.recorded_at}>{recapture.recorded_at}</time></dd></div>
                              <div><dt>Comparison basis</dt><dd>{recapture.comparison_reason}</dd></div>
                            </dl>
                            {retainedRecapture === null ? (
                              <button
                                type="button"
                                disabled={actionDisabled}
                                onClick={() => retainCapture(activeBank, activeEntry, 'favorite', deviceId)}
                              >
                                Retain {label} recapture evidence
                              </button>
                            ) : (
                              <p>
                                Recapture evidence retained as <code>{retainedRecapture.artifact_name}</code>
                                {' · '}<code>{retainedRecapture.sha256}</code>{' · '}
                                {retainedRecapture.byte_count} bytes
                              </p>
                            )}
                          </>
                        )}
                      </article>
                    );
                  })}
                </div>
                <div className="show-kit-forge-actions">
                  <button type="button" disabled={actionDisabled || activeEntry.rytm_hardware_save === null || activeEntry.analog_four_hardware_save === null || !pairedCaptureReady} onClick={() => entryCommand(activeBank, activeEntry, 'show_bank_verify_recapture', 'Verify paired recapture')}>Verify current paired recapture</button>
                  <button type="button" disabled={actionDisabled || (activeEntry.status !== 'verified' && activeEntry.status !== 'show-ready')} onClick={() => entryCommand(activeBank, activeEntry, 'show_bank_run_preflight', 'Run show-time fingerprint preflight')}>Run show-time preflight</button>
                  <button
                    type="button"
                    disabled={actionDisabled}
                    onClick={() =>
                      void issue(
                        {
                          type: 'show_bank_return_source',
                          bank_id: activeBank.bank_id,
                          entry_id: activeEntry.entry_id,
                          expected_revision: activeBank.revision,
                        },
                        'Reset Cockpit audition to source',
                        true,
                        (ack) => {
                          const slots = ack.source_slots ?? {
                            rytm: activeEntry.rytm_source.hardware_slot,
                            analog_four: activeEntry.analog_four_source.hardware_slot,
                          };
                          return `${
                            ack.instruction ??
                            'Cockpit reset its in-memory audition only; no instrument changed. Manually load the immutable Rytm and Analog Four source slots to return hardware.'
                          } Source slots: Rytm ${displaySlot(slots.rytm)}, Analog Four ${displaySlot(slots.analog_four)}.`;
                        },
                      )
                    }
                  >
                    Reset Cockpit audition to source
                  </button>
                </div>
                <p className="show-kit-forge-help">
                  Resetting Cockpit does not change either instrument. To return hardware, manually load Rytm source slot {displaySlot(activeEntry.rytm_source.hardware_slot)} and Analog Four source slot {displaySlot(activeEntry.analog_four_source.hardware_slot)}.
                </p>
                {activeEntry.show_time_preflight !== null && (
                  <article className="show-kit-forge-preflight" aria-label="Latest show-time preflight">
                    <h4>Latest show-time full-fingerprint preflight</h4>
                    <dl>
                      <div><dt>Rytm expected</dt><dd><code>{activeEntry.show_time_preflight.expected_rytm_fingerprint}</code></dd></div>
                      <div><dt>Rytm observed</dt><dd><code>{activeEntry.show_time_preflight.observed_rytm_fingerprint}</code> · {fingerprintMatchLabel(activeEntry.show_time_preflight.rytm_matches)}</dd></div>
                      <div><dt>Rytm observed capture</dt><dd><code>{activeEntry.show_time_preflight.observed_rytm_capture_id}</code> at <time dateTime={activeEntry.show_time_preflight.observed_rytm_captured_at}>{activeEntry.show_time_preflight.observed_rytm_captured_at}</time></dd></div>
                      <div><dt>A4 expected</dt><dd><code>{activeEntry.show_time_preflight.expected_a4_fingerprint}</code></dd></div>
                      <div><dt>A4 observed</dt><dd><code>{activeEntry.show_time_preflight.observed_a4_fingerprint}</code> · {fingerprintMatchLabel(activeEntry.show_time_preflight.a4_matches)}</dd></div>
                      <div><dt>A4 observed capture</dt><dd><code>{activeEntry.show_time_preflight.observed_a4_capture_id}</code> at <time dateTime={activeEntry.show_time_preflight.observed_a4_captured_at}>{activeEntry.show_time_preflight.observed_a4_captured_at}</time></dd></div>
                    </dl>
                    <p>
                      Checked at <time dateTime={activeEntry.show_time_preflight.checked_at}>{activeEntry.show_time_preflight.checked_at}</time>.
                      {!stale && activeEntry.status === 'show-ready'
                        ? ' This preflight currently grants show readiness.'
                        : ' Historical result only; it does not currently grant show readiness.'}
                    </p>
                    <p>{activeEntry.show_time_preflight.reason}</p>
                  </article>
                )}
                {hasMismatch && <div className="show-kit-forge-mismatch" role="alert"><strong>Fingerprint mismatch — show readiness revoked.</strong><ul>{mismatches.map((message) => <li key={message}>{message}</li>)}</ul><p>Reset Cockpit audition to source, manually load both source slots, or recapture the intended favorite slots.</p></div>}
              </section>

              <section className="show-kit-forge-section" aria-labelledby="show-kit-cues-title">
                <div className="show-kit-forge-section-heading"><div><p className="show-kit-forge-step">Show bank</p><h3 id="show-kit-cues-title">Readiness and cue sheet</h3></div><span>{sortedEntries.length} cues</span></div>
                <div className="show-kit-forge-table-scroll">
                  <table className="show-kit-forge-cue-table">
                    <thead>
                      <tr>
                        <th scope="col">Order</th><th scope="col">Cue</th><th scope="col">State</th><th scope="col">Source slots</th><th scope="col">Favorite slots</th><th scope="col">Favorite captures</th><th scope="col">Energy / transition</th><th scope="col">OXI metadata</th><th scope="col">Recovery</th><th scope="col">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedEntries.map((entry, index) => (
                        <tr key={entry.entry_id}>
                          <td>{entry.cue_index}</td>
                          <th scope="row"><button type="button" className="show-kit-forge-link-button" onClick={() => setSelectedEntryId(entry.entry_id)}>{entry.name}</button></th>
                          <td>{statusLabel(entry.status)}</td>
                          <td>R {displaySlot(entry.rytm_source.hardware_slot)} · A4 {displaySlot(entry.analog_four_source.hardware_slot)}<br />{entry.rytm_source.kit_name} / {entry.analog_four_source.kit_name}</td>
                          <td>R {entry.rytm_hardware_save?.hardware_slot ?? 'Not attested'} · A4 {entry.analog_four_hardware_save?.hardware_slot ?? 'Not attested'}</td>
                          <td>
                            <span>R <code>{entry.rytm_recapture?.capture.fingerprint ?? '—'}</code></span><br />
                            <span>A4 <code>{entry.analog_four_recapture?.capture.fingerprint ?? '—'}</code></span>
                          </td>
                          <td>
                            <span>Level {entry.energy_level ?? '—'} / 5</span><br />
                            <span>Energy: {entry.energy_notes.join(', ') || '—'}</span><br />
                            <span>Transition: {entry.transition_notes.join(', ') || '—'}</span>
                          </td>
                          <td>{entry.oxi.project || '—'} / {entry.oxi.pattern || '—'} / {entry.oxi.chapter || '—'}</td>
                          <td>
                            <strong>Required</strong>
                            <ul>
                              {(entry.readiness.recovery_actions.length === 0 ? ['None'] : entry.readiness.recovery_actions).map((action) => <li key={action}>{action}</li>)}
                            </ul>
                            <strong>Operator notes</strong>
                            <ul>
                              {(entry.recovery_notes.length === 0 ? ['None'] : entry.recovery_notes).map((note) => <li key={note}>{note}</li>)}
                            </ul>
                          </td>
                          <td>
                            <div className="show-kit-forge-table-actions">
                              <button type="button" aria-label={`Move ${entry.name} earlier`} disabled={actionDisabled || index === 0} onClick={() => applyEntryMove(sortedEntries, entry.entry_id, -1, (ids) => reorderEntries(activeBank, ids))}>↑</button>
                              <button type="button" aria-label={`Move ${entry.name} later`} disabled={actionDisabled || index === sortedEntries.length - 1} onClick={() => applyEntryMove(sortedEntries, entry.entry_id, 1, (ids) => reorderEntries(activeBank, ids))}>↓</button>
                              <button type="button" disabled={actionDisabled} onClick={() => void issue({ type: 'show_bank_duplicate_entry', bank_id: activeBank.bank_id, entry_id: entry.entry_id, expected_revision: activeBank.revision }, 'Duplicate cue')}>Duplicate</button>
                              {removePendingKey === `${activeBank.bank_id}:${activeBank.revision}:${entry.entry_id}` ? (
                                <>
                                  <button type="button" onClick={() => setRemovePendingKey(null)}>Cancel</button>
                                  <button type="button" disabled={actionDisabled} onClick={() => { void issue({ type: 'show_bank_remove_entry', bank_id: activeBank.bank_id, entry_id: entry.entry_id, expected_revision: activeBank.revision }, 'Remove cue'); setRemovePendingKey(null); }}>Confirm remove</button>
                                </>
                              ) : (
                                <button type="button" disabled={actionDisabled} onClick={() => setRemovePendingKey(`${activeBank.bank_id}:${activeBank.revision}:${entry.entry_id}`)}>Remove</button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

        </>
      )}

      <section className="show-kit-forge-section" aria-labelledby="show-kit-pack-title">
        <div className="show-kit-forge-section-heading">
          <div><p className="show-kit-forge-step">Local artifacts</p><h3 id="show-kit-pack-title">Import and export local show packs</h3></div>
          <span>
            {activeBank === null
              ? 'Import available · select a bank to export'
              : `Active bank: ${statusLabel(activeBank.status)}`}
          </span>
        </div>
        <div className="show-kit-forge-inline-fields">
          <label>Import package ID<input value={packName} pattern={SAFE_ARTIFACT_NAME.source} maxLength={96} autoCapitalize="none" onChange={(event) => setPackName(event.currentTarget.value.toLowerCase())} placeholder="my-show" /></label>
          <button
            type="button"
            disabled={actionDisabled || !validPackName}
            onClick={() =>
              void issue(
                { type: 'show_bank_import', pack_name: packName },
                'Import show pack',
                true,
                (ack) =>
                  ack.show_pack_import === undefined
                    ? 'Show-pack import accepted; waiting for authoritative show bank state.'
                    : `Imported ${ack.show_pack_import.package_id}: ${ack.show_pack_import.artifact_count} artifacts verified and ${ack.show_pack_import.write_count} files retained.`,
              )
            }
          >
            Import local pack
          </button>
          {activeBank === null ? (
            <p className="show-kit-forge-help">Select or create a bank before exporting. Import remains available for empty-workspace recovery.</p>
          ) : (
            <>
              <label>Export package ID<input value={artifactName} pattern={SAFE_ARTIFACT_NAME.source} maxLength={96} autoCapitalize="none" onChange={(event) => setArtifactName(event.currentTarget.value.toLowerCase())} placeholder="my-show" /></label>
              <button
                type="button"
                disabled={actionDisabled || !validArtifactName}
                onClick={() =>
                  void issue(
                    { type: 'show_bank_export', bank_id: activeBank.bank_id, artifact_name: artifactName, expected_revision: activeBank.revision },
                    'Export show pack',
                    true,
                    (ack) =>
                      ack.show_pack_export === undefined
                        ? 'Show-pack export completed beneath the configured server export root.'
                        : `Exported ${ack.show_pack_export.package_id} as ${ack.show_pack_export.directory_name}: ${ack.show_pack_export.artifact_count} files.`,
                  )
                }
              >
                Export {!stale && activeBank.readiness.show_ready ? 'show-ready' : 'draft'} local pack
              </button>
            </>
          )}
        </div>
        <p className="show-kit-forge-help">Lowercase package IDs are resolved beneath validated server import/export roots; the server adds <code>.show-pack</code>. Filesystem paths never cross WebSocket. Draft exports preserve their non-ready status.</p>
      </section>

      <PanelRenderer spec={readinessSpec} />
    </section>
  );
}
