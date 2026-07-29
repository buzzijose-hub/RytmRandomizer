/**
 * Cockpit-wide axe-core audit — WCAG 2.2 AA gate.
 *
 * Every operator-facing cockpit component and schema-driven panel is rendered
 * into a detached container and scanned with the WCAG 2.0/2.1/2.2 A + AA rule
 * tags. The `FLOORS` map is the audit BASELINE: every entry is the count of
 * KNOWN violations that pre-date this suite. A component with no entry must be
 * clean (floor 0). A regression that pushes any component above its floor —
 * or introduces a violation on a floor-0 component — fails the build.
 *
 * This is the PR-blocking half of the a11y gate. The E2E `a11y_axe_scan.spec`
 * scans whole routes against a live sidecar; this suite scans every leaf
 * surface in isolation without needing the sidecar, so it runs in the fast
 * Vitest lane on every push.
 *
 * NOTE ON SCOPE: the intent is that every `FLOORS` value is 0. Any non-zero
 * entry is a documented, dated debt with a fix owner. As of this suite's
 * introduction the audit found every scanned surface clean (all floors 0).
 */
import { render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { ArmControl } from '../../src/cockpit/ArmControl';
import { DepthSlider } from '../../src/cockpit/DepthSlider';
import { Knob } from '../../src/cockpit/Knob';
import { ProfileToggle } from '../../src/cockpit/ProfileToggle';
import { LockButton } from '../../src/cockpit/LockButton';
import { ConnectionDoctorPanel } from '../../src/cockpit/panels/ConnectionDoctorPanel';
import { LibraryPanel } from '../../src/cockpit/panels/LibraryPanel';
import { LiveMidiMonitorPanel } from '../../src/cockpit/panels/LiveMidiMonitorPanel';
import { PanelRenderer } from '../../src/cockpit/panels/PanelRenderer';
import { liveMidiMonitorPanelSpec } from '../../src/cockpit/panels/liveMidiMonitorPanelSpec';
import { useCockpitStore } from '../../src/state';

import {
  connectionListening,
  diagnosticsHealthy,
  libraryRecordA,
  midiBatch,
  sessionMock,
} from '../cockpit/_fixtures';
import { runAxe, violationSummary } from './__helpers__/axe';
import { FakeCockpitClient } from '../cockpit/_fixtures';

// component-name → expected (grandfathered) violation count. Keep at 0.
const FLOORS = {
  ArmControl: 0,
  ArmControlDialog: 0,
  DepthSlider: 0,
  Knob: 0,
  ProfileToggle: 0,
  LockButton: 0,
  ConnectionDoctorPanel: 0,
  LibraryPanel: 0,
  LiveMidiMonitorPanel: 0,
  PanelRenderer: 0,
} as const;

function withClient(node: React.ReactNode): JSX.Element {
  const fake = new FakeCockpitClient();
  return <CockpitClientProvider client={fake.asClient()}>{node}</CockpitClientProvider>;
}

function seedStore(): void {
  useCockpitStore.setState({
    sessionStatus: sessionMock,
    connection: connectionListening,
    diagnostics: diagnosticsHealthy,
    libraryRecords: [libraryRecordA],
    midiActivityRows: [],
    midiActivityMeta: { port: midiBatch.port, dropped: 0, ignored: 0, read_errors: 0 },
    midiActivityPaused: false,
    midiActivityBatchCount: 0,
  });
}

async function expectClean(name: keyof typeof FLOORS, container: Element): Promise<void> {
  const results = await runAxe(container);
  expect(results.violations.length, `${name}\n${violationSummary(results)}`).toBeLessThanOrEqual(
    FLOORS[name],
  );
}

describe('cockpit axe audit (WCAG 2.2 AA)', () => {
  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  it('ArmControl (passive) is clean', async () => {
    const { container } = render(withClient(<ArmControl />));
    await expectClean('ArmControl', container);
  });

  it('DepthSlider is clean', async () => {
    const { container } = render(withClient(<DepthSlider />));
    await expectClean('DepthSlider', container);
  });

  it('Knob (read-only meter) is clean', async () => {
    const { container } = render(<Knob label="TUN" value={64} ghostValue={100} />);
    await expectClean('Knob', container);
  });

  it('ProfileToggle is clean', async () => {
    const { container } = render(<ProfileToggle value="scene" onChange={() => {}} />);
    await expectClean('ProfileToggle', container);
  });

  it('LockButton is clean', async () => {
    const { container } = render(<LockButton locked={false} onToggle={() => {}} padId={1} />);
    await expectClean('LockButton', container);
  });

  it('PanelRenderer (generic schema panel) is clean', async () => {
    const spec = liveMidiMonitorPanelSpec([], null, false);
    const { container } = render(<PanelRenderer spec={spec} />);
    await expectClean('PanelRenderer', container);
  });

  it('ConnectionDoctorPanel is clean', async () => {
    seedStore();
    const { container } = render(withClient(<ConnectionDoctorPanel />));
    await expectClean('ConnectionDoctorPanel', container);
  });

  it('LibraryPanel is clean', async () => {
    seedStore();
    const { container } = render(withClient(<LibraryPanel />));
    await expectClean('LibraryPanel', container);
  });

  it('LiveMidiMonitorPanel is clean', async () => {
    seedStore();
    const { container } = render(withClient(<LiveMidiMonitorPanel />));
    await expectClean('LiveMidiMonitorPanel', container);
  });
});
