/**
 * Wizard kind strategy table — single source of truth for "what does the AddStep do
 * when the operator picks kind X?" Currently consolidates two facts:
 *
 *   - `label`       — the button caption (e.g. "+ kit")
 *   - `defaultMode` — the source mode the draft picker opens in (file / folder / reference)
 *
 * Phase 3+ will extend this with the picker variant (file picker vs reference text input)
 * so the AddStep can become a single table-driven render. For now both consumers in
 * AddStep.tsx import this dict instead of redefining KIND_LABELS / DEFAULT_MODE_FOR_KIND
 * locally — adding a new kind becomes one insertion here (plus the wizard_protocol.ts
 * union extension owned separately).
 */

import type { WizardSourceKind, WizardSourceMode } from '../types/wizard_protocol';

export interface KindStrategy {
  /** Caption shown on the "+ <kind>" button. */
  readonly label: string;
  /** Mode the draft form opens in when the operator picks this kind. */
  readonly defaultMode: WizardSourceMode;
}

export const KIND_STRATEGY: Readonly<Record<WizardSourceKind, KindStrategy>> = {
  kit: { label: '+ kit', defaultMode: 'file' },
  sound: { label: '+ sound', defaultMode: 'file' },
  song: { label: '+ song', defaultMode: 'file' },
  album: { label: '+ album', defaultMode: 'folder' },
  artist: { label: '+ artist', defaultMode: 'reference' },
};

/**
 * Display-order tuple of wizard kinds. The AddStep iterates this to render the kind
 * buttons in a stable order regardless of `Object.keys` iteration order. Kept in the
 * spec-declaration order from `wizard_protocol.ts` so the buttons match the protocol's
 * union order.
 */
export const KIND_DISPLAY_ORDER: ReadonlyArray<WizardSourceKind> = [
  'kit',
  'sound',
  'song',
  'album',
  'artist',
];
