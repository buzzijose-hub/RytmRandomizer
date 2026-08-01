/**
 * Tests for DepthSlider.
 */

import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { DepthSlider } from '../../src/cockpit/DepthSlider';
import { runAxe } from '../a11y/__helpers__/axe';

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

  it('exposes aria-valuetext as a human percentage (APG slider name/role/value)', () => {
    renderWith(0.45);
    const input = screen.getByRole('slider');
    // Native range reports aria-valuenow as the raw float; aria-valuetext
    // gives the SR the "45 percent" the sighted chip shows.
    expect(input).toHaveAttribute('aria-valuetext', '45 percent');
    fireEvent.change(input, { target: { value: '0.7' } });
    expect(input).toHaveAttribute('aria-valuetext', '70 percent');
  });

  it('has no axe (WCAG 2.2 AA) violations', async () => {
    const container = renderAsElement();
    const results = await runAxe(container);
    expect(results.violations).toEqual([]);
  });
});

function renderAsElement(): HTMLElement {
  const fake = new FakeCockpitClient();
  const { container } = render(
    <CockpitClientProvider client={fake.asClient()}>
      <DepthSlider />
    </CockpitClientProvider>,
  );
  return container;
}
