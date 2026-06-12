import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StyleCrateQueue } from '../../src/cockpit/StyleCrateQueue';
import {
  DEFAULT_STYLE_CRATE_QUEUE_MODEL,
  type StyleCrateQueueModel,
} from '../../src/cockpit/styleCrateQueueModel';

const EMPTY_QUEUE_MODEL: StyleCrateQueueModel = {
  modelVersion: 'test-style-queue-v1',
  deckId: 'test-empty-queue',
  status: 'passive-preview',
  crates: [
    {
      key: 'recovery',
      testIdKey: 'recovery',
      name: 'Recovery',
      summary: 'Clean reset',
      move: 'Back To Clean',
      energy: 1,
      risk: 1,
      tone: 'muted',
      targetPads: [],
      riskStatus: 'safe',
      operatorAction: 'Preview only',
    },
  ],
  queue: [],
  journalCount: 0,
  summary: 'No staged moves cover 0 target pad slots and 0 journal seeds.',
  safetyLabel: 'Passive queue preview only',
  blockedActions: [],
  replayCommands: [],
};

const NO_CRATE_MODEL: StyleCrateQueueModel = {
  ...EMPTY_QUEUE_MODEL,
  deckId: 'test-no-crate-deck',
  crates: [],
};

describe('StyleCrateQueue', () => {
  it('renders a supplied style crate queue model instead of hardcoded component data', () => {
    render(<StyleCrateQueue model={DEFAULT_STYLE_CRATE_QUEUE_MODEL} />);

    expect(screen.getByTestId('style-crate-dark-hypnotic')).toHaveTextContent('Dark Hypnotic');
    expect(screen.getByTestId('style-crate-hard-groove')).toHaveTextContent('Hard Groove');
    expect(screen.getByTestId('style-queue-current')).toHaveTextContent('Shadow Filter Pressure');
    expect(screen.getByTestId('style-queue-next-0')).toHaveTextContent('Rolling Perc Push');
    expect(screen.getByTestId('style-crate-summary')).toHaveTextContent(
      '3 staged moves cover 14 target pad slots and 2 journal seeds.',
    );
  });

  it('updates selected backend-derived crate details locally', () => {
    render(<StyleCrateQueue model={DEFAULT_STYLE_CRATE_QUEUE_MODEL} />);

    fireEvent.click(screen.getByTestId('style-crate-hard-groove'));
    fireEvent.click(screen.getByRole('button', { name: 'Extreme' }));

    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('Hard Groove');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('Rolling Perc Push');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('pads 2, 3, 5, 6, 7, 9');
    expect(screen.getByRole('button', { name: 'Extreme' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  it('resets stale crate selection when the passive queue model changes', async () => {
    const { rerender } = render(<StyleCrateQueue model={DEFAULT_STYLE_CRATE_QUEUE_MODEL} />);
    fireEvent.click(screen.getByTestId('style-crate-hard-groove'));

    rerender(<StyleCrateQueue model={EMPTY_QUEUE_MODEL} />);

    expect(await screen.findByTestId('style-crate-selected')).toHaveTextContent('Recovery');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('pads none');
    expect(screen.getByTestId('style-queue-empty')).toHaveTextContent('No staged moves');
  });

  it('renders a passive empty-state when no style crates are supplied', () => {
    render(<StyleCrateQueue model={NO_CRATE_MODEL} />);

    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('No crate staged');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('No staged move');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('pads none');
    expect(screen.getByTestId('style-queue-empty')).toHaveTextContent('No staged moves');
  });
});
