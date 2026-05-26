/**
 * Tests for ProfileChips — chip list, active card, export button.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { ProfileChips } from '../../src/cockpit/ProfileChips';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, availableProfiles, profile } from './_fixtures';

function renderWith(
  available: ReadonlyArray<{ profile_id: string; name: string; kind: 'scene' | 'user' }> = availableProfiles,
): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <ProfileChips available={available} />
    </CockpitClientProvider>,
  );
  return fake;
}

describe('ProfileChips', () => {
  beforeEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });
  afterEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('renders an empty-state message when available is empty', () => {
    renderWith([]);
    expect(screen.getByText('No profiles available')).toBeInTheDocument();
  });

  it('renders one chip per available profile', () => {
    renderWith();
    for (const p of availableProfiles) {
      expect(screen.getByTestId(`profile-chip-${p.profile_id}`)).toBeInTheDocument();
    }
  });

  it('highlights the active chip when its id matches the store profile', () => {
    act(() => {
      useCockpitStore.getState().setProfile(profile);
    });
    renderWith();
    const activeChip = screen.getByTestId(`profile-chip-${profile.profile_id}`);
    expect(activeChip.className).toBe('profile-chip active');
    expect(activeChip).toHaveTextContent('★ buzzi');
  });

  it('does not render the active card when no profile is selected', () => {
    renderWith();
    expect(screen.queryByTestId('profile-active-card')).not.toBeInTheDocument();
  });

  it('renders the active card with name + traits + meta when a profile is selected', () => {
    act(() => {
      useCockpitStore.getState().setProfile(profile);
    });
    renderWith();
    const card = screen.getByTestId('profile-active-card');
    expect(card).toHaveTextContent('★ buzzi');
    expect(card).toHaveTextContent('model 1.2.0');
    expect(card).toHaveTextContent('rolling_low_end');
    expect(card).toHaveTextContent('85%');
    expect(card).toHaveTextContent('metallic_tension');
    expect(card).toHaveTextContent('40%');
  });

  it('clicking a chip emits select_profile', () => {
    const fake = renderWith();
    fireEvent.click(screen.getByTestId('profile-chip-user-buzzi'));
    expect(fake.sent).toEqual([{ type: 'select_profile', profile_id: 'user-buzzi' }]);
  });

  it('clicking EXPORT MODEL emits export_profile_model with target=binary', async () => {
    act(() => {
      useCockpitStore.getState().setProfile(profile);
    });
    const fake = renderWith();
    fireEvent.click(screen.getByTestId('profile-export-button'));
    expect(fake.sent).toEqual([
      {
        type: 'export_profile_model',
        profile_id: profile.profile_id,
        target: 'binary',
      },
    ]);
    expect(await screen.findByText(/Export ready/)).toBeInTheDocument();
  });

  it('shows a visible export success message when the sidecar returns model bytes', async () => {
    act(() => {
      useCockpitStore.getState().setProfile(profile);
    });
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-ok',
      ok: true,
      model_bytes_b64: 'cnltcA==',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    expect(await screen.findByText(/Export ready/)).toBeInTheDocument();
    expect(screen.getByText(/4 bytes/)).toBeInTheDocument();
  });
});
