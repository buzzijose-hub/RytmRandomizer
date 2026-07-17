import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PatchGenomePanel } from '../../src/cockpit/PatchGenomePanel';
import {
  DEFAULT_PATCH_GENOME_MODEL,
  type PatchGenomeModel,
} from '../../src/cockpit/patchGenomeModel';

describe('PatchGenomePanel', () => {
  it('renders the design-preview genome surface without send controls', () => {
    render(<PatchGenomePanel previewOn={false} />);

    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('Patch Genome');
    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('Analog Four MKII');
    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('Dry-run preview');
    expect(screen.queryByRole('button', { name: /send/i })).not.toBeInTheDocument();
  });

  it('switches selected gene families locally', () => {
    render(<PatchGenomePanel previewOn={true} />);

    fireEvent.click(screen.getByTestId('patch-genome-family-filter_fx'));

    expect(screen.getByTestId('patch-genome-selected-family')).toHaveTextContent('Filter / FX');
    expect(screen.getByTestId('patch-genome-selected-family')).toHaveTextContent(
      'Filter 1 Frequency',
    );
  });

  it('locks and unlocks individual genes without dispatching hardware actions', () => {
    render(<PatchGenomePanel previewOn={true} />);
    fireEvent.click(screen.getByTestId('patch-genome-family-filter_fx'));
    const gene = screen.getByTestId('patch-genome-gene-filter_freq');

    fireEvent.click(within(gene).getByRole('button', { name: /lock filter frequency/i }));

    expect(gene).toHaveTextContent('Locked locally');

    fireEvent.click(within(gene).getByRole('button', { name: /unlock filter frequency/i }));

    expect(gene).not.toHaveTextContent('Locked locally');
  });

  it('grows and resets local variants', () => {
    render(<PatchGenomePanel previewOn={true} />);

    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Variant 1');

    fireEvent.click(screen.getByRole('button', { name: 'Grow variant' }));

    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Variant 2');

    fireEvent.click(screen.getByRole('button', { name: 'Reset seed' }));

    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Variant 1');
  });

  it('falls back to the first provided family and clamps local candidate values', () => {
    const model: PatchGenomeModel = {
      ...DEFAULT_PATCH_GENOME_MODEL,
      families: [
        {
          key: 'filter_fx',
          sectionLabel: 'III.',
          label: 'Clamp Family',
          summary: 'Exercises fallback and bounded preview values.',
          sendPolicy: 'No-send review',
          genes: [
            {
              key: 'below_zero',
              label: 'Below Zero',
              parameterLabel: 'Local test parameter',
              laneLabel: 'Clamp low',
              currentValue: 12,
              candidateValue: -4,
              status: 'ready',
              statusLabel: 'Ready',
            },
            {
              key: 'above_max',
              label: 'Above Max',
              parameterLabel: 'Local test parameter',
              laneLabel: 'Clamp high',
              currentValue: 12,
              candidateValue: 126,
              status: 'review',
              statusLabel: 'Needs review',
            },
          ],
        },
      ],
    };

    render(<PatchGenomePanel previewOn={true} model={model} />);

    expect(screen.getByTestId('patch-genome-selected-family')).toHaveTextContent('Clamp Family');
    expect(screen.getByTestId('patch-genome-gene-below_zero')).toHaveTextContent('0');

    fireEvent.click(screen.getByRole('button', { name: 'Grow variant' }));

    expect(screen.getByTestId('patch-genome-gene-above_max')).toHaveTextContent('127');
  });

  it('falls back to the default family when no model families exist', () => {
    const model: PatchGenomeModel = {
      ...DEFAULT_PATCH_GENOME_MODEL,
      families: [],
    };

    render(<PatchGenomePanel previewOn={false} model={model} />);

    expect(screen.getByTestId('patch-genome-selected-family')).toHaveTextContent('Oscillators');
  });
});
