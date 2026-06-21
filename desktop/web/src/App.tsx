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
 *
 * A11y wiring
 * -----------
 * - `<LiveRegion />` mounts the global aria-live region (Cluster 4 — announcer).
 * - `useDocumentTitle` sets per-route document.title (Cluster 6 — landmarks).
 * - `useFocusOnRouteChange` moves focus to the route container on hash change
 *   (Cluster 5 — focus management). Each return branch wraps its content in a
 *   `<div ref={routeRootRef} tabIndex={-1}>` so the hook has a focusable target.
 */

import { useEffect, useMemo, useRef, useState } from 'react';

import { LiveRegion, useDocumentTitle, useFocusOnRouteChange } from './a11y';
import { Cockpit, PerformanceConsole, performanceConsoleDemoModel } from './cockpit';
import { bindClientToStore, useCockpitStore } from './state';
import type { LiveGuiPerformanceConsoleModelDict } from './types/live_gui_protocol';
import { Wizard } from './wizard';
import { CockpitClient, type ConnectionStatus } from './ws/client';

interface AppProps {
  /** Inject a client for tests/storybook. Default: a new singleton connected to the sidecar. */
  client?: CockpitClient;
  /** Inject the passive performance-console packet for mock-safe preview routes. */
  performanceConsole?: LiveGuiPerformanceConsoleModelDict;
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

/** True when the hash points at the passive performance console preview surface. */
function isPerformanceConsoleRoute(hash: string): boolean {
  return hash === '#/performance-console' || hash === '#/console';
}

export function App({ client: injected, performanceConsole }: AppProps = {}): JSX.Element {
  const client = useMemo(() => injected ?? new CockpitClient(), [injected]);
  const sessionStatus = useCockpitStore((s) => s.sessionStatus);
  const storePerformanceConsole = useCockpitStore((s) => s.performanceConsole);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>(client.getStatus());
  const route = useHashRoute();
  const routeRootRef = useRef<HTMLDivElement>(null);
  const isConsoleRoute = isPerformanceConsoleRoute(route);
  const performanceConsoleModel = isConsoleRoute
    ? performanceConsole ?? storePerformanceConsole ?? performanceConsoleDemoModel
    : undefined;
  const performanceConsoleSource = isConsoleRoute
    ? performanceConsole !== undefined
      ? 'injected packet'
      : storePerformanceConsole !== null
        ? 'live websocket'
        : 'demo fallback'
    : undefined;
  const showPerformanceConsole = performanceConsoleModel !== undefined;

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
    showPerformanceConsole
      ? 'RytmRandomizer · Performance Console'
      : sessionStatus === null
      ? 'RytmRandomizer · Connecting'
      : isWizardRoute(route)
        ? 'RytmRandomizer · Profile Wizard'
        : 'RytmRandomizer · Cockpit',
  );

  useFocusOnRouteChange(routeRootRef, [route, sessionStatus === null]);

  if (showPerformanceConsole) {
    return (
      <>
        <LiveRegion />
        <div ref={routeRootRef} tabIndex={-1}>
          <PerformanceConsole
            model={performanceConsoleModel}
            packetSource={performanceConsoleSource}
            onRehearseOperatorPackageStep={(command) => client.send(command)}
          />
        </div>
      </>
    );
  }

  if (sessionStatus === null) {
    return (
      <>
        <LiveRegion />
        <div ref={routeRootRef} tabIndex={-1}>
          <main className="cockpit-placeholder">
            <h1>RytmRandomizer · Cockpit</h1>
            <p>Connecting…</p>
            <small>status: {connStatus}</small>
          </main>
        </div>
      </>
    );
  }

  if (isWizardRoute(route)) {
    return (
      <>
        <LiveRegion />
        <div ref={routeRootRef} tabIndex={-1}>
          <Wizard client={client} />
        </div>
      </>
    );
  }

  return (
    <>
      <LiveRegion />
      <div ref={routeRootRef} tabIndex={-1}>
        <Cockpit client={client} />
      </div>
    </>
  );
}
