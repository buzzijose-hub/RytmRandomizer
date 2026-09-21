/**
 * `OperatorLogList` — the single log-list component in the cockpit.
 *
 * Extracted from the markup that lived inline in SafetyRail so the update
 * panel's activity list can reuse it (plan reuse contract R4). These tests
 * pin the markup contract both surfaces depend on.
 */

import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  OperatorLogList,
  type OperatorLogListEntry,
} from '../../src/cockpit/OperatorLogList';

const ENTRIES: ReadonlyArray<OperatorLogListEntry> = [
  { id: 'a', level: 'info', message: 'WebSocket connected' },
  { id: 'b', level: 'success', message: 'download_ok 42 MB' },
  { id: 'c', level: 'error', message: 'signature_rejected bad_signature' },
];

describe('OperatorLogList', () => {
  it('renders the empty copy in place of an empty list', () => {
    render(
      <OperatorLogList entries={[]} emptyText="Nothing yet." testId="x" label="Log" />,
    );
    expect(screen.getByText('Nothing yet.')).toBeInTheDocument();
    expect(screen.queryByTestId('x')).not.toBeInTheDocument();
  });

  it('renders an ordered list with one class-tagged item per entry', () => {
    render(
      <OperatorLogList entries={ENTRIES} emptyText="Nothing yet." testId="x" label="Log" />,
    );
    const list = screen.getByTestId('x');
    expect(list.tagName).toBe('OL');
    expect(list).toHaveClass('operator-log-list');
    const items = within(list).getAllByRole('listitem');
    expect(items.map((li) => li.textContent)).toEqual([
      'WebSocket connected',
      'download_ok 42 MB',
      'signature_rejected bad_signature',
    ]);
    expect(items[0]).toHaveClass('operator-log-entry', 'info');
    expect(items[1]).toHaveClass('operator-log-entry', 'success');
    expect(items[2]).toHaveClass('operator-log-entry', 'error');
  });

  it('carries the accessible name the caller supplied', () => {
    render(
      <OperatorLogList entries={ENTRIES} emptyText="Nothing yet." testId="x" label="Operator log" />,
    );
    expect(screen.getByRole('list', { name: 'Operator log' })).toBeInTheDocument();
  });
});
