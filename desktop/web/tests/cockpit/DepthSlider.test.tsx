/**
 * Tests for DepthSlider.
 */

import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { DepthSlider } from '../../src/cockpit/DepthSlider';

import { FakeCockpitClient } from './_fixtures';

function renderWith(initial?: number): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      {initial === undefined ? <DepthSlider /> : <DepthSlider initial={initial} />}
    </CockpitClientProvider>,
  );
  return fake;
}

describe('DepthSlider', () => {
  it('renders with the default initial value (45%)', () => {
    renderWith();
    expect(screen.getByTestId('depth-slider-value')).toHaveTextContent('45%');
  });

  it('renders with a custom initial value', () => {
    renderWith(0.3);
    expect(screen.getByTestId('depth-slider-value')).toHaveTextContent('30%');
  });

  it('changing the slider emits set_depth with the new value and updates the displayed %', () => {
    const fake = renderWith();
    const input = screen.getByRole('slider');
    fireEvent.change(input, { target: { value: '0.7' } });
    expect(screen.getByTestId('depth-slider-value')).toHaveTextContent('70%');
    expect(fake.sent).toEqual([{ type: 'set_depth', depth: 0.7 }]);
  });

  it('pointer down + up toggles the "active" class on the input', () => {
    renderWith();
    const input = screen.getByRole('slider');
    expect(input.className).toBe('depth-slider-range');
    fireEvent.pointerDown(input);
    expect(input.className).toBe('depth-slider-range active');
    fireEvent.pointerUp(input);
    expect(input.className).toBe('depth-slider-range');
  });

  it('blur clears the active class even if pointerUp did not fire', () => {
    renderWith();
    const input = screen.getByRole('slider');
    fireEvent.pointerDown(input);
    expect(input.className).toBe('depth-slider-range active');
    fireEvent.blur(input);
    expect(input.className).toBe('depth-slider-range');
  });

  it('renders the 10/30/50/70/90 ticks', () => {
    renderWith();
    for (const t of ['10', '30', '50', '70', '90']) {
      expect(screen.getByText(t)).toBeInTheDocument();
    }
  });
});
