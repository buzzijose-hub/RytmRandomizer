/**
 * Tests for ActionBar — PREVIEW toggle, REGEN, SEND (disabled paths), UNDO (disabled paths), SAVE.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

import { ActionBar } from '../../src/cockpit/ActionBar';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { useCockpitStore, type SessionStatus } from '../../src/state';

import {
  FakeCockpitClient,
  blockedSendPlan,
  candidate,
  history,
  readyDualMachineStage,
  sendPlan,
  sessionMock,
} from './_fixtures';

interface Harness {
  fake: FakeCockpitClient;
  toggle: ReturnType<typeof vi.fn>;
}

function renderWith(previewOn: boolean): Harness {
  const fake = new FakeCockpitClient();
  const toggle = vi.fn();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <ActionBar previewOn={previewOn} onTogglePreview={toggle} />
    </CockpitClientProvider>,
  );
  return { fake, toggle };
}

describe('ActionBar', () => {
  const updateStore = (update: () => void): void => {
    act(update);
  };

  /** Most tests exercise a connected (mock) session; offline tests skip this. */
  const seedSession = (): void => {
    updateStore(() => {
      useCockpitStore.getState().setConnectionStatus('connected');
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
  };

  const seedPreparedState = (
    plan: typeof sendPlan = sendPlan,
    status: SessionStatus = sessionMock,
  ): void => {
    updateStore(() => {
      useCockpitStore.getState().setConnectionStatus('connected');
      useCockpitStore.getState().setDualMachineStage(readyDualMachineStage);
      useCockpitStore.getState().setSessionStatus(status);
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan(plan);
    });
  };

  beforeEach(() => {
    updateStore(() => useCockpitStore.getState().reset());
  });
  afterEach(() => {
    vi.restoreAllMocks();
    updateStore(() => useCockpitStore.getState().reset());
  });

  it('preview button shows "(off)" label and aria-pressed=false when previewOn=false', () => {
    renderWith(false);
    const btn = screen.getByTestId('action-preview');
    expect(btn).toHaveTextContent('PREVIEW (off)');
    expect(btn).toHaveAttribute('aria-pressed', 'false');
    expect(btn.className).toBe('action-button toggle');
  });

  it('preview button shows "(on)" label and the on class when previewOn=true', () => {
    renderWith(true);
    const btn = screen.getByTestId('action-preview');
    expect(btn).toHaveTextContent('PREVIEW (on)');
    expect(btn).toHaveAttribute('aria-pressed', 'true');
    expect(btn.className).toBe('action-button toggle on');
  });

  it('clicking PREVIEW calls onTogglePreview(true) and emits toggle_preview {on: true} when off', () => {
    seedSession();
    const { fake, toggle } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(toggle).toHaveBeenCalledWith(true);
    expect(fake.sent).toEqual([{ type: 'toggle_preview', on: true }]);
  });

  it('clicking PREVIEW when on emits toggle_preview {on: false}', () => {
    seedSession();
    const { fake, toggle } = renderWith(true);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(toggle).toHaveBeenCalledWith(false);
    expect(fake.sent).toEqual([{ type: 'toggle_preview', on: false }]);
  });

  it('REGEN emits regen', () => {
    seedSession();
    const { fake } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-regen'));
    expect(fake.sent).toEqual([{ type: 'regen' }]);
  });

  it('PREPARE is disabled when there is no candidate', () => {
    const { fake } = renderWith(false);
    const prepare = screen.getByTestId('action-prepare-send-plan');
    expect(prepare).toBeDisabled();
    fireEvent.click(prepare);
    expect(fake.sent).toEqual([]);
  });

  it('PREPARE emits prepare_send_plan when a candidate is staged', () => {
    updateStore(() => useCockpitStore.getState().setPreviewCandidate(candidate));
    const { fake } = renderWith(true);
    const prepare = screen.getByTestId('action-prepare-send-plan');
    expect(prepare).not.toBeDisabled();
    fireEvent.click(prepare);
    expect(fake.sent).toEqual([{ type: 'prepare_send_plan' }]);
  });

  it('SEND is disabled when there is no ready send plan', () => {
    const { fake } = renderWith(false);
    const send = screen.getByTestId('action-send');
    expect(send).toBeDisabled();
    fireEvent.click(send);
    expect(fake.sent).toEqual([]);
  });

  it('SEND is disabled and unclickable when send plan is blocked', () => {
    seedPreparedState(blockedSendPlan);
    const { fake } = renderWith(true);
    const send = screen.getByTestId('action-send');
    expect(send).toBeDisabled();
    fireEvent.click(send);
    expect(fake.sent).toEqual([]);
  });

  it('SEND enabled with safe candidate, shows mock-safe dry-run label, and emits the plan id', () => {
    seedPreparedState();
    const { fake } = renderWith(true);
    const send = screen.getByTestId('action-send');
    expect(send).not.toBeDisabled();
    expect(send).toHaveTextContent('DRY-RUN SEND');
    expect(send).toHaveTextContent('(2 pads)');
    fireEvent.click(send);
    // The mock path stays one click and carries no per-action confirmation,
    // while still binding the request to the exact prepared plan.
    expect(fake.sent).toEqual([{ type: 'send', send_plan_id: sendPlan.plan_id }]);
    expect(screen.queryByTestId('send-confirm-dialog')).toBeNull();
  });

  it('SEND shows the live-hardware label only when the session is live and armed', () => {
    seedPreparedState(sendPlan, {
      armed: true,
      midi_port: 'IAC Driver Bus 1',
      mode: 'live',
      connection_phase: 'armed',
      unsaved_sends: 0,
      capture_enabled: true,
    });
    renderWith(true);
    expect(screen.getByTestId('action-send')).toHaveTextContent('SEND');
    expect(screen.getByTestId('action-send')).not.toHaveTextContent('DRY-RUN SEND');
  });

  describe('armed per-action send confirmation', () => {
    const armLiveSession = (port: string | null = 'IAC Driver Bus 1'): void => {
      seedPreparedState(sendPlan, {
        armed: true,
        midi_port: port,
        mode: 'live',
        connection_phase: 'armed',
        unsaved_sends: 0,
        capture_enabled: true,
      });
    };

    it('armed SEND opens the confirm dialog and emits nothing until confirmed', () => {
      armLiveSession();
      const { fake } = renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      expect(fake.sent).toEqual([]);
      const dialog = screen.getByTestId('send-confirm-dialog');
      expect(dialog).toHaveAttribute('role', 'dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      // Real label, not a testid-only affordance.
      expect(screen.getByRole('heading', { name: 'Confirm send to hardware' })).toBeTruthy();
      expect(dialog).toHaveTextContent('IAC Driver Bus 1');
      expect(dialog).toHaveTextContent(sendPlan.plan_id);
      expect(dialog).toHaveTextContent('1, 3');
      expect(dialog).toHaveTextContent('Messages');
      expect(dialog).toHaveTextContent('2');
    });

    it('confirming an armed SEND emits confirmation with the exact plan id and closes', () => {
      armLiveSession();
      const { fake } = renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      fireEvent.click(screen.getByRole('button', { name: 'Confirm send' }));
      expect(fake.sent).toEqual([
        { type: 'send', confirm: true, send_plan_id: sendPlan.plan_id },
      ]);
      expect(screen.queryByTestId('send-confirm-dialog')).toBeNull();
    });

    it('cancelling an armed SEND emits nothing and closes the dialog', () => {
      armLiveSession();
      const { fake } = renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
      expect(fake.sent).toEqual([]);
      expect(screen.queryByTestId('send-confirm-dialog')).toBeNull();
    });

    it('Escape closes the confirm dialog without sending', () => {
      armLiveSession();
      const { fake } = renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      fireEvent.keyDown(screen.getByTestId('send-confirm-dialog'), { key: 'Escape' });
      expect(fake.sent).toEqual([]);
      expect(screen.queryByTestId('send-confirm-dialog')).toBeNull();
    });

    it('Tab wraps focus from the last control back to the first (focus trap)', () => {
      armLiveSession();
      renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      const dialog = screen.getByTestId('send-confirm-dialog');
      const cancel = screen.getByTestId('send-cancel-button');
      const confirm = screen.getByTestId('send-confirm-button');
      confirm.focus();
      fireEvent.keyDown(dialog, { key: 'Tab' });
      expect(document.activeElement).toBe(cancel);
    });

    it('Shift+Tab wraps focus from the first control back to the last (focus trap)', () => {
      armLiveSession();
      renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      const dialog = screen.getByTestId('send-confirm-dialog');
      const cancel = screen.getByTestId('send-cancel-button');
      const confirm = screen.getByTestId('send-confirm-button');
      cancel.focus();
      fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true });
      expect(document.activeElement).toBe(confirm);
    });

    it('Tab is left alone when focus is not on either edge control', () => {
      armLiveSession();
      renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      const dialog = screen.getByTestId('send-confirm-dialog');
      // Focus parked outside the dialog's focusable set: neither the
      // first-control nor last-control wrap applies, so the browser's own Tab
      // handling stands and focus must not be forced anywhere.
      const outside = screen.getByTestId('action-regen');
      outside.focus();
      fireEvent.keyDown(dialog, { key: 'Tab' });
      expect(document.activeElement).toBe(outside);
      expect(screen.getByTestId('send-confirm-dialog')).toBeTruthy();
    });

    it('other keys inside the dialog neither close it nor move focus', () => {
      armLiveSession();
      const { fake } = renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      fireEvent.keyDown(screen.getByTestId('send-confirm-dialog'), { key: 'a' });
      expect(screen.getByTestId('send-confirm-dialog')).toBeTruthy();
      expect(fake.sent).toEqual([]);
    });

    it('drops the open confirm dialog if the session disarms underneath it', () => {
      armLiveSession();
      renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      expect(screen.getByTestId('send-confirm-dialog')).toBeTruthy();

      // Cable pull / explicit disarm while the dialog is up.
      updateStore(() => {
        useCockpitStore.getState().setSessionStatus({
          armed: false,
          midi_port: null,
          mode: 'mock',
          connection_phase: 'disconnected',
          unsaved_sends: 0,
          capture_enabled: false,
        });
      });

      expect(screen.queryByTestId('send-confirm-dialog')).toBeNull();
      expect(screen.getByTestId('action-send')).toHaveTextContent('DRY-RUN SEND');
    });

    it('disables armed SEND when the session reports no exact output port', () => {
      armLiveSession(null);
      const { fake } = renderWith(true);
      expect(screen.getByTestId('action-send')).toBeDisabled();
      expect(fake.sent).toEqual([]);
    });

    it('omits the pad-count phrase in the dialog when the plan has zero pads', () => {
      seedPreparedState({ ...sendPlan, pad_count: 0, packets: [] }, {
        armed: true,
        midi_port: 'IAC Driver Bus 1',
        mode: 'live',
        connection_phase: 'armed',
        unsaved_sends: 0,
        capture_enabled: true,
      });
      renderWith(true);
      fireEvent.click(screen.getByTestId('action-send'));
      expect(screen.getByTestId('send-confirm-dialog').textContent).not.toMatch(/\(\d+ pad/);
    });
  });

  it('logs rejected command acks for operator troubleshooting', async () => {
    seedPreparedState();
    const { fake } = renderWith(true);
    fake.ackQueue.push({ request_id: 'reject-1', ok: false, error: 'sidecar rejected send' });
    await act(async () => {
      fireEvent.click(screen.getByTestId('action-send'));
    });
    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      level: 'error',
      message: 'send failed: sidecar rejected send',
    });
  });

  it('logs the generic rejection reason when a command ack omits an error', async () => {
    seedPreparedState();
    const { fake } = renderWith(true);
    fake.ackQueue.push({ request_id: 'reject-generic', ok: false });
    await act(async () => {
      fireEvent.click(screen.getByTestId('action-send'));
      await Promise.resolve();
    });
    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      level: 'error',
      message: 'send failed: command rejected',
    });
  });

  it('logs Error command rejections for operator troubleshooting', async () => {
    seedSession();
    const { fake } = renderWith(true);
    fake.nextRejection = new Error('socket closed');
    await act(async () => {
      fireEvent.click(screen.getByTestId('action-regen'));
      await Promise.resolve();
    });
    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      level: 'error',
      message: 'regen failed: socket closed',
    });
  });

  it('logs non-Error command rejections for operator troubleshooting', async () => {
    seedSession();
    const { fake } = renderWith(true);
    fake.nextRejection = 'transport closed';
    await act(async () => {
      fireEvent.click(screen.getByTestId('action-regen'));
      await Promise.resolve();
    });
    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      level: 'error',
      message: 'regen failed: transport closed',
    });
  });

  it('SEND shows singular "1 pad" when exactly one delta is present', () => {
    seedPreparedState({ ...sendPlan, pad_count: 1 });
    renderWith(true);
    expect(screen.getByTestId('action-send')).toHaveTextContent('DRY-RUN SEND');
    expect(screen.getByTestId('action-send')).toHaveTextContent('(1 pad)');
  });

  it('SEND omits the pad-count chip when candidate has zero deltas', () => {
    seedPreparedState({ ...sendPlan, pad_count: 0, packets: [] });
    renderWith(true);
    expect(screen.getByTestId('action-send')).toHaveTextContent('DRY-RUN SEND');
    expect(screen.getByTestId('action-send').textContent).not.toMatch(/\(\d/);
  });

  it('UNDO is disabled when canUndo=false (no history)', () => {
    renderWith(false);
    const undo = screen.getByTestId('action-undo');
    expect(undo).toBeDisabled();
  });

  it('UNDO is enabled and emits undo when canUndo=true', () => {
    updateStore(() => useCockpitStore.getState().setHistory(history));
    const { fake } = renderWith(false);
    const undo = screen.getByTestId('action-undo');
    expect(undo).not.toBeDisabled();
    fireEvent.click(undo);
    expect(fake.sent).toEqual([{ type: 'undo' }]);
  });

  it('SAVE emits save (no label arg)', () => {
    seedSession();
    const { fake } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-save'));
    expect(fake.sent).toEqual([{ type: 'save' }]);
  });

  describe('offline (no session ever arrived)', () => {
    it('disables the sidecar-requiring buttons with an accessible reason — never hides them', () => {
      const { fake } = renderWith(false);

      for (const testId of ['action-preview', 'action-regen', 'action-save']) {
        const button = screen.getByTestId(testId);
        expect(button).toBeInTheDocument();
        expect(button).toBeDisabled();
        expect(button).toHaveAttribute('title', 'Requires sidecar connection');
        fireEvent.click(button);
      }
      expect(fake.sent).toEqual([]);
      // Data-driven buttons are disabled by their empty slices as before.
      expect(screen.getByTestId('action-prepare-send-plan')).toBeDisabled();
      expect(screen.getByTestId('action-send')).toBeDisabled();
      expect(screen.getByTestId('action-undo')).toBeDisabled();
    });

    it('re-enables the gated buttons the moment a session arrives', () => {
      renderWith(false);
      expect(screen.getByTestId('action-regen')).toBeDisabled();

      updateStore(() => useCockpitStore.getState().setSessionStatus(sessionMock));

      expect(screen.getByTestId('action-regen')).toBeEnabled();
      expect(screen.getByTestId('action-save')).toBeEnabled();
      expect(screen.getByTestId('action-preview')).toBeEnabled();
      expect(screen.getByTestId('action-regen')).not.toHaveAttribute('title');
    });
  });
});
