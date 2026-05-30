/**
 * Tests for the wizard zustand store + `bindWizardClient` + `sendWizardCommand` +
 * `isWizardEvent` type guard. 100% branch coverage on:
 *   - src/state/wizard_store.ts
 *   - src/types/wizard_protocol.ts
 */

import { describe, expect, it, vi } from 'vitest';

import {
  bindWizardClient,
  createWizardStore,
  INITIAL_WIZARD_STATE,
  selectAnalysisComplete,
  selectCandidateProfile,
  selectIsWizardActive,
  selectJobs,
  selectSources,
  selectStep,
  sendWizardCommand,
  useWizardStore,
  type WizardStore,
} from '../../src/state/wizard_store';
import {
  isWizardEvent,
  type AnalysisJob,
  type AnalysisProgressEvent,
  type CandidateProfileModel,
  type InspirationSource,
  type ProfileCreatedEvent,
  type WizardCommand,
  type WizardEvent,
  type WizardState,
  type WizardStateChangedEvent,
} from '../../src/types/wizard_protocol';
import type {
  CockpitClient,
  EventHandler,
  Unsubscribe,
} from '../../src/ws/client';
import type { Event as ProtocolEvent, EventType } from '../../src/ws/protocol';

// ---------- Fixtures ----------

const source: InspirationSource = {
  source_id: 'src_01',
  kind: 'artist',
  mode: 'reference',
  location: 'Surgeon',
  display_name: 'Surgeon',
  added_at: '2026-05-24T10:00:00Z',
};

const source2: InspirationSource = {
  source_id: 'src_02',
  kind: 'kit',
  mode: 'file',
  location: '/tmp/kit.syx',
  display_name: 'kit.syx',
  added_at: '2026-05-24T10:01:00Z',
};

const job: AnalysisJob = {
  source_id: 'src_01',
  status: 'pending',
  progress: 0,
  error: null,
  extracted_traits: [],
};

const job2: AnalysisJob = {
  source_id: 'src_02',
  status: 'pending',
  progress: 0,
  error: null,
  extracted_traits: [],
};

const candidate: CandidateProfileModel = {
  profile_id: 'wiz_01',
  name: 'buzzi',
  kind: 'user',
  model_version: '1.0.0',
  traits: [{ name: 'rolling_low_end', value: 0.8 }],
  pad_mappings: [{ trait: 'rolling_low_end', pad_id: 1, weight: 0.9 }],
  transition_curve: 'progressive',
  source_summary: '2 sources · 13 analyzed signals',
};

const wizardState: WizardState = {
  wizard_id: 'wiz_01',
  step: 'name',
  name: null,
  description: null,
  sources: [source, source2],
  jobs: [job, job2],
  candidate_profile: null,
};

// ---------- Store: initial state + reset ----------

describe('wizard store — initial state and reset', () => {
  it('exposes INITIAL_WIZARD_STATE matching the slice shape', () => {
    expect(INITIAL_WIZARD_STATE).toEqual({ state: null, lastCreatedProfile: null });
  });

  it('starts in the initial-wizard state', () => {
    const store = createWizardStore();
    expect(store.getState().state).toBeNull();
    expect(store.getState().lastCreatedProfile).toBeNull();
  });

  it('reset() returns to the initial state', () => {
    const store = createWizardStore();
    store.getState().handleEvent({ type: 'wizard_state_changed', state: wizardState });
    store.getState().handleEvent({ type: 'profile_created', profile: candidate });
    expect(store.getState().state).not.toBeNull();
    expect(store.getState().lastCreatedProfile).not.toBeNull();
    store.getState().reset();
    expect(store.getState().state).toBeNull();
    expect(store.getState().lastCreatedProfile).toBeNull();
  });

  it('singleton useWizardStore is a real zustand store', () => {
    expect(typeof useWizardStore.getState).toBe('function');
    expect(typeof useWizardStore.setState).toBe('function');
    expect(typeof useWizardStore.subscribe).toBe('function');
  });
});

// ---------- Store: handleEvent reducer (every branch) ----------

describe('wizard store — handleEvent reducer', () => {
  it('wizard_state_changed replaces the whole state slice', () => {
    const store = createWizardStore();
    const event: WizardStateChangedEvent = { type: 'wizard_state_changed', state: wizardState };
    store.getState().handleEvent(event);
    expect(store.getState().state).toEqual(wizardState);
  });

  it('analysis_progress with no state is a no-op (guard branch)', () => {
    const store = createWizardStore();
    const event: AnalysisProgressEvent = {
      type: 'analysis_progress',
      job: {
        source_id: 'src_01',
        status: 'analyzing',
        progress: 0.5,
        error: null,
        extracted_traits: [],
      },
    };
    store.getState().handleEvent(event);
    expect(store.getState().state).toBeNull();
  });

  it('analysis_progress updates the matching job in place (mapping branch — match)', () => {
    const store = createWizardStore();
    store
      .getState()
      .handleEvent({ type: 'wizard_state_changed', state: wizardState });
    store.getState().handleEvent({
      type: 'analysis_progress',
      job: {
        source_id: 'src_01',
        status: 'analyzing',
        progress: 0.65,
        error: null,
        extracted_traits: [],
      },
    });
    const updated = store.getState().state;
    expect(updated).not.toBeNull();
    if (updated === null) throw new Error('expected state');
    const updatedJob = updated.jobs.find((j) => j.source_id === 'src_01');
    expect(updatedJob?.progress).toBe(0.65);
    expect(updatedJob?.status).toBe('analyzing');
    const otherJob = updated.jobs.find((j) => j.source_id === 'src_02');
    expect(otherJob).toEqual(job2);
  });

  it('analysis_progress propagates extracted_traits + error from the nested job', () => {
    const store = createWizardStore();
    store
      .getState()
      .handleEvent({ type: 'wizard_state_changed', state: wizardState });
    store.getState().handleEvent({
      type: 'analysis_progress',
      job: {
        source_id: 'src_01',
        status: 'ok',
        progress: 1.0,
        error: null,
        extracted_traits: [{ name: 'rolling_low_end', value: 0.8 }],
      },
    });
    const updated = store.getState().state;
    if (updated === null) throw new Error('expected state');
    const updatedJob = updated.jobs.find((j) => j.source_id === 'src_01');
    expect(updatedJob?.status).toBe('ok');
    expect(updatedJob?.extracted_traits).toEqual([
      { name: 'rolling_low_end', value: 0.8 },
    ]);
  });

  it('analysis_progress for an unknown source_id leaves jobs untouched (mapping branch — no match)', () => {
    const store = createWizardStore();
    store
      .getState()
      .handleEvent({ type: 'wizard_state_changed', state: wizardState });
    store.getState().handleEvent({
      type: 'analysis_progress',
      job: {
        source_id: 'src_99',
        status: 'ok',
        progress: 1.0,
        error: null,
        extracted_traits: [],
      },
    });
    const updated = store.getState().state;
    expect(updated?.jobs).toEqual([job, job2]);
  });

  it('profile_created writes lastCreatedProfile', () => {
    const store = createWizardStore();
    const event: ProfileCreatedEvent = { type: 'profile_created', profile: candidate };
    store.getState().handleEvent(event);
    expect(store.getState().lastCreatedProfile).toEqual(candidate);
  });
});

// ---------- Store: selectors ----------

describe('wizard store — selectors', () => {
  it('selectStep returns null when no state, else the active step', () => {
    expect(selectStep({ ...INITIAL_WIZARD_STATE })).toBeNull();
    expect(selectStep({ ...INITIAL_WIZARD_STATE, state: wizardState })).toBe('name');
  });

  it('selectSources returns [] when no state, else the sources array', () => {
    expect(selectSources({ ...INITIAL_WIZARD_STATE })).toEqual([]);
    expect(selectSources({ ...INITIAL_WIZARD_STATE, state: wizardState })).toEqual([
      source,
      source2,
    ]);
  });

  it('selectJobs returns [] when no state, else the jobs array', () => {
    expect(selectJobs({ ...INITIAL_WIZARD_STATE })).toEqual([]);
    expect(selectJobs({ ...INITIAL_WIZARD_STATE, state: wizardState })).toEqual([job, job2]);
  });

  it('selectCandidateProfile returns null when no state or no candidate, else the candidate', () => {
    expect(selectCandidateProfile({ ...INITIAL_WIZARD_STATE })).toBeNull();
    expect(
      selectCandidateProfile({ ...INITIAL_WIZARD_STATE, state: wizardState }),
    ).toBeNull();
    expect(
      selectCandidateProfile({
        ...INITIAL_WIZARD_STATE,
        state: { ...wizardState, candidate_profile: candidate },
      }),
    ).toEqual(candidate);
  });

  it('selectIsWizardActive is true once state is set', () => {
    expect(selectIsWizardActive({ ...INITIAL_WIZARD_STATE })).toBe(false);
    expect(selectIsWizardActive({ ...INITIAL_WIZARD_STATE, state: wizardState })).toBe(true);
  });

  it('selectAnalysisComplete: no jobs → false', () => {
    expect(selectAnalysisComplete({ ...INITIAL_WIZARD_STATE })).toBe(false);
    expect(
      selectAnalysisComplete({
        ...INITIAL_WIZARD_STATE,
        state: { ...wizardState, jobs: [] },
      }),
    ).toBe(false);
  });

  it('selectAnalysisComplete: any non-terminal job → false', () => {
    expect(
      selectAnalysisComplete({
        ...INITIAL_WIZARD_STATE,
        state: {
          ...wizardState,
          jobs: [
            { ...job, status: 'ok' },
            { ...job2, status: 'analyzing' },
          ],
        },
      }),
    ).toBe(false);
  });

  it('selectAnalysisComplete: all terminal → true', () => {
    expect(
      selectAnalysisComplete({
        ...INITIAL_WIZARD_STATE,
        state: {
          ...wizardState,
          jobs: [
            { ...job, status: 'ok' },
            { ...job2, status: 'failed', error: 'boom' },
          ],
        },
      }),
    ).toBe(true);
  });
});

// ---------- Type guard: isWizardEvent (every branch) ----------

describe('isWizardEvent type guard', () => {
  it('null → false', () => {
    expect(isWizardEvent(null)).toBe(false);
  });

  it('non-object (string) → false', () => {
    expect(isWizardEvent('not-an-event')).toBe(false);
  });

  it('object without type → false', () => {
    expect(isWizardEvent({ payload: 1 })).toBe(false);
  });

  it('object with unknown type → false', () => {
    expect(isWizardEvent({ type: 'something_else' })).toBe(false);
  });

  it('each known wizard event type → true', () => {
    expect(isWizardEvent({ type: 'wizard_state_changed', state: wizardState })).toBe(true);
    expect(
      isWizardEvent({
        type: 'analysis_progress',
        job: {
          source_id: 'src_01',
          status: 'analyzing',
          progress: 0.5,
          error: null,
          extracted_traits: [],
        },
      }),
    ).toBe(true);
    expect(isWizardEvent({ type: 'profile_created', profile: candidate })).toBe(true);
  });
});

// ---------- Binding: bindWizardClient ----------

class FakeClient {
  readonly handlers = new Map<string, Set<EventHandler>>();
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

  fire(type: string, event: unknown): void {
    const bucket = this.handlers.get(type);
    if (bucket === undefined) return;
    for (const h of bucket) (h as (e: unknown) => void)(event);
  }
}

describe('bindWizardClient', () => {
  it('routes the three wizard events into the store and detaches all on unsub', () => {
    const store = createWizardStore();
    const client = new FakeClient();
    const unbind = bindWizardClient(client as unknown as CockpitClient, store);

    expect(client.handlers.get('wizard_state_changed')).toBeDefined();
    expect(client.handlers.get('analysis_progress')).toBeDefined();
    expect(client.handlers.get('profile_created')).toBeDefined();

    client.fire('wizard_state_changed', {
      type: 'wizard_state_changed',
      state: wizardState,
    } satisfies WizardStateChangedEvent);
    expect(store.getState().state).toEqual(wizardState);

    client.fire('analysis_progress', {
      type: 'analysis_progress',
      job: {
        source_id: 'src_01',
        status: 'analyzing',
        progress: 0.5,
        error: null,
        extracted_traits: [],
      },
    } satisfies AnalysisProgressEvent);
    const after = store.getState().state;
    if (after === null) throw new Error('expected state');
    expect(after.jobs[0]?.progress).toBe(0.5);

    client.fire('profile_created', {
      type: 'profile_created',
      profile: candidate,
    } satisfies ProfileCreatedEvent);
    expect(store.getState().lastCreatedProfile).toEqual(candidate);

    unbind();
    expect(client.unsubCalls).toBe(3);
  });

  it('falls back to the singleton useWizardStore when no store override provided', () => {
    const client = new FakeClient();
    useWizardStore.getState().reset();
    const unbind = bindWizardClient(client as unknown as CockpitClient);
    client.fire('wizard_state_changed', {
      type: 'wizard_state_changed',
      state: wizardState,
    });
    expect(useWizardStore.getState().state).toEqual(wizardState);
    unbind();
    useWizardStore.getState().reset();
  });
});

// ---------- sendWizardCommand passthrough ----------

describe('sendWizardCommand', () => {
  it('forwards the command verbatim to the client and returns its promise', async () => {
    const send = vi.fn().mockResolvedValue({ request_id: 'r1', ok: true });
    const fakeClient = { send } as unknown as CockpitClient;
    const cmd: WizardCommand = { type: 'wizard_start' };
    const result = await sendWizardCommand(fakeClient, cmd);
    expect(send).toHaveBeenCalledWith(cmd);
    expect(result).toEqual({ request_id: 'r1', ok: true });
  });

  it('forwards every wizard command shape (type-coverage exercise)', () => {
    const send = vi.fn().mockResolvedValue({ request_id: 'r', ok: true });
    const fakeClient = { send } as unknown as CockpitClient;
    const commands: WizardCommand[] = [
      { type: 'wizard_start' },
      { type: 'wizard_set_metadata', name: 'x', description: 'd' },
      {
        type: 'wizard_add_source',
        kind: 'kit',
        mode: 'file',
        location: '/a',
        display_name: 'a',
      },
      { type: 'wizard_remove_source', source_id: 's1' },
      { type: 'wizard_analyze' },
      { type: 'wizard_review' },
      { type: 'wizard_save' },
      { type: 'wizard_cancel' },
    ];
    for (const cmd of commands) sendWizardCommand(fakeClient, cmd);
    expect(send).toHaveBeenCalledTimes(commands.length);
  });
});

// Compile-time sanity: store satisfies its actions interface.
const _typeProbe: WizardStore = createWizardStore().getState();
void _typeProbe;

// Compile-time sanity: every wizard event narrows through the union.
function _eventUnion(_e: WizardEvent): void {
  /* no-op */
}
void _eventUnion;
