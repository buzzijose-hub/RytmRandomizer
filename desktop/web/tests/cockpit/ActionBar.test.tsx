/**
 * Tests for ActionBar — PREVIEW toggle, REGEN, SEND (disabled paths), UNDO (disabled paths), SAVE.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

import { ActionBar } from '../../src/cockpit/ActionBar';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { useCockpitStore } from '../../src/state';

import {
  FakeCockpitClient,
  blockedSendPlan,
  candidate,
  history,
  sendPlan,
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

  beforeEach(() => {
    updateStore(() => useCockpitStore.getState().reset());
  });
  afterEach(() => {
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
    const { fake, toggle } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(toggle).toHaveBeenCalledWith(true);
    expect(fake.sent).toEqual([{ type: 'toggle_preview', on: true }]);
  });

  it('clicking PREVIEW when on emits toggle_preview {on: false}', () => {
    const { fake, toggle } = renderWith(true);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(toggle).toHaveBeenCalledWith(false);
    expect(fake.sent).toEqual([{ type: 'toggle_preview', on: false }]);
  });

  it('REGEN emits regen', () => {
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
    updateStore(() => {
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan(blockedSendPlan);
    });
    const { fake } = renderWith(true);
    const send = screen.getByTestId('action-send');
    expect(send).toBeDisabled();
    fireEvent.click(send);
    expect(fake.sent).toEqual([]);
  });

  it('SEND enabled with safe candidate, shows mock-safe dry-run label, and emits send', () => {
    updateStore(() => {
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan(sendPlan);
    });
    const { fake } = renderWith(true);
    const send = screen.getByTestId('action-send');
    expect(send).not.toBeDisabled();
    expect(send).toHaveTextContent('DRY-RUN SEND');
    expect(send).toHaveTextContent('(2 pads)');
    fireEvent.click(send);
    expect(fake.sent).toEqual([{ type: 'send' }]);
  });

  it('SEND shows the live-hardware label only when the session is live and armed', () => {
    updateStore(() => {
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan(sendPlan);
      useCockpitStore.getState().setSessionStatus({
        armed: true,
        midi_port: 'IAC Driver Bus 1',
        mode: 'live',
        connection_phase: 'armed',
        unsaved_sends: 0,
      });
    });
    renderWith(true);
    expect(screen.getByTestId('action-send')).toHaveTextContent('SEND');
    expect(screen.getByTestId('action-send')).not.toHaveTextContent('DRY-RUN SEND');
  });

  it('logs rejected command acks for operator troubleshooting', async () => {
    updateStore(() => {
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan(sendPlan);
    });
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
    updateStore(() => {
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan(sendPlan);
    });
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
    updateStore(() => {
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan({ ...sendPlan, pad_count: 1 });
    });
    renderWith(true);
    expect(screen.getByTestId('action-send')).toHaveTextContent('DRY-RUN SEND');
    expect(screen.getByTestId('action-send')).toHaveTextContent('(1 pad)');
  });

  it('SEND omits the pad-count chip when candidate has zero deltas', () => {
    updateStore(() => {
      useCockpitStore.getState().setPreviewCandidate(candidate);
      useCockpitStore.getState().setSendPlan({ ...sendPlan, pad_count: 0, packets: [] });
    });
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
    const { fake } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-save'));
    expect(fake.sent).toEqual([{ type: 'save' }]);
  });
});
