/**
 * Top-level App. Mounts <Cockpit /> once the engine has pushed a session_status; otherwise
 * shows a small connecting placeholder.
 */

import { useEffect, useMemo, useState } from 'react';

import { Cockpit } from './cockpit';
import { bindClientToStore, useCockpitStore } from './state';
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

  return <Cockpit client={client} />;
}
