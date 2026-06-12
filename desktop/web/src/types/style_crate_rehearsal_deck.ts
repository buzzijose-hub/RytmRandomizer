export interface StyleCrateRehearsalCrateCardDict {
  readonly crate_key: string;
  readonly crate_name: string;
  readonly summary: string;
  readonly tags: ReadonlyArray<string>;
  readonly move_count: number;
  readonly primary_move_key: string;
  readonly primary_move_name: string;
  readonly energy: number;
  readonly risk: number;
  readonly risk_status: string;
  readonly target_pads: ReadonlyArray<number>;
  readonly operator_action: string;
}

export interface StyleCrateRehearsalQueueCardDict {
  readonly queue_key: string;
  readonly order: number;
  readonly use_case: string;
  readonly chapter: string;
  readonly crate_key: string;
  readonly move_key: string;
  readonly move_name: string;
  readonly status: string;
  readonly mutation_amount_percent: number;
  readonly target_pads: ReadonlyArray<number>;
  readonly risk_status: string;
  readonly operator_action: string;
  readonly recovery_action: string;
  readonly dry_run_only: boolean;
}

export interface StyleCrateRehearsalJournalCardDict {
  readonly journal_key: string;
  readonly name: string;
  readonly tags: ReadonlyArray<string>;
  readonly replay_seed: string;
  readonly pads: ReadonlyArray<number>;
  readonly depth: string;
  readonly guardrail_mode: string;
  readonly risk_status: string;
  readonly value_summary: ReadonlyArray<string>;
  readonly operator_action: string;
}

export interface StyleCrateRehearsalDeckDict {
  readonly deck_version: string;
  readonly deck_id: string;
  readonly deck_status: string;
  readonly crate_filter: string;
  readonly crate_cards: ReadonlyArray<StyleCrateRehearsalCrateCardDict>;
  readonly queue_cards: ReadonlyArray<StyleCrateRehearsalQueueCardDict>;
  readonly journal_cards: ReadonlyArray<StyleCrateRehearsalJournalCardDict>;
  readonly blocked_actions: ReadonlyArray<string>;
  readonly replay_commands: ReadonlyArray<string>;
}
