/**
 * Tests for HistoryStrip - expandable snapshot recall list.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { HistoryStrip } from '../../src/cockpit/HistoryStrip';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, history, snapshot } from './_fixtures';

function renderWith(): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <HistoryStrip />
    </CockpitClientProvider>,
  );
  return fake;
}

describe('HistoryStrip', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
  });
  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  it('renders "No history yet" when history is null', () => {
    renderWith();
    expect(screen.getByText('No history yet')).toBeInTheDocument();
  });

  it('renders "No history yet" when history has zero entries', () => {
    useCockpitStore.getState().setHistory({ entries: [], current_id: '' });
    renderWith();
    expect(screen.getByText('No history yet')).toBeInTheDocument();
  });

  it('renders an expandable recall list with labels, kind, via, and current state', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const row1 = screen.getByTestId('history-row-snap-1');
    const row2 = screen.getByTestId('history-row-snap-2');
    const row3 = screen.getByTestId('history-row-snap-3');
    expect(screen.getByTestId('history-list')).toBeInTheDocument();
    expect(row1).toHaveTextContent('snap-1');
    expect(row2).toHaveTextContent('auto');
    expect(row2).toHaveTextContent('send');
    expect(row3).toHaveTextContent('industrial-peak');
    expect(row3).toHaveTextContent('saved');
    expect(row3).toHaveTextContent('current');
    expect(row3).toHaveClass('current');
  });

  it('renders no bpm when a snapshot entry has no tempo', () => {
    useCockpitStore.getState().setHistory({
      entries: [
        {
          snapshot: { ...snapshot, bpm: null },
          kind: 'auto',
          parent_id: null,
          via: null,
          label: null,
        },
      ],
      current_id: 'snap-1',
    });
    renderWith();
    expect(screen.getByTestId('history-row-snap-1')).toHaveTextContent('no bpm');
  });

  it('uses entry.label in the load button aria-label when present, otherwise snapshot_id', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    expect(screen.getByLabelText('Load snapshot industrial-peak')).toBeInTheDocument();
    expect(screen.getByLabelText('Load snapshot snap-1')).toBeInTheDocument();
  });

  it('clicking a row load button emits load_snapshot with that snapshot_id', () => {
    useCockpitStore.getState().setHistory(history);
    const fake = renderWith();
    fireEvent.click(screen.getByTestId('history-load-snap-1'));
    expect(fake.sent).toEqual([{ type: 'load_snapshot', snapshot_id: 'snap-1' }]);
  });
});
