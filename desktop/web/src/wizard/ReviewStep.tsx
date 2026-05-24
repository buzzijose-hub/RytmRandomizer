/**
 * ReviewStep — fourth wizard panel.
 *
 *   Profile preview                                  v1.0.0
 *   ──────────────────────────────────────────────────────────
 *   rolling_low_end   ███████████░░░  78%   → Pad 1 (weight 0.9)
 *   metallic_tension  █████░░░░░░░░░  35%   → Pad 2 (weight 0.6)
 *   hat_density       ██░░░░░░░░░░░░  15%   → Pad 3 (weight 0.3)
 *
 *   3 sources · 1,243 analyzed signals
 *
 *               [← Back]                       [Save profile]
 */

import type { CandidateProfileModel } from '../types/wizard_protocol';

export interface ReviewStepProps {
  candidate: CandidateProfileModel | null;
  onBack: () => void;
  onSave: () => void;
}

export function ReviewStep({ candidate, onBack, onSave }: ReviewStepProps): JSX.Element {
  if (candidate === null) {
    return (
      <section className="wizard-panel" data-testid="wizard-review-step">
        <h2>Review</h2>
        <p className="wizard-empty-hint" data-testid="wizard-review-empty">
          No candidate profile yet — finish analysis first.
        </p>
        <div className="wizard-actions">
          <button
            type="button"
            className="wizard-button ghost"
            data-testid="wizard-back"
            onClick={onBack}
          >
            ← Back
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="wizard-panel" data-testid="wizard-review-step">
      <header className="wizard-review-header">
        <h2>{candidate.name}</h2>
        <span className="wizard-review-version" data-testid="wizard-review-version">
          v{candidate.model_version}
        </span>
      </header>

      <ul className="wizard-trait-list" data-testid="wizard-trait-list">
        {candidate.traits.map((trait) => {
          const mappings = candidate.pad_mappings.filter((m) => m.trait === trait.name);
          return (
            <li
              key={trait.name}
              className="wizard-trait-row"
              data-testid={`wizard-trait-${trait.name}`}
            >
              <div className="wizard-trait-header">
                <span className="wizard-trait-name">{trait.name}</span>
                <span className="wizard-trait-value">{Math.round(trait.value * 100)}%</span>
              </div>
              <div
                className="wizard-progress"
                role="meter"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(trait.value * 100)}
              >
                <div
                  className="wizard-progress-bar"
                  style={{ width: `${Math.round(trait.value * 100)}%` }}
                />
              </div>
              {mappings.length === 0 ? null : (
                <ul className="wizard-trait-mappings">
                  {mappings.map((m) => (
                    <li
                      key={`${m.trait}-${m.pad_id}`}
                      className="wizard-trait-mapping"
                      data-testid={`wizard-trait-mapping-${m.trait}-${m.pad_id}`}
                    >
                      → Pad {m.pad_id} (weight {m.weight.toFixed(2)})
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ul>

      <p className="wizard-review-summary" data-testid="wizard-review-summary">
        {candidate.source_summary}
      </p>

      <div className="wizard-actions">
        <button
          type="button"
          className="wizard-button ghost"
          data-testid="wizard-back"
          onClick={onBack}
        >
          ← Back
        </button>
        <button
          type="button"
          className="wizard-button primary"
          data-testid="wizard-save"
          onClick={onSave}
        >
          Save profile
        </button>
      </div>
    </section>
  );
}
