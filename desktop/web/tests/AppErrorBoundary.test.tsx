import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AppErrorBoundary } from '../src/AppErrorBoundary';

function Thrower({ value }: { value: unknown }): JSX.Element {
  throw value;
}

describe('AppErrorBoundary', () => {
  // React logs every caught render error; keep test output readable.
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });
  afterEach(() => vi.restoreAllMocks());

  it('renders its children when nothing throws', () => {
    render(
      <AppErrorBoundary>
        <p>cockpit</p>
      </AppErrorBoundary>,
    );
    expect(screen.getByText('cockpit')).toBeInTheDocument();
    expect(screen.queryByTestId('app-render-error')).toBeNull();
  });

  it('replaces a blank crash with a readable message', () => {
    // Without a boundary React unmounts the whole tree and the window goes
    // blank. This is what an operator on stage would otherwise see.
    render(
      <AppErrorBoundary>
        <Thrower value={new Error('device_inventory is undefined')} />
      </AppErrorBoundary>,
    );
    expect(screen.getByRole('alert')).toHaveAttribute('data-testid', 'app-render-error');
    expect(screen.getByTestId('app-render-error-message')).toHaveTextContent(
      'device_inventory is undefined',
    );
    // A crash cannot prove that nothing was sent: it may follow an armed send.
    expect(screen.getByText(/outcome is unknown from here: check your instrument/)).toBeInTheDocument();
    expect(screen.queryByText(/Nothing was sent/)).toBeNull();
  });

  it('handles a non-Error throw and an empty message', () => {
    const { unmount } = render(
      <AppErrorBoundary>
        <Thrower value="plain string" />
      </AppErrorBoundary>,
    );
    expect(screen.getByTestId('app-render-error-message')).toHaveTextContent('plain string');
    unmount();

    render(
      <AppErrorBoundary>
        <Thrower value={new Error('')} />
      </AppErrorBoundary>,
    );
    expect(screen.getByTestId('app-render-error-message')).toHaveTextContent('Unknown error');
  });

  it('bounds a very long message', () => {
    render(
      <AppErrorBoundary>
        <Thrower value={new Error('x'.repeat(5000))} />
      </AppErrorBoundary>,
    );
    expect(screen.getByTestId('app-render-error-message').textContent).toHaveLength(300);
  });

  it('reloads through the injected handler', () => {
    const onReload = vi.fn();
    render(
      <AppErrorBoundary onReload={onReload}>
        <Thrower value={new Error('boom')} />
      </AppErrorBoundary>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Reload' }));
    expect(onReload).toHaveBeenCalledTimes(1);
  });

  it('defaults to a real page reload', () => {
    const reload = vi.fn();
    vi.spyOn(window, 'location', 'get').mockReturnValue({ ...window.location, reload });
    render(
      <AppErrorBoundary>
        <Thrower value={new Error('boom')} />
      </AppErrorBoundary>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Reload' }));
    expect(reload).toHaveBeenCalledTimes(1);
  });
});
