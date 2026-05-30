/**
 * AddStep — second wizard panel.
 *
 *   + kit · + sound · + song · + album · + artist
 *
 *   For file / folder kinds we open the bundled Tauri dialog plugin. If the call
 *   is unavailable (test or browser without a Tauri shell), we fall back to a
 *   plain text input. Reference picker is ALWAYS a text input (matches the spec —
 *   references are textual names, no file backing).
 *
 *   The accumulated source list renders below with a remove button per row. The "Analyze"
 *   action below is disabled until at least one source is added.
 *
 *   Draft submission is validated on click (Cluster-3 a11y fix): if either required
 *   field is blank, a `role="alert"` region is rendered, the offending input is marked
 *   `aria-invalid="true"`, `aria-describedby` is wired to the alert, and keyboard focus
 *   moves to the first invalid field. This satisfies WCAG 2.2 §3.3.1 / §3.3.3.
 */

import { useRef, useState, type ChangeEvent } from 'react';
import { open as openTauriDialog } from '@tauri-apps/plugin-dialog';

import type {
  InspirationSource,
  WizardSourceKind,
  WizardSourceMode,
} from '../types/wizard_protocol';
import { KIND_DISPLAY_ORDER, KIND_STRATEGY } from './kinds';

const DRAFT_ERROR_ID = 'wizard-draft-error';

export interface AddStepProps {
  sources: ReadonlyArray<InspirationSource>;
  onAddSource: (payload: {
    kind: WizardSourceKind;
    mode: WizardSourceMode;
    location: string;
    display_name: string;
  }) => boolean | void | Promise<boolean | void>;
  onRemoveSource: (sourceId: string) => void;
  onBack: () => void;
  onNext: () => void;
  submitError?: string | null;
  /**
   * Optional injection point for tests. Returns the picked path, or null if the user
   * cancelled. The production path dynamically imports `@tauri-apps/plugin-dialog`.
   */
  openDialog?: (mode: 'file' | 'folder') => Promise<string | null>;
}

interface PickerDraft {
  kind: WizardSourceKind;
  mode: WizardSourceMode;
}

/**
 * Default dialog opener — calls the bundled Tauri dialog plugin. When the plugin
 * is unavailable (test or browser without Tauri shell) returns null so the
 * caller falls back to the manual text input.
 */
interface TauriDialogModule {
  open: (opts: {
    directory?: boolean;
    multiple?: boolean;
  }) => Promise<string | string[] | null | undefined>;
}

/**
 * Indirected opener module. Exported only for tests so they can stub the Tauri
 * call while production keeps the plugin statically reachable for Vite.
 */
export const __tauriDialogImporter: { import: () => Promise<TauriDialogModule> } = {
  import: async () => ({ open: openTauriDialog }),
};

/**
 * Strip a path down to its trailing segment (split on either separator). Used to seed
 * the display name when the operator picks a file from disk. Exported for tests.
 */
export function basenameOf(path: string): string {
  // Trim trailing separators so `/a/b/` resolves to "b", not "". When the input is
  // entirely separators (or empty), trimming yields the empty string — fall back to
  // the original path so the operator can still see something.
  const trimmed = path.replace(/[\\/]+$/, '');
  if (trimmed === '') return path;
  const sepIndex = Math.max(trimmed.lastIndexOf('/'), trimmed.lastIndexOf('\\'));
  if (sepIndex < 0) return trimmed;
  return trimmed.slice(sepIndex + 1);
}

export async function defaultOpenDialog(mode: 'file' | 'folder'): Promise<string | null> {
  try {
    const mod = await __tauriDialogImporter.import();
    const result = await mod.open({ directory: mode === 'folder', multiple: false });
    if (result === null || result === undefined) return null;
    if (Array.isArray(result)) return result[0] ?? null;
    return result;
  } catch {
    return null;
  }
}

export function AddStep({
  sources,
  onAddSource,
  onRemoveSource,
  onBack,
  onNext,
  submitError = null,
  openDialog,
}: AddStepProps): JSX.Element {
  const [draft, setDraft] = useState<PickerDraft | null>(null);
  const [location, setLocation] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [browseFallbackMessage, setBrowseFallbackMessage] = useState<string | null>(null);
  const locationRef = useRef<HTMLInputElement>(null);
  const displayNameRef = useRef<HTMLInputElement>(null);
  const opener = openDialog ?? defaultOpenDialog;

  const openDraft = (kind: WizardSourceKind): void => {
    const mode = KIND_STRATEGY[kind].defaultMode;
    setDraft({ kind, mode });
    setLocation('');
    setDisplayName('');
    setError(null);
    setBrowseFallbackMessage(null);
  };

  const closeDraft = (): void => {
    setDraft(null);
    setLocation('');
    setDisplayName('');
    setError(null);
    setBrowseFallbackMessage(null);
  };

  const handleBrowse = async (currentDraft: PickerDraft): Promise<void> => {
    // `currentDraft.mode` is always 'file' or 'folder' here: the Browse button only
    // renders in those branches of the draft form. Narrow accordingly.
    const dialogMode: 'file' | 'folder' =
      currentDraft.mode === 'folder' ? 'folder' : 'file';
    const picked = await opener(dialogMode);
    if (picked === null) {
      setBrowseFallbackMessage(
        'Browse is unavailable in this shell. Paste the full path instead.',
      );
      locationRef.current?.focus();
      return;
    }
    setBrowseFallbackMessage(null);
    setLocation(picked);
    if (displayName === '') {
      setDisplayName(basenameOf(picked));
    }
  };

  /**
   * Validate `location` first, then `display_name`. The first-failing field
   * captures focus + describes itself via `aria-describedby` pointing at the
   * single `role="alert"` region rendered below the draft. This is the WCAG
   * 2.2 §3.3.1 / §3.3.3 error-identification pattern.
   */
  const handleConfirm = async (currentDraft: PickerDraft): Promise<void> => {
    const trimmedLocation = location.trim();
    const trimmedName = displayName.trim();
    if (trimmedLocation === '') {
      setError('Location is required.');
      locationRef.current?.focus();
      return;
    }
    if (trimmedName === '') {
      setError('Display name is required.');
      displayNameRef.current?.focus();
      return;
    }
    setError(null);
    const payload = {
      kind: currentDraft.kind,
      mode: currentDraft.mode,
      location: trimmedLocation,
      display_name: trimmedName,
    };
    const result = onAddSource(payload);
    if (result instanceof Promise) {
      const accepted = await result;
      if (accepted === false) {
        locationRef.current?.focus();
        return;
      }
    } else if (result === false) {
      locationRef.current?.focus();
      return;
    }
    closeDraft();
  };

  const setMode = (currentDraft: PickerDraft, e: ChangeEvent<HTMLSelectElement>): void => {
    setDraft({ ...currentDraft, mode: e.target.value as WizardSourceMode });
    setLocation('');
    setError(null);
    setBrowseFallbackMessage(null);
  };

  const locationInvalid = error === 'Location is required.';
  const displayNameInvalid = error === 'Display name is required.';
  const visibleError = error ?? submitError;
  const hasError = visibleError !== null;

  return (
    <section className="wizard-panel" data-testid="wizard-add-step">
      <h2>Add inspiration sources</h2>
      <div className="wizard-add-buttons" data-testid="wizard-add-buttons">
        {KIND_DISPLAY_ORDER.map((kind) => (
          <button
            key={kind}
            type="button"
            className="wizard-button ghost"
            data-testid={`wizard-add-${kind}`}
            onClick={() => openDraft(kind)}
          >
            {KIND_STRATEGY[kind].label}
          </button>
        ))}
      </div>

      {draft === null ? null : (
        <div className="wizard-draft" data-testid="wizard-draft">
          <div className="wizard-draft-header">
            <strong>{draft.kind}</strong>
            <label className="wizard-field inline">
              <span className="wizard-field-label">mode</span>
              <select
                value={draft.mode}
                data-testid="wizard-draft-mode"
                onChange={(e) => setMode(draft, e)}
              >
                <option value="file">file</option>
                <option value="folder">folder</option>
                <option value="reference">reference</option>
              </select>
            </label>
          </div>
          {draft.mode === 'reference' ? (
            <label className="wizard-field">
              <span className="wizard-field-label">reference (artist / album / song name)</span>
              <input
                type="text"
                data-testid="wizard-draft-location"
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  setBrowseFallbackMessage(null);
                }}
                placeholder="e.g. Surgeon"
                ref={locationRef}
                aria-required="true"
                aria-invalid={locationInvalid}
                aria-describedby={locationInvalid ? DRAFT_ERROR_ID : undefined}
              />
            </label>
          ) : (
            <label className="wizard-field">
              <span className="wizard-field-label">path</span>
              <div className="wizard-field-row">
                <input
                  type="text"
                  data-testid="wizard-draft-location"
                  value={location}
                  onChange={(e) => {
                    setLocation(e.target.value);
                    setBrowseFallbackMessage(null);
                  }}
                  placeholder={draft.mode === 'folder' ? '/path/to/folder' : '/path/to/file'}
                  ref={locationRef}
                  aria-required="true"
                  aria-invalid={locationInvalid}
                  aria-describedby={locationInvalid ? DRAFT_ERROR_ID : undefined}
                />
                <button
                  type="button"
                  className="wizard-button ghost"
                  data-testid="wizard-draft-browse"
                  onClick={() => {
                    void handleBrowse(draft);
                  }}
                >
                  Browse…
                </button>
              </div>
            </label>
          )}
          {browseFallbackMessage === null ? null : (
            <div role="status" className="wizard-field-help">
              {browseFallbackMessage}
            </div>
          )}
          <label className="wizard-field">
            <span className="wizard-field-label">display name</span>
            <input
              type="text"
              data-testid="wizard-draft-display-name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="shown in the source list"
              ref={displayNameRef}
              aria-required="true"
              aria-invalid={displayNameInvalid}
              aria-describedby={displayNameInvalid ? DRAFT_ERROR_ID : undefined}
            />
          </label>
          {hasError && (
            <div id={DRAFT_ERROR_ID} role="alert" className="wizard-field-error">
              {visibleError}
            </div>
          )}
          <div className="wizard-draft-actions">
            <button
              type="button"
              className="wizard-button ghost"
              data-testid="wizard-draft-cancel"
              onClick={closeDraft}
            >
              Cancel
            </button>
            <button
              type="button"
              className="wizard-button primary"
              data-testid="wizard-draft-confirm"
              onClick={() => {
                void handleConfirm(draft);
              }}
            >
              Add source
            </button>
          </div>
        </div>
      )}

      <ul className="wizard-source-list" data-testid="wizard-source-list">
        {sources.length === 0 ? (
          <li className="wizard-source-empty" data-testid="wizard-source-empty">
            No sources yet — pick one above.
          </li>
        ) : (
          sources.map((source) => (
            <li
              key={source.source_id}
              className="wizard-source-row"
              data-testid={`wizard-source-${source.source_id}`}
            >
              <span className="wizard-source-kind">{source.kind}</span>
              <span className="wizard-source-name">{source.display_name}</span>
              <span className="wizard-source-location">{source.location}</span>
              <button
                type="button"
                className="wizard-button ghost danger"
                data-testid={`wizard-source-remove-${source.source_id}`}
                onClick={() => onRemoveSource(source.source_id)}
              >
                Remove
              </button>
            </li>
          ))
        )}
      </ul>

      <div className="wizard-actions">
        <button
          type="button"
          className="wizard-button ghost"
          data-testid="wizard-back"
          onClick={onBack}
        >
          ← Back
        </button>
        <button
          type="button"
          className="wizard-button primary"
          data-testid="wizard-next"
          disabled={sources.length === 0}
          onClick={onNext}
        >
          Analyze →
        </button>
      </div>
    </section>
  );
}
