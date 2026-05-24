/**
 * Tests for the NameStep — first wizard panel.
 */

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { NameStep } from '../../src/wizard/NameStep';

describe('NameStep', () => {
  it('renders empty when no initial values are provided', () => {
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-name-input')).toHaveValue('');
    expect(screen.getByTestId('wizard-description-input')).toHaveValue('');
    expect(screen.getByTestId('wizard-next')).toBeDisabled();
  });

  it('seeds the inputs with the initial values when present', () => {
    render(
      <NameStep
        initialName="buzzi"
        initialDescription="industrial"
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-name-input')).toHaveValue('buzzi');
    expect(screen.getByTestId('wizard-description-input')).toHaveValue('industrial');
    expect(screen.getByTestId('wizard-next')).toBeEnabled();
  });

  it('keeps Next disabled when the name is only whitespace', () => {
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByTestId('wizard-name-input'), { target: { value: '   ' } });
    expect(screen.getByTestId('wizard-next')).toBeDisabled();
  });

  it('does not call onSubmit when the disabled button is clicked', () => {
    const onSubmit = vi.fn();
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );
    const next = screen.getByTestId('wizard-next');
    fireEvent.click(next);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits with a trimmed name and null description when description blank', () => {
    const onSubmit = vi.fn();
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByTestId('wizard-name-input'), {
      target: { value: '  buzzi  ' },
    });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(onSubmit).toHaveBeenCalledWith({ name: 'buzzi', description: null });
  });

  it('submits with both fields trimmed when description is non-empty', () => {
    const onSubmit = vi.fn();
    render(
      <NameStep
        initialName="x"
        initialDescription={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByTestId('wizard-description-input'), {
      target: { value: '   industrial heat   ' },
    });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(onSubmit).toHaveBeenCalledWith({ name: 'x', description: 'industrial heat' });
  });

  it('submits with null description when description is only whitespace', () => {
    const onSubmit = vi.fn();
    render(
      <NameStep
        initialName="x"
        initialDescription={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByTestId('wizard-description-input'), {
      target: { value: '     ' },
    });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(onSubmit).toHaveBeenCalledWith({ name: 'x', description: null });
  });

  it('calls onCancel when the Cancel button is clicked', () => {
    const onCancel = vi.fn();
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={vi.fn()}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-cancel'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
