import type { LiveGuiPerformanceConsoleModelDict } from '../../types/live_gui_protocol';
import type { PanelManifestEntry, PanelRegion } from './registry';
import { panelsForRegion } from './registry';

/**
 * Region renderer for the schema-driven panel registry: renders every
 * registered panel whose manifest entry targets `region`.
 *
 * `model-selector` entries are fed the `PanelSpecDict` their selector
 * derives from the passive console packet; `store-slice` entries are
 * self-contained and mount with no props. A `model-selector` entry in a
 * region rendered without a `model` is skipped rather than crashed — the
 * bottom rail has no console packet, and a missing packet is a data-flow
 * gap, not a reason to blank the whole region.
 */

export interface PanelHostProps {
  region: PanelRegion;
  model?: LiveGuiPerformanceConsoleModelDict;
}

function renderEntry(
  entry: PanelManifestEntry,
  model: LiveGuiPerformanceConsoleModelDict | undefined,
): JSX.Element | null {
  if (entry.kind === 'store-slice') {
    const Component = entry.component;
    return <Component key={entry.id} />;
  }
  if (model === undefined) return null;
  const Component = entry.component;
  return <Component key={entry.id} spec={entry.selector(model)} />;
}

export function PanelHost({ region, model }: PanelHostProps): JSX.Element {
  return <>{panelsForRegion(region).map((entry) => renderEntry(entry, model))}</>;
}
