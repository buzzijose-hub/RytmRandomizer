import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { analyzerPanelSpec, orderedAnalyzerControls } from '../../../src/cockpit/panels/analyzerPanel';
import { PanelHost } from '../../../src/cockpit/panels/PanelHost';
import { PanelRenderer } from '../../../src/cockpit/panels/PanelRenderer';
import { PANEL_REGISTRY, panelsForRegion } from '../../../src/cockpit/panels/registry';
import type {
  LiveGuiPerformanceConsoleModelDict,
  PanelSpecDict,
} from '../../../src/types/live_gui_protocol';
import { performanceConsolePayloadFixture } from '../performanceConsoleFixture';

const fixtureModel: LiveGuiPerformanceConsoleModelDict =
  performanceConsolePayloadFixture.live_gui_performance_console;

describe('analyzer registry panel', () => {
  it('is registered as a deck-region panel rendered by the generic PanelRenderer', () => {
    expect(PANEL_REGISTRY.map((entry) => entry.id)).toContain('analyzer');
    const deckPanels = panelsForRegion('deck');
    expect(deckPanels.map((entry) => entry.id)).toContain('analyzer');
    expect(deckPanels.every((entry) => entry.component === PanelRenderer)).toBe(true);
    expect(panelsForRegion('topbar')).toHaveLength(0);
  });

  it('skips a model-selector entry when the region is rendered without a console packet', () => {
    // The bottom rail has no packet; a deck render without one must degrade to
    // "nothing rendered", never a crash.
    const { container } = render(<PanelHost region="deck" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the committed fixture packet through PanelHost without enabling hardware actions', () => {
    render(<PanelHost region="deck" model={fixtureModel} />);

    const analyzerPanel = screen.getByTestId('cockpit-panel-analyzer');
    expect(analyzerPanel).toHaveTextContent('Analyzer (Post-Mutation Preview)');
    expect(analyzerPanel).toHaveTextContent('empty');
    expect(analyzerPanel).toHaveTextContent('split');
    expect(analyzerPanel).toHaveTextContent('No reference loaded');
    expect(analyzerPanel).toHaveTextContent('load-reference');

    // Spectrum bands land as a real table (columns, one row per band).
    expect(within(analyzerPanel).getByRole('columnheader', { name: 'Band' })).toBeInTheDocument();
    expect(within(analyzerPanel).getByRole('cell', { name: 'Low' })).toBeInTheDocument();
    expect(within(analyzerPanel).getByRole('cell', { name: '20-120 Hz' })).toBeInTheDocument();
    expect(within(analyzerPanel).getAllByRole('cell', { name: '0%' })).toHaveLength(5);

    // Controls surface as declarative chips in canonical order.
    const controls = within(analyzerPanel).getByLabelText('Controls');
    expect(controls).toHaveTextContent('Preview: waiting-for-reference');
    expect(controls).toHaveTextContent('Dry Run: waiting-for-reference');
    expect(controls).toHaveTextContent('Arm Hardware: locked');

    // Blocked actions are disabled buttons only — no clickable hardware path.
    const blocked = within(analyzerPanel).getByLabelText(/blocked actions/i);
    for (const action of fixtureModel.analyzer_panel.blocked_actions) {
      expect(within(blocked).getByRole('button', { name: action })).toBeDisabled();
    }

    // Only the true safety facts surface as safety lines.
    const safety = within(analyzerPanel).getByLabelText(/safety lines/i);
    expect(within(safety).getByText('passive')).toBeInTheDocument();
    expect(within(safety).queryByText('sends_midi')).not.toBeInTheDocument();
  });

  it('flips the status badge tone to ok when the analyzer is not empty', () => {
    const readyModel: LiveGuiPerformanceConsoleModelDict = {
      ...fixtureModel,
      analyzer_panel: { ...fixtureModel.analyzer_panel, panel_status: 'ready' },
    };
    const spec = analyzerPanelSpec(readyModel);
    expect(spec.status_badges[0]).toEqual({ label: 'ready', tone: 'ok', icon: '' });
    expect(analyzerPanelSpec(fixtureModel).status_badges[0]).toEqual({
      label: 'empty',
      tone: 'warn',
      icon: '',
    });
  });

  it('orders analyzer controls canonically, skips gaps, and appends unknown controls', () => {
    const ordered = orderedAnalyzerControls({
      extra: { key: 'extra', label: 'Extra', enabled: false, status: 'experimental' },
      arm_hardware: { key: 'arm_hardware', label: 'Arm Hardware', enabled: false, status: 'locked' },
      preview: { key: 'preview', label: 'Preview', enabled: false, status: 'waiting' },
    });
    expect(ordered.map((control) => control.key)).toEqual(['preview', 'arm_hardware', 'extra']);
  });
});

describe('PanelRenderer', () => {
  const bareSpec: PanelSpecDict = {
    panel_id: 'bare',
    title: 'Bare Panel',
    status_badges: [],
    sections: [],
    required_actions: [],
    blocked_actions: [],
    safety_lines: [],
  };

  it('renders a minimal spec without badges, sections, or action strips', () => {
    render(<PanelRenderer spec={bareSpec} />);

    const panel = screen.getByTestId('cockpit-panel-bare');
    expect(within(panel).getByRole('heading', { level: 2, name: 'Bare Panel' })).toBeInTheDocument();
    expect(within(panel).queryByRole('button')).not.toBeInTheDocument();
    expect(within(panel).queryByLabelText(/required actions/i)).not.toBeInTheDocument();
    expect(within(panel).queryByLabelText(/safety lines/i)).not.toBeInTheDocument();
  });

  it('renders every badge tone as icon plus text, honoring explicit icons', () => {
    render(
      <PanelRenderer
        spec={{
          ...bareSpec,
          panel_id: 'badges',
          status_badges: [
            { label: 'ready', tone: 'ok', icon: '' },
            { label: 'review', tone: 'warn', icon: '' },
            { label: 'edge', tone: 'risk', icon: '' },
            { label: 'info', tone: 'neutral', icon: 'i' },
          ],
        }}
      />,
    );

    const panel = screen.getByTestId('cockpit-panel-badges');
    expect(within(panel).getByText('✓')).toHaveAttribute('aria-hidden', 'true');
    expect(within(panel).getByText('!')).toBeInTheDocument();
    expect(within(panel).getByText('⚠')).toBeInTheDocument();
    expect(within(panel).getByText('i')).toBeInTheDocument();
    expect(within(panel).getByText('ready')).toBeInTheDocument();
  });

  it('renders an empty rows section with the house "none" placeholder', () => {
    render(
      <PanelRenderer
        spec={{
          ...bareSpec,
          panel_id: 'rows',
          sections: [
            { heading: 'Filled', kind: 'rows', rows: ['first row'], table: null, chips: [] },
            { heading: 'Empty', kind: 'rows', rows: [], table: null, chips: [] },
          ],
        }}
      />,
    );

    const panel = screen.getByTestId('cockpit-panel-rows');
    expect(within(panel).getByText('first row')).toBeInTheDocument();
    expect(within(panel).getByText('none')).toBeInTheDocument();
  });

  it('falls back to the rows placeholder when a table section carries no table payload', () => {
    render(
      <PanelRenderer
        spec={{
          ...bareSpec,
          panel_id: 'null-table',
          sections: [{ heading: 'Broken', kind: 'table', rows: [], table: null, chips: [] }],
        }}
      />,
    );

    const panel = screen.getByTestId('cockpit-panel-null-table');
    expect(within(panel).queryByRole('table')).not.toBeInTheDocument();
    expect(within(panel).getByText('none')).toBeInTheDocument();
  });

  it('renders required actions as chips and blocked actions as disabled buttons', () => {
    render(
      <PanelRenderer
        spec={{
          ...bareSpec,
          panel_id: 'actions',
          sections: [{ heading: 'Chips', kind: 'chips', rows: [], table: null, chips: ['one'] }],
          required_actions: ['load-reference'],
          blocked_actions: ['send-midi'],
          safety_lines: ['passive'],
        }}
      />,
    );

    const panel = screen.getByTestId('cockpit-panel-actions');
    expect(within(panel).getByText('one')).toBeInTheDocument();
    expect(within(panel).getByText('load-reference')).toBeInTheDocument();
    expect(within(panel).getByRole('button', { name: 'send-midi' })).toBeDisabled();
    expect(within(panel).getByText('passive')).toBeInTheDocument();
  });
});
