import { act, fireEvent, render, renderHook, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { ActionBar } from '../../src/cockpit/ActionBar';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { ExactRytmPlanInspection, ExactRytmSendDialog, useExactRytmSend } from '../../src/cockpit/ExactRytmSend';
import { SafetyRail } from '../../src/cockpit/SafetyRail';
import { useCockpitStore } from '../../src/state';
import type { CockpitSendPlan, Command } from '../../src/ws/protocol';

import { candidate, FakeCockpitClient, pad2RehearsalPlan, readyDualMachineStage, sendPlan, sessionLive } from './_fixtures';

describe('exact Rytm plan inspection', () => {
  beforeEach(() => act(() => useCockpitStore.getState().reset()));
  afterEach(() => act(() => useCockpitStore.getState().reset()));

  it('preserves frozen blocked packets, duplicates, canonical keys and server order without filtering', () => {
    const first = { pad_id: 12, parameter: 'lfo_depth', channel: 15, control: 109, value: 127 };
    const last = { pad_id: 1, parameter: 'flt', channel: 0, control: 74, value: 0 };
    const plan: CockpitSendPlan = {
      ...pad2RehearsalPlan, ready: false,
      readiness_reason: 'paired_control_precision_unverified',
      blocked_reasons: ['paired_control_precision_unverified'],
      locked_pad_ids: [12], target_pad_ids: [2],
      packets: [first, first, last],
    };
    const original = structuredClone(plan);
    Object.freeze(plan);
    Object.freeze(plan.packets);
    plan.packets.forEach((packet) => Object.freeze(packet));
    render(<ExactRytmPlanInspection sendPlan={plan} />);
    const table = screen.getByRole('table', { name: 'Exact prepared Rytm packets' });
    expect(within(table).getAllByRole('row').slice(1).map((row) =>
      within(row).getAllByRole('cell').map((cell) => cell.textContent),
    )).toEqual([
      ['12', 'lfo_depth', '16', '109', '127'],
      ['12', 'lfo_depth', '16', '109', '127'],
      ['1', 'flt', '1', '74', '0'],
    ]);
    expect(screen.getByText(plan.plan_id)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    expect(plan).toEqual(original);
  });

  it('shows the rail\'s exact values in confirmation and requires a new confirmation after plan changes', () => {
    const fake = new FakeCockpitClient();
    act(() => {
      const store = useCockpitStore.getState();
      store.setConnectionStatus('connected');
      store.setSessionStatus(sessionLive);
      store.setDualMachineStage({
        ...readyDualMachineStage,
        rytm: { ...readyDualMachineStage.rytm, target_ids: [2], locked_ids: [], effective_ids: [2] },
      });
      store.setPreviewCandidate(candidate);
      store.setSendPlan(pad2RehearsalPlan);
    });
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <SafetyRail />
        <ActionBar previewOn onTogglePreview={() => undefined} />
      </CockpitClientProvider>,
    );
    const rail = screen.getByLabelText('Safety status');
    const railTable = within(rail).getByRole('table');
    fireEvent.click(screen.getByTestId('action-send'));
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText(pad2RehearsalPlan.plan_id)).toBeInTheDocument();
    expect(within(dialog).getByRole('table').innerHTML).toBe(railTable.innerHTML);
    expect(fake.sent).toEqual([]);

    const nextPlan: CockpitSendPlan = {
      ...pad2RehearsalPlan, plan_id: 'sendplan-pad2-new-values',
      packets: [{ pad_id: 2, parameter: 'flt', channel: 1, control: 74, value: 33 }],
      estimated_midi_msgs: 1,
    };
    act(() => useCockpitStore.getState().setSendPlan(nextPlan));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.queryByText(pad2RehearsalPlan.plan_id)).not.toBeInTheDocument();
    expect(within(rail).getByText(nextPlan.plan_id)).toBeInTheDocument();
    expect(within(rail).queryByText('amp_decay')).not.toBeInTheDocument();
    expect(fake.sent).toEqual([]);

    fireEvent.click(screen.getByTestId('action-send'));
    const nextDialog = screen.getByRole('dialog');
    const nextTable = within(nextDialog).getByRole('table');
    expect(nextTable.innerHTML).toBe(within(rail).getByRole('table').innerHTML);
    expect(within(nextTable).getAllByRole('row').slice(1).map((row) =>
      within(row).getAllByRole('cell').map((cell) => cell.textContent),
    )).toEqual([['2', 'flt', '2', '74', '33']]);
    expect(fake.sent).toEqual([]);
    fireEvent.click(within(nextDialog).getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(fake.sent).toEqual([]);
    fireEvent.click(screen.getByTestId('action-send'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm send' }));
    expect(fake.sent).toEqual([{ type: 'send', confirm: true, send_plan_id: nextPlan.plan_id }]);
    expect(useCockpitStore.getState().sessionStatus).toEqual(sessionLive);
    expect(nextPlan.packets[0]?.channel).toBe(1);
  });

  it('closes confirmation if the current plan becomes blocked without sending any retained packets', () => {
    const sent: Command[] = [];
    const { result, rerender } = renderHook(
      ({ plan, canSend }) => useExactRytmSend({
        canSend, sendPlan: plan, session: sessionLive, onSend: (command) => sent.push(command),
      }),
      { initialProps: { plan: pad2RehearsalPlan, canSend: true } },
    );
    act(() => result.current.request());
    expect(result.current.confirmationOpen).toBe(true);
    rerender({
      plan: { ...pad2RehearsalPlan, ready: false, readiness_reason: 'paired_control_precision_unverified', blocked_reasons: ['paired_control_precision_unverified'] },
      canSend: false,
    });
    expect(result.current.confirmationOpen).toBe(false);
    act(() => { result.current.request(); result.current.confirm(); });
    expect(sent).toEqual([]);
  });
});

describe('exact Rytm send controller', () => {
  it('refuses stale or unconfirmed programmatic send attempts', () => {
    const sent: Command[] = [];
    const { result, rerender } = renderHook(
      ({ canSend }) => useExactRytmSend({ canSend, sendPlan, session: sessionLive, onSend: (command) => sent.push(command) }),
      { initialProps: { canSend: false } },
    );
    act(() => { result.current.request(); result.current.confirm(); });
    expect(sent).toEqual([]);
    rerender({ canSend: true });
    act(() => result.current.confirm());
    expect(sent).toEqual([]);
    act(() => result.current.request());
    expect(result.current.confirmationOpen).toBe(true);
    rerender({ canSend: false });
    expect(result.current.confirmationOpen).toBe(false);
    act(() => result.current.confirm());
    expect(sent).toEqual([]);
  });

  it('requires a new explicit source reload attestation for every Show audition', () => {
    const sent: Command[] = [];
    const { result } = renderHook(() => useExactRytmSend({
      canSend: true, sendPlan, session: sessionLive,
      sourceReload: { fingerprint: 'source-one', slot: null },
      onSend: (command) => sent.push(command),
    }));
    act(() => result.current.request());
    render(<ExactRytmSendDialog controller={result.current} sendPlan={sendPlan} session={sessionLive} />);
    expect(screen.getByRole('checkbox')).toHaveAccessibleName(/source slot not reported/);
    act(() => result.current.confirm());
    expect(sent).toEqual([]);
    act(() => result.current.setSourceReloadConfirmed(true));
    act(() => result.current.confirm());
    expect(sent).toEqual([{ type: 'send', confirm: true, send_plan_id: sendPlan.plan_id, show_bank_source_reloaded: true }]);
    act(() => result.current.request());
    expect(result.current.sourceReloadConfirmed).toBe(false);
    act(() => result.current.confirm());
    expect(sent).toHaveLength(1);
  });
});
