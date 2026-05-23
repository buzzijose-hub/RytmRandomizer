/**
 * ProfileChips — horizontal chip list of available profiles + an active-profile card.
 *
 * The list of available profiles is provided as a prop (the engine pushes a `profile_changed`
 * event for the active one; the full registry will land on the WS-K → integration side. For
 * the v10 layout we accept an `available` list so storybook / tests can drive it directly).
 *
 * Clicking a chip emits `select_profile`. The active profile (from the store) is highlighted
 * and its body is rendered as a card with traits + an EXPORT button.
 */

import { useCockpitStore } from '../state';
import type { ProfileKind, ProfileModel } from '../ws/protocol';

import { useCockpitClient } from './context';

export interface ProfileChipsProps {
  /** Catalogue of profiles to show as chips. Filtered by `kind` upstream. */
  available: ReadonlyArray<{ profile_id: string; name: string; kind: ProfileKind }>;
}

export function ProfileChips({ available }: ProfileChipsProps): JSX.Element {
  const active = useCockpitStore((s) => s.profile);
  const client = useCockpitClient();

  return (
    <div className="profile-chips" data-testid="profile-chips">
      <div className="profile-chip-list">
        {available.length === 0 ? (
          <span className="panel-meta">No profiles available</span>
        ) : (
          available.map((p) => {
            const isActive = active !== null && active.profile_id === p.profile_id;
            return (
              <button
                key={p.profile_id}
                type="button"
                className={isActive ? 'profile-chip active' : 'profile-chip'}
                aria-pressed={isActive}
                data-testid={`profile-chip-${p.profile_id}`}
                onClick={() => {
                  void client.send({ type: 'select_profile', profile_id: p.profile_id });
                }}
              >
                {isActive ? '★ ' : ''}
                {p.name}
              </button>
            );
          })
        )}
      </div>
      {active === null ? null : <ActiveProfileCard profile={active} />}
    </div>
  );
}

function ActiveProfileCard({ profile }: { profile: ProfileModel }): JSX.Element {
  const client = useCockpitClient();
  return (
    <div className="profile-active-card" data-testid="profile-active-card">
      <div className="name">★ {profile.name}</div>
      <div className="meta">
        model {profile.model_version} · {profile.source_summary}
      </div>
      <div className="profile-traits">
        {profile.traits.map((t) => (
          <div key={t.name} className="profile-trait">
            <span>{t.name}</span>
            <span>{Math.round(t.value * 100)}%</span>
          </div>
        ))}
      </div>
      <button
        type="button"
        className="profile-export-button"
        data-testid="profile-export-button"
        onClick={() => {
          void client.send({
            type: 'export_profile_model',
            profile_id: profile.profile_id,
            target: 'binary',
          });
        }}
      >
        ↗ EXPORT MODEL
      </button>
    </div>
  );
}
