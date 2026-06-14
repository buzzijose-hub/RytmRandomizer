import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PerformanceConsole } from '../../src/cockpit/PerformanceConsole';
import type { LiveGuiPerformanceConsoleModelDict } from '../../src/types/live_gui_protocol';
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

describe('PerformanceConsole', () => {
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

    fireEvent.click(screen.getByRole('button', { name: /skip next local set-plan step/i }));

    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Skipped local-step-02',
    );
    expect(operatorLog).toHaveTextContent('Skipped local-step-02');
    expect(localSetPlan).toHaveTextContent('No local set-plan steps staged.');

    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));
    expect(localSetPlan).toHaveTextContent('local-step-01');

    fireEvent.click(screen.getByRole('button', { name: /clear local set-plan/i }));

    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Cleared 1 local set-plan step',
    );
    expect(operatorLog).toHaveTextContent('Cleared 1 local set-plan step');
    expect(localSetPlan).toHaveTextContent('No local set-plan steps staged.');
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
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

    fireEvent.click(screen.getByRole('button', { name: /clear local set-plan/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Cleared 0 local set-plan step',
    );

    fireEvent.click(screen.getByRole('button', { name: /stage local set-plan step/i }));
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('No crate');
    expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
      'No queued move',
    );

    fireEvent.click(screen.getByRole('button', { name: /clear local set-plan/i }));
    expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent(
      'Cleared 1 local set-plan step',
    );

    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
  });
});
