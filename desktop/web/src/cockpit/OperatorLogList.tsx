/**
 * OperatorLogList — the single log-list component in the cockpit.
 *
 * Extracted verbatim from the markup that lived inline in `SafetyRail.tsx`
 * (same `<ol class="operator-log-list">` / `<li class="operator-log-entry
 * {level}">` shape, same styles in `styles.css`), so the Safety Rail's
 * rendering is unchanged and the update panel's "Recent update activity"
 * list reuses it rather than forking a second journal list — the fork the
 * plan's reuse contract R4 exists to prevent (Gate 17).
 *
 * It is deliberately dumb: entries in, list out. Severity is expressed as
 * a border/colour class AND carried in the entry text by the caller, never
 * by hue alone; the list itself adds no colour-only meaning.
 */

export interface OperatorLogListEntry {
  readonly id: string;
  readonly level: 'info' | 'success' | 'error';
  readonly message: string;
}

export interface OperatorLogListProps {
  readonly entries: ReadonlyArray<OperatorLogListEntry>;
  /** Copy shown in place of the list when there is nothing to show. */
  readonly emptyText: string;
  /** `data-testid` on the `<ol>`; each surface names its own list. */
  readonly testId: string;
  /** Accessible name for the list. */
  readonly label: string;
}

export function OperatorLogList({
  entries,
  emptyText,
  testId,
  label,
}: OperatorLogListProps): JSX.Element {
  if (entries.length === 0) {
    return <div className="operator-log-empty">{emptyText}</div>;
  }
  return (
    <ol className="operator-log-list" data-testid={testId} aria-label={label}>
      {entries.map((entry) => (
        <li key={entry.id} className={`operator-log-entry ${entry.level}`}>
          {entry.message}
        </li>
      ))}
    </ol>
  );
}
