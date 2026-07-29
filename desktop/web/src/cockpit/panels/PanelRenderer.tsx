import type { BadgeDict, PanelSectionDict, PanelSpecDict } from '../../types/live_gui_protocol';
import './panel.css';

/**
 * Generic renderer for any `PanelSpecDict` (the schema-driven panel contract
 * GENERATED from `rytm_randomizer/reports/panel_spec.py`).
 *
 * Accessibility rules baked in:
 * - badges render icon + text, never hue alone (`TONE_GLYPHS` fallback);
 * - every section is a labelled landmark-free region with its own heading;
 * - blocked actions render as disabled buttons so no hardware path is
 *   clickable in the passive console packet.
 */

const TONE_GLYPHS: Readonly<Record<BadgeDict['tone'], string>> = {
  ok: '✓',
  warn: '!',
  risk: '⚠',
  neutral: '•',
};

export interface PanelRendererProps {
  spec: PanelSpecDict;
}

function PanelBadge({ badge }: { badge: BadgeDict }) {
  return (
    <span className={`cockpit-panel-badge cockpit-panel-badge-${badge.tone}`}>
      <span aria-hidden="true">{badge.icon || TONE_GLYPHS[badge.tone]}</span> {badge.label}
    </span>
  );
}

function PanelSectionBody({ section }: { section: PanelSectionDict }) {
  if (section.kind === 'table' && section.table !== null) {
    return (
      <div className="cockpit-panel-table-scroll">
        <table className="cockpit-panel-table">
          <thead>
            <tr>
              {section.table.columns.map((column) => (
                <th key={column} scope="col">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {section.table.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  if (section.kind === 'chips') {
    return (
      <div className="live-chip-row" aria-label={section.heading}>
        {section.chips.map((chip) => (
          <span key={chip} className="live-chip">
            {chip}
          </span>
        ))}
      </div>
    );
  }
  return (
    <ul className="cockpit-panel-rows">
      {section.rows.length > 0 ? (
        section.rows.map((row) => <li key={row}>{row}</li>)
      ) : (
        <li className="cockpit-panel-row-empty">none</li>
      )}
    </ul>
  );
}

export function PanelRenderer({ spec }: PanelRendererProps) {
  const titleId = `cockpit-panel-${spec.panel_id}-title`;
  return (
    <section
      className="performance-console-surface cockpit-panel"
      data-testid={`cockpit-panel-${spec.panel_id}`}
      aria-labelledby={titleId}
    >
      <header className="performance-console-section-header">
        <h2 id={titleId}>{spec.title}</h2>
        {spec.status_badges.length > 0 && (
          <span className="cockpit-panel-badges">
            {spec.status_badges.map((badge) => (
              <PanelBadge key={`${badge.tone}-${badge.label}`} badge={badge} />
            ))}
          </span>
        )}
      </header>
      {spec.sections.map((section) => (
        <div key={section.heading} className="cockpit-panel-section">
          <h3 className="cockpit-panel-section-heading">{section.heading}</h3>
          <PanelSectionBody section={section} />
        </div>
      ))}
      {spec.required_actions.length > 0 && (
        <div className="live-chip-row" aria-label={`${spec.title} required actions`}>
          {spec.required_actions.map((action) => (
            <span key={action} className="live-chip">
              {action}
            </span>
          ))}
        </div>
      )}
      {spec.blocked_actions.length > 0 && (
        <div
          className="performance-console-macro-actions"
          aria-label={`${spec.title} blocked actions`}
        >
          {spec.blocked_actions.map((action) => (
            <button
              key={action}
              type="button"
              className="live-readiness-action live-readiness-action-locked"
              disabled
              title="Blocked in this passive console packet."
            >
              {action}
            </button>
          ))}
        </div>
      )}
      {spec.safety_lines.length > 0 && (
        <div className="live-chip-row" aria-label={`${spec.title} safety lines`}>
          {spec.safety_lines.map((line) => (
            <span key={line} className="live-chip">
              {line}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
