/**
 * Connection Doctor — pure checklist selector branches + the interactive
 * strip (refresh via COMMAND_DIAGNOSTICS, export-to-clipboard).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/react';

import { ConnectionDoctorPanel } from '../../../src/cockpit/panels/ConnectionDoctorPanel';
import { connectionDoctorPanelSpec } from '../../../src/cockpit/panels/connectionDoctorPanelSpec';
import { CockpitClientProvider } from '../../../src/cockpit/context';
import { useCockpitStore } from '../../../src/state';
import type { DiagnosticsPayload } from '../../../src/ws/protocol';

import {
  FakeCockpitClient,
  connectionListening,
  diagnosticsFaulty,
  diagnosticsHealthy,
} from '../_fixtures';

describe('connectionDoctorPanelSpec (pure)', () => {
  it('renders the not-run placeholder when diagnostics never ran', () => {
    const spec = connectionDoctorPanelSpec(null);
    expect(spec.status_badges[0]).toMatchObject({ label: 'not run', tone: 'neutral' });
    expect(spec.sections[0]!.rows[0]).toContain('No diagnostics captured yet');
  });

  it('renders all-pass checks for a healthy packet', () => {
    const spec = connectionDoctorPanelSpec(diagnosticsHealthy);
    expect(spec.status_badges[0]).toMatchObject({ label: 'listening', tone: 'ok' });
    const checklist = spec.sections[0]!.rows;
    expect(checklist).toHaveLength(6);
    for (const row of checklist) expect(row.startsWith('✓')).toBe(true);
    expect(checklist[4]).toContain('Analog Rytm MK2 IN');
    expect(spec.sections[1]!.rows).toEqual([
      'platform: darwin',
      diagnosticsHealthy.driver_hint,
    ]);
    expect(spec.sections[2]!.table!.rows).toEqual([]);
    expect(spec.sections[3]!.chips).toEqual(['none recorded']);
  });

  it('renders fail checks, journal rows, and error chips for a faulty packet', () => {
    const spec = connectionDoctorPanelSpec(diagnosticsFaulty);
    expect(spec.status_badges[0]).toMatchObject({ label: 'fault', tone: 'risk' });
    const checklist = spec.sections[0]!.rows;
    expect(checklist[0]!.startsWith('✓')).toBe(true);
    expect(checklist[1]).toContain(
      '✗ enumeration fault: cockpit.connection.enumeration_failed.oserror',
    );
    expect(checklist[2]).toContain('no MIDI inputs visible');
    expect(checklist[3]).toContain('no MIDI outputs visible');
    expect(checklist[4]).toContain('no Elektron input matched');
    expect(checklist[5]).toContain('no Elektron output matched');
    expect(spec.sections[2]!.table!.rows).toEqual([
      [
        'cockpit.connection.enumeration_failed.oserror',
        'MIDI port enumeration failed',
        '1721900000',
      ],
    ]);
    expect(spec.sections[3]!.chips).toEqual(['midi_port: 2']);
  });

  it('covers the no-manager and non-listening phase badge branches', () => {
    const noManager: DiagnosticsPayload = { ...diagnosticsHealthy, connection: null };
    const spec = connectionDoctorPanelSpec(noManager);
    expect(spec.status_badges[0]).toMatchObject({
      label: 'no connection manager',
      tone: 'warn',
    });
    expect(spec.sections[0]!.rows[0]).toContain('✗ no connection manager wired');
    expect(spec.sections[0]!.rows[1]).toContain('✓ phase: unknown');

    const searching: DiagnosticsPayload = {
      ...diagnosticsHealthy,
      connection: { ...connectionListening, phase: 'searching', selected_input: null },
    };
    expect(connectionDoctorPanelSpec(searching).status_badges[0]).toMatchObject({
      label: 'searching',
      tone: 'warn',
    });

    const armed: DiagnosticsPayload = {
      ...diagnosticsHealthy,
      connection: { ...connectionListening, phase: 'armed' },
    };
    expect(connectionDoctorPanelSpec(armed).status_badges[0]).toMatchObject({
      label: 'armed',
      tone: 'ok',
    });

    const fault: DiagnosticsPayload = {
      ...diagnosticsFaulty,
      connection: { ...connectionListening, phase: 'fault', last_error_fingerprint: null },
    };
    expect(connectionDoctorPanelSpec(fault).sections[0]!.rows[1]).toContain(
      'enumeration fault: unknown',
    );
  });
});

describe('ConnectionDoctorPanel (interactive)', () => {
  function renderPanel(fake: FakeCockpitClient): void {
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <ConnectionDoctorPanel />
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
    vi.unstubAllGlobals();
  });

  it('refresh sends the diagnostics command and stores the returned packet', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: true, diagnostics: diagnosticsHealthy });
    renderPanel(fake);

    expect(screen.getByTestId('doctor-export')).toBeDisabled();
    fireEvent.click(screen.getByTestId('doctor-refresh'));
    expect(fake.sent).toEqual([{ type: 'diagnostics' }]);

    expect(await screen.findByText('diagnostics refreshed')).toBeInTheDocument();
    const panel = screen.getByTestId('cockpit-panel-connection-doctor');
    expect(within(panel).getByText(/connection manager reporting/)).toBeInTheDocument();
    expect(useCockpitStore.getState().diagnostics).toBe(diagnosticsHealthy);
    expect(screen.getByTestId('doctor-export')).toBeEnabled();
  });

  it('surfaces rejected acks (message + fallback), missing payloads, and send failures', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'r1', ok: false, message: 'engine busy' });
    renderPanel(fake);

    fireEvent.click(screen.getByTestId('doctor-refresh'));
    expect(await screen.findByText('engine busy')).toBeInTheDocument();

    // ok ack with no diagnostics payload → fallback text.
    fake.ackQueue.push({ request_id: 'r2', ok: true });
    fireEvent.click(screen.getByTestId('doctor-refresh'));
    expect(await screen.findByText('diagnostics request rejected')).toBeInTheDocument();

    fake.nextRejection = new Error('socket not open');
    fireEvent.click(screen.getByTestId('doctor-refresh'));
    expect(
      await screen.findByText('diagnostics request failed to send'),
    ).toBeInTheDocument();
  });

  it('export copies the packet to the clipboard (unavailable, success, failure)', async () => {
    act(() => {
      useCockpitStore.getState().setDiagnostics(diagnosticsHealthy);
    });
    const fake = new FakeCockpitClient();
    renderPanel(fake);

    fireEvent.click(screen.getByTestId('doctor-export'));
    expect(await screen.findByText('clipboard unavailable')).toBeInTheDocument();

    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } });
    fireEvent.click(screen.getByTestId('doctor-export'));
    expect(await screen.findByText('diagnostics copied')).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith(JSON.stringify(diagnosticsHealthy, null, 2));

    writeText.mockRejectedValueOnce(new Error('denied'));
    fireEvent.click(screen.getByTestId('doctor-export'));
    expect(await screen.findByText('copy failed')).toBeInTheDocument();
  });
});
