import { useCockpitStore } from '../state';

export function DeviceRail(): JSX.Element {
  const snapshot = useCockpitStore((s) => s.snapshot);
  const session = useCockpitStore((s) => s.sessionStatus);
  const padCount = snapshot?.pads.length ?? 0;
  const rytmStatus = session?.mode === 'live' && session.armed ? 'Armed' : 'Mock Safe';

  return (
    <aside className="device-rail" data-testid="device-rail" aria-label="Device status">
      <div className="rail-section-title">Devices</div>
      <DeviceCard
        name="Analog Rytm MKII"
        status={rytmStatus}
        detail={`${padCount} pads mapped`}
        active={true}
      />
      <DeviceCard
        name="Analog Four MKII"
        status="Mock Ready"
        detail="style lane staged"
        active={false}
      />
    </aside>
  );
}

function DeviceCard({
  name,
  status,
  detail,
  active,
}: {
  name: string;
  status: string;
  detail: string;
  active: boolean;
}): JSX.Element {
  return (
    <section className={active ? 'device-card active' : 'device-card'} aria-label={name}>
      <div>
        <h2>{name}</h2>
        <p>{detail}</p>
      </div>
      <span className={active ? 'device-status ready' : 'device-status staged'}>{status}</span>
    </section>
  );
}
