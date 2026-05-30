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
import { useLoggedCommand } from './useLoggedCommand';

export interface ProfileChipsProps {
  /** Catalogue of profiles to show as chips. Filtered by `kind` upstream. */
  available: ReadonlyArray<{ profile_id: string; name: string; kind: ProfileKind }>;
}

export function ProfileChips({ available }: ProfileChipsProps): JSX.Element {
  const active = useCockpitStore((s) => s.profile);
  const sendCommand = useLoggedCommand();

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
                  sendCommand({ type: 'select_profile', profile_id: p.profile_id });
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

interface ExportStatus {
  kind: 'working' | 'success' | 'error';
  message: string;
}

function safeFilenamePart(value: string): string {
  const cleaned = value.replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '');
  return cleaned === '' ? 'profile' : cleaned;
}

function modelFilename(profile: ProfileModel): string {
  return `${safeFilenamePart(profile.profile_id)}-v${safeFilenamePart(profile.model_version)}.rymp`;
}

function base64ByteLength(value: string): number {
  const compact = value.replace(/\s/g, '');
  if (compact.length === 0) return 0;
  const padding = compact.endsWith('==') ? 2 : compact.endsWith('=') ? 1 : 0;
  return Math.max(0, Math.floor((compact.length * 3) / 4) - padding);
}

function decodeBase64(value: string): Uint8Array {
  const binary = window.atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function downloadProfileModel(modelBytesB64: string, filename: string): boolean {
  if (
    typeof window === 'undefined' ||
    typeof window.atob !== 'function' ||
    typeof URL === 'undefined' ||
    typeof URL.createObjectURL !== 'function'
  ) {
    return false;
  }

  const bytes = decodeBase64(modelBytesB64);
  const payload = new ArrayBuffer(bytes.byteLength);
  new Uint8Array(payload).set(bytes);
  const blob = new Blob([payload], { type: 'application/octet-stream' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = 'noopener';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  return true;
}

function ActiveProfileCard({ profile }: { profile: ProfileModel }): JSX.Element {
  const client = useCockpitClient();
  const [exporting, setExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<ExportStatus | null>(null);

  const handleExport = async (): Promise<void> => {
    const filename = modelFilename(profile);
    setExporting(true);
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

      const modelBytes = ack.model_bytes_b64 ?? ack.model_bytes;
      if (modelBytes === undefined || modelBytes === '') {
        throw new Error('Export response did not include model bytes');
      }
      const byteCount = base64ByteLength(modelBytes);
      const downloaded = downloadProfileModel(modelBytes, filename);
      setExportStatus({
        kind: 'success',
        message: downloaded
          ? `Export ready (${byteCount} bytes). Exported ${filename}.`
          : `Export ready (${byteCount} bytes).`,
      });
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      const message =
        detail === 'Export rejected by sidecar' || detail.startsWith('Export failed')
          ? detail
          : `Export failed: ${detail}`;
      setExportStatus({ kind: 'error', message });
    } finally {
      setExporting(false);
    }
  };

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
        disabled={exporting}
        onClick={() => void handleExport()}
      >
        ↗ EXPORT MODEL
      </button>
      {exportStatus?.kind === 'error' ? (
        <div
          className="profile-export-status error"
          data-testid="profile-export-status"
          role="alert"
        >
          {exportStatus.message}
        </div>
      ) : exportStatus === null ? null : (
        <div
          className={`profile-export-status ${exportStatus.kind}`}
          data-testid="profile-export-status"
          role="status"
        >
          {exportStatus.message}
        </div>
      )}
    </div>
  );
}
