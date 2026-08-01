/**
 * Tests for ArmControl — the three-factor arm dialog (exact port + token +
 * confirm:true), the one-click disarm, and every ack / rejection branch.
 *
 * The port selector is the safety control this suite guards hardest: with two
 * Elektron machines connected, arming without naming one can arm the wrong
 * instrument.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import { ArmControl } from '../../src/cockpit/ArmControl';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { useCockpitStore } from '../../src/state';

import {
  FakeCockpitClient,
  connectionListening,
  sessionLive,
  sessionMock,
} from './_fixtures';

const RYTM_OUT = 'Analog Rytm MK2 OUT';
const A4_OUT = 'Analog Four MKII OUT';

/** Seed the passive connection observation the selector is populated from. */
function seedOutputs(outputs: string[] = [RYTM_OUT]): void {
  act(() => {
    useCockpitStore.getState().setConnection({
      ...connectionListening,
      available_outputs: outputs,
    });
  });
}

/** The per-launch ARM secret the shell injects before any app code runs. */
const INJECTED_ARM_SECRET = 'injected-arm-secret';

/** Simulate the Tauri shell's injection (sidecar.rs::arm_secret_bootstrap_script). */
function injectArmSecret(secret: string | null = INJECTED_ARM_SECRET): void {
  const w = window as { __RYTM_RAND_ARM_SECRET__?: string };
  if (secret === null) {
    delete w.__RYTM_RAND_ARM_SECRET__;
    window.localStorage.removeItem('rytm-rand-arm-secret');
    return;
  }
  w.__RYTM_RAND_ARM_SECRET__ = secret;
}

/** Open the dialog and choose the exact port (the only operator input now). */
function fillArmDialog(port: string = RYTM_OUT): void {
  fireEvent.click(screen.getByTestId('arm-open-button'));
  fireEvent.change(screen.getByTestId('arm-port-select'), { target: { value: port } });
}

function renderArmControl(fake: FakeCockpitClient): void {
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <ArmControl />
    </CockpitClientProvider>,
  );
}

describe('ArmControl', () => {
  beforeEach(() => {
    // The shell injects the ARM secret before app code runs; the
    // missing-secret test clears it explicitly.
    injectArmSecret();
    act(() => {
      useCockpitStore.getState().reset();
    });
  });
  afterEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('defaults to the passive Arm affordance before any session_status arrives', () => {
    const fake = new FakeCockpitClient();
    renderArmControl(fake);
    expect(screen.getByTestId('arm-open-button')).toBeInTheDocument();
    expect(screen.queryByTestId('disarm-button')).not.toBeInTheDocument();
  });

  it('requires BOTH an exact port and a token, then sends them with confirm:true', async () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs([RYTM_OUT, A4_OUT]);
    const fake = new FakeCockpitClient();
    renderArmControl(fake);

    fireEvent.click(screen.getByTestId('arm-open-button'));
    expect(screen.getByTestId('arm-dialog')).toBeInTheDocument();

    // No port chosen → confirm disabled → nothing sent. An injected secret
    // alone is NOT enough: naming the exact instrument is the operator's
    // deliberate act, and there is no default selection.
    expect(screen.getByTestId('arm-confirm-button')).toBeDisabled();
    fireEvent.click(screen.getByTestId('arm-confirm-button'));
    expect(fake.sent).toEqual([]);

    // Choosing the port satisfies the last factor.
    fireEvent.change(screen.getByTestId('arm-port-select'), {
      target: { value: A4_OUT },
    });
    expect(screen.getByTestId('arm-confirm-button')).toBeEnabled();
    fireEvent.click(screen.getByTestId('arm-confirm-button'));
    // The token is the SHELL-INJECTED secret, never anything the operator
    // typed, and the port is the exact chosen name.
    expect(fake.sent).toEqual([
      {
        type: 'arm',
        arm_token: INJECTED_ARM_SECRET,
        port_name: A4_OUT,
        confirm: true,
      },
    ]);

    // ok ack → dialog closes.
    await waitFor(() =>
      expect(screen.queryByTestId('arm-dialog')).not.toBeInTheDocument(),
    );
  });

  it('re-disables confirm when the operator deselects the port again', () => {
    // The disabled state is the control: it must track the CURRENT choice,
    // not merely latch once both factors were briefly satisfied.
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs([RYTM_OUT]);
    const fake = new FakeCockpitClient();
    renderArmControl(fake);

    fillArmDialog(RYTM_OUT);
    const confirm = screen.getByTestId('arm-confirm-button');
    expect(confirm).toBeEnabled();

    // Back to the placeholder: confirm goes disabled and nothing can be sent.
    fireEvent.change(screen.getByTestId('arm-port-select'), { target: { value: '' } });
    expect(confirm).toBeDisabled();
    fireEvent.click(confirm);

    expect(fake.sent).toEqual([]);
    expect(screen.getByTestId('arm-dialog')).toBeInTheDocument();
  });

  it('renders one option per enumerated output, defaulting to none', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs([RYTM_OUT, A4_OUT]);
    renderArmControl(new FakeCockpitClient());
    fireEvent.click(screen.getByTestId('arm-open-button'));

    const select = screen.getByTestId('arm-port-select') as HTMLSelectElement;
    // The placeholder plus one option per enumerated output.
    expect([...select.options].map((o) => o.value)).toEqual(['', RYTM_OUT, A4_OUT]);
    // Nothing is pre-selected: pre-picking would reintroduce the auto-pick.
    expect(select.value).toBe('');
    expect(screen.queryByTestId('arm-no-ports')).not.toBeInTheDocument();
  });

  it('the port selector is a labelled, keyboard-operable control', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs([RYTM_OUT]);
    renderArmControl(new FakeCockpitClient());
    fireEvent.click(screen.getByTestId('arm-open-button'));

    // A real <label for> association — reachable by accessible name.
    const select = screen.getByLabelText('MIDI output port');
    expect(select).toBe(screen.getByTestId('arm-port-select'));
    // Natively focusable (no tabindex hack), so Tab reaches it.
    select.focus();
    expect(document.activeElement).toBe(select);
    // The token input is labelled too.
    // The arm secret is injected, so there is no token field to label.
    expect(screen.queryByTestId('arm-token-input')).toBeNull();
  });

  it('explains the empty state when no outputs are enumerated', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs([]);
    renderArmControl(new FakeCockpitClient());
    fireEvent.click(screen.getByTestId('arm-open-button'));

    expect(screen.getByTestId('arm-no-ports')).toBeInTheDocument();
    // With no port choosable, arming stays blocked no matter the token.
    expect(screen.getByTestId('arm-confirm-button')).toBeDisabled();
  });

  it('blocks arming when the store carries no connection observation at all', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    renderArmControl(new FakeCockpitClient());
    fireEvent.click(screen.getByTestId('arm-open-button'));

    const select = screen.getByTestId('arm-port-select') as HTMLSelectElement;
    expect([...select.options].map((o) => o.value)).toEqual(['']);
    expect(screen.getByTestId('arm-no-ports')).toBeInTheDocument();
  });

  it('cancel closes the dialog without sending; Escape also closes it', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs();
    const fake = new FakeCockpitClient();
    renderArmControl(fake);

    fireEvent.click(screen.getByTestId('arm-open-button'));
    fireEvent.click(screen.getByTestId('arm-cancel-button'));
    expect(screen.queryByTestId('arm-dialog')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('arm-open-button'));
    fireEvent.keyDown(screen.getByTestId('arm-dialog'), { key: 'Escape' });
    expect(screen.queryByTestId('arm-dialog')).not.toBeInTheDocument();

    // A non-Escape key leaves the dialog open.
    fireEvent.click(screen.getByTestId('arm-open-button'));
    fireEvent.keyDown(screen.getByTestId('arm-dialog'), { key: 'Enter' });
    expect(screen.getByTestId('arm-dialog')).toBeInTheDocument();
    expect(fake.sent).toEqual([]);
  });

  it('surfaces a rejected arm ack (message and fallback) and a send failure', async () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs();
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: false, message: 'bad token' });
    renderArmControl(fake);

    fillArmDialog(RYTM_OUT);
    fireEvent.click(screen.getByTestId('arm-confirm-button'));
    await screen.findByText('bad token');
    expect(screen.getByTestId('arm-dialog')).toBeInTheDocument();

    // No message on the ack → canonical fallback text.
    fake.ackQueue.push({ request_id: 'r2', ok: false });
    fireEvent.click(screen.getByTestId('arm-confirm-button'));
    await screen.findByText('Arm request rejected');

    // Transport failure → catch branch.
    fake.nextRejection = new Error('socket not open');
    fireEvent.click(screen.getByTestId('arm-confirm-button'));
    await screen.findByText('Arm request failed to send');
  });

  it('disarms in one click when armed and announces ok acks', async () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
    });
    const fake = new FakeCockpitClient();
    renderArmControl(fake);

    const disarm = screen.getByTestId('disarm-button');
    expect(disarm).toHaveTextContent('ARMED — Disarm');
    fireEvent.click(disarm);
    expect(fake.sent).toEqual([{ type: 'disarm' }]);
    await waitFor(() => expect(fake.sent).toHaveLength(1));
  });

  it('renders the arm rejection inside the dialog as a role=alert', async () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs();
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: false, message: 'bad token' });
    renderArmControl(fake);

    fillArmDialog(RYTM_OUT);
    fireEvent.click(screen.getByTestId('arm-confirm-button'));

    const alert = await screen.findByTestId('arm-dialog-error');
    expect(alert).toHaveAttribute('role', 'alert');
    expect(alert).toHaveTextContent('bad token');
    // Dialog stays open so the operator can retry; error is visible within it.
    expect(screen.getByTestId('arm-dialog')).toBeInTheDocument();
  });

  it('traps Tab focus inside the dialog (forward + reverse wrap), no-op mid-list', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs();
    const fake = new FakeCockpitClient();
    renderArmControl(fake);
    fireEvent.click(screen.getByTestId('arm-open-button'));
    const dialog = screen.getByTestId('arm-dialog');
    const portSelect = screen.getByTestId('arm-port-select');
    const cancel = screen.getByTestId('arm-cancel-button');
    // Choosing a port enables confirm, giving the trap a real mid-list
    // element: [port select, cancel, confirm]. The select MUST be inside the
    // trap — otherwise Tab escapes the dialog at the very control the
    // operator has to use.
    fireEvent.change(portSelect, { target: { value: RYTM_OUT } });
    const confirm = screen.getByTestId('arm-confirm-button');
    expect(confirm).toBeEnabled();

    // Shift+Tab on the first element wraps to the last.
    portSelect.focus();
    fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(confirm);

    // Tab on the last element wraps to the first.
    confirm.focus();
    fireEvent.keyDown(dialog, { key: 'Tab' });
    expect(document.activeElement).toBe(portSelect);

    // Tab in the middle / on a non-boundary element is a no-op (default flow).
    cancel.focus();
    fireEvent.keyDown(dialog, { key: 'Tab' });
    expect(document.activeElement).toBe(cancel);
  });

  it('the focus trap no-ops when the dialog momentarily has no focusable children', () => {
    // Guard the `focusable.length === 0` branch. The real dialog always has
    // children, so drive trapFocus against a synthetic empty container via a
    // Tab keydown on an emptied dialog clone.
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    const fake = new FakeCockpitClient();
    renderArmControl(fake);
    fireEvent.click(screen.getByTestId('arm-open-button'));
    const dialog = screen.getByTestId('arm-dialog');
    // Strip every focusable child, then Tab: the early return keeps focus put.
    dialog.querySelectorAll('button, input, select').forEach((el) => el.remove());
    const before = document.activeElement;
    fireEvent.keyDown(dialog, { key: 'Tab' });
    expect(document.activeElement).toBe(before);
  });

  it('surfaces a rejected disarm ack (message and fallback) and a send failure', async () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
    });
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: false, message: 'still busy' });
    renderArmControl(fake);

    fireEvent.click(screen.getByTestId('disarm-button'));
    await screen.findByText('still busy');

    fake.ackQueue.push({ request_id: 'r2', ok: false });
    fireEvent.click(screen.getByTestId('disarm-button'));
    await screen.findByText('Disarm request rejected');

    fake.nextRejection = new Error('socket not open');
    fireEvent.click(screen.getByTestId('disarm-button'));
    await screen.findByText('Disarm request failed to send');
  });

  it('falls closed and explains itself when no arm secret was injected', () => {
    // A packaged build always injects; a bare browser / stale webview may
    // not. Sending an empty token would surface as an opaque server refusal,
    // so the dialog names the real cause and refuses to send at all.
    injectArmSecret(null);
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs([RYTM_OUT]);
    const fake = new FakeCockpitClient();
    renderArmControl(fake);

    fillArmDialog(RYTM_OUT);

    expect(screen.getByTestId('arm-no-secret')).toBeInTheDocument();
    // Confirm stays disabled even with a valid port chosen.
    expect(screen.getByTestId('arm-confirm-button')).toBeDisabled();
    fireEvent.click(screen.getByTestId('arm-confirm-button'));
    expect(fake.sent).toEqual([]);
  });

  it('reads the injected arm secret from localStorage after a webview reload', () => {
    // The window property is set once at injection; localStorage is the
    // survivor across a reload. Precedence mirrors the WS auth token.
    injectArmSecret(null);
    window.localStorage.setItem('rytm-rand-arm-secret', 'stored-secret');
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    seedOutputs([RYTM_OUT]);
    const fake = new FakeCockpitClient();
    renderArmControl(fake);

    fillArmDialog(RYTM_OUT);
    fireEvent.click(screen.getByTestId('arm-confirm-button'));

    expect(fake.sent).toEqual([
      { type: 'arm', arm_token: 'stored-secret', port_name: RYTM_OUT, confirm: true },
    ]);
    window.localStorage.removeItem('rytm-rand-arm-secret');
  });
});
