/**
 * Top-level App. Mounts <Cockpit /> once the engine has pushed a session_status; otherwise
 * shows a small connecting placeholder.
 *
 * Hash routing
 * ------------
 * The cockpit ships as a SPA that lives behind a tiny hash-based router so the wizard can
 * be deep-linked at `#/wizard`. Anything else (empty hash, `#/`, unrecognised) renders the
 * Cockpit. The router uses the browser `hashchange` event so `window.location.hash = ...`
 * (used by both MutationPanel's wizard launcher and the wizard's post-save navigation)
 * is enough to switch surfaces without pulling in a routing library.
 */

import { useEffect, useMemo, useState } from 'react';

import { LiveRegion, useDocumentTitle } from './a11y';
import { Cockpit } from './cockpit';
import { bindClientToStore, useCockpitStore } from './state';
import { Wizard } from './wizard';
import { CockpitClient, type ConnectionStatus } from './ws/client';

interface AppProps {
  /** Inject a client for tests/storybook. Default: a new singleton connected to the sidecar. */
  client?: CockpitClient;
}

/**
 * Subscribe to `hashchange` and return the current `window.location.hash`. Initialised
 * lazily so SSR-style imports don't try to read `window` at module-load time (jsdom in
 * tests always has it; we keep the lazy initialiser for symmetry).
 */
function useHashRoute(): string {
  const [hash, setHash] = useState<string>(() => window.location.hash);
  useEffect(() => {
    const onChange = (): void => setHash(window.location.hash);
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return hash;
}

/** True when the hash points at the wizard surface (`#/wizard`, `#/wizard/anything`). */
function isWizardRoute(hash: string): boolean {
  return hash === '#/wizard' || hash.startsWith('#/wizard/');
}

export function App({ client: injected }: AppProps = {}): JSX.Element {
  const client = useMemo(() => injected ?? new CockpitClient(), [injected]);
  const sessionStatus = useCockpitStore((s) => s.sessionStatus);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>(client.getStatus());
  const route = useHashRoute();

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

  useDocumentTitle(
    sessionStatus === null
      ? 'RytmRandomizer · Connecting'
      : isWizardRoute(route)
        ? 'RytmRandomizer · Profile Wizard'
        : 'RytmRandomizer · Cockpit',
  );

  if (sessionStatus === null) {
    return (
      <>
        <LiveRegion />
        <main className="cockpit-placeholder">
          <h1>RytmRandomizer · Cockpit</h1>
          <p>Connecting…</p>
          <small>status: {connStatus}</small>
        </main>
      </>
    );
  }

  if (isWizardRoute(route)) {
    return (
      <>
        <LiveRegion />
        <Wizard client={client} />
      </>
    );
  }

  return (
    <>
      <LiveRegion />
      <Cockpit client={client} />
    </>
  );
}
