import { act, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DeviceRail } from '../../src/cockpit/DeviceRail';
import { useCockpitStore } from '../../src/state';

import { sessionMock, snapshot } from './_fixtures';

describe('DeviceRail', () => {
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

  it('renders the full Rytm 12-pad surface and staged Analog Four track plan', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    render(<DeviceRail />);

    const rail = screen.getByTestId('device-rail');
    const rytm = within(rail).getByTestId('device-card-analog-rytm-mk2');
    const analogFour = within(rail).getByTestId('device-card-analog-four-mk2');

    expect(rytm).toHaveTextContent('Analog Rytm MKII');
    expect(rytm).toHaveTextContent('12 pads mapped');
    expect(within(rytm).getAllByTestId(/device-rail-rytm-pad-/)).toHaveLength(12);
    expect(within(rytm).getByTestId('device-rail-rytm-pad-12')).toHaveTextContent(
      'BD Acoustic',
    );

    expect(analogFour).toHaveTextContent('Analog Four MKII');
    expect(analogFour).toHaveTextContent('4 tracks staged');
    expect(within(analogFour).getAllByTestId(/device-rail-a4-track-/)).toHaveLength(4);
    expect(within(analogFour).getByTestId('device-rail-a4-track-1')).toHaveTextContent(
      'Bass movement',
    );
    expect(within(analogFour).getByTestId('device-rail-a4-track-4')).toHaveTextContent(
      'FX / texture',
    );
  });

  it('keeps both device cards mock-safe when no MIDI port is open', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    render(<DeviceRail />);

    expect(screen.getByTestId('device-card-analog-rytm-mk2')).toHaveTextContent('Mock Safe');
    expect(screen.getByTestId('device-card-analog-four-mk2')).toHaveTextContent('Mock Staged');
    expect(screen.getByTestId('device-rail')).toHaveTextContent('No MIDI port open');
  });
});
