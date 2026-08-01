/**
 * DemoDataBanner — the honesty label for panels that are a *static
 * demonstration*, not a live view of device or backend state.
 *
 * Why this exists: the scoped-randomization and kit-morph panels recompute
 * their plans in TypeScript over a committed demo fixture
 * (`scopeMorphDemoData.json`). Cross-language parity with the Python engines
 * is pinned by `scopeMorphParity.test.ts`, but only for the specific
 * mask/depth combinations that fixture covers — the slider and mask toggles
 * let the operator reach states no backend ever computed. Rendering those
 * numbers with no label would present client-side arithmetic over canned data
 * as if it were the device's prepared plan.
 *
 * So the panel says so, in the UI, where the operator reads it: this is a
 * demonstration of the interaction, the values are illustrative, and nothing
 * here is armed, sent, or derived from the connected instrument. Replace the
 * banner (not just hide it) when the panel is wired to a real backend-computed
 * plan.
 *
 * `role="note"` + the visible text keeps it in the accessibility tree without
 * claiming alert urgency; it is not colour-only.
 */

import './panel.css';

export interface DemoDataBannerProps {
  /** What the panel demonstrates, e.g. "scoped randomization". */
  readonly what: string;
  /** Stable testid suffix so each host panel can assert its own banner. */
  readonly testId: string;
}

export function DemoDataBanner({ what, testId }: DemoDataBannerProps): JSX.Element {
  return (
    <p className="cockpit-panel-demo-banner" role="note" data-testid={testId}>
      <strong>Static demonstration.</strong> This panel demonstrates {what} using fixed sample
      data, not your connected instrument. The values are computed in the app for illustration
      and are not a prepared send plan — nothing here is armed or transmitted.
    </p>
  );
}
