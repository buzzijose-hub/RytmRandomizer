/**
 * Tests for the AnalyzeStep — third wizard panel.
 */

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { AnalyzeStep } from '../../src/wizard/AnalyzeStep';
import type { AnalysisJob, InspirationSource } from '../../src/types/wizard_protocol';

const sourceA: InspirationSource = {
  source_id: 'src_A',
  kind: 'artist',
  mode: 'reference',
  location: 'Surgeon',
  display_name: 'Surgeon',
  added_at: '2026-05-24T10:00:00Z',
};

const sourceB: InspirationSource = {
  source_id: 'src_B',
  kind: 'kit',
  mode: 'file',
  location: '/tmp/kit.syx',
  display_name: 'kit.syx',
  added_at: '2026-05-24T10:01:00Z',
};

const jobOk: AnalysisJob = {
  source_id: 'src_A',
  status: 'ok',
  progress: 1,
  error: null,
  extracted_traits: [{ name: 'rolling_low_end', value: 0.8 }],
};

const jobFailed: AnalysisJob = {
  source_id: 'src_B',
  status: 'failed',
  progress: 0.4,
  error: 'unsupported file',
  extracted_traits: [],
};

describe('AnalyzeStep', () => {
  it('shows the empty hint when there are no jobs yet', () => {
    render(
      <AnalyzeStep
        sources={[sourceA]}
        jobs={[]}
        onStartAnalyze={vi.fn()}
        onRetry={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-analyze-empty')).toBeInTheDocument();
    // Pending row renders with status "pending" and progress 0.
    expect(screen.getByTestId('wizard-job-status-src_A')).toHaveTextContent('pending');
    const bar = screen.getByTestId('wizard-progress-src_A');
    expect(bar).toHaveAttribute('aria-valuenow', '0');
  });

  it('renders per-source progress + status when jobs are present', () => {
    render(
      <AnalyzeStep
        sources={[sourceA, sourceB]}
        jobs={[jobOk, jobFailed]}
        onStartAnalyze={vi.fn()}
        onRetry={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.queryByTestId('wizard-analyze-empty')).not.toBeInTheDocument();
    expect(screen.getByTestId('wizard-job-status-src_A')).toHaveTextContent('ok');
    expect(screen.getByTestId('wizard-progress-src_A')).toHaveAttribute('aria-valuenow', '100');
    expect(screen.getByTestId('wizard-job-status-src_B')).toHaveTextContent('failed');
    expect(screen.getByTestId('wizard-progress-src_B')).toHaveAttribute('aria-valuenow', '40');
  });

  it('shows the error text + Retry button on a failed job', () => {
    const onRetry = vi.fn();
    render(
      <AnalyzeStep
        sources={[sourceB]}
        jobs={[jobFailed]}
        onStartAnalyze={vi.fn()}
        onRetry={onRetry}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-job-error-src_B')).toHaveTextContent('unsupported file');
    fireEvent.click(screen.getByTestId('wizard-job-retry-src_B'));
    expect(onRetry).toHaveBeenCalledWith('src_B');
  });

  it('falls back to "analysis failed" when the job error is null', () => {
    render(
      <AnalyzeStep
        sources={[sourceB]}
        jobs={[{ ...jobFailed, error: null }]}
        onStartAnalyze={vi.fn()}
        onRetry={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-job-error-src_B')).toHaveTextContent('analysis failed');
  });

  it('does not show a Retry button for ok / analyzing / pending jobs', () => {
    render(
      <AnalyzeStep
        sources={[sourceA, sourceB]}
        jobs={[jobOk, { ...jobFailed, status: 'analyzing', error: null }]}
        onStartAnalyze={vi.fn()}
        onRetry={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.queryByTestId('wizard-job-retry-src_A')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-job-retry-src_B')).not.toBeInTheDocument();
  });

  it('keeps Review disabled until every job is terminal AND at least one is ok', () => {
    const { rerender } = render(
      <AnalyzeStep
        sources={[sourceA, sourceB]}
        jobs={[jobOk, { ...jobFailed, status: 'analyzing' }]}
        onStartAnalyze={vi.fn()}
        onRetry={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-next')).toBeDisabled();

    // All terminal but none ok: still disabled.
    rerender(
      <AnalyzeStep
        sources={[sourceA, sourceB]}
        jobs={[
          { ...jobOk, status: 'failed', error: 'x' },
          jobFailed,
        ]}
        onStartAnalyze={vi.fn()}
        onRetry={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-next')).toBeDisabled();

    // All terminal AND at least one ok: enabled.
    rerender(
      <AnalyzeStep
        sources={[sourceA, sourceB]}
        jobs={[jobOk, jobFailed]}
        onStartAnalyze={vi.fn()}
        onRetry={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-next')).toBeEnabled();
  });

  it('wires Run analysis / Back / Review buttons to their handlers', () => {
    const onStartAnalyze = vi.fn();
    const onBack = vi.fn();
    const onNext = vi.fn();
    render(
      <AnalyzeStep
        sources={[sourceA]}
        jobs={[jobOk]}
        onStartAnalyze={onStartAnalyze}
        onRetry={vi.fn()}
        onBack={onBack}
        onNext={onNext}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    fireEvent.click(screen.getByTestId('wizard-back'));
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(onStartAnalyze).toHaveBeenCalledTimes(1);
    expect(onBack).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
  });
});
