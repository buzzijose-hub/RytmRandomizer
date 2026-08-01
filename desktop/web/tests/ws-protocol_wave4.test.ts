/**
 * Wave-4 protocol mirror: the three new push events must be recognised by
 * the isEvent guard, and the new command shapes compile against the
 * Command union (exercised via typed literals).
 */

import { describe, expect, it } from 'vitest';

import { isCommandAck, isEvent, type Command } from '../src/ws/protocol';

import {
  connectionListening,
  libraryRecordA,
  midiBatch,
} from './cockpit/_fixtures';

describe('wave-4 protocol mirror', () => {
  it('isEvent recognises connection_changed, midi_activity, and library_changed', () => {
    expect(
      isEvent({ type: 'connection_changed', connection: connectionListening }),
    ).toBe(true);
    expect(isEvent({ type: 'midi_activity', midi_activity: midiBatch })).toBe(true);
    expect(
      isEvent({ type: 'library_changed', library: { records: [libraryRecordA] } }),
    ).toBe(true);
    expect(isEvent({ type: 'not_a_cockpit_event' })).toBe(false);
  });

  it('the eight new command shapes are members of the Command union', () => {
    const commands: Command[] = [
      { type: 'arm', arm_token: 'tok', confirm: true, port_name: 'Analog Rytm MK2 OUT' },
      { type: 'disarm' },
      { type: 'diagnostics' },
      { type: 'library_list' },
      { type: 'library_search', query: 'acid' },
      { type: 'library_tag', record_id: 'abc123', tags: ['techno'] },
      { type: 'library_delete', record_id: 'abc123' },
      { type: 'library_import_captures' },
    ];
    expect(commands.map((command) => command.type)).toEqual([
      'arm',
      'disarm',
      'diagnostics',
      'library_list',
      'library_search',
      'library_tag',
      'library_delete',
      'library_import_captures',
    ]);
  });

  it('acks carrying the wave-4 payload fields still satisfy isCommandAck', () => {
    expect(
      isCommandAck({
        request_id: 'r1',
        ok: true,
        armed: true,
        midi_port: 'Analog Rytm MK2 OUT',
        diagnostics: null,
        library_records: [],
        library_record: null,
        library_record_id: 'abc123',
        library_import: null,
      }),
    ).toBe(true);
  });
});
