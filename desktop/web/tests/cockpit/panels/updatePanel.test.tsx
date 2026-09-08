/**
 * UpdatePanel — the interactive shell around the §7.1 spec.
 *
 * Two things this file exists to prove, beyond rendering:
 *
 *   1. **The #238 lesson.** Mounting this panel transmits NOTHING, and no
 *      user action can transmit before the WS handshake has completed.
 *   2. **R4 reuse.** The activity list is the SHARED operator-log list
 *      component, not a second journal list.
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { emitTauriEvent, installTauriEventBridge } from '../../tauriEvent';

import { _reset as resetAnnouncer, _registerWriter } from '../../../src/a11y';
import { CockpitClientProvider } from '../../../src/cockpit/context';
import {
  UNKNOWN_VERSION,
  UpdatePanel,
  WAITING_FOR_CONNECTION,
  updateActionsAllowed,
} from '../../../src/cockpit/panels/UpdatePanel';
import { UPDATE_COPY } from '../../../src/cockpit/panels/updatePanelSpec';
import { useCockpitStore } from '../../../src/state';
import {
  UPDATE_STATE_EVENT_NAME,
  type UpdateJournalRow,
  type UpdateStateEvent,
} from '../../../src/updateProtocol';

import { FakeCockpitClient } from '../_fixtures';

function state(over: Partial<UpdateStateEvent> = {}): UpdateStateEvent {
  return {
    state: 'staged',
    version: '1.35.1',
    notes: 'Show Kit Forge: bank list no longer sends before handshake',
    hardware_revalidation: false,
    error_code: null,
    ...over,
  };
}

function row(over: Partial<UpdateJournalRow> = {}): UpdateJournalRow {
  return { ts: '12:04', event: 'check_ok', version: '1.35.1', detail: '1.35.1 available', ...over };
}

let client: FakeCockpitClient;

function mount(): void {
  render(
    <CockpitClientProvider client={client as never}>
      <UpdatePanel />
    </CockpitClientProvider>,
  );
}

function connect(): void {
  act(() => {
    useCockpitStore.getState().setConnectionStatus('connected');
    useCockpitStore.getState().setSessionStatus({
      armed: false,
      midi_port: null,
      mode: 'mock',
      connection_phase: 'listening',
      unsaved_sends: 0,
      app_version: '1.35.0',
    });
  });
}

beforeEach(() => {
  client = new FakeCockpitClient();
  act(() => useCockpitStore.getState().reset());
});

afterEach(() => {
  resetAnnouncer();
});

describe('#238 — nothing transmits on mount or before the handshake', () => {
  it('sends no command when the panel mounts', () => {
    mount();
    expect(client.sent).toEqual([]);
  });

  it('sends nothing even after the shell pushes a staged update', () => {
    mount();
    act(() => {
      useCockpitStore.getState().setUpdateState(state());
    });
    expect(client.sent).toEqual([]);
  });

  it('disables "Check now" until the WebSocket is connected, and says why', () => {
    mount();
    const check = screen.getByTestId('update-check-now');
    expect(check).toBeDisabled();
    expect(check).toHaveAttribute('title', WAITING_FOR_CONNECTION);
    fireEvent.click(check);
    expect(client.sent).toEqual([]);
    expect(screen.queryByText('Check requested.')).not.toBeInTheDocument();
  });

  it('disables "Confirm choice" until connected and refuses the click', () => {
    mount();
    act(() => useCockpitStore.getState().setUpdateState(state()));
    const confirm = screen.getByTestId('update-confirm');
    expect(confirm).toBeDisabled();
    fireEvent.click(confirm);
    expect(useCockpitStore.getState().update.confirmedChoice).toBeNull();
  });

  it('gates every action on an established connection (the named predicate)', () => {
    // `disabled` is an affordance, not a guarantee — the handlers consult
    // this predicate too, so a refactor that drops the attribute cannot
    // silently re-open the pre-handshake transmit path.
    expect(updateActionsAllowed('connected')).toBe(true);
    for (const status of ['closed', 'connecting', 'reconnecting'] as const) {
      expect(updateActionsAllowed(status)).toBe(false);
    }
  });

  it('enables the controls once connected', () => {
    mount();
    connect();
    expect(screen.getByTestId('update-check-now')).toBeEnabled();
    fireEvent.click(screen.getByTestId('update-check-now'));
    expect(screen.getByText('Check requested.')).toBeInTheDocument();
    // Still no command on the wire: the shell owns the check, not the panel.
    expect(client.sent).toEqual([]);
  });
});

describe('shell event subscription (receive-only)', () => {
  beforeEach(() => {
    installTauriEventBridge();
  });

  // These assert the TAURI IPC transport, not a DOM event. The original pair
  // dispatched a CustomEvent on `window` and passed — while the shell emitted
  // over IPC, so the panel could never have received a real message. A test
  // that asserts a mechanism the producer does not use is how that shipped.
  it('applies a well-formed payload delivered over the shell IPC channel', async () => {
    mount();
    // subscribeUpdateState registers through a dynamic import, so the listener
    // is not live on mount's tick. Let it settle rather than racing it.
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    await act(async () => {
      await emitTauriEvent(UPDATE_STATE_EVENT_NAME, state({ version: '2.0.0' }));
    });
    expect(useCockpitStore.getState().update.state?.version).toBe('2.0.0');
  });

  it('ignores an unrecognised payload rather than crashing the panel', async () => {
    mount();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    await act(async () => {
      await emitTauriEvent(UPDATE_STATE_EVENT_NAME, { state: 'bogus' });
    });
    expect(useCockpitStore.getState().update.state).toBeNull();
    expect(screen.getByTestId('update-panel')).toBeInTheDocument();
  });
});

describe('§7.1 rendering', () => {
  it('renders the running version from session_status.app_version (I1)', () => {
    mount();
    connect();
    expect(screen.getByText('Running v1.35.0 · channel: stable')).toBeInTheDocument();
  });

  it('says "unknown" rather than inventing a version', () => {
    mount();
    expect(screen.getByText(`Running v${UNKNOWN_VERSION} · channel: stable`)).toBeInTheDocument();
  });

  it('renders the staged block, notes, radios in order, and the default selection', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));

    expect(screen.getByText('⬆ Update ready: v1.35.1')).toBeInTheDocument();
    expect(screen.getByText("What's new")).toBeInTheDocument();
    expect(
      screen.getByText('Show Kit Forge: bank list no longer sends before handshake'),
    ).toBeInTheDocument();

    const group = screen.getByTestId('update-consent');
    expect(within(group).getByText(UPDATE_COPY.consentQuestion)).toBeInTheDocument();
    const radios = within(group).getAllByRole('radio');
    expect(radios.map((r) => (r as HTMLInputElement).value)).toEqual([
      'install_on_quit',
      'install_now',
      'skip_this_version',
    ]);
    expect(screen.getByTestId('update-consent-install_on_quit')).toBeChecked();
    expect(screen.getByLabelText('When I quit the app')).toBeInTheDocument();
    expect(screen.getByLabelText('Now — restart RytmRandomizer immediately')).toBeInTheDocument();
    expect(screen.getByLabelText('Skip this version')).toBeInTheDocument();
  });

  it('shows the hardware-revalidation warning ONLY when I2 flags it', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));
    expect(screen.queryByText(`→ ${UPDATE_COPY.hardwareDoc}`)).not.toBeInTheDocument();

    act(() =>
      useCockpitStore.getState().setUpdateState(state({ hardware_revalidation: true })),
    );
    expect(screen.getByText(`⚠ ${UPDATE_COPY.hardwareWarning}`)).toBeInTheDocument();
    expect(screen.getByText(`→ ${UPDATE_COPY.hardwareDoc}`)).toBeInTheDocument();
  });

  it('hides the consent block outside the staged state', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state({ state: 'up_to_date' })));
    expect(screen.queryByTestId('update-consent')).not.toBeInTheDocument();
    expect(
      screen.getByText("You're on the latest version (v1.35.0). Next automatic check in about 4 hours."),
    ).toBeInTheDocument();
  });

  it('renders the check_failed body with the reason code verbatim', () => {
    mount();
    connect();
    act(() =>
      useCockpitStore
        .getState()
        .setUpdateState(state({ state: 'check_failed', error_code: 'manifest_unreachable' })),
    );
    expect(
      screen.getByText("Couldn't check for updates (manifest_unreachable). Will retry automatically."),
    ).toBeInTheDocument();
  });

  it('renders the dev-loop sentence, not a broken control, with no shell', () => {
    mount();
    connect();
    expect(screen.getByText(UPDATE_COPY.devLoopBody)).toBeInTheDocument();
  });
});

describe('freeze toggle', () => {
  it('replaces the body and suppresses the consent block', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));
    fireEvent.click(screen.getByTestId('update-freeze'));
    expect(useCockpitStore.getState().update.frozen).toBe(true);
    expect(screen.getByText(UPDATE_COPY.frozenBody)).toBeInTheDocument();
    expect(screen.queryByTestId('update-consent')).not.toBeInTheDocument();
  });

  it('unfreezes back to the staged body', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));
    fireEvent.click(screen.getByTestId('update-freeze'));
    fireEvent.click(screen.getByTestId('update-freeze'));
    expect(useCockpitStore.getState().update.frozen).toBe(false);
    expect(screen.getByTestId('update-consent')).toBeInTheDocument();
  });

  it('is labelled with the §7.1 copy', () => {
    mount();
    expect(screen.getByLabelText(UPDATE_COPY.freezeToggle)).toBeInTheDocument();
  });
});

describe('channel selector', () => {
  it('writes the operator selection into the slice and the running line', () => {
    mount();
    connect();
    fireEvent.change(screen.getByTestId('update-channel'), { target: { value: 'beta' } });
    expect(useCockpitStore.getState().update.channel).toBe('beta');
    expect(screen.getByText('Running v1.35.0 · channel: beta')).toBeInTheDocument();
  });

  it('offers exactly the two channels and is labelled', () => {
    mount();
    const select = screen.getByLabelText('channel:');
    expect(within(select).getAllByRole('option').map((o) => o.textContent)).toEqual([
      'stable',
      'beta',
    ]);
  });
});

describe('consent confirmation', () => {
  it('surfaces a shell rejection instead of swallowing it', async () => {
    // A rejection means the two ends disagree on the choice vocabulary — the
    // shell refuses an unrecognised value rather than defaulting, precisely so
    // a drift shows up. Swallowing it would leave the operator believing a
    // choice was recorded that never reached the driver.
    const protocol = await import('../../../src/updateProtocol');
    const spy = vi
      .spyOn(protocol, 'confirmUpdateChoiceOnShell')
      .mockResolvedValue(false);

    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));

    fireEvent.click(screen.getByTestId('update-confirm'));
    await act(async () => {
      await Promise.resolve();
    });

    expect(spy).toHaveBeenCalled();
    expect(screen.getByText('The shell did not accept that choice.')).toBeInTheDocument();
    spy.mockRestore();
  });

  it('records the chosen option, announces once, and notes it in the panel', () => {
    const announced: string[] = [];
    _registerWriter((message) => announced.push(message));
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));

    fireEvent.click(screen.getByTestId('update-consent-install_now'));
    fireEvent.click(screen.getByTestId('update-confirm'));

    expect(useCockpitStore.getState().update.confirmedChoice).toBe('install_now');
    expect(
      screen.getByText('Choice recorded: Now — restart RytmRandomizer immediately'),
    ).toBeInTheDocument();
    // Confirming clears the consent block: the question has been answered.
    expect(screen.queryByTestId('update-consent')).not.toBeInTheDocument();
  });

  it('defaults to install_on_quit when the operator just presses Confirm', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));
    fireEvent.click(screen.getByTestId('update-confirm'));
    expect(useCockpitStore.getState().update.confirmedChoice).toBe('install_on_quit');
  });

  it('records skip_this_version like any other choice', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateState(state()));
    fireEvent.click(screen.getByTestId('update-consent-skip_this_version'));
    fireEvent.click(screen.getByTestId('update-confirm'));
    expect(useCockpitStore.getState().update.confirmedChoice).toBe('skip_this_version');
  });
});

describe('Recent update activity — the SHARED operator-log list (R4)', () => {
  it('renders the journal tail newest-first through the shared list', () => {
    mount();
    connect();
    act(() =>
      useCockpitStore
        .getState()
        .setUpdateJournal([
          row({ ts: '12:03', event: 'check_started', detail: '' }),
          row({ ts: '12:04', event: 'check_ok', detail: '1.35.1 available' }),
          row({ ts: '12:04', event: 'download_ok', detail: '42 MB · 6 s' }),
        ]),
    );
    const list = screen.getByTestId('update-activity-list');
    expect(list.tagName).toBe('OL');
    expect(list).toHaveClass('operator-log-list');
    const items = within(list).getAllByRole('listitem').map((li) => li.textContent);
    expect(items).toEqual([
      '12:04  download_ok  42 MB · 6 s',
      '12:04  check_ok  1.35.1 available',
      '12:03  check_started',
    ]);
    expect(within(list).getAllByRole('listitem')[0]).toHaveClass('operator-log-entry', 'success');
  });

  it('shows honest empty copy rather than an empty box', () => {
    mount();
    expect(screen.getByText(UPDATE_COPY.activityEmpty)).toBeInTheDocument();
    expect(screen.queryByTestId('update-activity-list')).not.toBeInTheDocument();
  });

  it('renders the heading and the phone-home honesty line', () => {
    mount();
    connect();
    act(() => useCockpitStore.getState().setUpdateJournal([row({ ts: '12:04', event: 'ping_ok' })]));
    expect(screen.getByText(UPDATE_COPY.activityHeading)).toBeInTheDocument();
    expect(screen.getByText('Last checked never · Last check-in ping 12:04')).toBeInTheDocument();
  });
});
