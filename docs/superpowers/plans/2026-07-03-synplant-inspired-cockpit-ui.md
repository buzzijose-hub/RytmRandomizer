# Synplant-Inspired Cockpit UI Implementation Plan

Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a frontend-only Synplant-inspired `Patch Genome` cockpit surface without implementing the separate audio-to-patch intelligence layer.

**Architecture:** The new UI is a typed React component plus a small model file under `desktop/web/src/cockpit/`. It consumes deterministic design-preview data today and can later receive real patch genome data via props. It does not send MIDI, touch Python runtime behavior, or alter V1.34 parity surfaces.

**Tech Stack:** React 18, TypeScript 5, Vitest, Testing Library, existing cockpit CSS tokens.

---

## File Structure

- Create `desktop/web/src/cockpit/patchGenomeModel.ts`: typed model, default design data, and small selectors.
- Create `desktop/web/src/cockpit/PatchGenomePanel.tsx`: interactive frontend-only genome panel.
- Modify `desktop/web/src/cockpit/Cockpit.tsx`: insert panel into the side stack.
- Modify `desktop/web/src/cockpit/index.ts`: export panel and model surface.
- Modify `desktop/web/src/cockpit/styles.css`: add responsive styles using existing tokens.
- Create `desktop/web/tests/cockpit/patchGenomeModel.test.ts`: model behavior tests.
- Create `desktop/web/tests/cockpit/PatchGenomePanel.test.tsx`: component interaction tests.
- Modify `desktop/web/tests/cockpit/Cockpit.test.tsx`: top-level composition test.
- Create `docs/superpowers/specs/2026-07-03-synplant-inspired-cockpit-ui-design.md`: durable design spec.

### Task 1: Model Tests

**Files:**
- Create: `desktop/web/tests/cockpit/patchGenomeModel.test.ts`
- Create: `desktop/web/src/cockpit/patchGenomeModel.ts`

- [ ] **Step 1: Write failing model tests**

```ts
import { describe, expect, it } from 'vitest';

import {
  DEFAULT_PATCH_GENOME_MODEL,
  countReadyGenes,
  getPatchGenomeFamily,
} from '../../src/cockpit/patchGenomeModel';

describe('patchGenomeModel', () => {
  it('ships four named gene families for the cockpit design surface', () => {
    expect(DEFAULT_PATCH_GENOME_MODEL.families.map((family) => family.label)).toEqual([
      'Oscillators',
      'Envelope / LFO',
      'Filter / FX',
      'Performance',
    ]);
  });

  it('resolves a selected family by key', () => {
    expect(getPatchGenomeFamily(DEFAULT_PATCH_GENOME_MODEL, 'filter_fx')?.label).toBe(
      'Filter / FX',
    );
  });

  it('counts only ready genes as dry-run-ready', () => {
    const family = getPatchGenomeFamily(DEFAULT_PATCH_GENOME_MODEL, 'filter_fx');
    expect(family).toBeDefined();
    if (family === undefined) throw new Error('missing filter_fx family');
    expect(countReadyGenes(family.genes)).toBe(2);
  });
});
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
cd desktop/web
npm.cmd run test:run -- tests/cockpit/patchGenomeModel.test.ts
```

Expected: fail because `patchGenomeModel` does not exist yet.

- [ ] **Step 3: Implement the typed model**

Create `patchGenomeModel.ts` with exported types, `DEFAULT_PATCH_GENOME_MODEL`, `getPatchGenomeFamily`, and `countReadyGenes`.

- [ ] **Step 4: Run the model test to verify GREEN**

Run:

```bash
cd desktop/web
npm.cmd run test:run -- tests/cockpit/patchGenomeModel.test.ts
```

Expected: pass.

### Task 2: Panel Tests And Component

**Files:**
- Create: `desktop/web/tests/cockpit/PatchGenomePanel.test.tsx`
- Create: `desktop/web/src/cockpit/PatchGenomePanel.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`

- [ ] **Step 1: Write failing component tests**

```tsx
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PatchGenomePanel } from '../../src/cockpit/PatchGenomePanel';

describe('PatchGenomePanel', () => {
  it('renders the design-preview genome surface without send controls', () => {
    render(<PatchGenomePanel previewOn={false} />);
    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('Patch Genome');
    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('Analog Four MKII');
    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('Dry-run preview');
    expect(screen.queryByRole('button', { name: /send/i })).not.toBeInTheDocument();
  });

  it('switches selected gene families locally', () => {
    render(<PatchGenomePanel previewOn={true} />);
    fireEvent.click(screen.getByTestId('patch-genome-family-filter_fx'));
    expect(screen.getByTestId('patch-genome-selected-family')).toHaveTextContent('Filter / FX');
    expect(screen.getByTestId('patch-genome-selected-family')).toHaveTextContent('Filter 1 Frequency');
  });

  it('locks and unlocks individual genes without dispatching hardware actions', () => {
    render(<PatchGenomePanel previewOn={true} />);
    fireEvent.click(screen.getByTestId('patch-genome-family-filter_fx'));
    const gene = screen.getByTestId('patch-genome-gene-filter_freq');
    fireEvent.click(within(gene).getByRole('button', { name: /lock filter frequency/i }));
    expect(gene).toHaveTextContent('Locked locally');
    fireEvent.click(within(gene).getByRole('button', { name: /unlock filter frequency/i }));
    expect(gene).not.toHaveTextContent('Locked locally');
  });

  it('grows and resets local variants', () => {
    render(<PatchGenomePanel previewOn={true} />);
    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Variant 1');
    fireEvent.click(screen.getByRole('button', { name: 'Grow variant' }));
    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Variant 2');
    fireEvent.click(screen.getByRole('button', { name: 'Reset seed' }));
    expect(screen.getByTestId('patch-genome-variant')).toHaveTextContent('Variant 1');
  });
});
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
cd desktop/web
npm.cmd run test:run -- tests/cockpit/PatchGenomePanel.test.tsx
```

Expected: fail because `PatchGenomePanel` does not exist yet.

- [ ] **Step 3: Implement the component**

Create a pure React component with local selected-family, variant, and locked-gene state. It must not call `useCockpitClient` or send commands.

- [ ] **Step 4: Add CSS**

Add `.patch-genome-*` classes to `styles.css` using existing cockpit tokens and responsive constraints.

- [ ] **Step 5: Run the component test to verify GREEN**

Run:

```bash
cd desktop/web
npm.cmd run test:run -- tests/cockpit/PatchGenomePanel.test.tsx
```

Expected: pass.

### Task 3: Cockpit Wiring

**Files:**
- Modify: `desktop/web/src/cockpit/Cockpit.tsx`
- Modify: `desktop/web/src/cockpit/index.ts`
- Modify: `desktop/web/tests/cockpit/Cockpit.test.tsx`

- [ ] **Step 1: Write failing top-level composition assertion**

Add to `renders the root + HeaderBar + both panels`:

```ts
expect(screen.getByTestId('patch-genome-panel')).toBeInTheDocument();
```

- [ ] **Step 2: Run the Cockpit test to verify RED**

Run:

```bash
cd desktop/web
npm.cmd run test:run -- tests/cockpit/Cockpit.test.tsx
```

Expected: fail because the panel is not wired into `Cockpit`.

- [ ] **Step 3: Wire the component**

Import `PatchGenomePanel` in `Cockpit.tsx` and render it in `.cockpit-side-stack` before `MutationPanel`, passing `previewOn`.

- [ ] **Step 4: Export the component and model**

Update `index.ts` to export `PatchGenomePanel`, its props, model helpers, and model types.

- [ ] **Step 5: Run the focused cockpit tests to verify GREEN**

Run:

```bash
cd desktop/web
npm.cmd run test:run -- tests/cockpit/Cockpit.test.tsx tests/cockpit/PatchGenomePanel.test.tsx tests/cockpit/patchGenomeModel.test.ts
```

Expected: pass.

### Task 4: Verification And Docs

**Files:**
- Modify: `docs/STATUS.md` only if this branch's status convention can be followed without overwriting existing edits.

- [ ] **Step 1: Run frontend verification**

Run:

```bash
cd desktop/web
npm.cmd run test:run
npm.cmd run build
npm.cmd run lint
```

Expected: all pass.

- [ ] **Step 2: Run repo architecture/readme checks if docs changed**

Run:

```powershell
& '.venv\Scripts\python.exe' -m pytest tests/architecture/test_readme_freshness.py -q
```

Expected: pass.

- [ ] **Step 3: Review diff for scope**

Run:

```bash
git diff --stat
git diff -- desktop/web/src/cockpit desktop/web/tests/cockpit docs/assets/synplant-2-reference docs/superpowers/specs docs/superpowers/plans
```

Expected: new feature stays in frontend/docs surfaces and does not touch MIDI/parity surfaces.
