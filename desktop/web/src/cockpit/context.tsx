/**
 * React context wrapping the `CockpitClient` so any cockpit component can emit commands
 * without prop-drilling. The provider is set up at the top of `<Cockpit />`.
 *
 * Tests inject a fake client via `<CockpitClientProvider value={fake}>`.
 */

import { createContext, useContext, type ReactNode } from 'react';

import type { CockpitClient } from '../ws/client';

const CockpitClientContext = createContext<CockpitClient | null>(null);

export interface CockpitClientProviderProps {
  client: CockpitClient;
  children: ReactNode;
}

export function CockpitClientProvider({
  client,
  children,
}: CockpitClientProviderProps): JSX.Element {
  return (
    <CockpitClientContext.Provider value={client}>{children}</CockpitClientContext.Provider>
  );
}

/**
 * Hook for components to obtain the cockpit client. Throws if no provider mounted —
 * a misconfiguration we'd rather catch at first render than silently no-op.
 */
export function useCockpitClient(): CockpitClient {
  const client = useContext(CockpitClientContext);
  if (client === null) {
    throw new Error(
      'useCockpitClient called outside <CockpitClientProvider>; mount <Cockpit /> with a client',
    );
  }
  return client;
}
