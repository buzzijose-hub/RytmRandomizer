import type { ComponentType } from 'react';

import type {
  LiveGuiPerformanceConsoleModelDict,
  PanelSpecDict,
} from '../../types/live_gui_protocol';
import { analyzerPanelSpec } from './analyzerPanel';
import { PanelRenderer } from './PanelRenderer';

/**
 * Schema-driven panel manifest. Adding a cockpit panel is one entry here:
 * an id, a layout region, a pure selector (`console packet -> PanelSpecDict`),
 * and the component (almost always the generic `PanelRenderer`).
 *
 * See `.claude/skills/add-cockpit-panel/SKILL.md` for the full recipe.
 */

export type PanelRegion = 'topbar' | 'left-rail' | 'deck' | 'bottom';

export interface PanelManifestEntry {
  readonly id: string;
  readonly region: PanelRegion;
  readonly selector: (model: LiveGuiPerformanceConsoleModelDict) => PanelSpecDict;
  readonly component: ComponentType<{ spec: PanelSpecDict }>;
}

export const PANEL_REGISTRY: ReadonlyArray<PanelManifestEntry> = [
  { id: 'analyzer', region: 'deck', selector: analyzerPanelSpec, component: PanelRenderer },
];

export function panelsForRegion(region: PanelRegion): ReadonlyArray<PanelManifestEntry> {
  return PANEL_REGISTRY.filter((entry) => entry.region === region);
}
