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

import { useState } from 'react';

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
  const [exportStatus, setExportStatus] = useState<{
    kind: 'working' | 'success' | 'error';
    message: string;
  } | null>(null);

  async function handleExport(): Promise<void> {
    setExportStatus({ kind: 'working', message: 'Preparing export...' });
    try {
      const ack = await client.send({
        type: 'export_profile_model',
        profile_id: profile.profile_id,
        target: 'binary',
      });
      if (!ack.ok) {
        throw new Error(ack.error ?? 'Export rejected by sidecar');
      }

      const modelBytes = ack.model_bytes_b64 ?? ack.model_bytes ?? '';
      const byteCount = base64ByteLength(modelBytes);
      triggerModelDownload(profile, modelBytes);
      setExportStatus({
        kind: 'success',
        message: `Export ready (${byteCount} bytes).`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Export failed';
      setExportStatus({ kind: 'error', message });
    }
  }

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
          void handleExport();
        }}
      >
        ↗ EXPORT MODEL
      </button>
      {exportStatus === null ? null : (
        <div className={`profile-export-status ${exportStatus.kind}`} role="status">
          {exportStatus.message}
        </div>
      )}
    </div>
  );
}

function base64ByteLength(value: string): number {
  const compact = value.replace(/\s/g, '');
  if (compact.length === 0) return 0;
  const padding = compact.endsWith('==') ? 2 : compact.endsWith('=') ? 1 : 0;
  return Math.max(0, Math.floor((compact.length * 3) / 4) - padding);
}

function triggerModelDownload(profile: ProfileModel, modelBytesBase64: string): void {
  if (
    modelBytesBase64.length === 0 ||
    typeof window === 'undefined' ||
    typeof window.atob !== 'function' ||
    typeof URL === 'undefined' ||
    typeof URL.createObjectURL !== 'function'
  ) {
    return;
  }

  const binary = window.atob(modelBytesBase64);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  const blob = new Blob([bytes], { type: 'application/octet-stream' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${profile.profile_id}-${profile.model_version}.rymp`;
  link.click();
  URL.revokeObjectURL(url);
}
