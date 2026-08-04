/**
 * Tests for the App-level hash router.
 *
 * Verifies:
 *   - An empty / `#/` hash mounts the Cockpit surface, and a `#/wizard` hash mounts
 *     the Wizard surface — IMMEDIATELY, with or without a sessionStatus. There is no
 *     session gate: the cockpit is usable offline and the ReconnectBanner is the
 *     connection surface.
 *   - Mutating `window.location.hash` after mount + dispatching `hashchange` swaps the
 *     surface in place (the same behaviour MutationPanel's launcher relies on).
 *   - The passive performance-console route renders the bundled demo model with no
 *     session at all.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, render, screen } from '@testing-library/react';

import { App } from '../src/App';
import { useCockpitStore } from '../src/state';
import { useWizardStore } from '../src/state/wizard_store';

import { FakeCockpitClient, sessionLive, snapshot } from './cockpit/_fixtures';
import { performanceConsoleModel } from './cockpit/performanceConsoleFixture';

function setHash(hash: string): void {
  window.location.hash = hash;
}

function fireHashChange(): void {
  window.dispatchEvent(new HashChangeEvent('hashchange'));
}

describe('App hash router', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
    useWizardStore.getState().reset();
    setHash('');
  });

  afterEach(() => {
    setHash('');
    useCockpitStore.getState().reset();
    useWizardStore.getState().reset();
  });

  it('mounts the Cockpit immediately with NO session (no gate)', () => {
    const fake = new FakeCockpitClient();
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    // Honest degraded surfaces instead of a gate:
    expect(screen.getByTestId('header-bar')).toHaveTextContent('disconnected');
    expect(screen.getByTestId('snapshot-panel')).toHaveTextContent('Waiting for snapshot…');
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('shows the ReconnectBanner over the mounted cockpit while the WS is down', () => {
    const fake = new FakeCockpitClient();
    fake.setStatus('reconnecting');
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.getByTestId('reconnect-banner')).toBeInTheDocument();
    expect(screen.getByTestId('reconnect-banner-retry-now')).toBeInTheDocument();
    // Pre-session: the banner carries the connection-help disclosure.
    expect(screen.getByTestId('reconnect-banner-help')).toBeInTheDocument();
  });

  it('hydrates the already-mounted Cockpit in place when session_status arrives', () => {
    const fake = new FakeCockpitClient();
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.getByTestId('header-bar')).toHaveTextContent('disconnected');

    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.getByTestId('header-bar')).toHaveTextContent('RytmRandomizer · Live');
    expect(screen.getByTestId('snapshot-panel')).not.toHaveTextContent(
      'Waiting for snapshot…',
    );
  });

  it('mounts the Wizard at #/wizard even while the sidecar is unreachable', () => {
    setHash('/wizard');
    const fake = new FakeCockpitClient();
    fake.setStatus('reconnecting');
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
    expect(screen.getByTestId('reconnect-banner')).toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
  });

  it('mounts the Performance Console preview route from an injected passive model before session_status arrives', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();

    render(<App client={fake.asClient()} performanceConsole={performanceConsoleModel} />);

    expect(screen.getByTestId('performance-console')).toBeInTheDocument();
    expect(screen.getByLabelText('Console safety state')).toHaveTextContent('injected packet');
    expect(screen.queryByText(/Connecting/)).not.toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('mounts the Performance Console preview route from the short console alias', () => {
    setHash('/console');
    const fake = new FakeCockpitClient();

    render(<App client={fake.asClient()} performanceConsole={performanceConsoleModel} />);

    expect(screen.getByTestId('performance-console')).toBeInTheDocument();
    expect(screen.getByLabelText('Console safety state')).toHaveTextContent('injected packet');
    expect(screen.queryByText(/Connecting/)).not.toBeInTheDocument();
  });

  it('mounts the bundled Performance Console demo route without an injected model', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();

    render(<App client={fake.asClient()} />);

    expect(screen.getByTestId('performance-console')).toBeInTheDocument();
    expect(screen.getByLabelText('Console safety state')).toHaveTextContent('demo fallback');
    expect(screen.getByText('RytmRandomizer Cockpit Performance Console')).toBeInTheDocument();
    expect(screen.queryByText(/Connecting/)).not.toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('swaps Performance Console → Wizard when the hash changes after mount', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} performanceConsole={performanceConsoleModel} />);
    expect(screen.getByTestId('performance-console')).toBeInTheDocument();

    act(() => {
      setHash('/wizard');
      fireHashChange();
    });

    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
    expect(screen.queryByTestId('performance-console')).not.toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
  });

  it('swaps Performance Console → Cockpit when the hash returns to "#/" after mount', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} performanceConsole={performanceConsoleModel} />);
    expect(screen.getByTestId('performance-console')).toBeInTheDocument();

    act(() => {
      setHash('/');
      fireHashChange();
    });

    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.queryByTestId('performance-console')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('mounts the Performance Console route from the live store packet before falling back to demo', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();
    const storeModel = {
      ...performanceConsoleModel,
      console_id: 'console-live-ws',
      session_label: 'Live WS packet',
    };
    useCockpitStore.getState().setPerformanceConsole(storeModel);

    render(<App client={fake.asClient()} />);

    expect(screen.getByTestId('performance-console')).toBeInTheDocument();
    expect(screen.getByLabelText('Console safety state')).toHaveTextContent('live websocket');
    expect(screen.getByText('Live WS packet')).toBeInTheDocument();
    expect(screen.queryByText('Warehouse arc')).not.toBeInTheDocument();
    expect(screen.queryByText(/Connecting/)).not.toBeInTheDocument();
  });

  it('keeps the injected Performance Console model ahead of the live store packet', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setPerformanceConsole({
      ...performanceConsoleModel,
      console_id: 'console-live-ws',
      session_label: 'Live WS packet',
    });
    const injectedModel = {
      ...performanceConsoleModel,
      console_id: 'console-injected',
      session_label: 'Injected packet',
    };

    render(<App client={fake.asClient()} performanceConsole={injectedModel} />);

    expect(screen.getByTestId('performance-console')).toBeInTheDocument();
    expect(screen.getByLabelText('Console safety state')).toHaveTextContent('injected packet');
    expect(screen.getByText('Injected packet')).toBeInTheDocument();
    expect(screen.queryByText('Live WS packet')).not.toBeInTheDocument();
  });

  it('mounts the Cockpit when the hash is empty', () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('mounts the Cockpit when the hash is "#/"', () => {
    setHash('/');
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('mounts the Wizard when the hash is "#/wizard"', () => {
    setHash('/wizard');
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
  });

  it('swaps Cockpit → Wizard when the hash changes after mount', () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();

    act(() => {
      setHash('/wizard');
      fireHashChange();
    });

    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
  });

  it('swaps Wizard → Cockpit when the hash returns to "#/" after mount', () => {
    setHash('/wizard');
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();

    act(() => {
      setHash('/');
      fireHashChange();
    });

    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('reuses the injected client for both surfaces (no second WS connection)', () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    // Cockpit doesn't send a command on mount, but the wizard does (`wizard_start`).
    const sentBefore = fake.sent.length;
    act(() => {
      setHash('/wizard');
      fireHashChange();
    });
    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
    // The Wizard's mount-effect runs `wizard_start` through the SAME injected client.
    expect(fake.sent.length).toBe(sentBefore + 1);
    expect(fake.sent[fake.sent.length - 1]).toEqual({ type: 'wizard_start' });
  });
});
