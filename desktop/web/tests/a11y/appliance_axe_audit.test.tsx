import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { Appliance } from '../../src/appliance/Appliance';
import { useCockpitStore } from '../../src/state';
import type { ApplianceState } from '../../src/ws/protocol';
import { ApplianceFakeClient, applianceState, candidateState } from '../appliance/fixtures';

import { runAxe, violationSummary } from './__helpers__/axe';

async function mount(state: ApplianceState = applianceState()): Promise<HTMLElement> {
  const client = new ApplianceFakeClient();
  client.ackQueue.push({ request_id: 'state', ok: true, appliance: state });
  const { container } = render(<Appliance client={client.asClient()} />);
  await screen.findByRole('heading', { name: 'HOME / PERFORM' });
  return container;
}

async function expectClean(container: Element): Promise<void> {
  const result = await runAxe(container);
  expect(result.violations, violationSummary(result)).toHaveLength(0);
}

function pageButton(name: string): HTMLElement {
  return within(screen.getByRole('navigation', { name: 'Appliance pages' }))
    .getByRole('button', { name });
}

beforeEach(() => { useCockpitStore.getState().reset(); });
afterEach(() => { cleanup(); useCockpitStore.getState().reset(); });

describe('appliance axe audit (WCAG 2.2 AA, zero violations)', () => {
  it('covers the connected home controls and twelve-pad target grid', async () => {
    const container = await mount();
    expect(screen.getAllByRole('button', { name: /^Pad \d+,/ })).toHaveLength(12);
    await expectClean(container);
  });

  it('covers per-track depth and protection controls', async () => {
    const container = await mount();
    fireEvent.click(pageButton('RYTM'));
    expect(screen.getByRole('combobox', { name: 'Track to edit' })).toBeInTheDocument();
    await expectClean(container);
  });

  it('covers parameter protection and explicit unavailable reasons', async () => {
    const container = await mount();
    fireEvent.click(pageButton('RYTM'));
    fireEvent.click(screen.getByRole('button', { name: 'PROTECT' }));
    expect(screen.getByRole('button', { name: 'Unlock ROUTING' })).toBeDisabled();
    await expectClean(container);
  });

  it('covers the touch numeric dialog', async () => {
    const container = await mount();
    fireEvent.click(screen.getByRole('button', { name: 'MASTER 25 percent. Adjust' }));
    expect(screen.getByRole('dialog', { name: 'MASTER DEPTH' })).toBeInTheDocument();
    await expectClean(container);
  });

  it('covers the exact local-apply confirmation and candidate diff', async () => {
    const container = await mount(candidateState());
    fireEvent.click(screen.getByRole('button', { name: 'LOCAL APPLY…' }));
    expect(screen.getByRole('dialog', { name: 'CONFIRM LOCAL APPLY' })).toBeInTheDocument();
    await expectClean(container);
  });

  it('covers the passive exact-output dialog without granting arm authority', async () => {
    const container = await mount(applianceState({ mode: 'production' }));
    fireEvent.click(screen.getByRole('button', { name: 'ARM…' }));
    expect(screen.getByRole('dialog', { name: 'ARM EXACT OUTPUT' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'CONFIRM ARM' })).toBeDisabled();
    await expectClean(container);
  });
});
