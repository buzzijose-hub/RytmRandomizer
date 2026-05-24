/**
 * Tests for ActionBar — PREVIEW toggle, REGEN, SEND (disabled paths), UNDO (disabled paths), SAVE.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { ActionBar } from '../../src/cockpit/ActionBar';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, candidate, highRiskCandidate, history } from './_fixtures';

interface Harness {
  fake: FakeCockpitClient;
  toggle: ReturnType<typeof vi.fn>;
}

function renderWith(previewOn: boolean): Harness {
  const fake = new FakeCockpitClient();
  const toggle = vi.fn();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <ActionBar previewOn={previewOn} onTogglePreview={toggle} />
    </CockpitClientProvider>,
  );
  return { fake, toggle };
}

describe('ActionBar', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
  });
  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  it('preview button shows "(off)" label and aria-pressed=false when previewOn=false', () => {
    renderWith(false);
    const btn = screen.getByTestId('action-preview');
    expect(btn).toHaveTextContent('PREVIEW (off)');
    expect(btn).toHaveAttribute('aria-pressed', 'false');
    expect(btn.className).toBe('action-button toggle');
  });

  it('preview button shows "(on)" label and the on class when previewOn=true', () => {
    renderWith(true);
    const btn = screen.getByTestId('action-preview');
    expect(btn).toHaveTextContent('PREVIEW (on)');
    expect(btn).toHaveAttribute('aria-pressed', 'true');
    expect(btn.className).toBe('action-button toggle on');
  });

  it('clicking PREVIEW calls onTogglePreview(true) and emits toggle_preview {on: true} when off', () => {
    const { fake, toggle } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(toggle).toHaveBeenCalledWith(true);
    expect(fake.sent).toEqual([{ type: 'toggle_preview', on: true }]);
  });

  it('clicking PREVIEW when on emits toggle_preview {on: false}', () => {
    const { fake, toggle } = renderWith(true);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(toggle).toHaveBeenCalledWith(false);
    expect(fake.sent).toEqual([{ type: 'toggle_preview', on: false }]);
  });

  it('REGEN emits regen', () => {
    const { fake } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-regen'));
    expect(fake.sent).toEqual([{ type: 'regen' }]);
  });

  it('SEND is disabled when there is no candidate', () => {
    const { fake } = renderWith(false);
    const send = screen.getByTestId('action-send');
    expect(send).toBeDisabled();
    fireEvent.click(send);
    expect(fake.sent).toEqual([]);
  });

  it('SEND is disabled and unclickable when candidate is high_risk', () => {
    useCockpitStore.getState().setPreviewCandidate(highRiskCandidate);
    const { fake } = renderWith(true);
    const send = screen.getByTestId('action-send');
    expect(send).toBeDisabled();
    fireEvent.click(send);
    expect(fake.sent).toEqual([]);
  });

  it('SEND enabled with safe candidate, shows pad count, and emits send', () => {
    useCockpitStore.getState().setPreviewCandidate(candidate);
    const { fake } = renderWith(true);
    const send = screen.getByTestId('action-send');
    expect(send).not.toBeDisabled();
    expect(send).toHaveTextContent('SEND ▶ (2 pads)');
    fireEvent.click(send);
    expect(fake.sent).toEqual([{ type: 'send' }]);
  });

  it('SEND shows singular "1 pad" when exactly one delta is present', () => {
    useCockpitStore
      .getState()
      .setPreviewCandidate({ ...candidate, pad_deltas: [candidate.pad_deltas[0]!] });
    renderWith(true);
    expect(screen.getByTestId('action-send')).toHaveTextContent('SEND ▶ (1 pad)');
  });

  it('SEND omits the pad-count chip when candidate has zero deltas', () => {
    useCockpitStore.getState().setPreviewCandidate({ ...candidate, pad_deltas: [] });
    renderWith(true);
    expect(screen.getByTestId('action-send')).toHaveTextContent('SEND ▶');
    expect(screen.getByTestId('action-send').textContent).not.toMatch(/\(\d/);
  });

  it('UNDO is disabled when canUndo=false (no history)', () => {
    renderWith(false);
    const undo = screen.getByTestId('action-undo');
    expect(undo).toBeDisabled();
  });

  it('UNDO is enabled and emits undo when canUndo=true', () => {
    useCockpitStore.getState().setHistory(history);
    const { fake } = renderWith(false);
    const undo = screen.getByTestId('action-undo');
    expect(undo).not.toBeDisabled();
    fireEvent.click(undo);
    expect(fake.sent).toEqual([{ type: 'undo' }]);
  });

  it('SAVE emits save (no label arg)', () => {
    const { fake } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-save'));
    expect(fake.sent).toEqual([{ type: 'save' }]);
  });
});
