/**
 * Library — pure PanelSpec selector + helpers over the library record slice
 * (no React, no fetch, no state).
 *
 * The passive browse table goes through the schema-driven PanelSpec platform
 * (`PanelRenderer`); search / tag / import interactions live in
 * `LibraryPanel.tsx`.
 */

import type { PanelSpecDict } from '../../types/live_gui_protocol';
import type { LibraryRecord } from '../../ws/protocol';

/** Split a comma-separated tags draft into clean tag strings. */
export function splitTags(draft: string): string[] {
  return draft
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => tag !== '');
}

/** Build the passive PanelSpec; `null` means the library was never loaded. */
export function libraryPanelSpec(records: LibraryRecord[] | null): PanelSpecDict {
  if (records === null) {
    return {
      panel_id: 'library',
      title: 'Library',
      status_badges: [{ label: 'not loaded', tone: 'neutral', icon: '•' }],
      sections: [
        {
          heading: 'Records',
          kind: 'rows',
          rows: ['Library not loaded yet — press Load library.'],
          table: null,
          chips: [],
        },
      ],
      required_actions: [],
      blocked_actions: [],
      safety_lines: ['captured records only — no hardware path'],
    };
  }
  return {
    panel_id: 'library',
    title: 'Library',
    status_badges: [{ label: `${records.length} record(s)`, tone: 'ok', icon: '✓' }],
    sections: [
      {
        heading: 'Records',
        kind: 'table',
        rows: [],
        table: {
          columns: ['Kit', 'Device', 'Captured', 'Tags', 'Record id'],
          rows: records.map((record) => [
            record.kit_name,
            record.device_id,
            record.captured_at,
            record.tags.join(', '),
            record.record_id,
          ]),
        },
        chips: [],
      },
    ],
    required_actions: [],
    blocked_actions: [],
    safety_lines: ['captured records only — no hardware path'],
  };
}
