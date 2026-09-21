import { useCockpitStore } from '../state';

import { OperatorLogList } from './OperatorLogList';

export function SafetyRail(): JSX.Element {
  const session = useCockpitStore((s) => s.sessionStatus);
  const sendPlan = useCockpitStore((s) => s.sendPlan);
  const connectionStatus = useCockpitStore((s) => s.connectionStatus);
  const operatorLog = useCockpitStore((s) => s.operatorLog);
  const isLive = session?.mode === 'live';
  const hardwareState = session?.armed ? 'Hardware Armed' : 'Hardware Off';
  const portState = session?.midi_port ?? 'No MIDI Port Open';
  const safetyState = isLive && session?.armed ? 'Live Armed' : 'Mock Safe';
  const modeState = isLive ? 'Live Hardware' : 'Simulation / Mock';
  const commandCount = sendPlan?.packets.length ?? 0;
  const messageCount = sendPlan?.estimated_midi_msgs ?? 0;
  const readyLabel =
    sendPlan === null ? 'No send plan prepared' : sendPlan.ready ? 'Ready after prepare' : 'Blocked';
  const connectionLabel =
    connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1);

  return (
    <aside className="safety-rail" data-testid="safety-rail" aria-label="Safety status">
      <section className="safety-card">
        <div className="rail-section-title">Session Safety</div>
        <StatusRow
          label="WebSocket"
          value={connectionLabel}
          tone={connectionStatus === 'connected' ? 'safe' : 'muted'}
        />
        <StatusRow label="Status" value={safetyState} tone={safetyState === 'Mock Safe' ? 'safe' : 'armed'} />
        <StatusRow label="MIDI Port" value={portState} tone={session?.midi_port ? 'armed' : 'muted'} />
        <StatusRow label="Hardware" value={hardwareState} tone={session?.armed ? 'armed' : 'muted'} />
        <StatusRow label="Mode" value={modeState} tone={isLive ? 'armed' : 'safe'} />
      </section>

      <section className="safety-card">
        <div className="rail-section-title">Dry-Run Queue</div>
        <div className="queue-row">
          <span>Commands</span>
          <strong>{commandCount}</strong>
        </div>
        <div className="queue-row">
          <span>Dry-run msgs</span>
          <strong>{messageCount}</strong>
        </div>
        <div className="queue-row">
          <span>Readiness</span>
          <strong>{readyLabel}</strong>
        </div>
      </section>

      <section className="safety-card">
        <div className="rail-section-title">Operator Log</div>
        <OperatorLogList
          entries={operatorLog}
          emptyText="No connection or command errors yet."
          testId="operator-log-list"
          label="Operator log"
        />
      </section>
    </aside>
  );
}

function StatusRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: 'safe' | 'armed' | 'muted';
}): JSX.Element {
  return (
    <div className="status-row">
      <span>{label}</span>
      <strong className={`status-pill ${tone}`}>{value}</strong>
    </div>
  );
}
