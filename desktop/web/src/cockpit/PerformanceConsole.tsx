import type {
  LiveGuiAnalyzerPanelControlDict,
  LiveGuiDeviceInventoryCardDict,
  LiveGuiPerformanceConsoleMacroActionCardDict,
  LiveGuiPerformanceConsoleModelDict,
  LiveGuiPerformanceConsoleRytmMacroPolicyRowDict,
  LiveGuiRytmPadSurfaceCardDict,
  LiveGuiSnapshotHistoryEntryDict,
} from '../types/live_gui_protocol';
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID } from './devices';
import { RYTM_PARAMETER_GROUPS } from './parameterGroups';

export interface PerformanceConsoleProps {
  model: LiveGuiPerformanceConsoleModelDict;
  packetSource?: string;
}

const ANALYZER_CONTROL_ORDER: ReadonlyArray<string> = ['preview', 'dry_run', 'arm_hardware'];
const SNAPSHOT_DECK_PREVIEW_PARAMETER_COUNT = 3;

function orderedDevices(
  devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>,
): ReadonlyArray<LiveGuiDeviceInventoryCardDict> {
  return [...devices].sort((left, right) => left.order - right.order);
}

function orderedPads(
  pads: ReadonlyArray<LiveGuiRytmPadSurfaceCardDict>,
): ReadonlyArray<LiveGuiRytmPadSurfaceCardDict> {
  return [...pads].sort((left, right) => left.pad - right.pad);
}

function orderedMacroActions(
  cards: ReadonlyArray<LiveGuiPerformanceConsoleMacroActionCardDict>,
): ReadonlyArray<LiveGuiPerformanceConsoleMacroActionCardDict> {
  return [...cards].sort((left, right) => left.order - right.order);
}

function orderedRytmMacroPolicies(
  rows: ReadonlyArray<LiveGuiPerformanceConsoleRytmMacroPolicyRowDict>,
): ReadonlyArray<LiveGuiPerformanceConsoleRytmMacroPolicyRowDict> {
  return [...rows].sort((left, right) => left.order - right.order);
}

function toTestIdKey(value: string): string {
  return value.toLowerCase().replaceAll('_', '-').replaceAll('/', '-').replaceAll(' ', '-');
}

function toHumanLabel(value: string): string {
  return value
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function toStatusLabel(value: string): string {
  return toHumanLabel(value).toUpperCase();
}

function uniqueText(values: ReadonlyArray<string>): ReadonlyArray<string> {
  return [...new Set(values.filter((value) => value.trim().length > 0))];
}

function deviceTrackLabel(device: LiveGuiDeviceInventoryCardDict, index: number): string | number {
  if (device.device_id === ANALOG_FOUR_DEVICE_ID) {
    return `T${index + 1}`;
  }
  if (device.device_id === RYTM_DEVICE_ID) {
    return index + 1;
  }
  return `${device.default_midi_channel_label}:${index + 1}`;
}

function portSummary(
  devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>,
  model: LiveGuiPerformanceConsoleModelDict,
): string {
  const armGate = model.safety_checklist.arm_gate;
  if (armGate.midi_port_name !== null) {
    return armGate.midi_port_name;
  }
  if (armGate.midi_port_open) {
    return 'MIDI port open';
  }
  const portStates = uniqueText(devices.map((device) => device.port_state));
  if (portStates.every((state) => ['closed', 'not_open', 'none'].includes(state))) {
    return 'No MIDI Port Open';
  }
  return portStates.map(toHumanLabel).join(' / ');
}

function mockSummary(devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>): string {
  return uniqueText(devices.map((device) => device.mock_state)).map(toHumanLabel).join(' / ') || 'mock state unknown';
}

function armSummary(model: LiveGuiPerformanceConsoleModelDict): string {
  if (model.command_queue.hardware_armed) {
    return 'ARMED';
  }
  return toStatusLabel(model.safety_checklist.arm_gate.state);
}

function dryRunSummary(model: LiveGuiPerformanceConsoleModelDict): string {
  return model.command_queue.dry_run_active ? 'dry-run active' : 'dry-run inactive';
}

function snapshotSceneLabel(snapshot: LiveGuiSnapshotHistoryEntryDict | undefined): string {
  if (snapshot === undefined || snapshot.scene_slot === null) {
    return 'Scene not set';
  }
  return `Scene ${snapshot.scene_slot}`;
}

function snapshotIdentityLabel(snapshot: LiveGuiSnapshotHistoryEntryDict | undefined): string {
  return snapshot === undefined ? 'No current snapshot' : `Snapshot ${snapshot.snapshot_id}`;
}

function snapshotBpmLabel(snapshot: LiveGuiSnapshotHistoryEntryDict | undefined): string {
  if (snapshot === undefined) {
    return 'BPM unknown';
  }
  return snapshot.bpm_label;
}

function profileLabels(
  model: LiveGuiPerformanceConsoleModelDict,
  currentMove: { readonly risk_status: string; readonly status: string } | undefined,
  currentMacro: LiveGuiPerformanceConsoleMacroActionCardDict | undefined,
): ReadonlyArray<string> {
  const labels = [model.macro_action_deck.deck_status];
  if (currentMove !== undefined) {
    labels.push(currentMove.risk_status, currentMove.status);
  }
  if (currentMacro !== undefined) {
    labels.push(currentMacro.risk_label);
  }
  return uniqueText(labels);
}

function companionTrackCount(devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>): number {
  return devices
    .filter((device) => device.device_id !== RYTM_DEVICE_ID)
    .reduce((total, device) => total + device.track_count, 0);
}

function deviceListLabel(devices: ReadonlyArray<LiveGuiDeviceInventoryCardDict>): string {
  if (devices.length === 0) {
    return 'none';
  }
  return devices.map((device) => device.display_name).join(' + ');
}

function queuedCommandButtonLabel(
  command: { readonly label: string } | undefined,
  queueStatus: string,
): string {
  if (command === undefined) {
    return `Queue ${queueStatus}`;
  }
  return `Queue ${command.label}`;
}

function orderedAnalyzerControls(
  controls: Readonly<Record<string, LiveGuiAnalyzerPanelControlDict>>,
): ReadonlyArray<LiveGuiAnalyzerPanelControlDict> {
  const ordered = ANALYZER_CONTROL_ORDER.map((key) => controls[key]).filter(
    (control): control is LiveGuiAnalyzerPanelControlDict => control !== undefined,
  );
  const remaining = Object.values(controls).filter(
    (control) => !ANALYZER_CONTROL_ORDER.includes(control.key),
  );
  return [...ordered, ...remaining];
}

function formatLanePolicies(lanes: Readonly<Record<string, string>>): string {
  const entries = Object.entries(lanes).sort(([left], [right]) => left.localeCompare(right));
  return entries.map(([key, value]) => `${key}=${value}`).join(', ') || 'default lanes';
}

function formatSectionAllowlists(
  allowlists: Readonly<Record<string, ReadonlyArray<string>>>,
): string {
  const entries = Object.entries(allowlists).sort(([left], [right]) => left.localeCompare(right));
  return (
    entries
      .map(([section, families]) => `${section}: ${[...families].sort().join(', ')}`)
      .join(' / ') || 'all allowed families'
  );
}

export function PerformanceConsole({
  model,
  packetSource = 'passive packet',
}: PerformanceConsoleProps): JSX.Element {
  const a4SetPlan = model.performance_flow.analog_four_set_plan;
  const a4ReviewSurface = model.analog_four_review_surface;
  const a4ReviewFocus = a4ReviewSurface.review_focus;
  const macroPath = [a4SetPlan.current_macro, ...a4SetPlan.up_next_macros].join(' -> ');
  const sortedDevices = orderedDevices(model.device_inventory.cards);
  const sortedPads = orderedPads(model.rytm_pad_surface.cards);
  const sortedMacros = orderedMacroActions(model.macro_action_deck.cards);
  const sortedRytmPolicies = orderedRytmMacroPolicies(model.rytm_lane_policy_matrix.macro_rows);
  const sortedQueue = [...model.style_queue.queue_cards].sort((left, right) => left.order - right.order);
  const currentQueueMove = sortedQueue[0];
  const currentSnapshot =
    model.snapshot_history.entries.find((entry) => entry.snapshot_id === model.snapshot_history.current_id) ??
    model.snapshot_history.entries[0];
  const currentMacro =
    sortedMacros.find((card) => card.macro_key === model.macro_action_deck.current_macro_key) ??
    sortedMacros[0];
  const currentDepth = currentQueueMove?.mutation_amount_percent ?? 0;
  const mutationPadCount = currentMacro?.affected_pads.length ?? 0;
  const analogFourDevice = sortedDevices.find((device) => device.device_id === ANALOG_FOUR_DEVICE_ID);
  const rytmDevice = sortedDevices.find((device) => device.device_id === RYTM_DEVICE_ID);
  const currentSceneLabel = snapshotSceneLabel(currentSnapshot);
  const currentSnapshotLabel = snapshotIdentityLabel(currentSnapshot);
  const portState = portSummary(sortedDevices, model);
  const mutationProfileLabels = profileLabels(model, currentQueueMove, currentMacro);
  const synthTrackCount = analogFourDevice?.track_count ?? companionTrackCount(sortedDevices);
  const previewParameters = RYTM_PARAMETER_GROUPS[0]!.params.slice(
    0,
    SNAPSHOT_DECK_PREVIEW_PARAMETER_COUNT,
  );
  const queuedCommand = model.command_queue.queued_commands[0];

  return (
    <main
      className="performance-console"
      data-testid="performance-console"
      aria-labelledby="performance-console-title"
    >
      <header className="performance-console-topbar" data-testid="performance-console-topbar">
        <div className="performance-console-brand">
          <span aria-hidden="true" className="performance-console-brand-mark" />
          <h1 id="performance-console-title">RytmRandomizer Cockpit Performance Console</h1>
        </div>
        <div className="performance-console-status" aria-label="Console safety state">
          <span>{model.console_status}</span>
          <span>{model.hardware_mode}</span>
          <span>{packetSource}</span>
        </div>
        <div className="performance-console-topbar-controls" aria-label="Cockpit hardware state">
          <strong>
            {toStatusLabel(model.console_status)} - {portState}
          </strong>
          <span>MIDI Port</span>
          <span>{portState}</span>
          <span>Arm</span>
          <strong>{armSummary(model)}</strong>
          <span>{model.command_queue.queue_status}</span>
          <span>{dryRunSummary(model)}</span>
          <span>{currentSceneLabel}</span>
          <span>{snapshotBpmLabel(currentSnapshot)}</span>
          <button type="button" className="live-readiness-action" disabled>
            Tap Tempo
          </button>
        </div>
      </header>

      <aside className="performance-console-left-rail" data-testid="performance-console-left-rail">
        <section className="performance-console-surface" aria-labelledby="console-device-rail-title">
          <h2 id="console-device-rail-title">Device Rail</h2>
          <div className="performance-console-device-grid">
            {sortedDevices.map((device) => (
              <article
                key={device.device_id}
                className="performance-console-device performance-console-device-rail-card"
                data-testid={`performance-console-device-${device.device_id}`}
              >
                <header>
                  <strong>{device.display_name}</strong>
                  <span>{toStatusLabel(device.hardware_state)}</span>
                </header>
                <small>{device.role_summary}</small>
                <small>
                  {device.track_count} tracks / port {device.port_state} / mock {device.mock_state}
                </small>
                <div className="performance-console-device-chip-grid">
                  {Array.from({ length: device.track_count }, (_, index) => (
                    <span key={`${device.device_id}-${index + 1}`} className="performance-console-device-chip">
                      {deviceTrackLabel(device, index)}
                    </span>
                  ))}
                </div>
                <div className="live-chip-row">
                  {device.capability_badges.map((badge) => (
                    <span key={badge} className="live-chip">
                      {badge}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="performance-console-surface performance-console-readiness-card">
          <h2>Safety / Readiness</h2>
          <div className="performance-console-readiness-meter">
            <strong>{toStatusLabel(model.safety_checklist.checklist_status)}</strong>
            <span>{model.safety_checklist.arm_gate.reason}</span>
          </div>
          <div className="performance-console-list">
            {model.safety_checklist.items.map((item) => (
              <article key={item.key}>
                <strong>{item.label}</strong>
                <span>{item.status}</span>
                <small>{item.message}</small>
              </article>
            ))}
            <article>
              <strong>{model.safety_checklist.arm_gate.label}</strong>
              <span>{model.safety_checklist.arm_gate.state}</span>
              <small>{model.safety_checklist.arm_gate.reason}</small>
            </article>
          </div>
        </section>
      </aside>

      <section
        className="performance-console-snapshot-deck"
        data-testid="performance-console-snapshot-deck"
        aria-labelledby="console-pad-grid-title"
      >
        <header className="performance-console-deck-header">
          <div>
            <p className="panel-meta">SNAPSHOT - ANALOG RYTM MKII</p>
            <h2 id="console-pad-grid-title">Snapshot - Analog Rytm MKII</h2>
          </div>
          <div className="live-chip-row">
            <span className="live-chip">{currentSceneLabel}</span>
            <span className="live-chip">{model.session_label}</span>
            <span className="live-chip">{currentSnapshotLabel}</span>
            <span className="live-chip">{snapshotBpmLabel(currentSnapshot)}</span>
          </div>
        </header>
        <div className="performance-console-pad-grid">
          {sortedPads.map((pad) => (
            <article
              key={pad.pad}
              className={`performance-console-pad ${pad.surface_state}`}
              data-testid={`performance-console-pad-${pad.pad}`}
            >
              <header>
                <span>{pad.pad}</span>
                <small>{pad.track_code}</small>
              </header>
              <strong>{pad.label}</strong>
              <small>
                {pad.track_code} / {pad.default_role} / {pad.default_machine_label}
              </small>
              <div className="performance-console-pad-knobs" aria-label={`Pad ${pad.pad} preview controls`}>
                {previewParameters.map((parameter, index) => (
                  <span key={`${pad.pad}-${parameter.key}`} className={`performance-console-mini-knob knob-${index}`}>
                    <span aria-hidden="true" />
                    <small>{parameter.label}</small>
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
        <section
          className="performance-console-surface performance-console-snapshot-history-panel"
          data-testid="performance-console-snapshot-history"
          aria-labelledby="console-snapshot-history-title"
        >
          <header className="performance-console-section-header">
            <h2 id="console-snapshot-history-title">Snapshot History / Mutation Journal</h2>
            <span>{model.snapshot_history.entry_count} entries</span>
          </header>
          <div className="performance-console-history-rail">
            {model.snapshot_history.entries.map((entry) => (
              <article
                key={entry.key}
                className={entry.snapshot_id === currentSnapshot?.snapshot_id ? 'current' : undefined}
              >
                <strong>{entry.snapshot_id}</strong>
                <span>{entry.label}</span>
                <small>{entry.summary}</small>
              </article>
            ))}
          </div>
        </section>
      </section>

      <section
        className="performance-console-mutation-panel"
        data-testid="performance-console-mutation-panel"
        aria-labelledby="console-mutation-panel-title"
      >
        <header className="performance-console-deck-header">
          <div>
            <p className="panel-meta">MUTATION PANEL</p>
            <h2 id="console-mutation-panel-title">Mutation Panel</h2>
          </div>
          <span className="live-chip">Queue ({sortedQueue.length})</span>
        </header>

        <section
          className="performance-console-surface"
          data-testid="performance-console-style-queue"
          aria-labelledby="console-style-queue-title"
        >
          <header className="performance-console-section-header">
            <h2 id="console-style-queue-title">Style Queue / Journal</h2>
            <span>{model.style_queue.deck_status}</span>
          </header>
          <h3 className="performance-console-subheading">Style Crates</h3>
          <div className="performance-console-list performance-console-crate-list" aria-label="Style crates">
            {model.style_queue.crate_cards.map((crate) => (
              <article
                key={crate.crate_key}
                data-testid={`style-crate-${toTestIdKey(crate.crate_key)}`}
              >
                <strong>{crate.crate_name}</strong>
                <span>{crate.summary}</span>
                <small>
                  energy {crate.energy} / risk {crate.risk} / {crate.risk_status} / pads{' '}
                  {crate.target_pads.join(', ')}
                </small>
                <small>
                  primary move {crate.primary_move_name} / {crate.operator_action}
                </small>
                <div className="live-chip-row">
                  {crate.tags.map((tag) => (
                    <span key={`${crate.crate_key}-${tag}`} className="live-chip">
                      {tag}
                    </span>
                  ))}
                </div>
                <button
                  type="button"
                  className="live-readiness-action"
                  disabled
                  title="Style crate staging remains passive in this console packet."
                >
                  Stage {crate.primary_move_name}
                </button>
              </article>
            ))}
          </div>
          <h3 className="performance-console-subheading">Queued Moves</h3>
          <div className="performance-console-list">
            {sortedQueue.map((move) => (
              <article
                key={move.queue_key}
                className={move.queue_key === currentQueueMove?.queue_key ? 'current' : undefined}
                data-testid={`style-queue-move-${toTestIdKey(move.queue_key)}`}
              >
                <strong>{move.move_name}</strong>
                <span>
                  {move.chapter} / {move.mutation_amount_percent}% / {move.risk_status}
                </span>
                <small>
                  pads {move.target_pads.join(', ')} / {move.operator_action} / recover{' '}
                  {move.recovery_action}
                </small>
                {move.dry_run_only ? (
                  <div className="live-chip-row">
                    <span className="live-chip">dry-run only</span>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
          <h3 className="performance-console-subheading">Mutation Journal</h3>
          <div className="performance-console-list">
            {model.style_queue.journal_cards.map((entry) => (
              <article key={entry.journal_key}>
                <strong>{entry.name}</strong>
                <span>{entry.value_summary.join(', ')}</span>
              </article>
            ))}
          </div>
        </section>

        <section className="performance-console-surface performance-console-depth-panel">
          <header className="performance-console-section-header">
            <h2>Depth</h2>
            <span>{currentDepth}%</span>
          </header>
          <div className="performance-console-depth-track" aria-label="Mutation depth preview">
            <span style={{ width: `${currentDepth}%` }} />
          </div>
          <h3 className="performance-console-subheading">Profile</h3>
          <div className="performance-console-profile-row">
            {mutationProfileLabels.map((profile, index) => (
              <span key={profile} className={index === 0 ? 'active' : undefined}>
                {toHumanLabel(profile)}
              </span>
            ))}
          </div>
        </section>

        <section className="performance-console-surface performance-console-mutation-summary">
          <header className="performance-console-section-header">
            <h2>Mutation Summary</h2>
            <span>{model.macro_action_deck.deck_status}</span>
          </header>
          <p>
            {mutationPadCount} drum pads and {synthTrackCount} synth tracks
            represented in the passive console.
          </p>
          <div className="performance-console-radar" aria-label="Mutation summary radar">
            {['energy', 'density', 'chaos', 'space', 'grit', 'motion'].map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
        </section>

        <section className="performance-console-surface">
          <h2>Actions</h2>
          <div className="performance-console-action-grid">
            <button type="button" className="live-readiness-action" disabled>
              {currentQueueMove?.operator_action ?? model.style_queue.deck_status}
            </button>
            <button type="button" className="live-readiness-action" disabled>
              Review {currentMacro?.label ?? model.macro_action_deck.current_macro_key}
            </button>
            <button type="button" className="live-readiness-action live-readiness-action-locked" disabled>
              {queuedCommandButtonLabel(queuedCommand, model.command_queue.queue_status)}
            </button>
            <button type="button" className="live-readiness-action live-readiness-action-locked" disabled>
              {model.safety_checklist.arm_gate.label} {model.safety_checklist.arm_gate.state}
            </button>
          </div>
        </section>

        <section
          className="performance-console-surface"
          data-testid="performance-console-blocked-actions"
          aria-labelledby="console-blocked-actions-title"
        >
          <h2 id="console-blocked-actions-title">Blocked Hardware Actions</h2>
          <div className="live-chip-row">
            {model.blocked_actions.map((action) => (
              <span key={action} className="live-chip live-chip-blocked">
                {action}
              </span>
            ))}
          </div>
          <div className="live-chip-row">
            {model.safety_lines.map((line) => (
              <span key={line} className="live-chip">
                {line}
              </span>
            ))}
          </div>
        </section>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-rytm-lane-policy-matrix"
        aria-labelledby="console-rytm-lane-policy-matrix-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-rytm-lane-policy-matrix-title">Rytm Lane Policy Matrix</h2>
          <span>
            {model.rytm_lane_policy_matrix.matrix_status} /{' '}
            {model.rytm_lane_policy_matrix.macro_count} macros
          </span>
        </header>
        <p className="panel-meta">{model.rytm_lane_policy_matrix.source_report}</p>

        <h3 className="performance-console-subheading">Pad Groups</h3>
        <div className="performance-console-list">
          {model.rytm_lane_policy_matrix.pad_groups.map((group) => (
            <article key={group.group_key} data-testid={`rytm-lane-policy-${group.group_key}`}>
              <strong>{group.group_key}</strong>
              <span>pads {group.pads.join(', ')}</span>
              <small>{group.summary}</small>
              <small>{group.lane_policy}</small>
              <small>{group.operator_note}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Macro Policies</h3>
        <div className="performance-console-list">
          {sortedRytmPolicies.map((row) => (
            <article key={row.macro_key} data-testid={`rytm-macro-policy-${row.macro_key}`}>
              <strong>{row.label}</strong>
              <span>
                {row.macro_key} / {row.style_crate} / {row.risk_label}
              </span>
              <small>pads {row.affected_pads.join(', ')}</small>
              <small>{row.lane_policy_summary}</small>
              <small>recover {row.recovery_action}</small>
              <small>{row.summary}</small>
              {Object.entries(row.pad_policy_cards).map(([pad, policy]) => (
                <small key={`${row.macro_key}-pad-${pad}`}>
                  Pad {pad}: amount {policy.amount ?? 'default'} / density{' '}
                  {policy.density ?? 'default'} / bias {policy.bias ?? 'default'} /{' '}
                  {formatLanePolicies(policy.lane_policies)} /{' '}
                  {formatSectionAllowlists(policy.section_family_allowlists)}
                </small>
              ))}
            </article>
          ))}
        </div>

        <div className="live-chip-row">
          {model.rytm_lane_policy_matrix.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
          {model.rytm_lane_policy_matrix.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="Rytm lane policy dispatch remains blocked in this passive console."
          >
            Apply Rytm Lane Policy
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="Real Rytm sends remain in the explicitly armed snapshot shell."
          >
            Send Rytm Policy
          </button>
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-flow"
        aria-labelledby="console-flow-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-flow-title">Performance Flow</h2>
          <span>{model.performance_flow.flow_status}</span>
        </header>
        <div className="performance-console-flow-rail">
          {model.performance_flow.steps.map((step) => (
            <article
              key={step.key}
              className={`performance-console-step ${
                step.key === model.performance_flow.current_step_key ? 'current' : 'next'
              }`}
            >
              <strong>{step.key}</strong>
              <span>{step.label}</span>
              <small>
                Rytm {step.rytm_command} / A4 {step.analog_four_action} / {step.send_policy}
              </small>
            </article>
          ))}
        </div>
        <article className="performance-console-a4-plan">
          <strong>{a4SetPlan.set_name}</strong>
          <span>{macroPath}</span>
          <small>{a4SetPlan.summary}</small>
          <div className="live-chip-row">
            {a4SetPlan.blocked_active_actions.map((action) => (
              <span key={action} className="live-chip live-chip-blocked">
                {action}
              </span>
            ))}
          </div>
        </article>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-a4-review-surface"
        aria-labelledby="console-a4-review-surface-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-a4-review-surface-title">{a4ReviewSurface.title}</h2>
          <span>{a4ReviewSurface.surface_status}</span>
        </header>
        <p className="panel-meta">
          {a4ReviewSurface.set_name} / focus {a4ReviewFocus.macro_name} /{' '}
          {a4ReviewFocus.readiness}
        </p>
        <small>{a4ReviewSurface.preflight_command}</small>

        <h3 className="performance-console-subheading">A4 Set Review Path</h3>
        <div className="performance-console-list">
          {a4ReviewSurface.steps.map((step) => (
            <article key={`${step.order}-${step.macro_name}`}>
              <strong>{step.macro_label}</strong>
              <span>
                {step.macro_name} / seed {step.seed} / intensity {step.intensity} / energy{' '}
                {step.energy}
              </span>
              <small>{step.summary}</small>
              <small>
                {step.readiness} / ready {step.ready_count} / review {step.review_count} /
                blocked {step.blocked_count}
              </small>
              <small>{step.validation_command}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Readiness Events</h3>
        <div className="performance-console-list">
          {a4ReviewSurface.readiness_events.map((event) => (
            <article key={`${event.track}-${event.parameter}-${event.value}`}>
              <strong>
                Track {event.track} / {event.parameter}
              </strong>
              <span>
                {event.role} / {event.lane} / CC{event.control} to {event.value}
              </span>
              <small>{event.status}</small>
              <small>{event.validation_command}</small>
              <small>{event.reason}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Validation Workflow</h3>
        <div className="performance-console-list">
          <article>
            <strong>Preflight</strong>
            <span>{a4ReviewSurface.preflight_command}</span>
            {a4ReviewSurface.validation_steps.map((step) => (
              <small key={step}>{step}</small>
            ))}
          </article>
          <article>
            <strong>Promotion Gates</strong>
            {a4ReviewSurface.promotion_gates.map((gate) => (
              <small key={gate}>{gate}</small>
            ))}
          </article>
          <article>
            <strong>Recovery Notes</strong>
            {a4ReviewSurface.recovery_notes.map((note) => (
              <small key={note}>{note}</small>
            ))}
          </article>
        </div>

        <div className="live-chip-row">
          {a4ReviewSurface.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
          {a4ReviewSurface.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="A4 macro validation is a review-only Cockpit surface."
          >
            Review A4 {a4ReviewFocus.macro_name}
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="A4 full macro send remains blocked until hardware validation promotes it."
          >
            Promote A4 Macro
          </button>
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-macro-actions"
        aria-labelledby="console-macro-actions-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-macro-actions-title">Live Macro Actions</h2>
          <span>
            {model.macro_action_deck.deck_status} / current {model.macro_action_deck.current_macro_key}
          </span>
        </header>
        <div className="performance-console-macro-grid">
          {sortedMacros.map((card) => (
            <article
              key={card.macro_key}
              className={`performance-console-macro-card ${card.status}`}
              data-testid={card.test_id}
            >
              <header>
                <strong>{card.label}</strong>
                <span>{card.macro_key}</span>
              </header>
              <small>
                {card.shell_command} / {card.send_policy} / {card.risk_label}
              </small>
              <span>pads {card.affected_pads.join(', ')}</span>
              <div className="live-chip-row" aria-label={`Macro ${card.macro_key} boundary`}>
                <span className="live-chip">recover {card.recovery_action}</span>
                <span className="live-chip live-chip-blocked">
                  hardware {card.hardware_action_state}
                </span>
                {card.dry_run_only ? <span className="live-chip">dry-run only</span> : null}
              </div>
              <small>{card.operator_hint}</small>
              <div className="live-chip-row">
                {model.macro_action_deck.blocked_actions.map((action) => (
                  <span key={`${card.macro_key}-${action}`} className="live-chip live-chip-blocked">
                    {action}
                  </span>
                ))}
              </div>
              <div className="performance-console-macro-actions">
                <button
                  type="button"
                  className="live-readiness-action"
                  disabled
                  title="Macro preparation is blocked in this passive console packet."
                >
                  Prepare {card.macro_key}
                </button>
                <button
                  type="button"
                  className="live-readiness-action live-readiness-action-locked"
                  disabled
                  title="Real sends remain in the explicitly armed snapshot shell."
                >
                  Send {card.macro_key}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-rehearsal-board"
        aria-labelledby="console-rehearsal-board-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-rehearsal-board-title">Rehearsal Board</h2>
          <span>{model.rehearsal_board.board_status}</span>
        </header>
        <p className="panel-meta">{model.rehearsal_board.title}</p>
        <small>{model.rehearsal_board.launch_command}</small>
        <div className="performance-console-macro-actions">
          <button
            type="button"
            className="live-readiness-action"
            disabled
            title="The armed shell launch command is shown for operator review only."
          >
            Launch Armed Shell
          </button>
          <button
            type="button"
            className="live-readiness-action live-readiness-action-locked"
            disabled
            title="Rehearsal cues cannot send hardware from this passive console."
          >
            Fire Cue
          </button>
        </div>

        <h3 className="performance-console-subheading">Live Chapters</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.chapters.map((chapter) => (
            <article key={chapter.name}>
              <strong>{chapter.label}</strong>
              <span>
                {chapter.rytm_command} / recover {chapter.recovery_action}
              </span>
              <small>{chapter.operator_intent}</small>
              <div className="live-chip-row">
                {chapter.macro_sequence.map((macro) => (
                  <span key={`${chapter.name}-${macro}`} className="live-chip">
                    {macro}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Operator Cues</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.operator_cues.map((cue) => (
            <article key={`${cue.chapter_name}-${cue.rytm_stage_command}`}>
              <strong>{cue.label}</strong>
              <span>
                OXI {cue.oxi_action} / Rytm {cue.rytm_stage_command}
              </span>
              <small>
                inspect {cue.inspect_command} / fire {cue.fire_command} / recover{' '}
                {cue.recovery_command}
              </small>
              <small>{cue.expected_result}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Pad Lane Checks</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.pad_lane_checks.map((lane) => (
            <article key={lane.summary}>
              <strong>{lane.summary}</strong>
              <span>pads {lane.pads.join(', ')}</span>
              <small>{lane.expected_motion}</small>
              <small>{lane.warning}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Next Hardware Validations</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.hardware_validation_runway.map((step) => (
            <article key={step.name}>
              <strong>{step.name}</strong>
              <span>
                {step.device} / {step.validation_mode}
              </span>
              <small>{step.operator_path}</small>
              <small>{step.expected_evidence}</small>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">A4 Promotion Gates</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.promotion_criteria.map((criterion) => (
            <article key={criterion.name}>
              <strong>{toHumanLabel(criterion.name)}</strong>
              <span>
                {criterion.device} / {criterion.current_status}
              </span>
              <small>{criterion.required_evidence}</small>
              <small>{criterion.safety_note}</small>
            </article>
          ))}
        </div>

        <div className="live-chip-row">
          {model.rehearsal_board.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface"
        data-testid="performance-console-analyzer-panel"
        aria-labelledby="console-analyzer-panel-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-analyzer-panel-title">{model.analyzer_panel.title}</h2>
          <span>
            {model.analyzer_panel.panel_status} / {model.analyzer_panel.panel_mode}
          </span>
        </header>
        <p className="panel-meta">{model.analyzer_panel.reference_label}</p>
        <div className="performance-console-list" aria-label="Analyzer spectrum">
          {model.analyzer_panel.spectrum_bands.map((band) => (
            <article key={band.key}>
              <strong>{band.label}</strong>
              <span>
                {band.low_hz}-{band.high_hz} Hz / {band.status}
              </span>
              <small>{band.value_percent}%</small>
            </article>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Analyzer required actions">
          {model.analyzer_panel.required_actions.map((action) => (
            <span key={action} className="live-chip">
              {action}
            </span>
          ))}
        </div>
        <div className="live-chip-row" aria-label="Analyzer blocked actions">
          {model.analyzer_panel.blocked_actions.map((action) => (
            <span key={action} className="live-chip live-chip-blocked">
              {action}
            </span>
          ))}
        </div>
        <div className="performance-console-macro-actions">
          {orderedAnalyzerControls(model.analyzer_panel.controls).map((control) => (
            <button
              key={control.key}
              type="button"
              className="live-readiness-action"
              disabled={!control.enabled}
              title={control.status}
            >
              {control.label} analyzer
            </button>
          ))}
        </div>
      </section>

      <section
        className="performance-console-surface"
        data-testid="performance-console-command-queue"
        aria-labelledby="console-command-queue-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-command-queue-title">Command Queue</h2>
          <span>{model.command_queue.queue_status}</span>
        </header>
        <div className="performance-console-list">
          {model.command_queue.queued_commands.map((command) => (
            <article key={command.key}>
              <strong>{command.label}</strong>
              <span>{command.target}</span>
              <small>
                {command.status} / {command.estimated_message_count} dry-run messages
              </small>
            </article>
          ))}
        </div>
        <button type="button" className="live-readiness-action" disabled>
          Dry-run SEND
        </button>
      </section>

      <section
        className="performance-console-surface"
        data-testid="performance-console-safety"
        aria-labelledby="console-safety-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-safety-title">Safety Checklist</h2>
          <span>
            {model.safety_checklist.passed_count} / {model.safety_checklist.total_count}
          </span>
        </header>
        <div className="performance-console-list">
          {model.safety_checklist.items.map((item) => (
            <article key={item.key}>
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
          title={model.safety_checklist.arm_gate.reason}
        >
          {model.safety_checklist.arm_gate.label} / {model.safety_checklist.arm_gate.state}
        </button>
      </section>

      <footer className="performance-console-bottom-strip" data-testid="performance-console-bottom-strip">
        <span>Session {model.session_label}</span>
        <span>Devices {deviceListLabel(sortedDevices)}</span>
        <span>Mock {mockSummary(sortedDevices)}</span>
        <span>Rytm {rytmDevice?.hardware_state ?? 'not present'}</span>
        <span>A4 {analogFourDevice?.hardware_state ?? 'not present'}</span>
        <span>Journal entries {model.style_queue.journal_cards.length}</span>
        <span>Cockpit Mode {model.hardware_mode}</span>
      </footer>
    </main>
  );
}
