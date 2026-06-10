import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StyleCrateQueue } from '../../src/cockpit/StyleCrateQueue';
import { DEFAULT_STYLE_CRATE_QUEUE_MODEL } from '../../src/cockpit/styleCrateQueueModel';

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

    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('Hard Groove');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('Rolling Perc Push');
    expect(screen.getByTestId('style-crate-selected')).toHaveTextContent('pads 2, 3, 5, 6, 7, 9');
  });
});
