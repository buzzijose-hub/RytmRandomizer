/**
 * ConnectionDoctorPanel — read-only health surface over the `diagnostics`
 * WS command. The checklist / journal render through the generic
 * PanelRenderer; the bespoke strip provides Refresh (re-runs the command)
 * and Export (copies the raw packet to the clipboard).
 */

import { useState } from 'react';

import { useCockpitStore } from '../../state';
import { useCockpitClient } from '../context';

import { connectionDoctorPanelSpec } from './connectionDoctorPanelSpec';
import { PanelRenderer } from './PanelRenderer';

export function ConnectionDoctorPanel(): JSX.Element {
  const client = useCockpitClient();
  const diagnostics = useCockpitStore((s) => s.diagnostics);
  const setDiagnostics = useCockpitStore((s) => s.setDiagnostics);
  const [note, setNote] = useState<string | null>(null);

  const refresh = (): void => {
    client
      .send({ type: 'diagnostics' })
      .then((ack) => {
        if (ack.ok && ack.diagnostics !== undefined && ack.diagnostics !== null) {
          setDiagnostics(ack.diagnostics);
          setNote('diagnostics refreshed');
        } else {
          setNote(ack.message ?? 'diagnostics request rejected');
        }
      })
      .catch(() => setNote('diagnostics request failed to send'));
  };

  const exportDiagnostics = (): void => {
    const clip = navigator.clipboard as Clipboard | undefined;
    if (clip === undefined) {
      setNote('clipboard unavailable');
      return;
    }
    clip
      .writeText(JSON.stringify(diagnostics, null, 2))
      .then(() => setNote('diagnostics copied'))
      .catch(() => setNote('copy failed'));
  };

  return (
    <div className="cockpit-panel-stack" data-testid="connection-doctor">
      <div className="cockpit-panel-controls">
        <button type="button" onClick={refresh} data-testid="doctor-refresh">
          Refresh diagnostics
        </button>
        <button
          type="button"
          onClick={exportDiagnostics}
          disabled={diagnostics === null}
          data-testid="doctor-export"
        >
          Export to clipboard
        </button>
        {note !== null && <span className="cockpit-panel-note">{note}</span>}
      </div>
      <PanelRenderer spec={connectionDoctorPanelSpec(diagnostics)} />
    </div>
  );
}
