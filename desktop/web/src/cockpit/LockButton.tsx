/**
 * LockButton — small affordance toggling a pad's lock state.
 *
 * Shows 🔒 when locked, 🔓 when unlocked. Click fires `onToggle`. The parent (`<PadCard />`)
 * owns the actual lock state via the `usePadLocks` hook.
 */

export interface LockButtonProps {
  locked: boolean;
  onToggle: () => void;
  /** Pad id, used only for accessibility labelling. */
  padId: number;
  itemLabel?: 'pad' | 'track';
}

export function LockButton({
  locked,
  onToggle,
  padId,
  itemLabel = 'pad',
}: LockButtonProps): JSX.Element {
  const className = locked ? 'lock-button locked' : 'lock-button';
  const label = locked
    ? `Unlock ${itemLabel} ${padId}`
    : `Lock ${itemLabel} ${padId}`;
  return (
    <button
      type="button"
      className={className}
      onClick={onToggle}
      aria-label={label}
      aria-pressed={locked}
      title={label}
    >
      {locked ? '🔒' : '🔓'}
    </button>
  );
}
