import { useEffect, useState, useSyncExternalStore } from 'react';

import { useCockpitStore } from '../../state';
import { useCockpitClient } from '../context';
import { ANALOG_FOUR_TRACKS } from '../devices';
import type { ReferenceAudioDiagnostics } from '../../ws/referenceSound';
import {
  currentSoundRecordings, legacyNoiseFadeSession, nativeSourceLabel, nativeSources, recordingRefinementHeld, ReferenceSoundModel, segmentIsValid, selectedSound,
} from './referenceSoundModel';

import './referenceSound.css';

function levelDbfs(value: number): string {
  return value === 0 ? '-inf' : (20 * Math.log10(value)).toFixed(2);
}

function AudioDiagnostics({ diagnostics, label }: { diagnostics: ReferenceAudioDiagnostics | undefined; label: string }): JSX.Element {
  if (diagnostics === undefined) return <p className="panel-meta">{label}: legacy analysis; pitch and quality diagnostics unavailable.</p>;
  return <div className="reference-sound-table-scroll"><table className="reference-sound-table">
    <caption>{label}</caption>
    <tbody>
      <tr><th scope="row">Fundamental estimate</th><td>{diagnostics.qualified_pitch_hz === null ? 'Not qualified' : `${diagnostics.qualified_pitch_hz.toFixed(3)} Hz`} / {diagnostics.pitch_status}</td></tr>
      <tr><th scope="row">Strongest spectral peak</th><td>{diagnostics.spectral_peak_hz === null ? 'Unavailable' : `${diagnostics.spectral_peak_hz.toFixed(3)} Hz`} / not a verified fundamental</td></tr>
      <tr><th scope="row">Pitch method</th><td>{diagnostics.pitch_method} / monophonic estimate, not a played-note capture</td></tr>
      <tr><th scope="row">Voicing estimate</th><td>{diagnostics.pitch_confidence.toFixed(3)} / voiced fraction {diagnostics.voiced_fraction.toFixed(3)} / not accuracy</td></tr>
      <tr><th scope="row">Pitch stability</th><td>{diagnostics.pitch_stability_cents === null ? 'Unavailable' : `${diagnostics.pitch_stability_cents.toFixed(2)} cents`} / octave ambiguity {diagnostics.octave_ambiguous ? 'yes' : 'no'}</td></tr>
      <tr><th scope="row">Original capture levels</th><td>RMS {levelDbfs(diagnostics.rms)} dBFS / peak {levelDbfs(diagnostics.peak)} dBFS / clipped samples {(100 * diagnostics.clipped_fraction).toFixed(3)}%</td></tr>
      <tr><th scope="row">Detected note activity</th><td>{diagnostics.note_count ?? 'Uncertain'} / additional onsets {diagnostics.onset_count} / multiple pitches {diagnostics.multiple_pitch ? 'yes' : 'no'}</td></tr>
      <tr><th scope="row">Segment-local samples</th><td>{diagnostics.start_sample}:{diagnostics.sample_count} at {diagnostics.sample_rate} Hz / PCM SHA-256 {diagnostics.pcm_sha256}</td></tr>
      <tr><th scope="row">Diagnostic warnings</th><td>{diagnostics.warnings.length === 0 ? 'None detected' : diagnostics.warnings.join(', ').replace(/_/g, ' ')}</td></tr>
    </tbody>
  </table></div>;
}

export function ReferenceSoundPanel(): JSX.Element {
  const [open, setOpen] = useState(false);
  return (
    <section aria-labelledby="reference-sound-title" className="cockpit-panel reference-sound" data-testid="reference-sound-panel">
      <header className="reference-sound-header">
        <h2 id="reference-sound-title">Reference sound</h2>
        <span className="panel-meta">Native KIT alternatives / local files only</span>
        <button type="button" aria-expanded={open} aria-controls="reference-sound-workspace" onClick={() => setOpen(!open)}>
          {open ? 'Close reference sound' : 'Open reference sound'}
        </button>
      </header>
      {open && <ReferenceSoundWorkspace />}
    </section>
  );
}

export function ReferenceSoundWorkspace(): JSX.Element {
  const client = useCockpitClient();
  const records = useCockpitStore((state) => state.libraryRecords);
  const connected = useCockpitStore((state) => state.connectionStatus === 'connected');
  const armed = useCockpitStore((state) => state.sessionStatus?.armed === true || state.connection?.phase === 'armed');
  const rytmLocks = useCockpitStore((state) => state.rytmPadLocks);
  const a4Locks = useCockpitStore((state) => state.a4TrackLocks);
  const [model] = useState(() => new ReferenceSoundModel(client, (library) => useCockpitStore.getState().setLibraryRecords(library)));
  const view = useSyncExternalStore(model.subscribe, model.snapshot);
  const [reopenId, setReopenId] = useState('');
  const [gain, setGain] = useState(0.5);
  const [scratchSlot, setScratchSlot] = useState('');
  const [auditionStart, setAuditionStart] = useState('');
  const [auditionCount, setAuditionCount] = useState('');
  const auditionRangeValid = (auditionStart === '' && auditionCount === '') ||
    (auditionStart !== '' && auditionCount !== '' && Number.isInteger(Number(auditionStart)) &&
      Number(auditionStart) >= 0 && Number.isInteger(Number(auditionCount)) && Number(auditionCount) > 0);
  const scratchSlotValid = scratchSlot !== '' && Number.isInteger(Number(scratchSlot)) && Number(scratchSlot) >= 1 && Number(scratchSlot) <= 128;
  const candidate = selectedSound(view);
  const session = view.session;
  const busy = view.busy !== null;
  const unavailable = !connected || armed;
  const targetLocked = (view.deviceId === 'analog_four_mk2' ? a4Locks : rytmLocks).includes(view.target);
  const sources = nativeSources(records ?? []);
  const recordings = currentSoundRecordings(view);
  const recording = recordings.find((item) => item.audio_sha256 === view.recordingSha) ?? recordings.at(-1);
  const comparingOlderRecording = recording !== undefined && recording.audio_sha256 !== recordings.at(-1)!.audio_sha256;

  useEffect(() => {
    model.activate();
    const unsubscribe = useCockpitStore.subscribe((state, previous) => {
      if (state.mutationContextRevision !== previous.mutationContextRevision ||
        state.connectionStatus !== previous.connectionStatus || state.sessionGeneration !== previous.sessionGeneration ||
        state.sessionStatus?.armed !== previous.sessionStatus?.armed) model.invalidate();
    });
    return () => { unsubscribe(); model.dispose(); };
  }, [model]);

  useEffect(() => { model.setRecords(records ?? []); }, [model, records]);

  const retainedSegment = session !== null && view.startFrame === session.segment.start_frame && view.frameCount === session.segment.frame_count;
  const canGenerate = session !== null && retainedSegment && segmentIsValid(view) && view.sourceId !== '' &&
    view.parameters.some((parameter) => !view.locks.includes(parameter)) && !targetLocked;

  return (
    <div id="reference-sound-workspace" className="reference-sound-workspace" aria-busy={busy}>
      {unavailable && <p className="panel-meta">{armed ? 'DISARM before opening the offline workspace.' : 'Sidecar disconnected.'}</p>}
      <div className="reference-sound-toolbar">
        <button type="button" disabled={busy || unavailable} onClick={() => void model.refresh()}>Refresh sessions</button>
        <label>Retained session
          <select value={reopenId} onChange={(event) => setReopenId(event.target.value)} disabled={busy || unavailable}>
            <option value="">Choose session</option>
            {view.sessions.map((item) => <option key={item.session_id} value={item.session_id}>
              {item.title} / {item.context?.device_id ?? 'reference'} / {item.segment.start_frame}:{item.segment.frame_count} / {item.favorites.length} favorites
            </option>)}
          </select>
        </label>
        <button type="button" disabled={busy || unavailable || reopenId === ''} onClick={() => void model.reopen(reopenId)}>Reopen session</button>
        <button type="button" disabled={!busy} onClick={() => void model.cancel()}>Cancel operation</button>
      </div>
      {view.error !== null && <p className="reference-sound-error" role="alert">{view.error}</p>}
      {busy && <p className="panel-meta">{view.busy}{view.uploadSize > 0 ? ` / ${view.received} of ${view.uploadSize} bytes` : ''}</p>}

      <div className="reference-sound-inputs">
        <div className="reference-sound-source">
          <h3>Reference audio</h3>
          <label>Original WAV
            <input type="file" accept=".wav,audio/wav" disabled={busy || unavailable} onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = '';
              if (file !== undefined) void model.importReference(file);
            }} />
          </label>
          {view.originalUrl !== null && <audio controls preload="metadata" src={view.originalUrl} aria-label="Original reference playback" />}
          {session !== null && <>
            <p className="panel-meta">{session.title} / {session.segment.original.seconds}s / {session.segment.original.sample_rate} Hz / {session.segment.original.channels} channels / {session.segment.original.sample_width * 8}-bit PCM</p>
            <button type="button" disabled={busy || unavailable} onClick={() => void model.playReference('original')}>Reload original WAV</button>
            <div className="reference-sound-toolbar">
              <label>Start frame<input type="number" min={0} max={session.segment.original.frame_count - view.frameCount} step={1}
                value={view.startFrame} onChange={(event) => model.setSegment(Number(event.target.value), view.frameCount)} /></label>
              <label>Frame count<input type="number" min={Math.ceil(session.segment.original.sample_rate * 0.05)}
                max={Math.min(session.segment.original.sample_rate * 8, session.segment.original.frame_count - view.startFrame)} step={1}
                value={view.frameCount} onChange={(event) => model.setSegment(view.startFrame, Number(event.target.value))} /></label>
              <output>{view.startFrame / session.segment.original.sample_rate}s - {(view.startFrame + view.frameCount) / session.segment.original.sample_rate}s</output>
              <button type="button" disabled={busy || unavailable || !segmentIsValid(view)} onClick={() => void model.applySegment()}>Retain segment</button>
            </div>
            {view.segmentUrl !== null && <audio controls preload="metadata" src={view.segmentUrl} aria-label="Retained reference segment playback" />}
            <button type="button" disabled={busy || unavailable} onClick={() => void model.playReference('segment')}>Reload retained segment</button>
            <p className="panel-meta">Retained frames {session.segment.start_frame}:{session.segment.frame_count} / SHA-256 {session.segment.sha256}</p>
          </>}
        </div>

        <div className="reference-sound-source">
          <h3>Native source KIT</h3>
          <div className="reference-sound-toolbar">
            <button type="button" disabled={busy || unavailable} onClick={() => void model.loadLibrary()}>Load source library</button>
            <button type="button" disabled={busy || unavailable} onClick={() => void model.loadLibrary(true)}>Import captures</button>
          </div>
          <label>Device
            <select value={view.deviceId} disabled={busy || unavailable} onChange={(event) => void model.chooseSource('',
              event.target.value === 'analog_four_mk2' ? 'analog_four_mk2' : 'analog_rytm_mk2', 1)}>
              <option value="analog_rytm_mk2">Analog Rytm MKII</option>
              <option value="analog_four_mk2">Analog Four MKII</option>
            </select>
          </label>
          <label>Source Library record
            <select value={view.sourceId} disabled={busy || unavailable} onChange={(event) => void model.chooseSource(event.target.value, view.deviceId, view.target)}>
              <option value="">Choose original native KIT</option>
              {sources.filter((item) => item.device_id === view.deviceId).map((item) =>
                <option value={item.record_id} key={item.record_id}>{nativeSourceLabel(item)}</option>)}
            </select>
          </label>
          <label>{view.deviceId === 'analog_four_mk2' ? 'Target track' : 'Target pad'}
            <input type="number" min={1} max={view.deviceId === 'analog_four_mk2' ? ANALOG_FOUR_TRACKS.length : 12} step={1}
              value={view.target} disabled={busy || unavailable} onChange={(event) => void model.chooseSource(view.sourceId, view.deviceId, Number(event.target.value))} />
          </label>
          {targetLocked && <p className="reference-sound-error">Target locked in Cockpit.</p>}
          <label>Mutation strength <span>{view.strength}</span>
            <input type="range" min={0} max={1} step={0.01} value={view.strength} onChange={(event) => model.setStrength(Number(event.target.value))} />
          </label>
        </div>
      </div>

      {view.controls.length > 0 && <div className="reference-sound-table-scroll">
        <table className="reference-sound-table reference-sound-table--scope">
          <caption>Native field scope and protections</caption>
          <thead><tr><th scope="col">Field</th><th scope="col">Source / encoded</th><th scope="col">Units / domain</th><th scope="col">Mutate</th><th scope="col">Lock</th><th scope="col">Protection</th></tr></thead>
          <tbody>{view.controls.map((control) => <tr key={control.parameter}>
            <th scope="row">{control.parameter}</th>
            <td>{control.source_display ?? 'Unavailable'} / {control.source_value}</td>
            <td>{control.units}{control.domain !== null && (control.domain.values.length > 0
              ? ` / allowed: ${control.domain.values.join(', ')}`
              : ` / ${control.domain.minimum}..${control.domain.maximum} step ${control.domain.quantum}`)}</td>
            <td><input type="checkbox" aria-label={`Mutate ${control.parameter}`} disabled={!control.mutable || unavailable}
              checked={view.parameters.includes(control.parameter)} onChange={() => model.toggleField(control.parameter, false)} /></td>
            <td><input type="checkbox" aria-label={`Lock ${control.parameter}`} disabled={!control.mutable || unavailable}
              checked={!control.mutable || view.locks.includes(control.parameter)} onChange={() => model.toggleField(control.parameter, true)} /></td>
            <td>{control.reasons.join(', ')}</td>
          </tr>)}</tbody>
        </table>
      </div>}

      <div className="reference-sound-toolbar">
        <button type="button" disabled={busy || unavailable || !canGenerate} onClick={() => void model.generate()}>Generate eight alternatives</button>
        {view.stale && <p className="reference-sound-error">Source, segment or scope changed. Previous candidates are no longer current.</p>}
      </div>

      {session !== null && !view.stale && session.candidates.length > 0 && <>
        {legacyNoiseFadeSession(session) && <p className="reference-sound-error">Legacy Noise Fade model: exact recall and favorites remain available. Generate a separate current-model session before new refinement.</p>}
        {session.analysis?.diagnostics === undefined && <button type="button" disabled={busy || unavailable}
          onClick={() => void model.measureReference()}>Measure retained reference</button>}
        <AudioDiagnostics diagnostics={session.analysis?.diagnostics} label="Reference segment diagnostics" />
        <fieldset className="reference-sound-candidates">
          <legend>Native alternatives</legend>
          {session.candidates.map((item, index) => <label key={item.candidate_id}>
            <input type="radio" name="reference-sound-candidate" value={item.candidate_id}
              checked={session.selected_candidate_id === item.candidate_id} disabled={busy || unavailable}
              onChange={() => void model.select(item.candidate_id)} />
            <strong>{index + 1}. {item.label}</strong><span>{item.direction}</span>
            <small>{item.changes.length} native changes{session.favorites.includes(item.candidate_id) ? ' / Favorite' : ''}</small>
          </label>)}
        </fieldset>
        {candidate !== undefined && <>
          <div className="reference-sound-toolbar">
            <h3>{candidate.label}</h3>
            <button type="button" disabled={busy || unavailable} aria-pressed={session.favorites.includes(candidate.candidate_id)}
              onClick={() => void model.select(candidate.candidate_id, !session.favorites.includes(candidate.candidate_id))}>
              {session.favorites.includes(candidate.candidate_id) ? 'Remove favorite' : 'Favorite candidate'}
            </button>
            <label>Scratch KIT slot (1-128)<input type="number" min={1} max={128} step={1} value={scratchSlot}
              onChange={(event) => setScratchSlot(event.target.value)} /></label>
            <button type="button" disabled={busy || unavailable || !scratchSlotValid}
              onClick={() => void model.download(Number(scratchSlot) - 1)}>Download .syx</button>
            <span className="panel-meta">Candidate at source destination: {candidate.frame_size} bytes / SHA-256 {candidate.frame_sha256}</span>
          </div>
          <div className="reference-sound-table-scroll"><table className="reference-sound-table reference-sound-table--changes">
            <caption>Exact native changes</caption>
            <thead><tr><th scope="col">Field</th><th scope="col">Source</th><th scope="col">Proposed</th><th scope="col">Rendered readback</th><th scope="col">Units</th><th scope="col">Rationale</th></tr></thead>
            <tbody>{candidate.changes.map((change) => <tr key={change.parameter}>
              <th scope="row">{change.parameter}</th><td>{change.source_display ?? 'Unavailable'} / {change.source_value}</td>
              <td>{change.proposed_display} / {change.proposed_value}</td><td>{change.rendered_display ?? 'Unavailable'} / {change.rendered_value}</td>
              <td>{change.units}</td><td>{change.rationale}</td>
            </tr>)}</tbody>
          </table></div>
          <ul className="panel-meta">{candidate.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>

          <div className="reference-sound-toolbar">
            <label>Audition start frame (optional)<input type="number" min={0} step={1} value={auditionStart}
              disabled={busy || unavailable} onChange={(event) => setAuditionStart(event.target.value)} /></label>
            <label>Audition frame count (optional)<input type="number" min={1} step={1} value={auditionCount}
              disabled={busy || unavailable} onChange={(event) => setAuditionCount(event.target.value)} /></label>
            <label>Supplied candidate recording WAV (0.05-8s)
              <input type="file" accept=".wav,audio/wav" disabled={busy || unavailable || !auditionRangeValid || session.recordings.length >= 16} onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = '';
                if (file !== undefined) void model.record(file, auditionStart === '' ? undefined :
                  { start_frame: Number(auditionStart), frame_count: Number(auditionCount) });
              }} />
            </label>
            {recordings.length > 0 && <label>Retained supplied recording
              <select value={view.recordingSha ?? ''} disabled={busy || unavailable} onChange={(event) => void model.playRecording(event.target.value)}>
                <option value="">Choose supplied recording</option>
                {recordings.map((item, index) => <option key={`${item.audio_sha256}-${index}`} value={item.audio_sha256}>
                  Score {item.score}/100 / {item.audio_sha256}
                </option>)}
              </select>
            </label>}
            {view.recordingUrl !== null && <audio controls preload="metadata" src={view.recordingUrl} aria-label="Supplied candidate recording playback" />}
            <label>Correction gain <span>{gain}</span><input type="range" min={0} max={1} step={0.01} value={gain} onChange={(event) => setGain(Number(event.target.value))} /></label>
            <button type="button" disabled={busy || unavailable || recording === undefined || comparingOlderRecording || recordingRefinementHeld(recording) || legacyNoiseFadeSession(session) || session.refinements.length >= 3}
              title={comparingOlderRecording ? 'Latest supplied recording required for refinement' : undefined}
              onClick={() => void model.refine(gain)}>Refine candidate ({session.refinements.length}/3)</button>
          </div>
          {recording === undefined ? <p className="panel-meta">No measured recording for this candidate. No synthetic audio preview.</p> : <>
            {recording.segment !== undefined && <p className="panel-meta">
              Analyzed audition: frames {recording.segment.start_frame}:{recording.segment.frame_count} / {recording.segment.start_frame / recording.segment.original.sample_rate}s - {(recording.segment.start_frame + recording.segment.frame_count) / recording.segment.original.sample_rate}s / {recording.segment.original.sample_rate} Hz / segment SHA-256 {recording.segment.sha256} / original SHA-256 {recording.segment.original.sha256}
            </p>}
            {recording.segment === undefined && <p className="panel-meta">Legacy whole-recording analysis / SHA-256 {recording.audio_sha256}</p>}
            <AudioDiagnostics diagnostics={recording.features.diagnostics} label="Controlled audition diagnostics" />
            <p className={recordingRefinementHeld(recording) ? 'reference-sound-error' : 'panel-meta'}>
              Pitch comparison: {recording.pitch_comparison?.support_status ?? 'held'} / recording minus reference {recording.pitch_comparison?.delta_cents == null ? 'not qualified' : `${recording.pitch_comparison.delta_cents.toFixed(2)} cents`} / octave difference {recording.pitch_comparison?.octave_difference ?? 'not qualified'} / separate from the eleven-feature score.
              {recordingRefinementHeld(recording) && ` Refinement held: ${recording.pitch_comparison?.blockers.join(', ').replace(/_/g, ' ') || 'diagnostics unavailable'}. Supply a clean single-note audition with onset and release; no pitch or tuning changed.`}
            </p>
            <p className="panel-meta">Score {recording.score}/100 / distance {recording.distance} / {recording.metric} / physical validation: no</p>
            <div className="reference-sound-table-scroll"><table className="reference-sound-table">
              <caption>Measured reference and supplied recording (normalized 0-1)</caption>
              <thead><tr><th scope="col">Feature</th><th scope="col">Reference</th><th scope="col">Supplied recording</th>
                <th scope="col">Absolute delta</th><th scope="col">Weight</th><th scope="col">Weighted delta</th></tr></thead>
              <tbody>{recording.feature_deltas.map((delta) => <tr key={delta.feature}><th scope="row">{delta.feature}</th>
                <td>{delta.reference_value}</td><td>{delta.render_value}</td><td>{delta.absolute_delta}</td><td>{delta.weight}</td><td>{delta.weighted_delta}</td></tr>)}</tbody>
            </table></div>
          </>}
        </>}
        {session.recordings.length > 0 && <div className="reference-sound-table-scroll"><table className="reference-sound-table">
          <caption>Supplied recording ranking / weighted normalized 11-feature L1 distance / not a probability</caption>
          <thead><tr><th scope="col">Candidate</th><th scope="col">Recording SHA-256</th><th scope="col">Distance (lower is closer)</th><th scope="col">Score / 100</th><th scope="col">Compare</th></tr></thead>
          <tbody>{[...session.recordings].sort((left, right) => left.distance - right.distance).map((item, index) => <tr key={`${item.audio_sha256}-${index}`}>
            <th scope="row">{item.candidate_id}</th><td>{item.audio_sha256}</td><td>{item.distance}</td><td>{item.score}</td>
            <td><button type="button" disabled={busy || unavailable} onClick={() => void model.select(item.candidate_id)}>Compare {item.candidate_id}</button></td>
          </tr>)}</tbody>
        </table></div>}
      </>}
    </div>
  );
}
