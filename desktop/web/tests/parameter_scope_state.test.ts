import { describe, expect, it } from 'vitest';

import { bindClientToStore, createCockpitStore, selectCanSend } from '../src/state';
import { candidate, FakeCockpitClient, patchGenome, readyDualMachineStage, sendPlan, sessionLive } from './cockpit/_fixtures';
import { parameterEvent } from './cockpit/parameterScopeFixture';

describe('parameter scope state authority', () => {
  it('applies whole authoritative state and clears every stale derivation when selection changes', () => {
    const store = createCockpitStore();
    store.getState().setPreviewCandidate(candidate);
    store.getState().setSendPlan(sendPlan);
    store.getState().setPatchGenome(patchGenome);
    const client = new FakeCockpitClient();
    const unbind = bindClientToStore(client.asClient(), store);
    client.emitEvent(parameterEvent);
    expect(store.getState().parameterControls).toEqual(parameterEvent.controls);
    expect(store.getState().rytmParameters).toBeNull();
    expect(store.getState().a4Parameters).toEqual([]);
    expect(store.getState().previewCandidate).toBeNull();
    expect(store.getState().sendPlan).toBeNull();
    expect(store.getState().patchGenomeStale).toBe(true);
    unbind();
  });
  it('recognizes equivalent explicit selections without losing an independently current candidate', () => {
    const store = createCockpitStore();
    const cells = [{ item_id: 1, parameter_key: 'flt' }, { item_id: 2, parameter_key: 'amp_decay' }];
    store.getState().setMutationParameters({ ...parameterEvent, rytm_parameters: cells });
    store.getState().setPreviewCandidate(candidate);
    store.getState().setMutationParameters({ ...parameterEvent, rytm_parameters: [...cells].reverse() });
    expect(store.getState().previewCandidate).toBe(candidate);
    store.getState().setMutationParameters({ ...parameterEvent, rytm_parameters: [{ item_id: 1, parameter_key: 'flt' }] });
    expect(store.getState().previewCandidate).toBeNull();
    store.getState().setMutationParameters({ ...parameterEvent, rytm_parameters: [{ item_id: 1, parameter_key: 'amp_decay' }] });
    expect(store.getState().rytmParameters).toEqual([{ item_id: 1, parameter_key: 'amp_decay' }]);
  });
  it('refreshes metadata fail-closed while retaining offline values that remain source-bound', () => {
    const store = createCockpitStore();
    store.getState().setMutationParameters({ ...parameterEvent, a4_parameters: null });
    store.getState().setConnectionStatus('connected');
    store.getState().setDualMachineStage(readyDualMachineStage);
    store.getState().setPreviewCandidate(candidate);
    store.getState().setSendPlan(sendPlan);
    store.getState().invalidateParameterMetadata();
    expect(store.getState().parameterControls).toEqual([]);
    expect(store.getState().mutationParametersReady).toBe(false);
    expect(selectCanSend(store.getState())).toBe(false);
    expect(store.getState().previewCandidate).toBe(candidate);
    store.getState().setMutationParameters({ ...parameterEvent, a4_parameters: null });
    expect(store.getState().parameterMetadataRefreshing).toBe(false);
  });
  it('revokes local recall authority without reading or applying stored metadata', () => {
    const store = createCockpitStore();
    store.getState().setSessionStatus(sessionLive);
    store.getState().setPatchGenome(patchGenome);
    store.getState().invalidateMutationContext(true);
    expect(store.getState().sessionStatusStale).toBe(true);
    expect(store.getState().patchGenomeStale).toBe(true);
    expect(store.getState().sendPlan).toBeNull();
    expect(store.getState().sessionStatus?.armed).toBe(true); // no invented hardware observation
  });
});
