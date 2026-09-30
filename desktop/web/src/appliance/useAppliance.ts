import { useCallback, useEffect, useRef, useState } from 'react';

import { announce } from '../a11y';
import type { CockpitClient } from '../ws/client';
import type { ApplianceOperation, ApplianceState, Command, CommandAck } from '../ws/protocol';

export interface ApplianceController {
  state: ApplianceState | null;
  busy: boolean;
  pendingCommand: Command['type'] | null;
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
  const [pendingCommand, setPendingCommand] = useState<Command['type'] | null>(null);
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
      }).catch(() => { if (mounted && generation === epoch.current) setNotice('Sidecar unavailable. No action was queued.'); });
    };
    const dropAuthority = (): void => {
      epoch.current += 1;
      setState(null);
      stateRef.current = null;
      busyRef.current = false;
      setBusy(false);
      setPendingCommand(null);
    };
    const off = client.on('appliance_changed', (event) => { stateRef.current = event.state; setState(event.state); });
    const statusOff = client.onStatusChange((status) => {
      dropAuthority();
      if (status === 'connected') refresh();
      else setNotice('Transport disconnected. Fresh state and arming are required.');
    });
    const contextOffs = (['connection_changed', 'kit_captures_changed', 'snapshot_changed', 'performance_console_changed', 'show_bank_changed', 'dual_machine_stage_changed', 'profile_changed'] as const).map((type) => client.on(type, () => {
      dropAuthority();
      setNotice('Device or Studio context changed. Waiting for fresh appliance state.');
      if (client.getStatus() === 'connected') refresh();
    }));
    if (client.getStatus() === 'connected') refresh();
    return () => { mounted = false; epoch.current += 1; off(); statusOff(); contextOffs.forEach((unsubscribe) => unsubscribe()); };
  }, [client]);

  const command = useCallback(async (request: Command, timeoutMs?: number): Promise<CommandAck | null> => {
    const disarming = request.type === 'disarm';
    if ((!disarming && busyRef.current) || client.getStatus() !== 'connected') return null;
    // A safety action supersedes any pending local result, never waits for a roll/capture.
    if (disarming) epoch.current += 1;
    const generation = epoch.current;
    busyRef.current = true;
    setBusy(true);
    setPendingCommand(request.type);
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
      if (generation === epoch.current) { busyRef.current = false; setBusy(false); setPendingCommand(null); }
    }
  }, [client]);

  const execute = useCallback(async (operation: ApplianceOperation, payload: Record<string, unknown> = {}): Promise<CommandAck | null> => {
    const current = stateRef.current;
    if (operation !== 'state' && current === null) return null;
    return command({ type: 'appliance', operation, payload, ...(operation === 'state' ? {} : { expected_revision: current?.revision }) });
  }, [command]);
  return { state, busy, pendingCommand, notice, execute, command, getState: () => stateRef.current, isBusy: () => busyRef.current };
}
