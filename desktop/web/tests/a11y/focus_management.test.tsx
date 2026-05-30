/**
 * Focus moves to the route container when the hash route changes.
 *
 * The hook is a 3-line `useEffect`; coverage is driven from this test
 * via the App-level integration so the happy path AND the null-ref
 * early-return branch both fire (the null-ref branch executes during
 * initial render before the ref is attached, then runs the focus
 * branch on subsequent route-change effects).
 *
 * Renders App with the FakeCockpitClient fixture used by router.test.tsx
 * so no real WebSocket / sidecar is required.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import type { RefObject } from 'react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { useFocusOnRouteChange } from '../../src/a11y';
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

describe('Focus management on route change', () => {
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

  it('cockpit route container has focus after the initial route load', async () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setSessionStatus(sessionLive);
    useCockpitStore.getState().setSnapshot(snapshot);
    render(<App client={fake.asClient()} />);
    await waitFor(
      () => expect(screen.queryByTestId('cockpit-root')).toBeInTheDocument(),
      { timeout: 5000 },
    );
    // The focused element should be the route container (a focusable
    // ancestor of cockpit-root) — not body.
    expect(document.activeElement).not.toBe(document.body);
    const cockpitRoot = screen.getByTestId('cockpit-root');
    expect(
      document.activeElement === cockpitRoot ||
        cockpitRoot.contains(document.activeElement) ||
        (document.activeElement !== null &&
          document.activeElement.contains(cockpitRoot)),
    ).toBe(true);
  });

  it('switching hash to #/wizard moves focus into the wizard surface', async () => {
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
    expect(document.activeElement).not.toBe(document.body);
    const wizardRoot = screen.getByTestId('wizard-root');
    expect(
      document.activeElement === wizardRoot ||
        wizardRoot.contains(document.activeElement) ||
        (document.activeElement !== null &&
          document.activeElement.contains(wizardRoot)),
    ).toBe(true);
  });

  it('does nothing when the ref is null (early-return branch coverage)', () => {
    // Directly exercise the hook with a never-attached ref so the
    // `ref.current === null` early-return executes without errors.
    // Test pattern from React Testing Library: render a tiny harness
    // whose only purpose is to call the hook.
    function Harness(): JSX.Element {
      const ref: RefObject<HTMLElement> = { current: null };
      useFocusOnRouteChange(ref, ['only-once']);
      return <span data-testid="harness-mounted" />;
    }
    render(<Harness />);
    // If the hook didn't early-return, .focus() on null would throw and
    // the render would crash before reaching this assertion.
    expect(screen.getByTestId('harness-mounted')).toBeInTheDocument();
  });
});
