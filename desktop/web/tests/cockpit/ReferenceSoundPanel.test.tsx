import { Blob as NodeBlob } from 'node:buffer';
import { webcrypto } from 'node:crypto';
import { StrictMode } from 'react';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { Cockpit } from '../../src/cockpit/Cockpit';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { ReferenceSoundPanel, ReferenceSoundWorkspace } from '../../src/cockpit/referenceSound/ReferenceSoundPanel';
import { bindClientToStore, useCockpitStore } from '../../src/state';
import { sendPlan, sessionLive } from './_fixtures';
import { audioFile, prepareSound, sha, soundAck, soundControls, soundHarness, soundSession, sourceRecord, wav } from './referenceSoundTestSupport';
import { runAxe, violationSummary } from '../a11y/__helpers__/axe';

beforeEach(() => {
  vi.stubGlobal('Blob', NodeBlob);
  vi.stubGlobal('crypto', webcrypto);
  vi.spyOn(URL, 'createObjectURL').mockImplementation(() => `blob:${Math.random()}`);
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  act(() => {
    useCockpitStore.getState().reset();
    useCockpitStore.setState({ connectionStatus: 'connected', sessionStatus: { ...sessionLive, armed: false }, libraryRecords: [sourceRecord] });
  });
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

function mount(h = soundHarness(), panel = false) {
  return { h, ...render(<StrictMode><CockpitClientProvider client={h.fake.asClient()}>
    {panel ? <ReferenceSoundPanel /> : <ReferenceSoundWorkspace />}
  </CockpitClientProvider></StrictMode>) };
}

async function reopen(h: ReturnType<typeof soundHarness>) {
  fireEvent.click(screen.getByRole('button', { name: 'Refresh sessions' }));
  await waitFor(() => expect(screen.getByLabelText('Retained session').querySelectorAll('option')).toHaveLength(2));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh sessions' })).toBeEnabled());
  fireEvent.change(screen.getByLabelText('Retained session'), { target: { value: h.getSession().session_id } });
  fireEvent.click(screen.getByRole('button', { name: 'Reopen session' }));
  await waitFor(() => expect(screen.getByLabelText('Retained reference segment playback')).toHaveAttribute('src'));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh sessions' })).toBeEnabled());
}

describe('actual reference sound workspace', () => {
  it('is reachable through Cockpit, separate from the existing four-candidate description compiler', async () => {
    const h = soundHarness();
    render(<Cockpit client={h.fake.asClient()} />);
    expect(screen.getByTestId('reference-sound-panel')).toHaveTextContent('Reference sound');
    expect(h.calls).toHaveLength(0);
    fireEvent.click(screen.getByRole('button', { name: 'Open reference sound' }));
    expect(screen.getByLabelText('Original WAV')).toBeEnabled();
    fireEvent.click(screen.getByTestId('device-select-analog-four-mk2'));
    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('A4 Patch Genome');
    expect(screen.getByLabelText('Original WAV')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Close reference sound' }));
    expect(screen.queryByLabelText('Original WAV')).not.toBeInTheDocument();
  });

  it('uploads/playbacks a real WAV, retains exact samples, protects scope, chooses eight native alternatives, favorites, records, refines and downloads', async () => {
    const h = soundHarness();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    mount(h);
    fireEvent.change(screen.getByLabelText('Original WAV'), { target: { files: [audioFile()] } });
    await waitFor(() => expect(screen.getByLabelText('Original reference playback')).toHaveAttribute('src'));
    await waitFor(() => expect(screen.getByLabelText('Retained reference segment playback')).toHaveAttribute('src'));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh sessions' })).toBeEnabled());
    fireEvent.change(screen.getByLabelText('Start frame'), { target: { value: '100' } });
    fireEvent.change(screen.getByLabelText('Frame count'), { target: { value: '400' } });
    expect(screen.getByRole('button', { name: 'Generate eight alternatives' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Retain segment' }));
    await waitFor(() => expect(screen.getByText(/Retained frames 100:400/)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh sessions' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Load source library' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Load source library' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Import captures' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Import captures' })).toBeEnabled());
    fireEvent.change(screen.getByLabelText('Source Library record'), { target: { value: 'native-source' } });
    await waitFor(() => expect(screen.getByLabelText('Mutate dec')).toBeChecked());
    expect(screen.getByLabelText('Mutate unsupported')).toBeDisabled();
    expect(screen.getByLabelText('Lock unsupported')).toBeChecked();
    fireEvent.click(screen.getByLabelText('Lock lev'));
    fireEvent.click(screen.getByRole('button', { name: 'Generate eight alternatives' }));
    await waitFor(() => expect(screen.getAllByRole('radio')).toHaveLength(8));
    const changes = screen.getByRole('table', { name: 'Exact native changes' });
    expect(changes).toHaveTextContent('64 / 64');
    expect(changes).toHaveTextContent('80 / 80');
    expect(changes).toHaveTextContent('72 / 72');
    expect(changes).toHaveTextContent('Measured decay contribution');
    expect(screen.getByRole('button', { name: /Refine candidate/ })).toBeDisabled();
    fireEvent.click(screen.getByRole('radio', { name: /2. Alternative 2/ }));
    await waitFor(() => expect(screen.getByRole('radio', { name: /2. Alternative 2/ })).toBeChecked());
    fireEvent.click(screen.getByRole('button', { name: 'Favorite candidate' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Remove favorite' })).toHaveAttribute('aria-pressed', 'true'));
    fireEvent.click(screen.getByRole('button', { name: 'Remove favorite' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Favorite candidate' })).toBeEnabled());
    fireEvent.change(screen.getByLabelText('Supplied candidate recording WAV (0.05-8s)'), { target: { files: [audioFile(wav(), 'recording.wav')] } });
    await waitFor(() => expect(screen.getByLabelText('Supplied candidate recording playback')).toHaveAttribute('src'));
    expect(screen.getByText(/Score 90\/100 \/ distance/)).toHaveTextContent('not a probability');
    expect(within(screen.getByRole('table', { name: /Measured reference/ })).getAllByRole('row')).toHaveLength(12);
    fireEvent.change(screen.getByLabelText(/Correction gain/), { target: { value: '0.25' } });
    fireEvent.click(screen.getByRole('button', { name: 'Refine candidate (0/3)' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Refine candidate (1/3)' })).toBeDisabled());
    expect(screen.getByLabelText('Scratch KIT slot (1-128)')).toHaveValue(null);
    expect(screen.getByRole('button', { name: 'Download .syx' })).toBeDisabled();
    for (const value of ['0', '129', '1.5']) {
      fireEvent.change(screen.getByLabelText('Scratch KIT slot (1-128)'), { target: { value } });
      expect(screen.getByRole('button', { name: 'Download .syx' })).toBeDisabled();
    }
    fireEvent.change(screen.getByLabelText('Scratch KIT slot (1-128)'), { target: { value: '128' } });
    fireEvent.click(screen.getByRole('button', { name: 'Download .syx' }));
    await waitFor(() => expect(click).toHaveBeenCalledOnce());
    expect(h.calls.at(-1)?.command).toMatchObject({ action: 'export', destination_slot: 127 });
    expect(h.calls.every((call) => ['reference_sound', 'library_list', 'library_import_captures'].includes(call.command.type))).toBe(true);
  });

  it('reopens saved favorites with retained playback after restart and ranks only supplied recordings by actual distance', async () => {
    const h = soundHarness();
    await prepareSound(h);
    await h.model.record(audioFile());
    await h.model.select('candidate-1', true);
    const saved = h.getSession();
    h.setSession({ ...saved, recordings: [saved.recordings[0]!, { ...saved.recordings[0]!, candidate_id: 'candidate-2', score: 97, distance: 0.03, audio_sha256: 'closer-recording' }],
      refinements: Array.from({ length: 3 }, () => ({ parent_id: 'candidate-1', recording_sha256: 'x', gain: 0.25, features: saved.analysis!.features })) });
    mount(h);
    await reopen(h);
    expect(screen.getByLabelText('Original reference playback')).toHaveAttribute('src');
    expect(screen.getByLabelText('Supplied candidate recording playback')).toHaveAttribute('src');
    expect(screen.getByLabelText('Retained supplied recording')).toHaveValue(saved.recordings[0]!.audio_sha256);
    expect(screen.getByRole('button', { name: 'Remove favorite' })).toBeInTheDocument();
    const ranking = screen.getByRole('table', { name: /Supplied recording ranking/ });
    expect(within(ranking).getAllByRole('row')[1]).toHaveTextContent('candidate-2closer-recording0.0397');
    expect(screen.getByRole('button', { name: 'Refine candidate (3/3)' })).toBeDisabled();
    h.model.dispose();
  });

  it('plays reopened original and retained supplied recordings, switching exact server metric explanations with the recording', async () => {
    const h = soundHarness(); await prepareSound(h);
    await h.model.record(audioFile());
    const firstSha = h.getSession().recordings[0]!.audio_sha256;
    const secondAudio = wav(400);
    secondAudio[44] = 8;
    await h.model.record(audioFile(secondAudio));
    const saved = h.getSession();
    saved.recordings[0] = { ...saved.recordings[0]!, score: 80, distance: 0.2,
      feature_deltas: saved.recordings[0]!.feature_deltas.map((delta) => ({ ...delta, render_value: 0.7, absolute_delta: 0.2, weighted_delta: delta.weight * 0.2 })) };
    h.setSession(saved);
    mount(h); await reopen(h);
    expect(screen.getByLabelText('Original reference playback')).toHaveAttribute('src');
    expect(screen.getByLabelText('Supplied candidate recording playback')).toHaveAttribute('src');
    expect(screen.getByLabelText('Retained supplied recording')).toHaveValue(sha(secondAudio));
    fireEvent.change(screen.getByLabelText('Retained supplied recording'), { target: { value: firstSha } });
    await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh sessions' })).toBeEnabled());
    expect(h.calls.at(-1)?.command).toMatchObject({ audio_kind: 'recording', recording_sha256: firstSha });
    expect(screen.getByText(/Score 80\/100 \/ distance/)).toHaveTextContent('not a probability');
    expect(screen.getByRole('button', { name: 'Refine candidate (0/3)' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Refine candidate (0/3)' })).toHaveAttribute('title', 'Latest supplied recording required for refinement');
    const deltas = screen.getByRole('table', { name: /Measured reference and supplied recording/ });
    expect(within(deltas).getByRole('columnheader', { name: 'Absolute delta' })).toBeInTheDocument();
    expect(within(deltas).getByRole('columnheader', { name: /^Weight$/ })).toBeInTheDocument();
    expect(within(deltas).getByRole('columnheader', { name: 'Weighted delta' })).toBeInTheDocument();
    expect(within(deltas).getByRole('row', { name: /brightness/ })).toHaveTextContent('brightness0.50.70.20.150.03');
    fireEvent.click(screen.getByRole('button', { name: 'Reload original WAV' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Reload original WAV' })).toBeEnabled());
    expect(h.calls.at(-1)?.command).toMatchObject({ audio_kind: 'original' });
    fireEvent.click(screen.getByRole('button', { name: 'Reload retained segment' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Reload retained segment' })).toBeEnabled());
    expect(h.calls.at(-1)?.command).toMatchObject({ audio_kind: 'segment' });
    h.model.dispose();
  });

  it('does not invent a refined variant or lose supplied playback when the server returns zero residual', async () => {
    const h = soundHarness(); await prepareSound(h); await h.model.record(audioFile());
    const saved = h.getSession();
    saved.recordings = saved.recordings.map((recording) => ({ ...recording, score: 100, distance: 0,
      feature_deltas: recording.feature_deltas.map((delta) => ({ ...delta, render_value: delta.reference_value, absolute_delta: 0, weighted_delta: 0 })) }));
    h.setSession(saved);
    mount(h); await reopen(h);
    const before = screen.getByLabelText('Supplied candidate recording playback').getAttribute('src');
    fireEvent.click(screen.getByRole('button', { name: 'Refine candidate (0/3)' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Refine candidate (0/3)' })).toBeEnabled());
    expect(screen.getAllByRole('radio')).toHaveLength(8);
    expect(screen.getByLabelText('Supplied candidate recording playback')).toHaveAttribute('src', before);
    expect(screen.getByText(/Score 100\/100 \/ distance/)).toHaveTextContent('distance 0');
    h.model.dispose();
  });

  it.each(['before-ack', 'after-ack'] as const)('keeps reference results current across successful ack and canonical plan-clear events (%s)', async (eventOrder) => {
    const h = soundHarness(); h.setSession(soundSession(wav(), true));
    const unbind = bindClientToStore(h.fake.asClient());
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation(async (command, ...rest) => {
      const ack = await original(command, ...rest);
      if (command.type === 'reference_sound' && ack.ok && ['reopen', 'segment', 'generate', 'select', 'favorite', 'refine'].includes(command.action)) {
        const clearPlan = () => act(() => h.fake.emitEvent({ type: 'send_plan_changed', send_plan: null }));
        if (eventOrder === 'before-ack') clearPlan();
        else setTimeout(clearPlan, 0);
      }
      return ack;
    });
    mount(h);
    const revision = useCockpitStore.getState().mutationContextRevision;
    const assertCleared = async () => {
      await waitFor(() => expect(useCockpitStore.getState().sendPlan).toBeNull());
      await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh sessions' })).toBeEnabled());
      expect(useCockpitStore.getState().mutationContextRevision).toBe(revision);
      expect(screen.queryByText(/Previous candidates are no longer current/)).not.toBeInTheDocument();
    };
    act(() => useCockpitStore.getState().setSendPlan(sendPlan));
    await reopen(h);
    await assertCleared();
    expect(screen.getAllByRole('radio')).toHaveLength(8);
    act(() => useCockpitStore.getState().setSendPlan(sendPlan));
    fireEvent.click(screen.getByRole('button', { name: 'Generate eight alternatives' }));
    await assertCleared();
    expect(screen.getAllByRole('radio')).toHaveLength(8);
    act(() => useCockpitStore.getState().setSendPlan(sendPlan));
    fireEvent.click(screen.getByRole('radio', { name: /2. Alternative 2/ }));
    await assertCleared();
    expect(screen.getByRole('radio', { name: /2. Alternative 2/ })).toBeChecked();
    act(() => useCockpitStore.getState().setSendPlan(sendPlan));
    fireEvent.click(screen.getByRole('button', { name: 'Favorite candidate' }));
    await assertCleared();
    expect(screen.getByRole('button', { name: 'Remove favorite' })).toBeInTheDocument();
    act(() => useCockpitStore.getState().setSendPlan(sendPlan));
    fireEvent.change(screen.getByLabelText('Supplied candidate recording WAV (0.05-8s)'), { target: { files: [audioFile()] } });
    await waitFor(() => expect(screen.getByRole('button', { name: 'Refine candidate (0/3)' })).toBeEnabled());
    expect(useCockpitStore.getState().sendPlan).toBe(sendPlan);
    fireEvent.click(screen.getByRole('button', { name: 'Refine candidate (0/3)' }));
    await assertCleared();
    expect(screen.getAllByRole('radio')).toHaveLength(9);
    act(() => useCockpitStore.getState().setSendPlan(sendPlan));
    fireEvent.change(screen.getByLabelText('Start frame'), { target: { value: '100' } });
    fireEvent.change(screen.getByLabelText('Frame count'), { target: { value: '400' } });
    fireEvent.click(screen.getByRole('button', { name: 'Retain segment' }));
    await assertCleared();
    expect(screen.getByText(/Retained frames 100:400/)).toBeInTheDocument();
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
    expect(h.calls.some(({ command }) => command.type === 'reference_sound' && command.action === 'cancel')).toBe(false);
    unbind();
  });

  it.each(['reopen', 'segment', 'select'] as const)('preserves the primary plan when reference %s is refused', async (action) => {
    const h = soundHarness(); h.setSession(soundSession(wav(), true));
    const unbind = bindClientToStore(h.fake.asClient());
    mount(h); await reopen(h);
    const revision = useCockpitStore.getState().mutationContextRevision;
    act(() => useCockpitStore.getState().setSendPlan(sendPlan));
    h.send.mockResolvedValueOnce({ ok: false, request_id: 'refused', message: 'Reference-sound request refused; existing work is unchanged.' });
    if (action === 'reopen') fireEvent.click(screen.getByRole('button', { name: 'Reopen session' }));
    else if (action === 'select') fireEvent.click(screen.getByRole('radio', { name: /2. Alternative 2/ }));
    else {
      fireEvent.change(screen.getByLabelText('Start frame'), { target: { value: '100' } });
      fireEvent.change(screen.getByLabelText('Frame count'), { target: { value: '400' } });
      fireEvent.click(screen.getByRole('button', { name: 'Retain segment' }));
    }
    expect(await screen.findByRole('alert')).toHaveTextContent('existing work is unchanged');
    expect(useCockpitStore.getState().sendPlan).toBe(sendPlan);
    expect(useCockpitStore.getState().mutationContextRevision).toBe(revision);
    expect(h.getSession().selected_candidate_id).toBe('candidate-1');
    unbind();
  });

  it('invalidates candidates on local changes and shared Cockpit lock/scope/connection changes', async () => {
    const h = soundHarness(); h.setSession(soundSession(wav(), true));
    mount(h); await reopen(h);
    fireEvent.change(screen.getByLabelText(/Mutation strength/), { target: { value: '0.6' } });
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
    expect(screen.getByText(/Previous candidates are no longer current/)).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Mutate dec'));
    act(() => useCockpitStore.getState().setMutationLocks([1], []));
    expect(screen.getByRole('button', { name: 'Generate eight alternatives' })).toBeDisabled();
    expect(screen.getByText('Target locked in Cockpit.')).toBeInTheDocument();
    act(() => useCockpitStore.setState({ connectionStatus: 'closed' }));
    expect(screen.getByText('Sidecar disconnected.')).toBeInTheDocument();
    act(() => useCockpitStore.setState({ sessionGeneration: 5 }));
    act(() => useCockpitStore.setState({ sessionStatus: { ...sessionLive, armed: true } }));
    expect(screen.getByText(/DISARM before/)).toBeInTheDocument();
  });

  it('uses native metadata for either device, clearing source and selection when device/target changes', async () => {
    const h = soundHarness();
    act(() => useCockpitStore.setState({ libraryRecords: [sourceRecord, { ...sourceRecord, record_id: 'a4-native', device_id: 'analog_four_mk2' }] }));
    mount(h);
    fireEvent.change(screen.getByLabelText('Device'), { target: { value: 'analog_four_mk2' } });
    expect(screen.getByLabelText('Target track')).toHaveAttribute('max', '4');
    fireEvent.change(screen.getByLabelText('Source Library record'), { target: { value: 'a4-native' } });
    await waitFor(() => expect(screen.getByLabelText('Mutate dec')).toBeInTheDocument());
    act(() => useCockpitStore.getState().setMutationLocks([], [2]));
    fireEvent.change(screen.getByLabelText('Target track'), { target: { value: '2' } });
    await waitFor(() => expect(screen.getByText('Target locked in Cockpit.')).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText('Device'), { target: { value: 'analog_rytm_mk2' } });
    expect(screen.getByLabelText('Target pad')).toHaveAttribute('max', '12');
    expect(screen.getByLabelText('Source Library record')).toHaveValue('');
  });

  it('surfaces server refusal and missing-recording evidence; canceled file choosers do nothing', async () => {
    const h = soundHarness(); mount(h);
    fireEvent.change(screen.getByLabelText('Original WAV'), { target: { files: [] } });
    fireEvent.change(screen.getByLabelText('Original WAV'), { target: {} });
    expect(h.calls).toHaveLength(0);
    h.send.mockResolvedValueOnce({ ok: false, request_id: 'x', message: 'Audio runtime is missing.' });
    fireEvent.click(screen.getByRole('button', { name: 'Refresh sessions' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Audio runtime is missing.');
  });

  it('keeps cancellation available during worker/upload progress and ignores late results', async () => {
    const h = soundHarness(); mount(h);
    let resolve!: (reply: ReturnType<typeof soundAck>) => void;
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'upload_chunk'
      ? new Promise((done) => { resolve = done; }) : original(command, ...rest));
    fireEvent.change(screen.getByLabelText('Original WAV'), { target: { files: [audioFile()] } });
    await waitFor(() => expect(screen.getByText(/0 of 16044 bytes/)).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Cancel operation' }));
    await act(async () => resolve(soundAck({ upload_id: 'owned-upload', received: 16044 })));
    expect(screen.queryByLabelText('Original reference playback')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel operation' })).toBeDisabled();
  });

  it('handles empty source library and PCM references shorter than the legal segment', async () => {
    const h = soundHarness(wav(100));
    act(() => useCockpitStore.setState({ libraryRecords: null }));
    mount(h); await reopen(h);
    expect(screen.getByRole('button', { name: 'Retain segment' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Generate eight alternatives' })).toBeDisabled();
  });

  it('handles unavailable native displays, recording limits and missing selected candidate safely', async () => {
    const h = soundHarness();
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'controls'
      ? Promise.resolve(soundAck({ controls: soundControls.map((control) => control.parameter === 'lev'
        ? { ...control, domain: { minimum: 0, maximum: 127, quantum: 1, values: [0, 80, 127] } } : control) })) : original(command, ...rest));
    const generated = soundSession(wav(), true);
    generated.candidates[0]!.changes[0]!.source_display = null;
    generated.candidates[0]!.changes[0]!.rendered_display = null;
    h.setSession(generated);
    mount(h); await reopen(h);
    expect(screen.getByRole('table', { name: 'Exact native changes' })).toHaveTextContent('Unavailable / 64');
    expect(screen.getByRole('table', { name: 'Native field scope and protections' })).toHaveTextContent('allowed: 0, 80, 127');
    fireEvent.change(screen.getByLabelText('Supplied candidate recording WAV (0.05-8s)'), { target: { files: [] } });
    expect(screen.getByText(/No measured recording/)).toBeInTheDocument();
  });

  it('passes the WCAG AA structural scan for the open actual workflow', async () => {
    const h = soundHarness(); h.setSession(soundSession(wav(), true));
    const { container } = mount(h, true);
    fireEvent.click(screen.getByRole('button', { name: 'Open reference sound' }));
    await reopen(h);
    const result = await runAxe(container);
    expect(result.violations, violationSummary(result)).toEqual([]);
  });
});
