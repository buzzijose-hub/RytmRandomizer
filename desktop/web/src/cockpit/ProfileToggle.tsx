/**
 * ProfileToggle — pill toggle between "Scene" (built-in profiles) and "Inspiration" (user
 * profiles trained from style sources). Spec calls these tabs.
 *
 * Local state held by the parent (<MutationPanel />). Component is pure & dumb.
 */

import type { ProfileKind } from '../ws/protocol';

export interface ProfileToggleProps {
  value: ProfileKind;
  onChange: (kind: ProfileKind) => void;
}

export function ProfileToggle({ value, onChange }: ProfileToggleProps): JSX.Element {
  return (
    <div className="profile-toggle" role="tablist" data-testid="profile-toggle">
      <button
        type="button"
        role="tab"
        aria-selected={value === 'scene'}
        className={value === 'scene' ? 'active' : ''}
        onClick={() => onChange('scene')}
      >
        Scene
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={value === 'user'}
        className={value === 'user' ? 'active' : ''}
        onClick={() => onChange('user')}
      >
        Inspiration
      </button>
    </div>
  );
}
