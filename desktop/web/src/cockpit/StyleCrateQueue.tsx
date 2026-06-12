import { useEffect, useMemo, useState } from 'react';

import {
  DEFAULT_STYLE_CRATE_QUEUE_MODEL,
  type StyleCrateQueueCrate,
  type StyleCrateQueueModel,
} from './styleCrateQueueModel';

const PROFILE_LABELS = ['Subtle', 'Balanced', 'Extreme', 'Chaos'] as const;
type ProfileLabel = (typeof PROFILE_LABELS)[number];

export interface StyleCrateQueueProps {
  readonly model?: StyleCrateQueueModel;
}

const EMPTY_STYLE_CRATE: StyleCrateQueueCrate = {
  key: 'empty',
  testIdKey: 'empty',
  name: 'No crate staged',
  summary: 'No passive crate deck is available.',
  move: 'No staged move',
  energy: 0,
  risk: 0,
  tone: 'muted',
  targetPads: [],
  riskStatus: 'safe',
  operatorAction: 'Load a passive rehearsal deck',
};

export function StyleCrateQueue({
  model = DEFAULT_STYLE_CRATE_QUEUE_MODEL,
}: StyleCrateQueueProps): JSX.Element {
  const firstCrateKey = model.crates[0]?.key ?? EMPTY_STYLE_CRATE.key;
  const [selectedKey, setSelectedKey] = useState(firstCrateKey);
  const [selectedProfile, setSelectedProfile] = useState<ProfileLabel>('Balanced');

  useEffect(() => {
    if (!model.crates.some((crate) => crate.key === selectedKey)) {
      setSelectedKey(firstCrateKey);
    }
  }, [firstCrateKey, model.crates, selectedKey]);

  const selectedCrate = useMemo(
    () =>
      model.crates.find((crate) => crate.key === selectedKey) ??
      model.crates[0] ??
      EMPTY_STYLE_CRATE,
    [model.crates, selectedKey],
  );
  const analogFourSetPlan = model.analogFourSetPlan;
  const analogFourNextLabels = analogFourSetPlan.upNext
    .map((step) => step.macroName)
    .join(' -> ');

  return (
    <section className="style-crate-queue" data-testid="style-crate-queue">
      <div className="style-crate-layout">
        <div className="style-crate-list" aria-label="Style crates">
          <div className="style-section-heading">Style Crates</div>
          {model.crates.map((crate) => (
            <button
              key={crate.key}
              type="button"
              className={`style-crate-card ${crate.tone} ${
                crate.key === selectedKey ? 'active' : ''
              }`}
              data-testid={`style-crate-${crate.testIdKey}`}
              aria-pressed={crate.key === selectedKey}
              onClick={() => setSelectedKey(crate.key)}
            >
              <span className="style-crate-name">{crate.name}</span>
              <span className="style-crate-summary-line">{crate.summary}</span>
              <span aria-hidden="true" className="style-crate-star">
                *
              </span>
            </button>
          ))}
        </div>

        <div className="style-queue-panel" aria-label="Staged style queue">
          <div className="style-section-heading">Queue ({model.queue.length})</div>
          <div className="style-queue-stack">
            {model.queue.map((move, index) => (
              <article
                key={move.key}
                className={`style-queue-card ${index === 0 ? 'current' : ''}`}
                data-testid={index === 0 ? 'style-queue-current' : `style-queue-next-${index - 1}`}
              >
                <span className="style-queue-eyebrow">{move.position}</span>
                <strong>{move.label}</strong>
                <span>{move.crateName}</span>
                <span>{move.subtitle}</span>
                <em>{move.status}</em>
              </article>
            ))}
            {model.queue.length === 0 ? (
              <article className="style-queue-card" data-testid="style-queue-empty">
                <span className="style-queue-eyebrow">Empty</span>
                <strong>No staged moves</strong>
                <span>Load a passive rehearsal deck to populate the queue.</span>
              </article>
            ) : null}
          </div>
        </div>
      </div>

      <article className="style-crate-selected" data-testid="style-crate-selected">
        <div>
          <span className="style-section-heading">Selected Move</span>
          <strong>{selectedCrate.name}</strong>
          <span>{selectedCrate.summary}</span>
        </div>
        <div className="style-crate-meter-grid" aria-label="Selected move risk and energy">
          <span>Energy {selectedCrate.energy}/10</span>
          <span>Risk {selectedCrate.risk}/10</span>
          <span>{selectedCrate.move}</span>
          <span>pads {selectedCrate.targetPads.join(', ') || 'none'}</span>
        </div>
      </article>

      <div className="style-profile-row" aria-label="Mutation profile">
        {PROFILE_LABELS.map((label) => (
          <button
            key={label}
            type="button"
            className={`style-profile-pill ${label === selectedProfile ? 'active' : ''}`}
            aria-pressed={label === selectedProfile}
            onClick={() => setSelectedProfile(label)}
          >
            {label}
          </button>
        ))}
      </div>

      <article className="style-crate-a4-set-plan" data-testid="style-crate-a4-set-plan">
        <div className="style-crate-a4-header">
          <div>
            <span className="style-section-heading">Analog Four Set Plan</span>
            <strong>{analogFourSetPlan.setName}</strong>
          </div>
          <span>{analogFourSetPlan.sendsMidi ? 'active send path' : 'passive review'}</span>
        </div>
        <div className="style-crate-a4-grid">
          <div data-testid="style-crate-a4-current">
            <span className="style-queue-eyebrow">Current</span>
            <strong>{analogFourSetPlan.currentStep.macroName}</strong>
            <span>{analogFourSetPlan.currentStep.macroLabel}</span>
            <span>{analogFourSetPlan.currentStep.readiness}</span>
          </div>
          <div data-testid="style-crate-a4-next">
            <span className="style-queue-eyebrow">Up Next</span>
            <strong>{analogFourNextLabels || 'none'}</strong>
            <span>{analogFourSetPlan.upNext.length} queued A4 moves</span>
            <span>{analogFourSetPlan.currentStep.recoveryAction}</span>
          </div>
        </div>
        <div className="style-crate-a4-safety">
          {analogFourSetPlan.blockedActiveActions.map((action) => (
            <span key={action}>{action}</span>
          ))}
          <span>{analogFourSetPlan.safety.find((line) => line === 'no MIDI sending')}</span>
        </div>
      </article>

      <div className="style-crate-summary" data-testid="style-crate-summary">
        <strong>Mutation Summary</strong>
        <span>{model.summary}</span>
      </div>
      <div className="style-crate-safety" data-testid="style-crate-safety">
        {model.safetyLabel}
      </div>
    </section>
  );
}
