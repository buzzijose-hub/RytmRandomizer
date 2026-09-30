import { useCallback, useEffect, useRef, useState } from 'react';

import { announce } from '../a11y';
import type { CockpitClient } from '../ws/client';
import type { ApplianceOperation, ApplianceState, Command, CommandAck } from '../ws/protocol';

export interface ApplianceController {
  state: ApplianceState | null;
  busy: boolean;
  notice: string;
  getState: () => ApplianceState | null;
  isBusy: () => boolean;
  execute: (operation: ApplianceOperation, payload?: Record<string, unknown>) => Promise<CommandAck | null>;
  command: (command: Command, timeoutMs?: number) => Promise<CommandAck | null>;
}

/** Uses the existing authenticated client; connection loss removes local authority. */
export function useAppliance(client: CockpitClient): ApplianceController {
  const [state, setState] = useState<ApplianceState | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('Waiting for authenticated appliance state.');
  const busyRef = useRef(false);
  const stateRef = useRef(state);
  stateRef.current = state;
  const epoch = useRef(0);

  useEffect(() => {
    let mounted = true;
    const refresh = (): void => {
      const generation = epoch.current;
      void client.send({ type: 'appliance', operation: 'state' }).then((ack) => {
        if (!mounted || generation !== epoch.current) return;
        if (ack.ok && ack.appliance !== undefined) {
          setState(ack.appliance);
          stateRef.current = ack.appliance;
          setNotice('State received. Outputs require explicit arming and exact confirmation.');
        } else setNotice(ack.message ?? 'This sidecar does not provide appliance state. Update the sidecar.');
      }).catch(() => { if (mounted) setNotice('Sidecar unavailable. No action was queued.'); });
    };
    const off = client.on('appliance_changed', (event) => { stateRef.current = event.state; setState(event.state); });
    const statusOff = client.onStatusChange((status) => {
      epoch.current += 1;
      setState(null);
      stateRef.current = null;
      busyRef.current = false;
      setBusy(false);
      if (status === 'connected') refresh();
      else setNotice('Transport disconnected. Fresh state and arming are required.');
    });
    if (client.getStatus() === 'connected') refresh();
    return () => { mounted = false; epoch.current += 1; off(); statusOff(); };
  }, [client]);

  const command = useCallback(async (request: Command, timeoutMs?: number): Promise<CommandAck | null> => {
    const disarming = request.type === 'disarm';
    if ((!disarming && busyRef.current) || client.getStatus() !== 'connected') return null;
    // A safety action supersedes any pending local result, never waits for a roll/capture.
    if (disarming) epoch.current += 1;
    const generation = epoch.current;
    busyRef.current = true;
    setBusy(true);
    try {
      const ack = await client.send(request, timeoutMs === undefined ? {} : { timeoutMs });
      if (generation !== epoch.current) return null;
      const next = ack.appliance;
      if (next !== undefined) { stateRef.current = next; setState(next); }
      const message = ack.ok ? (ack.message ?? 'Command acknowledged. Hardware acceptance is not verified.') : (ack.message ?? ack.code ?? 'Command refused. Readiness remains blocked.');
      setNotice(message);
      announce(message);
      return ack;
    } catch {
      if (generation === epoch.current) setNotice('Command interrupted or timed out. Do not replay without fresh state.');
      return null;
    } finally {
      if (generation === epoch.current) { busyRef.current = false; setBusy(false); }
    }
  }, [client]);

  const execute = useCallback(async (operation: ApplianceOperation, payload: Record<string, unknown> = {}): Promise<CommandAck | null> => {
    const current = stateRef.current;
    if (operation !== 'state' && current === null) return null;
    return command({ type: 'appliance', operation, payload, ...(operation === 'state' ? {} : { expected_revision: current?.revision }) });
  }, [command]);
  return { state, busy, notice, execute, command, getState: () => stateRef.current, isBusy: () => busyRef.current };
}
