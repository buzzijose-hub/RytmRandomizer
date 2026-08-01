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

import { selectConnectionPhase, useCockpitStore } from '../state';
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

export function HeaderBar(): JSX.Element {
  const session = useCockpitStore((s) => s.sessionStatus);
  const phase = useCockpitStore(selectConnectionPhase);
  const reconnectNotice = useCockpitStore((s) => s.reconnectNotice);
  const clearReconnectNotice = useCockpitStore((s) => s.clearReconnectNotice);

  if (session === null) {
    return (
      <header className="cockpit-header" data-testid="header-bar">
        <span className="title">RytmRandomizer · Cockpit</span>
        <span className="badge">disconnected</span>
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
      <ArmControl />
    </header>
  );
}
