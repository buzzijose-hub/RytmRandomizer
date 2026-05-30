/**
 * ProfileToggle — pill toggle between "Scene" (built-in profiles) and "Inspiration" (user
 * profiles trained from style sources). Spec calls these tabs.
 *
 * Local state held by the parent (<MutationPanel />). Component is pure & dumb.
 *
 * ARIA Authoring Practices §"Tabs": roving tabindex + Left/Right/Home/End.
 * Only the selected tab is in the document tab order (tabIndex=0);
 * unselected tabs use tabIndex=-1 and are reachable only via the arrow
 * keys while the tablist is focused.
 */

import { useRef } from 'react';

import { nextIndex } from '../a11y';
import type { ProfileKind } from '../ws/protocol';

const TAB_ORDER: readonly ProfileKind[] = ['scene', 'user'] as const;

export interface ProfileToggleProps {
  value: ProfileKind;
  onChange: (kind: ProfileKind) => void;
}

export function ProfileToggle({ value, onChange }: ProfileToggleProps): JSX.Element {
  const buttonRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const focusedIndex = TAB_ORDER.indexOf(value);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>): void => {
    const next = nextIndex(focusedIndex, TAB_ORDER.length, event.key);
    if (next === focusedIndex) return;
    event.preventDefault();
    const targetKind = TAB_ORDER[next];
    if (targetKind === undefined) return;
    onChange(targetKind);
    // Focus must move synchronously with the selection per the tabs pattern.
    queueMicrotask(() => buttonRefs.current[next]?.focus());
  };

  return (
    <div className="profile-toggle" role="tablist" data-testid="profile-toggle">
      {TAB_ORDER.map((kind, index) => {
        const selected = value === kind;
        return (
          <button
            key={kind}
            ref={(el) => {
              buttonRefs.current[index] = el;
            }}
            type="button"
            role="tab"
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            className={selected ? 'active' : ''}
            onClick={() => onChange(kind)}
            onKeyDown={handleKeyDown}
          >
            {kind === 'scene' ? 'Scene' : 'Inspiration'}
          </button>
        );
      })}
    </div>
  );
}
