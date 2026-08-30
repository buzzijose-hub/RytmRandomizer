import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { KitCapturePanel } from '../../src/cockpit/KitCapturePanel';
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID } from '../../src/cockpit/devices';
import { useCockpitStore } from '../../src/state';
import type { CommandAck, KitCaptureResult } from '../../src/ws/protocol';

import { FakeCockpitClient, sessionLive, sessionMock } from './_fixtures';

function captureResult(deviceId: typeof RYTM_DEVICE_ID | typeof ANALOG_FOUR_DEVICE_ID): KitCaptureResult {
  const isRytm = deviceId === RYTM_DEVICE_ID;
  const count = isRytm ? 12 : 4;
  return {
    device_id: deviceId,
    kit_name: isRytm ? 'LIVE RYTM KIT' : 'LIVE A4 KIT',
    slot: isRytm ? 3 : null,
    fingerprint: isRytm ? '0123456789abcdef' : 'fedcba9876543210',
    frame_bytes: isRytm ? 3001 : 2771,
    captured_at: '2026-08-26T12:00:00+00:00',
    snapshot_layout: 'saved_kit',
    parameter_readiness: isRytm
      ? 'rytm_anchor_ready'
      : 'exact_kit_anchor_offsets_candidate',
    round_trip_verified: true,
    input_only: true,
    sent_midi: false,
    layout_items: Array.from({ length: count }, (_, index) => ({
      index: index + 1,
      label: isRytm ? `Machine ${index + 1}` : `T${index + 1}`,
      status: isRytm ? 'mutation_ready' : 'captured_mapping_pending',
      detail: isRytm ? 'promoted machine fact' : 'semantic parameter offsets pending mapping',
    })),
  };
}

describe('KitCapturePanel', () => {
  beforeEach(() => {
    act(() => useCockpitStore.getState().reset());
  });

  afterEach(() => {
    act(() => useCockpitStore.getState().reset());
  });

  it('keeps input receive visibly locked in the passive preview', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({
      request_id: 'list-inputs',
      ok: true,
      capture_enabled: false,
      capture_device_id: RYTM_DEVICE_ID,
      capture_inputs: [],
    });
    act(() => useCockpitStore.getState().setSessionStatus(sessionMock));

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    expect(await screen.findByTestId('capture-locked-message')).toHaveTextContent(
      'Hardware receive is locked',
    );
    expect(screen.getByTestId('capture-current-kit-start')).toBeDisabled();
    expect(fake.sent).toEqual([{ type: 'list_capture_inputs', device_id: RYTM_DEVICE_ID }]);
  });

  it('prepares one A4 input, receives the kit, and lays out four truthful tracks', async () => {
    const fake = new FakeCockpitClient();
    const capture = captureResult(ANALOG_FOUR_DEVICE_ID);
    fake.ackQueue.push(
      {
        request_id: 'list-inputs',
        ok: true,
        capture_enabled: true,
        capture_device_id: ANALOG_FOUR_DEVICE_ID,
        capture_inputs: ['Analog Four MIDI In'],
      },
      { request_id: 'capture-kit', ok: true, kit_capture: capture },
    );
    act(() => useCockpitStore.getState().setSessionStatus(sessionLive));

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={ANALOG_FOUR_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    expect(await screen.findByText('Analog Four MIDI In')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('capture-current-kit-start'));

    expect(await screen.findByText('LIVE A4 KIT')).toBeInTheDocument();
    expect(screen.getByTestId('captured-kit-layout')).toHaveTextContent('fedcba9876543210');
    expect(screen.getAllByText('Mapping pending')).toHaveLength(4);
    expect(screen.getByText(/Unverified semantic offsets stay parked/)).toBeInTheDocument();
    expect(fake.sent[1]).toEqual({
      type: 'capture_current_kit',
      device_id: ANALOG_FOUR_DEVICE_ID,
      input_port: 'Analog Four MIDI In',
    });
    expect(fake.sent.filter((message) => message.type === 'list_capture_inputs')).toHaveLength(1);
  });

  it('renders all 12 Rytm pad rows from an already captured anchor', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({
      request_id: 'list-inputs',
      ok: true,
      capture_enabled: true,
      capture_device_id: RYTM_DEVICE_ID,
      capture_inputs: ['Analog Rytm MIDI In'],
    });
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setKitCaptures([captureResult(RYTM_DEVICE_ID)]);
    });

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    await waitFor(() => expect(screen.getAllByText('Mutation ready')).toHaveLength(12));
    expect(screen.getByTestId('captured-kit-layout')).toHaveTextContent('LIVE RYTM KIT');
    expect(screen.getByText(/12-pad kit anchor decoded/)).toBeInTheDocument();
  });

  it('shows a safe error when the input scan is rejected', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'scan-rejected', ok: false, error: 'closed' });

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    expect(await screen.findByText(/input scan was rejected/)).toBeInTheDocument();
  });

  it('shows a safe error when scanning the input API fails', async () => {
    const fake = new FakeCockpitClient();
    fake.nextRejection = new Error('MIDI provider unavailable');

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    expect(await screen.findByText(/Could not scan MIDI inputs/)).toBeInTheDocument();
  });

  it('does not update an unmounted panel after a late successful scan', async () => {
    const fake = new FakeCockpitClient();
    const client = fake.asClient();
    let resolveScan: (ack: CommandAck) => void = () => undefined;
    vi.spyOn(client, 'send').mockImplementationOnce(
      () => new Promise((resolve) => { resolveScan = resolve; }),
    );

    const { unmount } = render(
      <CockpitClientProvider client={client}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );
    unmount();

    await act(async () => {
      resolveScan({ request_id: 'late-scan', ok: true, capture_inputs: ['Late Input'] });
      await Promise.resolve();
    });
  });

  it('does not update an unmounted panel after a late failed scan', async () => {
    const fake = new FakeCockpitClient();
    const client = fake.asClient();
    let rejectScan: (reason: unknown) => void = () => undefined;
    vi.spyOn(client, 'send').mockImplementationOnce(
      () => new Promise((_resolve, reject) => { rejectScan = reject; }),
    );

    const { unmount } = render(
      <CockpitClientProvider client={client}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );
    unmount();

    await act(async () => {
      rejectScan(new Error('late failure'));
      await Promise.resolve();
    });
  });

  it('uses safe defaults when the scan ack omits optional capture fields', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'minimal-scan', ok: true });

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    expect(await screen.findByText('No input detected')).toBeInTheDocument();
    expect(screen.getByTestId('capture-locked-message')).toBeInTheDocument();
  });

  it('keeps the prior anchor when a capture ack has no verified kit', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push(
      {
        request_id: 'scan',
        ok: true,
        capture_enabled: true,
        capture_inputs: ['Input One', 'Input Two'],
      },
      { request_id: 'empty-capture', ok: true },
    );
    act(() => useCockpitStore.getState().setSessionStatus(sessionLive));

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    const select = await screen.findByLabelText('MIDI input');
    fireEvent.change(select, { target: { value: 'Input Two' } });
    fireEvent.click(screen.getByTestId('capture-current-kit-start'));

    expect(await screen.findByText(/No valid current-KIT frame/)).toBeInTheDocument();
    expect(fake.sent[1]).toEqual({
      type: 'capture_current_kit',
      device_id: RYTM_DEVICE_ID,
      input_port: 'Input Two',
    });
  });

  it('handles both a rejected capture ack and a transport timeout', async () => {
    const fake = new FakeCockpitClient();
    const client = fake.asClient();
    vi.spyOn(client, 'send')
      .mockResolvedValueOnce({
        request_id: 'scan',
        ok: true,
        capture_enabled: true,
        capture_inputs: ['Rytm Input'],
      })
      .mockResolvedValueOnce({ request_id: 'capture-rejected', ok: false, error: 'wrong frame' })
      .mockRejectedValueOnce(new Error('timeout'));
    act(() => useCockpitStore.getState().setSessionStatus(sessionLive));

    render(
      <CockpitClientProvider client={client}>
        <KitCapturePanel deviceId={RYTM_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    await screen.findByText('Rytm Input');
    fireEvent.click(screen.getByTestId('capture-current-kit-start'));
    expect(await screen.findByText(/No valid current-KIT frame/)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('capture-current-kit-start'));
    expect(await screen.findByText(/Capture timed out/)).toBeInTheDocument();
  });

  it('renders unnamed and unverified metadata without claiming readiness', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({
      request_id: 'scan',
      ok: true,
      capture_enabled: true,
      capture_inputs: ['A4 Input'],
    });
    const capture = captureResult(ANALOG_FOUR_DEVICE_ID);
    capture.kit_name = '';
    capture.round_trip_verified = false;
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setKitCaptures([capture]);
    });

    render(
      <CockpitClientProvider client={fake.asClient()}>
        <KitCapturePanel deviceId={ANALOG_FOUR_DEVICE_ID} onClose={() => undefined} />
      </CockpitClientProvider>,
    );

    expect(await screen.findByText('Unnamed Kit')).toBeInTheDocument();
    expect(screen.getByText('Blocked')).toBeInTheDocument();
  });
});
