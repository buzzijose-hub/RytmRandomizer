import { useCallback } from 'react';

import { useCockpitStore } from '../state';
import type { Command } from '../ws/protocol';

import { useCockpitClient } from './context';

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function useLoggedCommand(): (command: Command) => void {
  const client = useCockpitClient();
  const appendOperatorLog = useCockpitStore((s) => s.appendOperatorLog);

  return useCallback(
    (command: Command): void => {
      void client
        .send(command)
        .then((ack) => {
          if (ack.ok) return;
          appendOperatorLog({
            level: 'error',
            message: `${command.type} failed: ${ack.error ?? 'command rejected'}`,
          });
        })
        .catch((error: unknown) => {
          appendOperatorLog({
            level: 'error',
            message: `${command.type} failed: ${errorMessage(error)}`,
          });
        });
    },
    [appendOperatorLog, client],
  );
}
