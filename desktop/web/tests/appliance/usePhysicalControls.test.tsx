import { act, cleanup, render, renderHook, screen } from '@testing-library/react';
import { useRef } from 'react';

import { usePhysicalControls } from '../../src/appliance/usePhysicalControls';
import type { ApplianceControlIntentEvent } from '../../src/ws/protocol';

import { ApplianceFakeClient } from './fixtures';

function intent(fake: ApplianceFakeClient, action: ApplianceControlIntentEvent['action'], delta = 0): void {
  act(() => fake.emit({ type: 'appliance_control_intent', source: 'physical_input', action, delta }));
}
function rect(top = 20, height = 44, width = 44): DOMRect { return { x: 20, y: top, top, left: 20, bottom: top + height, right: 20 + width, width, height, toJSON: () => undefined }; }
function Harness({ fake, actions, dialog = false }: { fake: ApplianceFakeClient; actions: { enabled: () => boolean; mutate: () => void; undo: () => void; anchor: () => void }; dialog?: boolean }): JSX.Element {
  const root = useRef<HTMLDivElement>(null); usePhysicalControls(fake.asClient(), root, actions);
  return <div ref={root} data-root><button type="button" onClick={actions.mutate}>VISIBLE</button><button type="button" disabled>DISABLED</button><button type="button" data-tiny>TINY</button><div className="appliance-content"><button type="button" data-clipped>CLIPPED</button></div><button type="button" data-appliance-confirmation="true" onClick={actions.undo}>CONFIRM APPLY</button>{dialog && <div role="dialog"><button type="button" onClick={actions.anchor}>CANCEL</button><button type="button" data-appliance-confirmation="true" onClick={actions.undo}>CONFIRM ARM</button></div>}</div>;
}

beforeEach(() => {
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function (this: HTMLElement) {
    if (this.hasAttribute('data-root') || this.getAttribute('role') === 'dialog') return rect(0, 400, 600);
    if (this.className === 'appliance-content') return rect(0, 100, 600);
    if (this.hasAttribute('data-tiny')) return rect(20, 20, 20);
    if (this.hasAttribute('data-clipped')) return rect(300);
    return rect();
  });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe('optional physical input shares touch actions', () => {
  it('routes mutation, undo and anchor through the same enabled touch callbacks', () => {
    const fake = new ApplianceFakeClient(); const actions = { enabled: () => true, mutate: vi.fn(), undo: vi.fn(), anchor: vi.fn() }; render(<Harness fake={fake} actions={actions} />);
    intent(fake, 'mutate'); intent(fake, 'undo'); intent(fake, 'capture_anchor'); expect(actions.mutate).toHaveBeenCalledOnce(); expect(actions.undo).toHaveBeenCalledOnce(); expect(actions.anchor).toHaveBeenCalledOnce();
  });
  it('cycles only visible enabled touch targets and blocks hardware confirmations', () => {
    const fake = new ApplianceFakeClient(); const actions = { enabled: () => true, mutate: vi.fn(), undo: vi.fn(), anchor: vi.fn() }; render(<Harness fake={fake} actions={actions} />);
    intent(fake, 'focus_step', 1); expect(screen.getByRole('button', { name: 'VISIBLE' })).toHaveFocus(); intent(fake, 'activate_focus'); expect(actions.mutate).toHaveBeenCalledOnce();
    intent(fake, 'focus_step', 1); expect(screen.getByRole('button', { name: 'CONFIRM APPLY' })).toHaveFocus(); intent(fake, 'activate_focus'); expect(actions.undo).not.toHaveBeenCalled();
    intent(fake, 'focus_step', 1); expect(screen.getByRole('button', { name: 'VISIBLE' })).toHaveFocus(); intent(fake, 'focus_step', -1); expect(screen.getByRole('button', { name: 'CONFIRM APPLY' })).toHaveFocus();
    (document.activeElement as HTMLElement).blur(); intent(fake, 'focus_step', -1); expect(screen.getByRole('button', { name: 'CONFIRM APPLY' })).toHaveFocus();
    intent(fake, 'focus_step', 0); expect(screen.getByRole('button', { name: 'CONFIRM APPLY' })).toHaveFocus();
  });
  it('confines focus to an open modal and never turns encoder push into an ARM approval', () => {
    const fake = new ApplianceFakeClient(); const actions = { enabled: () => true, mutate: vi.fn(), undo: vi.fn(), anchor: vi.fn() }; render(<Harness fake={fake} actions={actions} dialog />);
    intent(fake, 'focus_step', 1); expect(screen.getByRole('button', { name: 'CANCEL' })).toHaveFocus(); intent(fake, 'focus_step', 1); intent(fake, 'activate_focus'); expect(actions.undo).not.toHaveBeenCalled();
    intent(fake, 'focus_step', -1); intent(fake, 'activate_focus'); expect(actions.anchor).toHaveBeenCalledOnce(); intent(fake, 'mutate'); expect(actions.mutate).not.toHaveBeenCalled();
  });
  it('ignores unconfigured, busy, invalid and empty-surface input', () => {
    const fake = new ApplianceFakeClient(); const actions = { enabled: () => false, mutate: vi.fn(), undo: vi.fn(), anchor: vi.fn() }; const { rerender } = render(<Harness fake={fake} actions={actions} />);
    intent(fake, 'mutate'); expect(actions.mutate).not.toHaveBeenCalled();
    act(() => fake.emit({ type: 'appliance_control_intent', source: 'unexpected', action: 'mutate', delta: 0 } as unknown as ApplianceControlIntentEvent));
    intent(fake, 'focus_step', .5); intent(fake, 'focus_step', 33);
    rerender(<Harness fake={fake} actions={{ ...actions, enabled: () => true }} />); intent(fake, 'activate_focus'); expect(actions.mutate).not.toHaveBeenCalled();
    cleanup(); renderHook(() => usePhysicalControls(fake.asClient(), { current: null }, { ...actions, enabled: () => true })); intent(fake, 'mutate'); expect(actions.mutate).not.toHaveBeenCalled();
    cleanup(); const element = document.createElement('div'); renderHook(() => usePhysicalControls(fake.asClient(), { current: element }, { ...actions, enabled: () => true })); intent(fake, 'focus_step', 1); expect(actions.mutate).not.toHaveBeenCalled();
  });
});
