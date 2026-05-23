/**
 * Top-level App placeholder for the scaffold (WS-I).
 *
 * The real cockpit UI lives in `src/cockpit/**` (WS-J) — it will replace this component.
 * Until the first `session_status` event arrives, we render "Connecting…".
 *
 * This file uses only the scaffold's own surface (state + ws). Once WS-J lands, this file
 * becomes a thin wrapper that mounts `<Cockpit />` instead of the placeholder shell.
 */

import { useEffect, useMemo, useState } from 'react';

import { bindClientToStore, useCockpitStore, type SessionStatus } from './state';
import { CockpitClient, type ConnectionStatus } from './ws/client';

interface AppProps {
  /** Inject a client for tests/storybook. Default: a new singleton connected to the sidecar. */
  client?: CockpitClient;
}

export function App({ client: injected }: AppProps = {}): JSX.Element {
  const client = useMemo(() => injected ?? new CockpitClient(), [injected]);
  const sessionStatus = useCockpitStore((s) => s.sessionStatus);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>(client.getStatus());

  useEffect(() => {
    const unbind = bindClientToStore(client);
    const offStatus = client.onStatusChange(setConnStatus);
    client.connect();
    return () => {
      offStatus();
      unbind();
      client.close();
    };
  }, [client]);

  if (sessionStatus === null) {
    return (
      <main className="cockpit-placeholder">
        <h1>RytmRandomizer · Cockpit</h1>
        <p>Connecting…</p>
        <small>status: {connStatus}</small>
      </main>
    );
  }

  return (
    <main className="cockpit-placeholder">
      <h1>RytmRandomizer · Cockpit</h1>
      <ConnectedBanner status={sessionStatus} />
      <p>
        Scaffold ready. The v10 cockpit UI mounts here once <code>src/cockpit/**</code>{' '}
        ships (WS-J).
      </p>
    </main>
  );
}

function ConnectedBanner({ status }: { status: SessionStatus }): JSX.Element {
  const armed = status.armed ? 'armed' : 'safe';
  return (
    <p className="cockpit-status">
      <span>mode: {status.mode}</span>
      <span> · port: {status.midi_port ?? 'none'}</span>
      <span> · {armed}</span>
      <span> · unsaved sends: {status.unsaved_sends}</span>
    </p>
  );
}
