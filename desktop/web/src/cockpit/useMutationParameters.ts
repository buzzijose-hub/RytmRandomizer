import { useCallback, useEffect, useRef } from 'react';

import { useCockpitStore } from '../state';
import type { ParameterCell } from '../ws/protocol';

import { useCockpitClient } from './context';
import { RYTM_DEVICE_ID, type CockpitDeviceId } from './devices';

export function useMutationParameters(deviceId: CockpitDeviceId) {
  const client = useCockpitClient();
  const request = useRef(0);
  useEffect(() => () => { request.current += 1; }, [deviceId]);
  const selection = useCockpitStore((state) => deviceId === RYTM_DEVICE_ID ? state.rytmParameters : state.a4Parameters);
  const replace = useCallback((cells: ParameterCell[] | null): void => {
    const before = useCockpitStore.getState();
    const previous = deviceId === RYTM_DEVICE_ID ? before.rytmParameters : before.a4Parameters;
    const serial = ++request.current;
    before.replaceMutationParameters(
      deviceId === RYTM_DEVICE_ID ? cells : before.rytmParameters,
      deviceId === RYTM_DEVICE_ID ? before.a4Parameters : cells,
    );
    const revision = useCockpitStore.getState().mutationContextRevision;
    const failed = (detail: string): void => {
      const current = useCockpitStore.getState();
      // An authoritative event (even for identical cells), a lock change, or a
      // newer edit wins over this delayed rejection. No old plan is restored.
      if (serial === request.current && revision === current.mutationContextRevision) {
        current.replaceMutationParameters(
          deviceId === RYTM_DEVICE_ID ? previous : current.rytmParameters,
          deviceId === RYTM_DEVICE_ID ? current.a4Parameters : previous,
        );
      }
      current.appendOperatorLog({ level: 'error', message: `Parameter scope rejected: ${detail}` });
    };
    client.send({ type: 'set_mutation_parameters', device_id: deviceId, parameter_cells: cells })
      .then((ack) => { if (!ack.ok) failed(ack.message ?? ack.error ?? 'command rejected'); })
      .catch((error: unknown) => failed(error instanceof Error ? error.message : String(error)));
  }, [client, deviceId]);
  return { selection, replace };
}
