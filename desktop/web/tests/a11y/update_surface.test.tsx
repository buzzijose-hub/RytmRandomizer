/**
 * Axe floor 0 + keyboard operability for the update surface (spec §7 a11y
 * clause: "axe floor 0 for panel and chip; keyboard operable; state-change
 * announcements via the announcer; no live-region countdown spam").
 */

import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { _reset as resetAnnouncer } from '../../src/a11y';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { UpdateChip } from '../../src/cockpit/HeaderBar';
import { UpdatePanel } from '../../src/cockpit/panels/UpdatePanel';
import { UPDATE_COPY } from '../../src/cockpit/panels/updatePanelSpec';
import { useCockpitStore } from '../../src/state';
import type { UpdateStateEvent } from '../../src/updateProtocol';

import { FakeCockpitClient } from '../cockpit/_fixtures';
import { runAxe, violationSummary } from './__helpers__/axe';

function state(over: Partial<UpdateStateEvent> = {}): UpdateStateEvent {
  return {
    state: 'staged',
    version: '1.35.1',
    notes: 'first note\nsecond note',
    hardware_revalidation: true,
    error_code: null,
    ...over,
  };
}

function stage(): void {
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
    useCockpitStore.getState().setUpdateState(state());
    useCockpitStore.getState().setUpdateJournal([
      { ts: '12:04', event: 'check_ok', version: '1.35.1', detail: '1.35.1 available' },
      { ts: '12:04', event: 'download_ok', version: '1.35.1', detail: '42 MB · 6 s' },
    ]);
  });
}

function renderSurface(): HTMLElement {
  const { container } = render(
    <CockpitClientProvider client={new FakeCockpitClient() as never}>
      <div>
        <header>
          <UpdateChip />
        </header>
        <main>
          <UpdatePanel />
        </main>
      </div>
    </CockpitClientProvider>,
  );
  return container;
}

beforeEach(() => {
  act(() => useCockpitStore.getState().reset());
});

afterEach(() => {
  resetAnnouncer();
});

describe('axe floor 0', () => {
  it('has zero violations in the staged consent state', async () => {
    const container = renderSurface();
    stage();
    const results = await runAxe(container);
    expect(results.violations, violationSummary(results)).toHaveLength(0);
  });

  it('has zero violations in the dev-loop (no shell) state', async () => {
    const container = renderSurface();
    const results = await runAxe(container);
    expect(results.violations, violationSummary(results)).toHaveLength(0);
  });

  it('has zero violations in the frozen state', async () => {
    const container = renderSurface();
    stage();
    act(() => useCockpitStore.getState().setUpdateFrozen(true));
    const results = await runAxe(container);
    expect(results.violations, violationSummary(results)).toHaveLength(0);
  });

  it('has zero violations in the check_failed state', async () => {
    const container = renderSurface();
    stage();
    act(() =>
      useCockpitStore
        .getState()
        .setUpdateState(state({ state: 'check_failed', error_code: 'manifest_unreachable' })),
    );
    const results = await runAxe(container);
    expect(results.violations, violationSummary(results)).toHaveLength(0);
  });
});

describe('keyboard operability + grouping', () => {
  it('groups the three radios under the §7.1 question as a real fieldset', () => {
    renderSurface();
    stage();
    const group = screen.getByRole('group', { name: UPDATE_COPY.consentQuestion });
    expect(group.tagName).toBe('FIELDSET');
    expect(within(group).getAllByRole('radio')).toHaveLength(3);
  });

  it('gives every radio an accessible name and one shared radio group name', () => {
    renderSurface();
    stage();
    const radios = screen.getAllByRole('radio') as HTMLInputElement[];
    expect(new Set(radios.map((r) => r.name))).toEqual(new Set(['update-consent']));
    for (const radio of radios) {
      expect(radio).toHaveAccessibleName();
    }
  });

  it('selects a radio by keyboard and confirms with the keyboard-reachable button', () => {
    renderSurface();
    stage();
    const skip = screen.getByTestId('update-consent-skip_this_version');
    skip.focus();
    expect(skip).toHaveFocus();
    fireEvent.click(skip);
    const confirm = screen.getByTestId('update-confirm');
    confirm.focus();
    expect(confirm).toHaveFocus();
    fireEvent.click(confirm);
    expect(useCockpitStore.getState().update.confirmedChoice).toBe('skip_this_version');
  });

  it('labels the channel select and the freeze checkbox', () => {
    renderSurface();
    stage();
    expect(screen.getByLabelText('channel:')).toBeInTheDocument();
    expect(screen.getByLabelText(UPDATE_COPY.freezeToggle)).toBeInTheDocument();
  });

  it('names the activity list so a screen reader can jump to it', () => {
    renderSurface();
    stage();
    expect(
      screen.getByRole('list', { name: UPDATE_COPY.activityHeading }),
    ).toBeInTheDocument();
  });
});

describe('no live-region countdown spam', () => {
  it('mounts no aria-live region of its own — announcements go via the announcer', () => {
    const container = renderSurface();
    stage();
    expect(container.querySelectorAll('[aria-live]')).toHaveLength(0);
    expect(container.querySelectorAll('[role="status"], [role="alert"]')).toHaveLength(0);
  });
});

describe('never colour alone', () => {
  it('pairs the chip with a glyph and the version text', () => {
    renderSurface();
    stage();
    expect(screen.getByTestId('update-chip').textContent).toBe('⬆ 1.35.1 ready');
  });

  it('pairs the status badge with an icon glyph', () => {
    renderSurface();
    stage();
    const panel = screen.getByTestId('cockpit-panel-updates');
    expect(panel.textContent).toContain('⬆');
    expect(panel.textContent).toContain('update ready');
  });
});
