/**
 * Cockpit — top-level v10 layout.
 *
 *   ┌──────────────── HeaderBar ────────────────┐
 *   │                                            │
 *   │  ┌─ SnapshotPanel ─┐  ┌─ MutationPanel ─┐ │
 *   │  │   pad grid       │  │  profile chips   │ │
 *   │  │   history strip  │  │  depth slider    │ │
 *   │  │                  │  │  action bar      │ │
 *   │  └──────────────────┘  └─────────────────┘ │
 *   └────────────────────────────────────────────┘
 *
 * Owns:
 *   - `previewOn` local state (lifted from ActionBar so SnapshotPanel can render ghosts)
 *   - `availableProfiles` prop list passed down to the right panel
 *
 * Wires the WebSocket client into a React Context so children can emit commands without
 * prop-drilling.
 */

import { useState } from 'react';

import type { ProfileKind } from '../ws/protocol';
import type { CockpitClient } from '../ws/client';

import '../a11y/srOnly.css';

import { CockpitClientProvider } from './context';
import { HeaderBar } from './HeaderBar';
import { MutationPanel } from './MutationPanel';
import { SnapshotPanel } from './SnapshotPanel';

import './styles.css';

export interface CockpitProps {
  client: CockpitClient;
  /**
   * Catalogue of selectable profiles. Until the profile registry pushes a real list (WS-K
   * integration), the caller (App) provides a static fallback so the chips render.
   */
  availableProfiles?: ReadonlyArray<{
    profile_id: string;
    name: string;
    kind: ProfileKind;
  }>;
}

const DEFAULT_AVAILABLE_PROFILES: ReadonlyArray<{
  profile_id: string;
  name: string;
  kind: ProfileKind;
}> = [
  { profile_id: 'scene-industrial', name: 'Industrial', kind: 'scene' },
  { profile_id: 'scene-warehouse', name: 'Warehouse', kind: 'scene' },
  { profile_id: 'user-buzzi', name: 'buzzi', kind: 'user' },
  { profile_id: 'user-kanye', name: 'kanye', kind: 'user' },
];

export function Cockpit({
  client,
  availableProfiles = DEFAULT_AVAILABLE_PROFILES,
}: CockpitProps): JSX.Element {
  const [previewOn, setPreviewOn] = useState<boolean>(false);

  return (
    <CockpitClientProvider client={client}>
      <main className="cockpit-root" data-testid="cockpit-root">
        <h1 className="sr-only">RytmRandomizer · Cockpit</h1>
        <HeaderBar />
        <div className="cockpit-main">
          <SnapshotPanel previewOn={previewOn} />
          <MutationPanel
            availableProfiles={availableProfiles}
            previewOn={previewOn}
            onTogglePreview={setPreviewOn}
          />
        </div>
      </main>
    </CockpitClientProvider>
  );
}
