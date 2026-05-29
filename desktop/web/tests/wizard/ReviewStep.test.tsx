/**
 * Tests for the ReviewStep — fourth wizard panel.
 */

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { ReviewStep } from '../../src/wizard/ReviewStep';
import type { CandidateProfileModel } from '../../src/types/wizard_protocol';

const candidate: CandidateProfileModel = {
  profile_id: 'wiz_01',
  name: 'buzzi',
  kind: 'user',
  model_version: '1.0.0',
  traits: [
    { name: 'rolling_low_end', value: 0.78 },
    { name: 'metallic_tension', value: 0.35 },
    { name: 'hat_density', value: 0.15 },
  ],
  pad_mappings: [
    { trait: 'rolling_low_end', pad_id: 1, weight: 0.9 },
    { trait: 'metallic_tension', pad_id: 2, weight: 0.6 },
  ],
  transition_curve: 'progressive',
  source_summary: '3 sources · 1,243 analyzed signals',
};

describe('ReviewStep', () => {
  it('shows the empty hint and Back button when there is no candidate', () => {
    const onBack = vi.fn();
    render(<ReviewStep candidate={null} onBack={onBack} onSave={vi.fn()} />);
    expect(screen.getByTestId('wizard-review-empty')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('wizard-back'));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('renders the candidate name, version, and source summary', () => {
    render(<ReviewStep candidate={candidate} onBack={vi.fn()} onSave={vi.fn()} />);
    expect(screen.getByRole('heading', { name: 'buzzi' })).toBeInTheDocument();
    expect(screen.getByTestId('wizard-review-version')).toHaveTextContent('v1.0.0');
    expect(screen.getByTestId('wizard-review-summary')).toHaveTextContent(
      '3 sources · 1,243 analyzed signals',
    );
  });

  it('renders one row per trait with the percent-formatted value', () => {
    render(<ReviewStep candidate={candidate} onBack={vi.fn()} onSave={vi.fn()} />);
    expect(screen.getByTestId('wizard-trait-rolling_low_end')).toHaveTextContent('78%');
    expect(screen.getByTestId('wizard-trait-metallic_tension')).toHaveTextContent('35%');
    expect(screen.getByTestId('wizard-trait-hat_density')).toHaveTextContent('15%');
  });

  it('renders pad-mapping bullets for traits that have a mapping AND omits the bullet list otherwise', () => {
    render(<ReviewStep candidate={candidate} onBack={vi.fn()} onSave={vi.fn()} />);
    expect(
      screen.getByTestId('wizard-trait-mapping-rolling_low_end-1'),
    ).toHaveTextContent('→ Pad 1 (weight 0.90)');
    expect(
      screen.getByTestId('wizard-trait-mapping-metallic_tension-2'),
    ).toHaveTextContent('→ Pad 2 (weight 0.60)');
    // hat_density has no mapping → no bullets rendered.
    expect(screen.queryByTestId('wizard-trait-mapping-hat_density-3')).not.toBeInTheDocument();
  });

  it('wires Save and Back to their handlers when a candidate is present', () => {
    const onBack = vi.fn();
    const onSave = vi.fn();
    render(<ReviewStep candidate={candidate} onBack={onBack} onSave={onSave} />);
    fireEvent.click(screen.getByTestId('wizard-save'));
    fireEvent.click(screen.getByTestId('wizard-back'));
    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('groups multiple pad mappings under the same trait into one bucket', () => {
    // Two mappings share the trait `rolling_low_end`. The first hits the
    // `bucket === undefined` branch (new array); the second hits the
    // already-exists branch (push onto the existing bucket) — both rendered
    // under the single trait row.
    const multiMapping: CandidateProfileModel = {
      ...candidate,
      pad_mappings: [
        { trait: 'rolling_low_end', pad_id: 1, weight: 0.9 },
        { trait: 'rolling_low_end', pad_id: 5, weight: 0.4 },
      ],
    };
    render(<ReviewStep candidate={multiMapping} onBack={vi.fn()} onSave={vi.fn()} />);
    expect(
      screen.getByTestId('wizard-trait-mapping-rolling_low_end-1'),
    ).toHaveTextContent('→ Pad 1 (weight 0.90)');
    expect(
      screen.getByTestId('wizard-trait-mapping-rolling_low_end-5'),
    ).toHaveTextContent('→ Pad 5 (weight 0.40)');
  });
});
