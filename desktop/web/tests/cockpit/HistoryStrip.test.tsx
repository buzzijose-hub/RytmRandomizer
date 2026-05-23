/**
 * Tests for HistoryStrip — dot rendering by kind/current, click → load_snapshot, empty state.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { HistoryStrip } from '../../src/cockpit/HistoryStrip';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, history } from './_fixtures';

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

  it('renders one dot per history entry with correct classes', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const dot1 = screen.getByTestId('history-dot-snap-1');
    const dot2 = screen.getByTestId('history-dot-snap-2');
    const dot3 = screen.getByTestId('history-dot-snap-3');
    expect(dot1.className).toBe('history-dot');
    expect(dot2.className).toBe('history-dot');
    expect(dot3.className).toBe('history-dot saved current');
    expect(dot1).toHaveAttribute('aria-current', 'false');
    expect(dot3).toHaveAttribute('aria-current', 'true');
  });

  it('uses entry.label in the aria-label when present, otherwise snapshot_id', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    expect(screen.getByLabelText('Load snapshot industrial-peak')).toBeInTheDocument();
    expect(screen.getByLabelText('Load snapshot snap-1')).toBeInTheDocument();
  });

  it('clicking a dot emits load_snapshot with that snapshot_id', () => {
    useCockpitStore.getState().setHistory(history);
    const fake = renderWith();
    fireEvent.click(screen.getByTestId('history-dot-snap-1'));
    expect(fake.sent).toEqual([{ type: 'load_snapshot', snapshot_id: 'snap-1' }]);
  });
});
