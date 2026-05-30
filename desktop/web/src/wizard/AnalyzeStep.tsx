/**
 * AnalyzeStep — third wizard panel.
 *
 *   Source A ████████████░░░░  72%   analyzing
 *   Source B ████████████████ 100%   ok
 *   Source C ██░░░░░░░░░░░░░░  10%   failed   [retry]
 *
 * The progress + status come from the `jobs` slice; the WS-D backend pushes
 * `analysis_progress` events that update each job in place via the store.
 *
 * The "Review" action becomes enabled once every job has reached a terminal status
 * (ok or failed) AND at least one job is ok (otherwise there's nothing to build from).
 *
 * Perf: the source → job lookup is held in a `useMemo`-d `Map` keyed by `source_id`,
 * so the render is O(N) in sources instead of O(N·M) from a per-source `jobs.find`.
 * Backend `analysis_progress` events fire frequently while sources are running, so
 * the constant-factor savings compound during the analyze step.
 */

import { useMemo } from 'react';

import type { AnalysisJob, InspirationSource } from '../types/wizard_protocol';

export interface AnalyzeStepProps {
  sources: ReadonlyArray<InspirationSource>;
  jobs: ReadonlyArray<AnalysisJob>;
  onStartAnalyze: () => void;
  onRetry: (sourceId: string) => void;
  onBack: () => void;
  onNext: () => void;
  commandError?: string | null;
}

export function AnalyzeStep({
  sources,
  jobs,
  onStartAnalyze,
  onRetry,
  onBack,
  onNext,
  commandError = null,
}: AnalyzeStepProps): JSX.Element {
  const hasJobs = jobs.length > 0;
  const allTerminal = hasJobs && jobs.every((j) => j.status === 'ok' || j.status === 'failed');
  const anyOk = jobs.some((j) => j.status === 'ok');
  const canReview = allTerminal && anyOk;

  // Build the index once per `jobs` reference. Each analysis_progress event swaps the
  // jobs array; the Map is rebuilt then but stays stable for every render in between.
  const jobsBySourceId = useMemo<Map<string, AnalysisJob>>(() => {
    const map = new Map<string, AnalysisJob>();
    for (const job of jobs) map.set(job.source_id, job);
    return map;
  }, [jobs]);

  return (
    <section className="wizard-panel" data-testid="wizard-analyze-step">
      <h2>Analyze sources</h2>
      {commandError === null ? null : (
        <div
          role="alert"
          className="wizard-field-error"
          data-testid="wizard-command-error"
        >
          {commandError}
        </div>
      )}
      {hasJobs ? null : (
        <p className="wizard-empty-hint" data-testid="wizard-analyze-empty">
          Tap Analyze to run all sources through the analysis pipeline.
        </p>
      )}

      <ul className="wizard-job-list" data-testid="wizard-job-list">
        {sources.map((source) => {
          const job = jobsBySourceId.get(source.source_id) ?? null;
          return (
            <li
              key={source.source_id}
              className={`wizard-job-row status-${job?.status ?? 'pending'}`}
              data-testid={`wizard-job-${source.source_id}`}
            >
              <div className="wizard-job-meta">
                <span className="wizard-job-name">{source.display_name}</span>
                <span className="wizard-job-status" data-testid={`wizard-job-status-${source.source_id}`}>
                  {job?.status ?? 'pending'}
                </span>
              </div>
              <div
                className="wizard-progress"
                data-testid={`wizard-progress-${source.source_id}`}
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round((job?.progress ?? 0) * 100)}
              >
                <div
                  className="wizard-progress-bar"
                  style={{ width: `${Math.round((job?.progress ?? 0) * 100)}%` }}
                />
              </div>
              {job !== null && job.status === 'failed' ? (
                <div className="wizard-job-error">
                  <span className="wizard-job-error-text" data-testid={`wizard-job-error-${source.source_id}`}>
                    {job.error ?? 'analysis failed'}
                  </span>
                  <button
                    type="button"
                    className="wizard-button ghost"
                    data-testid={`wizard-job-retry-${source.source_id}`}
                    onClick={() => onRetry(source.source_id)}
                  >
                    Retry
                  </button>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>

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
          className="wizard-button ghost"
          data-testid="wizard-analyze-start"
          onClick={onStartAnalyze}
        >
          Run analysis
        </button>
        <button
          type="button"
          className="wizard-button primary"
          data-testid="wizard-next"
          disabled={!canReview}
          onClick={onNext}
        >
          Review →
        </button>
      </div>
    </section>
  );
}
