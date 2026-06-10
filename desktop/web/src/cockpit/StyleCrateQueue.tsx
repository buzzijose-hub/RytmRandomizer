import { useMemo, useState } from 'react';

type CrateTone = 'blue' | 'cyan' | 'green' | 'muted' | 'orange' | 'purple' | 'yellow';

interface StyleCrate {
  readonly key: string;
  readonly name: string;
  readonly summary: string;
  readonly move: string;
  readonly energy: number;
  readonly risk: number;
  readonly tone: CrateTone;
}

interface QueueMove {
  readonly key: string;
  readonly crateKey: string;
  readonly label: string;
  readonly subtitle: string;
  readonly status: string;
}

const DEFAULT_STYLE_CRATE: StyleCrate = {
  key: 'dark-hypnotic',
  name: 'Dark Hypnotic',
  summary: 'Deeper & Minimal',
  move: 'Shadow Filter Pressure',
  energy: 5,
  risk: 3,
  tone: 'blue',
};

const STYLE_CRATES: ReadonlyArray<StyleCrate> = [
  {
    key: 'hard-groove',
    name: 'Hard Groove',
    summary: 'Rolling percussion density',
    move: 'Rolling Perc Push',
    energy: 7,
    risk: 4,
    tone: 'green',
  },
  DEFAULT_STYLE_CRATE,
  {
    key: 'industrial-warehouse',
    name: 'Industrial Warehouse',
    summary: 'Metal & Drive',
    move: 'Broken Metal Stress',
    energy: 8,
    risk: 7,
    tone: 'orange',
  },
  {
    key: 'dub-pressure',
    name: 'Dub Pressure',
    summary: 'Space and low-end',
    move: 'Sub Space Bloom',
    energy: 4,
    risk: 3,
    tone: 'purple',
  },
  {
    key: 'peak-time',
    name: 'Peak Time',
    summary: 'Energy & Lift',
    move: 'Warehouse Lift',
    energy: 9,
    risk: 6,
    tone: 'yellow',
  },
  {
    key: 'transition-build',
    name: 'Transition / Build',
    summary: 'Handoff movement',
    move: 'Back To Clean Handoff',
    energy: 6,
    risk: 2,
    tone: 'cyan',
  },
  {
    key: 'home-reset',
    name: 'Home / Reset',
    summary: 'Recovery anchor',
    move: 'Back To Clean',
    energy: 2,
    risk: 1,
    tone: 'muted',
  },
];

const STAGED_QUEUE: ReadonlyArray<QueueMove> = [
  {
    key: 'current-dark-hypnotic',
    crateKey: 'dark-hypnotic',
    label: 'Dark Hypnotic',
    subtitle: 'Deeper & Minimal',
    status: 'pending',
  },
  {
    key: 'next-industrial',
    crateKey: 'industrial-warehouse',
    label: 'Industrial Warehouse',
    subtitle: 'Metal & Drive',
    status: 'up next',
  },
  {
    key: 'next-peak-time',
    crateKey: 'peak-time',
    label: 'Peak Time',
    subtitle: 'Energy & Lift',
    status: 'up next',
  },
];

const PROFILE_LABELS = ['Subtle', 'Balanced', 'Extreme', 'Chaos'] as const;
type ProfileLabel = (typeof PROFILE_LABELS)[number];

export function StyleCrateQueue(): JSX.Element {
  const [selectedKey, setSelectedKey] = useState('dark-hypnotic');
  const [selectedProfile, setSelectedProfile] = useState<ProfileLabel>('Balanced');
  const selectedCrate = useMemo(
    () => STYLE_CRATES.find((crate) => crate.key === selectedKey) ?? DEFAULT_STYLE_CRATE,
    [selectedKey],
  );

  return (
    <section className="style-crate-queue" data-testid="style-crate-queue">
      <div className="style-crate-layout">
        <div className="style-crate-list" aria-label="Style crates">
          <div className="style-section-heading">Style Crates</div>
          {STYLE_CRATES.map((crate) => (
            <button
              key={crate.key}
              type="button"
              className={`style-crate-card ${crate.tone} ${
                crate.key === selectedKey ? 'active' : ''
              }`}
              data-testid={`style-crate-${crate.key}`}
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
          <div className="style-section-heading">Queue (3)</div>
          <div className="style-queue-stack">
            {STAGED_QUEUE.map((move, index) => (
              <article
                key={move.key}
                className={`style-queue-card ${index === 0 ? 'current' : ''}`}
                data-testid={index === 0 ? 'style-queue-current' : `style-queue-next-${index - 1}`}
              >
                <span className="style-queue-eyebrow">{index === 0 ? 'Current' : 'Up Next'}</span>
                <strong>{move.label}</strong>
                <span>{move.subtitle}</span>
                <em>{move.status}</em>
              </article>
            ))}
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

      <div className="style-crate-summary" data-testid="style-crate-summary">
        <strong>Mutation Summary</strong>
        <span>28 parameters will change across 5 pads and 1 synth track.</span>
      </div>
      <div className="style-crate-safety" data-testid="style-crate-safety">
        Passive queue preview only
      </div>
    </section>
  );
}
