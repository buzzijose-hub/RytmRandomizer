/**
 * HistoryStrip — bottom row of dots representing snapshot history.
 *
 * Color coding per spec:
 *   - green = saved snapshot
 *   - grey  = auto snapshot (post-send)
 *   - cyan (glowing) = current snapshot (overrides the kind)
 *
 * Clicking a dot emits `load_snapshot { snapshot_id }`.
 *
 * ARIA Authoring Practices §"Tabs" roving tabindex pattern on the dots:
 * only one dot is in the tab stop at a time (the current snapshot when
 * present, otherwise the first). Left/Right/Home/End move focus within
 * the strip without leaving it.
 */

import { useEffect, useRef, useState } from 'react';

import { nextIndex } from '../a11y';
import { useCockpitStore } from '../state';

import { useCockpitClient } from './context';

export function HistoryStrip(): JSX.Element {
  const history = useCockpitStore((s) => s.history);
  const client = useCockpitClient();
  const buttonRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [focusedIndex, setFocusedIndex] = useState<number>(0);

  // Keep the roving tab stop on the current snapshot whenever the
  // store's `current_id` changes (e.g. after a load_snapshot round-trip).
  const currentId = history?.current_id ?? null;
  const entries = history?.entries ?? [];
  const currentIdx =
    currentId === null ? -1 : entries.findIndex((e) => e.snapshot.snapshot_id === currentId);
  useEffect(() => {
    if (currentIdx >= 0) setFocusedIndex(currentIdx);
  }, [currentIdx]);

  if (history === null || history.entries.length === 0) {
    return (
      <div className="history-strip" data-testid="history-strip">
        <span className="history-empty">No history yet</span>
      </div>
    );
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>): void => {
    const next = nextIndex(focusedIndex, history.entries.length, event.key);
    if (next === focusedIndex) return;
    event.preventDefault();
    setFocusedIndex(next);
    queueMicrotask(() => buttonRefs.current[next]?.focus());
  };

  return (
    <div className="history-strip" data-testid="history-strip">
      <div className="history-strip-dots">
        {history.entries.map((entry, index) => {
          const id = entry.snapshot.snapshot_id;
          const isCurrent = id === history.current_id;
          const isSaved = entry.kind === 'saved';
          const classes = ['history-dot'];
          if (isSaved) classes.push('saved');
          if (isCurrent) classes.push('current');
          const label = entry.label ?? id;
          const isFocusStop = index === focusedIndex;
          return (
            <button
              key={id}
              ref={(el) => {
                buttonRefs.current[index] = el;
              }}
              type="button"
              className={classes.join(' ')}
              aria-label={`Load snapshot ${label}`}
              aria-current={isCurrent ? 'true' : 'false'}
              tabIndex={isFocusStop ? 0 : -1}
              data-testid={`history-dot-${id}`}
              onClick={() => {
                setFocusedIndex(index);
                void client.send({ type: 'load_snapshot', snapshot_id: id });
              }}
              onKeyDown={handleKeyDown}
            />
          );
        })}
      </div>
    </div>
  );
}
