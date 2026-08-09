/**
 * Tests for MutationPanel — wires ProfileToggle, ProfileChips, DepthSlider, ActionBar.
 *
 * We don't re-test the children's internals — just the wiring (filter by kind, propagation
 * of previewOn/onTogglePreview).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { MutationPanel } from '../../src/cockpit/MutationPanel';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, availableProfiles, sessionMock } from './_fixtures';

function renderWith(
  previewOn = false,
  onLaunchWizard?: () => void,
): {
  fake: FakeCockpitClient;
  togglePreview: ReturnType<typeof vi.fn>;
} {
  const fake = new FakeCockpitClient();
  const togglePreview = vi.fn();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <MutationPanel
        availableProfiles={availableProfiles}
        previewOn={previewOn}
        onTogglePreview={togglePreview}
        {...(onLaunchWizard === undefined ? {} : { onLaunchWizard })}
      />
    </CockpitClientProvider>,
  );
  return { fake, togglePreview };
}

describe('MutationPanel', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
  });
  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  it('renders the panel scaffolding with the four child sections', () => {
    renderWith();
    expect(screen.getByTestId('mutation-panel')).toBeInTheDocument();
    expect(screen.getByTestId('style-crate-queue')).toBeInTheDocument();
    expect(screen.getByTestId('profile-toggle')).toBeInTheDocument();
    expect(screen.getByTestId('profile-chips')).toBeInTheDocument();
    expect(screen.getByTestId('depth-slider')).toBeInTheDocument();
    expect(screen.getByTestId('action-bar')).toBeInTheDocument();
  });

  it('renders passive style crates and the staged performance queue', () => {
    renderWith();

    expect(screen.getByTestId('style-crate-hard-groove')).toHaveTextContent('Hard Groove');
    expect(screen.getByTestId('style-crate-dark-hypnotic')).toHaveTextContent('Dark Hypnotic');
    expect(screen.getByTestId('style-crate-industrial-warehouse')).toHaveTextContent(
      'Industrial Warehouse',
    );
    expect(screen.getByTestId('style-queue-current')).toHaveTextContent('Dark Hypnotic');
    expect(screen.getByTestId('style-queue-next-0')).toHaveTextContent('Hard Groove');
    expect(screen.getByTestId('style-queue-next-1')).toHaveTextContent('Industrial Warehouse');
    expect(screen.getByTestId('style-crate-summary')).toHaveTextContent(
      '3 staged moves cover 14 target pad slots and 2 journal seeds.',
    );
    expect(screen.getByTestId('style-crate-safety')).toHaveTextContent(
      'Passive queue preview only',
    );
  });

  it('updates the selected crate detail without dispatching hardware actions', () => {
    const { fake } = renderWith();

    fireEvent.click(screen.getByTestId('style-crate-dub-pressure'));

    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('Dub Pressure');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('Space and low-end');
    expect(fake.sent).toHaveLength(0);
  });

  it('initially shows only "scene" profiles in the chip list', () => {
    renderWith();
    expect(screen.getByTestId('profile-chip-scene-industrial')).toBeInTheDocument();
    expect(screen.getByTestId('profile-chip-scene-warehouse')).toBeInTheDocument();
    expect(screen.queryByTestId('profile-chip-user-buzzi')).not.toBeInTheDocument();
  });

  it('switching the toggle to Inspiration filters to user profiles', () => {
    renderWith();
    fireEvent.click(screen.getByRole('tab', { name: 'Inspiration' }));
    expect(screen.getByTestId('profile-chip-user-buzzi')).toBeInTheDocument();
    expect(screen.queryByTestId('profile-chip-scene-industrial')).not.toBeInTheDocument();
  });

  it('forwards previewOn to the ActionBar (PREVIEW reflects state)', () => {
    renderWith(true);
    expect(screen.getByTestId('action-preview')).toHaveTextContent('PREVIEW (on)');
  });

  it('forwards onTogglePreview to the ActionBar', () => {
    // PREVIEW is disabled while no session ever arrived, so seed one.
    useCockpitStore.getState().setSessionStatus(sessionMock);
    const { togglePreview } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(togglePreview).toHaveBeenCalledWith(true);
  });

  it('renders the wizard launcher and invokes the injected onLaunchWizard handler', () => {
    const onLaunchWizard = vi.fn();
    renderWith(false, onLaunchWizard);
    fireEvent.click(screen.getByTestId('mutation-panel-launch-wizard'));
    expect(onLaunchWizard).toHaveBeenCalledTimes(1);
  });

  it('wizard launcher falls back to setting window.location.hash when no handler is provided', () => {
    renderWith();
    const originalHash = window.location.hash;
    fireEvent.click(screen.getByTestId('mutation-panel-launch-wizard'));
    expect(window.location.hash).toBe('#/wizard');
    window.location.hash = originalHash;
  });
});
