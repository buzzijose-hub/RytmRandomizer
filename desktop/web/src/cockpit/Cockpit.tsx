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
 * Owns `previewOn` local state (lifted from ActionBar so SnapshotPanel can render ghosts).
 *
 * The bottom rail is NOT hand-mounted: it renders whatever the panel registry
 * (`panels/registry.ts`) declares for the `bottom` region, via `PanelHost`.
 * That keeps the registry the one extension seam for adding cockpit panels
 * instead of a manifest the real layout quietly bypasses.
 *
 * Wires the WebSocket client into a React Context so children can emit commands without
 * prop-drilling.
 */

import { useState } from 'react';

import type { CockpitClient } from '../ws/client';

import '../a11y/srOnly.css';

import { CockpitClientProvider } from './context';
import { DeviceRail } from './DeviceRail';
import { type CockpitDeviceId, RYTM_DEVICE_ID } from './devices';
import { HeaderBar } from './HeaderBar';
import { KitCapturePanel } from './KitCapturePanel';
import { LiveReadinessPanel } from './LiveReadinessPanel';
import { MutationPanel } from './MutationPanel';
import { PanelHost } from './panels/PanelHost';
import { PatchGenomePanel } from './PatchGenomePanel';
import { SafetyRail } from './SafetyRail';
import { SnapshotPanel } from './SnapshotPanel';

import './styles.css';

export interface CockpitProps {
  client: CockpitClient;
}

export function Cockpit({ client }: CockpitProps): JSX.Element {
  const [previewOn, setPreviewOn] = useState<boolean>(false);
  const [activeDeviceId, setActiveDeviceId] = useState<CockpitDeviceId>(RYTM_DEVICE_ID);
  const [captureDeviceId, setCaptureDeviceId] = useState<CockpitDeviceId | null>(null);

  const prepareCapture = (deviceId: CockpitDeviceId): void => {
    setActiveDeviceId(deviceId);
    setCaptureDeviceId(deviceId);
  };

  return (
    <CockpitClientProvider client={client}>
      <main className="cockpit-root" data-testid="cockpit-root">
        <h1 className="sr-only">RytmRandomizer · Cockpit</h1>
        <HeaderBar />
        <div className="cockpit-main">
          <DeviceRail
            activeDeviceId={activeDeviceId}
            onSelectDevice={(deviceId) => {
              setActiveDeviceId(deviceId);
              setCaptureDeviceId(null);
            }}
            onCaptureDevice={prepareCapture}
          />
          <div className="cockpit-center-stack">
            {captureDeviceId !== null ? (
              <KitCapturePanel
                deviceId={captureDeviceId}
                onClose={() => setCaptureDeviceId(null)}
              />
            ) : activeDeviceId === RYTM_DEVICE_ID ? (
              <>
                <SnapshotPanel activeDeviceId={activeDeviceId} previewOn={previewOn} />
                <LiveReadinessPanel />
              </>
            ) : (
              <>
                <SnapshotPanel activeDeviceId={activeDeviceId} previewOn={previewOn} />
                <PatchGenomePanel previewOn={previewOn} />
              </>
            )}
          </div>
          <div className="cockpit-side-stack">
            <MutationPanel
              previewOn={previewOn}
              onTogglePreview={setPreviewOn}
            />
            <SafetyRail />
          </div>
        </div>
        <div className="cockpit-bottom-stack">
          {/*
            Bottom-rail panels mount through the schema-driven registry, not by
            hand. Ordering is the manifest's order in `panels/registry.ts`, so
            adding or reordering a bottom panel is a registry edit — no change
            to this file. See `.claude/skills/add-cockpit-panel/SKILL.md`.
          */}
          <PanelHost region="bottom" />
        </div>
      </main>
    </CockpitClientProvider>
  );
}
