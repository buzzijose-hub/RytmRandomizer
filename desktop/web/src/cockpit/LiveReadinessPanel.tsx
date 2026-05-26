export interface LiveReadinessPad {
  pad: number;
  trackCode: string;
  label: string;
  state: string;
  role: string;
  machine: string;
  lockReason: string;
}

export interface LiveReadinessDevice {
  deviceId: string;
  displayName: string;
  roleSummary: string;
  trackCountLabel: string;
  status: string;
  capabilities: ReadonlyArray<string>;
}

export interface LiveReadinessScene {
  sceneKey: string;
  label: string;
  description: string;
  affectedPads: string;
  depthPercent: number;
  dryRunMessages: number;
  status: string;
}

export interface LiveReadinessPreviewQueueItem {
  sceneKey: string;
  label: string;
  position: string;
  duration: string;
  status: string;
}

export interface LiveReadinessFooterItem {
  key: string;
  label: string;
  value: string;
  severity: string;
}

export interface LiveReadinessHistoryEntry {
  snapshotId: string;
  label: string;
  summary: string;
  state: string;
}

export interface LiveReadinessControl {
  key: string;
  label: string;
  state: string;
  reason: string;
}

export interface LiveReadinessSafetyItem {
  key: string;
  label: string;
  status: string;
  message: string;
}

export interface LiveReadinessArmGate {
  label: string;
  state: string;
  reason: string;
}

export interface LiveReadinessCommand {
  key: string;
  label: string;
  status: string;
  target: string;
  messageCount: number;
}

export interface LiveReadinessActionRow {
  key: string;
  label: string;
  status: string;
  detail: string;
}

export interface LiveReadinessUndoEntry {
  key: string;
  label: string;
  status: string;
}

export interface LiveReadinessWaveformBin {
  label: string;
  valuePercent: number;
  status: string;
}

export interface LiveReadinessSpectrumBand {
  key: string;
  label: string;
  valuePercent: number;
  status: string;
}

export interface LiveReadinessHardwareAction {
  key: string;
  label: string;
  enabled: boolean;
  reason: string;
}

export interface LiveReadinessHardwareCard {
  key: string;
  title: string;
  status: string;
  summary: string;
  actions: ReadonlyArray<LiveReadinessHardwareAction>;
}

export interface LiveReadinessCompatibilityPad {
  pad: number;
  label: string;
  status: string;
  machineCountLabel: string;
}

export interface LiveReadinessModel {
  padSurface: {
    summary: string;
    pads: ReadonlyArray<LiveReadinessPad>;
  };
  deviceInventory: {
    devices: ReadonlyArray<LiveReadinessDevice>;
  };
  sceneQueue: {
    queueStatus: string;
    scenes: ReadonlyArray<LiveReadinessScene>;
    previewQueue: ReadonlyArray<LiveReadinessPreviewQueueItem>;
  };
  statusFooter: {
    items: ReadonlyArray<LiveReadinessFooterItem>;
  };
  snapshotHistory: {
    entries: ReadonlyArray<LiveReadinessHistoryEntry>;
    controls: ReadonlyArray<LiveReadinessControl>;
  };
  safetyChecklist: {
    status: string;
    passedLabel: string;
    items: ReadonlyArray<LiveReadinessSafetyItem>;
    armGate: LiveReadinessArmGate;
  };
  commandQueue: {
    queueStatus: string;
    commands: ReadonlyArray<LiveReadinessCommand>;
    lastActions: ReadonlyArray<LiveReadinessActionRow>;
    undoStack: ReadonlyArray<LiveReadinessUndoEntry>;
  };
  analyzerPanel: {
    title: string;
    referenceLabel: string;
    panelStatus: string;
    bpmLabel: string;
    tempoStabilityLabel: string;
    waveformBins: ReadonlyArray<LiveReadinessWaveformBin>;
    spectrumBands: ReadonlyArray<LiveReadinessSpectrumBand>;
  };
  hardwareRail: {
    railStatus: string;
    cards: ReadonlyArray<LiveReadinessHardwareCard>;
  };
  snapshotCompatibility: {
    statusBadge: string;
    summary: string;
    pads: ReadonlyArray<LiveReadinessCompatibilityPad>;
  };
}

export interface LiveReadinessPanelProps {
  model?: LiveReadinessModel;
}

export const DEFAULT_LIVE_READINESS_MODEL: LiveReadinessModel = {
  padSurface: {
    summary: '4 active pads, 8 planned pads',
    pads: [
      pad(1, 'BD', 'BD Hard', 'active_v134', 'kick', 'BD Hard', 'ready for dry-run review'),
      pad(2, 'SD', 'SD Classic', 'active_v134', 'snare', 'SD Classic', 'ready for dry-run review'),
      pad(3, 'CH/OH', 'CH Closed', 'active_v134', 'hat', 'CH Closed', 'ready for dry-run review'),
      pad(4, 'FX/FLT', 'OH Open', 'active_v134', 'cymbal', 'OH Open', 'ready for dry-run review'),
      pad(5, 'BT', 'BT Rim', 'planned_expansion', 'tom', 'BT Rim', 'awaiting V1.34-compatible mutation routing'),
      pad(6, 'LT', 'LT Low', 'planned_expansion', 'tom', 'LT Low', 'awaiting V1.34-compatible mutation routing'),
      pad(7, 'MT', 'MT Mid', 'planned_expansion', 'tom', 'MT Mid', 'awaiting V1.34-compatible mutation routing'),
      pad(8, 'HT', 'HT High', 'planned_expansion', 'tom', 'HT High', 'awaiting V1.34-compatible mutation routing'),
      pad(9, 'CP', 'CP Clap', 'planned_expansion', 'perc', 'CP Clap', 'awaiting V1.34-compatible mutation routing'),
      pad(10, 'RS', 'RS Riser', 'planned_expansion', 'fx', 'RS Riser', 'awaiting V1.34-compatible mutation routing'),
      pad(11, 'SY', 'SY Raw', 'planned_expansion', 'synth', 'SY Raw', 'awaiting V1.34-compatible mutation routing'),
      pad(12, 'BD', 'BD Acoustic', 'planned_expansion', 'kick', 'BD Acoustic', 'awaiting V1.34-compatible mutation routing'),
    ],
  },
  deviceInventory: {
    devices: [
      {
        deviceId: 'analog_rytm_mk2',
        displayName: 'Analog Rytm MKII',
        roleSummary: '12-pad drum and sample performance surface',
        trackCountLabel: '12 tracks',
        status: 'mock_safe',
        capabilities: ['snapshot_decode', 'mutation_plan', 'mock_render', 'guarded_send'],
      },
      {
        deviceId: 'analog_four_mk2',
        displayName: 'Analog Four MKII',
        roleSummary: '4-track synth performance surface',
        trackCountLabel: '4 tracks',
        status: 'mock_safe',
        capabilities: ['snapshot_decode', 'mutation_plan', 'mock_render', 'guarded_send'],
      },
    ],
  },
  sceneQueue: {
    queueStatus: 'review-needed',
    scenes: [
      scene('S0', 'Home Clean', 'Return to anchors', '1/2/3/4', 15, 18, 'safe'),
      scene('S1', 'Rolling', 'Introduce rolling low-end motion', '1/2/3/4', 42, 42, 'armed'),
      scene('S2', 'Deeper Tunnel', 'Push into depth and movement', '1/2/3/4', 42, 68, 'armed'),
      scene('S3', 'Metallic Pressure', 'Add metallic tension and grit', '1/2/3/4', 68, 93, 'high-risk'),
      scene('S4', 'Controlled Chaos', 'Max motion with control', '1/2/3/4', 85, 121, 'high-risk'),
      scene('S5', 'Back to Clean', 'Release back to anchors', '1/2/3/4', 15, 22, 'safe'),
    ],
    previewQueue: [
      queueItem('S1', 'Rolling', 'current', '16s', 'armed'),
      queueItem('S1A', 'Rolling Light', 'up-next-1', '16s', 'armed'),
      queueItem('S2', 'Deeper Tunnel', 'up-next-2', '32s', 'armed'),
      queueItem('S3', 'Metallic Pressure', 'up-next-3', '32s', 'high-risk'),
    ],
  },
  statusFooter: {
    items: [
      footerItem('safety', 'Mock Safe', 'No hardware will be changed', 'safe'),
      footerItem('midi-port', 'No MIDI Port Open', 'No MIDI port selected', 'safe'),
      footerItem('hardware', 'Hardware Off', 'Hardware controls locked', 'safe'),
      footerItem('mode', 'Simulation / Mock', 'Simulation mode', 'info'),
      footerItem('send-state', 'no unsaved sends', 'Send queue clean', 'safe'),
      footerItem('version', 'Version', 'v1.34.0', 'info'),
    ],
  },
  snapshotHistory: {
    entries: [
      historyEntry('snap-1', 'Initial snapshot', 'analog_rytm_mk2: 12 pad(s), scene A01, 132 BPM', 'past'),
      historyEntry('snap-2', 'Auto snapshot 2', 'analog_rytm_mk2: 12 pad(s), scene A01, 132 BPM', 'past'),
      historyEntry('snap-3', 'industrial-peak', 'analog_rytm_mk2: 12 pad(s), scene A01, 132 BPM', 'current'),
    ],
    controls: [
      control('undo', 'Undo', 'enabled', 'Undo to previous snapshot snap-2.'),
      control('redo', 'Redo', 'disabled', 'No redo stack is modeled by the cockpit history store yet.'),
      control('load-current', 'Load Current', 'disabled', 'Current snapshot is already loaded.'),
    ],
  },
  safetyChecklist: {
    status: 'passed',
    passedLabel: '4 / 4',
    items: [
      safetyItem('conflicting-sessions', 'No conflicting sessions', 'passed', 'No conflicting sessions detected'),
      safetyItem('guards-enabled', 'All guards enabled', 'passed', 'All safety guards enabled'),
      safetyItem('snapshot-compatible', 'Snapshot compatibility verified', 'passed', 'Snapshot compatibility verified'),
      safetyItem('parameter-limits', 'Parameter limits within safe range', 'passed', 'Parameter limits within safe range'),
    ],
    armGate: {
      label: 'Arm Hardware',
      state: 'locked',
      reason: 'Arm Hardware stays locked until SEND readiness, dry run, MIDI port, and hardware metadata are all ready.',
    },
  },
  commandQueue: {
    queueStatus: 'queued',
    commands: [
      command('queued-command-snapshot-save', 'Snapshot Save (Pre-Mutation)', 'queued', 'history', 0),
      command('queued-command-mutate-pad-11', 'Mutate Pad 11 (SY Raw)', 'queued', 'Pad 11 / SY Raw', 8),
      command('queued-command-mutate-pad-1', 'Mutate Pad 1 (BD Hard)', 'queued', 'Pad 1 / BD Hard', 7),
      command('queued-command-parameter-lock-check', 'Parameter Lock Check', 'queued', 'snapshot compatibility', 0),
    ],
    lastActions: [
      actionRow('last-action-snap-3', 'Send snapshot', 'current', 'saved snapshot via send'),
      actionRow('last-action-snap-2', 'Preview generated', 'past', 'auto snapshot via regen'),
    ],
    undoStack: [
      undoEntry('undo-stack-snap-3', 'industrial-peak', 'current'),
      undoEntry('undo-stack-snap-2', 'Auto snapshot 2', 'available'),
    ],
  },
  analyzerPanel: {
    title: 'Analyzer (Post-Mutation Preview)',
    referenceLabel: 'No reference loaded',
    panelStatus: 'empty',
    bpmLabel: '0.0 BPM',
    tempoStabilityLabel: '0%',
    waveformBins: [
      meter('bin 1', 0, 'empty'),
      meter('bin 2', 0, 'empty'),
      meter('bin 3', 0, 'empty'),
      meter('bin 4', 0, 'empty'),
    ],
    spectrumBands: [
      band('low', 'Low', 0, 'empty'),
      band('body', 'Body', 0, 'empty'),
      band('mid', 'Mid', 0, 'empty'),
      band('high', 'High', 0, 'empty'),
      band('noise', 'Noise', 0, 'empty'),
    ],
  },
  hardwareRail: {
    railStatus: 'mock-safe',
    cards: [
      hardwareCard(
        'mock-dry-run',
        'Mock / Dry Run',
        'active',
        'All changes are simulated. No hardware will be modified.',
        hardwareAction('toggle-dry-run', 'Toggle dry run', false, 'passive GUI state toggle metadata only'),
      ),
      hardwareCard(
        'midi-port',
        'MIDI Port',
        'none',
        'No MIDI port selected or opened.',
        hardwareAction('select-midi-port', 'Open MIDI Port', false, 'no passive port labels supplied'),
      ),
      hardwareCard(
        'arm-hardware',
        'Arm Hardware',
        'locked',
        'Hardware arm is locked until prerequisites are satisfied.',
        hardwareAction('arm-hardware', 'Arm hardware', false, 'dry-run mode is active'),
      ),
    ],
  },
  snapshotCompatibility: {
    statusBadge: 'Limited',
    summary: '4 of 12 pads are snapshot-mutable; 8 are planned/locked.',
    pads: [
      compatibilityPad(1, 'BD Hard', 'compatible', '7 machines'),
      compatibilityPad(2, 'SD Classic', 'compatible', '6 machines'),
      compatibilityPad(3, 'CH Closed', 'compatible', '9 machines'),
      compatibilityPad(4, 'OH Open', 'compatible', '9 machines'),
      compatibilityPad(5, 'BT Rim', 'planned', '3 machines'),
      compatibilityPad(6, 'LT Low', 'planned', '3 machines'),
      compatibilityPad(7, 'MT Mid', 'planned', '3 machines'),
      compatibilityPad(8, 'HT High', 'planned', '3 machines'),
      compatibilityPad(9, 'CP Clap', 'planned', '4 machines'),
      compatibilityPad(10, 'RS Riser', 'planned', '4 machines'),
      compatibilityPad(11, 'SY Raw', 'planned', '4 machines'),
      compatibilityPad(12, 'BD Acoustic', 'planned', '3 machines'),
    ],
  },
};

function pad(
  padNumber: number,
  trackCode: string,
  label: string,
  state: string,
  role: string,
  machine: string,
  lockReason: string,
): LiveReadinessPad {
  return { pad: padNumber, trackCode, label, state, role, machine, lockReason };
}

function scene(
  sceneKey: string,
  label: string,
  description: string,
  affectedPads: string,
  depthPercent: number,
  dryRunMessages: number,
  status: string,
): LiveReadinessScene {
  return { sceneKey, label, description, affectedPads, depthPercent, dryRunMessages, status };
}

function queueItem(
  sceneKey: string,
  label: string,
  position: string,
  duration: string,
  status: string,
): LiveReadinessPreviewQueueItem {
  return { sceneKey, label, position, duration, status };
}

function footerItem(
  key: string,
  label: string,
  value: string,
  severity: string,
): LiveReadinessFooterItem {
  return { key, label, value, severity };
}

function historyEntry(
  snapshotId: string,
  label: string,
  summary: string,
  state: string,
): LiveReadinessHistoryEntry {
  return { snapshotId, label, summary, state };
}

function control(key: string, label: string, state: string, reason: string): LiveReadinessControl {
  return { key, label, state, reason };
}

function safetyItem(
  key: string,
  label: string,
  status: string,
  message: string,
): LiveReadinessSafetyItem {
  return { key, label, status, message };
}

function command(
  key: string,
  label: string,
  status: string,
  target: string,
  messageCount: number,
): LiveReadinessCommand {
  return { key, label, status, target, messageCount };
}

function actionRow(
  key: string,
  label: string,
  status: string,
  detail: string,
): LiveReadinessActionRow {
  return { key, label, status, detail };
}

function undoEntry(key: string, label: string, status: string): LiveReadinessUndoEntry {
  return { key, label, status };
}

function meter(label: string, valuePercent: number, status: string): LiveReadinessWaveformBin {
  return { label, valuePercent, status };
}

function band(
  key: string,
  label: string,
  valuePercent: number,
  status: string,
): LiveReadinessSpectrumBand {
  return { key, label, valuePercent, status };
}

function hardwareAction(
  key: string,
  label: string,
  enabled: boolean,
  reason: string,
): LiveReadinessHardwareAction {
  return { key, label, enabled, reason };
}

function hardwareCard(
  key: string,
  title: string,
  status: string,
  summary: string,
  action: LiveReadinessHardwareAction,
): LiveReadinessHardwareCard {
  return { key, title, status, summary, actions: [action] };
}

function compatibilityPad(
  padNumber: number,
  label: string,
  status: string,
  machineCountLabel: string,
): LiveReadinessCompatibilityPad {
  return { pad: padNumber, label, status, machineCountLabel };
}

export function LiveReadinessPanel({
  model = DEFAULT_LIVE_READINESS_MODEL,
}: LiveReadinessPanelProps): JSX.Element {
  return (
    <section
      className="cockpit-panel live-readiness-panel"
      data-testid="live-readiness-panel"
      aria-labelledby="live-readiness-title"
    >
      <header className="live-readiness-header">
        <h2 id="live-readiness-title">Live Readiness</h2>
        <p className="panel-meta">Passive GUI consumers for cockpit readiness models</p>
      </header>
      <div className="live-readiness-grid">
        <LiveTwelvePadSurface model={model.padSurface} />
        <LiveDeviceInventory model={model.deviceInventory} />
        <LiveSceneQueue model={model.sceneQueue} />
        <LiveStatusFooter model={model.statusFooter} />
        <LiveSnapshotHistory model={model.snapshotHistory} />
        <LiveSafetyChecklist model={model.safetyChecklist} />
        <LiveCommandQueue model={model.commandQueue} />
        <LiveAnalyzerPanel model={model.analyzerPanel} />
        <LiveHardwareRail model={model.hardwareRail} />
        <LiveSnapshotCompatibility model={model.snapshotCompatibility} />
      </div>
    </section>
  );
}

function SurfaceTitle({ title, meta }: { title: string; meta: string }): JSX.Element {
  return (
    <header className="live-surface-header">
      <h3>{title}</h3>
      <span>{meta}</span>
    </header>
  );
}

export function LiveTwelvePadSurface({
  model,
}: {
  model: LiveReadinessModel['padSurface'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-12-pad-surface">
      <SurfaceTitle title="Pad Surface" meta={model.summary} />
      <div className="live-pad-grid">
        {model.pads.map((padItem) => (
          <article
            key={padItem.pad}
            className={`live-pad-card ${padItem.state}`}
            data-testid={`live-pad-${padItem.pad}`}
          >
            <span className="live-pad-index">Pad {padItem.pad}</span>
            <strong>{padItem.label}</strong>
            <span>{padItem.trackCode}</span>
            <span>{padItem.role}</span>
            <span>{padItem.machine}</span>
            <small>{padItem.lockReason}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveDeviceInventory({
  model,
}: {
  model: LiveReadinessModel['deviceInventory'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-device-inventory">
      <SurfaceTitle title="Device Inventory" meta={`${model.devices.length} devices`} />
      <div className="live-list">
        {model.devices.map((device) => (
          <article key={device.deviceId} className="live-row">
            <strong>{device.displayName}</strong>
            <span>{device.roleSummary}</span>
            <span>
              {device.trackCountLabel} / {device.status}
            </span>
            <div className="live-chip-row">
              {device.capabilities.map((capability) => (
                <span key={capability} className="live-chip">
                  {capability}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveSceneQueue({
  model,
}: {
  model: LiveReadinessModel['sceneQueue'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-scene-queue">
      <SurfaceTitle title="Scene Queue" meta={model.queueStatus} />
      <div className="live-scene-rail">
        {model.scenes.map((sceneItem) => (
          <article key={sceneItem.sceneKey} className={`live-scene-card ${sceneItem.status}`}>
            <strong>{sceneItem.sceneKey}</strong>
            <span>{sceneItem.label}</span>
            <small>{sceneItem.description}</small>
            <span>{sceneItem.affectedPads}</span>
            <span>{sceneItem.depthPercent}%</span>
            <span>{sceneItem.dryRunMessages} msgs</span>
          </article>
        ))}
      </div>
      <div className="live-preview-queue">
        {model.previewQueue.map((item) => (
          <article key={`${item.position}-${item.sceneKey}`} className="live-preview-step">
            <strong>{item.sceneKey}</strong>
            <span>{item.label}</span>
            <small>
              {item.position} / {item.duration} / {item.status}
            </small>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveStatusFooter({
  model,
}: {
  model: LiveReadinessModel['statusFooter'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-status-footer">
      <SurfaceTitle title="Status Footer" meta={`${model.items.length} chips`} />
      <div className="live-chip-grid">
        {model.items.map((item) => (
          <article key={item.key} className={`live-status-chip ${item.severity}`}>
            <strong>{item.label}</strong>
            <span>{item.value}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveSnapshotHistory({
  model,
}: {
  model: LiveReadinessModel['snapshotHistory'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-snapshot-history">
      <SurfaceTitle title="Snapshot History" meta={`${model.entries.length} entries`} />
      <div className="live-list">
        {model.entries.map((entry) => (
          <article key={entry.snapshotId} className={`live-row ${entry.state}`}>
            <strong>{entry.label}</strong>
            <span>{entry.snapshotId}</span>
            <small>{entry.summary}</small>
          </article>
        ))}
      </div>
      <div className="live-action-strip">
        {model.controls.map((controlItem) => (
          <button
            key={controlItem.key}
            type="button"
            className="live-readiness-action"
            disabled
            title={controlItem.reason}
          >
            {controlItem.label} / {controlItem.state}
          </button>
        ))}
      </div>
    </section>
  );
}

export function LiveSafetyChecklist({
  model,
}: {
  model: LiveReadinessModel['safetyChecklist'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-safety-checklist">
      <SurfaceTitle title="Safety Checklist" meta={`${model.passedLabel} / ${model.status}`} />
      <div className="live-list">
        {model.items.map((item) => (
          <article key={item.key} className={`live-row ${item.status}`}>
            <strong>{item.label}</strong>
            <span>{item.status}</span>
            <small>{item.message}</small>
          </article>
        ))}
      </div>
      <button
        type="button"
        className="live-readiness-action live-readiness-action-locked"
        disabled
        title={model.armGate.reason}
      >
        {model.armGate.label} / {model.armGate.state}
      </button>
    </section>
  );
}

export function LiveCommandQueue({
  model,
}: {
  model: LiveReadinessModel['commandQueue'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-command-queue">
      <SurfaceTitle title="Command Queue" meta={model.queueStatus} />
      <div className="live-command-columns">
        <div>
          <h4>Queued</h4>
          {model.commands.map((commandItem) => (
            <article key={commandItem.key} className="live-row">
              <strong>{commandItem.label}</strong>
              <span>{commandItem.target}</span>
              <small>
                {commandItem.status} / {commandItem.messageCount} msgs
              </small>
            </article>
          ))}
        </div>
        <div>
          <h4>Last Actions</h4>
          {model.lastActions.map((action) => (
            <article key={action.key} className="live-row">
              <strong>{action.label}</strong>
              <span>{action.status}</span>
              <small>{action.detail}</small>
            </article>
          ))}
        </div>
        <div>
          <h4>Undo Stack</h4>
          {model.undoStack.map((entry) => (
            <article key={entry.key} className="live-row">
              <strong>{entry.label}</strong>
              <span>{entry.status}</span>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function LiveAnalyzerPanel({
  model,
}: {
  model: LiveReadinessModel['analyzerPanel'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-analyzer-panel">
      <SurfaceTitle title={model.title} meta={model.panelStatus} />
      <p className="live-reference-label">{model.referenceLabel}</p>
      <div className="live-metric-row">
        <span>{model.bpmLabel}</span>
        <span>{model.tempoStabilityLabel}</span>
      </div>
      <div className="live-meter-stack">
        {model.waveformBins.map((binItem) => (
          <MeterRow key={binItem.label} label={binItem.label} value={binItem.valuePercent} status={binItem.status} />
        ))}
      </div>
      <div className="live-meter-stack">
        {model.spectrumBands.map((bandItem) => (
          <MeterRow key={bandItem.key} label={bandItem.label} value={bandItem.valuePercent} status={bandItem.status} />
        ))}
      </div>
    </section>
  );
}

function MeterRow({ label, value, status }: { label: string; value: number; status: string }): JSX.Element {
  return (
    <div className="live-meter-row">
      <span>{label}</span>
      <span
        className={`live-meter ${status}`}
        role="meter"
        aria-label={`${label} ${status}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
      >
        <span style={{ width: `${value}%` }} />
      </span>
      <strong>{value}%</strong>
    </div>
  );
}

export function LiveHardwareRail({
  model,
}: {
  model: LiveReadinessModel['hardwareRail'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-hardware-rail">
      <SurfaceTitle title="Hardware Rail" meta={model.railStatus} />
      <div className="live-list">
        {model.cards.map((card) => (
          <article key={card.key} className={`live-row ${card.status}`}>
            <strong>{card.title}</strong>
            <span>{card.status}</span>
            <small>{card.summary}</small>
            <div className="live-action-strip">
              {card.actions.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  className="live-readiness-action"
                  data-action-enabled={String(action.enabled)}
                  disabled
                  title={action.reason}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveSnapshotCompatibility({
  model,
}: {
  model: LiveReadinessModel['snapshotCompatibility'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-snapshot-compatibility">
      <SurfaceTitle title="Snapshot Compatibility" meta={model.statusBadge} />
      <p className="panel-meta">{model.summary}</p>
      <div className="live-compatibility-grid">
        {model.pads.map((padItem) => (
          <article key={padItem.pad} className={`live-compatibility-pad ${padItem.status}`}>
            <strong>Pad {padItem.pad}</strong>
            <span>{padItem.label}</span>
            <span>{padItem.status}</span>
            <small>{padItem.machineCountLabel}</small>
          </article>
        ))}
      </div>
    </section>
  );
}
