import { describe, expect, it } from 'vitest';

import {
  ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND,
  DEFAULT_STYLE_CRATE_REHEARSAL_DECK,
  DEFAULT_STYLE_CRATE_QUEUE_MODEL,
  toStyleCrateAnalogFourSetPlan,
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

  it('does not duplicate the Analog Four set planner replay command', () => {
    const model = toStyleCrateQueueModel({
      ...DEFAULT_STYLE_CRATE_REHEARSAL_DECK,
      replay_commands: [
        'rytm-randomizer style-crates --format json',
        ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND,
      ],
    });

    expect(
      model.replayCommands.filter((command) => command === ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND),
    ).toHaveLength(1);
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

  it('converts backend Analog Four set-planner JSON into the cockpit model', () => {
    const backendPlan = {
      title: 'RytmRandomizer passive Analog Four OXI macro set planner',
      set_name: 'late-room',
      step_count: 2,
      current_step: {
        order: 1,
        macro_name: 'home',
        macro_label: 'Home',
        summary: 'Reset-adjacent motion.',
        seed: 30,
        intensity: 2,
        energy: 2,
        readiness: 'review-ready',
        event_count: 8,
        ready_count: 8,
        review_count: 0,
        blocked_count: 0,
        validation_command:
          'analog-four-oxi-macro-readiness-report home --seed 30 --intensity 2 --limit 4',
        recovery_action: 'reload saved A4 kit or return to home macro',
      },
      up_next: [
        {
          order: 2,
          macro_name: 'industrial-transition',
          macro_label: 'Industrial Transition',
          summary: 'Transition pressure.',
          seed: 31,
          intensity: 7,
          energy: 7,
          readiness: 'review-ready',
          event_count: 9,
          ready_count: 9,
          review_count: 0,
          blocked_count: 0,
          validation_command:
            'analog-four-oxi-macro-readiness-report industrial-transition --seed 31 --intensity 7 --limit 4',
          recovery_action: 'reload saved A4 kit or return to home macro',
        },
      ],
      steps: [
        {
          order: 1,
          macro_name: 'home',
          macro_label: 'Home',
          summary: 'Reset-adjacent motion.',
          seed: 30,
          intensity: 2,
          energy: 2,
          readiness: 'review-ready',
          event_count: 8,
          ready_count: 8,
          review_count: 0,
          blocked_count: 0,
          validation_command:
            'analog-four-oxi-macro-readiness-report home --seed 30 --intensity 2 --limit 4',
          recovery_action: 'reload saved A4 kit or return to home macro',
        },
        {
          order: 2,
          macro_name: 'industrial-transition',
          macro_label: 'Industrial Transition',
          summary: 'Transition pressure.',
          seed: 31,
          intensity: 7,
          energy: 7,
          readiness: 'review-ready',
          event_count: 9,
          ready_count: 9,
          review_count: 0,
          blocked_count: 0,
          validation_command:
            'analog-four-oxi-macro-readiness-report industrial-transition --seed 31 --intensity 7 --limit 4',
          recovery_action: 'reload saved A4 kit or return to home macro',
        },
      ],
      opens_ports: false,
      sends_midi: false,
      hardware_required: false,
      blocked_active_actions: ['A4 full macro SEND'],
      safety: ['passive/read-only', 'no MIDI sending'],
      replay_command:
        'python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --set-name late-room --json',
    };

    const plan = toStyleCrateAnalogFourSetPlan(backendPlan);

    expect(plan.setName).toBe('late-room');
    expect(plan.currentStep).toMatchObject({
      macroName: 'home',
      validationCommand:
        'analog-four-oxi-macro-readiness-report home --seed 30 --intensity 2 --limit 4',
    });
    expect(plan.upNext[0]).toMatchObject({
      macroName: 'industrial-transition',
      eventCount: 9,
    });
    expect(plan.blockedActiveActions).toEqual(['A4 full macro SEND']);
    expect(plan.replayCommand).toBe(
      'python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --set-name late-room --json',
    );
  });

  it('lets a backend Analog Four set planner drive the style queue replay command', () => {
    const model = toStyleCrateQueueModel(DEFAULT_STYLE_CRATE_REHEARSAL_DECK, {
      analogFourSetPlan: {
        title: 'RytmRandomizer passive Analog Four OXI macro set planner',
        set_name: 'late-room',
        step_count: 1,
        current_step: {
          order: 1,
          macro_name: 'dub-pressure',
          macro_label: 'Dub Pressure',
          summary: 'Space pressure.',
          seed: 8,
          intensity: 4,
          energy: 4,
          readiness: 'review-ready',
          event_count: 8,
          ready_count: 8,
          review_count: 0,
          blocked_count: 0,
          validation_command:
            'analog-four-oxi-macro-readiness-report dub-pressure --seed 8 --intensity 4 --limit 4',
          recovery_action: 'reload saved A4 kit or return to home macro',
        },
        up_next: [],
        steps: [
          {
            order: 1,
            macro_name: 'dub-pressure',
            macro_label: 'Dub Pressure',
            summary: 'Space pressure.',
            seed: 8,
            intensity: 4,
            energy: 4,
            readiness: 'review-ready',
            event_count: 8,
            ready_count: 8,
            review_count: 0,
            blocked_count: 0,
            validation_command:
              'analog-four-oxi-macro-readiness-report dub-pressure --seed 8 --intensity 4 --limit 4',
            recovery_action: 'reload saved A4 kit or return to home macro',
          },
        ],
        opens_ports: false,
        sends_midi: false,
        hardware_required: false,
        blocked_active_actions: ['A4 full macro SEND'],
        safety: ['passive/read-only', 'no MIDI sending'],
        replay_command:
          'python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --sequence dub-pressure --json',
      },
    });

    expect(model.analogFourSetPlan.setName).toBe('late-room');
    expect(model.analogFourSetPlan.currentStep.macroName).toBe('dub-pressure');
    expect(model.replayCommands).toContain(
      'python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --sequence dub-pressure --json',
    );
    expect(model.replayCommands).not.toContain(ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND);
  });
});
