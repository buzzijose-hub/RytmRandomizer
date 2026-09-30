import { useEffect, type RefObject } from 'react';

import type { CockpitClient } from '../ws/client';

interface PhysicalActions {
  enabled: () => boolean;
  mutate: () => void;
  undo: () => void;
  anchor: () => void;
}

function visibleControls(root: HTMLElement): HTMLElement[] {
  const surface = root.querySelector<HTMLElement>('[role="dialog"]') ?? root;
  const bounds = surface.getBoundingClientRect();
  return [...surface.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], select:not([disabled])')].filter((control) => {
    const rect = control.getBoundingClientRect();
    const clip = control.closest('.appliance-content')?.getBoundingClientRect() ?? bounds;
    return rect.width >= 44 && rect.height >= 44 && rect.bottom > Math.max(0, clip.top) && rect.top < Math.min(window.innerHeight, clip.bottom) && rect.right > Math.max(0, clip.left) && rect.left < Math.min(window.innerWidth, clip.right);
  });
}

/** Optional configured input uses the exact touch actions. It cannot confirm output authority. */
export function usePhysicalControls(client: CockpitClient, root: RefObject<HTMLElement>, actions: PhysicalActions): void {
  useEffect(() => client.on('appliance_control_intent', (intent) => {
    if (intent.source !== 'physical_input' || !Number.isSafeInteger(intent.delta) || Math.abs(intent.delta) > 32 || !actions.enabled() || root.current === null) return;
    if (root.current.querySelector('[role="dialog"]') !== null && ['mutate', 'undo', 'capture_anchor'].includes(intent.action)) return;
    if (intent.action === 'mutate') { actions.mutate(); return; }
    if (intent.action === 'undo') { actions.undo(); return; }
    if (intent.action === 'capture_anchor') { actions.anchor(); return; }
    const controls = visibleControls(root.current);
    if (controls.length === 0) return;
    const focused = document.activeElement as HTMLElement;
    if (intent.action === 'activate_focus') {
      if (controls.includes(focused) && focused.dataset.applianceConfirmation !== 'true') focused.click();
      return;
    }
    if (intent.delta === 0) return;
    const current = controls.indexOf(focused);
    const origin = current >= 0 ? current : intent.delta > 0 ? -1 : 0;
    const index = ((origin + intent.delta) % controls.length + controls.length) % controls.length;
    controls[index]!.focus();
  }), [client, root, actions]);
}
