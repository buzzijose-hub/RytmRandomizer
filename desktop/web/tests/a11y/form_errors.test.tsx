/**
 * Cluster 3 coverage — form-error feedback wired through ARIA so screen-reader users
 * hear what's wrong and keyboard focus moves to the offending field.
 *
 * Covers WCAG 2.2 success criteria 3.3.1 (Error Identification) and 3.3.3
 * (Error Suggestion). Each step that has required fields must:
 *   - allow the operator to attempt submission (no hard `disabled` gate)
 *   - on invalid: set `aria-invalid="true"` on the offending field, render a
 *     `role="alert"` region with a human-readable error, point
 *     `aria-describedby` at it, and move focus to the field
 *   - on a subsequent valid submission: clear the error, then call onSubmit
 *
 * `@testing-library/user-event` is not a project dep — we drive the form with
 * `fireEvent` (same approach the rest of the wizard test suite uses).
 */

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { NameStep } from '../../src/wizard/NameStep';
import { AddStep } from '../../src/wizard/AddStep';

describe('NameStep error feedback', () => {
  it('submitting empty name sets aria-invalid + role=alert + focuses field', () => {
    const onSubmit = vi.fn();
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );
    const nameInput = screen.getByTestId('wizard-name-input');
    const submit = screen.getByTestId('wizard-next');
    fireEvent.click(submit);

    expect(onSubmit).not.toHaveBeenCalled();
    expect(nameInput).toHaveAttribute('aria-invalid', 'true');
    const errorRegion = screen.getByRole('alert');
    expect(errorRegion).toHaveTextContent(/name is required/i);
    expect(nameInput).toHaveAttribute('aria-describedby', errorRegion.id);
    expect(nameInput).toHaveFocus();
  });

  it('valid submit calls onSubmit and does not set aria-invalid', () => {
    const onSubmit = vi.fn();
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );
    const nameInput = screen.getByTestId('wizard-name-input');
    fireEvent.change(nameInput, { target: { value: 'My new profile' } });
    fireEvent.click(screen.getByTestId('wizard-next'));

    expect(onSubmit).toHaveBeenCalledWith({
      name: 'My new profile',
      description: null,
    });
    expect(nameInput).toHaveAttribute('aria-invalid', 'false');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('correcting an empty submission clears the error region', () => {
    // Exercises the "error → valid → clear" branch so the coverage gate (100%
    // branches on wizard/**) lands on both arms of the `error !== null` check.
    const onSubmit = vi.fn();
    render(
      <NameStep
        initialName={null}
        initialDescription={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(screen.getByRole('alert')).toBeInTheDocument();

    fireEvent.change(screen.getByTestId('wizard-name-input'), {
      target: { value: 'fixed' },
    });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(onSubmit).toHaveBeenCalledWith({ name: 'fixed', description: null });
  });
});

describe('AddStep draft error feedback', () => {
  it('confirming an empty draft sets aria-invalid + role=alert + focuses location', () => {
    const onAddSource = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));

    expect(onAddSource).not.toHaveBeenCalled();
    const locationInput = screen.getByTestId('wizard-draft-location');
    expect(locationInput).toHaveAttribute('aria-invalid', 'true');
    const errorRegion = screen.getByRole('alert');
    expect(errorRegion).toHaveTextContent(/required/i);
    expect(locationInput).toHaveAttribute('aria-describedby', errorRegion.id);
    expect(locationInput).toHaveFocus();
  });

  it('valid confirm calls onAddSource and does not set aria-invalid', () => {
    const onAddSource = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: 'Surgeon' },
    });
    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: 'Surgeon' },
    });
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));

    expect(onAddSource).toHaveBeenCalledWith({
      kind: 'artist',
      mode: 'reference',
      location: 'Surgeon',
      display_name: 'Surgeon',
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('correcting an invalid draft clears the alert (display-name-only branch)', () => {
    // Cover the "display name missing" arm of the validator so both required-field
    // branches (location + display name) are exercised.
    const onAddSource = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: 'Surgeon' },
    });
    // display name still blank — confirm fails.
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    expect(screen.getByRole('alert')).toHaveTextContent(/display name/i);

    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: 'Surgeon' },
    });
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    expect(onAddSource).toHaveBeenCalled();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('file-mode draft also marks location aria-invalid on empty submit', () => {
    // Exercises the file/folder branch of the location input (the other JSX arm).
    // The reference-mode tests above cover the `reference` branch; this one covers
    // the path-input branch so `aria-describedby={... ? DRAFT_ERROR_ID : undefined}`
    // is exercised on both render paths (100% branch coverage on wizard/**).
    const onAddSource = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit')); // defaults to 'file' mode
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    const locationInput = screen.getByTestId('wizard-draft-location');
    expect(locationInput).toHaveAttribute('aria-invalid', 'true');
    const errorRegion = screen.getByRole('alert');
    expect(locationInput).toHaveAttribute('aria-describedby', errorRegion.id);
    expect(onAddSource).not.toHaveBeenCalled();
  });
});
