import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PerformanceConsole } from '../../src/cockpit/PerformanceConsole';
import { performanceConsoleModel } from './performanceConsoleFixture';

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

    const styleQueue = screen.getByTestId('performance-console-style-queue');
    expect(styleQueue).toHaveTextContent('Dark Hypnotic');
    expect(styleQueue).toHaveTextContent('snap-06');

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
});
