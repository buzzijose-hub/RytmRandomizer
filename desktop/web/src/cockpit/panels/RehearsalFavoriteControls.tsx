import { useEffect, useRef, useState, type FormEvent } from 'react';

import { useCockpitStore } from '../../state';
import type { LibraryRecord } from '../../ws/protocol';
import { useCockpitClient } from '../context';
import './parameterScope.css';

/** Local retention uses LibraryStore. Stored rehearsal metadata grants no UI authority. */
export function RehearsalFavoriteControls({ records }: { records: LibraryRecord[] | null }): JSX.Element {
  const client = useCockpitClient();
  const candidate = useCockpitStore((state) => state.previewCandidate);
  const connected = useCockpitStore((state) => state.connectionStatus === 'connected');
  const [name, setName] = useState('');
  const [recordId, setRecordId] = useState('');
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const request = useRef(0);
  useEffect(() => () => { request.current += 1; }, []);
  const favorites = (records ?? []).filter((record) => record.record_kind === 'rehearsal_favorite');
  const selected = favorites.find((record) => record.record_id === recordId);

  const execute = async (recall: boolean): Promise<void> => {
    const serial = ++request.current;
    if (recall) useCockpitStore.getState().invalidateMutationContext(true);
    setBusy(true);
    setNote(null);
    setError(null);
    try {
      const ack = await client.send(recall
        ? { type: 'recall_rehearsal_favorite', record_id: recordId }
        : { type: 'retain_rehearsal_favorite', name: name.trim() });
      if (request.current !== serial) return;
      if (!ack.ok) throw new Error(ack.message ?? ack.error ?? 'Local favorite request refused.');
      if (ack.library_records !== undefined && ack.library_records !== null) {
        useCockpitStore.getState().setLibraryRecords(ack.library_records);
      }
      setNote(recall ? 'Local favorite reopened. Fresh preparation required.' : 'Favorite retained locally. Hardware KIT unchanged.');
    } catch (failure) {
      if (request.current === serial) setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      if (request.current === serial) setBusy(false);
    }
  };

  const retain = (event: FormEvent): void => {
    event.preventDefault();
    if (candidate !== null && name.trim() !== '' && connected && !busy) void execute(false);
  };

  return (
    <section aria-label="Local rehearsal favorites" className="cockpit-panel-controls rehearsal-favorite-controls" data-testid="rehearsal-favorites">
      <h3>Local rehearsal favorites</h3>
      <p>Local retention only. Hardware SAVE and manual KIT reload are separate.</p>
      {candidate !== null && <p data-testid="favorite-candidate-summary">
        Source <code>{candidate.source_snapshot_id}</code>; candidate <code>{candidate.candidate_id}</code>;
        seed {candidate.seed}; depth {Math.round(candidate.depth * 100)}%.
      </p>}
      <form onSubmit={retain} className="cockpit-panel-inline-form">
        <label>Favorite name<input value={name} maxLength={64} disabled={busy}
          onChange={(event) => setName(event.currentTarget.value)} data-testid="favorite-name" /></label>
        <button type="submit" disabled={!connected || busy || candidate === null || name.trim() === ''} data-testid="favorite-retain">Retain local favorite</button>
      </form>
      <div className="cockpit-panel-inline-form">
        <label>Local favorite<select value={selected === undefined ? '' : recordId} disabled={busy}
          onChange={(event) => setRecordId(event.currentTarget.value)} data-testid="favorite-record">
          <option value="">Select a local favorite</option>
          {favorites.map((record) => <option key={record.record_id} value={record.record_id}>{record.kit_name} ({record.record_id})</option>)}
        </select></label>
        <button type="button" disabled={!connected || busy || selected === undefined}
          onClick={() => void execute(true)} data-testid="favorite-reopen">Reopen disarmed</button>
      </div>
      {note !== null && <p role="status">{note}</p>}
      {error !== null && <p role="alert">{error}</p>}
    </section>
  );
}
