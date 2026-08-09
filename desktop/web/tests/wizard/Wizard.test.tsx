/**
 * Tests for the Wizard top-level container.
 *
 * Strategy: use an isolated wizard store (created per test) + a hand-rolled fake client
 * that records sent commands and exposes a `fire(event)` helper to push events. We do
 * NOT mock @tauri-apps/plugin-dialog because the Wizard delegates dialog handling to
 * AddStep via an injected `openDialog` (covered exhaustively in AddStep.test.tsx).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

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
  ConnectionStatus,
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
  readonly ackQueue: CommandAck[] = [];
  readonly rejectionQueue: unknown[] = [];
  readonly sent: WizardCommand[] = [];
  readonly statusHandlers = new Set<(status: ConnectionStatus) => void>();
  status: ConnectionStatus = 'connected';
  unsubCalls = 0;
  statusUnsubCalls = 0;

  getStatus(): ConnectionStatus {
    return this.status;
  }

  onStatusChange(handler: (status: ConnectionStatus) => void): Unsubscribe {
    this.statusHandlers.add(handler);
    return () => {
      this.statusHandlers.delete(handler);
      this.statusUnsubCalls += 1;
    };
  }

  /** Test helper: change the reported status and notify subscribers. */
  setStatus(status: ConnectionStatus): void {
    this.status = status;
    for (const handler of this.statusHandlers) handler(status);
  }

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
    if (this.rejectionQueue.length > 0) {
      return Promise.reject(this.rejectionQueue.shift());
    }
    return Promise.resolve(
      this.ackQueue.shift() ?? { request_id: `req-${this.sent.length}`, ok: true },
    );
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

  it('mounts OFFLINE and defers wizard_start to the first connected transition', () => {
    const client = new FakeClient();
    client.status = 'reconnecting';
    const store = createWizardStore();
    render(
      <Wizard
        client={client.asClient()}
        store={store as unknown as typeof useWizardStore}
        navigate={vi.fn()}
      />,
    );

    // The wizard UI is fully mounted with no sidecar; nothing was sent yet.
    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
    expect(client.sent).toEqual([]);

    // A non-connected transition is ignored…
    act(() => client.setStatus('closed'));
    expect(client.sent).toEqual([]);

    // …the first connected transition starts the session, exactly once.
    act(() => client.setStatus('connected'));
    expect(client.sent).toEqual([{ type: 'wizard_start' }]);
    act(() => client.setStatus('reconnecting'));
    act(() => client.setStatus('connected'));
    expect(client.sent).toEqual([{ type: 'wizard_start' }]);
  });

  it('unmounting before the sidecar connects detaches the deferred start', () => {
    const client = new FakeClient();
    client.status = 'connecting';
    const store = createWizardStore();
    const { unmount } = render(
      <Wizard
        client={client.asClient()}
        store={store as unknown as typeof useWizardStore}
        navigate={vi.fn()}
      />,
    );
    unmount();
    expect(client.statusUnsubCalls).toBe(1);

    client.setStatus('connected');
    expect(client.sent).toEqual([]);
  });

  it('swallows a wizard_start rejection (offline race) without crashing the surface', async () => {
    const client = new FakeClient();
    client.rejectionQueue.push(new Error('socket not open'));
    const store = createWizardStore();
    render(
      <Wizard
        client={client.asClient()}
        store={store as unknown as typeof useWizardStore}
        navigate={vi.fn()}
      />,
    );
    await act(async () => {
      await Promise.resolve();
    });
    expect(client.sent).toEqual([{ type: 'wizard_start' }]);
    expect(screen.getByTestId('wizard-root')).toBeInTheDocument();
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

  it('NameStep cancel still resets + navigates when wizard_cancel cannot be sent (offline)', async () => {
    const navigate = vi.fn();
    const { client, store } = renderWizard({ navigate });
    client.rejectionQueue.push(new Error('socket not open'));
    fireEvent.click(screen.getByTestId('wizard-cancel'));
    await act(async () => {
      await Promise.resolve();
    });
    expect(client.sent).toContainEqual({ type: 'wizard_cancel' });
    expect(store.getState().state).toBeNull();
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

  it('AddStep keeps the draft open and surfaces a rejected add-source ack', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAdd });
    const { client } = renderWizard({ store });
    client.ackQueue.push({
      request_id: 'reject-add-source',
      ok: false,
      error: 'source path rejected by policy',
    });

    fireEvent.click(screen.getByTestId('wizard-add-song'));
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: 'C:\\Users\\Jose Buzzi\\Downloads\\The Bells.wav' },
    });
    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: 'The Bells' },
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        'source path rejected by policy',
      );
    });
    expect(screen.getByTestId('wizard-draft')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-draft-location')).toHaveFocus();
  });

  it('AnalyzeStep: Run analysis emits wizard_analyze; Retry also emits wizard_analyze', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({
      type: 'wizard_state_changed',
      state: {
        ...stateAnalyze,
        jobs: [{ ...stateAnalyze.jobs[0]!, status: 'failed', error: 'boom' }],
      },
    });
    const { client } = renderWizard({ store });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    });
    // Yield to let the first command's microtask resolve so the per-command
    // inflight guard releases before the retry click. Without this await, the
    // retry would be dropped — which is the LOW double-dispatch protection.
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-job-retry-src_A'));
    });
    expect(client.sent.filter((c) => c.type === 'wizard_analyze')).toHaveLength(2);
  });

  it('AnalyzeStep surfaces a rejected run-analysis ack without leaving the step', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAnalyze });
    const { client } = renderWizard({ store });
    client.ackQueue.push({
      request_id: 'reject-analyze',
      ok: false,
      error: 'no active wizard session',
    });

    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('wizard-command-error')).toHaveTextContent(
        'no active wizard session',
      );
    });
    expect(screen.getByTestId('wizard-analyze-step')).toBeInTheDocument();
  });

  it('AnalyzeStep surfaces socket send failures with useful fallbacks', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAnalyze });
    const { client } = renderWizard({ store });

    client.rejectionQueue.push(new Error('socket closed'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-command-error')).toHaveTextContent(
        'socket closed',
      );
    });

    client.rejectionQueue.push(null);
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-command-error')).toHaveTextContent(
        'connection unavailable',
      );
    });
  });

  it('AnalyzeStep falls back to ack codes and generic rejection text', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAnalyze });
    const { client } = renderWizard({ store });

    client.ackQueue.push({
      request_id: 'reject-analyze-code',
      ok: false,
      code: 'wizard_source_path_rejected',
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-command-error')).toHaveTextContent(
        'wizard_source_path_rejected',
      );
    });

    client.ackQueue.push({
      request_id: 'reject-analyze-generic',
      ok: false,
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-analyze-start'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-command-error')).toHaveTextContent(
        'command rejected',
      );
    });
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

  it('NameStep: rejected wizard_set_metadata renders an alert and keeps the operator on the Name step', async () => {
    const { client } = renderWizard();
    client.ackQueue.push({
      request_id: 'reject-set-metadata',
      ok: false,
      error: 'name conflicts with existing profile',
    });
    fireEvent.change(screen.getByTestId('wizard-name-input'), {
      target: { value: 'buzzi' },
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-next'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-name-command-error')).toHaveTextContent(
        'name conflicts with existing profile',
      );
    });
    expect(screen.getByTestId('wizard-name-step')).toBeInTheDocument();
  });

  it('NameStep: rejected wizard_set_metadata via thrown send error surfaces the fallback message', async () => {
    const { client } = renderWizard();
    client.rejectionQueue.push(new Error('socket closed'));
    fireEvent.change(screen.getByTestId('wizard-name-input'), {
      target: { value: 'buzzi' },
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-next'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-name-command-error')).toHaveTextContent(
        'socket closed',
      );
    });
    expect(screen.getByTestId('wizard-name-step')).toBeInTheDocument();
  });

  it('AnalyzeStep: rejected wizard_review surfaces on the optimistically-mounted ReviewStep', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateAnalyze });
    const { client } = renderWizard({ store });
    client.ackQueue.push({
      request_id: 'reject-review',
      ok: false,
      error: 'candidate not buildable',
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-next'));
    });
    // Optimistic nav already happened; the ReviewStep is mounted and renders
    // the rejection via its commandError prop (its candidate is non-null from
    // the seeded stateAnalyze, but the same path holds for a null candidate
    // — verified by the empty-state branch in ReviewStep.tsx).
    await waitFor(() => {
      expect(screen.getByTestId('wizard-review-error')).toHaveTextContent(
        'candidate not buildable',
      );
    });
    expect(screen.getByTestId('wizard-review-step')).toBeInTheDocument();
  });

  it('ReviewStep: rejected wizard_save renders an alert and does NOT navigate', async () => {
    const navigate = vi.fn();
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateReview });
    const { client } = renderWizard({ store, navigate });
    client.ackQueue.push({
      request_id: 'reject-save',
      ok: false,
      error: 'profile registry refused write',
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-save'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-review-error')).toHaveTextContent(
        'profile registry refused write',
      );
    });
    expect(navigate).not.toHaveBeenCalled();
    expect(screen.getByTestId('wizard-review-step')).toBeInTheDocument();
  });

  it('ReviewStep: rejected wizard_save via thrown send error surfaces the fallback message', async () => {
    const navigate = vi.fn();
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateReview });
    const { client } = renderWizard({ store, navigate });
    client.rejectionQueue.push(new Error('socket closed'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-save'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-review-error')).toHaveTextContent(
        'socket closed',
      );
    });
    expect(navigate).not.toHaveBeenCalled();
  });

  it('AddStep: rejected wizard_remove_source renders a panel-level alert and keeps the source visible', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({
      type: 'wizard_state_changed',
      state: { ...stateAnalyze, step: 'add' },
    });
    const { client } = renderWizard({ store });
    client.ackQueue.push({
      request_id: 'reject-remove-source',
      ok: false,
      error: 'source is locked',
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-source-remove-src_A'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('wizard-add-panel-error')).toHaveTextContent(
        'source is locked',
      );
    });
    expect(screen.getByTestId('wizard-add-step')).toBeInTheDocument();
  });

  it('rapid double-click on Save dispatches wizard_save exactly once (inflight guard)', async () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: stateReview });
    const { client } = renderWizard({ store });
    // First click starts an in-flight save; the FakeClient default ack does not resolve
    // until the microtask queue drains. The second click within the same synchronous
    // batch must be dropped by the inflight guard.
    fireEvent.click(screen.getByTestId('wizard-save'));
    fireEvent.click(screen.getByTestId('wizard-save'));
    await act(async () => {
      await Promise.resolve();
    });
    const saveCalls = client.sent.filter((c) => c.type === 'wizard_save');
    expect(saveCalls).toHaveLength(1);
  });
});
