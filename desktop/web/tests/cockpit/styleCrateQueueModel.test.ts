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

  it('carries the passive Analog Four macro set plan for cockpit review', () => {
    const setPlan = DEFAULT_STYLE_CRATE_QUEUE_MODEL.analogFourSetPlan;

    expect(setPlan.setName).toBe('warehouse-arc');
    expect(setPlan.currentStep).toMatchObject({
      macroName: 'home',
      macroLabel: 'Home',
      readiness: 'review-ready',
    });
    expect(setPlan.upNext.map((step) => step.macroName)).toEqual([
      'hard-groove',
      'dub-pressure',
      'industrial-transition',
      'home',
    ]);
    expect(setPlan.opensPorts).toBe(false);
    expect(setPlan.sendsMidi).toBe(false);
    expect(setPlan.hardwareRequired).toBe(false);
    expect(setPlan.blockedActiveActions).toContain('A4 full macro SEND');
    expect(setPlan.replayCommand).toBe(
      'python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json',
    );
    expect(DEFAULT_STYLE_CRATE_QUEUE_MODEL.replayCommands).toContain(setPlan.replayCommand);
  });

  it('keeps generic crate display and unknown queued crate labels deterministic', () => {
    const sourceCrate = DEFAULT_STYLE_CRATE_REHEARSAL_DECK.crate_cards[0];
    const sourceQueueCard = DEFAULT_STYLE_CRATE_REHEARSAL_DECK.queue_cards[0];
    if (sourceCrate === undefined || sourceQueueCard === undefined) {
      throw new Error('default style crate fixture must include one crate and one queue card');
    }

    const model = toStyleCrateQueueModel({
      ...DEFAULT_STYLE_CRATE_REHEARSAL_DECK,
      crate_cards: [
        {
          ...sourceCrate,
          crate_key: 'Custom Crate/One',
          crate_name: 'Custom Crate One',
          primary_move_name: 'Custom Move',
        },
      ],
      queue_cards: [
        {
          ...sourceQueueCard,
          queue_key: 'custom queue/one',
          crate_key: 'missing_crate',
          move_name: 'Unknown Crate Move',
          target_pads: [12],
        },
      ],
      journal_cards: [],
    });

    expect(model.crates[0]).toMatchObject({
      key: 'Custom Crate/One',
      testIdKey: 'custom-crate-one',
      name: 'Custom Crate One',
      tone: 'blue',
    });
    expect(model.queue[0]).toMatchObject({
      key: 'custom queue/one',
      testIdKey: 'custom-queue-one',
      crateName: 'missing_crate',
      label: 'Unknown Crate Move',
      position: 'Current',
    });
    expect(model.summary).toBe('1 staged moves cover 1 target pad slots and 0 journal seeds.');
  });
});
