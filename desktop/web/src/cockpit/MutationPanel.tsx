/**
 * MutationPanel — right panel:
 *   ProfileToggle (Scene | Inspiration)
 *   ProfileChips (filtered by the toggle's kind)
 *   DepthSlider
 *   ActionBar
 */

import { useMemo, useState } from 'react';

import type { ProfileKind } from '../ws/protocol';

import { ActionBar } from './ActionBar';
import { DepthSlider } from './DepthSlider';
import { ProfileChips } from './ProfileChips';
import { ProfileToggle } from './ProfileToggle';

export interface MutationPanelProps {
  /** Catalogue of all profiles known to the cockpit. */
  availableProfiles: ReadonlyArray<{
    profile_id: string;
    name: string;
    kind: ProfileKind;
  }>;
  previewOn: boolean;
  onTogglePreview: (next: boolean) => void;
}

export function MutationPanel({
  availableProfiles,
  previewOn,
  onTogglePreview,
}: MutationPanelProps): JSX.Element {
  const [kind, setKind] = useState<ProfileKind>('scene');
  const filtered = useMemo(
    () => availableProfiles.filter((p) => p.kind === kind),
    [availableProfiles, kind],
  );

  return (
    <section className="cockpit-panel" data-testid="mutation-panel">
      <h2>Mutation Panel</h2>
      <ProfileToggle value={kind} onChange={setKind} />
      <ProfileChips available={filtered} />
      <DepthSlider />
      <ActionBar previewOn={previewOn} onTogglePreview={onTogglePreview} />
    </section>
  );
}
