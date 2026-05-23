/**
 * HeaderBar — top status strip.
 *
 *   RytmRandomizer · Live ● armed · 2 unsaved sends
 *
 * Renders straight from `session_status`. Hidden in placeholder mode (handled by <App />,
 * which only mounts <Cockpit /> once a session_status arrives).
 */

import { useCockpitStore } from '../state';

export function HeaderBar(): JSX.Element {
  const session = useCockpitStore((s) => s.sessionStatus);

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

  return (
    <header className="cockpit-header" data-testid="header-bar">
      <span className="title">RytmRandomizer · {modeLabel}</span>
      <span className={armedClass}>{armedLabel}</span>
      <span className="badge">port: {session.midi_port ?? 'none'}</span>
      {session.unsaved_sends > 0 ? (
        <span className="badge unsaved">{session.unsaved_sends} unsaved sends</span>
      ) : (
        <span className="badge">no unsaved sends</span>
      )}
    </header>
  );
}
