/**
 * Tests for the Wizard top-level container.
 *
 * Strategy: use an isolated wizard store (created per test) + a hand-rolled fake client
 * that records sent commands and exposes a `fire(event)` helper to push events. We do
 * NOT mock @tauri-apps/plugin-dialog because the Wizard delegates dialog handling to
 * AddStep via an injected `openDialog` (covered exhaustively in AddStep.test.tsx).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

import { Wizard } from '../../src/wizard/Wizard';
import {
  createWizardStore,
  useWizardStore,
  type WizardStore,
} from '../../src/state/wizard_store';
import type {
  AnalysisProgressEvent,
  CandidateProfileModel,
  ProfileCreatedEvent,
  WizardCommand,
  WizardState,
  WizardStateChangedEvent,
} from '../../src/types/wizard_protocol';
import type {
  CockpitClient,
  EventHandler,
  Unsubscribe,
} from '../../src/ws/client';
import type {
  CommandAck,
  Event as ProtocolEvent,
  EventType,
} from '../../src/ws/protocol';

// ---------- Fixtures ----------

const stateName: WizardState = {
  wizard_id: 'wiz_01',
  step: 'name',
  name: null,
  description: null,
  sources: [],
  jobs: [],
  candidate_profile: null,
};

const stateAdd: WizardState = {
  ...stateName,
  step: 'add',
  name: 'buzzi',
};

const stateAnalyze: WizardState = {
  ...stateAdd,
  step: 'analyze',
  sources: [
    {
      source_id: 'src_A',
      kind: 'artist',
      mode: 'reference',
      location: 'Surgeon',
      display_name: 'Surgeon',
      added_at: '2026-05-24T10:00:00Z',
    },
  ],
  jobs: [
    {
      source_id: 'src_A',
      status: 'ok',
      progress: 1,
      error: null,
      extracted_traits: [{ name: 'rolling_low_end', value: 0.8 }],
    },
  ],
};

const candidate: CandidateProfileModel = {
  profile_id: 'wiz_01',
  name: 'buzzi',
  kind: 'user',
  model_version: '1.0.0',
  traits: [{ name: 'rolling_low_end', value: 0.8 }],
  pad_mappings: [{ trait: 'rolling_low_end', pad_id: 1, weight: 0.9 }],
  transition_curve: 'progressive',
  source_summary: '1 source · 13 analyzed signals',
};

const stateReview: WizardState = {
  ...stateAnalyze,
  step: 'review',
  candidate_profile: candidate,
};

// ---------- Fake client ----------

class FakeClient {
  readonly handlers = new Map<string, Set<EventHandler>>();
  readonly sent: WizardCommand[] = [];
  unsubCalls = 0;

  on<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<ProtocolEvent, { type: T }>>,
  ): Unsubscribe {
    const key = eventType as unknown as string;
    let bucket = this.handlers.get(key);
    if (bucket === undefined) {
      bucket = new Set();
      this.handlers.set(key, bucket);
    }
    bucket.add(handler as EventHandler);
    return () => {
      this.unsubCalls += 1;
    };
  }

  send(cmd: WizardCommand): Promise<CommandAck> {
    this.sent.push(cmd);
    return Promise.resolve({ request_id: `req-${this.sent.length}`, ok: true });
  }

  fire(type: string, event: unknown): void {
    const bucket = this.handlers.get(type);
    if (bucket === undefined) return;
    for (const h of bucket) (h as (e: unknown) => void)(event);
  }

  asClient(): CockpitClient {
    return this as unknown as CockpitClient;
  }
}

function renderWizard(args?: {
  store?: ReturnType<typeof createWizardStore>;
  navigate?: (hash: string) => void;
  openDialog?: (mode: 'file' | 'folder') => Promise<string | null>;
}): {
  client: FakeClient;
  store: ReturnType<typeof createWizardStore>;
  navigate: ReturnType<typeof vi.fn>;
} {
  const client = new FakeClient();
  const store = args?.store ?? createWizardStore();
  const navigate = args?.navigate ?? vi.fn<(hash: string) => void>();
  render(
    <Wizard
      client={client.asClient()}
      store={store as unknown as typeof useWizardStore}
      navigate={navigate}
      {...(args?.openDialog === undefined ? {} : { openDialog: args.openDialog })}
    />,
  );
  return { client, store, navigate: navigate as ReturnType<typeof vi.fn> };
}

describe('Wizard container — mount + WS lifecycle', () => {
  beforeEach(() => {
    useWizardStore.getState().reset();
  });
  afterEach(() => {
    useWizardStore.getState().reset();
  });

  it('mounts on the Name step and emits wizard_start once', () => {
    const { client } = renderWizard();
    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-name-step')).toBeInTheDocument();
    expect(client.sent).toContainEqual({ type: 'wizard_start' });
  });

  it('binds three wizard event subscriptions and detaches them on unmount', () => {
    const client = new FakeClient();
    const store = createWizardStore();
    const navigate = vi.fn();
    const { unmount } = render(
      <Wizard
        client={client.asClient()}
        store={store as unknown as typeof useWizardStore}
        navigate={navigate}
      />,
    );
    expect(client.handlers.get('wizard_state_changed')).toBeDefined();
    expect(client.handlers.get('analysis_progress')).toBeDefined();
    expect(client.handlers.get('profile_created')).toBeDefined();
    unmount();
    expect(client.unsubCalls).toBe(3);
  });

  it('reacts to wizard_state_changed by advancing the active step', () => {
    const { client } = renderWizard();
    expect(screen.getByTestId('wizard-name-step')).toBeInTheDocument();
    act(() => {
      client.fire('wizard_state_changed', {
        type: 'wizard_state_changed',
        state: stateAdd,
      } satisfies WizardStateChangedEvent);
    });
    expect(screen.getByTestId('wizard-add-step')).toBeInTheDocument();
  });

  it('falls back to setting window.location.hash when no navigate prop is provided', () => {
    // Use the singleton store so we can drive a profile_created.
    const client = new FakeClient();
    render(<Wizard client={client.asClient()} />);
    // Establish a wizard state first.
    act(() => {
      client.fire('wizard_state_changed', {
        type: 'wizard_state_changed',
        state: stateReview,
      } satisfies WizardStateChangedEvent);
    });
    const originalHash = window.location.hash;
    act(() => {
      client.fire('profile_created', {
        type: 'profile_created',
        profile: candidate,
      } satisfies ProfileCreatedEvent);
    });
    expect(window.location.hash).toBe('#/');
    // Restore.
    window.location.hash = originalHash;
  });
});

describe('Wizard container — step handlers', () => {
  it('NameStep submit → sends wizard_set_metadata with name + description', () => {
    const { client } = renderWizard();
    fireEvent.change(screen.getByTestId('wizard-name-input'), {
      target: { value: 'buzzi' },
    });
    fireEvent.change(screen.getByTestId('wizard-description-input'), {
      target: { value: 'industrial drone' },
    });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(client.sent).toContainEqual({
      type: 'wizard_set_metadata',
      name: 'buzzi',
      description: 'industrial drone',
    });
  });

  it('NameStep submit omits description when blank', () => {
    const { client } = renderWizard();
    fireEvent.change(screen.getByTestId('wizard-name-input'), {
      target: { value: 'buzzi' },
    });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(client.sent).toContainEqual({ type: 'wizard_set_metadata', name: 'buzzi' });
  });

  it('NameStep cancel → emits wizard_cancel and navigates back to /', () => {
    const navigate = vi.fn();
    const { client } = renderWizard({ navigate });
    fireEvent.click(screen.getByTestId('wizard-cancel'));
    expect(client.sent).toContainEqual({ type: 'wizard_cancel' });
    expect(navigate).toHaveBeenCalledWith('/');
  });

  it('NameStep cancel clears local wizard draft state before returning to cockpit', () => {
    const navigate = vi.fn();
    const store = createWizardStore();
    store.getState().handleEvent({
      type: 'wizard_state_changed',
      state: { ...stateName, name: 'to-be-cancelled' },
    });
    renderWizard({ store, navigate });
    expect(screen.getByTestId('wizard-name-input')).toHaveValue('to-be-cancelled');
    fireEvent.click(screen.getByTestId('wizard-cancel'));
    expect(store.getState().state).toBeNull();
    expect(navigate).toHaveBeenCalledWith('/');
  });

  it('NameStep cancel falls back to window.location.hash when navigate prop omitted', () => {
    const client = new FakeClient();
    render(<Wizard client={client.asClient()} />);
    const originalHash = window.location.hash;
    fireEvent.click(screen.getByTestId('wizard-cancel'));
    expect(window.location.hash).toBe('#/');
    window.location.hash = originalHash;
  });

  it('AddStep handlers forward add/remove/back/next correctly', () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAdd });
    const { client } = renderWizard({ store });
    expect(screen.getByTestId('wizard-add-step')).toBeInTheDocument();

    // Add a source via the draft flow.
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: 'Surgeon' },
    });
    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: 'Surgeon' },
    });
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    expect(client.sent).toContainEqual({
      type: 'wizard_add_source',
      kind: 'artist',
      mode: 'reference',
      location: 'Surgeon',
      display_name: 'Surgeon',
    });

    // Push a state with a source so we can exercise remove.
    act(() => {
      client.fire('wizard_state_changed', {
        type: 'wizard_state_changed',
        state: stateAnalyze, // has src_A
      } satisfies WizardStateChangedEvent);
    });
    // Back to add step for remove (state.step is analyze; switch via optimistic).
    // Easier: push a state with sources but step=add.
    act(() => {
      client.fire('wizard_state_changed', {
        type: 'wizard_state_changed',
        state: { ...stateAnalyze, step: 'add' },
      } satisfies WizardStateChangedEvent);
    });
    fireEvent.click(screen.getByTestId('wizard-source-remove-src_A'));
    expect(client.sent).toContainEqual({
      type: 'wizard_remove_source',
      source_id: 'src_A',
    });

    // Back goes to name (optimistic).
    fireEvent.click(screen.getByTestId('wizard-back'));
    expect(screen.getByTestId('wizard-name-step')).toBeInTheDocument();
  });

  it('AddStep next button advances to analyze and starts analysis immediately', () => {
    const store = createWizardStore();
    store.getState().handleEvent({
      type: 'wizard_state_changed',
      state: { ...stateAnalyze, step: 'add' },
    });
    const { client } = renderWizard({ store });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(screen.getByTestId('wizard-analyze-step')).toBeInTheDocument();
    expect(client.sent).toContainEqual({ type: 'wizard_analyze' });
  });

  it('AddStep forwards an injected openDialog prop into AddStep', async () => {
    const openDialog = vi.fn().mockResolvedValue('/p/k.syx');
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAdd });
    renderWizard({ store, openDialog });
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-draft-browse'));
    });
    expect(openDialog).toHaveBeenCalledWith('file');
  });

  it('AnalyzeStep: Run analysis emits wizard_analyze; Retry also emits wizard_analyze', () => {
    const store = createWizardStore();
    store.getState().handleEvent({
      type: 'wizard_state_changed',
      state: {
        ...stateAnalyze,
        jobs: [{ ...stateAnalyze.jobs[0]!, status: 'failed', error: 'boom' }],
      },
    });
    const { client } = renderWizard({ store });
    fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    fireEvent.click(screen.getByTestId('wizard-job-retry-src_A'));
    expect(client.sent.filter((c) => c.type === 'wizard_analyze')).toHaveLength(2);
  });

  it('AnalyzeStep: Review emits wizard_review and optimistically jumps to review', () => {
    const store = createWizardStore();
    store
      .getState()
      .handleEvent({ type: 'wizard_state_changed', state: stateAnalyze });
    const { client } = renderWizard({ store });
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(client.sent).toContainEqual({ type: 'wizard_review' });
    expect(screen.getByTestId('wizard-review-step')).toBeInTheDocument();
  });

  it('AnalyzeStep: Back returns to the Add step', () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAnalyze });
    renderWizard({ store });
    fireEvent.click(screen.getByTestId('wizard-back'));
    expect(screen.getByTestId('wizard-add-step')).toBeInTheDocument();
  });

  it('analysis_progress updates the visible progress bar', () => {
    const store = createWizardStore();
    store.getState().handleEvent({
      type: 'wizard_state_changed',
      state: { ...stateAnalyze, jobs: [{ ...stateAnalyze.jobs[0]!, progress: 0, status: 'pending' }] },
    });
    const { client } = renderWizard({ store });
    expect(screen.getByTestId('wizard-progress-src_A')).toHaveAttribute('aria-valuenow', '0');
    act(() => {
      client.fire('analysis_progress', {
        type: 'analysis_progress',
        job: {
          source_id: 'src_A',
          status: 'analyzing',
          progress: 0.4,
          error: null,
          extracted_traits: [],
        },
      } satisfies AnalysisProgressEvent);
    });
    expect(screen.getByTestId('wizard-progress-src_A')).toHaveAttribute('aria-valuenow', '40');
  });

  it('ReviewStep: Save emits wizard_save; profile_created then navigates back', () => {
    const navigate = vi.fn();
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateReview });
    const { client } = renderWizard({ store, navigate });
    fireEvent.click(screen.getByTestId('wizard-save'));
    expect(client.sent).toContainEqual({ type: 'wizard_save' });
    act(() => {
      client.fire('profile_created', {
        type: 'profile_created',
        profile: candidate,
      } satisfies ProfileCreatedEvent);
    });
    expect(navigate).toHaveBeenCalledWith('/');
    // Reset clears the slice so re-entry doesn't re-navigate.
    expect((store.getState() as WizardStore).lastCreatedProfile).toBeNull();
  });

  it('ReviewStep: Back returns to the Analyze step', () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateReview });
    renderWizard({ store });
    fireEvent.click(screen.getByTestId('wizard-back'));
    expect(screen.getByTestId('wizard-analyze-step')).toBeInTheDocument();
  });
});
