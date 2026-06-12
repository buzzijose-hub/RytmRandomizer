/**
 * Tests for the App-level hash router.
 *
 * Verifies:
 *   - With sessionStatus seeded, an empty / `#/` hash mounts the Cockpit surface.
 *   - A `#/wizard` hash mounts the Wizard surface.
 *   - Mutating `window.location.hash` after mount + dispatching `hashchange` swaps the
 *     surface in place (the same behaviour MutationPanel's launcher relies on).
 *   - Without a sessionStatus the connecting placeholder still shows (router is a no-op
 *     until the engine pushes a session_status frame).
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

  it('shows the connecting placeholder until session_status arrives', () => {
    const fake = new FakeCockpitClient();
    render(<App client={fake.asClient()} />);
    expect(screen.getByText(/Connecting/)).toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('mounts the Performance Console preview route from an injected passive model before session_status arrives', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();

    render(<App client={fake.asClient()} performanceConsole={performanceConsoleModel} />);

    expect(screen.getByTestId('performance-console')).toBeInTheDocument();
    expect(screen.queryByText(/Connecting/)).not.toBeInTheDocument();
    expect(screen.queryByTestId('cockpit-root')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-root')).not.toBeInTheDocument();
  });

  it('mounts the Performance Console preview route from the short console alias', () => {
    setHash('/console');
    const fake = new FakeCockpitClient();

    render(<App client={fake.asClient()} performanceConsole={performanceConsoleModel} />);

    expect(screen.getByTestId('performance-console')).toBeInTheDocument();
    expect(screen.queryByText(/Connecting/)).not.toBeInTheDocument();
  });

  it('falls back to the connecting placeholder on the Performance Console route without a model', () => {
    setHash('/performance-console');
    const fake = new FakeCockpitClient();

    render(<App client={fake.asClient()} />);

    expect(screen.getByText(/Connecting/)).toBeInTheDocument();
    expect(screen.queryByTestId('performance-console')).not.toBeInTheDocument();
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
