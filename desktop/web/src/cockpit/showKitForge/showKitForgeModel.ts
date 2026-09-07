import type { PanelSpecDict } from '../../types/live_gui_protocol';
import type {
  ShowBank,
  ShowBankEntry,
  ShowBankState,
  ShowKitForgeStatus,
} from '../../ws/protocol';

export const SHOW_STATUS_LABELS: Readonly<Record<ShowKitForgeStatus, string>> = {
  source: 'Source anchored',
  candidate: 'In-memory candidate',
  favorite: 'Favorite — not hardware-saved',
  'hardware-saved': 'Manually saved — attested/unverified',
  verified: 'Verified recapture',
  'show-ready': 'Show-ready',
};

/** Decide whether a new authoritative revision may replace a local form draft. */
export function shouldAdoptServerDraft(
  identityChanged: boolean,
  draftDirty: boolean,
  serverMatchesDraft: boolean,
): boolean {
  return identityChanged || !draftDirty || serverMatchesDraft;
}

export function normalizePackId(value: string): string {
  const normalized = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^[^a-z0-9]+/, '')
    .replace(/[-_]+$/, '')
    .slice(0, 96);
  return normalized === '' ? 'show-bank' : normalized;
}

export function fingerprintMatchLabel(matches: boolean): 'Match' | 'Mismatch' {
  return matches ? 'Match' : 'Mismatch';
}

export function findActiveBank(showBank: ShowBankState | null): ShowBank | null {
  if (showBank === null || showBank.active_bank_id === null) return null;
  return showBank.banks.find((bank) => bank.bank_id === showBank.active_bank_id) ?? null;
}

export function findEntry(bank: ShowBank | null, entryId: string | null): ShowBankEntry | null {
  if (bank === null || bank.entries.length === 0) return null;
  if (entryId !== null) {
    const selected = bank.entries.find((entry) => entry.entry_id === entryId);
    if (selected !== undefined) return selected;
  }
  if (bank.active_entry_id !== null) {
    const active = bank.entries.find((entry) => entry.entry_id === bank.active_entry_id);
    if (active !== undefined) return active;
  }
  // The nonempty bank check above guarantees a first cue.
  return [...bank.entries].sort((left, right) => left.cue_index - right.cue_index)[0] as ShowBankEntry;
}

export function moveEntryIds(
  entries: readonly ShowBankEntry[],
  entryId: string,
  direction: -1 | 1,
): string[] | null {
  const ordered = [...entries].sort((left, right) => left.cue_index - right.cue_index);
  const moved = ordered.find((entry) => entry.entry_id === entryId);
  if (moved === undefined) return null;
  const index = ordered.indexOf(moved);
  const nextIndex = index + direction;
  if (nextIndex < 0 || nextIndex >= ordered.length) return null;
  ordered.splice(index, 1);
  ordered.splice(nextIndex, 0, moved);
  return ordered.map((entry) => entry.entry_id);
}

/** Apply a cue move only when the requested row and direction are valid. */
export function applyEntryMove(
  entries: readonly ShowBankEntry[],
  entryId: string,
  direction: -1 | 1,
  onMove: (entryIds: string[]) => void,
): boolean {
  const entryIds = moveEntryIds(entries, entryId, direction);
  if (entryIds === null) return false;
  onMove(entryIds);
  return true;
}

export function mismatchMessages(entry: ShowBankEntry | null): string[] {
  if (entry === null) return [];
  const messages: string[] = [];
  for (const [label, recapture] of [
    ['Rytm', entry.rytm_recapture],
    ['Analog Four', entry.analog_four_recapture],
  ] as const) {
    if (recapture !== null && !recapture.matches_candidate) {
      messages.push(
        `${label} semantic fingerprint mismatch: expected ${recapture.expected_semantic_fingerprint}; ` +
          `observed ${recapture.observed_semantic_fingerprint ?? 'unavailable'}. ` +
          `Immutable source ${recapture.source_semantic_fingerprint}: ${
            recapture.matches_source ? 'observed capture matches source' : 'observed capture does not match source'
          }. ${recapture.comparison_reason}`,
      );
    }
  }
  const preflight = entry.show_time_preflight;
  if (preflight !== null && !preflight.rytm_matches) {
    messages.push(
      `Rytm show-time full fingerprint mismatch: expected ${preflight.expected_rytm_fingerprint}; ` +
        `observed ${preflight.observed_rytm_fingerprint}. ${preflight.reason}`,
    );
  }
  if (preflight !== null && !preflight.a4_matches) {
    messages.push(
      `Analog Four show-time full fingerprint mismatch: expected ${preflight.expected_a4_fingerprint}; ` +
        `observed ${preflight.observed_a4_fingerprint}. ${preflight.reason}`,
    );
  }
  return messages;
}

/**
 * Adapt authoritative readiness fields to the existing schema renderer. This
 * function formats server truth; it never promotes or derives lifecycle state.
 */
export function showReadinessPanelSpec(
  bank: ShowBank | null,
  entry: ShowBankEntry | null,
  stale = false,
): PanelSpecDict {
  if (bank === null) {
    return {
      panel_id: 'show-kit-forge-readiness',
      title: 'Show readiness',
      status_badges: [{ label: 'Waiting for a bank', tone: 'neutral', icon: '•' }],
      sections: [
        {
          heading: 'Authoritative state',
          kind: 'rows',
          rows: ['Create or select a show bank to begin.'],
          table: null,
          chips: [],
        },
      ],
      required_actions: [],
      blocked_actions: [],
      safety_lines: ['No demo fallback', 'A4 SEND blocked', 'OXI owns sequencing'],
    };
  }

  if (stale) {
    return {
      panel_id: 'show-kit-forge-readiness',
      title: 'Show bank readiness',
      status_badges: [{ label: 'Readiness unavailable — refresh required', tone: 'warn', icon: '•' }],
      sections: [{
        heading: 'Last known state',
        kind: 'rows',
        rows: ['Reconnect and wait for a fresh server packet before using saved readiness evidence.'],
        table: null,
        chips: [],
      }],
      required_actions: ['Refresh from server.'],
      blocked_actions: ['Forge actions pending fresh state', 'Analog Four SEND — offline saved-KIT only'],
      safety_lines: ['OXI owns sequencing', 'Direct OXI control disabled'],
    };
  }

  const bankStatus = bank.readiness;
  const cueStatus = entry?.readiness;
  const sections = [
    {
      heading: 'Bank blocked reasons',
      kind: 'rows' as const,
      rows: bankStatus.blocked_reasons,
      table: null,
      chips: [],
    },
  ];
  if (entry !== null) {
    sections.push({
      heading: `Active cue blocked reasons — ${entry.name}`,
      kind: 'rows',
      rows: entry.readiness.blocked_reasons,
      table: null,
      chips: [],
    });
  }
  return {
    panel_id: 'show-kit-forge-readiness',
    title: 'Show bank readiness',
    status_badges: [
      {
        label: `Bank: ${SHOW_STATUS_LABELS[bankStatus.status]}`,
        tone: bankStatus.show_ready
          ? 'ok'
          : bankStatus.blocked_reasons.length > 0
            ? 'warn'
            : 'neutral',
        icon: bankStatus.show_ready ? '✓' : '•',
      },
      ...(cueStatus === undefined
        ? []
        : [
            {
              label: `Active cue: ${SHOW_STATUS_LABELS[cueStatus.status]}`,
              tone: cueStatus.show_ready
                ? ('ok' as const)
                : cueStatus.blocked_reasons.length > 0
                  ? ('warn' as const)
                  : ('neutral' as const),
              icon: cueStatus.show_ready ? '✓' : '•',
            },
          ]),
    ],
    sections,
    required_actions: [
      ...bankStatus.recovery_actions.map((action) => `Bank: ${action}`),
      ...(cueStatus?.recovery_actions.map((action) => `Active cue: ${action}`) ?? []),
    ],
    blocked_actions: ['Analog Four SEND — offline saved-KIT only'],
    safety_lines: ['OXI owns sequencing', 'Direct OXI control disabled'],
  };
}
