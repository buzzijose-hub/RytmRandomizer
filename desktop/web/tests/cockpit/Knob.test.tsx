/**
 * Tests for the Knob component.
 *
 * Coverage targets:
 *   - valueToAngle: low, mid, high, negative (clamps), over-max (clamps)
 *   - rendering: indicator angle reflects value
 *   - ghost indicator: not shown when ghostValue is null/undefined, not shown when ghostValue === value, shown otherwise
 */

import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import { Knob, valueToAngle } from '../../src/cockpit/Knob';

describe('Knob — valueToAngle', () => {
  it('maps value 0 to -135 degrees', () => {
    expect(valueToAngle(0)).toBe(-135);
  });

  it('maps value 127 to +135 degrees', () => {
    expect(valueToAngle(127)).toBe(135);
  });

  it('maps midpoint (63.5) to ~0 degrees', () => {
    expect(valueToAngle(63.5)).toBeCloseTo(0, 5);
  });

  it('clamps negative values to -135', () => {
    expect(valueToAngle(-50)).toBe(-135);
  });

  it('clamps over-max values to +135', () => {
    expect(valueToAngle(500)).toBe(135);
  });
});

describe('Knob — rendering', () => {
  it('renders the label and current value', () => {
    render(<Knob label="TUN" value={64} />);
    expect(screen.getByText('TUN')).toBeInTheDocument();
    expect(screen.getByText('64')).toBeInTheDocument();
  });

  it('applies a rotated transform on the indicator', () => {
    render(<Knob label="DEC" value={127} />);
    const indicator = screen.getByTestId('knob-indicator-DEC');
    expect(indicator.getAttribute('style')).toContain('rotate(135deg)');
  });

  it('does not render the ghost indicator when ghostValue is null', () => {
    render(<Knob label="LEV" value={50} ghostValue={null} />);
    expect(screen.queryByTestId('knob-ghost-LEV')).not.toBeInTheDocument();
  });

  it('does not render the ghost indicator when ghostValue is omitted (undefined default)', () => {
    render(<Knob label="LEV" value={50} />);
    expect(screen.queryByTestId('knob-ghost-LEV')).not.toBeInTheDocument();
  });

  it('does not render the ghost indicator when ghostValue equals value (no delta)', () => {
    render(<Knob label="LEV" value={50} ghostValue={50} />);
    expect(screen.queryByTestId('knob-ghost-LEV')).not.toBeInTheDocument();
  });

  it('renders the ghost indicator when ghostValue differs from value', () => {
    render(<Knob label="FLT" value={20} ghostValue={100} />);
    const ghost = screen.getByTestId('knob-ghost-FLT');
    expect(ghost).toBeInTheDocument();
    // 100 maps to about 76.85 degrees.
    expect(ghost.getAttribute('style')).toMatch(/rotate\(7[0-9](\.[0-9]+)?deg\)/);
  });
});
