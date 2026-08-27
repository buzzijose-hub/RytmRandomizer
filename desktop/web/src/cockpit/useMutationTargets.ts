/** Shared explicit mutation include-list state for Rytm pads and A4 tracks. */

import { useCallback, useMemo, useRef } from 'react';

import { useCockpitStore } from '../state';

import { useCockpitClient } from './context';
import { RYTM_DEVICE_ID, type CockpitDeviceId } from './devices';

export interface MutationTargetsApi {
  targets: ReadonlySet<number>;
  hasExplicitTargets: boolean;
  isTargeted: (id: number) => boolean;
  toggleTarget: (id: number) => void;
  clearTargets: () => void;
}

export function useMutationTargets(deviceId: CockpitDeviceId): MutationTargetsApi {
  const client = useCockpitClient();
  const appendOperatorLog = useCockpitStore((state) => state.appendOperatorLog);
  const targetIds = useCockpitStore((state) =>
    deviceId === RYTM_DEVICE_ID ? state.rytmPadTargets : state.a4TrackTargets,
  );
  const setTargets = useCockpitStore((state) => state.setMutationTargets);
  const requestGeneration = useRef(0);
  const targets = useMemo<ReadonlySet<number>>(() => new Set(targetIds), [targetIds]);
  const hasExplicitTargets = targetIds.length > 0;

  const replaceLocal = useCallback(
    (nextIds: number[]): void => {
      const state = useCockpitStore.getState();
      setTargets(
        deviceId === RYTM_DEVICE_ID ? nextIds : state.rytmPadTargets,
        deviceId === RYTM_DEVICE_ID ? state.a4TrackTargets : nextIds,
      );
    },
    [deviceId, setTargets],
  );

  const sendReplacement = useCallback(
    (nextIds: number[], previousIds: number[]): void => {
      const generation = ++requestGeneration.current;
      replaceLocal(nextIds);
      const command =
        nextIds.length === 0
          ? ({ type: 'clear_mutation_targets', device_id: deviceId } as const)
          : ({
              type: 'set_mutation_targets',
              device_id: deviceId,
              target_ids: nextIds,
            } as const);
      client
        .send(command)
        .then((ack) => {
          if (ack.ok) return;
          const currentIds =
            deviceId === RYTM_DEVICE_ID
              ? useCockpitStore.getState().rytmPadTargets
              : useCockpitStore.getState().a4TrackTargets;
          if (
            generation === requestGeneration.current &&
            currentIds.length === nextIds.length &&
            currentIds.every((id, index) => id === nextIds[index])
          ) {
            replaceLocal(previousIds);
          }
          appendOperatorLog({
            level: 'error',
            message: `${command.type} failed: ${ack.message ?? ack.error ?? 'command rejected'}`,
          });
        })
        .catch((error: unknown) => {
          const currentIds =
            deviceId === RYTM_DEVICE_ID
              ? useCockpitStore.getState().rytmPadTargets
              : useCockpitStore.getState().a4TrackTargets;
          if (
            generation === requestGeneration.current &&
            currentIds.length === nextIds.length &&
            currentIds.every((id, index) => id === nextIds[index])
          ) {
            replaceLocal(previousIds);
          }
          const detail = error instanceof Error ? error.message : String(error);
          appendOperatorLog({ level: 'error', message: `${command.type} failed: ${detail}` });
        });
    },
    [appendOperatorLog, client, deviceId, replaceLocal],
  );

  const toggleTarget = useCallback(
    (id: number): void => {
      const previousIds = [...targets].sort((left, right) => left - right);
      const next = new Set(targets);
      if (!hasExplicitTargets) next.add(id);
      else if (next.has(id)) next.delete(id);
      else next.add(id);
      sendReplacement([...next].sort((left, right) => left - right), previousIds);
    },
    [hasExplicitTargets, sendReplacement, targets],
  );

  const clearTargets = useCallback((): void => {
    if (!hasExplicitTargets) return;
    sendReplacement([], [...targets].sort((left, right) => left - right));
  }, [hasExplicitTargets, sendReplacement, targets]);

  const isTargeted = useCallback(
    (id: number): boolean => !hasExplicitTargets || targets.has(id),
    [hasExplicitTargets, targets],
  );

  return { targets, hasExplicitTargets, isTargeted, toggleTarget, clearTargets };
}
