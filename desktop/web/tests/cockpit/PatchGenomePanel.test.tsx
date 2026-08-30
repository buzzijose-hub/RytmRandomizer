import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { PatchGenomePanel } from '../../src/cockpit/PatchGenomePanel';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, patchGenome } from './_fixtures';

function renderPanel(withPayload = true, previewOn = false): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  if (withPayload) {
    act(() => useCockpitStore.getState().setPatchGenome(patchGenome));
  }
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <PatchGenomePanel previewOn={previewOn} />
    </CockpitClientProvider>,
  );
  return fake;
}

describe('PatchGenomePanel', () => {
  beforeEach(() => useCockpitStore.getState().reset());
  afterEach(() => useCockpitStore.getState().reset());

  it('renders the sidecar-backed compiler surface with hardware send locked', () => {
    renderPanel();

    const panel = screen.getByTestId('patch-genome-panel');
    expect(panel).toHaveTextContent('A4 Patch Genome');
    expect(screen.getByDisplayValue('Tight warehouse pressure')).toBeInTheDocument();
    expect(panel).toHaveTextContent('Brighter sync');
    expect(panel).toHaveTextContent('Candidate 2 of 4');
    expect(screen.getByRole('button', { name: 'Hardware send locked' })).toBeDisabled();
  });

  it('shows when the Rytm preview overlay is active', () => {
    renderPanel(true, true);

    expect(screen.getByText('Preview overlay active')).toBeInTheDocument();
  });

  it('marks an A4 genome stale after a scope change and clears it on fresh analysis data', () => {
    renderPanel();

    act(() => useCockpitStore.getState().setA4TrackLocks([2]));

    expect(screen.getByTestId('patch-genome-stale')).toHaveTextContent(
      'mutation targets or locks changed',
    );
    expect(screen.getByRole('button', { name: 'Grow candidate' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Reset selection' })).toBeDisabled();

    act(() => useCockpitStore.getState().setPatchGenome(patchGenome));
    expect(screen.queryByTestId('patch-genome-stale')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Grow candidate' })).toBeEnabled();
  });

  it('switches between real candidate columns and resets to the compiler selection', () => {
    renderPanel();

    fireEvent.click(screen.getByTestId('patch-genome-candidate-4'));
    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Candidate 4 of 4');

    fireEvent.click(screen.getByRole('button', { name: 'Grow candidate' }));
    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Candidate 1 of 4');

    fireEvent.click(screen.getByRole('button', { name: 'Reset selection' }));
    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Candidate 2 of 4');
  });

  it('switches mapped families and keeps gene locks local', () => {
    const fake = renderPanel();
    fireEvent.click(screen.getByTestId('patch-genome-family-filter_fx'));
    const gene = screen.getByTestId('patch-genome-gene-2-filter-a-filt1-frq');

    expect(screen.getByTestId('patch-genome-selected-family')).toHaveTextContent('Filter / FX');
    expect(gene).toHaveTextContent('FILT1 FRQ');
    expect(gene).toHaveTextContent('Screen review');

    fireEvent.click(within(gene).getByRole('button', { name: /lock filt1 frq/i }));
    expect(gene).toHaveTextContent('Locked locally');
    fireEvent.click(within(gene).getByRole('button', { name: /unlock filt1 frq/i }));
    expect(gene).toHaveTextContent('Screen review');
    expect(fake.sent).toHaveLength(0);
  });

  it('submits a passive compiler request with description and track', async () => {
    const fake = renderPanel();
    fake.ackQueue.push({ request_id: 'genome', ok: true, patch_genome: patchGenome });
    fireEvent.change(screen.getByLabelText('Source description'), {
      target: { value: 'Brittle sync pressure' },
    });
    fireEvent.change(screen.getByLabelText('Track'), { target: { value: '4' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analyze source' }));

    await waitFor(() => {
      expect(fake.sent).toContainEqual({
        type: 'analyze_patch_genome',
        description: 'Brittle sync pressure',
        track: 4,
      });
    });
  });

  it('multi-selects A4 mutation targets and shows inactive and locked tracks', async () => {
    const fake = renderPanel();

    fireEvent.click(screen.getByRole('button', { name: 'Target track 2' }));
    await waitFor(() => {
      expect(fake.sent).toContainEqual({
        type: 'set_mutation_targets',
        device_id: 'analog_four_mk2',
        target_ids: [2],
      });
    });
    expect(screen.getByTestId('a4-target-control-1')).toHaveClass('inactive');
    expect(screen.getByTestId('a4-target-control-2')).toHaveClass('targeted');

    fireEvent.click(screen.getByRole('button', { name: 'Lock track 2' }));
    expect(fake.sent).toContainEqual({
      type: 'set_a4_track_lock',
      track: 2,
      locked: true,
    });
    expect(screen.getByTestId('a4-target-control-2')).toHaveClass('locked');
    expect(screen.getByRole('button', { name: 'Analyze source' })).toBeDisabled();
  });

  it('shows a waiting state before the bootstrap compiler packet arrives', () => {
    renderPanel(false);

    expect(screen.getByTestId('patch-genome-empty')).toHaveTextContent(
      'Waiting for the passive sidecar compiler packet',
    );
    expect(screen.getByRole('button', { name: 'Grow candidate' })).toBeDisabled();
  });

  it('validates an empty description without sending a command', () => {
    const fake = renderPanel();
    fireEvent.change(screen.getByLabelText('Source description'), { target: { value: '   ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analyze source' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Describe the patch before analyzing');
    expect(fake.sent).toHaveLength(0);
  });

  it.each([
    [{ request_id: 'message', ok: false, message: 'Description rejected' }, 'Description rejected'],
    [{ request_id: 'error', ok: false, error: 'Compiler offline' }, 'Compiler offline'],
    [{ request_id: 'fallback', ok: false }, 'Compiler request rejected'],
  ])('shows a passive compiler rejection from %o', async (ack, expected) => {
    const fake = renderPanel();
    fake.ackQueue.push(ack);

    fireEvent.click(screen.getByRole('button', { name: 'Analyze source' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(expected);
    expect(useCockpitStore.getState().operatorLog.at(-1)?.level).toBe('error');
  });

  it('handles a non-error compiler transport rejection', async () => {
    const fake = renderPanel();
    fake.nextRejection = 'transport closed';

    fireEvent.click(screen.getByRole('button', { name: 'Analyze source' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('transport closed');
  });

  it('accepts a successful compiler ack without an inline payload', async () => {
    const fake = renderPanel();

    fireEvent.click(screen.getByRole('button', { name: 'Analyze source' }));

    await waitFor(() => expect(fake.sent).toHaveLength(1));
    expect(useCockpitStore.getState().patchGenome).toBe(patchGenome);
    expect(useCockpitStore.getState().operatorLog.at(-1)?.level).toBe('success');
  });
});
