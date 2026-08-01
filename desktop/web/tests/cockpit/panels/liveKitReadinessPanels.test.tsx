import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { PerformanceConsole } from '../../../src/cockpit/PerformanceConsole';
import type { LiveGuiPerformanceConsoleModelDict } from '../../../src/types/live_gui_protocol';
import { performanceConsoleModel } from '../performanceConsoleFixture';

// Pure move from PerformanceConsole.test.tsx: the live-kit readiness-gate
// panel group (workbench mutation gates + package audition checks).

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

describe('PerformanceConsole live-kit readiness panels', () => {
  beforeEach(() => {
    window.localStorage.clear();
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
});
