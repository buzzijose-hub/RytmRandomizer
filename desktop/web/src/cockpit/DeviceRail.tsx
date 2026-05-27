import type { ReactNode } from 'react';

import { useCockpitStore } from '../state';

const ANALOG_FOUR_TRACKS = [
  { track: 1, label: 'T1', role: 'Bass movement' },
  { track: 2, label: 'T2', role: 'Lead pressure' },
  { track: 3, label: 'T3', role: 'Texture motion' },
  { track: 4, label: 'T4', role: 'FX / texture' },
] as const;

export function DeviceRail(): JSX.Element {
  const snapshot = useCockpitStore((s) => s.snapshot);
  const session = useCockpitStore((s) => s.sessionStatus);
  const pads = snapshot?.pads ?? [];
  const padCount = pads.length;
  const rytmStatus = session?.mode === 'live' && session.armed ? 'Armed' : 'Mock Safe';
  const portLabel = session?.midi_port ?? 'No MIDI port open';

  return (
    <aside className="device-rail" data-testid="device-rail" aria-label="Device status">
      <div className="rail-section-title">Devices</div>
      <DeviceCard
        name="Analog Rytm MKII"
        status={rytmStatus}
        detail={`${padCount} pads mapped`}
        active={true}
        testId="device-card-analog-rytm-mk2"
      >
        <div className="device-chip-grid" aria-label="Analog Rytm pad map">
          {pads.map((pad) => (
            <span
              className={pad.pad_id > 4 ? 'device-chip locked' : 'device-chip active'}
              data-testid={`device-rail-rytm-pad-${pad.pad_id}`}
              key={pad.pad_id}
            >
              <span className="device-chip-index">{pad.pad_id}</span>
              <span className="device-chip-role">{pad.machine}</span>
            </span>
          ))}
        </div>
        <p className="device-port-state">{portLabel}</p>
      </DeviceCard>
      <DeviceCard
        name="Analog Four MKII"
        status="Mock Staged"
        detail={`${ANALOG_FOUR_TRACKS.length} tracks staged`}
        active={false}
        testId="device-card-analog-four-mk2"
      >
        <div className="device-chip-grid" aria-label="Analog Four staged track map">
          {ANALOG_FOUR_TRACKS.map((track) => (
            <span
              className="device-chip staged"
              data-testid={`device-rail-a4-track-${track.track}`}
              key={track.track}
            >
              <span className="device-chip-index">{track.label}</span>
              <span className="device-chip-role">{track.role}</span>
            </span>
          ))}
        </div>
        <p className="device-port-state">No MIDI port open</p>
      </DeviceCard>
    </aside>
  );
}

function DeviceCard({
  name,
  status,
  detail,
  active,
  testId,
  children,
}: {
  name: string;
  status: string;
  detail: string;
  active: boolean;
  testId: string;
  children: ReactNode;
}): JSX.Element {
  return (
    <section
      className={active ? 'device-card active' : 'device-card'}
      aria-label={name}
      data-testid={testId}
    >
      <div className="device-card-header">
        <div>
          <h2>{name}</h2>
          <p>{detail}</p>
        </div>
        <span className={active ? 'device-status ready' : 'device-status staged'}>{status}</span>
      </div>
      {children}
    </section>
  );
}
