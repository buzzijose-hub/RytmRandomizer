import { Component, type ErrorInfo, type ReactNode } from 'react';

/** Keep the on-screen message short; the full error goes to the console. */
const MAX_MESSAGE_LENGTH = 300;

interface AppErrorBoundaryProps {
  children: ReactNode;
  /** Injected for tests; defaults to a real page reload. */
  onReload?: () => void;
}

interface AppErrorBoundaryState {
  message: string | null;
}

/**
 * Last line of defence for the whole app.
 *
 * Without a boundary, React unmounts the ENTIRE tree when any component throws
 * during render: the window goes blank with no explanation. On stage that is
 * the worst possible failure -- the operator cannot tell a crash from a hang,
 * and has no way back except killing the app.
 *
 * With it, a render error leaves a visible, readable message and a Reload
 * button. The native acceptance driver also reads `app-render-error`, so a CI
 * failure names the actual error instead of "Timed out: React cockpit mounted"
 * (see issue #251).
 *
 * This deliberately does not try to recover or retry: after an unexpected
 * render error the app's state is untrustworthy, and a reload is the honest
 * way back.
 */
export class AppErrorBoundary extends Component<AppErrorBoundaryProps, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = { message: null };

  static getDerivedStateFromError(error: unknown): AppErrorBoundaryState {
    const message = error instanceof Error ? error.message : String(error);
    return { message: message.slice(0, MAX_MESSAGE_LENGTH) || 'Unknown error' };
  }

  componentDidCatch(error: unknown, info: ErrorInfo): void {
    console.error('RytmRandomizer render error', error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.message === null) return this.props.children;
    const reload = this.props.onReload ?? (() => window.location.reload());
    return (
      <main className="app-render-error" role="alert" data-testid="app-render-error">
        <h1>Something went wrong</h1>
        <p>The cockpit hit an unexpected error and stopped drawing. Nothing was sent to your hardware.</p>
        <pre data-testid="app-render-error-message">{this.state.message}</pre>
        <button type="button" onClick={reload}>
          Reload
        </button>
      </main>
    );
  }
}
