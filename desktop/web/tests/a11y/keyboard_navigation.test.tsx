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
 * HistoryStrip roving tabindex — only one dot is in the tab stop at a
 * time. Arrow keys move focus through the strip; Home/End jump to ends.
 * The current snapshot drives the initial tab stop.
 */
describe('HistoryStrip roving tabindex', () => {
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

  it('only the current dot has tabindex=0; others are -1', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const dot1 = screen.getByTestId('history-dot-snap-1');
    const dot2 = screen.getByTestId('history-dot-snap-2');
    const dot3 = screen.getByTestId('history-dot-snap-3');
    expect(dot1).toHaveAttribute('tabindex', '-1');
    expect(dot2).toHaveAttribute('tabindex', '-1');
    // snap-3 is current_id in the fixture.
    expect(dot3).toHaveAttribute('tabindex', '0');
  });

  it('ArrowLeft from the current dot moves the tab stop to the previous dot', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const dot3 = screen.getByTestId('history-dot-snap-3');
    dot3.focus();
    fireEvent.keyDown(dot3, { key: 'ArrowLeft' });
    expect(screen.getByTestId('history-dot-snap-2')).toHaveAttribute('tabindex', '0');
    expect(screen.getByTestId('history-dot-snap-3')).toHaveAttribute('tabindex', '-1');
  });

  it('Home jumps the tab stop to the first dot', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const dot3 = screen.getByTestId('history-dot-snap-3');
    dot3.focus();
    fireEvent.keyDown(dot3, { key: 'Home' });
    expect(screen.getByTestId('history-dot-snap-1')).toHaveAttribute('tabindex', '0');
  });

  it('End jumps the tab stop to the last dot', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const dot1 = screen.getByTestId('history-dot-snap-1');
    // Manually focus dot1 by pressing Home from the current (snap-3) first
    // so dot1 becomes the focused index, then End advances to the last.
    const dot3 = screen.getByTestId('history-dot-snap-3');
    dot3.focus();
    fireEvent.keyDown(dot3, { key: 'Home' });
    expect(dot1).toHaveAttribute('tabindex', '0');
    fireEvent.keyDown(dot1, { key: 'End' });
    expect(screen.getByTestId('history-dot-snap-3')).toHaveAttribute('tabindex', '0');
  });

  it('Unknown key on a dot is a no-op', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const dot3 = screen.getByTestId('history-dot-snap-3');
    dot3.focus();
    fireEvent.keyDown(dot3, { key: 'Enter' });
    // Tab stops unchanged.
    expect(screen.getByTestId('history-dot-snap-3')).toHaveAttribute('tabindex', '0');
    expect(screen.getByTestId('history-dot-snap-1')).toHaveAttribute('tabindex', '-1');
  });

  it('clicking a non-current dot updates the focus index', () => {
    useCockpitStore.getState().setHistory(history);
    renderWith();
    const dot1 = screen.getByTestId('history-dot-snap-1');
    fireEvent.click(dot1);
    expect(dot1).toHaveAttribute('tabindex', '0');
  });
});
