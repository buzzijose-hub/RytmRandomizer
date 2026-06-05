/**
 * Tests for LiveReadinessPanel -- consumers for the passive GUI model surfaces.
 */

import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL,
  DEFAULT_LIVE_READINESS_MODEL,
  LiveReadinessPanel,
  type LivePerformanceFlowModel,
  type LiveReadinessModel,
} from '../../src/cockpit/LiveReadinessPanel';

import { runAxe, violationSummary } from '../a11y/__helpers__/axe';

const model: LiveReadinessModel = {
  ...DEFAULT_LIVE_READINESS_MODEL,
  pad_surface: {
    ...DEFAULT_LIVE_READINESS_MODEL.pad_surface,
    active_pad_count: 1,
    planned_pad_count: 1,
    cards_by_pad: {
      1: DEFAULT_LIVE_READINESS_MODEL.pad_surface.cards_by_pad[1]!,
      12: {
        ...DEFAULT_LIVE_READINESS_MODEL.pad_surface.cards_by_pad[12]!,
        default_role: 'accent kick',
        lock_reason: 'awaiting V1.34-compatible mutation routing',
      },
    },
  },
  scene_queue: {
    ...DEFAULT_LIVE_READINESS_MODEL.scene_queue,
    queue_status: 'review-needed',
    scene_cards: [
      DEFAULT_LIVE_READINESS_MODEL.scene_queue.scene_cards[0]!,
      {
        ...DEFAULT_LIVE_READINESS_MODEL.scene_queue.scene_cards[3]!,
        description: 'Grit-forward intensity',
      },
    ],
    preview_queue: [
      {
        ...DEFAULT_LIVE_READINESS_MODEL.scene_queue.preview_queue[3]!,
        scene_key: 'S3',
        queue_position: 'current',
      },
    ],
  },
  snapshot_history: {
    ...DEFAULT_LIVE_READINESS_MODEL.snapshot_history,
    entry_count: 2,
    entries: [
      DEFAULT_LIVE_READINESS_MODEL.snapshot_history.entries[0]!,
      DEFAULT_LIVE_READINESS_MODEL.snapshot_history.entries[2]!,
    ],
    controls: DEFAULT_LIVE_READINESS_MODEL.snapshot_history.controls.slice(0, 2),
  },
  safety_checklist: {
    ...DEFAULT_LIVE_READINESS_MODEL.safety_checklist,
    checklist_status: 'blocked',
    passed_count: 3,
    total_count: 4,
    items: [
      DEFAULT_LIVE_READINESS_MODEL.safety_checklist.items[1]!,
      {
        ...DEFAULT_LIVE_READINESS_MODEL.safety_checklist.items[2]!,
        status: 'blocked',
        severity: 'critical',
        message: 'Snapshot compatibility is not verified',
      },
    ],
    arm_gate: {
      ...DEFAULT_LIVE_READINESS_MODEL.safety_checklist.arm_gate,
      state: 'blocked',
      reason: 'Resolve blocked safety checklist rows before arming.',
    },
  },
  command_queue: {
    ...DEFAULT_LIVE_READINESS_MODEL.command_queue,
    queued_commands: [DEFAULT_LIVE_READINESS_MODEL.command_queue.queued_commands[1]!],
    last_actions: [DEFAULT_LIVE_READINESS_MODEL.command_queue.last_actions[0]!],
    undo_stack: [DEFAULT_LIVE_READINESS_MODEL.command_queue.undo_stack[1]!],
  },
  analyzer_panel: {
    ...DEFAULT_LIVE_READINESS_MODEL.analyzer_panel,
    reference_label: 'The Bells - Jeff Mills',
    panel_status: 'ready',
    bpm: 132,
    tempo_stability_percent: 86,
    waveform_bins: [
      { ...DEFAULT_LIVE_READINESS_MODEL.analyzer_panel.waveform_bins[0]!, value_percent: 64, status: 'active' },
      { ...DEFAULT_LIVE_READINESS_MODEL.analyzer_panel.waveform_bins[1]!, value_percent: 82, status: 'hot' },
    ],
    spectrum_bands: [
      { ...DEFAULT_LIVE_READINESS_MODEL.analyzer_panel.spectrum_bands[0]!, value_percent: 78, status: 'active' },
      { ...DEFAULT_LIVE_READINESS_MODEL.analyzer_panel.spectrum_bands[4]!, value_percent: 31, status: 'low' },
    ],
  },
  hardware_rail: {
    ...DEFAULT_LIVE_READINESS_MODEL.hardware_rail,
    cards: DEFAULT_LIVE_READINESS_MODEL.hardware_rail.cards.slice(0, 2),
  },
  snapshot_compatibility: {
    ...DEFAULT_LIVE_READINESS_MODEL.snapshot_compatibility,
    summary: '8 of 12 pads are snapshot-mutable; 4 are planned/locked.',
    pads: [
      DEFAULT_LIVE_READINESS_MODEL.snapshot_compatibility.pads[0]!,
      DEFAULT_LIVE_READINESS_MODEL.snapshot_compatibility.pads[11]!,
    ],
  },
};

const performanceFlow: LivePerformanceFlowModel = {
  ...DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL,
  flow_status: 'mock-safe-review',
  current_step_key: 'kit-core',
  steps: [
    DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL.steps[0]!,
    {
      ...DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL.steps[1]!,
      key: 'kit-core',
      label: 'Kit Core',
      rytm_command: 'kit-core',
      analog_four_action: 'review low-pulse candidate',
      send_policy: 'stage-review-send',
      status: 'staged',
    },
    DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL.steps[6]!,
  ],
};

describe('LiveReadinessPanel', () => {
  it('renders all passive GUI model surfaces as visible consumers', () => {
    render(<LiveReadinessPanel model={model} />);

    expect(screen.getByTestId('live-readiness-panel')).toBeInTheDocument();
    expect(screen.getByTestId('live-12-pad-surface')).toHaveTextContent('Pad Surface');
    expect(screen.getByTestId('live-pad-12')).toHaveTextContent('BD Acoustic');
    expect(screen.getByTestId('live-device-inventory')).toHaveTextContent('Analog Four MKII');
    expect(screen.getByTestId('live-scene-queue')).toHaveTextContent('Metallic Pressure');
    expect(screen.getByTestId('live-status-footer')).toHaveTextContent('No MIDI Port Open');
    expect(screen.getByTestId('live-snapshot-history')).toHaveTextContent('industrial-peak');
    expect(screen.getByTestId('live-safety-checklist')).toHaveTextContent('3 / 4');
    expect(screen.getByTestId('live-command-queue')).toHaveTextContent('Mutate Pad 11');
    expect(screen.getByTestId('live-analyzer-panel')).toHaveTextContent('The Bells - Jeff Mills');
    expect(screen.getByTestId('live-hardware-rail')).toHaveTextContent('Open MIDI Port');
    expect(screen.getByTestId('live-snapshot-compatibility')).toHaveTextContent(
      '8 of 12 pads are snapshot-mutable',
    );
  });

  it('renders the default model with 12 pads and both Elektron devices', () => {
    render(<LiveReadinessPanel />);

    const padSurface = screen.getByTestId('live-12-pad-surface');
    expect(padSurface).toHaveTextContent('4 active pads, 8 planned pads');
    expect(within(padSurface).getByTestId('live-pad-1')).toHaveTextContent('BD Hard');
    expect(within(padSurface).getByTestId('live-pad-5')).toHaveTextContent(
      'awaiting V1.34-compatible mutation routing for pads 5-12',
    );
    expect(within(padSurface).getByTestId('live-pad-5')).toHaveClass('planned_v134');
    expect(within(padSurface).getByTestId('live-pad-12')).toHaveTextContent('BD Acoustic');
    expect(screen.getByTestId('live-device-inventory')).toHaveTextContent('Analog Rytm MKII');
    expect(screen.getByTestId('live-device-inventory')).toHaveTextContent('Analog Four MKII');
  });

  it('renders the passive performance flow across Rytm and Analog Four lanes', () => {
    render(<LiveReadinessPanel model={model} performanceFlow={performanceFlow} />);

    const flowPanel = screen.getByTestId('live-performance-flow');
    expect(flowPanel).toHaveTextContent('Performance Flow');
    expect(flowPanel).toHaveTextContent('mock-safe-review');

    const captureStep = within(flowPanel).getByTestId('live-performance-flow-step-capture-anchor');
    expect(captureStep).toHaveTextContent('kit/resnapshot');
    expect(captureStep).toHaveTextContent('receive-only');

    const kitCoreStep = within(flowPanel).getByTestId('live-performance-flow-step-kit-core');
    expect(kitCoreStep).toHaveClass('staged');
    expect(kitCoreStep).toHaveTextContent('review low-pulse candidate');
    expect(kitCoreStep).toHaveTextContent('stage-review-send');

    const homeStep = within(flowPanel).getByTestId('live-performance-flow-step-home');
    expect(homeStep).toHaveTextContent('Z + send');
    expect(homeStep).toHaveTextContent('restore-anchor');

    expect(flowPanel).toHaveTextContent('a4_outbound_macro_send');
    expect(flowPanel).toHaveTextContent('unattended_hardware_behavior');
  });

  it('keeps hardware rail actions declarative and disabled in passive mode', () => {
    render(<LiveReadinessPanel model={model} />);

    const hardwareRail = screen.getByTestId('live-hardware-rail');
    expect(within(hardwareRail).getByRole('button', { name: 'Toggle dry run' })).toBeDisabled();
    expect(within(hardwareRail).getByRole('button', { name: 'Open MIDI Port' })).toBeDisabled();
  });

  it('has no axe-core violations', async () => {
    const { container } = render(<LiveReadinessPanel model={model} />);
    const results = await runAxe(container);
    expect(results.violations.length, violationSummary(results)).toBe(0);
  });
});
