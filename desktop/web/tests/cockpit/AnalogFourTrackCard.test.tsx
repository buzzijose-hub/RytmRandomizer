import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AnalogFourTrackCard } from '../../src/cockpit/AnalogFourTrackCard';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { ANALOG_FOUR_TRACKS } from '../../src/cockpit/devices';

import { FakeCockpitClient } from './_fixtures';

function renderCard(previewOn: boolean): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <AnalogFourTrackCard track={ANALOG_FOUR_TRACKS[0]!} previewOn={previewOn} />
    </CockpitClientProvider>,
  );
  return fake;
}

describe('AnalogFourTrackCard', () => {
  it('shows preview rows for CC-ready zones and deferred rows for NRPN-only zones', () => {
    renderCard(true);

    const oscillator = screen.getByTestId('a4-track-1-zone-oscillator');
    const drive = screen.getByTestId('a4-track-1-zone-drive');

    expect(oscillator).toHaveTextContent('Preview row');
    expect(oscillator).toHaveTextContent('OSC1 Level');
    expect(drive).toHaveTextContent('Deferred');
    expect(drive).toHaveTextContent('NRPN-only / deferred');
  });

  it('shows dry-run rows when preview is off and can lock the A4 track locally', () => {
    const fake = renderCard(false);
    const card = screen.getByTestId('a4-track-card-1');

    expect(within(card).getByTestId('a4-track-1-zone-oscillator')).toHaveTextContent(
      'Dry-run row',
    );
    expect(card).not.toHaveClass('locked');

    fireEvent.click(screen.getByRole('button', { name: 'Lock pad 1' }));

    expect(fake.sent).toEqual([{ type: 'set_pad_lock', pad_id: 1, locked: true }]);
    expect(card).toHaveClass('locked');
    expect(screen.getByRole('button', { name: 'Unlock pad 1' })).toBeInTheDocument();
  });

  it('exposes the role key as a data-role-key attribute for diagnostics + locks it against the devices.ts source of truth', () => {
    renderCard(true);
    const card = screen.getByTestId('a4-track-card-1');
    // Asserting the exact value rather than just "non-empty" so a swap between
    // roleKey and roleLabel in devices.ts is caught.
    expect(card).toHaveAttribute('data-role-key', ANALOG_FOUR_TRACKS[0]!.roleKey);
    expect(card).toHaveAttribute('data-role-key', 'bass_foundation');
  });

  it('gives the safe-depth meter an accessible name and value-text for screen readers', () => {
    renderCard(true);
    const meter = screen.getByRole('meter');
    expect(meter).toHaveAccessibleName('Safe Depth');
    expect(meter).toHaveAttribute(
      'aria-valuetext',
      expect.stringContaining('safe mutation depth'),
    );
    expect(meter).toHaveAttribute(
      'aria-valuetext',
      expect.stringContaining(ANALOG_FOUR_TRACKS[0]!.trackLabel),
    );
  });
});
