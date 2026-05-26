import { useCockpitStore } from '../state';

export function SafetyRail(): JSX.Element {
  const session = useCockpitStore((s) => s.sessionStatus);
  const sendPlan = useCockpitStore((s) => s.sendPlan);
  const isLive = session?.mode === 'live';
  const hardwareState = session?.armed ? 'Hardware Armed' : 'Hardware Off';
  const portState = session?.midi_port ?? 'No MIDI Port Open';
  const safetyState = isLive && session?.armed ? 'Live Armed' : 'Mock Safe';
  const modeState = isLive ? 'Live Hardware' : 'Simulation / Mock';
  const commandCount = sendPlan?.packets.length ?? 0;
  const messageCount = sendPlan?.estimated_midi_msgs ?? 0;
  const readyLabel =
    sendPlan === null ? 'No send plan prepared' : sendPlan.ready ? 'Ready after prepare' : 'Blocked';

  return (
    <aside className="safety-rail" data-testid="safety-rail" aria-label="Safety status">
      <section className="safety-card">
        <div className="rail-section-title">Session Safety</div>
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
