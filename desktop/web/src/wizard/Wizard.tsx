/**
 * Wizard — top-level container mounted at the `#/wizard` hash route.
 *
 * Responsibilities:
 *   - On mount: bind the cockpit client to the wizard store + emit `wizard_start`.
 *   - Drive the active step from the store's WizardState.step (with optimistic fallback).
 *   - Forward step-specific events to typed WS commands via `sendWizardCommand`.
 *   - On `wizard_save` ack, navigate back to the cockpit (`#/`).
 *   - On unmount: detach the binding (no implicit cancel — the cancel button does it).
 */

import { useEffect, useRef, useState } from 'react';

import { useCockpitStore } from '../state';
import type { CockpitClient } from '../ws/client';
import type { CommandAck } from '../ws/protocol';
import {
  bindWizardClient,
  selectCandidateProfile,
  selectJobs,
  selectSources,
  selectStep,
  sendWizardCommand,
  useWizardStore,
  type WizardStore,
} from '../state/wizard_store';
import type {
  WizardSourceKind,
  WizardSourceMode,
  WizardCommand,
  WizardStep,
} from '../types/wizard_protocol';

import { AddStep } from './AddStep';
import { AnalyzeStep } from './AnalyzeStep';
import { NameStep } from './NameStep';
import { ReviewStep } from './ReviewStep';
import { WizardSteps } from './WizardSteps';

import './styles.css';

function ackErrorMessage(action: string, ack: CommandAck): string {
  const detail = ack.error?.trim() || ack.code?.trim() || 'command rejected';
  return `${action} failed: ${detail}`;
}

function thrownErrorMessage(action: string, error: unknown): string {
  if (error instanceof Error && error.message.trim() !== '') {
    return `${action} failed: ${error.message.trim()}`;
  }
  return `${action} failed: connection unavailable`;
}

export interface WizardProps {
  client: CockpitClient;
  /**
   * Optional store override (defaults to the singleton). Tests use this to isolate state.
   * The zustand `UseBoundStore` is structurally compatible — accept any shape that exposes
   * `getState` + a `(selector) => T` call signature.
   */
  store?: typeof useWizardStore;
  /** Optional navigation override; defaults to mutating `window.location.hash`. */
  navigate?: (hash: string) => void;
  /**
   * Optional dialog opener passed through to AddStep (tests inject this; production code
   * lets AddStep dynamically import the Tauri plugin).
   */
  openDialog?: (mode: 'file' | 'folder') => Promise<string | null>;
}

export function Wizard({
  client,
  store = useWizardStore,
  navigate,
  openDialog,
}: WizardProps): JSX.Element {
  // Slice the store into the four things this container actually depends on. Each
  // selector subscribes to a single field of the underlying WizardState, so changing
  // (say) the jobs slice does not re-render the metadata fields or vice versa.
  // Existing selectors live in wizard_store.ts — we just consume them here.
  const sliceStep = store(selectStep);
  const sources = store(selectSources);
  const jobs = store(selectJobs);
  const candidateProfile = store(selectCandidateProfile);
  // Metadata fields (name / description) don't have dedicated selectors yet; they
  // change at most once per wizard session, so a single tiny inline selector is fine.
  const name = store((s) => s.state?.name ?? null);
  const description = store((s) => s.state?.description ?? null);
  const lastCreated = store((s) => s.lastCreatedProfile);
  // The active step is held locally so the operator can move forward/back through the
  // wizard without waiting for the sidecar to ack each transition. The store's
  // `state.step` only overrides on the first state push (initial render) so backend
  // catch-ups don't fight the optimistic local cursor.
  const [activeStep, setActiveStep] = useState<WizardStep>(sliceStep ?? 'name');
  const [hasSyncedInitialStep, setHasSyncedInitialStep] = useState<boolean>(
    sliceStep !== null,
  );
  const [commandError, setCommandError] = useState<string | null>(null);
  // Per-action inflight set tracks WizardCommand types (not action labels) that
  // are currently awaiting an ack. A rapid double-click on the same surface
  // (same command.type) is dropped; different commands run concurrently.
  // Stored in a ref so the guard reads the current value synchronously inside
  // event handlers without waiting for a re-render.
  const inflightCommandsRef = useRef<Set<string>>(new Set());
  const appendOperatorLog = useCockpitStore((s) => s.appendOperatorLog);

  const runWizardCommand = async (
    action: string,
    command: WizardCommand,
  ): Promise<boolean> => {
    // Drop a re-dispatch of the same command type while the previous one is
    // still in flight (LOW finding from review: rapid double-click on Save).
    if (inflightCommandsRef.current.has(command.type)) {
      return false;
    }
    inflightCommandsRef.current.add(command.type);
    setCommandError(null);
    try {
      const ack = await sendWizardCommand(client, command);
      if (!ack.ok) {
        const message = ackErrorMessage(action, ack);
        setCommandError(message);
        // Persist to the cockpit operator log for post-session debug. The UI
        // shows the error to the operator now; the log keeps it discoverable
        // after navigation or remount.
        appendOperatorLog({ level: 'error', message });
        return false;
      }
      return true;
    } catch (error) {
      const message = thrownErrorMessage(action, error);
      setCommandError(message);
      appendOperatorLog({ level: 'error', message });
      return false;
    } finally {
      inflightCommandsRef.current.delete(command.type);
    }
  };

  // Bind WS events into the store + start a wizard session on mount.
  useEffect(() => {
    const unbind = bindWizardClient(client, store);
    void sendWizardCommand(client, { type: 'wizard_start' });
    return () => {
      unbind();
    };
  }, [client, store]);

  // First state push from the sidecar seeds the optimistic step. Subsequent pushes
  // do NOT clobber it (the operator's button clicks drive the cursor).
  useEffect(() => {
    if (sliceStep !== null && !hasSyncedInitialStep) {
      setActiveStep(sliceStep);
      setHasSyncedInitialStep(true);
    }
  }, [sliceStep, hasSyncedInitialStep]);

  // After save, return to the cockpit when we see the profile_created event.
  useEffect(() => {
    if (lastCreated === null) return;
    const go = navigate ?? ((hash: string) => {
      window.location.hash = hash;
    });
    go('/');
    // Clear the last-created marker so re-entering the wizard doesn't re-navigate.
    (store as unknown as { getState: () => WizardStore }).getState().reset();
  }, [lastCreated, navigate, store]);

  const handleCancel = (): void => {
    void sendWizardCommand(client, { type: 'wizard_cancel' });
    setCommandError(null);
    (store as unknown as { getState: () => WizardStore }).getState().reset();
    const go = navigate ?? ((hash: string) => {
      window.location.hash = hash;
    });
    go('/');
  };

  const handleNameSubmit = async (payload: {
    name: string;
    description: string | null;
  }): Promise<void> => {
    // wizard_set_metadata is validation-style: the operator is at a form input
    // and a rejection (e.g., name conflicts with an existing profile) means
    // they need to correct the value. Wait for ack-ok before advancing to the
    // Add step. The new NameStep `commandError` prop renders the rejection
    // text in place so the operator sees what to fix.
    const ok = await runWizardCommand('Set profile metadata', {
      type: 'wizard_set_metadata',
      name: payload.name,
      ...(payload.description === null ? {} : { description: payload.description }),
    });
    if (ok) {
      setActiveStep('add');
    }
  };

  const handleAddSource = (payload: {
    kind: WizardSourceKind;
    mode: WizardSourceMode;
    location: string;
    display_name: string;
  }): Promise<boolean> => {
    return runWizardCommand('Add source', {
      type: 'wizard_add_source',
      kind: payload.kind,
      mode: payload.mode,
      location: payload.location,
      display_name: payload.display_name,
    });
  };

  const handleRemoveSource = (sourceId: string): void => {
    void runWizardCommand('Remove source', {
      type: 'wizard_remove_source',
      source_id: sourceId,
    });
  };

  const handleStartAnalyze = (): void => {
    void runWizardCommand('Run analysis', { type: 'wizard_analyze' });
  };

  const handleRetryAnalysis = (_sourceId: string): void => {
    // For Phase 2, retry simply re-runs the whole analyze pipeline. The backend skips
    // jobs already in 'ok' status. We deliberately ignore the per-source id here — the
    // protocol doesn't include a retry-one command yet.
    void runWizardCommand('Retry analysis', { type: 'wizard_analyze' });
  };

  const handleReview = (): void => {
    // Optimistic transition: jump to the Review step immediately. If the backend
    // rejects `wizard_review`, ReviewStep renders the error via `commandError`.
    setCommandError(null);
    setActiveStep('review');
    void runWizardCommand('Build review', { type: 'wizard_review' });
  };

  const handleSave = (): void => {
    void runWizardCommand('Save profile', { type: 'wizard_save' });
  };

  const goToAdd = (): void => {
    setCommandError(null);
    setActiveStep('add');
  };
  const goToName = (): void => {
    setCommandError(null);
    setActiveStep('name');
  };
  const goToAnalyze = (): void => {
    setCommandError(null);
    setActiveStep('analyze');
  };
  const startAnalyzeFromAdd = (): void => {
    setCommandError(null);
    setActiveStep('analyze');
    void runWizardCommand('Run analysis', { type: 'wizard_analyze' });
  };

  return (
    <div className="wizard-root" data-testid="wizard-root">
      <header className="wizard-header">
        <h1>Create profile</h1>
        <WizardSteps active={activeStep} />
      </header>
      <main className="wizard-main">
        {activeStep === 'name' ? (
          <NameStep
            initialName={name}
            initialDescription={description}
            onSubmit={(payload) => {
              void handleNameSubmit(payload);
            }}
            onCancel={handleCancel}
            commandError={commandError}
          />
        ) : null}
        {activeStep === 'add' ? (
          <AddStep
            sources={sources}
            onAddSource={handleAddSource}
            onRemoveSource={handleRemoveSource}
            onBack={goToName}
            onNext={startAnalyzeFromAdd}
            submitError={commandError}
            {...(openDialog === undefined ? {} : { openDialog })}
          />
        ) : null}
        {activeStep === 'analyze' ? (
          <AnalyzeStep
            sources={sources}
            jobs={jobs}
            onStartAnalyze={handleStartAnalyze}
            onRetry={handleRetryAnalysis}
            onBack={goToAdd}
            onNext={handleReview}
            commandError={commandError}
          />
        ) : null}
        {activeStep === 'review' ? (
          <ReviewStep
            candidate={candidateProfile}
            onBack={goToAnalyze}
            onSave={handleSave}
            commandError={commandError}
          />
        ) : null}
      </main>
    </div>
  );
}
