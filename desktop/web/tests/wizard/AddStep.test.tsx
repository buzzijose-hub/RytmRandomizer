/**
 * Tests for the AddStep — second wizard panel.
 *
 * The default dialog opener uses dynamic-import to fetch the Tauri plugin. We mock that
 * module per-test via `vi.mock(...)` and exercise both the "picked a path" and
 * "user cancelled" branches. We also exercise the failure branch by tearing down the
 * mock and letting `import` reject in jsdom.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

import {
  AddStep,
  __tauriDialogImporter,
  basenameOf,
  defaultOpenDialog,
} from '../../src/wizard/AddStep';
import type { InspirationSource } from '../../src/types/wizard_protocol';

const sourceA: InspirationSource = {
  source_id: 'src_A',
  kind: 'artist',
  mode: 'reference',
  location: 'Surgeon',
  display_name: 'Surgeon',
  added_at: '2026-05-24T10:00:00Z',
};

describe('AddStep — picker UI', () => {
  beforeEach(() => {
    vi.resetModules();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the kind buttons + empty source list initially', () => {
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-add-kit')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-add-sound')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-add-song')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-add-album')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-add-artist')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-source-empty')).toBeInTheDocument();
    // No draft visible until a kind is selected.
    expect(screen.queryByTestId('wizard-draft')).not.toBeInTheDocument();
    // Next is disabled with zero sources.
    expect(screen.getByTestId('wizard-next')).toBeDisabled();
  });

  it('opens a draft with reference mode when "+ artist" is clicked', () => {
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    expect(screen.getByTestId('wizard-draft')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-draft-mode')).toHaveValue('reference');
    expect(screen.queryByTestId('wizard-draft-browse')).not.toBeInTheDocument();
  });

  it('opens a draft with file mode when "+ kit" is clicked and shows the Browse button', () => {
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    expect(screen.getByTestId('wizard-draft-mode')).toHaveValue('file');
    expect(screen.getByTestId('wizard-draft-browse')).toBeInTheDocument();
  });

  it('opens a draft with folder mode when "+ album" is clicked', () => {
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-album'));
    expect(screen.getByTestId('wizard-draft-mode')).toHaveValue('folder');
  });

  it('confirm does not fire onAddSource until both required fields are non-empty', () => {
    // Cluster-3 a11y fix: confirm button is always enabled; the validate-on-submit
    // path short-circuits when either field is blank (see form_errors.test.tsx
    // for the ARIA assertions). Behaviour from the operator's standpoint is the
    // same — onAddSource only fires when both fields validate.
    const onAddSource = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    expect(onAddSource).not.toHaveBeenCalled();
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: 'Surgeon' },
    });
    // Display name still blank.
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    expect(onAddSource).not.toHaveBeenCalled();
    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: 'Surgeon' },
    });
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    expect(onAddSource).toHaveBeenCalledTimes(1);
  });

  it('calls onAddSource with the trimmed payload and closes the draft on confirm', () => {
    const onAddSource = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: '  Surgeon  ' },
    });
    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: '  Surgeon  ' },
    });
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));
    expect(onAddSource).toHaveBeenCalledWith({
      kind: 'artist',
      mode: 'reference',
      location: 'Surgeon',
      display_name: 'Surgeon',
    });
    // Draft closes after add.
    expect(screen.queryByTestId('wizard-draft')).not.toBeInTheDocument();
  });

  it('keeps the draft open when onAddSource synchronously rejects the payload', () => {
    const onAddSource = vi.fn(() => false);
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
        submitError="source path rejected by policy"
      />,
    );

    fireEvent.click(screen.getByTestId('wizard-add-song'));
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: 'C:\\Users\\Jose Buzzi\\Downloads\\The Bells.wav' },
    });
    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: 'The Bells' },
    });
    fireEvent.click(screen.getByTestId('wizard-draft-confirm'));

    expect(onAddSource).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('wizard-draft')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-draft-location')).toHaveFocus();
    expect(screen.getByRole('alert')).toHaveTextContent(
      'source path rejected by policy',
    );
  });

  it('cancel button closes the draft without firing onAddSource', () => {
    const onAddSource = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={onAddSource}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    fireEvent.click(screen.getByTestId('wizard-draft-cancel'));
    expect(screen.queryByTestId('wizard-draft')).not.toBeInTheDocument();
    expect(onAddSource).not.toHaveBeenCalled();
  });

  it('switching the mode select clears the location input', () => {
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    fireEvent.change(screen.getByTestId('wizard-draft-location'), {
      target: { value: '/some/path' },
    });
    fireEvent.change(screen.getByTestId('wizard-draft-mode'), {
      target: { value: 'reference' },
    });
    expect(screen.getByTestId('wizard-draft-location')).toHaveValue('');
  });
});

describe('AddStep — dialog opener (injected for determinism)', () => {
  it('Browse button populates location and infers display name from path tail (forward slashes)', async () => {
    const openDialog = vi.fn().mockResolvedValue('/Users/me/kits/buzzi-2024.syx');
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
        openDialog={openDialog}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-draft-browse'));
    });
    expect(openDialog).toHaveBeenCalledWith('file');
    expect(screen.getByTestId('wizard-draft-location')).toHaveValue(
      '/Users/me/kits/buzzi-2024.syx',
    );
    expect(screen.getByTestId('wizard-draft-display-name')).toHaveValue('buzzi-2024.syx');
  });

  it('Browse button forwards "folder" mode to the opener when the kind defaults to folder', async () => {
    const openDialog = vi.fn().mockResolvedValue('/Users/me/albums/album-1');
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
        openDialog={openDialog}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-album'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-draft-browse'));
    });
    expect(openDialog).toHaveBeenCalledWith('folder');
    expect(screen.getByTestId('wizard-draft-location')).toHaveValue('/Users/me/albums/album-1');
  });

  it('Browse button leaves the display name alone when user already typed one', async () => {
    const openDialog = vi.fn().mockResolvedValue('C:\\kits\\name.syx');
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
        openDialog={openDialog}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    // Pre-fill the display name.
    fireEvent.change(screen.getByTestId('wizard-draft-display-name'), {
      target: { value: 'my-kit' },
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-draft-browse'));
    });
    expect(screen.getByTestId('wizard-draft-display-name')).toHaveValue('my-kit');
    // Location updates even though display name does not.
    expect(screen.getByTestId('wizard-draft-location')).toHaveValue('C:\\kits\\name.syx');
  });

  it('Browse button does nothing when the picker resolves to null (user cancelled)', async () => {
    const openDialog = vi.fn().mockResolvedValue(null);
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
        openDialog={openDialog}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-draft-browse'));
    });
    expect(screen.getByTestId('wizard-draft-location')).toHaveValue('');
  });

  it('Browse button is a no-op when the draft is in reference mode (guard branch)', async () => {
    const openDialog = vi.fn();
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
        openDialog={openDialog}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-artist'));
    // No browse button visible in reference mode — verify it's gone.
    expect(screen.queryByTestId('wizard-draft-browse')).not.toBeInTheDocument();
    expect(openDialog).not.toHaveBeenCalled();
  });

  it('default dialog opener (no injection) shows a paste-path fallback when the Tauri plugin is unavailable', async () => {
    // No injection: production path runs the dynamic import, which throws in jsdom.
    render(
      <AddStep
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-add-kit'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('wizard-draft-browse'));
    });
    // Plugin import fails → location stays empty.
    expect(screen.getByTestId('wizard-draft-location')).toHaveValue('');
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Browse is unavailable in this shell. Paste the full path instead.',
    );
  });
});

describe('basenameOf', () => {
  it('extracts the trailing segment from a forward-slash path', () => {
    expect(basenameOf('/a/b/c.syx')).toBe('c.syx');
  });

  it('extracts the trailing segment from a backslash path', () => {
    expect(basenameOf('C:\\\\kits\\\\d.syx')).toBe('d.syx');
  });

  it('returns the path verbatim when there is no separator', () => {
    expect(basenameOf('just-a-name')).toBe('just-a-name');
  });

  it('strips a single trailing slash before extracting (e.g. "/a/b/" → "b")', () => {
    expect(basenameOf('/a/b/')).toBe('b');
  });

  it('falls back to the original path when the input is only separators', () => {
    expect(basenameOf('///')).toBe('///');
  });

  it('returns the empty string when the input is the empty string', () => {
    expect(basenameOf('')).toBe('');
  });
});

describe('defaultOpenDialog — stubbed Tauri importer', () => {
  const originalImporter = __tauriDialogImporter.import;
  afterEach(() => {
    __tauriDialogImporter.import = originalImporter;
  });

  it('returns the picked path when the plugin returns a string', async () => {
    __tauriDialogImporter.import = vi
      .fn()
      .mockResolvedValue({ open: vi.fn().mockResolvedValue('/a/b.syx') });
    expect(await defaultOpenDialog('file')).toBe('/a/b.syx');
  });

  it('returns the first entry when the plugin returns an array', async () => {
    __tauriDialogImporter.import = vi
      .fn()
      .mockResolvedValue({ open: vi.fn().mockResolvedValue(['/a/b.syx', '/a/c.syx']) });
    expect(await defaultOpenDialog('file')).toBe('/a/b.syx');
  });

  it('returns null when the plugin returns null (user cancelled)', async () => {
    __tauriDialogImporter.import = vi
      .fn()
      .mockResolvedValue({ open: vi.fn().mockResolvedValue(null) });
    expect(await defaultOpenDialog('file')).toBeNull();
  });

  it('returns null when the plugin returns an empty array (array[0] fallback)', async () => {
    __tauriDialogImporter.import = vi
      .fn()
      .mockResolvedValue({ open: vi.fn().mockResolvedValue([]) });
    expect(await defaultOpenDialog('folder')).toBeNull();
  });

  it('returns null when the dynamic import itself rejects', async () => {
    __tauriDialogImporter.import = vi.fn().mockRejectedValue(new Error('no plugin'));
    expect(await defaultOpenDialog('folder')).toBeNull();
  });

  it('passes directory:true when mode is folder', async () => {
    const open = vi.fn().mockResolvedValue('/a');
    __tauriDialogImporter.import = vi.fn().mockResolvedValue({ open });
    await defaultOpenDialog('folder');
    expect(open).toHaveBeenCalledWith({ directory: true, multiple: false });
  });
});

describe('AddStep — sources list + actions', () => {
  it('renders rows for each source with a Remove button', () => {
    const onRemoveSource = vi.fn();
    render(
      <AddStep
        sources={[sourceA]}
        onAddSource={vi.fn()}
        onRemoveSource={onRemoveSource}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId(`wizard-source-${sourceA.source_id}`)).toBeInTheDocument();
    fireEvent.click(screen.getByTestId(`wizard-source-remove-${sourceA.source_id}`));
    expect(onRemoveSource).toHaveBeenCalledWith(sourceA.source_id);
  });

  it('Next becomes enabled once at least one source is present', () => {
    render(
      <AddStep
        sources={[sourceA]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={vi.fn()}
        onNext={vi.fn()}
      />,
    );
    expect(screen.getByTestId('wizard-next')).toBeEnabled();
  });

  it('Back and Next fire their handlers', () => {
    const onBack = vi.fn();
    const onNext = vi.fn();
    render(
      <AddStep
        sources={[sourceA]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onBack={onBack}
        onNext={onNext}
      />,
    );
    fireEvent.click(screen.getByTestId('wizard-back'));
    fireEvent.click(screen.getByTestId('wizard-next'));
    expect(onBack).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
  });
});
