/**
 * Tests for the CockpitClientProvider + useCockpitClient hook.
 */

import { describe, expect, it } from 'vitest';
import { render, renderHook, screen } from '@testing-library/react';

import {
  CockpitClientProvider,
  useCockpitClient,
} from '../../src/cockpit/context';

import { FakeCockpitClient } from './_fixtures';

function Consumer(): JSX.Element {
  const client = useCockpitClient();
  return <span data-testid="ok">status:{client.getStatus()}</span>;
}

describe('CockpitClientProvider + useCockpitClient', () => {
  it('provides the client to children', () => {
    const fake = new FakeCockpitClient();
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <Consumer />
      </CockpitClientProvider>,
    );
    expect(screen.getByTestId('ok')).toHaveTextContent('status:connected');
  });

  it('throws when used outside a provider', () => {
    // renderHook surfaces the throw as the `result.error` field in v16, but the docs
    // change between RTL versions; the simplest guarantee is to wrap renderHook in a
    // try/catch via expect(() => ...).toThrow.
    expect(() => {
      renderHook(() => useCockpitClient());
    }).toThrow(/useCockpitClient/);
  });
});
