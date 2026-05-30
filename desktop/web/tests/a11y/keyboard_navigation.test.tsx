/**
 * Keyboard navigation flows for tablist + roving-tabindex widgets.
 * Cluster 1 coverage.
 *
 * Uses fireEvent rather than @testing-library/user-event because the
 * latter isn't a project dependency. fireEvent dispatches the same
 * KeyboardEvent that React's synthetic event system reads, so the
 * onKeyDown handler is exercised identically — only the typing
 * affordances differ.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { HistoryStrip } from '../../src/cockpit/HistoryStrip';
import { ProfileToggle } from '../../src/cockpit/ProfileToggle';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, history } from '../cockpit/_fixtures';

describe('ProfileToggle roving tabindex', () => {
  it('only the selected tab is in the tab order', () => {
    render(<ProfileToggle value="scene" onChange={() => {}} />);
    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(2);
    expect(tabs[0]).toHaveAttribute('tabindex', '0');
    expect(tabs[1]).toHaveAttribute('tabindex', '-1');
  });

  it('ArrowRight moves selection + focus to next tab', () => {
    const onChange = vi.fn();
    render(<ProfileToggle value="scene" onChange={onChange} />);
    const sceneTab = screen.getAllByRole('tab')[0]!;
    sceneTab.focus();
    fireEvent.keyDown(sceneTab, { key: 'ArrowRight' });
    expect(onChange).toHaveBeenCalledWith('user');
  });

  it('Home jumps to first tab', () => {
    const onChange = vi.fn();
    render(<ProfileToggle value="user" onChange={onChange} />);
    const userTab = screen.getAllByRole('tab')[1]!;
    userTab.focus();
    fireEvent.keyDown(userTab, { key: 'Home' });
    expect(onChange).toHaveBeenCalledWith('scene');
  });

  it('End jumps to last tab', () => {
    const onChange = vi.fn();
    render(<ProfileToggle value="scene" onChange={onChange} />);
    const sceneTab = screen.getAllByRole('tab')[0]!;
    sceneTab.focus();
    fireEvent.keyDown(sceneTab, { key: 'End' });
    expect(onChange).toHaveBeenCalledWith('user');
  });

  it('Unknown key does nothing (covers handleKeyDown early-return branch)', () => {
    const onChange = vi.fn();
    render(<ProfileToggle value="scene" onChange={onChange} />);
    const sceneTab = screen.getAllByRole('tab')[0]!;
    sceneTab.focus();
    fireEvent.keyDown(sceneTab, { key: ' ' });
    expect(onChange).not.toHaveBeenCalled();
  });
});

/**
 * Covers the defensive `targetKind === undefined` guard branch in
 * ProfileToggle. The branch is unreachable through the real `nextIndex`
 * (which wraps modulo length) — we mock the helper to return an
 * out-of-bounds index so the guard's truthy path executes.
 */
describe('ProfileToggle defensive out-of-bounds guard', () => {
  beforeEach(() => {
    vi.resetModules();
  });
  afterEach(() => {
    vi.doUnmock('../../src/a11y');
    vi.resetModules();
  });

  it('does not call onChange when nextIndex returns an out-of-bounds index', async () => {
    vi.doMock('../../src/a11y', () => ({
      // Return an index past the last TAB_ORDER entry so TAB_ORDER[next]
      // is undefined; the guard short-circuits without calling onChange.
      nextIndex: vi.fn((_current: number, _length: number, _key: string) => 99),
    }));
    const { ProfileToggle: PT } = await import('../../src/cockpit/ProfileToggle');
    const onChange = vi.fn();
    render(<PT value="scene" onChange={onChange} />);
    const sceneTab = screen.getAllByRole('tab')[0]!;
    sceneTab.focus();
    fireEvent.keyDown(sceneTab, { key: 'ArrowRight' });
    expect(onChange).not.toHaveBeenCalled();
  });
});

/**
 * HistoryStrip now exposes an expandable recall list. Each snapshot has a
 * normal Load button, so keyboard access follows native button/tab behavior
 * instead of the old dot-strip roving-tabindex pattern.
 */
describe('HistoryStrip expandable recall list', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
  });
  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  function renderWith(): FakeCockpitClient {
    const fake = new FakeCockpitClient();
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <HistoryStrip />
      </CockpitClientProvider>,
    );
    return fake;
  }

  it('renders snapshot rows with the current marker', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    expect(screen.getByTestId('history-row-snap-1')).toHaveTextContent('snap-1');
    expect(screen.getByTestId('history-row-snap-2')).toHaveTextContent('auto');
    expect(screen.getByTestId('history-row-snap-3')).toHaveTextContent('current');
  });

  it('exposes one load button per snapshot with accessible names', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const buttons = screen.getAllByRole('button', { name: /Load snapshot/i });
    expect(buttons).toHaveLength(3);
    expect(screen.getByRole('button', { name: 'Load snapshot snap-1' })).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Load snapshot industrial-peak' }),
    ).toBeInTheDocument();
  });

  it('clicking a load button emits load_snapshot for that snapshot', () => {
    useCockpitStore.getState().setHistory(history);
    const fake = renderWith();
    fireEvent.click(screen.getByRole('button', { name: 'Load snapshot snap-2' }));
    expect(fake.sent).toEqual([{ type: 'load_snapshot', snapshot_id: 'snap-2' }]);
  });

  it('leaves the recall list open by default for keyboard scanning', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    expect(screen.getByTestId('history-strip')).toHaveAttribute('open');
  });
});
