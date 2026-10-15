/**
 * Tests for SafetyRail -- passive session/device readiness summary.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, render, screen, within } from '@testing-library/react';

import { ActionBar } from '../../src/cockpit/ActionBar';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { SafetyRail } from '../../src/cockpit/SafetyRail';
import { useCockpitStore } from '../../src/state';
import type { SendPlanReadinessReason } from '../../src/ws/protocol';

import {
  blockedSendPlan, candidate, FakeCockpitClient, pad2RehearsalPlan,
  readyDualMachineStage, sendPlan, sessionLive, sessionMock,
} from './_fixtures';

describe('SafetyRail', () => {
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

  it('renders mock-safe defaults before a send plan is prepared', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setConnectionStatus('connected');
      useCockpitStore.getState().appendOperatorLog({
        level: 'info',
        message: 'WebSocket connected',
      });
    });

    render(<SafetyRail />);

    expect(screen.getByLabelText('Safety status')).toBeInTheDocument();
    expect(screen.getByText('Mock Safe')).toBeInTheDocument();
    expect(screen.getByText('No MIDI Port Open')).toBeInTheDocument();
    expect(screen.getByText('Hardware Off')).toBeInTheDocument();
    expect(screen.getByText('Simulation / Mock')).toBeInTheDocument();
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('Operator Log')).toBeInTheDocument();
    expect(screen.getByText('WebSocket connected')).toBeInTheDocument();
    expect(screen.getByText('No send plan prepared')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('renders live armed readiness counts when a send plan is ready', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setSendPlan(sendPlan);
    });

    render(<SafetyRail />);

    expect(screen.getByText('Live Armed')).toBeInTheDocument();
    expect(screen.getByText('IAC Driver Bus 1')).toBeInTheDocument();
    expect(screen.getByText('Hardware Armed')).toBeInTheDocument();
    expect(screen.getByText('Live Hardware')).toBeInTheDocument();
    expect(screen.getByText('Ready after prepare')).toBeInTheDocument();
    expect(screen.getAllByText(String(sendPlan.packets.length))).toHaveLength(2);
    expect(sendPlan.packets.length).toBe(sendPlan.estimated_midi_msgs);
  });

  it('renders blocked readiness when a prepared plan is not sendable', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSendPlan(blockedSendPlan);
    });

    render(<SafetyRail />);

    expect(screen.getByText('Blocked')).toBeInTheDocument();
    expect(screen.getByText(blockedSendPlan.plan_id)).toBeInTheDocument();
    expect(screen.getByRole('table')).toHaveTextContent('No packets in prepared plan.');
  });

  it.each([true, false])('shows every exact Pad 2 packet before arming when ready=%s', (ready) => {
    const fake = new FakeCockpitClient();
    const plan = {
      ...pad2RehearsalPlan,
      ready,
      readiness_reason: ready ? 'ready' as const : 'paired_control_precision_unverified' as const,
      blocked_reasons: ready ? [] : ['paired_control_precision_unverified' as const],
    };
    const passiveSession = { ...sessionLive, armed: false, midi_port: null, connection_phase: 'listening' as const };
    act(() => {
      const store = useCockpitStore.getState();
      store.setConnectionStatus('connected');
      store.setSessionStatus(passiveSession);
      store.setDualMachineStage({
        ...readyDualMachineStage,
        rytm: { ...readyDualMachineStage.rytm, target_ids: plan.target_pad_ids, locked_ids: plan.locked_pad_ids, effective_ids: [2] },
      });
      store.setPreviewCandidate(candidate);
      store.setSendPlan(plan);
    });
    const stateBeforeInspection = useCockpitStore.getState();
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <SafetyRail />
        <ActionBar previewOn onTogglePreview={() => undefined} />
      </CockpitClientProvider>,
    );
    const rail = screen.getByLabelText('Safety status');
    expect(within(rail).getByText(plan.plan_id)).toBeInTheDocument();
    const table = within(rail).getByRole('table', { name: 'Exact prepared Rytm packets' });
    expect(within(table).getAllByRole('columnheader').map((cell) => cell.textContent)).toEqual([
      'Pad', 'Parameter', 'Channel', 'CC', 'Value (7-bit)',
    ]);
    expect(within(table).getAllByRole('row').slice(1).map((row) =>
      within(row).getAllByRole('cell').map((cell) => cell.textContent),
    )).toEqual([
      ['2', 'flt', '2', '74', '72'],
      ['2', 'amp_decay', '2', '80', '0'],
      ['2', 'overdrive', '2', '81', '127'],
      ['2', 'reverb', '2', '83', '84'],
    ]);
    expect(within(rail).getByText('Hardware Off')).toBeInTheDocument();
    expect(fake.sent).toEqual([]);
    expect(useCockpitStore.getState()).toBe(stateBeforeInspection);
    expect(plan.packets.map((packet) => packet.channel)).toEqual([1, 1, 1, 1]);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    if (!ready) {
      expect(screen.getByTestId('action-send')).toBeDisabled();
      expect(within(rail).getByRole('status')).toHaveTextContent('No part of this plan will be sent.');
    } else {
      expect(screen.getByTestId('action-send')).not.toBeDisabled();
    }
  });

  it('replaces stale inspection rows and removes them when preparation is revoked', () => {
    act(() => useCockpitStore.getState().setSendPlan(pad2RehearsalPlan));
    render(<SafetyRail />);
    const nextPlan = { ...sendPlan, plan_id: 'replacement-plan' };
    act(() => useCockpitStore.getState().setSendPlan(nextPlan));
    expect(screen.queryByText(pad2RehearsalPlan.plan_id)).not.toBeInTheDocument();
    expect(screen.getByText(nextPlan.plan_id)).toBeInTheDocument();
    const table = screen.getByRole('table');
    expect(within(table).getAllByRole('row').slice(1).map((row) =>
      within(row).getAllByRole('cell').map((cell) => cell.textContent),
    )).toEqual([['1', 'tun', '1', '52', '35'], ['3', 'tun', '1', '52', '55']]);
    expect(screen.queryByText('amp_decay')).not.toBeInTheDocument();
    act(() => useCockpitStore.getState().setSendPlan(null));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.queryByText(nextPlan.plan_id)).not.toBeInTheDocument();
    expect(screen.getByText('No send plan prepared')).toBeInTheDocument();
  });

  it('explains that a paired-control refusal blocks every packet in the plan', () => {
    act(() => {
      useCockpitStore.getState().setSendPlan({
        ...sendPlan,
        ready: false,
        readiness_reason: 'paired_control_precision_unverified',
        blocked_reasons: ['paired_control_precision_unverified'],
      });
    });

    render(<SafetyRail />);

    expect(screen.getByText('Blocked')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent(
      'Paired-control precision is unverified. No part of this plan will be sent.',
    );
  });

  it.each([
    ['candidate_high_risk', 'High-risk or protected changes are blocked.'],
    ['profile_mismatch', 'The candidate belongs to another profile.'],
    ['source_snapshot_mismatch', 'The candidate belongs to another source.'],
    ['no_sendable_changes', 'No supported changes remain in the selected, unlocked pads.'],
    ['parameter_scope_mismatch', 'Parameter scope changed. Regenerate the candidate'],
    ['unsupported_control_changed', 'An unsupported or protected control changed. No part of this plan will be sent.'],
  ] as const)('explains the specific requirement for %s', (reason, message) => {
    act(() => {
      useCockpitStore.getState().setSendPlan({
        ...sendPlan,
        ready: false,
        readiness_reason: reason,
        blocked_reasons: [reason],
      });
    });
    render(<SafetyRail />);
    expect(screen.getByRole('status')).toHaveTextContent(message);
  });

  it('shows every refusal while omitting the ready sentinel', () => {
    const reasons: SendPlanReadinessReason[] = [
      'ready', 'candidate_high_risk', 'paired_control_precision_unverified',
    ];
    act(() => {
      useCockpitStore.getState().setSendPlan({ ...blockedSendPlan, blocked_reasons: reasons });
    });
    render(<SafetyRail />);
    expect(screen.getAllByRole('status')).toHaveLength(2);
    expect(screen.queryByText('Ready after prepare')).not.toBeInTheDocument();
  });
});
