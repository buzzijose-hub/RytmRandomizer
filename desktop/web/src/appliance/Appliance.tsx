import { useEffect, useRef, useState } from 'react';

import { useCockpitStore } from '../state';
import { resolveArmSecret, type CockpitClient } from '../ws/client';
import type { ApplianceCandidate, ApplianceDeviceId, ApplianceLane, ApplianceScope, ApplianceState, ApplianceTarget } from '../ws/protocol';

import { TouchDialog } from './TouchDialog';
import { TouchNumber } from './TouchNumber';
import { useAppliance, type ApplianceController } from './useAppliance';
import { usePhysicalControls } from './usePhysicalControls';
import './appliance.css';

type Page = 'perform' | 'rytm' | 'a4' | 'both' | 'history' | 'more';
type Tool = 'profiles' | 'capture' | 'diagnostics';
const DEVICE_LABELS: Readonly<Record<ApplianceDeviceId, string>> = { analog_rytm_mk2: 'RYTM', analog_four_mk2: 'A4' };
const DEVICE_IDS: readonly ApplianceDeviceId[] = ['analog_rytm_mk2', 'analog_four_mk2'];
const PAD_ORDER = [9, 10, 11, 12, 5, 6, 7, 8, 1, 2, 3, 4] as const;

function readable(reason: string): string { return reason.replaceAll('_', ' '); }
function toggle<T extends string | number>(values: readonly T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}
function percent(depth: number): number { return Math.round(depth * 100); }
function selectedDevices(target: ApplianceTarget): readonly ApplianceDeviceId[] {
  return target === 'both' ? DEVICE_IDS : [target === 'rytm' ? 'analog_rytm_mk2' : 'analog_four_mk2'];
}
function scopeAllowsMutation(state: ApplianceState): boolean {
  return state.master_depth > 0 && selectedDevices(state.target).every((id) => {
    const lane = state.lanes[id];
    return lane.scope.page_ids.length > 0 && lane.scope.target_ids.some((target) => !lane.scope.locked_ids.includes(target));
  });
}

interface LaneProps {
  lane: ApplianceLane;
  disabled: boolean;
  onScope: (patch: Partial<ApplianceScope>) => void;
  compact?: boolean;
  revision?: number;
}

function TargetGrid({ lane, disabled, onScope, compact = false }: LaneProps): JSX.Element {
  const isRytm = lane.device_id === 'analog_rytm_mk2';
  const order: readonly number[] = isRytm ? PAD_ORDER : [1, 2, 3, 4];
  return (
    <div className={`appliance-target-grid ${isRytm ? 'rytm' : 'a4'} ${compact ? 'compact' : ''}`} aria-label={`${DEVICE_LABELS[lane.device_id]} ${isRytm ? 'pad' : 'track'} targets`}>
      {order.map((track) => {
        const locked = lane.scope.locked_ids.includes(track);
        const selected = lane.scope.target_ids.includes(track);
        return <button type="button" key={track} disabled={disabled} className={`${selected ? 'selected' : ''} ${locked ? 'locked' : ''}`} aria-pressed={selected} aria-label={`${isRytm ? 'Pad' : 'Track'} ${track}, ${selected ? 'selected' : 'not targeted'}${locked ? ', protected' : ''}`} onClick={() => onScope({ target_ids: toggle(lane.scope.target_ids, track) })}>
          <strong>{isRytm ? 'P' : 'T'}{String(track).padStart(isRytm ? 2 : 1, '0')}</strong><span>{locked ? 'LOCKED' : selected ? 'TARGET' : 'OFF'}</span>
        </button>;
      })}
    </div>
  );
}

function LaneEditor({ lane, disabled, onScope, revision }: LaneProps): JSX.Element {
  const [section, setSection] = useState<'targets' | 'pages' | 'protect'>('targets');
  const [track, setTrack] = useState(lane.reference_track_id ?? 1);
  const pages = [...new Set(lane.parameters.map((parameter) => parameter.page))];
  const [filterPage, setFilterPage] = useState('');
  const visiblePage = pages.includes(filterPage) ? filterPage : (pages[0] ?? '');
  const count = lane.device_id === 'analog_rytm_mk2' ? 12 : 4;
  const allIds = Array.from({ length: count }, (_, i) => i + 1);
  return (
    <section className="appliance-lane-editor">
      <div className="appliance-section-heading"><h2>{DEVICE_LABELS[lane.device_id]} SCOPE</h2><span>{lane.scope.target_ids.length} TARGET / {lane.scope.locked_ids.length} LOCK</span></div>
      <div className="appliance-subnav" aria-label="Scope controls">
        {(['targets', 'pages', 'protect'] as const).map((item) => <button type="button" key={item} aria-pressed={section === item} onClick={() => setSection(item)}>{item.toUpperCase()}</button>)}
      </div>
      {section === 'targets' && <div className="appliance-target-editor">
        <div><TargetGrid lane={lane} disabled={disabled} onScope={onScope} /><div className="appliance-inline-actions"><button type="button" disabled={disabled} onClick={() => onScope({ target_ids: allIds })}>ALL {count}</button><button type="button" disabled={disabled} onClick={() => onScope({ target_ids: [] })}>NONE</button></div><p>OFF is excluded. An empty selection targets nothing.</p></div>
        <div className="appliance-track-rules"><label>EDIT {lane.device_id === 'analog_rytm_mk2' ? 'PAD' : 'TRACK'}<select aria-label="Track to edit" value={track} onChange={(event) => setTrack(Number(event.target.value))}>{allIds.map((id) => <option key={id} value={id}>{lane.device_id === 'analog_rytm_mk2' ? 'PAD' : 'TRACK'} {id}</option>)}</select></label>
          <TouchNumber key={`${track}:${revision}`} label={`TRACK ${track}`} value={percent(lane.scope.track_depths[String(track)] ?? 1)} disabled={disabled} onChange={(value) => onScope({ track_depths: { ...lane.scope.track_depths, [String(track)]: value / 100 } })} />
          <button type="button" className="appliance-lock" aria-pressed={lane.scope.locked_ids.includes(track)} disabled={disabled} onClick={() => onScope({ locked_ids: toggle(lane.scope.locked_ids, track) })}>{lane.scope.locked_ids.includes(track) ? 'UNLOCK' : 'PROTECT'} {lane.device_id === 'analog_rytm_mk2' ? 'PAD' : 'TRACK'} {track}</button>
          <p>Locks deny this app&apos;s writes. Instrument modulation and OXI keep operating.</p>
        </div>
      </div>}
      {section === 'pages' && <div className="appliance-page-list">{pages.map((page) => <article key={page} className="appliance-page-rule"><button type="button" aria-pressed={lane.scope.page_ids.includes(page)} disabled={disabled} onClick={() => onScope({ page_ids: toggle(lane.scope.page_ids, page) })}><span>{page}</span><strong>{lane.scope.page_ids.includes(page) ? 'TARGET' : 'OFF'}</strong></button><TouchNumber key={`${page}:${revision}`} label={page} value={percent(lane.scope.page_depths[page] ?? 1)} disabled={disabled} onChange={(value) => onScope({ page_depths: { ...lane.scope.page_depths, [page]: value / 100 } })} /></article>)}<p>Page families come from the device catalog. Master × track × page depth governs the next roll.</p></div>}
      {section === 'protect' && <div><label className="appliance-page-filter">PARAMETER PAGE<select aria-label="Parameter page" value={visiblePage} onChange={(event) => setFilterPage(event.target.value)}>{pages.map((page) => <option value={page} key={page}>{page}</option>)}</select></label><p>Parameter protection applies to all chosen tracks. Categorical and unsupported policies always win.</p><div className="appliance-parameter-list">{lane.parameters.filter((parameter) => parameter.page === visiblePage).map((parameter) => {
        const locked = parameter.categorical === true || lane.scope.parameter_locks.includes(parameter.parameter_id);
        const value = parameter.values_by_track[String(track)];
        const display = parameter.display_values_by_track?.[String(track)] ?? value;
        return <article key={parameter.parameter_id}><div><strong>{parameter.parameter}{parameter.machine_key === null ? '' : ` / ${parameter.machine_key}`}</strong><small>{parameter.categorical === true ? 'CATEGORICAL / NO VALIDATED MUTATION' : parameter.default_protected ? 'DEFAULT PROTECTION POLICY' : parameter.blockers.length ? parameter.blockers.map(readable).join(' · ') : 'CATALOG POLICY'}{value !== undefined ? ` · TRACK ${track}: ${display}` : ` · TRACK ${track}: VALUE UNKNOWN`}{parameter.protection_reasons?.length ? ` · ${parameter.protection_reasons.map(readable).join(' · ')}` : ''}</small></div><button type="button" disabled={disabled || parameter.categorical === true} aria-pressed={locked} aria-label={`${locked ? 'Unlock' : 'Protect'} ${parameter.parameter}`} onClick={() => onScope({ parameter_locks: toggle(lane.scope.parameter_locks, parameter.parameter_id) })}>{locked ? 'LOCKED' : 'PROTECT'}</button></article>;
      })}</div></div>}
    </section>
  );
}

function Provenance({ lane }: { lane: ApplianceLane }): JSX.Element {
  const source = lane.provenance;
  return <article className="appliance-provenance"><div><strong>{DEVICE_LABELS[lane.device_id]}</strong><span>{source.source_type === 'simulation' ? 'SIMULATED SOURCE' : source.source_type === 'saved_kit' ? 'SAVED KIT CAPTURE' : 'NO CAPTURE'}</span></div><h3>{source.kit_name ?? 'NO KNOWN KIT'}</h3><p>{source.fingerprint === null ? 'Identity unknown' : `Fingerprint ${source.fingerprint}`}</p><p>Working RAM unverified. {lane.blocked_reasons.map(readable).join(' · ')}</p></article>;
}

function CandidateDiff({ candidate }: { candidate: ApplianceCandidate | null }): JSX.Element {
  if (candidate === null) return <div className="appliance-empty"><span>01 / CHOOSE TARGETS</span><span>02 / SET DEPTH + PROTECTION</span><span>03 / MUTATE TO PREVIEW</span><p>One roll. No background mutation.</p></div>;
  return <div className="appliance-diff"><div className="appliance-section-heading"><h3>EXACT NEXT APPLY</h3><span>{candidate.changes.length} CHANGES</span></div>{candidate.changes.length === 0 ? <p>No eligible changes. Zero depth and locks produce no writes.</p> : <table><thead><tr><th>TRACK / PARAMETER</th><th>BEFORE</th><th>AFTER</th></tr></thead><tbody>{candidate.changes.map((change) => <tr key={`${change.device_id}:${change.track_id}:${change.parameter_id}`}><th>{DEVICE_LABELS[change.device_id]} {change.track_id} / {change.parameter}</th><td>{change.before_display ?? change.before}</td><td>{change.after_display ?? change.after}</td></tr>)}</tbody></table>}<p>{candidate.blocked_reasons.map(readable).join(' · ')}</p></div>;
}

function ProfileTools({ state, controller }: { state: ApplianceState; controller: ApplianceController }): JSX.Element {
  const [name, setName] = useState('PERFORMANCE 1');
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [transferNotice, setTransferNotice] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const exportProfile = async (profileName: string): Promise<void> => {
    const ack = await controller.execute('profile_export', { name: profileName });
    if (!ack?.ok || ack.document === undefined) { setTransferNotice('Profile export refused or unavailable.'); return; }
    const url = URL.createObjectURL(new Blob([JSON.stringify(ack.document, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = 'rytm-appliance-profile.json'; link.click(); URL.revokeObjectURL(url);
    setTransferNotice('Validated profile document exported. Arming and live authority are excluded.');
  };
  return <section><div className="appliance-section-heading"><h2>RULE PROFILES</h2><span>{state.profiles.length} SAVED</span></div><p>Profiles save scope, depth and protection with device/capture associations. Recall never arms an output.</p><div className="appliance-inline-actions"><button type="button" disabled={controller.busy} onClick={() => setEditing(true)}>NAME: {name}</button><button type="button" disabled={controller.busy || name.trim() === ''} onClick={() => void controller.execute('profile_save', { name })}>SAVE RULES</button><button type="button" disabled={controller.busy} onClick={() => fileRef.current?.click()}>IMPORT</button></div><input ref={fileRef} type="file" accept="application/json,.json" hidden aria-label="Import profile document" onChange={(event) => {
    const file = event.currentTarget.files?.[0]; if (file === undefined) return;
    if (file.size > 65536) { setTransferNotice('Profile import exceeds 64 KiB.'); return; }
    void file.text().then(async (text) => {
      let document: unknown;
      try { document = JSON.parse(text); } catch { setTransferNotice('Profile JSON is corrupt. Existing rules are unchanged.'); return; }
      await controller.execute('profile_import', { document });
    }).catch(() => setTransferNotice('Profile file could not be read.'));
    event.currentTarget.value = '';
  }} />
    {state.profiles.length === 0 ? <p>No saved rules. Set targets before saving a profile.</p> : <div className="appliance-profile-list">{state.profiles.map((profile) => <article key={profile.name}><h3>{profile.name}</h3><p>{profile.association.device_ids.join(' + ')} / {Object.values(profile.association.fingerprints).map((fingerprint) => fingerprint ?? 'UNKNOWN KIT').join(' + ')}</p><div className="appliance-inline-actions"><button type="button" disabled={controller.busy} onClick={() => void controller.execute('profile_load', { name: profile.name })}>RECALL</button><button type="button" disabled={controller.busy} onClick={() => void exportProfile(profile.name)}>EXPORT</button><button type="button" disabled={controller.busy} onClick={() => setDeleting(profile.name)}>DELETE</button></div></article>)}</div>}
    {transferNotice && <p role="status">{transferNotice}</p>}
    {editing && <TouchDialog title="PROFILE NAME" onClose={() => setEditing(false)}><output className="appliance-name">{name || 'EMPTY'}</output><div className="appliance-keyboard">{[...'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'].map((key) => <button type="button" key={key} disabled={name.length >= 48} onClick={() => setName((current) => current + key)}>{key}</button>)}</div><div className="appliance-inline-actions"><button type="button" onClick={() => setName((current) => current.slice(0, -1))}>BACKSPACE</button><button type="button" onClick={() => setName('')}>CLEAR</button><button type="button" disabled={name.length >= 48} onClick={() => setName((current) => current + ' ')}>SPACE</button><button type="button" className="appliance-primary" disabled={name.trim() === ''} onClick={() => setEditing(false)}>DONE</button></div></TouchDialog>}
    {deleting !== null && <TouchDialog title="DELETE PROFILE" onClose={() => setDeleting(null)}><p>Delete saved rules “{deleting}”? Current scope and device state stay in this session.</p><div className="appliance-dialog-actions"><button type="button" onClick={() => setDeleting(null)}>CANCEL</button><button type="button" onClick={() => { void controller.execute('profile_delete', { name: deleting }); setDeleting(null); }}>DELETE {deleting}</button></div></TouchDialog>}
  </section>;
}

function CaptureTools({ state, controller }: { state: ApplianceState; controller: ApplianceController }): JSX.Element {
  const [device, setDevice] = useState<ApplianceDeviceId>('analog_rytm_mk2');
  const [inputs, setInputs] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [enabled, setEnabled] = useState(false);
  const scan = async (): Promise<void> => {
    const ack = await controller.command({ type: 'list_capture_inputs', device_id: device });
    if (ack?.ok) { setInputs(ack.capture_inputs ?? []); setEnabled(ack.capture_enabled ?? false); setInput(''); }
  };
  const capture = async (): Promise<void> => {
    const ack = await controller.command({ type: 'capture_current_kit', device_id: device, input_port: input }, 125_000);
    if (ack?.ok) await controller.execute('state');
  };
  return <section><h2>CONNECTION / CAPTURE</h2><div className="appliance-device-choice">{DEVICE_IDS.map((id) => <button type="button" key={id} aria-pressed={device === id} disabled={controller.busy} onClick={() => { setDevice(id); setInputs([]); setInput(''); setEnabled(false); }}>{DEVICE_LABELS[id]}</button>)}</div><Provenance lane={state.lanes[device]} /><div className="appliance-inline-actions"><button type="button" disabled={controller.busy} onClick={() => void scan()}>SCAN INPUTS</button><button type="button" disabled={controller.busy} onClick={() => void controller.execute('state')}>RESYNC APP STATE</button></div><label>MIDI INPUT<select aria-label="Exact capture input" value={input} disabled={controller.busy} onChange={(event) => setInput(event.target.value)}><option value="">CHOOSE EXACT INPUT</option>{inputs.map((port, index) => <option key={`${port}:${index}`} value={port}>{port}</option>)}</select></label><button type="button" className="appliance-primary" disabled={!enabled || input === '' || controller.busy || inputs.filter((port) => port === input).length !== 1} onClick={() => void capture()}>{controller.busy ? 'WAITING FOR INPUT / COMMAND' : 'LISTEN FOR KIT CAPTURE'}</button>{!enabled && <p className="appliance-blocker">{state.mode === 'simulation' ? 'SIMULATION: hardware capture is disabled.' : 'Capture input is unavailable. Scan inputs or launch with the passive capture provider.'}</p>}<p>Input only. On the selected instrument, send its KIT via SYSEX DUMP. No automatic request or hardware save is sent.</p><p>A saved-KIT capture does not prove unsaved front-panel values. RESYNC APP STATE only refreshes the software projection. NEW ANCHOR separately adopts its known baseline.</p></section>;
}

function DiagnosticsTools({ state, controller, client }: { state: ApplianceState; controller: ApplianceController; client: CockpitClient }): JSX.Element {
  const diagnostics = useCockpitStore((store) => store.diagnostics);
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false);
  return <section><h2>DIAGNOSTICS / SETTINGS</h2><div className="appliance-inline-actions"><button type="button" disabled={controller.busy} onClick={() => void controller.command({ type: 'diagnostics' }).then((ack) => { if (ack?.diagnostics) useCockpitStore.getState().setDiagnostics(ack.diagnostics); })}>READ HEALTH</button><button type="button" onClick={() => client.retryNow()}>RETRY CONNECTION</button><button type="button" aria-pressed={reducedMotion} onClick={() => { const next = !reducedMotion; setReducedMotion(next); document.documentElement.dataset.applianceMotion = next ? 'reduced' : 'system'; }}>MOTION {reducedMotion ? 'REDUCED' : 'SYSTEM'}</button><a href="#/">STUDIO VIEW</a></div><dl className="appliance-details"><div><dt>TRANSPORT</dt><dd>{client.getStatus().toUpperCase()}</dd></div><div><dt>SESSION</dt><dd>{state.mode.toUpperCase()} / REV {state.revision}</dd></div><div><dt>RESTORATION</dt><dd>LOCAL HISTORY ONLY / HARDWARE UNVERIFIED</dd></div><div><dt>PLATFORM</dt><dd>{diagnostics?.platform ?? 'NOT QUERIED'}</dd></div><div><dt>DRIVER</dt><dd>{diagnostics?.driver_hint ?? 'NOT QUERIED'}</dd></div></dl><p>{state.blocked_reasons.map(readable).join(' · ') || 'No global blocker reported. Per-device evidence still governs each action.'}</p>{diagnostics?.journal.map((entry) => <article className="appliance-diagnostic-row" key={`${entry.fingerprint}:${entry.ts}`}><strong>{entry.message}</strong><small>{entry.fingerprint}</small></article>)}<p>Optional physical controls use these same commands. A configured hardware adapter is required; touchscreen operation is complete without it.</p></section>;
}

export function Appliance({ client }: { client: CockpitClient }): JSX.Element {
  const controller = useAppliance(client);
  const rootRef = useRef<HTMLElement>(null);
  const { state, busy } = controller;
  const connection = useCockpitStore((store) => store.connection);
  const [page, setPage] = useState<Page>('perform');
  const [tool, setTool] = useState<Tool>('profiles');
  const [confirmation, setConfirmation] = useState<{ kind: 'apply' | 'anchor' | 'arm'; revision: number; candidateId?: string } | null>(null);
  const [output, setOutput] = useState('');
  const [targetDialog, setTargetDialog] = useState<ApplianceDeviceId | null>(null);
  const outputOccurrences = connection?.available_outputs.filter((port) => port === output).length ?? 0;
  const confirmationCurrent = confirmation !== null && state !== null && confirmation.revision === state.revision && (confirmation.kind !== 'apply' || confirmation.candidateId === state.candidate?.candidate_id);
  useEffect(() => { if (confirmation !== null && !confirmationCurrent) { setConfirmation(null); setOutput(''); } }, [confirmation, confirmationCurrent]);
  const updateScope = (payload: Record<string, unknown>): void => { void controller.execute('scope', payload); };
  const laneScope = (id: ApplianceDeviceId, patch: Partial<ApplianceScope>): void => updateScope({ lanes: { [id]: patch } });
  const canMutate = state !== null && scopeAllowsMutation(state);
  const requestMutation = (): void => { const current = controller.getState(); if (current !== null && scopeAllowsMutation(current)) void controller.execute('mutate'); };
  const requestUndo = (): void => { if (controller.getState()?.history.can_undo) void controller.execute('undo'); };
  const requestAnchor = (): void => { const current = controller.getState(); if (current !== null && !controller.isBusy()) setConfirmation({ kind: 'anchor', revision: current.revision }); };
  usePhysicalControls(client, rootRef, { enabled: () => controller.getState() !== null && !controller.isBusy(), mutate: requestMutation, undo: requestUndo, anchor: requestAnchor });
  const canApply = state !== null && state.candidate !== null && state.candidate.changes.length > 0 && (state.mode === 'simulation' || (state.armed && state.candidate.live_ready));
  const choosePage = (next: Page): void => {
    setPage(next);
    if (state !== null && (next === 'rytm' || next === 'a4' || next === 'both') && next !== state.target) updateScope({ target: next });
  };
  const apply = async (): Promise<void> => {
    const current = controller.getState();
    if (current === null || current.candidate === null || confirmation === null || confirmation.revision !== current.revision || confirmation.candidateId !== current.candidate.candidate_id || (current.mode === 'production' && (!current.armed || !current.candidate.live_ready))) return;
    const candidate = current.candidate;
    setConfirmation(null);
    await controller.execute('apply', { candidate_id: candidate.candidate_id, confirmed: true, ...(candidate.send_plan_id === null ? {} : { send_plan_id: candidate.send_plan_id }) });
  };
  const arm = async (): Promise<void> => {
    const secret = resolveArmSecret();
    const current = controller.getState();
    const available = useCockpitStore.getState().connection?.available_outputs ?? [];
    if (!confirmationCurrent || current?.mode !== 'production' || current.revision !== confirmation?.revision || secret === null || output === '' || available.filter((port) => port === output).length !== 1) return;
    setConfirmation(null);
    const ack = await controller.command({ type: 'arm', arm_token: secret, confirm: true, port_name: output });
    setOutput('');
    if (ack?.ok) await controller.execute('state');
  };
  const disarm = async (): Promise<void> => { setConfirmation(null); const ack = await controller.command({ type: 'disarm' }); if (ack?.ok) await controller.execute('state'); };
  return <main ref={rootRef} className="appliance" data-testid="appliance" aria-label="RytmRandomizer performance appliance">
    <header className="appliance-top"><a href="#/appliance" aria-label="RytmRandomizer appliance home" onClick={() => setPage('perform')}><span className="appliance-logo" aria-hidden="true">RR</span><span>RYTM RANDOMIZER<small>PERFORMANCE APPLIANCE</small></span></a><span className={`appliance-mode ${state?.mode === 'simulation' ? 'simulation' : ''}`}>{state === null ? 'DISCONNECTED' : state.mode === 'simulation' ? 'SIMULATION / NO MIDI' : state.armed ? 'OUTPUT ARMED' : 'PASSIVE / DISARMED'}</span><button type="button" className="appliance-disarm" disabled={state === null || (!state.armed && (busy || state.mode === 'simulation'))} onClick={() => state?.armed ? void disarm() : state !== null && setConfirmation({ kind: 'arm', revision: state.revision })}>{state?.armed ? 'DISARM' : 'ARM…'}</button></header>
    <div className="appliance-content" key={page}>
      {state === null ? <section className="appliance-unavailable"><h1>PASSIVE / WAITING</h1><p>Connect the authenticated sidecar to receive current device catalogs and session state.</p><button type="button" onClick={() => client.retryNow()}>RETRY CONNECTION</button><a href="#/">OPEN STUDIO</a></section> : <>
        {state.mode === 'simulation' && (state.target !== 'rytm' || page === 'a4' || page === 'both') && <p className="appliance-simulation-values">A4 SIMULATED 7-BIT VALUES / 0–127 / NOT NATIVE DISPLAY PRECISION</p>}
        {page === 'perform' && <div className="appliance-perform"><section><div className="appliance-section-heading"><h1>HOME / PERFORM</h1><span>REV {state.revision}</span></div><div className="appliance-device-choice" aria-label="Mutation device selection">{(['rytm', 'a4', 'both'] as const).map((target) => <button type="button" key={target} disabled={busy} aria-pressed={state.target === target} onClick={() => updateScope({ target })}>{target.toUpperCase()}</button>)}</div><div className="appliance-performance-targets">{selectedDevices(state.target).map((id) => <section key={id}><div className="appliance-section-heading"><h2>{DEVICE_LABELS[id]}</h2><button type="button" className="appliance-compact-target-button" onClick={() => setTargetDialog(id)}>{DEVICE_LABELS[id]} TARGETS</button></div><TargetGrid lane={state.lanes[id]} disabled={busy} onScope={(patch) => laneScope(id, patch)} compact={state.target === 'both'} /></section>)}</div></section><section className="appliance-perform-right"><TouchNumber key={state.revision} label="MASTER" value={percent(state.master_depth)} disabled={busy} onChange={(value) => updateScope({ master_depth: value / 100 })} /><CandidateDiff candidate={state.candidate} />{state.last_receipt !== null && <p className="appliance-receipt">{readable(state.last_receipt.status).toUpperCase()} / {state.last_receipt.sent_count} OF {state.last_receipt.expected_count}<br />HARDWARE ACCEPTANCE UNVERIFIED</p>}</section></div>}
        {(page === 'rytm' || page === 'a4') && <LaneEditor key={page} lane={state.lanes[page === 'rytm' ? 'analog_rytm_mk2' : 'analog_four_mk2']} disabled={busy} revision={state.revision} onScope={(patch) => laneScope(page === 'rytm' ? 'analog_rytm_mk2' : 'analog_four_mk2', patch)} />}
        {page === 'both' && <section><div className="appliance-section-heading"><h1>LINKED BOTH</h1><TouchNumber key={state.revision} label="MASTER" value={percent(state.master_depth)} disabled={busy} onChange={(value) => updateScope({ master_depth: value / 100 })} /></div><p>Both lanes preflight before apply. A blocked lane blocks the linked action. Cross-device sends are not atomic.</p><div className="appliance-linked-lanes">{DEVICE_IDS.map((id) => <section key={id}><Provenance lane={state.lanes[id]} /><TargetGrid lane={state.lanes[id]} disabled={busy} onScope={(patch) => laneScope(id, patch)} /></section>)}</div><CandidateDiff candidate={state.candidate} /></section>}
        {page === 'history' && <section><h1>ANCHOR / HISTORY</h1><div className="appliance-history-overview"><strong>{state.history.count}<small>LOCAL STEPS</small></strong><span>{state.history.anchor_captured ? 'ANCHOR ADOPTED' : 'NO LOCAL ANCHOR'}</span></div><p>Local undo/redo selects precise software states. Hardware restoration remains unsupported; these controls do not restore an instrument or an entire kit.</p><div className="appliance-inline-actions"><button type="button" disabled={busy || !state.history.can_undo} onClick={requestUndo}>LOCAL UNDO</button><button type="button" disabled={busy || !state.history.can_redo} onClick={() => void controller.execute('redo')}>LOCAL REDO</button><button type="button" disabled={busy || !state.history.anchor_captured} onClick={() => void controller.execute('return_anchor')}>RETURN TO ANCHOR / LOCAL</button><button type="button" disabled={busy} onClick={requestAnchor}>NEW ANCHOR…</button></div><div className="appliance-linked-lanes">{DEVICE_IDS.map((id) => <Provenance key={id} lane={state.lanes[id]} />)}</div></section>}
        {page === 'more' && <div><div className="appliance-subnav">{(['profiles', 'capture', 'diagnostics'] as const).map((item) => <button type="button" key={item} aria-pressed={tool === item} onClick={() => setTool(item)}>{item.toUpperCase()}</button>)}</div>{tool === 'profiles' ? <ProfileTools state={state} controller={controller} /> : tool === 'capture' ? <CaptureTools state={state} controller={controller} /> : <DiagnosticsTools state={state} controller={controller} client={client} />}</div>}
      </>}
    </div>
    <div className="appliance-notice" role="status"><span>{busy ? 'BUSY' : 'STATUS'}</span><p>{!canMutate && state !== null && state.candidate === null ? `No mutation eligible: ${state.master_depth === 0 ? 'master depth zero' : 'choose unlocked tracks and pages'}. ` : ''}{controller.notice}</p></div>
    <div className="appliance-action-row"><button type="button" className="appliance-mutate" disabled={busy || !canMutate} onClick={requestMutation}>MUTATE</button><button type="button" className="appliance-primary" disabled={busy || !canApply} onClick={() => state?.candidate && setConfirmation({ kind: 'apply', revision: state.revision, candidateId: state.candidate.candidate_id })}>{state?.mode === 'simulation' ? 'LOCAL APPLY…' : 'APPLY…'}</button><button type="button" disabled={busy || !state?.history.can_undo} onClick={requestUndo}>UNDO / LOCAL</button><button type="button" disabled={busy || state === null} onClick={() => { setPage('more'); setTool('capture'); }}>CAPTURE / RESYNC</button></div>
    <nav className="appliance-nav" aria-label="Appliance pages">{([['perform', 'HOME'], ['rytm', 'RYTM'], ['a4', 'A4'], ['both', 'BOTH'], ['history', 'HISTORY'], ['more', 'MORE']] as const).map(([id, label]) => <button type="button" key={id} aria-current={page === id ? 'page' : undefined} disabled={busy && (id === 'rytm' || id === 'a4' || id === 'both')} onClick={() => choosePage(id)}>{label}</button>)}</nav>
    {targetDialog !== null && state !== null && <TouchDialog title={`${DEVICE_LABELS[targetDialog]} TARGETS`} onClose={() => setTargetDialog(null)}><TargetGrid lane={state.lanes[targetDialog]} disabled={busy} onScope={(patch) => laneScope(targetDialog, patch)} /><div className="appliance-inline-actions"><button type="button" disabled={busy} onClick={() => laneScope(targetDialog, { target_ids: Array.from({ length: targetDialog === 'analog_rytm_mk2' ? 12 : 4 }, (_, index) => index + 1) })}>ALL</button><button type="button" disabled={busy} onClick={() => laneScope(targetDialog, { target_ids: [] })}>NONE</button></div></TouchDialog>}
    {confirmationCurrent && state !== null && confirmation?.kind === 'apply' && <TouchDialog title={state.mode === 'simulation' ? 'CONFIRM LOCAL APPLY' : 'CONFIRM EXACT HARDWARE APPLY'} onClose={() => setConfirmation(null)}><p>{state.mode === 'simulation' ? 'Simulation only. No output port is opened and no MIDI is sent.' : 'Confirm this exact plan once. Local send success does not verify hardware acceptance. Saved kits and sounds are not written.'}</p><dl className="appliance-details"><div><dt>CANDIDATE</dt><dd>{state.candidate?.candidate_id}</dd></div><div><dt>PLAN</dt><dd>{state.candidate?.send_plan_id ?? 'LOCAL ONLY'}</dd></div><div><dt>REVISION</dt><dd>{state.revision}</dd></div><div><dt>OUTPUT</dt><dd>{state.mode === 'simulation' ? 'NONE / SIMULATED' : connection?.selected_output ?? 'EXACT OUTPUT UNAVAILABLE'}</dd></div></dl><CandidateDiff candidate={state.candidate} /><div className="appliance-dialog-actions"><button type="button" onClick={() => setConfirmation(null)}>CANCEL</button><button type="button" data-appliance-confirmation="true" disabled={busy || !canApply} className="appliance-primary" onClick={() => void apply()}>{state.mode === 'simulation' ? 'CONFIRM LOCAL APPLY' : 'CONFIRM EXACT APPLY'}</button></div></TouchDialog>}
    {confirmationCurrent && confirmation?.kind === 'anchor' && <TouchDialog title="ADOPT NEW LOCAL ANCHOR" onClose={() => setConfirmation(null)}><p>Adopt the currently known software baseline as the next local return point. This does not request a capture, save a hardware kit, or restore the instrument.</p><div className="appliance-dialog-actions"><button type="button" onClick={() => setConfirmation(null)}>CANCEL</button><button type="button" className="appliance-primary" disabled={busy} onClick={() => { setConfirmation(null); void controller.execute('anchor'); }}>ADOPT KNOWN BASELINE</button></div></TouchDialog>}
    {confirmationCurrent && confirmation?.kind === 'arm' && state?.mode === 'production' && <TouchDialog title="ARM EXACT OUTPUT" onClose={() => { setConfirmation(null); setOutput(''); }}><p>Choose the exact paired instrument output. Arming does not bypass capability, known-state or per-action confirmation checks. Reconnect clears authority.</p><label>MIDI OUTPUT<select aria-label="Exact MIDI output" value={output} onChange={(event) => setOutput(event.target.value)}><option value="">CHOOSE EXACT OUTPUT</option>{(connection?.available_outputs ?? []).map((port, index) => <option key={`${port}:${index}`} value={port}>{port}</option>)}</select></label>{resolveArmSecret() === null && <p>Arm secret unavailable. Relaunch through the supervised launcher.</p>}<div className="appliance-dialog-actions"><button type="button" onClick={() => setConfirmation(null)}>CANCEL</button><button type="button" data-appliance-confirmation="true" disabled={busy || output === '' || resolveArmSecret() === null || outputOccurrences !== 1} onClick={() => void arm()}>CONFIRM ARM</button></div></TouchDialog>}
  </main>;
}
