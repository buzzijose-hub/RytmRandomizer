import type {
  StyleCrateRehearsalCrateCardDict,
  StyleCrateRehearsalDeckDict,
} from '../types/style_crate_rehearsal_deck';

export type StyleCrateTone =
  | 'blue'
  | 'cyan'
  | 'green'
  | 'muted'
  | 'orange'
  | 'purple'
  | 'yellow';

export interface StyleCrateQueueCrate {
  readonly key: string;
  readonly testIdKey: string;
  readonly name: string;
  readonly summary: string;
  readonly move: string;
  readonly energy: number;
  readonly risk: number;
  readonly tone: StyleCrateTone;
  readonly targetPads: ReadonlyArray<number>;
  readonly riskStatus: string;
  readonly operatorAction: string;
}

export interface StyleCrateQueueMove {
  readonly key: string;
  readonly testIdKey: string;
  readonly crateKey: string;
  readonly crateName: string;
  readonly label: string;
  readonly subtitle: string;
  readonly status: string;
  readonly position: 'Current' | 'Up Next';
  readonly mutationAmountPercent: number;
  readonly targetPads: ReadonlyArray<number>;
  readonly riskStatus: string;
  readonly operatorAction: string;
  readonly recoveryAction: string;
  readonly dryRunOnly: boolean;
}

export interface StyleCrateAnalogFourSetStep {
  readonly order: number;
  readonly macroName: string;
  readonly macroLabel: string;
  readonly summary: string;
  readonly seed: number;
  readonly intensity: number;
  readonly energy: number;
  readonly readiness: string;
  readonly eventCount: number;
  readonly readyCount: number;
  readonly reviewCount: number;
  readonly blockedCount: number;
  readonly validationCommand: string;
  readonly recoveryAction: string;
}

export interface StyleCrateAnalogFourSetPlan {
  readonly title: string;
  readonly setName: string;
  readonly stepCount: number;
  readonly currentStep: StyleCrateAnalogFourSetStep;
  readonly upNext: ReadonlyArray<StyleCrateAnalogFourSetStep>;
  readonly steps: ReadonlyArray<StyleCrateAnalogFourSetStep>;
  readonly opensPorts: boolean;
  readonly sendsMidi: boolean;
  readonly hardwareRequired: boolean;
  readonly blockedActiveActions: ReadonlyArray<string>;
  readonly safety: ReadonlyArray<string>;
  readonly replayCommand: string;
}

export interface StyleCrateQueueModel {
  readonly modelVersion: string;
  readonly deckId: string;
  readonly status: string;
  readonly crates: ReadonlyArray<StyleCrateQueueCrate>;
  readonly queue: ReadonlyArray<StyleCrateQueueMove>;
  readonly journalCount: number;
  readonly summary: string;
  readonly safetyLabel: string;
  readonly blockedActions: ReadonlyArray<string>;
  readonly replayCommands: ReadonlyArray<string>;
  readonly analogFourSetPlan: StyleCrateAnalogFourSetPlan;
}

const CRATE_DISPLAY_OVERRIDES: Record<
  string,
  {
    readonly name?: string;
    readonly testIdKey?: string;
    readonly tone: StyleCrateTone;
  }
> = {
  chaos_fills: { tone: 'orange' },
  dark_hypnotic: { tone: 'blue' },
  deep_minimal: { tone: 'cyan' },
  dub_pressure: { tone: 'purple' },
  hard_groove: { tone: 'green' },
  industrial_broken: {
    name: 'Industrial Warehouse',
    testIdKey: 'industrial-warehouse',
    tone: 'orange',
  },
  peak_time: { tone: 'yellow' },
  saved_accidents: { tone: 'muted' },
  transitions: {
    name: 'Transition / Build',
    testIdKey: 'transition-build',
    tone: 'cyan',
  },
};

const DEFAULT_TONE: StyleCrateTone = 'blue';

export const ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND =
  'python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json';

const DEFAULT_ANALOG_FOUR_SET_STEPS: readonly [
  StyleCrateAnalogFourSetStep,
  ...StyleCrateAnalogFourSetStep[],
] = [
  {
    order: 1,
    macroName: 'home',
    macroLabel: 'Home',
    summary: 'Gentle four-track reset-adjacent motion for a stable live anchor.',
    seed: 0,
    intensity: 2,
    energy: 2,
    readiness: 'review-ready',
    eventCount: 8,
    readyCount: 8,
    reviewCount: 0,
    blockedCount: 0,
    validationCommand:
      'analog-four-oxi-macro-readiness-report home --seed 0 --intensity 2 --limit 4',
    recoveryAction: 'reload saved A4 kit or return to home macro',
  },
  {
    order: 2,
    macroName: 'hard-groove',
    macroLabel: 'Hard Groove',
    summary: 'OXI-style four-track pressure for bass, stab, motion, and air lanes.',
    seed: 1,
    intensity: 5,
    energy: 5,
    readiness: 'review-ready',
    eventCount: 12,
    readyCount: 12,
    reviewCount: 0,
    blockedCount: 0,
    validationCommand:
      'analog-four-oxi-macro-readiness-report hard-groove --seed 1 --intensity 5 --limit 4',
    recoveryAction: 'reload saved A4 kit or return to home macro',
  },
  {
    order: 3,
    macroName: 'dub-pressure',
    macroLabel: 'Dub Pressure',
    summary: 'Delay/reverb-led A4 macro for cavernous but controlled hypnosis.',
    seed: 2,
    intensity: 4,
    energy: 4,
    readiness: 'review-ready',
    eventCount: 8,
    readyCount: 8,
    reviewCount: 0,
    blockedCount: 0,
    validationCommand:
      'analog-four-oxi-macro-readiness-report dub-pressure --seed 2 --intensity 4 --limit 4',
    recoveryAction: 'reload saved A4 kit or return to home macro',
  },
  {
    order: 4,
    macroName: 'industrial-transition',
    macroLabel: 'Industrial Transition',
    summary: 'Tense four-track riser macro for transitions and breakdown pressure.',
    seed: 3,
    intensity: 7,
    energy: 7,
    readiness: 'review-ready',
    eventCount: 9,
    readyCount: 9,
    reviewCount: 0,
    blockedCount: 0,
    validationCommand:
      'analog-four-oxi-macro-readiness-report industrial-transition --seed 3 --intensity 7 --limit 4',
    recoveryAction: 'reload saved A4 kit or return to home macro',
  },
  {
    order: 5,
    macroName: 'home',
    macroLabel: 'Home',
    summary: 'Gentle four-track reset-adjacent motion for a stable live anchor.',
    seed: 4,
    intensity: 2,
    energy: 2,
    readiness: 'review-ready',
    eventCount: 8,
    readyCount: 8,
    reviewCount: 0,
    blockedCount: 0,
    validationCommand:
      'analog-four-oxi-macro-readiness-report home --seed 4 --intensity 2 --limit 4',
    recoveryAction: 'reload saved A4 kit or return to home macro',
  },
];

export const DEFAULT_ANALOG_FOUR_SET_PLAN: StyleCrateAnalogFourSetPlan = {
  title: 'RytmRandomizer passive Analog Four OXI macro set planner',
  setName: 'warehouse-arc',
  stepCount: DEFAULT_ANALOG_FOUR_SET_STEPS.length,
  currentStep: DEFAULT_ANALOG_FOUR_SET_STEPS[0],
  upNext: DEFAULT_ANALOG_FOUR_SET_STEPS.slice(1),
  steps: DEFAULT_ANALOG_FOUR_SET_STEPS,
  opensPorts: false,
  sendsMidi: false,
  hardwareRequired: false,
  blockedActiveActions: ['A4 full macro SEND', 'A4 unattended macro playback'],
  safety: [
    'passive/read-only',
    'A4 OXI macro set planning only',
    'manual-backed Analog Four CC metadata only',
    'no MIDI sending',
    'no port opening',
    'no command execution',
    'no hardware mutation',
    'A4 full macro SEND remains blocked',
  ],
  replayCommand: ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND,
};

function toTestIdKey(key: string): string {
  return key.toLowerCase().replaceAll('_', '-').replaceAll('/', '-').replaceAll(' ', '-');
}

function crateDisplay(crate: StyleCrateRehearsalCrateCardDict): {
  readonly name: string;
  readonly testIdKey: string;
  readonly tone: StyleCrateTone;
} {
  const override = CRATE_DISPLAY_OVERRIDES[crate.crate_key];
  return {
    name: override?.name ?? crate.crate_name,
    testIdKey: override?.testIdKey ?? toTestIdKey(crate.crate_key),
    tone: override?.tone ?? DEFAULT_TONE,
  };
}

function replayCommandsWithAnalogFourSetPlanner(
  replayCommands: ReadonlyArray<string>,
): ReadonlyArray<string> {
  return replayCommands.includes(ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND)
    ? replayCommands
    : [...replayCommands, ANALOG_FOUR_SET_PLAN_REPLAY_COMMAND];
}

export function toStyleCrateQueueModel(
  deck: StyleCrateRehearsalDeckDict,
): StyleCrateQueueModel {
  const crates = deck.crate_cards.map((crate) => {
    const display = crateDisplay(crate);
    return {
      key: crate.crate_key,
      testIdKey: display.testIdKey,
      name: display.name,
      summary: crate.summary,
      move: crate.primary_move_name,
      energy: crate.energy,
      risk: crate.risk,
      tone: display.tone,
      targetPads: crate.target_pads,
      riskStatus: crate.risk_status,
      operatorAction: crate.operator_action,
    };
  });

  const crateNames = new Map(crates.map((crate) => [crate.key, crate.name] as const));
  const stagedQueue = deck.queue_cards.filter((card) => card.status === 'staged');
  const queue = stagedQueue.map((card, index) => ({
    key: card.queue_key,
    testIdKey: toTestIdKey(card.queue_key),
    crateKey: card.crate_key,
    crateName: crateNames.get(card.crate_key) ?? card.crate_key,
    label: card.move_name,
    subtitle: card.chapter,
    status: card.status,
    position: index === 0 ? ('Current' as const) : ('Up Next' as const),
    mutationAmountPercent: card.mutation_amount_percent,
    targetPads: card.target_pads,
    riskStatus: card.risk_status,
    operatorAction: card.operator_action,
    recoveryAction: card.recovery_action,
    dryRunOnly: card.dry_run_only,
  }));
  const targetPadSlots = queue.reduce((total, move) => total + move.targetPads.length, 0);
  const journalCount = deck.journal_cards.length;

  return {
    modelVersion: deck.deck_version,
    deckId: deck.deck_id,
    status: deck.deck_status,
    crates,
    queue,
    journalCount,
    summary: `${queue.length} staged moves cover ${targetPadSlots} target pad slots and ${journalCount} journal seeds.`,
    safetyLabel: 'Passive queue preview only',
    blockedActions: deck.blocked_actions,
    replayCommands: replayCommandsWithAnalogFourSetPlanner(deck.replay_commands),
    analogFourSetPlan: DEFAULT_ANALOG_FOUR_SET_PLAN,
  };
}

export const DEFAULT_STYLE_CRATE_REHEARSAL_DECK: StyleCrateRehearsalDeckDict = {
  deck_version: 'style-crate-rehearsal-deck-v1',
  deck_id: 'default-style-crate-rehearsal',
  deck_status: 'passive-preview',
  crate_filter: 'all',
  crate_cards: [
    {
      crate_key: 'dark_hypnotic',
      crate_name: 'Dark Hypnotic',
      summary: 'Deeper & Minimal',
      tags: ['hypnotic', 'minimal', 'shadow'],
      move_count: 1,
      primary_move_key: 'shadow_filter_pressure',
      primary_move_name: 'Shadow Filter Pressure',
      energy: 5,
      risk: 3,
      risk_status: 'safe',
      target_pads: [1, 3, 11],
      operator_action: 'Stage for passive preview',
    },
    {
      crate_key: 'peak_time',
      crate_name: 'Peak Time',
      summary: 'Energy & Lift',
      tags: ['peak', 'lift', 'warehouse'],
      move_count: 1,
      primary_move_key: 'warehouse_lift',
      primary_move_name: 'Warehouse Lift',
      energy: 9,
      risk: 6,
      risk_status: 'review-ready',
      target_pads: [1, 2, 3, 4, 9, 11],
      operator_action: 'Review before staging',
    },
    {
      crate_key: 'hard_groove',
      crate_name: 'Hard Groove',
      summary: 'Rolling percussion density',
      tags: ['groove', 'rolling', 'percussion'],
      move_count: 1,
      primary_move_key: 'rolling_perc_push',
      primary_move_name: 'Rolling Perc Push',
      energy: 7,
      risk: 4,
      risk_status: 'review-ready',
      target_pads: [2, 3, 5, 6, 7, 9],
      operator_action: 'Stage with preview',
    },
    {
      crate_key: 'dub_pressure',
      crate_name: 'Dub Pressure',
      summary: 'Space and low-end',
      tags: ['dub', 'pressure', 'space'],
      move_count: 1,
      primary_move_key: 'sub_space_bloom',
      primary_move_name: 'Sub Space Bloom',
      energy: 4,
      risk: 3,
      risk_status: 'safe',
      target_pads: [1, 3, 12],
      operator_action: 'Stage for space movement',
    },
    {
      crate_key: 'industrial_broken',
      crate_name: 'Industrial/Broken',
      summary: 'Metal & Drive',
      tags: ['industrial', 'broken', 'metal'],
      move_count: 1,
      primary_move_key: 'broken_metal_stress',
      primary_move_name: 'Broken Metal Stress',
      energy: 8,
      risk: 7,
      risk_status: 'high-risk',
      target_pads: [3, 4, 8, 10, 11],
      operator_action: 'Keep dry-run only until reviewed',
    },
    {
      crate_key: 'deep_minimal',
      crate_name: 'Deep Minimal',
      summary: 'Sparse low-motion restraint',
      tags: ['deep', 'minimal', 'restraint'],
      move_count: 1,
      primary_move_key: 'micro_motion_hold',
      primary_move_name: 'Micro Motion Hold',
      energy: 3,
      risk: 2,
      risk_status: 'safe',
      target_pads: [1, 2, 3],
      operator_action: 'Stage as a low-risk bridge',
    },
    {
      crate_key: 'chaos_fills',
      crate_name: 'Chaos Fills',
      summary: 'Explicit one-bar disruption',
      tags: ['fills', 'chaos', 'one-shot'],
      move_count: 1,
      primary_move_key: 'one_bar_flash',
      primary_move_name: 'One-Bar Flash',
      energy: 10,
      risk: 9,
      risk_status: 'high-risk',
      target_pads: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
      operator_action: 'Require explicit chaos mode',
    },
    {
      crate_key: 'transitions',
      crate_name: 'Transitions',
      summary: 'Handoff movement',
      tags: ['transition', 'handoff', 'reset'],
      move_count: 1,
      primary_move_key: 'back_to_clean_handoff',
      primary_move_name: 'Back To Clean Handoff',
      energy: 2,
      risk: 1,
      risk_status: 'safe',
      target_pads: [1, 2, 3, 4],
      operator_action: 'Stage for recovery',
    },
    {
      crate_key: 'saved_accidents',
      crate_name: 'Saved Accidents',
      summary: 'Rehearsed happy accidents',
      tags: ['journal', 'replay', 'accident'],
      move_count: 1,
      primary_move_key: 'journaled_pressure_rattle',
      primary_move_name: 'Journaled Pressure Rattle',
      energy: 6,
      risk: 5,
      risk_status: 'review-ready',
      target_pads: [3, 9, 11],
      operator_action: 'Review saved seed before staging',
    },
  ],
  queue_cards: [
    {
      queue_key: 'queue-opening-shadow',
      order: 1,
      use_case: 'pre-planned set story',
      chapter: 'opening tunnel',
      crate_key: 'dark_hypnotic',
      move_key: 'shadow_filter_pressure',
      move_name: 'Shadow Filter Pressure',
      status: 'staged',
      mutation_amount_percent: 28,
      target_pads: [1, 3, 11],
      risk_status: 'safe',
      operator_action: 'Preview before real send',
      recovery_action: 'Back To Clean Handoff',
      dry_run_only: true,
    },
    {
      queue_key: 'queue-groove-pressure',
      order: 2,
      use_case: 'pre-planned set story',
      chapter: 'pressure lift',
      crate_key: 'hard_groove',
      move_key: 'rolling_perc_push',
      move_name: 'Rolling Perc Push',
      status: 'staged',
      mutation_amount_percent: 45,
      target_pads: [2, 3, 5, 6, 7, 9],
      risk_status: 'review-ready',
      operator_action: 'Preview with locks visible',
      recovery_action: 'Back To Clean Handoff',
      dry_run_only: true,
    },
    {
      queue_key: 'queue-peak-metal',
      order: 3,
      use_case: 'pre-planned set story',
      chapter: 'peak stress',
      crate_key: 'industrial_broken',
      move_key: 'broken_metal_stress',
      move_name: 'Broken Metal Stress',
      status: 'staged',
      mutation_amount_percent: 64,
      target_pads: [3, 4, 8, 10, 11],
      risk_status: 'high-risk',
      operator_action: 'Dry-run only until approved',
      recovery_action: 'Back To Clean Handoff',
      dry_run_only: true,
    },
    {
      queue_key: 'queue-scratchpad-clean',
      order: 4,
      use_case: 'live scratchpad',
      chapter: 'scratchpad recovery',
      crate_key: 'transitions',
      move_key: 'back_to_clean_handoff',
      move_name: 'Back To Clean Handoff',
      status: 'scratchpad',
      mutation_amount_percent: 0,
      target_pads: [1, 2, 3, 4],
      risk_status: 'safe',
      operator_action: 'Keep available for recovery',
      recovery_action: 'Already a recovery move',
      dry_run_only: true,
    },
  ],
  journal_cards: [
    {
      journal_key: 'journal-pressure-rattle',
      name: 'Pressure Rattle',
      tags: ['rattle', 'pressure'],
      replay_seed: 'rr-journal-pressure-rattle',
      pads: [3, 9, 11],
      depth: 'groove',
      guardrail_mode: 'Live Safe',
      risk_status: 'review-ready',
      value_summary: ['Pad 3 filter lift', 'Pad 9 SRC bite', 'Pad 11 FX grit'],
      operator_action: 'Replay in dry-run first',
    },
    {
      journal_key: 'journal-clean-recovery',
      name: 'Clean Recovery',
      tags: ['reset', 'safe'],
      replay_seed: 'rr-journal-clean-recovery',
      pads: [1, 2, 3, 4],
      depth: 'micro',
      guardrail_mode: 'Live Safe',
      risk_status: 'safe',
      value_summary: ['Return core pads to anchor', 'Reduce FX send'],
      operator_action: 'Use as recovery seed',
    },
  ],
  blocked_actions: ['send MIDI', 'open hardware port', 'apply unattended send'],
  replay_commands: [
    'rytm-randomizer style-crates --format json',
    'rytm-randomizer style-crates --crate dark_hypnotic --format json',
  ],
};

export const DEFAULT_STYLE_CRATE_QUEUE_MODEL = toStyleCrateQueueModel(
  DEFAULT_STYLE_CRATE_REHEARSAL_DECK,
);
