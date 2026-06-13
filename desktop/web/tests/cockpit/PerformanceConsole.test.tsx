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
        move.queue_key === 'queue-opening-shadow' ? { ...move, dry_run_only: false } : move,
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
    expect(within(styleQueue).getAllByTestId(/^style-crate-/)).toHaveLength(9);
    const darkHypnoticCrate = within(styleQueue).getByTestId('style-crate-dark-hypnotic');
    expect(darkHypnoticCrate).toHaveTextContent('Deeper & Minimal');
    expect(darkHypnoticCrate).toHaveTextContent('energy 5');
    expect(darkHypnoticCrate).toHaveTextContent('risk 3');
    expect(darkHypnoticCrate).toHaveTextContent('pads 1, 3, 11');
    expect(darkHypnoticCrate).toHaveTextContent('hypnotic');
    expect(darkHypnoticCrate).toHaveTextContent('minimal');
    expect(darkHypnoticCrate).toHaveTextContent('shadow');
    expect(
      within(darkHypnoticCrate).getByRole('button', { name: /stage shadow filter pressure/i }),
    ).toBeDisabled();
    const industrialCrate = within(styleQueue).getByTestId('style-crate-industrial-broken');
    expect(industrialCrate).toHaveTextContent('Industrial/Broken');
    expect(industrialCrate).toHaveTextContent('Metal & Drive');
    expect(industrialCrate).toHaveTextContent('energy 8');
    expect(industrialCrate).toHaveTextContent('risk 7');
    expect(industrialCrate).toHaveTextContent('pads 3, 4, 8, 10, 11');
    expect(styleQueue).toHaveTextContent('Dark Hypnotic');
    expect(styleQueue).toHaveTextContent('Shadow Filter Pressure');
    expect(styleQueue).toHaveTextContent('Pressure Rattle');
    expect(styleQueue).toHaveTextContent('Preview before real send');
    expect(styleQueue).toHaveTextContent('recover Back To Clean Handoff');
    expect(styleQueue).toHaveTextContent('pads 1, 3, 11');
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
    const openingMove = within(styleQueue).getByTestId('style-queue-move-queue-opening-shadow');
    expect(openingMove).toHaveTextContent('Preview before real send');
    expect(openingMove).toHaveTextContent('recover Back To Clean Handoff');
    expect(openingMove).not.toHaveTextContent('dry-run only');
    expect(within(styleQueue).getByTestId('style-queue-move-queue-groove-pressure')).toHaveTextContent(
      'dry-run only',
    );
  });
});
