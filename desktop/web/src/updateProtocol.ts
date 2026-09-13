/**
 * Update protocol — the ONE TypeScript home for the auto-update wire shapes
 * (reuse contract R4 of `docs/superpowers/plans/2026-09-07-autoupdate-implementation.md`).
 *
 * Two shapes cross the language boundary and are declared here exactly once:
 *
 *   - **I2** — the shell -> webview event `rytm-update-state`, carrying the
 *     §5 state machine's current state for the cockpit to render.
 *   - **I8** — one row of the update journal (`update-journal.jsonl`), whose
 *     `event` is drawn from the closed §5.1 vocabulary.
 *
 * Every consumer (store slice, header chip, update panel, e2e specs) imports
 * from here. Re-declaring either shape inline — even under a different
 * symbol name — is the fork R4 exists to prevent (Gate 17).
 *
 * IPC adapters below subscribe and query the local shell. They never use
 * the backend WebSocket or initiate an update check on mount.
 */

/**
 * Closed vocabulary of §5 client states the shell reports.
 *
 * `dev_loop` is the browser two-terminal loop where no shell exists at all;
 * it is a rendering state, not a shell-reported one, and the cockpit adopts
 * it when no `rytm-update-state` event has ever arrived.
 */
export const UPDATE_STATES = [
  'idle',
  'checking',
  'up_to_date',
  'check_failed',
  'update_available',
  'downloading',
  'staged',
  'stage_failed',
  'failed',
  'skipped',
  'installing',
  'frozen',
  'dev_loop',
] as const;

export type UpdateState = (typeof UPDATE_STATES)[number];

/**
 * Closed §5.1 journal event vocabulary. The panel's activity list renders
 * these verbatim — they are reason codes, not prose, and are never
 * translated or prettified into something the journal does not say.
 */
export const UPDATE_JOURNAL_EVENTS = [
  'check_started',
  'check_ok',
  'check_failed',
  'manifest_rejected',
  'bucket_excluded',
  'download_started',
  'download_ok',
  'stage_failed',
  'signature_rejected',
  'consent_granted',
  'install_started',
  'install_ok',
  'install_failed',
  'skip_recorded',
  'freeze_suppressed',
  'ping_ok',
  'ping_failed',
] as const;

export type UpdateJournalEvent = (typeof UPDATE_JOURNAL_EVENTS)[number];

/** The three §5 consent choices, in the normative §7.1 presentation order. */
export const UPDATE_CONSENT_CHOICES = [
  'install_on_quit',
  'install_now',
  'skip_this_version',
] as const;

export type UpdateConsentChoice = (typeof UPDATE_CONSENT_CHOICES)[number];

/** Spec §7.1 / decision D3: `When I quit the app` is pre-selected. */
export const DEFAULT_CONSENT_CHOICE: UpdateConsentChoice = 'install_on_quit';

/** The two release channels (§4 channel gate). */
export const UPDATE_CHANNELS = ['stable', 'beta'] as const;

export type UpdateChannel = (typeof UPDATE_CHANNELS)[number];

/**
 * **I8** — one update-journal row.
 *
 * `detail` is a bounded, path-free string produced by the shell (typed
 * reason codes plus sizes/durations only — the #224/#238 hygiene standard).
 * The cockpit renders it as given and never reconstructs it from an error.
 */
export interface UpdateJournalRow {
  /** ISO-8601 timestamp minted by the shell. */
  readonly ts: string;
  readonly event: UpdateJournalEvent;
  /** Version the row concerns; empty when the row predates a known version. */
  readonly version: string;
  readonly detail: string;
}

/**
 * **I2** — payload of the shell -> webview `rytm-update-state` event.
 *
 * The chip and the panel's staged block are the same state rendered twice;
 * neither derives anything the shell did not send.
 */
export interface UpdateStateEvent {
  readonly state: UpdateState;
  /** Version the state concerns (the staged/available version when relevant). */
  readonly version: string;
  /** Manifest release notes for the staged version; empty when none. */
  readonly notes: string;
  /** True only when the manifest flags the release (spec §2.5). */
  readonly hardware_revalidation: boolean;
  /**
   * Typed reason code for a failure state, or `null`. Verbatim from the
   * journal row — never a `str(err)` passthrough and never a path.
   */
  readonly error_code: string | null;
}

/** Tauri IPC event name used by the shell to deliver I2. */
export const UPDATE_STATE_EVENT_NAME = 'rytm-update-state';

/** Read-only shell snapshot, replayed after the event listener is installed. */
export interface UpdateSnapshot {
  readonly state: UpdateStateEvent;
  readonly journal: ReadonlyArray<UpdateJournalRow>;
  readonly channel: UpdateChannel;
  readonly frozen: boolean;
}

/**
 * The cockpit's own view of the update surface: the last I2 payload the
 * shell pushed, plus its journal tail and resolved launch settings.
 */
export interface UpdateSlice {
  /** Last I2 payload, or `null` when the shell has never spoken (dev loop). */
  readonly state: UpdateStateEvent | null;
  /** Journal tail, oldest first, as the shell reported it (I8). */
  readonly journal: ReadonlyArray<UpdateJournalRow>;
  /** Release channel resolved by the shell at launch. */
  readonly channel: UpdateChannel;
  /** Process-lifetime shell posture (`RYTM_RAND_UPDATES=off`). */
  readonly frozen: boolean;
  /** Consent choice the operator confirmed for `state.version`, if any. */
  readonly confirmedChoice: UpdateConsentChoice | null;
}

/** Journal tail bound — the panel shows recent activity, not history. */
export const UPDATE_JOURNAL_LIMIT = 8;

/** Native snapshot/diagnostic tail bound, independent of the short panel list. */
export const UPDATE_SNAPSHOT_JOURNAL_LIMIT = 50;

// ---------- Pure predicates over the contract shapes ----------

/** Type guard for a value claiming to be an `UpdateState`. */
export function isUpdateState(value: unknown): value is UpdateState {
  return (
    typeof value === 'string' && (UPDATE_STATES as ReadonlyArray<string>).includes(value)
  );
}

/** Type guard for a value claiming to be an `UpdateJournalEvent`. */
export function isUpdateJournalEvent(value: unknown): value is UpdateJournalEvent {
  return (
    typeof value === 'string' &&
    (UPDATE_JOURNAL_EVENTS as ReadonlyArray<string>).includes(value)
  );
}

/**
 * Narrow an untrusted payload (a `CustomEvent.detail` off `window`) to I2.
 *
 * Returns `null` rather than throwing: a shell that speaks a shape we do not
 * recognise must leave the cockpit in its previous honest state, never crash
 * the panel. An unknown `state` or a non-object payload is refused outright.
 */
export function parseUpdateStateEvent(payload: unknown): UpdateStateEvent | null {
  if (typeof payload !== 'object' || payload === null) return null;
  const raw = payload as Record<string, unknown>;
  if (!isUpdateState(raw.state)) return null;
  const errorCode = raw.error_code;
  return {
    state: raw.state,
    version: typeof raw.version === 'string' ? raw.version : '',
    notes: typeof raw.notes === 'string' ? raw.notes : '',
    hardware_revalidation: raw.hardware_revalidation === true,
    error_code: typeof errorCode === 'string' && errorCode !== '' ? errorCode : null,
  };
}

/** Narrow one untrusted journal row to I8, or `null` when unrecognised. */
export function parseUpdateJournalRow(payload: unknown): UpdateJournalRow | null {
  if (typeof payload !== 'object' || payload === null) return null;
  const raw = payload as Record<string, unknown>;
  if (!isUpdateJournalEvent(raw.event)) return null;
  return {
    ts: typeof raw.ts === 'string' ? raw.ts : '',
    event: raw.event,
    version: typeof raw.version === 'string' ? raw.version : '',
    detail: typeof raw.detail === 'string' ? raw.detail : '',
  };
}

/** Refuse incomplete snapshots rather than inventing the shell's posture. */
export function parseUpdateSnapshot(payload: unknown): UpdateSnapshot | null {
  if (typeof payload !== 'object' || payload === null) return null;
  const raw = payload as Record<string, unknown>;
  if (raw.channel !== 'stable' && raw.channel !== 'beta') return null;
  if (typeof raw.frozen !== 'boolean' || !Array.isArray(raw.journal)) return null;
  const state = parseUpdateStateEvent(raw.state);
  if (state === null) return null;
  const journal: UpdateJournalRow[] = [];
  for (const value of raw.journal.slice(-UPDATE_SNAPSHOT_JOURNAL_LIMIT)) {
    const row = parseUpdateJournalRow(value);
    if (row === null) return null;
    journal.push(row);
  }
  return { state, journal, channel: raw.channel, frozen: raw.frozen };
}

/**
 * Read the current local shell posture and sanitized journal without checking
 * for updates or subscribing. Connection Doctor uses this even if the update
 * panel has never mounted. The native journal owns detail-code sanitation;
 * parsing projects only I8 fields and bounds the number of exported rows.
 */
export async function readUpdateSnapshot(): Promise<UpdateSnapshot | null> {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    return parseUpdateSnapshot(await invoke('update_snapshot'));
  } catch {
    return null;
  }
}

/**
 * `staged` is the only state that carries a consent prompt: the artifact is
 * on disk and the operator's choice is the last gate (§5 "download eagerly,
 * install consensually").
 */
export function isConsentPending(slice: UpdateSlice): boolean {
  return (
    !slice.frozen &&
    slice.state !== null &&
    slice.state.state === 'staged' &&
    slice.confirmedChoice === null
  );
}

/**
 * The header chip renders exactly when an update is staged and unfrozen.
 * Freeze mode hides it outright (§7); every other state is chip-silent —
 * `rollout-excluded` is indistinguishable from up-to-date by design (§5).
 */
export function shouldShowChip(slice: UpdateSlice): boolean {
  return isConsentPending(slice);
}

/** Chip text — icon + shape + text, never colour alone. */
export function chipLabel(version: string): string {
  return `⬆ ${version} ready`;
}

/**
 * Journal rows the activity list shows: newest first, bounded.
 *
 * The shell writes the journal oldest-first; spec §7.1's element→contract
 * table specifies "newest first" for this list, so the tail is reversed
 * here once and every consumer renders what it is handed.
 *
 * Known source disagreement (recorded deliberately, not silently resolved):
 * the pixel render at `docs/design/update-consent-prompt.html` legend #5
 * says "newest last". Spec §7.1 states that where render and spec disagree
 * the spec section wins, so "newest first" is the implemented contract; the
 * render's three sample rows share one timestamp and therefore do not
 * actually distinguish the two orderings.
 */
export function recentJournal(
  journal: ReadonlyArray<UpdateJournalRow>,
  limit: number = UPDATE_JOURNAL_LIMIT,
): ReadonlyArray<UpdateJournalRow> {
  return journal.slice(-limit).reverse();
}

/**
 * Rows that must ALSO be mirrored into the cockpit operator log (the §5.1
 * failure-honesty floor): a silently failing updater is impossible.
 */
export const MIRRORED_FAILURE_EVENTS: ReadonlyArray<UpdateJournalEvent> = [
  'check_failed',
  'signature_rejected',
];

export function isMirroredFailure(row: UpdateJournalRow): boolean {
  return MIRRORED_FAILURE_EVENTS.includes(row.event);
}

/** Operator-log message for a mirrored failure row. Bounded and path-free. */
export function mirroredFailureMessage(row: UpdateJournalRow): string {
  const detail = row.detail === '' ? 'no detail' : row.detail;
  return `Update ${row.event}: ${detail}`;
}

// ---------- Rendering adapter for the shared operator-log list (R4) ----------

/**
 * Severity of a journal row as the shared log list renders it.
 *
 * `error` for the closed vocabulary's failure events, `success` for the
 * terminal good outcomes, `info` for everything in between. The severity is
 * derived from the event code alone — never from `detail`, which is opaque
 * shell-authored text.
 */
const JOURNAL_FAILURE_EVENTS: ReadonlyArray<UpdateJournalEvent> = [
  'check_failed',
  'manifest_rejected',
  'stage_failed',
  'signature_rejected',
  'install_failed',
  'ping_failed',
];

const JOURNAL_SUCCESS_EVENTS: ReadonlyArray<UpdateJournalEvent> = [
  'check_ok',
  'download_ok',
  'install_ok',
];

export type UpdateJournalLevel = 'info' | 'success' | 'error';

export function journalRowLevel(event: UpdateJournalEvent): UpdateJournalLevel {
  if (JOURNAL_FAILURE_EVENTS.includes(event)) return 'error';
  if (JOURNAL_SUCCESS_EVENTS.includes(event)) return 'success';
  return 'info';
}

/**
 * One journal row rendered as a log line: `12:04  check_ok  1.35.1 available`.
 *
 * Timestamp, event code, and detail, separated by two spaces — the §7.1
 * three-column reading order, flattened into the single-line shape the
 * shared operator-log list renders. An empty field is dropped rather than
 * padded, so a row never claims a value the shell did not send.
 */
export function journalRowText(row: UpdateJournalRow): string {
  return [row.ts, row.event, row.detail].filter((part) => part !== '').join('  ');
}

/**
 * A journal row shaped for the shared operator-log list component (R4).
 *
 * The list takes `{id, level, message}`; this is the ONLY adapter between
 * I8 and it. Authoring a second journal-list component instead of reusing
 * the existing one is precisely the fork R4 forbids.
 */
export interface UpdateJournalLogEntry {
  readonly id: string;
  readonly level: UpdateJournalLevel;
  readonly message: string;
}

export function journalLogEntries(
  journal: ReadonlyArray<UpdateJournalRow>,
  limit: number = UPDATE_JOURNAL_LIMIT,
): ReadonlyArray<UpdateJournalLogEntry> {
  return recentJournal(journal, limit).map((row, index) => ({
    id: `update-journal-${index}-${row.ts}-${row.event}`,
    level: journalRowLevel(row.event),
    message: journalRowText(row),
  }));
}

/**
 * Subscribe to the shell's I2 update-state event. Returns an unsubscribe.
 *
 * **This function is the contract.** The I2 row originally fixed only the
 * event's NAME and PAYLOAD — the nouns — and left the transport free. The
 * shell emitted over Tauri IPC (`window.emit`) while the panel listened for a
 * DOM event (`window.addEventListener`): two different channels, nothing
 * bridging them. Both sides were individually correct, fully typed and 100%
 * covered, `cargo test` and `vitest` were green, and no message could ever
 * cross — in the bundled app the update chip simply never appeared.
 *
 * Naming the *call* rather than only the data is what closes that class of
 * defect, so every consumer goes through here and no component knows the
 * transport. `tests/architecture/test_cross_language_event_seams_agree.py`
 * fails if anything subscribes with `addEventListener` to an `emit`-ed event.
 *
 * Outside a Tauri webview (the two-terminal dev loop, or a plain browser)
 * `listen` is unavailable; this degrades to a no-op unsubscribe so the panel
 * renders its "updates run in the installed app" body rather than throwing
 * and blanking the cockpit (spec §7).
 *
 * Receive-only. Listening is not transmitting, so this is safe on mount and
 * does not need the armed-connection gate the #238 lesson requires of actions.
 */
export function subscribeUpdateState(
  onState: (event: UpdateStateEvent) => void,
  onSnapshot?: (snapshot: UpdateSnapshot) => void,
): () => void {
  let unlisten: (() => void) | null = null;
  let cancelled = false;
  let generation = 0;

  const refresh = async (): Promise<void> => {
    if (onSnapshot === undefined) return;
    const requestedGeneration = ++generation;
    const snapshot = await readUpdateSnapshot();
    // A newer event/request supersedes an older snapshot response. An
    // unmounted panel must not overwrite the next panel's state either.
    if (!cancelled && requestedGeneration === generation && snapshot !== null) {
      onSnapshot(snapshot);
    }
  };

  void import('@tauri-apps/api/event')
    .then(({ listen }) =>
      listen<unknown>(UPDATE_STATE_EVENT_NAME, (message) => {
        const parsed = parseUpdateStateEvent(message.payload);
        if (!cancelled && parsed !== null) {
          onState(parsed);
          void refresh();
        }
      }),
    )
    .then((stop) => {
      if (cancelled) stop();
      else {
        unlisten = stop;
        // Subscribe first: setup may have emitted before React mounted.
        void refresh();
      }
    })
    .catch(() => {
      // No Tauri bridge available. The panel's dev-loop body covers this; a
      // thrown error here would take the whole cockpit down over a chip.
    });

  return () => {
    cancelled = true;
    if (unlisten !== null) unlisten();
  };
}

/**
 * Ask the shell to check for an update now.
 *
 * Paired with {@link confirmUpdateChoiceOnShell} as the ONLY two ways the
 * panel reaches the updater. Before these existed the buttons were
 * decorative — "Check now" set a note and "Confirm choice" updated React
 * state, and neither reached the driver. Everything looked wired.
 *
 * A refusal or missing shell resolves false, so the panel cannot claim a
 * check happened when the command was never accepted.
 */
export async function requestUpdateCheck(): Promise<boolean> {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    return (await invoke('update_check_now')) === true;
  } catch {
    return false;
  }
}

/**
 * Send the operator's §7.1 consent decision to the shell.
 *
 * `choice` is one of {@link UPDATE_CONSENT_CHOICES}. The shell REFUSES an
 * unrecognised value rather than defaulting — there is no safe default, since
 * guessing "now" installs without consent and guessing "skip" suppresses an
 * update nobody dismissed — so a rejection here means the two ends have
 * drifted and should be surfaced, not swallowed.
 *
 * @returns `true` when the shell accepted the decision.
 */
export async function confirmUpdateChoiceOnShell(
  version: string,
  choice: UpdateConsentChoice,
): Promise<boolean> {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    return (await invoke('update_confirm_choice', { version, choice })) === true;
  } catch {
    return false;
  }
}
