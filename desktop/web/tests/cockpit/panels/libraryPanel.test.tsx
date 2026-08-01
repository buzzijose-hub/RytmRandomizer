/**
 * Library — pure spec selector branches + browse/search/tag/import
 * interactions and library_changed live updates.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/react';

import { LibraryPanel } from '../../../src/cockpit/panels/LibraryPanel';
import { libraryPanelSpec, splitTags } from '../../../src/cockpit/panels/libraryPanelSpec';
import { CockpitClientProvider } from '../../../src/cockpit/context';
import { useCockpitStore } from '../../../src/state';

import { FakeCockpitClient, libraryRecordA, libraryRecordB } from '../_fixtures';

describe('libraryPanelSpec (pure)', () => {
  it('renders the not-loaded placeholder for a null slice', () => {
    const spec = libraryPanelSpec(null);
    expect(spec.status_badges[0]).toMatchObject({ label: 'not loaded', tone: 'neutral' });
    expect(spec.sections[0]!.rows[0]).toContain('Library not loaded yet');
  });

  it('renders one table row per record with joined tags', () => {
    const spec = libraryPanelSpec([libraryRecordA, libraryRecordB]);
    expect(spec.status_badges[0]).toMatchObject({ label: '2 record(s)', tone: 'ok' });
    expect(spec.sections[0]!.table!.rows).toEqual([
      ['INDUSTRIAL KIT', 'analog_rytm_mk2', '2026-07-01T10:00:00+00:00', 'techno', 'abc123'],
      ['ACID BANK', 'analog_four_mk2', '2026-07-02T11:00:00+00:00', '', 'def456'],
    ]);
  });

  it('splitTags trims, drops empties, and handles the empty draft', () => {
    expect(splitTags('techno, rolling , ,percussive')).toEqual([
      'techno',
      'rolling',
      'percussive',
    ]);
    expect(splitTags('')).toEqual([]);
  });
});

describe('LibraryPanel (interactive)', () => {
  function renderPanel(fake: FakeCockpitClient): void {
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <LibraryPanel />
      </CockpitClientProvider>,
    );
  }

  beforeEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });
  afterEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('loads the record listing and re-renders live on library_changed updates', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({
      request_id: 'r1',
      ok: true,
      library_records: [libraryRecordA],
    });
    renderPanel(fake);

    fireEvent.click(screen.getByTestId('library-load'));
    expect(fake.sent).toEqual([{ type: 'library_list' }]);
    expect(await screen.findByText('library loaded')).toBeInTheDocument();

    const panel = screen.getByTestId('cockpit-panel-library');
    expect(within(panel).getByRole('cell', { name: 'INDUSTRIAL KIT' })).toBeInTheDocument();

    // A library_changed-style store update re-renders the browse table.
    act(() => {
      useCockpitStore.getState().setLibraryRecords([libraryRecordA, libraryRecordB]);
    });
    expect(within(panel).getByRole('cell', { name: 'ACID BANK' })).toBeInTheDocument();
  });

  it('searches records through the labelled form', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({
      request_id: 'r1',
      ok: true,
      library_records: [libraryRecordB],
    });
    renderPanel(fake);

    fireEvent.change(screen.getByTestId('library-search-input'), {
      target: { value: 'acid' },
    });
    fireEvent.click(screen.getByTestId('library-search-submit'));
    expect(fake.sent).toEqual([{ type: 'library_search', query: 'acid' }]);
    expect(await screen.findByText('search complete: acid')).toBeInTheDocument();
    expect(useCockpitStore.getState().libraryRecords).toEqual([libraryRecordB]);

    // Transport failure on search → catch branch.
    fake.nextRejection = new Error('socket not open');
    fireEvent.click(screen.getByTestId('library-search-submit'));
    expect(await screen.findByText('library request failed to send')).toBeInTheDocument();
  });

  it('surfaces rejected listing acks (message + fallback) and send failures', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: false, message: 'store unavailable' });
    renderPanel(fake);

    fireEvent.click(screen.getByTestId('library-load'));
    expect(await screen.findByText('store unavailable')).toBeInTheDocument();

    fake.ackQueue.push({ request_id: 'r2', ok: true });
    fireEvent.click(screen.getByTestId('library-load'));
    expect(await screen.findByText('library request rejected')).toBeInTheDocument();

    fake.nextRejection = new Error('socket not open');
    fireEvent.click(screen.getByTestId('library-load'));
    expect(await screen.findByText('library request failed to send')).toBeInTheDocument();
  });

  it('imports captures and reports the import counters and failures', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({
      request_id: 'r1',
      ok: true,
      library_import: {
        imported: [libraryRecordA],
        imported_count: 1,
        skipped_existing: 2,
        failed_files: ['junk.syx'],
      },
    });
    renderPanel(fake);

    fireEvent.click(screen.getByTestId('library-import'));
    expect(fake.sent).toEqual([{ type: 'library_import_captures' }]);
    expect(
      await screen.findByText('imported 1, skipped 2, failed 1'),
    ).toBeInTheDocument();

    fake.ackQueue.push({ request_id: 'r2', ok: false, message: 'captures dir missing' });
    fireEvent.click(screen.getByTestId('library-import'));
    expect(await screen.findByText('captures dir missing')).toBeInTheDocument();

    fake.ackQueue.push({ request_id: 'r3', ok: true });
    fireEvent.click(screen.getByTestId('library-import'));
    expect(await screen.findByText('import rejected')).toBeInTheDocument();

    fake.nextRejection = new Error('socket not open');
    fireEvent.click(screen.getByTestId('library-import'));
    expect(await screen.findByText('library request failed to send')).toBeInTheDocument();
  });

  it('tags a selected record with the cleaned tag list', async () => {
    act(() => {
      useCockpitStore.getState().setLibraryRecords([libraryRecordA, libraryRecordB]);
    });
    const fake = new FakeCockpitClient();
    renderPanel(fake);

    // Save is disabled until a record is selected.
    expect(screen.getByTestId('library-tags-save')).toBeDisabled();

    fireEvent.change(screen.getByTestId('library-tag-record'), {
      target: { value: 'abc123' },
    });
    fireEvent.change(screen.getByTestId('library-tags-input'), {
      target: { value: ' techno , rolling ' },
    });
    fireEvent.click(screen.getByTestId('library-tags-save'));
    expect(fake.sent).toEqual([
      { type: 'library_tag', record_id: 'abc123', tags: ['techno', 'rolling'] },
    ]);
    expect(await screen.findByText('tags saved for abc123')).toBeInTheDocument();
  });

  it('surfaces rejected tag acks (message + fallback) and send failures', async () => {
    act(() => {
      useCockpitStore.getState().setLibraryRecords([libraryRecordA]);
    });
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: false, message: 'unknown record' });
    renderPanel(fake);

    fireEvent.change(screen.getByTestId('library-tag-record'), {
      target: { value: 'abc123' },
    });
    fireEvent.click(screen.getByTestId('library-tags-save'));
    expect(await screen.findByText('unknown record')).toBeInTheDocument();

    fake.ackQueue.push({ request_id: 'r2', ok: false });
    fireEvent.click(screen.getByTestId('library-tags-save'));
    expect(await screen.findByText('tag update rejected')).toBeInTheDocument();

    fake.nextRejection = new Error('socket not open');
    fireEvent.click(screen.getByTestId('library-tags-save'));
    expect(await screen.findByText('library request failed to send')).toBeInTheDocument();
  });
});
