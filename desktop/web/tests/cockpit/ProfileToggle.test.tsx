/**
 * Tests for ProfileToggle.
 */

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { ProfileToggle } from '../../src/cockpit/ProfileToggle';

describe('ProfileToggle', () => {
  it('marks the Scene tab active when value="scene"', () => {
    render(<ProfileToggle value="scene" onChange={() => undefined} />);
    expect(screen.getByRole('tab', { name: 'Scene' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: 'Inspiration' })).toHaveAttribute(
      'aria-selected',
      'false',
    );
    expect(screen.getByRole('tab', { name: 'Scene' }).className).toBe('active');
    expect(screen.getByRole('tab', { name: 'Inspiration' }).className).toBe('');
  });

  it('marks the Inspiration tab active when value="user"', () => {
    render(<ProfileToggle value="user" onChange={() => undefined} />);
    expect(screen.getByRole('tab', { name: 'Scene' })).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByRole('tab', { name: 'Inspiration' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });

  it('clicking Scene calls onChange("scene")', () => {
    const spy = vi.fn();
    render(<ProfileToggle value="user" onChange={spy} />);
    fireEvent.click(screen.getByRole('tab', { name: 'Scene' }));
    expect(spy).toHaveBeenCalledWith('scene');
  });

  it('clicking Inspiration calls onChange("user")', () => {
    const spy = vi.fn();
    render(<ProfileToggle value="scene" onChange={spy} />);
    fireEvent.click(screen.getByRole('tab', { name: 'Inspiration' }));
    expect(spy).toHaveBeenCalledWith('user');
  });
});
