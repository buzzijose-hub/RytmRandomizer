import { useEffect, useId, useState } from 'react';

import { isRovingKey, nextIndex } from '../../a11y/rovingTabindex';
import { useCockpitStore } from '../../state';
import type { PerformanceParameterControl } from '../../ws/protocol';
import { useCockpitClient } from '../context';
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID, type CockpitDeviceId } from '../devices';
import { parameterBlockers, parameterCellKey, parameterSelected, replaceParameterCells, selectableParameter } from '../parameterScopeModel';
import { useMutationParameters } from '../useMutationParameters';
import { useMutationTargets } from '../useMutationTargets';
import { usePadLocks } from '../usePadLocks';

import { PanelRenderer } from './PanelRenderer';
import './parameterScope.css';

/** Interactive extension of the canonical store-slice panel platform. */
export function MutationParametersPanel(): JSX.Element {
  const client = useCockpitClient();
  const [deviceId, setDeviceId] = useState<CockpitDeviceId>(RYTM_DEVICE_ID);
  const [item, setItem] = useState(1);
  const [page, setPage] = useState('');
  const [presetError, setPresetError] = useState<string | null>(null);
  const [presetPending, setPresetPending] = useState(false);
  const controls = useCockpitStore((state) => state.parameterControls);
  const ready = useCockpitStore((state) => state.mutationParametersReady);
  const connected = useCockpitStore((state) => state.connectionStatus === 'connected');
  const sessionGeneration = useCockpitStore((state) => state.sessionGeneration);
  const snapshot = useCockpitStore((state) => state.snapshot);
  const captures = useCockpitStore((state) => state.kitCaptures);
  const candidate = useCockpitStore((state) => state.previewCandidate);
  const bankState = useCockpitStore((state) => state.showBank);
  const bank = bankState?.banks.find((item) => item.bank_id === bankState.active_bank_id);
  const sourceEntry = bank?.entries.find((item) => item.rytm_source.snapshot_id === snapshot?.snapshot_id);
  const pairedCandidate = sourceEntry?.candidates.find((item) => item.candidate_id === candidate?.candidate_id);
  const { selection, replace } = useMutationParameters(deviceId);
  const targets = useMutationTargets(deviceId);
  const locks = usePadLocks(deviceId);
  const tabId = useId();
  const a4CaptureIdentity = captures.find((capture) => capture.device_id === ANALOG_FOUR_DEVICE_ID);
  const sourceSnapshotId = snapshot?.snapshot_id;
  const a4Fingerprint = a4CaptureIdentity?.fingerprint;
  const a4CapturedAt = a4CaptureIdentity?.captured_at;
  useEffect(() => {
    if (!connected || sessionGeneration === 0) return;
    const state = useCockpitStore.getState();
    state.invalidateParameterMetadata();
    let active = true;
    client.send({ type: 'get_mutation_parameters' }).then((ack) => {
      if (active && !ack.ok) state.appendOperatorLog({ level: 'error', message: `Parameter catalog refresh refused: ${ack.message ?? ack.error ?? 'command rejected'}` });
    }).catch((error: unknown) => {
      if (active) state.appendOperatorLog({ level: 'error', message: `Parameter catalog refresh failed: ${error instanceof Error ? error.message : String(error)}` });
    });
    return () => { active = false; };
  }, [a4CapturedAt, a4Fingerprint, client, connected, sessionGeneration, sourceSnapshotId]);
  const deviceControls = controls.filter((control) => control.device_id === deviceId);
  const items = [...new Set(deviceControls.map((control) => control.item_id))];
  const currentItem = items.includes(item) ? item : (items[0] ?? 1);
  const itemControls = deviceControls.filter((control) => control.item_id === currentItem);
  const pages = [...new Set(itemControls.map((control) => control.page))];
  const currentPage = pages.includes(page) ? page : (pages[0] ?? '');
  const visible = itemControls.filter((control) => control.page === currentPage);
  const locked = locks.isLocked(currentItem);
  const targeted = targets.isTargeted(currentItem);
  const disabled = !ready || !connected || presetPending;
  const unit = deviceId === RYTM_DEVICE_ID ? 'Pad' : 'Track';
  const eligible = visible.filter(selectableParameter);
  const scopeLabel = selection === null ? 'All eligible controls (legacy)' : `${selection.length} explicit cells`;
  const sourceIdentity = deviceId === RYTM_DEVICE_ID ? snapshot?.snapshot_id : captures.find((capture) => capture.device_id === deviceId)?.fingerprint ?? sourceEntry?.analog_four_source.fingerprint;

  const setPageSelection = (selected: boolean): void => {
    replace(replaceParameterCells(selection, deviceControls, visible, selected));
  };

  const applyPreset = async (): Promise<void> => {
    useCockpitStore.getState().invalidateMutationContext();
    setPresetError(null);
    setPresetPending(true);
    try {
      const ack = await client.send({ type: 'set_rehearsal_preset', preset_id: 'rytm_pad2_common' });
      if (!ack.ok) throw new Error(ack.message ?? ack.error ?? 'Preset refused.');
      setDeviceId(RYTM_DEVICE_ID);
      setItem(2);
      setPage('FILTER');
      setPage('');
    } catch (error) {
      setPresetError(error instanceof Error ? error.message : String(error));
    } finally {
      setPresetPending(false);
    }
  };

  const proposal = (control: PerformanceParameterControl): number | undefined => {
    if (deviceId === ANALOG_FOUR_DEVICE_ID) {
      const value = pairedCandidate?.analog_four_candidate.values.find((item) => item.track_id === control.item_id && (item.parameter === control.parameter_key || (item.parameter === 'filter1_frequency' && control.parameter_key === 'Filter1 Frequency')));
      return value === undefined ? undefined : 'encoded_native' in value ? value.encoded_native : value.encoded_unsigned_8_8;
    }
    if (candidate?.source_snapshot_id !== snapshot?.snapshot_id) return undefined;
    return candidate?.pad_deltas.find((delta) => delta.pad_id === control.item_id)?.proposed_params[control.parameter_key];
  };

  return (
    <section className="cockpit-panel-stack parameter-scope" aria-label="Mutation parameter scope" data-testid="mutation-parameters-panel">
      <PanelRenderer spec={{
        panel_id: 'mutation-parameters', title: 'Mutation parameter scope',
        status_badges: [{ label: scopeLabel, tone: 'neutral', icon: '•' }],
        sections: [], required_actions: [], blocked_actions: [],
        safety_lines: [deviceId === ANALOG_FOUR_DEVICE_ID ? 'A4 offline only; SEND blocked' : 'Protection and pad locks remain mandatory'],
      }} />
      <div className="cockpit-panel-controls parameter-scope-toolbar">
        <label>Device<select aria-label="Parameter scope device" value={deviceId} disabled={presetPending}
          onChange={(event) => { setDeviceId(event.currentTarget.value as CockpitDeviceId); setItem(1); setPage(''); }}>
          <option value={RYTM_DEVICE_ID}>Analog Rytm</option>
          <option value={ANALOG_FOUR_DEVICE_ID}>Analog Four (offline)</option>
        </select></label>
        <label>{unit}<select aria-label="Parameter scope item" value={currentItem} disabled={items.length === 0 || presetPending}
          onChange={(event) => { setItem(Number(event.currentTarget.value)); setPage(''); }}>
          {items.length === 0 ? <option value={1}>Source unavailable</option> : items.map((id) => <option key={id} value={id}>{unit} {id}</option>)}
        </select></label>
        <label className="parameter-scope-check"><input type="checkbox" checked={targets.hasExplicitTargets && targeted} disabled={disabled || items.length === 0}
          onChange={() => targets.toggleTarget(currentItem)} />Explicit target {unit.toLowerCase()}</label>
        <label className="parameter-scope-check"><input type="checkbox" checked={locked} disabled={disabled || items.length === 0}
          onChange={() => locks.toggleLock(currentItem)} />Lock {unit.toLowerCase()}</label>
        <button type="button" disabled={disabled} onClick={() => void applyPreset()}>Pad 2 rehearsal</button>
        <span className="parameter-scope-warning">Physical validation pending</span>
      </div>
      {!ready ? <p>Canonical parameter scope unavailable. Reconnect to a scope-capable sidecar.</p> : deviceControls.length === 0 ? <p>No canonical source controls available for this device.</p> : <>
        <p className="parameter-scope-source">{unit} {currentItem} / {itemControls[0]!.machine} / Source <code>{sourceIdentity ?? 'not available'}</code> / Targets: {targets.hasExplicitTargets ? [...targets.targets].join(', ') : 'all (legacy)'}</p>
        <div className="cockpit-panel-controls parameter-scope-tabs" role="tablist" aria-label="Parameter pages">
          {pages.map((name, index) => <button key={name} type="button" role="tab" id={`${tabId}-tab-${index}`}
            aria-selected={name === currentPage} aria-controls={`${tabId}-page`} tabIndex={name === currentPage ? 0 : -1}
            onClick={() => setPage(name)} onKeyDown={(event) => {
              if (!isRovingKey(event.key)) return;
              event.preventDefault();
              const next = nextIndex(index, pages.length, event.key);
              setPage(pages[next]!);
              event.currentTarget.parentElement!.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]!.focus();
            }}>{name}</button>)}
        </div>
        <div role="tabpanel" id={`${tabId}-page`} aria-labelledby={`${tabId}-tab-${pages.indexOf(currentPage)}`}>
          <div className="cockpit-panel-controls parameter-scope-actions">
            <button type="button" disabled={disabled || locked || !targeted || eligible.length === 0} onClick={() => setPageSelection(true)}>Select page</button>
            <button type="button" disabled={disabled || eligible.length === 0} onClick={() => setPageSelection(false)}>Clear page</button>
            <button type="button" disabled={disabled} onClick={() => replace(deviceControls.filter(selectableParameter).map(({ item_id, parameter_key }) => ({ item_id, parameter_key })))}>Select all eligible</button>
            <button type="button" disabled={disabled} onClick={() => replace([])}>Select none</button>
            <button type="button" disabled={disabled} onClick={() => replace(null)}>Legacy all</button>
          </div>
          <div className="parameter-scope-rows">
            {visible.map((control) => {
              const supported = selectableParameter(control);
              const reasons = parameterBlockers(control, locked, targeted);
              const proposed = proposal(control);
              return <div className="parameter-scope-row" key={parameterCellKey(control)} data-testid={`parameter-row-${control.item_id}-${control.parameter_key}`}>
                <label className="parameter-scope-selection"><input type="checkbox"
                  aria-label={`Mutate ${unit} ${currentItem} ${control.name}`} checked={supported && parameterSelected(selection, control)}
                  disabled={disabled || locked || !targeted || !supported}
                  onChange={(event) => replace(replaceParameterCells(selection, deviceControls, [control], event.currentTarget.checked))} />
                  <span><strong>{control.name}</strong><code>{control.parameter_key}</code></span></label>
                <div className="parameter-scope-values"><span>Source {control.display_value ?? control.value ?? 'unavailable'}</span>
                  <span>Native {control.value ?? 'unavailable'} / {control.native_precision}</span>
                  <span>Range {control.minimum ?? '?'} to {control.maximum ?? '?'}</span>
                  <span>Proposal {proposed === undefined ? 'not generated' : proposed}</span></div>
                <div className="parameter-scope-evidence"><span>{control.evidence_level.replaceAll('_', ' ')}</span>
                  <span>{control.send_supported ? 'Conditional guarded send' : 'Live send blocked'}</span>
                  {reasons.map((reason) => <span key={reason}>{reason}</span>)}</div>
              </div>;
            })}
          </div>
        </div>
      </>}
      {presetError !== null && <p role="alert">{presetError}</p>}
    </section>
  );
}
