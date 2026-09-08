import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type RefObject,
} from 'react';

import type { SessionStatus } from '../state';
import type { CockpitSendPlan, Command } from '../ws/protocol';

type SendCommand = Extract<Command, { type: 'send' }>;

interface SourceReloadContext {
  readonly fingerprint: string;
  readonly slot: number | null;
}

export interface ExactRytmSendController {
  readonly confirmationOpen: boolean;
  readonly disabled: boolean;
  readonly isLiveHardware: boolean;
  readonly label: 'SEND' | 'DRY-RUN SEND';
  readonly triggerRef: RefObject<HTMLButtonElement>;
  readonly sourceReload: SourceReloadContext | undefined;
  readonly sourceReloadConfirmed: boolean;
  readonly setSourceReloadConfirmed: (confirmed: boolean) => void;
  readonly cancel: () => void;
  readonly confirm: () => void;
  readonly request: () => void;
}

interface UseExactRytmSendOptions {
  readonly canSend: boolean;
  readonly onSend: (command: SendCommand) => void;
  readonly sendPlan: CockpitSendPlan | null;
  readonly session: SessionStatus | null;
  readonly sourceReload?: SourceReloadContext;
}

/**
 * One safety contract for every exact Rytm send affordance.
 *
 * Mock/passive sessions execute a one-click dry run without performative
 * confirmation. Only an armed live session with an output port can open the
 * per-action hardware confirmation. Changing the plan, output, or armed state
 * invalidates an open confirmation immediately.
 */
export function useExactRytmSend({
  canSend,
  onSend,
  sendPlan,
  session,
  sourceReload,
}: UseExactRytmSendOptions): ExactRytmSendController {
  const [confirmationContext, setConfirmationContext] = useState<string | null>(null);
  const [sourceReloadConfirmed, setSourceReloadConfirmed] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const isLiveHardware = session?.mode === 'live' && session.armed;
  const liveOutputMissing = isLiveHardware && session.midi_port === null;
  const disabled = !canSend || sendPlan === null || liveOutputMissing;
  const confirmationPlan = !disabled && isLiveHardware ? sendPlan : null;
  const currentContext = useMemo(
    () =>
      confirmationPlan !== null
        ? `${confirmationPlan.plan_id}\u0000${session?.midi_port}\u0000${sourceReload?.fingerprint ?? ''}\u0000${sourceReload?.slot ?? ''}`
        : null,
    [confirmationPlan, session?.midi_port, sourceReload?.fingerprint, sourceReload?.slot],
  );
  const confirmationOpen =
    confirmationContext !== null && confirmationContext === currentContext;

  useEffect(() => {
    if (confirmationContext !== null && confirmationContext !== currentContext) {
      setConfirmationContext(null);
      triggerRef.current?.focus();
    }
  }, [confirmationContext, currentContext]);

  const closeConfirmation = (): void => {
    setConfirmationContext(null);
    setSourceReloadConfirmed(false);
    triggerRef.current?.focus();
  };

  const request = (): void => {
    if (disabled || sendPlan === null) return;
    if (isLiveHardware) {
      setSourceReloadConfirmed(false);
      setConfirmationContext(currentContext);
      return;
    }
    onSend({ type: 'send', send_plan_id: sendPlan.plan_id });
  };

  const confirm = (): void => {
    if (confirmationPlan === null || !confirmationOpen || (sourceReload !== undefined && !sourceReloadConfirmed)) return;
    closeConfirmation();
    onSend({
      type: 'send', confirm: true, send_plan_id: confirmationPlan.plan_id,
      ...(sourceReload === undefined ? {} : { show_bank_source_reloaded: true }),
    });
  };

  return {
    confirmationOpen,
    disabled,
    isLiveHardware,
    label: isLiveHardware ? 'SEND' : 'DRY-RUN SEND',
    triggerRef,
    sourceReload,
    sourceReloadConfirmed,
    setSourceReloadConfirmed,
    cancel: closeConfirmation,
    confirm,
    request,
  };
}

function trapFocus(container: HTMLElement, event: KeyboardEvent<HTMLElement>): void {
  const focusable = container.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled])');
  // Every open dialog renders an enabled Cancel button, so this set is nonempty.
  const first = focusable[0] as HTMLElement;
  const last = focusable[focusable.length - 1] as HTMLElement;
  const active = container.ownerDocument.activeElement;
  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

export interface ExactRytmSendDialogProps {
  readonly className?: string;
  readonly controller: ExactRytmSendController;
  readonly sendPlan: CockpitSendPlan | null;
  readonly session: SessionStatus | null;
}

/** Accessible exact-plan confirmation shared by ActionBar and Show Kit Forge. */
export function ExactRytmSendDialog({
  className = 'arm-dialog',
  controller,
  sendPlan,
  session,
}: ExactRytmSendDialogProps): JSX.Element | null {
  const titleId = useId();
  const descriptionId = useId();
  if (
    !controller.confirmationOpen ||
    !controller.isLiveHardware ||
    sendPlan === null ||
    session === null ||
    session.midi_port === null
  ) {
    return null;
  }
  const preparedPadIds = [...new Set(sendPlan.packets.map((packet) => packet.pad_id))].sort(
    (left, right) => left - right,
  );

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      className={className}
      data-testid="send-confirm-dialog"
      onKeyDown={(event) => {
        if (event.key === 'Escape') {
          controller.cancel();
        } else if (event.key === 'Tab') {
          trapFocus(event.currentTarget, event);
        }
      }}
    >
      <h2 id={titleId}>Confirm send to hardware</h2>
      <p id={descriptionId}>
        Confirming transmits this exact prepared plan as live-dial CC changes to the
        instrument&apos;s working memory. Saved kits and sounds are not written. Each send is
        confirmed separately.
      </p>
      <dl className="send-confirm-details">
        <div><dt>Output</dt><dd>{session.midi_port}</dd></div>
        <div><dt>Prepared plan</dt><dd>{sendPlan.plan_id}</dd></div>
        <div><dt>Pads</dt><dd>{preparedPadIds.join(', ') || 'None'}</dd></div>
        <div><dt>Messages</dt><dd>{sendPlan.estimated_midi_msgs}</dd></div>
      </dl>
      {controller.sourceReload !== undefined && (
        <label className="show-kit-forge-source-confirmation">
          <input
            type="checkbox"
            checked={controller.sourceReloadConfirmed}
            onChange={(event) => controller.setSourceReloadConfirmed(event.currentTarget.checked)}
          />
          I manually reloaded Rytm source slot {controller.sourceReload.slot ?? 'not reported'},
          then captured its current KIT and reselected this candidate.
          Source fingerprint: <code>{controller.sourceReload.fingerprint}</code>.
        </label>
      )}
      <div className="arm-dialog-actions">
        <button type="button" onClick={controller.cancel} data-testid="send-cancel-button" autoFocus={controller.sourceReload !== undefined}>
          Cancel
        </button>
        <button
          type="button"
          onClick={controller.confirm}
          data-testid="send-confirm-button"
          disabled={controller.sourceReload !== undefined && !controller.sourceReloadConfirmed}
          autoFocus={controller.sourceReload === undefined}
        >
          Confirm send
        </button>
      </div>
    </div>
  );
}
