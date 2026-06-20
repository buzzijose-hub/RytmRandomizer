import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { PerformanceConsole } from '../../src/cockpit/PerformanceConsole';
import type { LiveGuiPerformanceConsoleModelDict } from '../../src/types/live_gui_protocol';
import { FakeCockpitClient } from './_fixtures';
import { performanceConsoleModel } from './performanceConsoleFixture';

function performanceConsoleModelWithActiveDryRunBoundaries(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    macro_action_deck: {
      ...performanceConsoleModel.macro_action_deck,
      cards: performanceConsoleModel.macro_action_deck.cards.map((card) =>
        card.macro_key === 'hard-groove' ? { ...card, dry_run_only: false } : card,
      ),
    },
    rytm_lane_policy_matrix: {
      ...performanceConsoleModel.rytm_lane_policy_matrix,
      macro_rows: performanceConsoleModel.rytm_lane_policy_matrix.macro_rows.map((row) =>
        row.macro_key === 'hard-groove'
          ? {
              ...row,
              pad_policy_cards: {
                ...row.pad_policy_cards,
                '10': {
                  amount: null,
                  density: null,
                  bias: null,
                  lane_policies: {},
                  section_family_allowlists: {},
                },
                '11': {
                  amount: 'normal',
                  density: 'medium',
                  bias: 'brighter',
                  lane_policies: {},
                  section_family_allowlists: {
                    SRC: ['tune'],
                    AMP: ['overdrive'],
                  },
                },
              },
            }
          : row,
      ),
    },
    style_queue: {
      ...performanceConsoleModel.style_queue,
      queue_cards: performanceConsoleModel.style_queue.queue_cards.map((move) =>
        move.queue_key === 'queue-opening-shadow' ? { ...move, dry_run_only: false } : move,
      ),
    },
  };
}

function performanceConsoleModelWithHudFallbacks(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    device_inventory: {
      ...performanceConsoleModel.device_inventory,
      cards: [
        {
          ...performanceConsoleModel.device_inventory.cards[0]!,
          device_id: 'generic_device',
          display_name: 'Generic Device',
          track_count: 1,
          passive: false,
        },
      ],
    },
    macro_action_deck: {
      ...performanceConsoleModel.macro_action_deck,
      current_macro_key: 'missing-macro',
      cards: [],
    },
    snapshot_history: {
      ...performanceConsoleModel.snapshot_history,
      current_id: 'missing-snapshot',
      entry_count: 2,
      entries: [
        ...performanceConsoleModel.snapshot_history.entries,
        {
          ...performanceConsoleModel.snapshot_history.entries[0]!,
          key: 'history-older',
          order: 1,
          snapshot_id: 'console-snap-older',
          label: 'Earlier warehouse take',
          summary: 'older noncurrent take',
          is_current: false,
        },
      ],
    },
    style_queue: {
      ...performanceConsoleModel.style_queue,
      queue_cards: [],
    },
  };
}

function performanceConsoleModelWithNamedMidiPort(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    command_queue: {
      ...performanceConsoleModel.command_queue,
      hardware_armed: true,
    },
    safety_checklist: {
      ...performanceConsoleModel.safety_checklist,
      arm_gate: {
        ...performanceConsoleModel.safety_checklist.arm_gate,
        midi_port_name: 'Elektron Analog Rytm MKII 1',
        midi_port_open: true,
      },
    },
  };
}

function performanceConsoleModelWithUnnamedOpenMidiPort(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    safety_checklist: {
      ...performanceConsoleModel.safety_checklist,
      arm_gate: {
        ...performanceConsoleModel.safety_checklist.arm_gate,
        midi_port_open: true,
      },
    },
  };
}

function performanceConsoleModelWithScanningPortState(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModelWithHudFallbacks(),
    device_inventory: {
      ...performanceConsoleModel.device_inventory,
      cards: [
        {
          ...performanceConsoleModel.device_inventory.cards[0]!,
          device_id: 'generic_device',
          display_name: 'Generic Device',
          track_count: 1,
          port_state: 'scanning',
          passive: false,
        },
      ],
    },
  };
}

function performanceConsoleModelWithNoDevices(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModelWithHudFallbacks(),
    device_inventory: {
      ...performanceConsoleModel.device_inventory,
      cards: [],
    },
  };
}

function performanceConsoleModelWithNoSnapshotHistory(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModelWithHudFallbacks(),
    command_queue: {
      ...performanceConsoleModel.command_queue,
      dry_run_active: false,
      queued_commands: [],
    },
    snapshot_history: {
      ...performanceConsoleModel.snapshot_history,
      current_id: 'missing-snapshot',
      entry_count: 0,
      entries: [],
    },
  };
}

function performanceConsoleModelWithSelectableHistory(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    snapshot_history: {
      ...performanceConsoleModel.snapshot_history,
      current_id: 'console-snap-03',
      current_index: 2,
      entry_count: 3,
      entries: [
        {
          ...performanceConsoleModel.snapshot_history.entries[0]!,
          key: 'history-01',
          order: 1,
          snapshot_id: 'console-snap-01',
          label: 'Opening clean take',
          parent_id: null,
          scene_slot: 'S0',
          bpm_label: '124 BPM',
          is_current: false,
          can_load: true,
          can_undo_to: true,
          summary: 'earlier clean anchor',
          test_id: 'snapshot-history-console-snap-01',
        },
        {
          ...performanceConsoleModel.snapshot_history.entries[0]!,
          key: 'history-02',
          order: 2,
          snapshot_id: 'console-snap-02',
          label: 'Pressure build take',
          parent_id: 'console-snap-01',
          scene_slot: 'S1',
          bpm_label: '126 BPM',
          is_current: false,
          can_load: true,
          can_undo_to: true,
          summary: 'middle pressure build',
          test_id: 'snapshot-history-console-snap-02',
        },
        performanceConsoleModel.snapshot_history.entries[0]!,
      ],
    },
  };
}

function performanceConsoleModelWithEmptyStyleDeck(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    style_queue: {
      ...performanceConsoleModel.style_queue,
      crate_cards: [],
      queue_cards: [],
      journal_cards: [],
    },
  };
}

function performanceConsoleModelWithAllowedWorkbenchGate(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    live_kit_capture_workbench: {
      ...performanceConsoleModel.live_kit_capture_workbench,
      mutation_readiness: {
        ...performanceConsoleModel.live_kit_capture_workbench.mutation_readiness,
        gates: performanceConsoleModel.live_kit_capture_workbench.mutation_readiness.gates.map(
          (gate) =>
            gate.gate_key === 'manual-fire'
              ? { ...gate, cockpit_action_allowed: true }
              : gate,
        ),
      },
    },
  };
}

function performanceConsoleModelWithOptionalPackageCheck(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    live_kit_package_audition: {
      ...performanceConsoleModel.live_kit_package_audition,
      package_checks: performanceConsoleModel.live_kit_package_audition.package_checks.map(
        (check) =>
          check.check_key === 'journal-preview-only'
            ? { ...check, required: false }
            : check,
      ),
    },
  };
}

function performanceConsoleModelWithoutOperatorPackage(): LiveGuiPerformanceConsoleModelDict {
  const legacyModel: Partial<LiveGuiPerformanceConsoleModelDict> = { ...performanceConsoleModel };
  delete legacyModel.live_kit_operator_package;
  return legacyModel as LiveGuiPerformanceConsoleModelDict;
}

function performanceConsoleModelWithMissingOperatorPackageAuditionSlot(): LiveGuiPerformanceConsoleModelDict {
  const operatorStep = performanceConsoleModel.live_kit_operator_package.operator_steps[0]!;
  const slotBinding = performanceConsoleModel.live_kit_operator_package.slot_bindings[0]!;
  return {
    ...performanceConsoleModelWithSelectableHistory(),
    live_kit_operator_package: {
      ...performanceConsoleModel.live_kit_operator_package,
      operator_steps: [
        {
          ...operatorStep,
          step_key: 'stage-missing-slot',
          slot_key: 'missing-audition-slot',
          label: 'Missing Slot Operator',
          stage_target: 'missing-audition-slot',
        },
      ],
      slot_bindings: [
        {
          ...slotBinding,
          slot_key: 'missing-audition-slot',
          package_export_key: 'operator-package-missing-audition-slot',
        },
      ],
    },
  };
}

function performanceConsoleModelWithUnboundOperatorPackageStep(): LiveGuiPerformanceConsoleModelDict {
  const operatorStep = performanceConsoleModel.live_kit_operator_package.operator_steps[0]!;
  const recoveryRequirement =
    performanceConsoleModel.live_kit_operator_package.recovery_requirements[0]!;
  return {
    ...performanceConsoleModelWithSelectableHistory(),
    live_kit_operator_package: {
      ...performanceConsoleModel.live_kit_operator_package,
      operator_steps: [
        {
          ...operatorStep,
          step_key: 'stage-unbound-operator-slot',
          slot_key: 'unbound-operator-slot',
          label: 'Unbound Operator',
          stage_target: 'local-set-plan',
        },
      ],
      slot_bindings: [],
      recovery_requirements: [
        {
          ...recoveryRequirement,
          requirement_key: 'optional-recovery-note',
          label: 'Optional Recovery',
          required_before_send: false,
          evidence: 'Optional operator note only.',
        },
      ],
    },
  };
}

describe('PerformanceConsole', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders the passive console packet without enabling hardware actions', () => {
    render(<PerformanceConsole model={performanceConsoleModel} />);

    expect(screen.getByTestId('performance-console')).toHaveTextContent(
      'RytmRandomizer Cockpit Performance Console',
    );
    const safetyState = screen.getByLabelText('Console safety state');
    expect(within(safetyState).getByText('mock-safe')).toBeInTheDocument();
    expect(within(safetyState).getByText('passive')).toBeInTheDocument();
    expect(within(safetyState).getByText('passive packet')).toBeInTheDocument();
    expect(screen.getByText('Warehouse arc')).toBeInTheDocument();

    const topbar = screen.getByTestId('performance-console-topbar');
    expect(topbar).toHaveTextContent('MOCK SAFE - No MIDI Port Open');
    expect(topbar).toHaveTextContent('MIDI PortNo MIDI Port Open');
    expect(topbar).toHaveTextContent('ArmLOCKED');
    expect(topbar).toHaveTextContent('pending');
    expect(topbar).toHaveTextContent('dry-run active');
    expect(topbar).toHaveTextContent('Scene A01');
    expect(topbar).toHaveTextContent('128 BPM');
    expect(within(topbar).getByRole('button', { name: /tap tempo/i })).toBeDisabled();

    const leftRail = screen.getByTestId('performance-console-left-rail');
    expect(leftRail).toHaveTextContent('Device Rail');
    expect(leftRail).toHaveTextContent('Analog Rytm MKII');
    expect(leftRail).toHaveTextContent('Analog Four MKII');
    expect(leftRail).toHaveTextContent('PASSED');
    expect(leftRail).toHaveTextContent('Hardware arm remains locked in this passive console packet.');
    expect(leftRail).toHaveTextContent('No MIDI Port Open');
    expect(leftRail).toHaveTextContent('passed');
    expect(leftRail).toHaveTextContent('Arm Hardware');
    expect(leftRail).toHaveTextContent('locked');

    const snapshotDeck = screen.getByTestId('performance-console-snapshot-deck');
    expect(snapshotDeck).toHaveTextContent('Snapshot - Analog Rytm MKII');
    expect(snapshotDeck).toHaveTextContent('Scene A01');
    expect(snapshotDeck).toHaveTextContent('Snapshot console-snap-03');
    expect(snapshotDeck).toHaveTextContent('128 BPM');
    expect(snapshotDeck).toHaveTextContent('Snapshot History / Mutation Journal');
    expect(within(snapshotDeck).getAllByTestId(/performance-console-pad-/)).toHaveLength(12);

    const mutationPanel = screen.getByTestId('performance-console-mutation-panel');
    expect(mutationPanel).toHaveTextContent('Mutation Panel');
    expect(mutationPanel).toHaveTextContent('Queue (');
    expect(mutationPanel).toHaveTextContent('Depth');
    expect(mutationPanel).toHaveTextContent('Profile');
    expect(mutationPanel).toHaveTextContent('Mutation Summary');
    expect(mutationPanel).toHaveTextContent('Blocked Hardware Actions');
    expect(
      within(mutationPanel).getByRole('button', { name: /preview before real send/i }),
    ).toBeDisabled();
    expect(within(mutationPanel).getByRole('button', { name: /review kit core/i })).toBeDisabled();
    expect(
      within(mutationPanel).getByRole('button', { name: /queue mutate pad 11/i }),
    ).toBeDisabled();
    expect(
      within(mutationPanel).getByRole('button', { name: /arm hardware locked/i }),
    ).toBeDisabled();

    const bottomStrip = screen.getByTestId('performance-console-bottom-strip');
    expect(bottomStrip).toHaveTextContent('Session Warehouse arc');
    expect(bottomStrip).toHaveTextContent(
      'Devices Elektron Analog Rytm MKII + Elektron Analog Four MKII',
    );
    expect(bottomStrip).toHaveTextContent('Mock Mock Safe / Review Only');
    expect(bottomStrip).toHaveTextContent('Rytm disarmed');
    expect(bottomStrip).toHaveTextContent('A4 disarmed');
    expect(bottomStrip).toHaveTextContent('Journal entries');
    expect(bottomStrip).toHaveTextContent('Cockpit Mode passive');

    expect(screen.getByTestId('performance-console-device-analog_rytm_mk2')).toHaveTextContent(
      'Elektron Analog Rytm MKII',
    );
    expect(screen.getByTestId('performance-console-device-analog_four_mk2')).toHaveTextContent(
      'Elektron Analog Four MKII',
    );

    expect(screen.getAllByTestId(/performance-console-pad-/)).toHaveLength(12);
    expect(screen.getByTestId('performance-console-pad-11')).toHaveTextContent('SY Raw');
    expect(screen.getByTestId('performance-console-pad-12')).toHaveTextContent('Pad 12');

    const lanePolicyMatrix = screen.getByTestId('performance-console-rytm-lane-policy-matrix');
    expect(lanePolicyMatrix).toHaveTextContent('Rytm Lane Policy Matrix');
    expect(lanePolicyMatrix).toHaveTextContent('passive-ready');
    expect(lanePolicyMatrix).toHaveTextContent('reserved-src-fx');
    expect(lanePolicyMatrix).toHaveTextContent('pads 5, 9, 10, 11');
    expect(lanePolicyMatrix).toHaveTextContent('SRC-first');
    expect(lanePolicyMatrix).toHaveTextContent('filter=off');
    expect(lanePolicyMatrix).toHaveTextContent('lfo=off');
    expect(lanePolicyMatrix).toHaveTextContent('tom/source');
    expect(lanePolicyMatrix).toHaveTextContent('pad-12-supported');
    expect(lanePolicyMatrix).toHaveTextContent('hard-groove');
    expect(lanePolicyMatrix).toHaveTextContent('Hard Groove');
    expect(lanePolicyMatrix).toHaveTextContent('AMP: delay, overdrive, reverb');
    expect(lanePolicyMatrix).toHaveTextContent('dispatch Rytm lane policy from Cockpit console');
    expect(
      within(lanePolicyMatrix).getByRole('button', { name: /apply rytm lane policy/i }),
    ).toBeDisabled();
    expect(
      within(lanePolicyMatrix).getByRole('button', { name: /send rytm policy/i }),
    ).toBeDisabled();

    const flow = screen.getByTestId('performance-console-flow');
    expect(flow).toHaveTextContent('capture-anchor');
    expect(flow).toHaveTextContent('kit-core');
    expect(flow).toHaveTextContent('warehouse-arc');
    expect(flow).toHaveTextContent('A4 full macro SEND');

    const a4ReviewSurface = screen.getByTestId('performance-console-a4-review-surface');
    expect(a4ReviewSurface).toHaveTextContent('Analog Four Review Surface');
    expect(a4ReviewSurface).toHaveTextContent('review-only');
    expect(a4ReviewSurface).toHaveTextContent('warehouse-arc');
    expect(a4ReviewSurface).toHaveTextContent('focus hard-groove');
    expect(a4ReviewSurface).toHaveTextContent('Hard Groove');
    expect(a4ReviewSurface).toHaveTextContent('Dub Pressure');
    expect(a4ReviewSurface).toHaveTextContent('Industrial Transition');
    expect(a4ReviewSurface).toHaveTextContent('Track 1 / FLT Frequency');
    expect(a4ReviewSurface).toHaveTextContent('cc-ready');
    expect(a4ReviewSurface).toHaveTextContent('Run the input-only A4 soft capture first.');
    expect(a4ReviewSurface).toHaveTextContent('At least one operator-present validation pass is clean');
    expect(a4ReviewSurface).toHaveTextContent('A4 full macro SEND');
    expect(a4ReviewSurface).toHaveTextContent('A4 unattended macro playback');
    expect(a4ReviewSurface).toHaveTextContent('A4 full macro SEND remains blocked');
    expect(
      within(a4ReviewSurface).getByRole('button', { name: /review a4 hard-groove/i }),
    ).toBeDisabled();
    expect(within(a4ReviewSurface).getByRole('button', { name: /promote a4 macro/i })).toBeDisabled();

    const macroActions = screen.getByTestId('performance-console-macro-actions');
    expect(macroActions).toHaveTextContent('Live Macro Actions');
    expect(macroActions).toHaveTextContent('hard-groove');
    expect(macroActions).toHaveTextContent('pads 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12');
    expect(macroActions).toHaveTextContent('stage-review-send');
    expect(macroActions).toHaveTextContent('fire macro from Cockpit console');
    expect(within(macroActions).getAllByRole('button', { name: /prepare/i })[0]).toBeDisabled();
    expect(within(macroActions).getAllByRole('button', { name: /send/i })[0]).toBeDisabled();
    const hardGrooveMacro = within(macroActions).getByTestId('macro-action-hard-groove');
    expect(hardGrooveMacro).toHaveTextContent('recover home');
    expect(hardGrooveMacro).toHaveTextContent('hardware blocked');
    expect(hardGrooveMacro).toHaveTextContent('dry-run only');

    const rehearsalBoard = screen.getByTestId('performance-console-rehearsal-board');
    expect(rehearsalBoard).toHaveTextContent('Rehearsal Board');
    expect(rehearsalBoard).toHaveTextContent('passive-ready');
    expect(rehearsalBoard).toHaveTextContent('Capture Anchor');
    expect(rehearsalBoard).toHaveTextContent('Establish Groove');
    expect(rehearsalBoard).toHaveTextContent('macro hard-groove');
    expect(rehearsalBoard).toHaveTextContent('Pads 5, 9, 10, 11: SRC stays important');
    expect(rehearsalBoard).toHaveTextContent('Pads 6-8: tom/source movement');
    expect(rehearsalBoard).toHaveTextContent('a4-soft-capture');
    expect(rehearsalBoard).toHaveTextContent('A4 Input Label Coverage');
    expect(rehearsalBoard).toHaveTextContent('fire rehearsal cue from Cockpit console');
    expect(
      within(rehearsalBoard).getByRole('button', { name: /launch armed shell/i }),
    ).toBeDisabled();
    expect(within(rehearsalBoard).getByRole('button', { name: /fire cue/i })).toBeDisabled();

    const controllerBrainPanel = screen.getByTestId('performance-console-controller-brain-panel');
    expect(controllerBrainPanel).toHaveTextContent('Controller Brain');
    expect(controllerBrainPanel).toHaveTextContent('passive-ready');
    expect(controllerBrainPanel).toHaveTextContent('generic-16-encoder-performance');
    expect(controllerBrainPanel).toHaveTextContent('controller template rows 112');
    expect(controllerBrainPanel).toHaveTextContent('global-brain');
    expect(controllerBrainPanel).toHaveTextContent('slots 1-16');
    expect(controllerBrainPanel).toHaveTextContent(
      'rytm-pads-5-8:01 -> rytm.pad5.source_amount',
    );
    expect(controllerBrainPanel).toHaveTextContent('snapshot.panic_home');
    expect(controllerBrainPanel).toHaveTextContent('MIDI learn or raw CC capture');
    expect(within(controllerBrainPanel).getByRole('button', { name: /open controller input/i }))
      .toBeDisabled();
    expect(within(controllerBrainPanel).getByRole('button', { name: /dispatch controller cue/i }))
      .toBeDisabled();

    const liveKitCapturePanel = screen.getByTestId('performance-console-live-kit-capture-panel');
    expect(liveKitCapturePanel).toHaveTextContent('Live Kit Capture');
    expect(liveKitCapturePanel).toHaveTextContent('Mutate the kit you are actually playing.');
    expect(liveKitCapturePanel).toHaveTextContent('receive-kit-sysex');
    expect(liveKitCapturePanel).toHaveTextContent('mutate-captured-kit');
    expect(liveKitCapturePanel).toHaveTextContent('captured-anchor recovery');
    expect(liveKitCapturePanel).toHaveTextContent('live-kit-capture');
    expect(liveKitCapturePanel).toHaveTextContent('controller-complement');
    expect(liveKitCapturePanel).toHaveTextContent('receive kit from Cockpit console');
    expect(within(liveKitCapturePanel).getByRole('button', { name: /receive kit/i }))
      .toBeDisabled();
    expect(
      within(liveKitCapturePanel).getByRole('button', { name: /mutate captured kit/i }),
    ).toBeDisabled();
    expect(
      within(liveKitCapturePanel).getByRole('button', { name: /send captured plan/i }),
    ).toBeDisabled();

    const liveKitCaptureWorkbench = screen.getByTestId(
      'performance-console-live-kit-capture-workbench',
    );
    expect(liveKitCaptureWorkbench).toHaveTextContent('Live Kit Capture Workbench');
    expect(liveKitCaptureWorkbench).toHaveTextContent('current-live-kit');
    expect(liveKitCaptureWorkbench).toHaveTextContent('candidate-variation');
    expect(liveKitCaptureWorkbench).toHaveTextContent('recovery-anchor');
    expect(liveKitCaptureWorkbench).toHaveTextContent('resnapshot-target');
    expect(liveKitCaptureWorkbench).toHaveTextContent('twelve-pad-context');
    expect(liveKitCaptureWorkbench).toHaveTextContent('manual-fire');
    expect(liveKitCaptureWorkbench).toHaveTextContent('z-send');
    expect(liveKitCaptureWorkbench).toHaveTextContent(
      'live-kit-capture-workbench-package-v1',
    );
    expect(liveKitCaptureWorkbench).toHaveTextContent(
      'apply captured-kit package from Cockpit console',
    );
    expect(within(liveKitCaptureWorkbench).getByRole('button', { name: /receive kit/i }))
      .toBeDisabled();
    expect(
      within(liveKitCaptureWorkbench).getByRole('button', { name: /stage mutation/i }),
    ).toBeDisabled();
    expect(
      within(liveKitCaptureWorkbench).getByRole('button', { name: /apply package/i }),
    ).toBeDisabled();
    expect(
      within(liveKitCaptureWorkbench).getByRole('button', { name: /export package/i }),
    ).toBeDisabled();
    expect(
      within(liveKitCaptureWorkbench).getByRole('button', { name: /send captured plan/i }),
    ).toBeDisabled();

    const liveKitPackageAudition = screen.getByTestId(
      'performance-console-live-kit-package-audition',
    );
    expect(liveKitPackageAudition).toHaveTextContent('Live Kit Package Audition');
    expect(liveKitPackageAudition).toHaveTextContent('passive-ready');
    expect(liveKitPackageAudition).toHaveTextContent('captured-base');
    expect(liveKitPackageAudition).toHaveTextContent('hard-groove-lift');
    expect(liveKitPackageAudition).toHaveTextContent('Industrial/Broken');
    expect(liveKitPackageAudition).toHaveTextContent('queue industrial-pressure');
    expect(liveKitPackageAudition).toHaveTextContent('recovery-visible-before-fire');
    expect(liveKitPackageAudition).toHaveTextContent('Captured Kit Audition 0001');
    expect(liveKitPackageAudition).toHaveTextContent('live-kit-audition-0001');
    expect(liveKitPackageAudition).toHaveTextContent(
      'send audition variation from Cockpit console',
    );
    expect(
      within(liveKitPackageAudition).getByRole('button', { name: /generate package/i }),
    ).toBeDisabled();
    expect(
      within(liveKitPackageAudition).getByRole('button', { name: /audition variation/i }),
    ).toBeDisabled();
    expect(
      within(liveKitPackageAudition).getByRole('button', { name: /commit favorite/i }),
    ).toBeDisabled();
    expect(
      within(liveKitPackageAudition).getByRole('button', { name: /write journal/i }),
    ).toBeDisabled();
    expect(
      within(liveKitPackageAudition).getByRole('button', { name: /send variation/i }),
    ).toBeDisabled();

    const liveKitOperatorPackage = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    expect(liveKitOperatorPackage).toHaveTextContent('Live Kit Operator Package');
    expect(liveKitOperatorPackage).toHaveTextContent('passive-ready');
    expect(liveKitOperatorPackage).toHaveTextContent('live-kit-operator-package');
    expect(liveKitOperatorPackage).toHaveTextContent('hard-groove-lift');
    expect(liveKitOperatorPackage).toHaveTextContent('stage-local-set-plan');
    expect(liveKitOperatorPackage).toHaveTextContent('operator-package-hard-groove-lift');
    expect(liveKitOperatorPackage).toHaveTextContent('z-then-send');
    expect(liveKitOperatorPackage).toHaveTextContent('browser-local-only');
    expect(liveKitOperatorPackage).toHaveTextContent('Captured Kit Audition 0001');
    expect(liveKitOperatorPackage).toHaveTextContent('send operator package from Cockpit console');
    expect(within(liveKitOperatorPackage).getByRole('button', {
      name: /send operator package/i,
    })).toBeDisabled();

    const styleQueue = screen.getByTestId('performance-console-style-queue');
    expect(styleQueue).toHaveTextContent('Style Crates');
    expect(within(styleQueue).getAllByTestId(/^style-crate-/)).toHaveLength(9);
    const darkHypnoticCrate = within(styleQueue).getByTestId('style-crate-dark-hypnotic');
    expect(darkHypnoticCrate).toHaveTextContent('Deeper & Minimal');
    expect(darkHypnoticCrate).toHaveTextContent('energy 5');
    expect(darkHypnoticCrate).toHaveTextContent('risk 3');
    expect(darkHypnoticCrate).toHaveTextContent('pads 1, 3, 11');
    expect(darkHypnoticCrate).toHaveTextContent('hypnotic');
    expect(darkHypnoticCrate).toHaveTextContent('minimal');
    expect(darkHypnoticCrate).toHaveTextContent('shadow');
    expect(
      within(darkHypnoticCrate).getByRole('button', { name: /stage shadow filter pressure/i }),
    ).toBeDisabled();
    const industrialCrate = within(styleQueue).getByTestId('style-crate-industrial-broken');
    expect(industrialCrate).toHaveTextContent('Industrial/Broken');
    expect(industrialCrate).toHaveTextContent('Metal & Drive');
    expect(industrialCrate).toHaveTextContent('energy 8');
    expect(industrialCrate).toHaveTextContent('risk 7');
    expect(industrialCrate).toHaveTextContent('pads 3, 4, 8, 10, 11');
    expect(styleQueue).toHaveTextContent('Dark Hypnotic');
    expect(styleQueue).toHaveTextContent('Shadow Filter Pressure');
    expect(styleQueue).toHaveTextContent('Pressure Rattle');
    expect(styleQueue).toHaveTextContent('Preview before real send');
    expect(styleQueue).toHaveTextContent('recover Back To Clean Handoff');
    expect(styleQueue).toHaveTextContent('pads 1, 3, 11');
    expect(styleQueue).toHaveTextContent('dry-run only');

    const analyzerPanel = screen.getByTestId('performance-console-analyzer-panel');
    expect(analyzerPanel).toHaveTextContent('Analyzer (Post-Mutation Preview)');
    expect(analyzerPanel).toHaveTextContent('empty');
    expect(analyzerPanel).toHaveTextContent('No reference loaded');
    expect(analyzerPanel).toHaveTextContent('load-reference');
    expect(within(analyzerPanel).getByRole('button', { name: /preview analyzer/i })).toBeDisabled();
    expect(within(analyzerPanel).getByRole('button', { name: /dry run analyzer/i })).toBeDisabled();
    expect(within(analyzerPanel).getByText('record-audio')).toBeInTheDocument();

    expect(screen.getByTestId('performance-console-snapshot-history')).toHaveTextContent(
      'console-snap-03',
    );
    expect(screen.getByTestId('performance-console-command-queue')).toHaveTextContent(
      'Mutate Pad 11',
    );
    expect(screen.getByTestId('performance-console-safety')).toHaveTextContent('4 / 4');

    const blocked = screen.getByTestId('performance-console-blocked-actions');
    expect(within(blocked).getByText('a4_outbound_macro_send')).toBeInTheDocument();
    expect(within(blocked).getByText('send MIDI from snapshot history')).toBeInTheDocument();
    expect(
      within(screen.getByTestId('performance-console-command-queue')).getByRole('button', {
        name: /dry-run send/i,
      }),
    ).toBeDisabled();
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
  });

  it('renders an allowed live-kit workbench readiness gate when the packet permits it', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithAllowedWorkbenchGate()} />);

    const liveKitCaptureWorkbench = screen.getByTestId(
      'performance-console-live-kit-capture-workbench',
    );
    expect(liveKitCaptureWorkbench).toHaveTextContent('manual-fire');
    expect(liveKitCaptureWorkbench).toHaveTextContent('cockpit allowed');
  });

  it('renders optional live-kit package checks when a packet marks them optional', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithOptionalPackageCheck()} />);

    const liveKitPackageAudition = screen.getByTestId(
      'performance-console-live-kit-package-audition',
    );
    expect(liveKitPackageAudition).toHaveTextContent('journal-preview-only');
    expect(liveKitPackageAudition).toHaveTextContent('optional');
  });

  it('stages live-kit operator package slots locally before package export', () => {
    window.localStorage.clear();
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage hard groove lift operator package/i,
      }),
    );

    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'Hard Groove Lift',
    );
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'Live Kit Operator Package',
    );
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('70%');
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Staged operator package hard-groove-lift',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Z then send',
    );

    fireEvent.click(screen.getByRole('button', { name: /export local rehearsal package/i }));

    const packagePanel = screen.getByTestId('performance-console-local-package');
    expect(packagePanel).toHaveTextContent('Operator package');
    expect(packagePanel).toHaveTextContent('live-kit-operator-package');
    expect(packagePanel).toHaveTextContent('hard-groove-lift');
    expect(packagePanel).toHaveTextContent('Stage Local Operator Package');

    const packagePayload = screen.getByTestId('performance-console-local-package-payload');
    expect(packagePayload).toHaveTextContent('"auditionSource"');
    expect(packagePayload).toHaveTextContent('"sourceAuditionId": "live-kit-package-audition"');
    expect(packagePayload).toHaveTextContent('"slotKey": "hard-groove-lift"');
    expect(packagePayload).toHaveTextContent('"operatorPackage"');
    expect(packagePayload).toHaveTextContent('"operatorPackageId": "live-kit-operator-package"');
    expect(packagePayload).toHaveTextContent('"packageExportKey": "operator-package-hard-groove-lift"');
    expect(packagePayload).toHaveTextContent('"recoveryCommand": "Z then send"');
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('sends a mock-safe operator package rehearsal command when the sidecar callback is available', async () => {
    window.localStorage.clear();
    const client = new FakeCockpitClient();
    client.ackQueue.push({
      request_id: 'operator-package-rehearsed',
      ok: true,
      operator_package_rehearsal: {
        rehearsal_id: 'operator-package-rehearsal:operator-step-hard-groove-lift',
        operator_package_id: 'live-kit-operator-package',
        step_key: 'operator-step-hard-groove-lift',
        slot_key: 'hard-groove-lift',
        mock_safe: true,
        rehearsal_status: 'mock_safe_ready',
        opened_midi_port: false,
        sent_midi: false,
        writes_files: false,
      },
    });
    render(
      <PerformanceConsole
        model={performanceConsoleModelWithSelectableHistory()}
        onRehearseOperatorPackageStep={(command) => client.send(command)}
      />,
    );

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage hard groove lift operator package/i,
      }),
    );

    await waitFor(() => {
      expect(client.sent).toHaveLength(1);
    });
    expect(client.sent[0]).toMatchObject({
      type: 'rehearse_operator_package_step',
      operator_package_id: 'live-kit-operator-package',
      step_key: 'operator-step-hard-groove-lift',
      slot_key: 'hard-groove-lift',
      package_export_key: 'operator-package-hard-groove-lift',
      snapshot_id: 'console-snap-03',
      depth_percent: 70,
      mock_safe: true,
    });
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Sidecar rehearsal acknowledged',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'hard-groove-lift / mock_safe_ready / sent MIDI false',
    );
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
  });

  it('logs mock-safe operator package rehearsal rejection without rolling back local staging', async () => {
    const client = new FakeCockpitClient();
    client.ackQueue.push({
      request_id: 'operator-package-rejected',
      ok: false,
      code: 'validation_error',
      message: 'mock_safe must be true',
    });
    render(
      <PerformanceConsole
        model={performanceConsoleModelWithSelectableHistory()}
        onRehearseOperatorPackageStep={(command) => client.send(command)}
      />,
    );

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage hard groove lift operator package/i,
      }),
    );

    await waitFor(() => {
      expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
        'Sidecar rehearsal rejected',
      );
    });
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'Hard Groove Lift',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'mock_safe must be true',
    );
  });

  it.each([
    {
      name: 'error text',
      ack: { request_id: 'operator-package-error', ok: false, error: 'slot mismatch' },
      expected: 'slot mismatch',
    },
    {
      name: 'code text',
      ack: { request_id: 'operator-package-code', ok: false, code: 'slot_mismatch' },
      expected: 'slot_mismatch',
    },
    {
      name: 'fallback text',
      ack: { request_id: 'operator-package-fallback', ok: false },
      expected: 'Operator package rehearsal rejected.',
    },
  ])('logs mock-safe operator package rehearsal rejection $name', async ({ ack, expected }) => {
    const client = new FakeCockpitClient();
    client.ackQueue.push(ack);
    render(
      <PerformanceConsole
        model={performanceConsoleModelWithSelectableHistory()}
        onRehearseOperatorPackageStep={(command) => client.send(command)}
      />,
    );

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage hard groove lift operator package/i,
      }),
    );

    await waitFor(() => {
      expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
        'Sidecar rehearsal rejected',
      );
    });
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      expected,
    );
  });

  it('logs mock-safe operator package rehearsal Error failures without rolling back local staging', async () => {
    const client = new FakeCockpitClient();
    client.nextRejection = new Error('sidecar offline');
    render(
      <PerformanceConsole
        model={performanceConsoleModelWithSelectableHistory()}
        onRehearseOperatorPackageStep={(command) => client.send(command)}
      />,
    );

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage hard groove lift operator package/i,
      }),
    );

    await waitFor(() => {
      expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
        'Sidecar rehearsal failed',
      );
    });
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'Hard Groove Lift',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'sidecar offline',
    );
  });

  it('logs mock-safe operator package rehearsal transport failure without rolling back local staging', async () => {
    const client = new FakeCockpitClient();
    client.nextRejection = 'sidecar unavailable';
    render(
      <PerformanceConsole
        model={performanceConsoleModelWithSelectableHistory()}
        onRehearseOperatorPackageStep={(command) => client.send(command)}
      />,
    );

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage hard groove lift operator package/i,
      }),
    );

    await waitFor(() => {
      expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
        'Sidecar rehearsal failed',
      );
    });
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'Hard Groove Lift',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Operator package rehearsal failed.',
    );
  });

  it('renders legacy console packets without operator package metadata', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithoutOperatorPackage()} />);

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    expect(operatorPackagePanel).toHaveTextContent('Live Kit Operator Package');
    expect(operatorPackagePanel).toHaveTextContent('unavailable');
    expect(operatorPackagePanel).toHaveTextContent(
      'Operator package metadata is not present on this older console packet.',
    );
    expect(operatorPackagePanel).toHaveTextContent(
      'operator package unavailable on this console packet',
    );
    expect(
      within(operatorPackagePanel).getByRole('button', { name: /send operator package/i }),
    ).toBeDisabled();
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('keeps operator package export local when audition slot evidence is missing', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithMissingOperatorPackageAuditionSlot()} />);

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage missing slot operator operator package/i,
      }),
    );
    fireEvent.click(screen.getByRole('button', { name: /export local rehearsal package/i }));

    const packagePanel = screen.getByTestId('performance-console-local-package');
    expect(packagePanel).toHaveTextContent('Operator package');
    expect(packagePanel).toHaveTextContent('missing-audition-slot');

    const packagePayload = screen.getByTestId('performance-console-local-package-payload');
    expect(packagePayload).toHaveTextContent('"operatorPackage"');
    expect(packagePayload).toHaveTextContent(
      '"packageExportKey": "operator-package-missing-audition-slot"',
    );
    expect(packagePayload).not.toHaveTextContent('"auditionSource"');
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('stages unbound operator package steps with local depth fallback and optional recovery', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithUnboundOperatorPackageStep()} />);

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    expect(operatorPackagePanel).toHaveTextContent('Optional Recovery');
    expect(operatorPackagePanel).toHaveTextContent('optional');

    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage unbound operator operator package/i,
      }),
    );

    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'Unbound Operator',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Staged operator package unbound-operator-slot',
    );
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('sends unbound operator package rehearsal commands with local fallback package and depth', async () => {
    const client = new FakeCockpitClient();
    render(
      <PerformanceConsole
        model={performanceConsoleModelWithUnboundOperatorPackageStep()}
        onRehearseOperatorPackageStep={(command) => client.send(command)}
      />,
    );

    const operatorPackagePanel = screen.getByTestId(
      'performance-console-live-kit-operator-package',
    );
    fireEvent.click(
      within(operatorPackagePanel).getByRole('button', {
        name: /stage unbound operator operator package/i,
      }),
    );

    await waitFor(() => {
      expect(client.sent).toHaveLength(1);
    });
    expect(client.sent[0]).toMatchObject({
      type: 'rehearse_operator_package_step',
      slot_key: 'unbound-operator-slot',
      package_export_key: 'operator-package-unbound-operator-slot',
      depth_percent: 28,
      mock_safe: true,
    });
  });

  it('omits dry-run-only labels when a macro or queued move is not dry-run-only', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithActiveDryRunBoundaries()} />);

    const macroActions = screen.getByTestId('performance-console-macro-actions');
    const hardGrooveMacro = within(macroActions).getByTestId('macro-action-hard-groove');
    expect(hardGrooveMacro).not.toHaveTextContent('dry-run only');

    const lanePolicyMatrix = screen.getByTestId('performance-console-rytm-lane-policy-matrix');
    const hardGroovePolicy = within(lanePolicyMatrix).getByTestId('rytm-macro-policy-hard-groove');
    expect(hardGroovePolicy).toHaveTextContent(
      'Pad 10: amount default / density default / bias default / default lanes / all allowed families',
    );
    expect(hardGroovePolicy).toHaveTextContent(
      'Pad 11: amount normal / density medium / bias brighter / default lanes / AMP: overdrive / SRC: tune',
    );

    const styleQueue = screen.getByTestId('performance-console-style-queue');
    const openingMove = within(styleQueue).getByTestId('style-queue-move-queue-opening-shadow');
    expect(openingMove).toHaveTextContent('Preview before real send');
    expect(openingMove).toHaveTextContent('recover Back To Clean Handoff');
    expect(openingMove).not.toHaveTextContent('dry-run only');
    expect(within(styleQueue).getByTestId('style-queue-move-queue-groove-pressure')).toHaveTextContent(
      'dry-run only',
    );
  });

  it('renders safe HUD fallbacks when optional queue and device focus data is absent', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithHudFallbacks()} />);

    const leftRail = screen.getByTestId('performance-console-left-rail');
    expect(leftRail).toHaveTextContent('Generic Device');
    expect(leftRail).toHaveTextContent('DISARMED');

    const mutationPanel = screen.getByTestId('performance-console-mutation-panel');
    expect(mutationPanel).toHaveTextContent('Queue (0)');
    expect(mutationPanel).toHaveTextContent('0%');
    expect(mutationPanel).toHaveTextContent('0 drum pads and 1 synth tracks');

    expect(screen.getByTestId('performance-console-bottom-strip')).toHaveTextContent(
      'Devices Generic Device',
    );
    expect(screen.getByTestId('performance-console-bottom-strip')).toHaveTextContent('Rytm not present');
    expect(screen.getByTestId('performance-console-bottom-strip')).toHaveTextContent('A4 not present');
    expect(screen.getByTestId('performance-console-snapshot-history')).toHaveTextContent(
      'console-snap-03',
    );
  });

  it('renders named MIDI port and armed state directly from the packet', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithNamedMidiPort()} />);

    const topbar = screen.getByTestId('performance-console-topbar');
    expect(topbar).toHaveTextContent('MOCK SAFE - Elektron Analog Rytm MKII 1');
    expect(topbar).toHaveTextContent('ArmARMED');
  });

  it('renders unnamed open MIDI ports without fabricating a port name', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithUnnamedOpenMidiPort()} />);

    expect(screen.getByTestId('performance-console-topbar')).toHaveTextContent(
      'MOCK SAFE - MIDI port open',
    );
  });

  it('renders non-closed device port states from the device inventory', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithScanningPortState()} />);

    expect(screen.getByTestId('performance-console-topbar')).toHaveTextContent('MOCK SAFE - Scanning');
  });

  it('renders an explicit no-device footer when the packet has no device inventory cards', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithNoDevices()} />);

    const bottomStrip = screen.getByTestId('performance-console-bottom-strip');
    expect(bottomStrip).toHaveTextContent('Devices none');
    expect(bottomStrip).toHaveTextContent('Mock mock state unknown');
    expect(bottomStrip).toHaveTextContent('Rytm not present');
    expect(bottomStrip).toHaveTextContent('A4 not present');
  });

  it('renders empty snapshot history and inactive dry-run state from the packet', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithNoSnapshotHistory()} />);

    const topbar = screen.getByTestId('performance-console-topbar');
    expect(topbar).toHaveTextContent('dry-run inactive');
    expect(topbar).toHaveTextContent('Scene not set');
    expect(topbar).toHaveTextContent('BPM unknown');

    const snapshotDeck = screen.getByTestId('performance-console-snapshot-deck');
    expect(snapshotDeck).toHaveTextContent('No current snapshot');

    expect(
      within(screen.getByTestId('performance-console-mutation-panel')).getByRole('button', {
        name: /queue pending/i,
      }),
    ).toBeDisabled();
  });

  it('supports local-only rehearsal interactions without enabling hardware sends', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    fireEvent.click(screen.getByTestId('performance-console-style-crate-select-peak-time'));
    fireEvent.click(screen.getByTestId('performance-console-queue-select-queue-groove-pressure'));
    fireEvent.click(screen.getByTestId('performance-console-history-console-snap-01'));
    fireEvent.change(screen.getByTestId('performance-console-depth-input'), {
      target: { value: '72' },
    });
    fireEvent.click(screen.getByRole('button', { name: /run local dry-run/i }));
    fireEvent.click(screen.getByRole('button', { name: /save local journal take/i }));

    const localPreview = screen.getByTestId('performance-console-local-preview');
    expect(localPreview).toHaveTextContent('Selected crate Peak Time');
    expect(localPreview).toHaveTextContent('Selected move Rolling Perc Push');
    expect(localPreview).toHaveTextContent('Selected snapshot console-snap-01');
    expect(localPreview).toHaveTextContent('Depth 72%');
    expect(localPreview).toHaveTextContent('Local only');

    expect(screen.getByTestId('performance-console-last-dry-run')).toHaveTextContent('Local dry-run');
    expect(screen.getByTestId('performance-console-last-dry-run')).toHaveTextContent('Peak Time');
    expect(screen.getByTestId('performance-console-last-dry-run')).toHaveTextContent('72%');
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent('local-take-01');
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent(
      'Rolling Perc Push',
    );

    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('supports local-only set planning without enabling hardware sends', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    fireEvent.click(screen.getByTestId('performance-console-style-crate-select-peak-time'));
    fireEvent.click(screen.getByTestId('performance-console-queue-select-queue-groove-pressure'));
    fireEvent.click(screen.getByTestId('performance-console-history-console-snap-01'));
    fireEvent.change(screen.getByTestId('performance-console-depth-input'), {
      target: { value: '72' },
    });
    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));

    const localSetPlan = screen.getByTestId('performance-console-local-set-plan');
    expect(localSetPlan).toHaveTextContent('local-step-01');
    expect(localSetPlan).toHaveTextContent('Peak Time');
    expect(localSetPlan).toHaveTextContent('Rolling Perc Push');
    expect(localSetPlan).toHaveTextContent('console-snap-01');
    expect(localSetPlan).toHaveTextContent('72%');
    expect(localSetPlan).toHaveTextContent('Local only');

    fireEvent.click(screen.getByTestId('performance-console-style-crate-select-industrial-broken'));
    fireEvent.click(screen.getByTestId('performance-console-queue-select-queue-peak-metal'));
    fireEvent.click(screen.getByTestId('performance-console-history-console-snap-02'));
    fireEvent.change(screen.getByTestId('performance-console-depth-input'), {
      target: { value: '58' },
    });
    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));

    expect(localSetPlan).toHaveTextContent('local-step-02');
    expect(localSetPlan).toHaveTextContent('Industrial/Broken');
    expect(localSetPlan).toHaveTextContent('Broken Metal Stress');
    expect(localSetPlan).toHaveTextContent('console-snap-02');
    expect(localSetPlan).toHaveTextContent('58%');

    fireEvent.click(screen.getByRole('button', { name: /promote next local set-plan step/i }));

    const currentSetPlanStep = screen.getByTestId('performance-console-current-set-plan-step');
    expect(currentSetPlanStep).toHaveTextContent('local-step-01');
    expect(currentSetPlanStep).toHaveTextContent('Rolling Perc Push');
    expect(currentSetPlanStep).toHaveTextContent('Peak Time');
    expect(currentSetPlanStep).toHaveTextContent('console-snap-01');
    expect(currentSetPlanStep).toHaveTextContent('72%');

    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Promoted local-step-01',
    );
    expect(screen.queryByTestId('local-set-plan-step-local-step-01')).not.toBeInTheDocument();
    expect(localSetPlan).toHaveTextContent('local-step-02');
    expect(localSetPlan).toHaveTextContent('Up next');

    const operatorLog = screen.getByTestId('performance-console-local-operator-log');
    expect(operatorLog).toHaveTextContent('Staged local-step-01');
    expect(operatorLog).toHaveTextContent('Staged local-step-02');
    expect(operatorLog).toHaveTextContent('Promoted local-step-01');
    expect(operatorLog).toHaveTextContent('Local only');

    const handoff = screen.getByTestId('performance-console-local-handoff');
    expect(handoff).toHaveTextContent('Operator handoff');
    expect(handoff).toHaveTextContent(
      'Current: local-step-01 / Rolling Perc Push / Peak Time / console-snap-01 / 72%',
    );
    expect(handoff).toHaveTextContent(
      'Next: local-step-02 / Broken Metal Stress / Industrial/Broken / console-snap-02 / 58%',
    );
    expect(handoff).toHaveTextContent('Recent: Promoted local-step-01');
    expect(handoff).toHaveTextContent('Recovery: use Z + send from the armed snapshot shell.');
    expect(handoff).toHaveTextContent(
      'Local handoff only: no WebSocket command, sidecar action, MIDI port, arm, or send.',
    );

    fireEvent.click(screen.getByRole('button', { name: /complete current local set-plan step/i }));

    expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
      'No current local set-plan step.',
    );
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Completed local-step-01',
    );
    expect(localSetPlan).toHaveTextContent('local-step-02');
    expect(localSetPlan).toHaveTextContent('Up next');
    expect(operatorLog).toHaveTextContent('Completed local-step-01');
    expect(handoff).toHaveTextContent('Current: none');
    expect(handoff).toHaveTextContent(
      'Next: local-step-02 / Broken Metal Stress / Industrial/Broken / console-snap-02 / 58%',
    );

    fireEvent.click(screen.getByRole('button', { name: /skip next local set-plan step/i }));

    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Skipped local-step-02',
    );
    expect(operatorLog).toHaveTextContent('Skipped local-step-02');
    expect(localSetPlan).toHaveTextContent('No local set-plan steps staged.');

    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));
    expect(localSetPlan).toHaveTextContent('local-step-03');
    expect(localSetPlan).not.toHaveTextContent('local-step-01: Broken Metal Stress');

    fireEvent.click(screen.getByRole('button', { name: /clear local set-plan/i }));

    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Cleared 1 local set-plan step',
    );
    expect(operatorLog).toHaveTextContent('Cleared 1 local set-plan step');
    expect(localSetPlan).toHaveTextContent('No local set-plan steps staged.');

    fireEvent.click(screen.getByRole('button', { name: /reset local set-plan/i }));

    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Reset local set-plan',
    );
    expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
      'No current local set-plan step.',
    );
    expect(localSetPlan).toHaveTextContent('No local set-plan steps staged.');
    expect(operatorLog).toHaveTextContent('Reset local set-plan');
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('autosaves and restores the local rehearsal plan without hardware sends', () => {
    window.localStorage.clear();
    const { unmount } = render(
      <PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />,
    );

    fireEvent.click(screen.getByTestId('performance-console-style-crate-select-peak-time'));
    fireEvent.click(screen.getByTestId('performance-console-queue-select-queue-groove-pressure'));
    fireEvent.click(screen.getByTestId('performance-console-history-console-snap-01'));
    fireEvent.change(screen.getByTestId('performance-console-depth-input'), {
      target: { value: '72' },
    });
    fireEvent.click(screen.getByRole('button', { name: /run local dry-run/i }));
    fireEvent.click(screen.getByRole('button', { name: /save local journal take/i }));
    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));
    fireEvent.click(screen.getByRole('button', { name: /promote next local set-plan step/i }));

    const stored = window.localStorage.getItem(
      'rytmrandomizer.performanceConsole.localRehearsal.v1',
    );
    expect(stored).toContain('local-step-01');
    expect(stored).toContain('local-take-01');
    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Local auto-save on',
    );

    unmount();
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected crate Peak Time',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected move Rolling Perc Push',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected snapshot console-snap-01',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Depth 72%');
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent(
      'local-take-01',
    );
    expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
      'local-step-01',
    );
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
  });

  it('exports and imports local rehearsal JSON without dispatching hardware actions', () => {
    window.localStorage.clear();
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    const importPayload = {
      version: 1,
      selectedCrateKey: 'industrial-broken',
      selectedQueueKey: 'queue-peak-metal',
      selectedSnapshotId: 'console-snap-02',
      previewDepth: 64,
      lastDryRunSummary: 'Imported local dry-run. No MIDI port opened; no MIDI sent.',
      localJournalEntries: [
        {
          id: 'imported-take-01',
          crateName: 'Industrial/Broken',
          moveName: 'Broken Metal Stress',
          snapshotId: 'console-snap-02',
          depth: 64,
        },
      ],
      localSetPlanEntries: [
        {
          id: 'imported-step-02',
          crateName: 'Peak Time',
          moveName: 'Rolling Perc Push',
          snapshotId: 'console-snap-01',
          depth: 48,
          status: 'Local only',
        },
      ],
      currentSetPlanStep: {
        id: 'imported-step-01',
        crateName: 'Industrial/Broken',
        moveName: 'Broken Metal Stress',
        snapshotId: 'console-snap-02',
        depth: 64,
        status: 'Local only',
      },
      localOperatorEvents: [
        {
          id: 'imported-event-01',
          label: 'Imported rehearsal',
          detail: 'Loaded from passive JSON.',
          status: 'Local only',
        },
      ],
      lastSetPlanAction: 'Imported local rehearsal snapshot. Local only; no MIDI sent.',
      nextLocalSetPlanIndex: 7,
    };

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify(importPayload) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal json/i }));

    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected crate Industrial/Broken',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected move Broken Metal Stress',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected snapshot console-snap-02',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Depth 64%');
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent(
      'imported-take-01',
    );
    expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
      'imported-step-01',
    );
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'imported-step-02',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Imported local rehearsal JSON',
    );

    fireEvent.click(screen.getByRole('button', { name: /export local rehearsal json/i }));

    const exportedPayload = screen.getByTestId('performance-console-local-export-payload');
    expect(exportedPayload).toHaveTextContent('imported-step-01');
    expect(exportedPayload).toHaveTextContent('imported-take-01');
    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Exported local rehearsal JSON',
    );

    fireEvent.click(screen.getByRole('button', { name: /clear saved local rehearsal/i }));
    expect(window.localStorage.getItem('rytmrandomizer.performanceConsole.localRehearsal.v1')).toBe(
      null,
    );
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('exports a portable local rehearsal package with manifest and safety evidence', () => {
    window.localStorage.clear();
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    fireEvent.click(screen.getByTestId('performance-console-style-crate-select-peak-time'));
    fireEvent.click(screen.getByTestId('performance-console-queue-select-queue-groove-pressure'));
    fireEvent.click(screen.getByTestId('performance-console-history-console-snap-01'));
    fireEvent.change(screen.getByTestId('performance-console-depth-input'), {
      target: { value: '72' },
    });
    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));
    fireEvent.click(screen.getByRole('button', { name: /promote next local set-plan step/i }));
    fireEvent.click(screen.getByRole('button', { name: /export local rehearsal package/i }));

    const packagePanel = screen.getByTestId('performance-console-local-package');
    expect(packagePanel).toHaveTextContent('Local rehearsal package');
    expect(packagePanel).toHaveTextContent('compatible');
    expect(packagePanel).toHaveTextContent('Warehouse arc');
    expect(packagePanel).toHaveTextContent('passive packet');
    expect(packagePanel).toHaveTextContent('Peak Time');
    expect(packagePanel).toHaveTextContent('Rolling Perc Push');
    expect(packagePanel).toHaveTextContent('console-snap-01');
    expect(packagePanel).toHaveTextContent('current local-step-01');
    expect(packagePanel).toHaveTextContent('queued 0');
    expect(packagePanel).toHaveTextContent('journal 0');
    expect(packagePanel).toHaveTextContent('Elektron Analog Rytm MKII');
    expect(packagePanel).toHaveTextContent('Elektron Analog Four MKII');
    expect(packagePanel).toHaveTextContent('a4_outbound_macro_send');
    expect(packagePanel).toHaveTextContent('send audition variation from Cockpit console');
    expect(packagePanel).toHaveTextContent('live kit package audition is declarative only');
    expect(packagePanel).toHaveTextContent('use Z + send from the armed snapshot shell');
    expect(packagePanel).toHaveTextContent('reload saved kit if needed');

    const packagePayload = screen.getByTestId('performance-console-local-package-payload');
    expect(packagePayload).toHaveTextContent(
      '"kind": "rytmrandomizer.cockpit.local-rehearsal-package"',
    );
    expect(packagePayload).toHaveTextContent('"version": 1');
    expect(packagePayload).toHaveTextContent('"selectedCrateName": "Peak Time"');
    expect(packagePayload).toHaveTextContent('"selectedMoveName": "Rolling Perc Push"');
    expect(packagePayload).toHaveTextContent('"selectedSnapshotId": "console-snap-01"');
    expect(packagePayload).toHaveTextContent('"currentStepId": "local-step-01"');
    expect(packagePayload).toHaveTextContent('"status": "compatible"');
    expect(packagePayload).toHaveTextContent('"selected crate exists in current packet"');
    expect(packagePayload).toHaveTextContent('"selected queued move exists in current packet"');
    expect(packagePayload).toHaveTextContent('"selected snapshot exists in current packet"');
    expect(packagePayload).toHaveTextContent('"send audition variation from Cockpit console"');
    expect(packagePayload).toHaveTextContent('"live kit package audition is declarative only"');
    expect(packagePayload).toHaveTextContent('"reload saved kit if needed"');
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('reviews an exported rehearsal package against the current cockpit packet locally', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    fireEvent.click(screen.getByTestId('performance-console-style-crate-select-peak-time'));
    fireEvent.click(screen.getByTestId('performance-console-queue-select-queue-groove-pressure'));
    fireEvent.click(screen.getByTestId('performance-console-history-console-snap-01'));
    fireEvent.change(screen.getByTestId('performance-console-depth-input'), {
      target: { value: '72' },
    });
    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));
    fireEvent.click(screen.getByRole('button', { name: /export local rehearsal package/i }));

    const review = screen.getByTestId('performance-console-local-package-review');
    expect(review).toHaveTextContent('Package review workbench');
    expect(review).toHaveTextContent('review status compatible');
    expect(review).toHaveTextContent('Package can be rehearsed with the current cockpit packet.');
    expect(review).toHaveTextContent('Crate');
    expect(review).toHaveTextContent('package Peak Time');
    expect(review).toHaveTextContent('current Peak Time');
    expect(review).toHaveTextContent('Queued move');
    expect(review).toHaveTextContent('package Rolling Perc Push');
    expect(review).toHaveTextContent('current Rolling Perc Push');
    expect(review).toHaveTextContent('Snapshot');
    expect(review).toHaveTextContent('package console-snap-01');
    expect(review).toHaveTextContent('current console-snap-01');
    expect(review).toHaveTextContent('Depth');
    expect(review).toHaveTextContent('package 72%');
    expect(review).toHaveTextContent('current 72%');
    expect(review).toHaveTextContent('Blocked actions');
    expect(review).toHaveTextContent('Recovery notes');

    fireEvent.click(screen.getByRole('button', { name: /stage package review locally/i }));

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Staged local package review: compatible',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Staged package review',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Package can be rehearsed with the current cockpit packet.',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Crate: package Peak Time; current Peak Time; status match',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Depth: package 72%; current 72%; status match',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Blocked actions:',
    );
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });

  it('exports a compatible local rehearsal package before crate or queue selection', () => {
    window.localStorage.clear();
    render(<PerformanceConsole model={performanceConsoleModelWithEmptyStyleDeck()} />);

    fireEvent.click(screen.getByRole('button', { name: /export local rehearsal package/i }));

    const packagePanel = screen.getByTestId('performance-console-local-package');
    expect(packagePanel).toHaveTextContent('compatible');
    expect(packagePanel).toHaveTextContent('selected crate exists in current packet');
    expect(packagePanel).toHaveTextContent('selected queued move exists in current packet');
    expect(packagePanel).toHaveTextContent('current none');
    expect(packagePanel).not.toHaveTextContent('queue recovery:');

    const packagePayload = screen.getByTestId('performance-console-local-package-payload');
    expect(packagePayload).toHaveTextContent('"selectedCrateName": "none"');
    expect(packagePayload).toHaveTextContent('"selectedMoveName": "none"');
    expect(packagePayload).toHaveTextContent('"queuedStepCount": 0');
    expect(packagePayload).toHaveTextContent('"currentStepId": null');
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
  });

  it('imports a local rehearsal package and keeps raw snapshot import compatibility', () => {
    window.localStorage.clear();
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    const rehearsalSnapshot = {
      version: 1,
      selectedCrateKey: 'industrial-broken',
      selectedQueueKey: 'queue-peak-metal',
      selectedSnapshotId: 'console-snap-02',
      previewDepth: 64,
      lastDryRunSummary: 'Imported package dry-run. No MIDI port opened; no MIDI sent.',
      localJournalEntries: [
        {
          id: 'package-take-01',
          crateName: 'Industrial/Broken',
          moveName: 'Broken Metal Stress',
          snapshotId: 'console-snap-02',
          depth: 64,
        },
      ],
      localSetPlanEntries: [
        {
          id: 'package-step-02',
          crateName: 'Peak Time',
          moveName: 'Rolling Perc Push',
          snapshotId: 'console-snap-01',
          depth: 48,
          status: 'Local only',
        },
      ],
      currentSetPlanStep: {
        id: 'package-step-01',
        crateName: 'Industrial/Broken',
        moveName: 'Broken Metal Stress',
        snapshotId: 'console-snap-02',
        depth: 64,
        status: 'Local only',
      },
      localOperatorEvents: [
        {
          id: 'package-event-01',
          label: 'Package event',
          detail: 'Loaded from a portable package.',
          status: 'Local only',
        },
      ],
      lastSetPlanAction: 'Imported package snapshot. Local only; no MIDI sent.',
      nextLocalSetPlanIndex: 5,
      localAutosaveEnabled: true,
      selectedOperatorPackageSlotKey: 'hard-groove-lift',
    };
    const packagePayload = {
      kind: 'rytmrandomizer.cockpit.local-rehearsal-package',
      version: 1,
      manifest: {
        sessionLabel: 'Warehouse arc',
        packetSource: 'passive packet',
        selectedCrateName: 'Industrial/Broken',
        selectedMoveName: 'Broken Metal Stress',
        selectedSnapshotId: 'console-snap-02',
        queuedStepCount: 1,
        currentStepId: 'package-step-01',
        journalTakeCount: 1,
        hardwareMode: 'passive',
      },
      compatibility: {
        status: 'compatible',
        checks: [
          'selected crate exists in current packet',
          'selected queued move exists in current packet',
          'selected snapshot exists in current packet',
        ],
      },
      safety: {
        devices: ['Elektron Analog Rytm MKII', 'Elektron Analog Four MKII'],
        checklist: ['No MIDI Port Open'],
      },
      blockedActions: ['send MIDI from snapshot history'],
      recoveryNotes: ['use Z + send from the armed snapshot shell'],
      auditionSource: {
        sourceAuditionId: 'live-kit-package-audition',
        sourceWorkbenchId: 'live-kit-capture-workbench',
        slotKey: 'hard-groove-lift',
        slotLabel: 'Hard Groove Lift',
        styleCrate: 'Hard Groove',
        journalSeed: 'seed-hard-groove-lift',
        recoveryCommand: 'Z then send',
      },
      operatorPackage: {
        operatorPackageId: 'live-kit-operator-package',
        packageExportKey: 'operator-package-hard-groove-lift',
        cockpitBinding: 'Stage Local Operator Package',
        localAction: 'Stage Local Operator Package',
        stageTarget: 'local-set-plan',
        safetyStatus: 'passive-ready',
      },
      rehearsal: rehearsalSnapshot,
    };

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify(packagePayload) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal package/i }));

    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected crate Industrial/Broken',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected move Broken Metal Stress',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected snapshot console-snap-02',
    );
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent(
      'package-take-01',
    );
    expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
      'package-step-01',
    );
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'package-step-02',
    );
    expect(screen.getByTestId('performance-console-local-package')).toHaveTextContent(
      'compatible',
    );
    expect(screen.getByTestId('performance-console-local-package')).toHaveTextContent(
      'live-kit-operator-package',
    );
    expect(screen.getByTestId('performance-console-local-package')).toHaveTextContent(
      'hard-groove-lift',
    );
    expect(screen.getByTestId('performance-console-local-package')).toHaveTextContent(
      'Stage Local Operator Package',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Imported local rehearsal package',
    );

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify(packagePayload) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal json/i }));

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Imported local rehearsal JSON',
    );
    expect(screen.getByTestId('performance-console-local-package')).toHaveTextContent(
      'compatible',
    );

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify({ ...rehearsalSnapshot, selectedCrateKey: 'peak-time' }) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal json/i }));

    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected crate Peak Time',
    );
    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Imported local rehearsal JSON',
    );
    expect(screen.queryByTestId('performance-console-local-package-review')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
  });

  it('keeps imported rehearsal package compatibility warnings visible for missing packet references', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    const packagePayload = {
      kind: 'rytmrandomizer.cockpit.local-rehearsal-package',
      version: 1,
      manifest: {
        sessionLabel: 'External rehearsal',
        packetSource: 'external package',
        selectedCrateName: 'External Crate',
        selectedMoveName: 'External Move',
        selectedSnapshotId: 'external-snapshot',
        queuedStepCount: 0,
        currentStepId: null,
        journalTakeCount: 0,
        hardwareMode: 'passive',
      },
      compatibility: {
        status: 'compatible',
        checks: ['external package claimed compatibility'],
      },
      safety: {
        devices: ['External Device', 42],
        checklist: ['External safety note', false],
      },
      blockedActions: ['external blocked action', null],
      recoveryNotes: ['external recovery note', 7],
      operatorPackage: {
        operatorPackageId: 'partial-operator-package',
      },
      rehearsal: {
        version: 1,
        selectedCrateKey: 'missing-crate',
        selectedQueueKey: 'missing-queue',
        selectedSnapshotId: 'missing-snapshot',
        selectedOperatorPackageSlotKey: 'missing-operator-slot',
        previewDepth: 44,
        lastDryRunSummary: 'Imported missing-reference package.',
        localJournalEntries: [],
        localSetPlanEntries: [],
        currentSetPlanStep: null,
        localOperatorEvents: [],
        lastSetPlanAction: 'Imported missing-reference package.',
        nextLocalSetPlanIndex: 0,
        localAutosaveEnabled: true,
      },
    };

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify(packagePayload) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal package/i }));

    const packagePanel = screen.getByTestId('performance-console-local-package');
    expect(packagePanel).toHaveTextContent('needs review');
    expect(packagePanel).toHaveTextContent('selected crate missing from current packet');
    expect(packagePanel).toHaveTextContent('selected queued move missing from current packet');
    expect(packagePanel).toHaveTextContent('selected snapshot missing from current packet');
    expect(packagePanel).toHaveTextContent('operator package slot missing from current packet');
    expect(packagePanel).toHaveTextContent('External Device');
    expect(packagePanel).toHaveTextContent('external blocked action');
    expect(packagePanel).toHaveTextContent('external recovery note');
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Depth 44%');
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();

    const review = screen.getByTestId('performance-console-local-package-review');
    expect(review).toHaveTextContent('review status needs review');
    expect(review).toHaveTextContent('Package needs operator review before reuse.');
    expect(review).toHaveTextContent('Crate');
    expect(review).toHaveTextContent('package External Crate');
    expect(review).toHaveTextContent('current missing-crate');
    expect(review).toHaveTextContent('missing');
    expect(review).toHaveTextContent('Queued move');
    expect(review).toHaveTextContent('package External Move');
    expect(review).toHaveTextContent('current missing-queue');
    expect(review).toHaveTextContent('Snapshot');
    expect(review).toHaveTextContent('package external-snapshot');
    expect(review).toHaveTextContent('current missing-snapshot');
    expect(review).toHaveTextContent('Operator package slot');
    expect(review).toHaveTextContent('package missing-operator-slot');
    expect(review).toHaveTextContent('current missing-operator-slot');
    expect(review).toHaveTextContent('Blocked actions');
    expect(review).toHaveTextContent('package 1');
    expect(review).toHaveTextContent('Recovery notes');
    expect(review).toHaveTextContent('current 1');

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: {
        value: JSON.stringify({
          ...packagePayload,
          rehearsal: {
            ...packagePayload.rehearsal,
            selectedCrateKey: 'missing-crate',
            selectedQueueKey: 'queue-groove-pressure',
            selectedSnapshotId: null,
            selectedOperatorPackageSlotKey: 'missing-operator-slot',
          },
        }),
      },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal package/i }));

    const fallbackPackagePanel = screen.getByTestId('performance-console-local-package');
    expect(fallbackPackagePanel).toHaveTextContent('needs review');
    expect(fallbackPackagePanel).toHaveTextContent('selected crate missing from current packet');
    expect(fallbackPackagePanel).toHaveTextContent('selected queued move exists in current packet');
    expect(fallbackPackagePanel).toHaveTextContent('selected snapshot exists in current packet');
    expect(screen.getByTestId('performance-console-local-package-review')).toHaveTextContent(
      'review status needs review',
    );
    expect(screen.getByTestId('performance-console-local-package-review')).toHaveTextContent(
      'current missing-crate',
    );
  });

  it('reports invalid local rehearsal imports and ignores malformed imported rows safely', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: '{not json' },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal json/i }));

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Import failed: JSON could not be parsed',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Import failed',
    );

    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal package/i }));

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Import failed: JSON could not be parsed',
    );

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify({ version: 99 }) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal json/i }));

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Import failed: unsupported local rehearsal payload',
    );

    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal package/i }));

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Import failed: unsupported local rehearsal package',
    );

    const validPackageShell = {
      kind: 'rytmrandomizer.cockpit.local-rehearsal-package',
      version: 1,
      manifest: {
        sessionLabel: 'Import failure shell',
        packetSource: 'test',
        selectedCrateName: 'None',
        selectedMoveName: 'None',
        selectedSnapshotId: 'None',
        queuedStepCount: 0,
        currentStepId: null,
        journalTakeCount: 0,
        hardwareMode: 'passive',
      },
      compatibility: {
        status: 'compatible',
        checks: [],
      },
      safety: {
        devices: [],
        checklist: [],
      },
      blockedActions: [],
      recoveryNotes: [],
      rehearsal: {
        version: 1,
      },
    };

    for (const malformedPackage of [
      { ...validPackageShell, manifest: null },
      {
        ...validPackageShell,
        manifest: { ...validPackageShell.manifest, sessionLabel: null },
      },
      {
        ...validPackageShell,
        manifest: { ...validPackageShell.manifest, selectedMoveName: null },
      },
      { ...validPackageShell, compatibility: null },
      { ...validPackageShell, compatibility: { checks: [] } },
      { ...validPackageShell, safety: null },
      { ...validPackageShell, rehearsal: { version: 99 } },
    ]) {
      fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
        target: { value: JSON.stringify(malformedPackage) },
      });
      fireEvent.click(screen.getByRole('button', { name: /import local rehearsal package/i }));

      expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
        'Import failed: unsupported local rehearsal package',
      );
    }

    const packageWithMalformedOptionalMetadata = {
      ...validPackageShell,
      auditionSource: {
        sourceAuditionId: 'live-kit-package-audition',
      },
      operatorPackage: 'not an operator package',
    };
    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify(packageWithMalformedOptionalMetadata) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal package/i }));

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Imported local rehearsal package. Local only; no MIDI sent.',
    );

    const sparsePayload = {
      version: 1,
      selectedCrateKey: null,
      selectedQueueKey: null,
      selectedSnapshotId: null,
      previewDepth: 999,
      lastDryRunSummary: 'Sparse import dry-run summary.',
      localJournalEntries: [
        null,
        { id: 'bad-journal-row' },
        {
          id: 'valid-imported-take',
          crateName: 'Peak Time',
          moveName: 'Rolling Perc Push',
          snapshotId: 'console-snap-01',
          depth: 999,
        },
      ],
      localSetPlanEntries: [
        null,
        { id: 'bad-set-plan-row' },
        {
          id: 'valid-imported-step',
          crateName: 'Peak Time',
          moveName: 'Rolling Perc Push',
          snapshotId: 'console-snap-01',
          depth: -10,
        },
      ],
      currentSetPlanStep: { id: 'bad-current-step' },
      localOperatorEvents: [
        null,
        { id: 'bad-event-row' },
        {
          id: 'valid-imported-event',
          label: 'Valid imported event',
          detail: 'Kept by parser.',
        },
      ],
      lastSetPlanAction: 'Sparse import action.',
      nextLocalSetPlanIndex: -4,
      localAutosaveEnabled: false,
    };

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: { value: JSON.stringify(sparsePayload) },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal json/i }));

    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected crate Dark Hypnotic',
    );
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Depth 90%');
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent(
      'valid-imported-take',
    );
    expect(screen.getByTestId('performance-console-local-journal')).not.toHaveTextContent(
      'bad-journal-row',
    );
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'valid-imported-step',
    );
    expect(screen.getByTestId('performance-console-local-set-plan')).not.toHaveTextContent(
      'bad-set-plan-row',
    );
    expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
      'No current local set-plan step.',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Valid imported event',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Imported local rehearsal JSON',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).not.toHaveTextContent(
      'bad-event-row',
    );
    expect(screen.getByTestId('performance-console-local-autosave')).not.toBeChecked();

    fireEvent.click(screen.getByTestId('performance-console-local-autosave'));
    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Local auto-save on',
    );
    fireEvent.click(screen.getByTestId('performance-console-local-autosave'));
    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'Local auto-save off',
    );
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();

    fireEvent.change(screen.getByTestId('performance-console-local-import-input'), {
      target: {
        value: JSON.stringify({
          version: 1,
          localJournalEntries: {},
          localSetPlanEntries: {},
          localOperatorEvents: {},
        }),
      },
    });
    fireEvent.click(screen.getByRole('button', { name: /import local rehearsal json/i }));

    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent(
      'No local journal takes saved.',
    );
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'No local set-plan steps staged.',
    );
  });

  it('falls back safely when saved local rehearsal storage is unavailable or corrupt', () => {
    window.localStorage.setItem('rytmrandomizer.performanceConsole.localRehearsal.v1', '{bad json');
    const corruptStorageRender = render(
      <PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />,
    );

    expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
      'No saved local rehearsal loaded',
    );
    corruptStorageRender.unmount();

    const originalStorageDescriptor = Object.getOwnPropertyDescriptor(window, 'localStorage');
    if (originalStorageDescriptor === undefined) {
      throw new Error('Expected jsdom localStorage descriptor to exist');
    }
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      get() {
        throw new Error('blocked storage');
      },
    });

    try {
      render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

      expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
        'No saved local rehearsal loaded',
      );
      fireEvent.click(screen.getByRole('button', { name: /clear saved local rehearsal/i }));
      expect(screen.getByTestId('performance-console-local-persistence-summary')).toHaveTextContent(
        'Cleared saved local rehearsal',
      );
      expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    } finally {
      Object.defineProperty(window, 'localStorage', originalStorageDescriptor);
    }
  });

  it('supports keyboard snapshot selection in the local rehearsal preview', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithSelectableHistory()} />);

    const firstSnapshot = screen.getByTestId('performance-console-history-console-snap-01');
    const secondSnapshot = screen.getByTestId('performance-console-history-console-snap-02');

    fireEvent.keyDown(firstSnapshot, { key: 'Escape' });
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected snapshot console-snap-03',
    );

    fireEvent.keyDown(firstSnapshot, { key: 'Enter' });
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected snapshot console-snap-01',
    );

    fireEvent.keyDown(secondSnapshot, { key: ' ' });
    expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent(
      'Selected snapshot console-snap-02',
    );
  });

  it('keeps local rehearsal safe when no style crates or queue moves are available', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithEmptyStyleDeck()} />);

    const localPreview = screen.getByTestId('performance-console-local-preview');
    expect(localPreview).toHaveTextContent('Selected crate none');
    expect(localPreview).toHaveTextContent('Selected move none');

    fireEvent.click(screen.getByRole('button', { name: /run local dry-run/i }));
    fireEvent.click(screen.getByRole('button', { name: /save local journal take/i }));

    expect(screen.getByTestId('performance-console-last-dry-run')).toHaveTextContent('No crate');
    expect(screen.getByTestId('performance-console-last-dry-run')).toHaveTextContent(
      'No queued move',
    );
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent('No crate');
    expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent(
      'No queued move',
    );

    fireEvent.click(screen.getByRole('button', { name: /promote next local set-plan step/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'No local set-plan steps to promote',
    );

    fireEvent.click(screen.getByRole('button', { name: /skip next local set-plan step/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'No local set-plan steps to skip',
    );

    fireEvent.click(screen.getByRole('button', { name: /complete current local set-plan step/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'No current local set-plan step to complete',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Complete ignored',
    );

    fireEvent.click(screen.getByRole('button', { name: /clear local set-plan/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Cleared 0 local set-plan step',
    );

    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('No crate');
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'No queued move',
    );

    fireEvent.click(screen.getByRole('button', { name: /promote next local set-plan step/i }));
    expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
      'local-step-01',
    );

    fireEvent.click(screen.getByRole('button', { name: /clear local set-plan/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Cleared 0 local set-plan step',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Current step remains local-step-01',
    );

    fireEvent.click(screen.getByRole('button', { name: /reset local set-plan/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Reset local set-plan',
    );
    expect(screen.getByTestId('performance-console-local-operator-log')).toHaveTextContent(
      'Cleared current local-step-01 and 0 queued step',
    );

    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });
});
