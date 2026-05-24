/**
 * AddStep — second wizard panel.
 *
 *   + kit · + sound · + song · + album · + artist
 *
 *   For file / folder kinds we open the Tauri dialog plugin via dynamic import. The plugin
 *   is injected at runtime by the Tauri shell; in browser / test environments the import
 *   fails and we fall back to a plain text input. Reference picker is ALWAYS a text input
 *   (matches the spec — references are textual names, no file backing).
 *
 *   The accumulated source list renders below with a remove button per row. The "Analyze"
 *   action below is disabled until at least one source is added.
 */

import { useState, type ChangeEvent } from 'react';

import type {
  InspirationSource,
  WizardSourceKind,
  WizardSourceMode,
} from '../types/wizard_protocol';
import { KIND_DISPLAY_ORDER, KIND_STRATEGY } from './kinds';

export interface AddStepProps {
  sources: ReadonlyArray<InspirationSource>;
  onAddSource: (payload: {
    kind: WizardSourceKind;
    mode: WizardSourceMode;
    location: string;
    display_name: string;
  }) => void;
  onRemoveSource: (sourceId: string) => void;
  onBack: () => void;
  onNext: () => void;
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
 * Default dialog opener — dynamic-imports the Tauri plugin. When the plugin isn't
 * available (test or browser without Tauri shell) returns null so the caller falls back
 * to the manual text input.
 */
interface TauriDialogModule {
  open: (opts: {
    directory?: boolean;
    multiple?: boolean;
  }) => Promise<string | string[] | null>;
}

/**
 * Module specifier kept in a variable + tagged with `/* @vite-ignore *\/` so neither
 * Vite nor TypeScript's static analyser tries to resolve `@tauri-apps/plugin-dialog`
 * at build time. The Tauri shell injects the plugin into the runtime module graph;
 * everywhere else (jsdom / plain browser) the dynamic import throws and we return
 * null so the AddStep falls back to the manual text input.
 */
const TAURI_DIALOG_MODULE = '@tauri-apps/plugin-dialog';

/**
 * Indirected dynamic-import. Exported only for tests so they can stub the import.
 */
export const __tauriDialogImporter: { import: () => Promise<TauriDialogModule> } = {
  import: () => import(/* @vite-ignore */ TAURI_DIALOG_MODULE) as Promise<TauriDialogModule>,
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
    if (result === null) return null;
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
  openDialog,
}: AddStepProps): JSX.Element {
  const [draft, setDraft] = useState<PickerDraft | null>(null);
  const [location, setLocation] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');
  const opener = openDialog ?? defaultOpenDialog;

  const openDraft = (kind: WizardSourceKind): void => {
    const mode = KIND_STRATEGY[kind].defaultMode;
    setDraft({ kind, mode });
    setLocation('');
    setDisplayName('');
  };

  const closeDraft = (): void => {
    setDraft(null);
    setLocation('');
    setDisplayName('');
  };

  const handleBrowse = async (currentDraft: PickerDraft): Promise<void> => {
    // `currentDraft.mode` is always 'file' or 'folder' here: the Browse button only
    // renders in those branches of the draft form. Narrow accordingly.
    const dialogMode: 'file' | 'folder' =
      currentDraft.mode === 'folder' ? 'folder' : 'file';
    const picked = await opener(dialogMode);
    if (picked === null) return;
    setLocation(picked);
    if (displayName === '') {
      setDisplayName(basenameOf(picked));
    }
  };

  const handleConfirm = (currentDraft: PickerDraft): void => {
    const trimmedLocation = location.trim();
    const trimmedName = displayName.trim();
    onAddSource({
      kind: currentDraft.kind,
      mode: currentDraft.mode,
      location: trimmedLocation,
      display_name: trimmedName,
    });
    closeDraft();
  };

  const setMode = (currentDraft: PickerDraft, e: ChangeEvent<HTMLSelectElement>): void => {
    setDraft({ ...currentDraft, mode: e.target.value as WizardSourceMode });
    setLocation('');
  };

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
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Surgeon"
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
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder={draft.mode === 'folder' ? '/path/to/folder' : '/path/to/file'}
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
          <label className="wizard-field">
            <span className="wizard-field-label">display name</span>
            <input
              type="text"
              data-testid="wizard-draft-display-name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="shown in the source list"
            />
          </label>
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
              disabled={location.trim() === '' || displayName.trim() === ''}
              onClick={() => handleConfirm(draft)}
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
