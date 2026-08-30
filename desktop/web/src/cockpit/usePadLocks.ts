/**
 * Shared device-lock state hook.
 *
 * Lock state is hydrated from authoritative whole-state events. We still flip
 * optimistically for immediate operator feedback and emit `set_pad_lock`; if the
 * ack rejects, we roll back, while reconnect/bootstrap events always win.
 */

import { useCallback, useMemo, useRef } from 'react';

import { useCockpitStore } from '../state';

import { useCockpitClient } from './context';
import { RYTM_DEVICE_ID, type CockpitDeviceId } from './devices';

export interface PadLocksApi {
  /** Set of locked pad_ids. */
  locked: ReadonlySet<number>;
  /** True if `pad_id` is currently locked. */
  isLocked: (padId: number) => boolean;
  /** Toggle the lock state for `pad_id` and emit `set_pad_lock`. */
  toggleLock: (padId: number) => void;
}

export function usePadLocks(deviceId: CockpitDeviceId = RYTM_DEVICE_ID): PadLocksApi {
  const client = useCockpitClient();
  const appendOperatorLog = useCockpitStore((s) => s.appendOperatorLog);
  const lockIds = useCockpitStore((s) =>
    deviceId === RYTM_DEVICE_ID ? s.rytmPadLocks : s.a4TrackLocks,
  );
  const setLockIds = useCockpitStore((s) =>
    deviceId === RYTM_DEVICE_ID ? s.setRytmPadLocks : s.setA4TrackLocks,
  );
  const requestGenerations = useRef(new Map<number, number>());
  const locked = useMemo<ReadonlySet<number>>(() => new Set(lockIds), [lockIds]);

  const isLocked = useCallback((padId: number): boolean => locked.has(padId), [locked]);

  const toggleLock = useCallback(
    (padId: number): void => {
      let next: Set<number>;
      const wasLocked = locked.has(padId);
      if (wasLocked) {
        next = new Set(locked);
        next.delete(padId);
      } else {
        next = new Set(locked);
        next.add(padId);
      }
      setLockIds([...next].sort((left, right) => left - right));
      const desired = !wasLocked;
      const generation = (requestGenerations.current.get(padId) ?? 0) + 1;
      requestGenerations.current.set(padId, generation);
      const command =
        deviceId === RYTM_DEVICE_ID
          ? ({ type: 'set_pad_lock', pad_id: padId, locked: desired } as const)
          : ({ type: 'set_a4_track_lock', track: padId, locked: desired } as const);
      const commandName = command.type;

      const rollBackIfCurrent = (): void => {
        if (requestGenerations.current.get(padId) !== generation) return;
        const currentIds =
          deviceId === RYTM_DEVICE_ID
            ? useCockpitStore.getState().rytmPadLocks
            : useCockpitStore.getState().a4TrackLocks;
        const rolled = new Set(currentIds);
        if (rolled.has(padId) !== desired) return;
        if (desired) rolled.delete(padId);
        else rolled.add(padId);
        setLockIds([...rolled].sort((left, right) => left - right));
      };

      client
        .send(command)
        .then((ack) => {
          if (!ack.ok) {
            appendOperatorLog({
              level: 'error',
              message: `${commandName} failed: ${ack.error ?? 'command rejected'}`,
            });
            rollBackIfCurrent();
          }
        })
        .catch((error: unknown) => {
          const detail = error instanceof Error ? error.message : String(error);
          appendOperatorLog({
            level: 'error',
            message: `${commandName} failed: ${detail}`,
          });
          rollBackIfCurrent();
        });
    },
    [appendOperatorLog, client, deviceId, locked, setLockIds],
  );

  return { locked, isLocked, toggleLock };
}
