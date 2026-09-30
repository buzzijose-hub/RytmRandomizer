import { useEffect, useId, useRef, type ReactNode } from 'react';

interface TouchDialogProps {
  title: string;
  children: ReactNode;
  onClose: () => void;
}

/** One accessible touch dialog shared by exact-action and numeric controls. */
export function TouchDialog({ title, children, onClose }: TouchDialogProps): JSX.Element {
  const titleId = useId();
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const prior = document.activeElement as HTMLElement | null;
    root.current?.querySelector<HTMLElement>('button:not([disabled])')?.focus();
    return () => { prior?.focus(); };
  }, []);
  return (
    <div className="appliance-dialog-backdrop">
      <div
        ref={root}
        className="appliance-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onKeyDown={(event) => {
          if (event.key === 'Escape') onClose();
          if (event.key !== 'Tab') return;
          const controls = event.currentTarget.querySelectorAll<HTMLElement>(
            'button:not([disabled]), input:not([disabled]), select:not([disabled]), a[href]',
          );
          const first = controls[0];
          const last = controls[controls.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault(); last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault(); first?.focus();
          }
        }}
      >
        <header><h2 id={titleId}>{title}</h2><button type="button" aria-label="Close dialog" onClick={onClose}>CLOSE</button></header>
        {children}
      </div>
    </div>
  );
}
