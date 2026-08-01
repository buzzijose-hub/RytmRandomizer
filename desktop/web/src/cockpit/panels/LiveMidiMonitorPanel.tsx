/**
 * LiveMidiMonitorPanel — scrolling coalesced feed of passive `midi_activity`
 * batches. The passive table renders through the generic PanelRenderer; the
 * bespoke strip on top provides pause / clear / copy plus channel + text
 * filters, and a flash-rate-capped activity indicator (< 3 flashes/s).
 *
 * Read-only listening per the Live-but-Passive rule: nothing here can send.
 */

import { useEffect, useRef, useState } from 'react';

import { useCockpitStore } from '../../state';

import {
  FLASH_MIN_INTERVAL_MS,
  FLASH_ON_MS,
  filterMonitorRows,
  liveMidiMonitorPanelSpec,
  monitorChannels,
  shouldFlash,
} from './liveMidiMonitorPanelSpec';
import { PanelRenderer } from './PanelRenderer';

// Re-exported so tests exercise the cap constants from one import site.
export { FLASH_MIN_INTERVAL_MS, FLASH_ON_MS };

export function LiveMidiMonitorPanel(): JSX.Element {
  const rows = useCockpitStore((s) => s.midiActivityRows);
  const meta = useCockpitStore((s) => s.midiActivityMeta);
  const paused = useCockpitStore((s) => s.midiActivityPaused);
  const batchCount = useCockpitStore((s) => s.midiActivityBatchCount);
  const setPaused = useCockpitStore((s) => s.setMidiActivityPaused);
  const clearActivity = useCockpitStore((s) => s.clearMidiActivity);
  const [channel, setChannel] = useState('all');
  const [textFilter, setTextFilter] = useState('');
  const [note, setNote] = useState<string | null>(null);
  const [flash, setFlash] = useState(false);
  const lastFlashAt = useRef(0);

  // Flash trigger: rate-capped by shouldFlash so bursts (server cadence is
  // one batch per 60ms) light the dot at most once per FLASH_MIN_INTERVAL_MS.
  useEffect(() => {
    if (batchCount === 0) return;
    const now = Date.now();
    if (!shouldFlash(lastFlashAt.current, now)) return;
    lastFlashAt.current = now;
    setFlash(true);
  }, [batchCount]);

  // Flash decay: a separate effect so an in-window batch cannot cancel the
  // pending off-timer (it early-returns above without touching `flash`).
  useEffect(() => {
    if (!flash) return undefined;
    const timer = setTimeout(() => setFlash(false), FLASH_ON_MS);
    return () => clearTimeout(timer);
  }, [flash]);

  const filtered = filterMonitorRows(rows, channel, textFilter);

  const copyRows = (): void => {
    const clip = navigator.clipboard as Clipboard | undefined;
    if (clip === undefined) {
      setNote('clipboard unavailable');
      return;
    }
    clip
      .writeText(JSON.stringify(filtered, null, 2))
      .then(() => setNote(`copied ${filtered.length} rows`))
      .catch(() => setNote('copy failed'));
  };

  return (
    <div className="cockpit-panel-stack" data-testid="live-midi-monitor">
      <div className="cockpit-panel-controls">
        <span
          className={flash ? 'midi-activity-dot flashing' : 'midi-activity-dot'}
          data-testid="midi-activity-dot"
          aria-hidden="true"
        >
          ●
        </span>
        <button type="button" onClick={() => setPaused(!paused)} data-testid="monitor-pause">
          {paused ? 'Resume' : 'Pause'}
        </button>
        <button type="button" onClick={clearActivity} data-testid="monitor-clear">
          Clear
        </button>
        <button type="button" onClick={copyRows} data-testid="monitor-copy">
          Copy rows
        </button>
        <label>
          Channel
          <select
            value={channel}
            onChange={(ev) => setChannel(ev.target.value)}
            data-testid="monitor-channel-filter"
          >
            <option value="all">all</option>
            {monitorChannels(rows).map((ch) => (
              <option key={ch} value={String(ch)}>
                pad {ch + 1}
              </option>
            ))}
          </select>
        </label>
        <label>
          Filter
          <input
            value={textFilter}
            onChange={(ev) => setTextFilter(ev.target.value)}
            data-testid="monitor-text-filter"
          />
        </label>
        {note !== null && <span className="cockpit-panel-note">{note}</span>}
      </div>
      <PanelRenderer spec={liveMidiMonitorPanelSpec(filtered, meta, paused)} />
    </div>
  );
}
