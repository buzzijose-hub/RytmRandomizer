/**
 * The header update chip (spec §7 / the §7.1 header mockup).
 *
 * Contract: `⬆ 1.35.1 ready` — icon + shape + text, never colour alone;
 * visible only while an update is staged and unfrozen; announced exactly
 * ONCE per staged version so the polite live region never becomes a ticker;
 * and motionless (no animation, no countdown).
 */

import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _registerWriter, _reset as resetAnnouncer } from '../../src/a11y';
import { UpdateChip } from '../../src/cockpit/HeaderBar';
import { useCockpitStore } from '../../src/state';
import type { UpdateStateEvent } from '../../src/updateProtocol';

function state(over: Partial<UpdateStateEvent> = {}): UpdateStateEvent {
  return {
    state: 'staged',
    version: '1.35.1',
    notes: '',
    hardware_revalidation: false,
    error_code: null,
    ...over,
  };
}

let announced: string[];

beforeEach(() => {
  vi.useFakeTimers();
  announced = [];
  act(() => useCockpitStore.getState().reset());
  _registerWriter((message) => announced.push(message));
});

afterEach(() => {
  vi.runOnlyPendingTimers();
  vi.useRealTimers();
  resetAnnouncer();
});

function flushAnnouncer(): void {
  act(() => {
    vi.advanceTimersByTime(250);
  });
}

describe('visibility', () => {
  it('renders nothing before the shell has spoken', () => {
    render(<UpdateChip />);
    expect(screen.queryByTestId('update-chip')).not.toBeInTheDocument();
  });

  it('renders icon + text when an update is staged', () => {
    render(<UpdateChip />);
    act(() => useCockpitStore.getState().setUpdateState(state()));
    expect(screen.getByTestId('update-chip')).toHaveTextContent('⬆ 1.35.1 ready');
  });

  it('is hidden in freeze mode', () => {
    render(<UpdateChip />);
    act(() => {
      useCockpitStore.getState().setUpdateState(state());
      useCockpitStore.getState().setUpdateFrozen(true);
    });
    expect(screen.queryByTestId('update-chip')).not.toBeInTheDocument();
  });

  it('is hidden for every non-staged state', () => {
    render(<UpdateChip />);
    for (const s of ['idle', 'checking', 'up_to_date', 'check_failed', 'downloading'] as const) {
      act(() => useCockpitStore.getState().setUpdateState(state({ state: s })));
      expect(screen.queryByTestId('update-chip')).not.toBeInTheDocument();
    }
  });

  it('disappears once the operator has confirmed a choice', () => {
    render(<UpdateChip />);
    act(() => useCockpitStore.getState().setUpdateState(state()));
    act(() => useCockpitStore.getState().confirmUpdateChoice('install_on_quit'));
    expect(screen.queryByTestId('update-chip')).not.toBeInTheDocument();
  });
});

describe('announcement discipline', () => {
  it('announces exactly once for a staged version', () => {
    render(<UpdateChip />);
    act(() => useCockpitStore.getState().setUpdateState(state()));
    flushAnnouncer();
    expect(announced).toEqual(['Update 1.35.1 ready to install']);
  });

  it('does not re-announce when the same version is re-reported', () => {
    render(<UpdateChip />);
    act(() => useCockpitStore.getState().setUpdateState(state()));
    flushAnnouncer();
    act(() => useCockpitStore.getState().setUpdateState(state({ notes: 'refreshed' })));
    flushAnnouncer();
    expect(announced).toEqual(['Update 1.35.1 ready to install']);
  });

  it('announces again for a genuinely newer staged version', () => {
    render(<UpdateChip />);
    act(() => useCockpitStore.getState().setUpdateState(state()));
    flushAnnouncer();
    act(() => useCockpitStore.getState().setUpdateState(state({ version: '1.36.0' })));
    flushAnnouncer();
    expect(announced).toEqual([
      'Update 1.35.1 ready to install',
      'Update 1.36.0 ready to install',
    ]);
  });

  it('re-arms after the chip goes away, so the next stage announces', () => {
    render(<UpdateChip />);
    act(() => useCockpitStore.getState().setUpdateState(state()));
    flushAnnouncer();
    act(() => useCockpitStore.getState().setUpdateState(state({ state: 'up_to_date' })));
    flushAnnouncer();
    act(() => useCockpitStore.getState().setUpdateState(state()));
    flushAnnouncer();
    expect(announced).toEqual([
      'Update 1.35.1 ready to install',
      'Update 1.35.1 ready to install',
    ]);
  });

  it('says nothing at all while frozen', () => {
    render(<UpdateChip />);
    act(() => {
      useCockpitStore.getState().setUpdateFrozen(true);
      useCockpitStore.getState().setUpdateState(state());
    });
    flushAnnouncer();
    expect(announced).toEqual([]);
  });
});
