import type {
  LiveGuiAnalyzerPanelControlDict,
  LiveGuiDeviceInventoryCardDict,
  LiveGuiPerformanceConsoleMacroActionCardDict,
  LiveGuiPerformanceConsoleModelDict,
  LiveGuiRytmPadSurfaceCardDict,
} from '../types/live_gui_protocol';

export interface PerformanceConsoleProps {
  model: LiveGuiPerformanceConsoleModelDict;
  packetSource?: string;
}

const ANALYZER_CONTROL_ORDER: ReadonlyArray<string> = ['preview', 'dry_run', 'arm_hardware'];

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

export function PerformanceConsole({
  model,
  packetSource = 'passive packet',
}: PerformanceConsoleProps): JSX.Element {
  const a4SetPlan = model.performance_flow.analog_four_set_plan;
  const macroPath = [a4SetPlan.current_macro, ...a4SetPlan.up_next_macros].join(' -> ');

  return (
    <main
      className="performance-console"
      data-testid="performance-console"
      aria-labelledby="performance-console-title"
    >
      <header className="performance-console-header">
        <div>
          <p className="panel-meta">{model.session_label}</p>
          <h1 id="performance-console-title">RytmRandomizer Cockpit Performance Console</h1>
        </div>
        <div className="performance-console-status" aria-label="Console safety state">
          <span>{model.console_status}</span>
          <span>{model.hardware_mode}</span>
          <span>{packetSource}</span>
        </div>
      </header>

      <section className="performance-console-surface" aria-labelledby="console-device-rail-title">
        <h2 id="console-device-rail-title">Device Rail</h2>
        <div className="performance-console-device-grid">
          {orderedDevices(model.device_inventory.cards).map((device) => (
            <article
              key={device.device_id}
              className="performance-console-device"
              data-testid={`performance-console-device-${device.device_id}`}
            >
              <strong>{device.display_name}</strong>
              <span>{device.role_summary}</span>
              <small>
                {device.track_count} tracks / port {device.port_state} / mock {device.mock_state}
              </small>
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

      <section className="performance-console-surface" aria-labelledby="console-pad-grid-title">
        <header className="performance-console-section-header">
          <h2 id="console-pad-grid-title">Rytm 12-Pad Snapshot Surface</h2>
          <span>
            {model.rytm_pad_surface.active_pad_count} active / {model.rytm_pad_surface.pad_count} pads
          </span>
        </header>
        <div className="performance-console-pad-grid">
          {orderedPads(model.rytm_pad_surface.cards).map((pad) => (
            <article
              key={pad.pad}
              className={`performance-console-pad ${pad.surface_state}`}
              data-testid={`performance-console-pad-${pad.pad}`}
            >
              <span>Pad {pad.pad}</span>
              <strong>{pad.label}</strong>
              <small>
                {pad.track_code} / {pad.default_role} / {pad.default_machine_label}
              </small>
            </article>
          ))}
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
          {orderedMacroActions(model.macro_action_deck.cards).map((card) => (
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

        <h3 className="performance-console-subheading">Studio Workflow</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.studio_workflow.map((step) => (
            <article key={step}>
              <strong>{step}</strong>
            </article>
          ))}
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

        <h3 className="performance-console-subheading">Macro Checkpoints</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.macro_checkpoints.map((checkpoint) => (
            <article key={checkpoint.name}>
              <strong>{checkpoint.label}</strong>
              <span>
                {checkpoint.risk_label} / pads {checkpoint.affected_pads.join(', ')}
              </span>
              <small>{checkpoint.summary}</small>
              <small>recover with {checkpoint.recovery_action}</small>
              <div className="live-chip-row">
                {checkpoint.checkpoints.map((check) => (
                  <span key={`${checkpoint.name}-${check}`} className="live-chip">
                    {check}
                  </span>
                ))}
              </div>
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

        <h3 className="performance-console-subheading">Queued Hardware Validations</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.next_hardware_validations.map((validation) => (
            <article key={validation}>
              <strong>{validation}</strong>
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

        <h3 className="performance-console-subheading">Recovery Checks</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.recovery_checks.map((check) => (
            <article key={check}>
              <strong>{check}</strong>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Replay Commands</h3>
        <div className="performance-console-list">
          {model.rehearsal_board.replay_commands.map((command) => (
            <article key={command.name}>
              <strong>{command.name}</strong>
              <span>
                {command.execution_mode} / sends {command.sends_midi}
              </span>
              <small>{command.command}</small>
              <small>{command.purpose}</small>
              <small>{command.expected_observation}</small>
              <div className="live-chip-row">
                <span className={command.opens_ports ? 'live-chip live-chip-blocked' : 'live-chip'}>
                  {command.opens_ports ? 'opens ports' : 'opens no ports'}
                </span>
                <span className="live-chip">{command.safety_note}</span>
              </div>
            </article>
          ))}
        </div>

        <h3 className="performance-console-subheading">Safety Lines</h3>
        <div className="live-chip-row">
          {model.rehearsal_board.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
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
        data-testid="performance-console-style-queue"
        aria-labelledby="console-style-queue-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-style-queue-title">Style Queue / Journal</h2>
          <span>{model.style_queue.deck_status}</span>
        </header>
        <h3 className="performance-console-subheading">Style Crates</h3>
        <div className="performance-console-list" aria-label="Style crates">
          {model.style_queue.crate_cards.map((crate) => (
            <article key={crate.crate_key} data-testid={`style-crate-${toTestIdKey(crate.crate_key)}`}>
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
          {model.style_queue.queue_cards.map((move) => (
            <article
              key={move.queue_key}
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
        data-testid="performance-console-snapshot-history"
        aria-labelledby="console-snapshot-history-title"
      >
        <header className="performance-console-section-header">
          <h2 id="console-snapshot-history-title">Snapshot History</h2>
          <span>{model.snapshot_history.entry_count} entries</span>
        </header>
        <div className="performance-console-list">
          {model.snapshot_history.entries.map((entry) => (
            <article key={entry.key}>
              <strong>{entry.snapshot_id}</strong>
              <span>{entry.label}</span>
              <small>{entry.summary}</small>
            </article>
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

      <section
        className="performance-console-surface performance-console-wide"
        data-testid="performance-console-blocked-actions"
        aria-labelledby="console-blocked-actions-title"
      >
        <h2 id="console-blocked-actions-title">Blocked Active Actions</h2>
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
    </main>
  );
}
