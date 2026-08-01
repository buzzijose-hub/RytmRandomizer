/**
 * Live MIDI Monitor — pure spec selector branches + the interactive strip
 * (pause / clear / copy / filters) + the flash-rate-capped indicator.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/react';

import { LiveMidiMonitorPanel } from '../../../src/cockpit/panels/LiveMidiMonitorPanel';
import {
  FLASH_MIN_INTERVAL_MS,
  FLASH_ON_MS,
  filterMonitorRows,
  liveMidiMonitorPanelSpec,
  monitorChannels,
  shouldFlash,
} from '../../../src/cockpit/panels/liveMidiMonitorPanelSpec';
import { useCockpitStore, type MonitorRow } from '../../../src/state';

import { midiBatch } from '../_fixtures';

const rowA: MonitorRow = {
  id: 'r-1',
  channel: 0,
  pad: 1,
  control: 16,
  value: 90,
  repeat_count: 3,
  observed_at: 12.5,
  labels: ['BD Tune'],
};

const rowB: MonitorRow = {
  id: 'r-2',
  channel: 1,
  pad: 2,
  control: 24,
  value: 64,
  repeat_count: 1,
  observed_at: 12.6,
  labels: [],
};

describe('liveMidiMonitorPanelSpec (pure)', () => {
  it('renders the empty-meta chip and the paused badge', () => {
    const spec = liveMidiMonitorPanelSpec([], null, true);
    expect(spec.status_badges[0]).toMatchObject({ label: 'paused', tone: 'warn' });
    expect(spec.sections[0]!.chips).toEqual(['no input batches yet']);
    expect(spec.sections[1]!.table!.rows).toEqual([]);
  });

  it('renders meta chips, newest-first rows, and the listening badge', () => {
    const spec = liveMidiMonitorPanelSpec(
      [rowA, rowB],
      { port: 'IN', dropped: 1, ignored: 2, read_errors: 3 },
      false,
    );
    expect(spec.status_badges[0]).toMatchObject({ label: 'listening', tone: 'ok' });
    expect(spec.sections[0]!.chips).toEqual([
      'port: IN',
      'dropped: 1',
      'ignored: 2',
      'read errors: 3',
    ]);
    expect(spec.sections[1]!.table!.rows).toEqual([
      ['2', '24', '64', '1', ''],
      ['1', '16', '90', '3', 'BD Tune'],
    ]);
  });

  it('filterMonitorRows applies channel and text filters', () => {
    const rows = [rowA, rowB];
    expect(filterMonitorRows(rows, 'all', '')).toEqual(rows);
    expect(filterMonitorRows(rows, '0', '')).toEqual([rowA]);
    expect(filterMonitorRows(rows, 'all', 'bd tune')).toEqual([rowA]);
    expect(filterMonitorRows(rows, 'all', '24')).toEqual([rowB]);
    expect(filterMonitorRows(rows, 'all', 'nothing')).toEqual([]);
    expect(filterMonitorRows(rows, '1', 'bd tune')).toEqual([]);
  });

  it('monitorChannels returns unique sorted channels', () => {
    expect(monitorChannels([rowB, rowA, rowA])).toEqual([0, 1]);
    expect(monitorChannels([])).toEqual([]);
  });

  it('shouldFlash enforces the sub-3-per-second cap', () => {
    expect(shouldFlash(0, FLASH_MIN_INTERVAL_MS)).toBe(true);
    expect(shouldFlash(1000, 1000 + FLASH_MIN_INTERVAL_MS - 1)).toBe(false);
    expect(1000 / FLASH_MIN_INTERVAL_MS).toBeLessThan(3);
  });
});

describe('LiveMidiMonitorPanel (interactive)', () => {
  beforeEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });
  afterEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('renders the store ring through the PanelRenderer and pauses/clears it', () => {
    render(<LiveMidiMonitorPanel />);
    act(() => {
      useCockpitStore.getState().appendMidiActivity(midiBatch);
    });

    const panel = screen.getByTestId('cockpit-panel-live-midi-monitor');
    expect(within(panel).getByRole('cell', { name: 'BD Tune' })).toBeInTheDocument();
    expect(panel).toHaveTextContent('port: Analog Rytm MK2 IN');

    fireEvent.click(screen.getByTestId('monitor-pause'));
    expect(useCockpitStore.getState().midiActivityPaused).toBe(true);
    expect(screen.getByTestId('monitor-pause')).toHaveTextContent('Resume');
    expect(panel).toHaveTextContent('paused');

    fireEvent.click(screen.getByTestId('monitor-pause'));
    expect(useCockpitStore.getState().midiActivityPaused).toBe(false);

    fireEvent.click(screen.getByTestId('monitor-clear'));
    expect(useCockpitStore.getState().midiActivityRows).toEqual([]);
  });

  it('filters by channel and text through the labelled controls', () => {
    act(() => {
      useCockpitStore.getState().appendMidiActivity(midiBatch);
    });
    render(<LiveMidiMonitorPanel />);

    const select = screen.getByTestId('monitor-channel-filter');
    expect(within(select).getAllByRole('option').map((o) => o.textContent)).toEqual([
      'all',
      'pad 1',
      'pad 2',
    ]);
    fireEvent.change(select, { target: { value: '1' } });

    const panel = screen.getByTestId('cockpit-panel-live-midi-monitor');
    expect(within(panel).queryByRole('cell', { name: 'BD Tune' })).not.toBeInTheDocument();
    expect(within(panel).getByRole('cell', { name: '24' })).toBeInTheDocument();

    fireEvent.change(screen.getByTestId('monitor-text-filter'), {
      target: { value: 'no-match' },
    });
    expect(within(panel).queryByRole('cell', { name: '24' })).not.toBeInTheDocument();
  });

  it('copy reports clipboard-unavailable, success, and failure', async () => {
    render(<LiveMidiMonitorPanel />);

    // jsdom has no clipboard by default → unavailable branch.
    fireEvent.click(screen.getByTestId('monitor-copy'));
    expect(await screen.findByText('clipboard unavailable')).toBeInTheDocument();

    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } });
    fireEvent.click(screen.getByTestId('monitor-copy'));
    expect(await screen.findByText('copied 0 rows')).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith('[]');

    writeText.mockRejectedValueOnce(new Error('denied'));
    fireEvent.click(screen.getByTestId('monitor-copy'));
    expect(await screen.findByText('copy failed')).toBeInTheDocument();
  });

  it('flashes the activity dot at most once per interval and clears after FLASH_ON_MS', () => {
    vi.useFakeTimers();
    render(<LiveMidiMonitorPanel />);
    const dot = screen.getByTestId('midi-activity-dot');
    expect(dot.className).not.toContain('flashing');

    act(() => {
      useCockpitStore.getState().appendMidiActivity(midiBatch);
    });
    expect(dot.className).toContain('flashing');

    // A second batch inside the cap window must NOT restart the flash timer.
    act(() => {
      vi.advanceTimersByTime(FLASH_ON_MS - 50);
      useCockpitStore.getState().appendMidiActivity(midiBatch);
    });
    act(() => {
      vi.advanceTimersByTime(50);
    });
    expect(dot.className).not.toContain('flashing');

    // After the interval has elapsed, the next batch flashes again.
    act(() => {
      vi.advanceTimersByTime(FLASH_MIN_INTERVAL_MS);
      useCockpitStore.getState().appendMidiActivity(midiBatch);
    });
    expect(dot.className).toContain('flashing');
    act(() => {
      vi.advanceTimersByTime(FLASH_ON_MS);
    });
    expect(dot.className).not.toContain('flashing');
  });
});
