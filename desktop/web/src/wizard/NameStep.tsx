/**
 * NameStep — first wizard panel.
 *
 *   Name *      [_________________]
 *   Description [_________________]
 *
 *                            [ Next → ]
 *
 * The Next button is disabled until a non-empty name is provided.
 * On Next, emits `wizard_set_metadata` with the trimmed name + description, then asks the
 * container to advance.
 */

import { useState, type ChangeEvent } from 'react';

export interface NameStepProps {
  initialName: string | null;
  initialDescription: string | null;
  onSubmit: (payload: { name: string; description: string | null }) => void;
  onCancel: () => void;
}

export function NameStep({
  initialName,
  initialDescription,
  onSubmit,
  onCancel,
}: NameStepProps): JSX.Element {
  const [name, setName] = useState<string>(initialName ?? '');
  const [description, setDescription] = useState<string>(initialDescription ?? '');

  const trimmed = name.trim();
  const canSubmit = trimmed.length > 0;

  const handleNameChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setName(e.target.value);
  };
  const handleDescriptionChange = (e: ChangeEvent<HTMLTextAreaElement>): void => {
    setDescription(e.target.value);
  };

  const handleSubmit = (): void => {
    const trimmedDescription = description.trim();
    onSubmit({
      name: trimmed,
      description: trimmedDescription.length === 0 ? null : trimmedDescription,
    });
  };

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
        />
      </label>
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
          disabled={!canSubmit}
          onClick={handleSubmit}
        >
          Next →
        </button>
      </div>
    </section>
  );
}
