import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { RehearsalFavoriteControls } from '../../src/cockpit/panels/RehearsalFavoriteControls';
import { useCockpitStore } from '../../src/state';
import type { CommandAck, LibraryRecord } from '../../src/ws/protocol';
import { candidate, FakeCockpitClient, libraryRecordA, sendPlan, sessionLive } from './_fixtures';
import { rehearsalRecord } from './parameterScopeFixture';

function mount(fake: FakeCockpitClient, records: LibraryRecord[] | null = [libraryRecordA, rehearsalRecord]) {
  return render(<CockpitClientProvider client={fake.asClient()}><RehearsalFavoriteControls records={records} /></CockpitClientProvider>);
}
function prepare(): void {
  useCockpitStore.setState({ previewCandidate: candidate, connectionStatus: 'connected', sendPlan, sessionStatus: sessionLive });
}
async function retain(): Promise<void> {
  fireEvent.change(screen.getByTestId('favorite-name'), { target: { value: '  Rehearsal A  ' } });
  await act(async () => fireEvent.click(screen.getByTestId('favorite-retain')));
}
async function recall(): Promise<void> {
  fireEvent.change(screen.getByTestId('favorite-record'), { target: { value: rehearsalRecord.record_id } });
  await act(async () => fireEvent.click(screen.getByTestId('favorite-reopen')));
}

beforeEach(() => useCockpitStore.getState().reset());
afterEach(() => useCockpitStore.getState().reset());

describe('local rehearsal favorite UX', () => {
  it('requires candidate/name/connection and only lists explicitly local favorite records', () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    expect(screen.getByTestId('favorite-retain')).toBeDisabled();
    expect(screen.getByTestId('favorite-reopen')).toBeDisabled();
    expect(screen.queryByRole('option', { name: /INDUSTRIAL KIT/ })).not.toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Pad 2 rehearsal/ })).toBeVisible();
    expect(screen.getByText(/Hardware SAVE and manual KIT reload are separate/)).toBeVisible();
    expect(fake.sent).toEqual([]);
  });
  it('retains through LibraryStore with exact source/seed/depth summary and no hardware action', async () => {
    prepare();
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'saved', ok: true, library_records: [rehearsalRecord] });
    mount(fake);
    expect(screen.getByTestId('favorite-candidate-summary')).toHaveTextContent('snap-1');
    expect(screen.getByTestId('favorite-candidate-summary')).toHaveTextContent('seed 12345; depth 45%');
    await retain();
    expect(fake.sent).toEqual([{ type: 'retain_rehearsal_favorite', name: 'Rehearsal A' }]);
    expect(useCockpitStore.getState().libraryRecords).toEqual([rehearsalRecord]);
    expect(screen.getByRole('status')).toHaveTextContent('Favorite retained locally. Hardware KIT unchanged.');
    expect(useCockpitStore.getState().previewCandidate).toEqual(candidate);
  });
  it('reopens by id, invalidating candidate/plan before acknowledgment without trusting stored metadata', async () => {
    prepare();
    const fake = new FakeCockpitClient();
    mount(fake);
    await recall();
    expect(fake.sent).toEqual([{ type: 'recall_rehearsal_favorite', record_id: 'favorite-1' }]);
    expect(useCockpitStore.getState().previewCandidate).toBeNull();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
    expect(useCockpitStore.getState().sessionStatusStale).toBe(true);
    expect(useCockpitStore.getState().dualMachineStage).toBeNull();
    expect(screen.getByRole('status')).toHaveTextContent('Fresh preparation required');
    expect(screen.queryByText('untrusted summary')).not.toBeInTheDocument();
    expect(useCockpitStore.getState().rytmParameters).toBeNull();
  });
  it.each([{ message: 'disk full' }, { error: 'disk full' }, {}])('reports persistence refusal without a success claim: %j', async (detail) => {
    prepare();
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'failed', ok: false, ...detail });
    mount(fake);
    await retain();
    expect(screen.getByRole('alert')).toHaveTextContent(detail.message ?? detail.error ?? 'Local favorite request refused.');
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
  it.each([new Error('socket lost'), 'socket lost'])('leaves recall authority revoked on transport failure: %s', async (error) => {
    prepare();
    const fake = new FakeCockpitClient();
    fake.nextRejection = error;
    mount(fake);
    await recall();
    expect(screen.getByRole('alert')).toHaveTextContent('socket lost');
    expect(useCockpitStore.getState().sendPlan).toBeNull();
  });
  it('does not apply acknowledgments after the panel unmounts', async () => {
    prepare();
    const fake = new FakeCockpitClient();
    let resolve!: (value: CommandAck) => void;
    fake.responseQueue.push(new Promise((done) => { resolve = done; }));
    const view = mount(fake);
    await retain();
    view.unmount();
    await act(async () => resolve({ request_id: 'old', ok: true, library_records: [rehearsalRecord] }));
    expect(useCockpitStore.getState().libraryRecords).toBeNull();
  });
  it('does not publish a late unmounted failure', async () => {
    prepare();
    const fake = new FakeCockpitClient();
    let reject!: (error: Error) => void;
    fake.responseQueue.push(new Promise((_done, fail) => { reject = fail; }));
    const view = mount(fake, null);
    await retain();
    view.unmount();
    await act(async () => reject(new Error('late failure')));
    expect(useCockpitStore.getState().operatorLog).toEqual([]);
  });
  it('guards form submissions even when there is no retained candidate', () => {
    const fake = new FakeCockpitClient();
    const view = mount(fake, []);
    fireEvent.submit(view.container.querySelector('form')!);
    expect(fake.sent).toEqual([]);
  });
});
