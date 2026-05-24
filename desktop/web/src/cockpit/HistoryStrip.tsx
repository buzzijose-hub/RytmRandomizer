/**
 * HistoryStrip — bottom row of dots representing snapshot history.
 *
 * Color coding per spec:
 *   - green = saved snapshot
 *   - grey  = auto snapshot (post-send)
 *   - cyan (glowing) = current snapshot (overrides the kind)
 *
 * Clicking a dot emits `load_snapshot { snapshot_id }`.
 */

import { useCockpitStore } from '../state';

import { useCockpitClient } from './context';

export function HistoryStrip(): JSX.Element {
  const history = useCockpitStore((s) => s.history);
  const client = useCockpitClient();

  if (history === null || history.entries.length === 0) {
    return (
      <div className="history-strip" data-testid="history-strip">
        <span className="history-empty">No history yet</span>
      </div>
    );
  }

  return (
    <div className="history-strip" data-testid="history-strip">
      <div className="history-strip-dots">
        {history.entries.map((entry) => {
          const id = entry.snapshot.snapshot_id;
          const isCurrent = id === history.current_id;
          const isSaved = entry.kind === 'saved';
          const classes = ['history-dot'];
          if (isSaved) classes.push('saved');
          if (isCurrent) classes.push('current');
          const label = entry.label ?? id;
          return (
            <button
              key={id}
              type="button"
              className={classes.join(' ')}
              aria-label={`Load snapshot ${label}`}
              aria-current={isCurrent ? 'true' : 'false'}
              data-testid={`history-dot-${id}`}
              onClick={() => {
                void client.send({ type: 'load_snapshot', snapshot_id: id });
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
