/**
 * Tests for ArmControl — the two-factor arm dialog (token + confirm:true),
 * the one-click disarm, and every ack / rejection branch.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import { ArmControl } from '../../src/cockpit/ArmControl';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, sessionLive, sessionMock } from './_fixtures';

function renderArmControl(fake: FakeCockpitClient): void {
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <ArmControl />
    </CockpitClientProvider>,
  );
}

describe('ArmControl', () => {
  beforeEach(() => {
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

  it('opens the confirm dialog, requires a token, and sends arm with confirm:true', async () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    const fake = new FakeCockpitClient();
    renderArmControl(fake);

    fireEvent.click(screen.getByTestId('arm-open-button'));
    expect(screen.getByTestId('arm-dialog')).toBeInTheDocument();

    // Token empty → confirm disabled → nothing sent.
    expect(screen.getByTestId('arm-confirm-button')).toBeDisabled();
    expect(fake.sent).toEqual([]);

    fireEvent.change(screen.getByTestId('arm-token-input'), {
      target: { value: 'tok-123' },
    });
    fireEvent.click(screen.getByTestId('arm-confirm-button'));
    expect(fake.sent).toEqual([{ type: 'arm', arm_token: 'tok-123', confirm: true }]);

    // ok ack → dialog closes.
    await waitFor(() =>
      expect(screen.queryByTestId('arm-dialog')).not.toBeInTheDocument(),
    );
  });

  it('cancel closes the dialog without sending; Escape also closes it', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
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
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: false, message: 'bad token' });
    renderArmControl(fake);

    fireEvent.click(screen.getByTestId('arm-open-button'));
    fireEvent.change(screen.getByTestId('arm-token-input'), { target: { value: 'x' } });
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
});
