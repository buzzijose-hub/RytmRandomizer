import type {
  LiveGuiAnalyzerPanelControlDict,
  LiveGuiPerformanceConsoleModelDict,
  PanelSpecDict,
} from '../../types/live_gui_protocol';

/**
 * First registry panel: the analyzer surface, expressed as a `PanelSpecDict`
 * selected from the passive console packet's `analyzer_panel` model. This is
 * the proof-path for the schema-driven panel platform — the bespoke analyzer
 * `<section>` in `PerformanceConsole.tsx` became a one-line registry entry.
 */

const ANALYZER_CONTROL_ORDER: ReadonlyArray<string> = ['preview', 'dry_run', 'arm_hardware'];

export function orderedAnalyzerControls(
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

function activeSafetyLines(safety: Readonly<Record<string, boolean>>): ReadonlyArray<string> {
  return Object.entries(safety)
    .filter(([, active]) => active)
    .map(([line]) => line);
}

export function analyzerPanelSpec(model: LiveGuiPerformanceConsoleModelDict): PanelSpecDict {
  const panel = model.analyzer_panel;
  return {
    panel_id: 'analyzer',
    title: panel.title,
    status_badges: [
      {
        label: panel.panel_status,
        tone: panel.panel_status === 'empty' ? 'warn' : 'ok',
        icon: '',
      },
      { label: panel.panel_mode, tone: 'neutral', icon: '' },
    ],
    sections: [
      {
        heading: 'Reference',
        kind: 'rows',
        rows: [panel.reference_label],
        table: null,
        chips: [],
      },
      {
        heading: 'Spectrum',
        kind: 'table',
        rows: [],
        table: {
          columns: ['Band', 'Range', 'Status', 'Level'],
          rows: panel.spectrum_bands.map((band) => [
            band.label,
            `${band.low_hz}-${band.high_hz} Hz`,
            band.status,
            `${band.value_percent}%`,
          ]),
        },
        chips: [],
      },
      {
        heading: 'Controls',
        kind: 'chips',
        rows: [],
        table: null,
        chips: orderedAnalyzerControls(panel.controls).map(
          (control) => `${control.label}: ${control.status}`,
        ),
      },
    ],
    required_actions: panel.required_actions,
    blocked_actions: panel.blocked_actions,
    safety_lines: activeSafetyLines(panel.safety),
  };
}
