import { render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { PerformanceConsole } from '../../../src/cockpit/PerformanceConsole';
import type { LiveGuiPerformanceConsoleModelDict } from '../../../src/types/live_gui_protocol';
import { performanceConsoleModel } from '../performanceConsoleFixture';

// Pure move from PerformanceConsole.test.tsx: the HUD panel group (topbar
// MIDI-port state, device rail fallbacks, bottom strip, snapshot deck).

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

describe('PerformanceConsole HUD panels', () => {
  beforeEach(() => {
    window.localStorage.clear();
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
});
