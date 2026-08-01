/**
 * Connection Doctor — pure PanelSpec selector over the read-only
 * `diagnostics` command payload (no React, no fetch, no state).
 *
 * Renders a pass/fail checklist (dependencies, ports, Elektron match), the
 * per-OS driver hint, the bounded error journal, and the errors-by-kind
 * counters. Every check row pairs a ✓/✗ glyph with text — never hue alone.
 */

import type { BadgeDict, PanelSpecDict } from '../../types/live_gui_protocol';
import type { DiagnosticsPayload } from '../../ws/protocol';

function checkRow(ok: boolean, okText: string, failText: string): string {
  return ok ? `✓ ${okText}` : `✗ ${failText}`;
}

function phaseBadge(diagnostics: DiagnosticsPayload): BadgeDict {
  const connection = diagnostics.connection;
  if (connection === null) {
    return { label: 'no connection manager', tone: 'warn', icon: '!' };
  }
  if (connection.phase === 'fault') {
    return { label: 'fault', tone: 'risk', icon: '⚠' };
  }
  if (connection.phase === 'listening' || connection.phase === 'armed') {
    return { label: connection.phase, tone: 'ok', icon: '●' };
  }
  return { label: connection.phase, tone: 'warn', icon: '◌' };
}

/** Build the passive PanelSpec; `null` means diagnostics never ran yet. */
export function connectionDoctorPanelSpec(
  diagnostics: DiagnosticsPayload | null,
): PanelSpecDict {
  if (diagnostics === null) {
    return {
      panel_id: 'connection-doctor',
      title: 'Connection Doctor',
      status_badges: [{ label: 'not run', tone: 'neutral', icon: '•' }],
      sections: [
        {
          heading: 'Checklist',
          kind: 'rows',
          rows: ['No diagnostics captured yet — press Refresh diagnostics.'],
          table: null,
          chips: [],
        },
      ],
      required_actions: [],
      blocked_actions: [],
      safety_lines: ['read-only health query'],
    };
  }

  const connection = diagnostics.connection;
  const inputCount = diagnostics.available_inputs.length;
  const outputCount = diagnostics.available_outputs.length;
  const checklist = [
    checkRow(
      connection !== null,
      'connection manager reporting',
      'no connection manager wired',
    ),
    checkRow(
      connection === null || connection.phase !== 'fault',
      `phase: ${connection === null ? 'unknown' : connection.phase}`,
      `enumeration fault: ${connection?.last_error_fingerprint ?? 'unknown'}`,
    ),
    checkRow(
      inputCount > 0,
      `${inputCount} MIDI input(s) visible`,
      'no MIDI inputs visible — check cable and driver',
    ),
    checkRow(
      outputCount > 0,
      `${outputCount} MIDI output(s) visible`,
      'no MIDI outputs visible — check cable and driver',
    ),
    checkRow(
      connection?.selected_input != null,
      `Elektron input matched: ${connection?.selected_input ?? ''}`,
      'no Elektron input matched',
    ),
    checkRow(
      connection?.selected_output != null,
      `Elektron output matched: ${connection?.selected_output ?? ''}`,
      'no Elektron output matched',
    ),
  ];
  const errorChips = Object.entries(diagnostics.errors_by_kind).map(
    ([kind, count]) => `${kind}: ${count}`,
  );

  return {
    panel_id: 'connection-doctor',
    title: 'Connection Doctor',
    status_badges: [phaseBadge(diagnostics)],
    sections: [
      { heading: 'Checklist', kind: 'rows', rows: checklist, table: null, chips: [] },
      {
        heading: 'Driver hint',
        kind: 'rows',
        rows: [`platform: ${diagnostics.platform}`, diagnostics.driver_hint],
        table: null,
        chips: [],
      },
      {
        heading: 'Error journal',
        kind: 'table',
        rows: [],
        table: {
          columns: ['Fingerprint', 'Message', 'Timestamp'],
          rows: diagnostics.journal.map((entry) => [
            entry.fingerprint,
            entry.message,
            String(entry.ts),
          ]),
        },
        chips: [],
      },
      {
        heading: 'Errors by kind',
        kind: 'chips',
        rows: [],
        table: null,
        chips: errorChips.length > 0 ? errorChips : ['none recorded'],
      },
    ],
    required_actions: [],
    blocked_actions: [],
    safety_lines: ['read-only health query'],
  };
}
