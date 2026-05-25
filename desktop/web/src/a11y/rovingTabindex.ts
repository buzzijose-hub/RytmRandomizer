/**
 * Stateless helpers for the roving-tabindex keyboard pattern.
 *
 * Usage: composite widgets (tablists, listboxes, snapshot strips) keep
 * exactly one child in the tab stop at a time. Arrow keys move focus
 * within the widget without leaving it. Home/End jump to first/last.
 *
 * The widget tracks the focused index in state; passes each candidate
 * `tabIndex={index === focused ? 0 : -1}` and an `onKeyDown` handler
 * that calls `nextIndex(focused, length, ev.key)` then updates state +
 * focuses the new element via a ref.
 *
 * Reference: ARIA Authoring Practices §"Tabs" — https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
 */

export type RovingKey =
  | 'ArrowLeft'
  | 'ArrowRight'
  | 'ArrowUp'
  | 'ArrowDown'
  | 'Home'
  | 'End';

const NAV_KEYS: ReadonlySet<string> = new Set([
  'ArrowLeft',
  'ArrowRight',
  'ArrowUp',
  'ArrowDown',
  'Home',
  'End',
]);

/**
 * Return the next focused index given the current index, the total
 * length, and the key pressed. Returns `current` for keys that don't
 * navigate. Wraps at both ends.
 */
export function nextIndex(current: number, length: number, key: string): number {
  if (length <= 0) return 0;
  if (!NAV_KEYS.has(key)) return current;
  if (key === 'Home') return 0;
  if (key === 'End') return length - 1;
  if (key === 'ArrowRight' || key === 'ArrowDown') {
    return (current + 1) % length;
  }
  // ArrowLeft / ArrowUp
  return (current - 1 + length) % length;
}

export function isRovingKey(key: string): boolean {
  return NAV_KEYS.has(key);
}
