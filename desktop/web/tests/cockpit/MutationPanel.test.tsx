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

import { FakeCockpitClient, availableProfiles } from './_fixtures';

function renderWith(previewOn = false): {
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
    expect(screen.getByTestId('profile-toggle')).toBeInTheDocument();
    expect(screen.getByTestId('profile-chips')).toBeInTheDocument();
    expect(screen.getByTestId('depth-slider')).toBeInTheDocument();
    expect(screen.getByTestId('action-bar')).toBeInTheDocument();
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
    const { togglePreview } = renderWith(false);
    fireEvent.click(screen.getByTestId('action-preview'));
    expect(togglePreview).toHaveBeenCalledWith(true);
  });
});
