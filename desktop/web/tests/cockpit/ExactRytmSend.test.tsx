import { act, render, renderHook, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ExactRytmSendDialog, useExactRytmSend } from '../../src/cockpit/ExactRytmSend';
import type { Command } from '../../src/ws/protocol';

import { sendPlan, sessionLive } from './_fixtures';

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
