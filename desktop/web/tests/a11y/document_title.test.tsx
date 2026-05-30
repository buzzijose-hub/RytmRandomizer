/**
 * Per-route document.title verification (WCAG 2.4.2).
 *
 * Uses the FakeCockpitClient fixture so the App's `useCockpitStore`
 * receives a `sessionStatus` and renders Cockpit / Wizard rather than
 * the "Connecting" placeholder.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { App } from '../../src/App';
import { useCockpitStore } from '../../src/state';
import { useWizardStore } from '../../src/state/wizard_store';

import { FakeCockpitClient, sessionLive, snapshot } from '../cockpit/_fixtures';

function setHash(hash: string): void {
  window.location.hash = hash;
}

function fireHashChange(): void {
  window.dispatchEvent(new HashChangeEvent('hashchange'));
}

describe('document.title per route', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
    useWizardStore.getState().reset();
    setHash('');
    fireHashChange();
  });

  afterEach(() => {
    setHash('');
    fireHashChange();
    useCockpitStore.getState().reset();
    useWizardStore.getState().reset();
  });

  it('cockpit route sets title to "RytmRandomizer · Cockpit"', async () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    await waitFor(
      () => expect(screen.queryByTestId('cockpit-root')).toBeInTheDocument(),
      { timeout: 5000 },
    );
    await waitFor(
      () => expect(document.title).toBe('RytmRandomizer · Cockpit'),
      { timeout: 5000 },
    );
  });

  it('wizard route sets title to "RytmRandomizer · Profile Wizard"', async () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    await waitFor(
      () => expect(screen.queryByTestId('cockpit-root')).toBeInTheDocument(),
      { timeout: 5000 },
    );
    await act(async () => {
      setHash('/wizard');
      fireHashChange();
    });
    await waitFor(
      () => expect(screen.queryByTestId('wizard-root')).toBeInTheDocument(),
      { timeout: 5000 },
    );
    await waitFor(
      () => expect(document.title).toBe('RytmRandomizer · Profile Wizard'),
      { timeout: 5000 },
    );
  });
});
