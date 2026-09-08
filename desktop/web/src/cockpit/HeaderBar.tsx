/**
 * HeaderBar — top status strip.
 *
 *   RytmRandomizer · Live  [● listening]  ● armed · port · 2 unsaved sends  [Arm…]
 *
 * The device pill renders the passive connection phase from the Wave-3/4
 * ConnectionManager (`connection_changed` events, falling back to the
 * session_status snapshot). Every phase is icon + text — never hue alone.
 * A dismissible reconnect toast appears when a fault recovers to listening.
 */

import { useEffect } from 'react';

import { announce } from '../a11y';
import { selectConnectionPhase, useCockpitStore } from '../state';
import { chipLabel, shouldShowChip } from '../updateProtocol';
import type { ConnectionPhase } from '../ws/protocol';

import { ArmControl } from './ArmControl';

/** Icon + text per phase (exported for tests; icons are decorative). */
export const CONNECTION_PHASE_DISPLAY: Readonly<
  Record<ConnectionPhase, { icon: string; label: string }>
> = {
  disconnected: { icon: '○', label: 'disconnected' },
  searching: { icon: '◌', label: 'searching' },
  listening: { icon: '●', label: 'listening' },
  armed: { icon: '▲', label: 'armed' },
  fault: { icon: '⚠', label: 'fault' },
};

/**
 * Update chip — `⬆ 1.35.1 ready` (spec §7 / §7.1 header mockup).
 *
 * Icon + shape + text, never hue alone. Hidden outright in freeze mode and
 * in every state but `staged` (rollout-excluded is indistinguishable from
 * up-to-date by design, §5). Calm: no animation, no pulse, no countdown —
 * and announced exactly ONCE per staged version, not on every re-render,
 * so the polite live region never becomes a ticker.
 */
export function UpdateChip(): JSX.Element | null {
  const update = useCockpitStore((s) => s.update);
  const visible = shouldShowChip(update);
  const version = update.state?.version ?? '';

  // Once per (visible, version) pair — the dependency array IS the
  // de-duplicator. A re-render that changes neither (a refreshed manifest
  // for the SAME staged version, an unrelated store write) re-runs nothing,
  // so the polite live region never becomes a ticker. Leaving and re-
  // entering the staged state does announce again, which is correct: the
  // operator saw the chip disappear.
  useEffect(() => {
    if (!visible) return;
    announce(`Update ${version} ready to install`);
  }, [visible, version]);

  if (!visible) return null;
  return (
    <span className="badge update-chip" data-testid="update-chip">
      {chipLabel(version)}
    </span>
  );
}

export function HeaderBar(): JSX.Element {
  const session = useCockpitStore((s) => s.sessionStatus);
  const phase = useCockpitStore(selectConnectionPhase);
  const reconnectNotice = useCockpitStore((s) => s.reconnectNotice);
  const clearReconnectNotice = useCockpitStore((s) => s.clearReconnectNotice);

  if (session === null) {
    // No session yet (sidecar never answered): honest placeholder badges,
    // with the Arm affordance PRESENT but disabled — never hidden — so the
    // operator can see the control and why it is unavailable.
    return (
      <header className="cockpit-header" data-testid="header-bar">
        <span className="title">RytmRandomizer · Cockpit</span>
        <span className="badge">disconnected</span>
        <UpdateChip />
        <ArmControl />
      </header>
    );
  }

  const modeLabel = session.mode === 'live' ? 'Live' : 'Mock';
  const armedClass = session.armed ? 'badge armed' : 'badge safe';
  const armedLabel = session.armed ? '● armed' : '○ safe';
  const phaseDisplay = CONNECTION_PHASE_DISPLAY[phase];

  return (
    <header className="cockpit-header" data-testid="header-bar">
      <span className="title">RytmRandomizer · {modeLabel}</span>
      <span className={`badge connection-pill connection-pill-${phase}`} data-testid="connection-pill">
        <span aria-hidden="true">{phaseDisplay.icon}</span> {phaseDisplay.label}
      </span>
      <span className={armedClass}>{armedLabel}</span>
      <span className="badge">port: {session.midi_port ?? 'none'}</span>
      {session.unsaved_sends > 0 ? (
        <span className="badge unsaved">{session.unsaved_sends} unsaved sends</span>
      ) : (
        <span className="badge">no unsaved sends</span>
      )}
      {reconnectNotice !== null && (
        <span className="badge reconnect-toast" data-testid="reconnect-toast">
          <span aria-hidden="true">↻</span> {reconnectNotice}
          <button
            type="button"
            className="reconnect-toast-dismiss"
            aria-label="Dismiss reconnect notice"
            onClick={clearReconnectNotice}
          >
            ×
          </button>
        </span>
      )}
      <UpdateChip />
      <ArmControl />
    </header>
  );
}
