import { useEffect, useMemo, useRef, useState } from 'react';

import { useCockpitStore } from '../state';
import type { KitCaptureResult } from '../ws/protocol';

import { useCockpitClient } from './context';
import {
  ANALOG_FOUR_DEVICE_ID,
  type CockpitDeviceId,
  RYTM_DEVICE_ID,
} from './devices';

// The backend listener closes after 120 seconds; leave five seconds for the
// acknowledgement to cross the sidecar boundary before the UI times out.
const CAPTURE_ACK_TIMEOUT_MS = 125_000;

type CaptureStage = 'scanning' | 'ready' | 'listening' | 'captured' | 'error';

export interface KitCapturePanelProps {
  deviceId: CockpitDeviceId;
  onClose: () => void;
}

function deviceName(deviceId: CockpitDeviceId): string {
  return deviceId === RYTM_DEVICE_ID ? 'Analog Rytm MKII' : 'Analog Four MKII';
}

function hardwareInstruction(deviceId: CockpitDeviceId): string {
  if (deviceId === RYTM_DEVICE_ID) {
    return 'On the Rytm: GLOBAL SETTINGS → SYSEX DUMP → SYSEX SEND → KIT.';
  }
  return 'On the A4: open SYSEX DUMP, choose the currently loaded KIT, then send it.';
}

function readinessCopy(capture: KitCaptureResult): string {
  if (capture.parameter_readiness === 'rytm_anchor_ready') {
    return '12-pad kit anchor decoded. Verified pad rows can feed the Rytm mutation workflow.';
  }
  return 'Exact A4 kit anchor preserved. Unverified semantic offsets stay parked until mapping is promoted.';
}

export function KitCapturePanel({ deviceId, onClose }: KitCapturePanelProps): JSX.Element {
  const client = useCockpitClient();
  const session = useCockpitStore((state) => state.sessionStatus);
  const storedCaptures = useCockpitStore((state) => state.kitCaptures);
  const storedCapture = useMemo(
    () => storedCaptures.find((capture) => capture.device_id === deviceId) ?? null,
    [deviceId, storedCaptures],
  );
  const [stage, setStage] = useState<CaptureStage>('scanning');
  const [inputs, setInputs] = useState<string[]>([]);
  const [selectedInput, setSelectedInput] = useState('');
  const [captureEnabled, setCaptureEnabled] = useState(session?.capture_enabled ?? false);
  const [localCapture, setLocalCapture] = useState<KitCaptureResult | null>(null);
  const [error, setError] = useState('');
  const capture = localCapture ?? storedCapture;
  const captureRef = useRef<KitCaptureResult | null>(capture);
  captureRef.current = capture;

  useEffect(() => {
    let active = true;
    setStage('scanning');
    setError('');
    void client
      .send({ type: 'list_capture_inputs', device_id: deviceId })
      .then((ack) => {
        if (!active) return;
        if (!ack.ok) {
          setError('The input scan was rejected. Capture remains safely closed.');
          setStage('error');
          return;
        }
        const nextInputs = ack.capture_inputs ?? [];
        setInputs(nextInputs);
        setSelectedInput(nextInputs[0] ?? '');
        setCaptureEnabled(ack.capture_enabled ?? session?.capture_enabled ?? false);
        setStage(captureRef.current === null ? 'ready' : 'captured');
      })
      .catch(() => {
        if (!active) return;
        setError('Could not scan MIDI inputs. No port was opened.');
        setStage('error');
      });
    return () => {
      active = false;
    };
  }, [client, deviceId, session?.capture_enabled]);

  const startCapture = async (): Promise<void> => {
    setError('');
    setStage('listening');
    try {
      const ack = await client.send(
        {
          type: 'capture_current_kit',
          device_id: deviceId,
          input_port: selectedInput,
        },
        { timeoutMs: CAPTURE_ACK_TIMEOUT_MS },
      );
      if (!ack.ok || ack.kit_capture === undefined) {
        setError('No valid current-KIT frame was accepted. The prior anchor is unchanged.');
        setStage('error');
        return;
      }
      setLocalCapture(ack.kit_capture);
      setStage('captured');
    } catch {
      setError('Capture timed out or the input closed. The prior anchor is unchanged.');
      setStage('error');
    }
  };

  return (
    <section className="kit-capture-panel" data-testid="kit-capture-panel" aria-live="polite">
      <header className="kit-capture-header">
        <div>
          <span className="eyebrow">CURRENT KIT ANCHOR · INPUT ONLY</span>
          <h2>Prepare {deviceName(deviceId)} to receive</h2>
          <p>One machine at a time. The other machine remains untouched.</p>
        </div>
        <button type="button" className="capture-close" onClick={onClose} aria-label="Close kit capture">
          ×
        </button>
      </header>

      <div className="kit-capture-safety">
        <strong>No request is sent.</strong> The software only listens after you choose an input;
        no MIDI output is opened and no SysEx is written back to the hardware.
      </div>

      <div className="kit-capture-controls">
        <label htmlFor="kit-capture-input">MIDI input</label>
        <select
          id="kit-capture-input"
          value={selectedInput}
          onChange={(event) => setSelectedInput(event.target.value)}
          disabled={!captureEnabled || stage === 'listening'}
        >
          {inputs.length === 0 ? <option value="">No input detected</option> : null}
          {inputs.map((input) => (
            <option value={input} key={input}>
              {input}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="capture-start-button"
          data-testid="capture-current-kit-start"
          disabled={!captureEnabled || selectedInput === '' || stage === 'listening'}
          onClick={() => void startCapture()}
        >
          {stage === 'listening' ? 'Listening for KIT…' : 'Start input-only capture'}
        </button>
      </div>

      {!captureEnabled ? (
        <p className="capture-locked" data-testid="capture-locked-message">
          Hardware receive is locked in this passive preview. Launch the standalone Cockpit
          capture mode to enumerate an input.
        </p>
      ) : (
        <p className="capture-instruction">{hardwareInstruction(deviceId)}</p>
      )}

      {stage === 'listening' ? (
        <div className="capture-listening" data-testid="capture-listening">
          <span className="capture-pulse" aria-hidden="true" />
          Listening on {selectedInput}. Now send the currently loaded KIT from the hardware.
        </div>
      ) : null}
      {error !== '' ? <p className="capture-error">{error}</p> : null}

      {capture !== null ? (
        <div className="captured-kit" data-testid="captured-kit-layout">
          <div className="captured-kit-summary">
            <div>
              <span className="eyebrow">VERIFIED ANCHOR</span>
              <h3>{capture.kit_name || 'Unnamed Kit'}</h3>
            </div>
            <dl>
              <div><dt>Fingerprint</dt><dd>{capture.fingerprint}</dd></div>
              <div><dt>Frame</dt><dd>{capture.frame_bytes} bytes</dd></div>
              <div><dt>Round trip</dt><dd>{capture.round_trip_verified ? 'Verified' : 'Blocked'}</dd></div>
            </dl>
          </div>
          <p>{readinessCopy(capture)}</p>
          <div
            className={deviceId === ANALOG_FOUR_DEVICE_ID ? 'capture-layout a4' : 'capture-layout rytm'}
            aria-label={`${deviceName(deviceId)} captured layout`}
            role="list"
          >
            {capture.layout_items.map((item) => (
              <article
                className={`capture-layout-item ${item.status}`}
                key={item.index}
                role="listitem"
              >
                <span>{deviceId === RYTM_DEVICE_ID ? `P${item.index}` : `T${item.index}`}</span>
                <strong>{item.label}</strong>
                <small>
                  {item.status === 'mutation_ready' ? 'Mutation ready' : 'Mapping pending'}
                </small>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <div className="capture-empty-layout">
          Waiting for a verified {deviceName(deviceId)} KIT anchor before laying out its tracks.
        </div>
      )}
    </section>
  );
}
