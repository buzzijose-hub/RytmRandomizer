/**
 * Local pad-lock state hook.
 *
 * Per spec: lock state is local UI state, synced to the engine via `set_pad_lock`.
 * The engine doesn't push lock-state events — the UI owns this. We optimistically flip
 * the local bit on toggle and emit `set_pad_lock`; if the ack rejects, we roll back.
 */

import { useCallback, useState } from 'react';

import { useCockpitStore } from '../state';

import { useCockpitClient } from './context';

export interface PadLocksApi {
  /** Set of locked pad_ids. */
  locked: ReadonlySet<number>;
  /** True if `pad_id` is currently locked. */
  isLocked: (padId: number) => boolean;
  /** Toggle the lock state for `pad_id` and emit `set_pad_lock`. */
  toggleLock: (padId: number) => void;
}

export function usePadLocks(): PadLocksApi {
  const [locked, setLocked] = useState<ReadonlySet<number>>(() => new Set<number>());
  const client = useCockpitClient();
  const appendOperatorLog = useCockpitStore((s) => s.appendOperatorLog);

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
      setLocked(next);
      const desired = !wasLocked;
      client
        .send({ type: 'set_pad_lock', pad_id: padId, locked: desired })
        .then((ack) => {
          if (!ack.ok) {
            appendOperatorLog({
              level: 'error',
              message: `set_pad_lock failed: ${ack.error ?? 'command rejected'}`,
            });
            // Roll back on rejection.
            setLocked((prev) => {
              const rolled = new Set(prev);
              if (desired) {
                rolled.delete(padId);
              } else {
                rolled.add(padId);
              }
              return rolled;
            });
          }
        })
        .catch((error: unknown) => {
          const detail = error instanceof Error ? error.message : String(error);
          appendOperatorLog({
            level: 'error',
            message: `set_pad_lock failed: ${detail}`,
          });
          // Network / timeout — roll back so the UI doesn't lie to the operator.
          setLocked((prev) => {
            const rolled = new Set(prev);
            if (desired) {
              rolled.delete(padId);
            } else {
              rolled.add(padId);
            }
            return rolled;
          });
        });
    },
    [appendOperatorLog, client, locked],
  );

  return { locked, isLocked, toggleLock };
}
