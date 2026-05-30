/**
 * NameStep — first wizard panel.
 *
 *   Name *      [_________________]
 *   Description [_________________]
 *
 *                            [ Next → ]
 *
 * Submit validates the required `name` field: an empty/whitespace value renders
 * a `role="alert"` error region, sets `aria-invalid="true"` + `aria-describedby`
 * on the input, and moves keyboard focus there. This satisfies WCAG 2.2 §3.3.1
 * (Error Identification) and §3.3.3 (Error Suggestion). The Next button stays
 * focusable so screen-reader / keyboard users can discover the requirement —
 * disabling silently was the prior anti-pattern fixed by Cluster 3.
 *
 * On a valid submit, emits `wizard_set_metadata` with the trimmed name +
 * description, then asks the container to advance.
 */

import { useRef, useState, type ChangeEvent } from 'react';

export interface NameStepProps {
  initialName: string | null;
  initialDescription: string | null;
  onSubmit: (payload: { name: string; description: string | null }) => void;
  onCancel: () => void;
  /**
   * Most recent backend rejection of `wizard_set_metadata`. Rendered as a
   * `role="alert"` region so screen readers announce it on insertion and sighted
   * operators see why the expected advance to the Add step didn't happen.
   */
  commandError?: string | null;
}

const NAME_ERROR_ID = 'wizard-name-error';
const NAME_COMMAND_ERROR_ID = 'wizard-name-command-error';

export function NameStep({
  initialName,
  initialDescription,
  onSubmit,
  onCancel,
  commandError = null,
}: NameStepProps): JSX.Element {
  const [name, setName] = useState<string>(initialName ?? '');
  const [description, setDescription] = useState<string>(initialDescription ?? '');
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleNameChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setName(e.target.value);
  };
  const handleDescriptionChange = (e: ChangeEvent<HTMLTextAreaElement>): void => {
    setDescription(e.target.value);
  };

  const handleSubmit = (): void => {
    const trimmed = name.trim();
    if (trimmed.length === 0) {
      setError('Name is required.');
      inputRef.current?.focus();
      return;
    }
    setError(null);
    const trimmedDescription = description.trim();
    onSubmit({
      name: trimmed,
      description: trimmedDescription.length === 0 ? null : trimmedDescription,
    });
  };

  const hasError = error !== null;

  return (
    <section className="wizard-panel" data-testid="wizard-name-step">
      <h2>Name your profile</h2>
      <label className="wizard-field">
        <span className="wizard-field-label">Name</span>
        <input
          type="text"
          data-testid="wizard-name-input"
          value={name}
          onChange={handleNameChange}
          placeholder="e.g. buzzi"
          ref={inputRef}
          aria-required="true"
          aria-invalid={hasError}
          aria-describedby={hasError ? NAME_ERROR_ID : undefined}
        />
      </label>
      {hasError && (
        <div id={NAME_ERROR_ID} role="alert" className="wizard-field-error">
          {error}
        </div>
      )}
      {commandError !== null && (
        <div
          id={NAME_COMMAND_ERROR_ID}
          role="alert"
          className="wizard-field-error"
          data-testid="wizard-name-command-error"
        >
          {commandError}
        </div>
      )}
      <label className="wizard-field">
        <span className="wizard-field-label">Description (optional)</span>
        <textarea
          data-testid="wizard-description-input"
          value={description}
          onChange={handleDescriptionChange}
          placeholder="What is this profile for?"
          rows={3}
        />
      </label>
      <div className="wizard-actions">
        <button
          type="button"
          className="wizard-button ghost"
          data-testid="wizard-cancel"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          type="button"
          className="wizard-button primary"
          data-testid="wizard-next"
          onClick={handleSubmit}
        >
          Next →
        </button>
      </div>
    </section>
  );
}
