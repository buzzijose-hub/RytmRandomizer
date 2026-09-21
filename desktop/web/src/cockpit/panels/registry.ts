import type { ComponentType } from 'react';

import type {
  LiveGuiPerformanceConsoleModelDict,
  PanelSpecDict,
} from '../../types/live_gui_protocol';
import { ShowKitForgePanel } from '../showKitForge/ShowKitForgePanel';
import { analyzerPanelSpec } from './analyzerPanel';
import { ConnectionDoctorPanel } from './ConnectionDoctorPanel';
import { KitMorphPanel } from './KitMorphPanel';
import { LibraryPanel } from './LibraryPanel';
import { LiveMidiMonitorPanel } from './LiveMidiMonitorPanel';
import { PanelRenderer } from './PanelRenderer';
import { ScopedRandomizationPanel } from './ScopedRandomizationPanel';
import { UpdatePanel } from './UpdatePanel';

/**
 * Schema-driven panel manifest. Adding a cockpit panel is one entry here:
 * an id, a layout region, and either
 *
 *   - `kind: 'model-selector'` — a pure selector
 *     (`console packet -> PanelSpecDict`) plus a component that takes a
 *     `spec` (almost always the generic `PanelRenderer`), or
 *   - `kind: 'store-slice'` — a self-contained panel that sources its own
 *     data from the cockpit store / WS client and renders its body through
 *     `PanelRenderer` internally.
 *
 * The second variant exists because several panels are *interactive* (they
 * own filters, forms, and command dispatch) and therefore cannot be derived
 * from the passive console packet alone. Before this variant existed those
 * panels were mounted by hand in `Cockpit.tsx`, which bypassed the very
 * extension seam the registry is for. Both variants are registered here so
 * `panelsForRegion` is the single source of truth for what the cockpit
 * mounts and where.
 *
 * See `.claude/skills/add-cockpit-panel/SKILL.md` for the full recipe.
 */

export type PanelRegion = 'topbar' | 'left-rail' | 'deck' | 'bottom';

/** A panel derived purely from the passive performance-console packet. */
export interface ModelSelectorPanelEntry {
  readonly kind: 'model-selector';
  readonly id: string;
  readonly region: PanelRegion;
  readonly selector: (model: LiveGuiPerformanceConsoleModelDict) => PanelSpecDict;
  readonly component: ComponentType<{ spec: PanelSpecDict }>;
}

/**
 * A self-contained panel that reads the cockpit store / WS client itself.
 *
 * The component type is deliberately `ComponentType` with no required props:
 * the host mounts it with nothing but a React `key`. (`Record<string, never>`
 * would be stricter but rejects `key` itself, since React threads it through
 * the same prop position.)
 */
export interface StoreSlicePanelEntry {
  readonly kind: 'store-slice';
  readonly id: string;
  readonly region: PanelRegion;
  readonly component: ComponentType;
}

export type PanelManifestEntry = ModelSelectorPanelEntry | StoreSlicePanelEntry;

export const PANEL_REGISTRY: ReadonlyArray<PanelManifestEntry> = [
  {
    kind: 'model-selector',
    id: 'analyzer',
    region: 'deck',
    selector: analyzerPanelSpec,
    component: PanelRenderer,
  },
  { kind: 'store-slice', id: 'live-midi-monitor', region: 'bottom', component: LiveMidiMonitorPanel },
  { kind: 'store-slice', id: 'connection-doctor', region: 'bottom', component: ConnectionDoctorPanel },
  { kind: 'store-slice', id: 'library', region: 'bottom', component: LibraryPanel },
  {
    kind: 'store-slice',
    id: 'scoped-randomization',
    region: 'bottom',
    component: ScopedRandomizationPanel,
  },
  { kind: 'store-slice', id: 'kit-morph', region: 'bottom', component: KitMorphPanel },
  // Bottom region, beside the Connection Doctor (spec §7).
  { kind: 'store-slice', id: 'updates', region: 'bottom', component: UpdatePanel },
  {
    kind: 'store-slice',
    id: 'show-kit-forge',
    region: 'bottom',
    component: ShowKitForgePanel,
  },
];

export function panelsForRegion(region: PanelRegion): ReadonlyArray<PanelManifestEntry> {
  return PANEL_REGISTRY.filter((entry) => entry.region === region);
}
