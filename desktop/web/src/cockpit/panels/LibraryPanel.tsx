/**
 * LibraryPanel — browse / search / tag captured kit records and trigger the
 * captures importer. The record table renders through the generic
 * PanelRenderer; `library_changed` events keep the slice live after any
 * mutation. The importer only ever reads the sidecar's boot-time-configured
 * captures directory (no wire-supplied paths).
 */

import { useState, type FormEvent } from 'react';

import { useCockpitStore } from '../../state';
import type { CommandAck } from '../../ws/protocol';
import { useCockpitClient } from '../context';

import { libraryPanelSpec, splitTags } from './libraryPanelSpec';
import { PanelRenderer } from './PanelRenderer';

export function LibraryPanel(): JSX.Element {
  const client = useCockpitClient();
  const records = useCockpitStore((s) => s.libraryRecords);
  const setLibraryRecords = useCockpitStore((s) => s.setLibraryRecords);
  const [query, setQuery] = useState('');
  const [tagRecordId, setTagRecordId] = useState('');
  const [tagsDraft, setTagsDraft] = useState('');
  const [note, setNote] = useState<string | null>(null);

  const applyRecords = (ack: CommandAck, okNote: string): void => {
    if (ack.ok && ack.library_records !== undefined && ack.library_records !== null) {
      setLibraryRecords(ack.library_records);
      setNote(okNote);
    } else {
      setNote(ack.message ?? 'library request rejected');
    }
  };

  const loadAll = (): void => {
    client
      .send({ type: 'library_list' })
      .then((ack) => applyRecords(ack, 'library loaded'))
      .catch(() => setNote('library request failed to send'));
  };

  const search = (ev: FormEvent): void => {
    ev.preventDefault();
    client
      .send({ type: 'library_search', query })
      .then((ack) => applyRecords(ack, `search complete: ${query}`))
      .catch(() => setNote('library request failed to send'));
  };

  const importCaptures = (): void => {
    client
      .send({ type: 'library_import_captures' })
      .then((ack) => {
        if (ack.ok && ack.library_import !== undefined && ack.library_import !== null) {
          setNote(
            `imported ${ack.library_import.imported_count}, ` +
              `skipped ${ack.library_import.skipped_existing}, ` +
              `failed ${ack.library_import.failed_files.length}`,
          );
        } else {
          setNote(ack.message ?? 'import rejected');
        }
      })
      .catch(() => setNote('library request failed to send'));
  };

  const saveTags = (ev: FormEvent): void => {
    ev.preventDefault();
    client
      .send({ type: 'library_tag', record_id: tagRecordId, tags: splitTags(tagsDraft) })
      .then((ack) => {
        if (ack.ok) {
          setNote(`tags saved for ${tagRecordId}`);
        } else {
          setNote(ack.message ?? 'tag update rejected');
        }
      })
      .catch(() => setNote('library request failed to send'));
  };

  return (
    <div className="cockpit-panel-stack" data-testid="library-panel">
      <div className="cockpit-panel-controls">
        <button type="button" onClick={loadAll} data-testid="library-load">
          Load library
        </button>
        <button type="button" onClick={importCaptures} data-testid="library-import">
          Import captures
        </button>
        <form onSubmit={search} className="cockpit-panel-inline-form">
          <label>
            Search
            <input
              value={query}
              onChange={(ev) => setQuery(ev.target.value)}
              data-testid="library-search-input"
            />
          </label>
          <button type="submit" data-testid="library-search-submit">
            Search records
          </button>
        </form>
        <form onSubmit={saveTags} className="cockpit-panel-inline-form">
          <label>
            Record
            <select
              value={tagRecordId}
              onChange={(ev) => setTagRecordId(ev.target.value)}
              data-testid="library-tag-record"
            >
              <option value="">select record</option>
              {(records ?? []).map((record) => (
                <option key={record.record_id} value={record.record_id}>
                  {record.kit_name} ({record.record_id})
                </option>
              ))}
            </select>
          </label>
          <label>
            Tags
            <input
              value={tagsDraft}
              onChange={(ev) => setTagsDraft(ev.target.value)}
              data-testid="library-tags-input"
            />
          </label>
          <button type="submit" disabled={tagRecordId === ''} data-testid="library-tags-save">
            Save tags
          </button>
        </form>
        {note !== null && <span className="cockpit-panel-note">{note}</span>}
      </div>
      <PanelRenderer spec={libraryPanelSpec(records)} />
    </div>
  );
}
