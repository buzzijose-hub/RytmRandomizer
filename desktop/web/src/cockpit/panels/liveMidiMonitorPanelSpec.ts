/**
 * Live MIDI Monitor — pure PanelSpec selector + helpers (no React, no state).
 *
 * The passive display half of the monitor goes through the schema-driven
 * PanelSpec platform (`PanelRenderer`); the interactive half (pause / clear /
 * copy / filters) lives in `LiveMidiMonitorPanel.tsx`. Read-only listening
 * per the Live-but-Passive rule — nothing here can reach a transmit path.
 */

import type { MidiActivityMeta, MonitorRow } from '../../state/store';
import type { PanelSpecDict } from '../../types/live_gui_protocol';

/** Minimum ms between activity flashes — caps the indicator under 3/s. */
export const FLASH_MIN_INTERVAL_MS = 350;

/** How long one activity flash stays lit. */
export const FLASH_ON_MS = 200;

/** True when enough time has passed since the last flash to flash again. */
export function shouldFlash(lastFlashAt: number, now: number): boolean {
  return now - lastFlashAt >= FLASH_MIN_INTERVAL_MS;
}

/** Unique 0-based channels present in the ring, ascending. */
export function monitorChannels(rows: ReadonlyArray<MonitorRow>): number[] {
  return [...new Set(rows.map((row) => row.channel))].sort((a, b) => a - b);
}

/**
 * Apply the channel + text filters. `channel` is 'all' or a 0-based channel
 * number as a string; `text` matches the CC number or any decoded label.
 */
export function filterMonitorRows(
  rows: ReadonlyArray<MonitorRow>,
  channel: string,
  text: string,
): MonitorRow[] {
  const needle = text.trim().toLowerCase();
  return rows.filter((row) => {
    if (channel !== 'all' && String(row.channel) !== channel) return false;
    if (needle === '') return true;
    return (
      String(row.control).includes(needle) ||
      row.labels.some((label) => label.toLowerCase().includes(needle))
    );
  });
}

/** Build the passive PanelSpec for the monitor (newest row first). */
export function liveMidiMonitorPanelSpec(
  rows: ReadonlyArray<MonitorRow>,
  meta: MidiActivityMeta | null,
  paused: boolean,
): PanelSpecDict {
  const newestFirst = [...rows].reverse();
  return {
    panel_id: 'live-midi-monitor',
    title: 'Live MIDI Monitor',
    status_badges: [
      paused
        ? { label: 'paused', tone: 'warn', icon: '⏸' }
        : { label: 'listening', tone: 'ok', icon: '●' },
    ],
    sections: [
      {
        heading: 'Input',
        kind: 'chips',
        rows: [],
        table: null,
        chips:
          meta === null
            ? ['no input batches yet']
            : [
                `port: ${meta.port}`,
                `dropped: ${meta.dropped}`,
                `ignored: ${meta.ignored}`,
                `read errors: ${meta.read_errors}`,
              ],
      },
      {
        heading: 'Activity',
        kind: 'table',
        rows: [],
        table: {
          columns: ['Pad/Ch', 'CC', 'Value', 'Repeats', 'Labels'],
          rows: newestFirst.map((row) => [
            String(row.pad),
            String(row.control),
            String(row.value),
            String(row.repeat_count),
            row.labels.join(', '),
          ]),
        },
        chips: [],
      },
    ],
    required_actions: [],
    blocked_actions: [],
    safety_lines: ['read-only listening — no transmit path'],
  };
}
