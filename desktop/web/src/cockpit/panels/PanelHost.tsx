import type { LiveGuiPerformanceConsoleModelDict } from '../../types/live_gui_protocol';
import type { PanelRegion } from './registry';
import { panelsForRegion } from './registry';

/**
 * Region renderer for the schema-driven panel registry: renders every
 * registered panel whose manifest entry targets `region`, feeding each
 * component the `PanelSpecDict` its selector derives from the passive
 * console packet.
 */

export interface PanelHostProps {
  region: PanelRegion;
  model: LiveGuiPerformanceConsoleModelDict;
}

export function PanelHost({ region, model }: PanelHostProps) {
  return (
    <>
      {panelsForRegion(region).map(({ id, selector, component: Component }) => (
        <Component key={id} spec={selector(model)} />
      ))}
    </>
  );
}
