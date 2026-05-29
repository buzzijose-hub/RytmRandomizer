/**
 * HistoryStrip - expandable snapshot recall list.
 *
 * The session history doubles as Jose's live cue scratchpad: each row shows
 * whether a snapshot is saved/auto, how it was reached, and whether it is
 * current. Loading still emits the existing `load_snapshot` command.
 */

import { useCockpitStore } from '../state';

import { useLoggedCommand } from './useLoggedCommand';

export function HistoryStrip(): JSX.Element {
  const history = useCockpitStore((s) => s.history);
  const sendCommand = useLoggedCommand();

  if (history === null || history.entries.length === 0) {
    return (
      <div className="history-strip" data-testid="history-strip">
        <span className="history-empty">No history yet</span>
      </div>
    );
  }

  return (
    <details className="history-strip" data-testid="history-strip" open>
      <summary>
        Snapshot recall
        <span>{history.entries.length}</span>
      </summary>
      <ol className="history-list" data-testid="history-list">
        {history.entries.map((entry, index) => {
          const id = entry.snapshot.snapshot_id;
          const isCurrent = id === history.current_id;
          const label = entry.label ?? id;
          const rowClasses = ['history-row'];
          if (isCurrent) rowClasses.push('current');
          if (entry.kind === 'saved') rowClasses.push('saved');
          return (
            <li className={rowClasses.join(' ')} data-testid={`history-row-${id}`} key={id}>
              <div className="history-row-main">
                <span className="history-index">{index + 1}</span>
                <span className="history-label">{label}</span>
                {isCurrent ? <span className="history-current">current</span> : null}
              </div>
              <div className="history-row-meta">
                <span>{entry.kind}</span>
                <span>{entry.via ?? 'initial'}</span>
                <span>{entry.snapshot.bpm === null ? 'no bpm' : `${entry.snapshot.bpm} BPM`}</span>
              </div>
              <button
                type="button"
                className="history-load-button"
                aria-label={`Load snapshot ${label}`}
                data-testid={`history-load-${id}`}
                onClick={() => {
                  sendCommand({ type: 'load_snapshot', snapshot_id: id });
                }}
              >
                Load
              </button>
            </li>
          );
        })}
      </ol>
    </details>
  );
}
