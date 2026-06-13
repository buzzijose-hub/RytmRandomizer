import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PerformanceConsole } from '../../src/cockpit/PerformanceConsole';
import type { LiveGuiPerformanceConsoleModelDict } from '../../src/types/live_gui_protocol';
import { performanceConsoleModel } from './performanceConsoleFixture';

function performanceConsoleModelWithActiveDryRunBoundaries(): LiveGuiPerformanceConsoleModelDict {
  return {
    ...performanceConsoleModel,
    macro_action_deck: {
      ...performanceConsoleModel.macro_action_deck,
      cards: performanceConsoleModel.macro_action_deck.cards.map((card) =>
        card.macro_key === 'hard-groove' ? { ...card, dry_run_only: false } : card,
      ),
    },
    style_queue: {
      ...performanceConsoleModel.style_queue,
      queue_cards: performanceConsoleModel.style_queue.queue_cards.map((move) =>
        move.queue_key === 'queue-dark-01' ? { ...move, dry_run_only: false } : move,
      ),
    },
  };
}

describe('PerformanceConsole', () => {
  it('renders the passive console packet without enabling hardware actions', () => {
    render(<PerformanceConsole model={performanceConsoleModel} />);

    expect(screen.getByTestId('performance-console')).toHaveTextContent(
      'RytmRandomizer Cockpit Performance Console',
    );
    const safetyState = screen.getByLabelText('Console safety state');
    expect(within(safetyState).getByText('mock-safe')).toBeInTheDocument();
    expect(within(safetyState).getByText('passive')).toBeInTheDocument();
    expect(within(safetyState).getByText('passive packet')).toBeInTheDocument();
    expect(screen.getByText('Warehouse arc')).toBeInTheDocument();

    expect(screen.getByTestId('performance-console-device-analog_rytm_mk2')).toHaveTextContent(
      'Elektron Analog Rytm MKII',
    );
    expect(screen.getByTestId('performance-console-device-analog_four_mk2')).toHaveTextContent(
      'Elektron Analog Four MKII',
    );

    expect(screen.getAllByTestId(/performance-console-pad-/)).toHaveLength(12);
    expect(screen.getByTestId('performance-console-pad-11')).toHaveTextContent('SY Raw');
    expect(screen.getByTestId('performance-console-pad-12')).toHaveTextContent('Pad 12');

    const flow = screen.getByTestId('performance-console-flow');
    expect(flow).toHaveTextContent('capture-anchor');
    expect(flow).toHaveTextContent('kit-core');
    expect(flow).toHaveTextContent('warehouse-arc');
    expect(flow).toHaveTextContent('A4 full macro SEND');

    const macroActions = screen.getByTestId('performance-console-macro-actions');
    expect(macroActions).toHaveTextContent('Live Macro Actions');
    expect(macroActions).toHaveTextContent('hard-groove');
    expect(macroActions).toHaveTextContent('pads 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12');
    expect(macroActions).toHaveTextContent('stage-review-send');
    expect(macroActions).toHaveTextContent('fire macro from Cockpit console');
    expect(within(macroActions).getAllByRole('button', { name: /prepare/i })[0]).toBeDisabled();
    expect(within(macroActions).getAllByRole('button', { name: /send/i })[0]).toBeDisabled();
    const hardGrooveMacro = within(macroActions).getByTestId('macro-action-hard-groove');
    expect(hardGrooveMacro).toHaveTextContent('recover home');
    expect(hardGrooveMacro).toHaveTextContent('hardware blocked');
    expect(hardGrooveMacro).toHaveTextContent('dry-run only');

    const styleQueue = screen.getByTestId('performance-console-style-queue');
    expect(styleQueue).toHaveTextContent('Style Crates');
    const darkHypnoticCrate = within(styleQueue).getByTestId('style-crate-dark-hypnotic');
    expect(darkHypnoticCrate).toHaveTextContent('rolling pressure');
    expect(darkHypnoticCrate).toHaveTextContent('energy 7');
    expect(darkHypnoticCrate).toHaveTextContent('risk 4');
    expect(darkHypnoticCrate).toHaveTextContent('pads 1, 2, 3, 4');
    expect(darkHypnoticCrate).toHaveTextContent('dark');
    expect(darkHypnoticCrate).toHaveTextContent('hypnotic');
    expect(within(darkHypnoticCrate).getByRole('button', { name: /stage dark hypnotic/i })).toBeDisabled();
    expect(styleQueue).toHaveTextContent('Dark Hypnotic');
    expect(styleQueue).toHaveTextContent('snap-06');
    expect(styleQueue).toHaveTextContent('preview');
    expect(styleQueue).toHaveTextContent('recover home');
    expect(styleQueue).toHaveTextContent('pads 1, 2, 3, 4');
    expect(styleQueue).toHaveTextContent('dry-run only');

    expect(screen.getByTestId('performance-console-snapshot-history')).toHaveTextContent(
      'console-snap-03',
    );
    expect(screen.getByTestId('performance-console-command-queue')).toHaveTextContent(
      'Mutate Pad 11',
    );
    expect(screen.getByTestId('performance-console-safety')).toHaveTextContent('4 / 4');

    const blocked = screen.getByTestId('performance-console-blocked-actions');
    expect(within(blocked).getByText('a4_outbound_macro_send')).toBeInTheDocument();
    expect(within(blocked).getByText('send MIDI from snapshot history')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
  });

  it('omits dry-run-only labels when a macro or queued move is not dry-run-only', () => {
    render(<PerformanceConsole model={performanceConsoleModelWithActiveDryRunBoundaries()} />);

    const macroActions = screen.getByTestId('performance-console-macro-actions');
    const hardGrooveMacro = within(macroActions).getByTestId('macro-action-hard-groove');
    expect(hardGrooveMacro).not.toHaveTextContent('dry-run only');

    const styleQueue = screen.getByTestId('performance-console-style-queue');
    expect(styleQueue).toHaveTextContent('preview');
    expect(styleQueue).toHaveTextContent('recover home');
    expect(styleQueue).not.toHaveTextContent('dry-run only');
  });
});
