import { describe, expect, it } from 'vitest';

import {
  DEFAULT_STYLE_CRATE_REHEARSAL_DECK,
  DEFAULT_STYLE_CRATE_QUEUE_MODEL,
  toStyleCrateQueueModel,
} from '../../src/cockpit/styleCrateQueueModel';

describe('styleCrateQueueModel', () => {
  it('converts backend rehearsal deck cards into cockpit queue cards', () => {
    const model = toStyleCrateQueueModel(DEFAULT_STYLE_CRATE_REHEARSAL_DECK);

    expect(model.modelVersion).toBe('style-crate-rehearsal-deck-v1');
    expect(model.crates[0]).toMatchObject({
      key: 'dark_hypnotic',
      testIdKey: 'dark-hypnotic',
      name: 'Dark Hypnotic',
      move: 'Shadow Filter Pressure',
      energy: 5,
      risk: 3,
      tone: 'blue',
    });
    expect(model.queue[0]).toMatchObject({
      key: 'queue-opening-shadow',
      testIdKey: 'queue-opening-shadow',
      label: 'Shadow Filter Pressure',
      subtitle: 'opening tunnel',
      status: 'staged',
      position: 'Current',
      dryRunOnly: true,
    });
    expect(model.summary).toBe('3 staged moves cover 14 target pad slots and 2 journal seeds.');
    expect(model.safetyLabel).toBe('Passive queue preview only');
    expect(model.blockedActions).toContain('send MIDI');
  });

  it('ships a default model that keeps the cinematic panel populated without backend IO', () => {
    expect(DEFAULT_STYLE_CRATE_QUEUE_MODEL.crates).toHaveLength(9);
    expect(DEFAULT_STYLE_CRATE_QUEUE_MODEL.queue).toHaveLength(3);
    expect(DEFAULT_STYLE_CRATE_QUEUE_MODEL.journalCount).toBe(2);
  });
});
