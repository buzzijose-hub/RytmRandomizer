/**
 * Tests for LiveReadinessPanel -- consumers for the passive GUI model surfaces.
 */

import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { LiveReadinessPanel, type LiveReadinessModel } from '../../src/cockpit/LiveReadinessPanel';

import { runAxe, violationSummary } from '../a11y/__helpers__/axe';

const model = {
  padSurface: {
    summary: '4 active pads, 8 planned pads',
    pads: [
      {
        pad: 1,
        trackCode: 'BD',
        label: 'BD Hard',
        state: 'active_v134',
        role: 'kick',
        machine: 'BD Hard',
        lockReason: 'ready for dry-run review',
      },
      {
        pad: 12,
        trackCode: 'BD',
        label: 'BD Acoustic',
        state: 'planned_expansion',
        role: 'accent kick',
        machine: 'BD Acoustic',
        lockReason: 'awaiting V1.34-compatible mutation routing',
      },
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
        capabilities: ['snapshot_decode', 'mutation_plan'],
      },
      {
        deviceId: 'analog_four_mk2',
        displayName: 'Analog Four MKII',
        roleSummary: '4-track synth performance surface',
        trackCountLabel: '4 tracks',
        status: 'mock_safe',
        capabilities: ['snapshot_decode', 'mock_render'],
      },
    ],
  },
  sceneQueue: {
    queueStatus: 'review-needed',
    scenes: [
      {
        sceneKey: 'S0',
        label: 'Home Clean',
        description: 'Return to anchors',
        affectedPads: '1/2/3/4',
        depthPercent: 15,
        dryRunMessages: 18,
        status: 'safe',
      },
      {
        sceneKey: 'S3',
        label: 'Metallic Pressure',
        description: 'Grit-forward intensity',
        affectedPads: '1/2/3/4',
        depthPercent: 68,
        dryRunMessages: 93,
        status: 'high-risk',
      },
    ],
    previewQueue: [
      {
        sceneKey: 'S3',
        label: 'Metallic Pressure',
        position: 'current',
        duration: '32s',
        status: 'high-risk',
      },
    ],
  },
  statusFooter: {
    items: [
      {
        key: 'safety',
        label: 'Mock Safe',
        value: 'No hardware will be changed',
        severity: 'safe',
      },
      {
        key: 'midi-port',
        label: 'No MIDI Port Open',
        value: 'No MIDI port selected',
        severity: 'safe',
      },
    ],
  },
  snapshotHistory: {
    entries: [
      {
        snapshotId: 'snap-1',
        label: 'Initial snapshot',
        summary: 'analog_rytm_mk2: 12 pad(s), scene A01, 132 BPM',
        state: 'past',
      },
      {
        snapshotId: 'snap-3',
        label: 'industrial-peak',
        summary: 'analog_rytm_mk2: 12 pad(s), scene A01, 132 BPM',
        state: 'current',
      },
    ],
    controls: [
      {
        key: 'undo',
        label: 'Undo',
        state: 'enabled',
        reason: 'Undo to previous snapshot snap-2.',
      },
      {
        key: 'redo',
        label: 'Redo',
        state: 'disabled',
        reason: 'No redo stack modeled yet.',
      },
    ],
  },
  safetyChecklist: {
    status: 'blocked',
    passedLabel: '3 / 4',
    items: [
      {
        key: 'guards-enabled',
        label: 'All guards enabled',
        status: 'passed',
        message: 'All safety guards enabled',
      },
      {
        key: 'snapshot-compatible',
        label: 'Snapshot compatibility verified',
        status: 'blocked',
        message: 'Snapshot compatibility is not verified',
      },
    ],
    armGate: {
      label: 'Arm Hardware',
      state: 'blocked',
      reason: 'Resolve blocked safety checklist rows before arming.',
    },
  },
  commandQueue: {
    queueStatus: 'queued',
    commands: [
      {
        key: 'queued-command-mutate-pad-11',
        label: 'Mutate Pad 11 (SY Raw)',
        status: 'queued',
        target: 'Pad 11 / SY Raw',
        messageCount: 8,
      },
    ],
    lastActions: [
      {
        key: 'last-action-snap-3',
        label: 'Send snapshot',
        status: 'current',
        detail: 'saved snapshot via send',
      },
    ],
    undoStack: [
      {
        key: 'undo-stack-snap-2',
        label: 'Auto snapshot 2',
        status: 'available',
      },
    ],
  },
  analyzerPanel: {
    title: 'Analyzer (Post-Mutation Preview)',
    referenceLabel: 'The Bells - Jeff Mills',
    panelStatus: 'ready',
    bpmLabel: '132.0 BPM',
    tempoStabilityLabel: '86%',
    waveformBins: [
      { label: 'bin 1', valuePercent: 64, status: 'active' },
      { label: 'bin 2', valuePercent: 82, status: 'hot' },
    ],
    spectrumBands: [
      { key: 'low', label: 'Low', valuePercent: 78, status: 'active' },
      { key: 'noise', label: 'Noise', valuePercent: 31, status: 'low' },
    ],
  },
  hardwareRail: {
    railStatus: 'mock-safe',
    cards: [
      {
        key: 'mock-dry-run',
        title: 'Mock / Dry Run',
        status: 'active',
        summary: 'All changes are simulated. No hardware will be modified.',
        actions: [
          {
            key: 'toggle-dry-run',
            label: 'Toggle dry run',
            enabled: false,
            reason: 'passive GUI state toggle metadata only',
          },
        ],
      },
      {
        key: 'midi-port',
        title: 'MIDI Port',
        status: 'none',
        summary: 'No MIDI port selected or opened.',
        actions: [
          {
            key: 'select-midi-port',
            label: 'Open MIDI Port',
            enabled: false,
            reason: 'no passive port labels supplied',
          },
        ],
      },
    ],
  },
  snapshotCompatibility: {
    statusBadge: 'Limited',
    summary: '8 of 12 pads are snapshot-mutable; 4 are planned/locked.',
    pads: [
      {
        pad: 1,
        label: 'BD Hard',
        status: 'compatible',
        machineCountLabel: '7 machines',
      },
      {
        pad: 12,
        label: 'BD Acoustic',
        status: 'planned',
        machineCountLabel: '3 machines',
      },
    ],
  },
} satisfies LiveReadinessModel;

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
    expect(within(padSurface).getByTestId('live-pad-1')).toHaveTextContent('BD Hard');
    expect(within(padSurface).getByTestId('live-pad-12')).toHaveTextContent('BD Acoustic');
    expect(screen.getByTestId('live-device-inventory')).toHaveTextContent('Analog Rytm MKII');
    expect(screen.getByTestId('live-device-inventory')).toHaveTextContent('Analog Four MKII');
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
