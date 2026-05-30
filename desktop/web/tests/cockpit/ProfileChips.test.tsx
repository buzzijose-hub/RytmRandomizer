/**
 * Tests for ProfileChips — chip list, active card, export button.
 */

import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { ProfileChips } from '../../src/cockpit/ProfileChips';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, availableProfiles, profile } from './_fixtures';

const originalCreateObjectURL = URL.createObjectURL;
const originalRevokeObjectURL = URL.revokeObjectURL;

function renderWith(
  available: ReadonlyArray<{ profile_id: string; name: string; kind: 'scene' | 'user' }> = availableProfiles,
): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <ProfileChips available={available} />
    </CockpitClientProvider>,
  );
  return fake;
}

function setActiveProfile(): void {
  act(() => {
    useCockpitStore.getState().setProfile(profile);
  });
}

function stubDownloadApis(url = 'blob:profile-model'): {
  createObjectURL: ReturnType<typeof vi.fn>;
  revokeObjectURL: ReturnType<typeof vi.fn>;
} {
  const createObjectURL = vi.fn(() => url);
  const revokeObjectURL = vi.fn();
  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true,
    value: createObjectURL,
  });
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true,
    value: revokeObjectURL,
  });
  return { createObjectURL, revokeObjectURL };
}

describe('ProfileChips', () => {
  beforeEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: originalCreateObjectURL,
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: originalRevokeObjectURL,
    });
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('renders an empty-state message when available is empty', () => {
    renderWith([]);
    expect(screen.getByText('No profiles available')).toBeInTheDocument();
  });

  it('renders one chip per available profile', () => {
    renderWith();
    for (const p of availableProfiles) {
      expect(screen.getByTestId(`profile-chip-${p.profile_id}`)).toBeInTheDocument();
    }
  });

  it('highlights the active chip when its id matches the store profile', () => {
    setActiveProfile();
    renderWith();
    const activeChip = screen.getByTestId(`profile-chip-${profile.profile_id}`);
    expect(activeChip.className).toBe('profile-chip active');
    expect(activeChip).toHaveTextContent('★ buzzi');
  });

  it('does not render the active card when no profile is selected', () => {
    renderWith();
    expect(screen.queryByTestId('profile-active-card')).not.toBeInTheDocument();
  });

  it('renders the active card with name + traits + meta when a profile is selected', () => {
    setActiveProfile();
    renderWith();
    const card = screen.getByTestId('profile-active-card');
    expect(card).toHaveTextContent('★ buzzi');
    expect(card).toHaveTextContent('model 1.2.0');
    expect(card).toHaveTextContent('rolling_low_end');
    expect(card).toHaveTextContent('85%');
    expect(card).toHaveTextContent('metallic_tension');
    expect(card).toHaveTextContent('40%');
  });

  it('clicking a chip emits select_profile', () => {
    const fake = renderWith();
    fireEvent.click(screen.getByTestId('profile-chip-user-buzzi'));
    expect(fake.sent).toEqual([{ type: 'select_profile', profile_id: 'user-buzzi' }]);
  });

  it('clicking EXPORT MODEL emits export_profile_model with target=binary while pending', () => {
    setActiveProfile();
    const fake = renderWith();
    fake.hang = true;

    fireEvent.click(screen.getByTestId('profile-export-button'));

    expect(fake.sent).toEqual([
      {
        type: 'export_profile_model',
        profile_id: profile.profile_id,
        target: 'binary',
      },
    ]);
    expect(screen.getByTestId('profile-export-button')).toBeDisabled();
    expect(screen.getByTestId('profile-export-status')).toHaveTextContent('Preparing export...');
  });

  it('shows a visible export success message when the sidecar returns model bytes', async () => {
    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-ok',
      ok: true,
      model_bytes_b64: 'cnltcA==',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    expect(await screen.findByText(/Export ready/)).toBeInTheDocument();
    expect(screen.getByText(/4 bytes/)).toBeInTheDocument();
  });

  it('reports ready bytes without a download line when blob APIs are unavailable', async () => {
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: undefined,
    });
    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-no-blob-api',
      ok: true,
      model_bytes_b64: 'YWI=',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    const status = await screen.findByTestId('profile-export-status');
    expect(status).toHaveTextContent('Export ready (2 bytes)');
    expect(status).not.toHaveTextContent('Exported');
  });

  it('reports the byte count for unpadded base64 export payloads', async () => {
    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-unpadded',
      ok: true,
      model_bytes_b64: 'YWJj',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    expect(await screen.findByText(/Export ready/)).toBeInTheDocument();
    expect(screen.getByText(/3 bytes/)).toBeInTheDocument();
  });

  it('reports zero bytes for whitespace-only base64 export payloads', async () => {
    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-whitespace',
      ok: true,
      model_bytes_b64: ' \n\t ',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    expect(await screen.findByText(/Export ready/)).toBeInTheDocument();
    expect(screen.getByText(/0 bytes/)).toBeInTheDocument();
  });

  it('downloads a binary profile export when browser blob APIs are available', async () => {
    const { createObjectURL, revokeObjectURL } = stubDownloadApis();
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);

    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-download',
      ok: true,
      model_bytes: 'YWI=',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    await screen.findByTestId('profile-export-status');
    expect(screen.getByTestId('profile-export-status')).toHaveTextContent('Export ready (2 bytes)');
    expect(screen.getByTestId('profile-export-status')).toHaveTextContent(
      'Exported user-buzzi-v1.2.0.rymp',
    );
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    await waitFor(() => {
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:profile-model');
    });
    expect(clickSpy).toHaveBeenCalledTimes(1);
    const clickedAnchor = clickSpy.mock.contexts[0] as HTMLAnchorElement;
    expect(clickedAnchor.download).toBe('user-buzzi-v1.2.0.rymp');
    expect(clickedAnchor.href).toBe('blob:profile-model');
  });

  it('uses legacy model_bytes and safe fallback filename parts when exporting', async () => {
    const { createObjectURL, revokeObjectURL } = stubDownloadApis('blob:fallback-model');
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);

    act(() => {
      useCockpitStore.getState().setProfile({
        ...profile,
        profile_id: '***',
        model_version: '###',
      });
    });
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-legacy-ok',
      ok: true,
      model_bytes: 'UllNUHRlc3Q=',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    await screen.findByTestId('profile-export-status');
    expect(screen.getByTestId('profile-export-status')).toHaveTextContent(
      'Exported profile-vprofile.rymp',
    );
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    await waitFor(() => {
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:fallback-model');
    });
    const clickedAnchor = clickSpy.mock.contexts[0] as HTMLAnchorElement;
    expect(clickedAnchor.download).toBe('profile-vprofile.rymp');
  });

  it('shows the sidecar rejection reason when export fails', async () => {
    const { createObjectURL } = stubDownloadApis();
    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({ request_id: 'export-rejected', ok: false });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    const status = await screen.findByTestId('profile-export-status');
    expect(status).toHaveAttribute('role', 'alert');
    expect(status).toHaveTextContent('Export rejected by sidecar');
    expect(createObjectURL).not.toHaveBeenCalled();
    expect(screen.getByTestId('profile-export-button')).not.toBeDisabled();
  });

  it('reports missing export bytes without downloading', async () => {
    const { createObjectURL } = stubDownloadApis();
    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-empty',
      ok: true,
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    const status = await screen.findByTestId('profile-export-status');
    expect(status).toHaveAttribute('role', 'alert');
    expect(status).toHaveTextContent('Export failed: Export response did not include model bytes');
    expect(createObjectURL).not.toHaveBeenCalled();
  });

  it('reports empty export bytes without downloading', async () => {
    const { createObjectURL } = stubDownloadApis();
    setActiveProfile();
    const fake = renderWith();
    fake.ackQueue.push({
      request_id: 'export-empty-string',
      ok: true,
      model_bytes_b64: '',
    });

    fireEvent.click(screen.getByTestId('profile-export-button'));

    const status = await screen.findByTestId('profile-export-status');
    expect(status).toHaveAttribute('role', 'alert');
    expect(status).toHaveTextContent('Export failed: Export response did not include model bytes');
    expect(createObjectURL).not.toHaveBeenCalled();
  });

  it('reports non-error export rejections', async () => {
    setActiveProfile();
    const fake = renderWith();
    fake.nextRejection = 'transport closed' as unknown as Error;

    fireEvent.click(screen.getByTestId('profile-export-button'));

    const status = await screen.findByTestId('profile-export-status');
    expect(status).toHaveAttribute('role', 'alert');
    expect(status).toHaveTextContent('Export failed: transport closed');
  });
});
