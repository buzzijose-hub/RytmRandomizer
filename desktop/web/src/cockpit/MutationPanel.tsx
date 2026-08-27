/**
 * MutationPanel — right panel:
 *   ProfileToggle (Scene | Inspiration)
 *   ProfileChips (filtered by the toggle's kind)
 *   DepthSlider
 *   ActionBar
 */

import { useMemo, useState } from 'react';

import { useCockpitStore } from '../state';
import type { ProfileKind } from '../ws/protocol';

import { ActionBar } from './ActionBar';
import { DepthSlider } from './DepthSlider';
import { ProfileChips } from './ProfileChips';
import { ProfileToggle } from './ProfileToggle';
import { StyleCrateQueue } from './StyleCrateQueue';

export interface MutationPanelProps {
  previewOn: boolean;
  onTogglePreview: (next: boolean) => void;
  /**
   * Optional override for the wizard launcher's navigation. Defaults to setting
   * `window.location.hash = '/wizard'` so the Tauri shell's hash router can route to it.
   * Tests inject a spy.
   */
  onLaunchWizard?: () => void;
}

export function MutationPanel({
  previewOn,
  onTogglePreview,
  onLaunchWizard,
}: MutationPanelProps): JSX.Element {
  const availableProfiles = useCockpitStore((state) => state.profileCatalog);
  const [kind, setKind] = useState<ProfileKind>('scene');
  const filtered = useMemo(
    () => availableProfiles.filter((p) => p.kind === kind),
    [availableProfiles, kind],
  );

  const handleLaunchWizard = (): void => {
    if (onLaunchWizard !== undefined) {
      onLaunchWizard();
      return;
    }
    window.location.hash = '/wizard';
  };

  return (
    <section className="cockpit-panel" data-testid="mutation-panel">
      <div className="mutation-panel-heading">
        <div>
          <p className="panel-kicker">Registry synced</p>
          <h2>Live Profile Catalog</h2>
        </div>
        <span>{availableProfiles.length} profiles</span>
      </div>
      <ProfileToggle value={kind} onChange={setKind} />
      <ProfileChips available={filtered} />
      <button
        type="button"
        className="wizard-launcher"
        data-testid="mutation-panel-launch-wizard"
        onClick={handleLaunchWizard}
      >
        + Create profile…
      </button>
      <StyleCrateQueue />
      <DepthSlider />
      <ActionBar previewOn={previewOn} onTogglePreview={onTogglePreview} />
    </section>
  );
}
