/**
 * E2E: the I9 consent contract is pinned to its two normative sources.
 *
 * ## Why this file exists
 *
 * Contract I9 makes spec §7.1 normative for the consent prompt's labels,
 * element order, and default radio, and names a pixel render at
 * `docs/design/update-consent-prompt.html` as its companion ("if render and
 * spec ever disagree, this section wins"). Six other specs assert the panel
 * against the `CONSENT_LABELS` / `CONSENT_LABEL_ORDER` / `PANEL_COPY`
 * constants rather than inline strings — one edit reconciles them all.
 *
 * That centralization is only safe if something checks the constants
 * themselves. Six specs asserting three *wrong* strings is a worse outcome
 * than one failing spec, because nobody re-reads passing tests: the panel
 * would be verified against a confidently-formatted guess. This spec is that
 * check, and it needs no client, so it runs green today and keeps running
 * green as PR-B lands the UI.
 *
 * ### A note on a failure mode this file was written to close
 *
 * An earlier draft of these specs was authored against an obsolete revision
 * of the plan in which §7.1 did not exist. Its labels were reconstructed
 * from surrounding prose and were wrong ("Restart & install" for what §7.1
 * actually calls "Now — restart RytmRandomizer immediately"), and the radio
 * order was inverted. The assertions below are deliberately **unconditional**
 * — no `test.skip` guard on whether the source file happens to be present.
 * A missing normative source must fail this suite loudly, because "the spec
 * isn't here so we'll assume" is exactly how the wrong strings got written.
 */

import { existsSync, readFileSync } from 'node:fs';
import * as path from 'node:path';

import { expect, test } from '@playwright/test';

import {
  CONSENT_LABELS,
  CONSENT_LABEL_ORDER,
  DEFAULT_CONSENT_LABEL,
  PANEL_BODY_VARIANTS,
  PANEL_COPY,
} from './fixtures/update_fixture';
import { resolveRepoRootForManifest } from './fixtures/update_manifest';

/** I9's normative pixel render. */
const DESIGN_MOCKUP_RELPATH = 'docs/design/update-consent-prompt.html';
/** The spec §7.1 lives in — the tie-breaker when the two disagree. */
const SPEC_RELPATH = 'docs/superpowers/plans/2026-08-03-autoupdate-distribution.md';

/** Read a repo-relative normative source, failing loudly when it is absent. */
function readNormativeSource(relPath: string): string {
  const absolute = path.join(resolveRepoRootForManifest(), relPath);
  expect(
    existsSync(absolute),
    `${relPath} is a normative source for contract I9 and must exist`,
  ).toBe(true);
  return readFileSync(absolute, 'utf8');
}

/**
 * Collapse every run of whitespace to a single space.
 *
 * Both normative sources wrap: the spec hard-wraps its prose at ~70 columns
 * (so the frozen body's sentence spans two lines), and the HTML render
 * indents its markup. The UI strings themselves contain no newlines, so
 * comparing on collapsed whitespace asks the right question — "does the
 * source state this sentence?" — instead of "does the source happen to fit
 * it on one line?", which is a property of the author's text editor.
 */
function flattenWhitespace(text: string): string {
  return text.replace(/\s+/g, ' ');
}

/**
 * Position of `needle` in the whitespace-flattened `haystack`, asserted
 * present.
 *
 * Used to check §7.1's radio ORDER by document position. Order is part of
 * the contract, and a set-membership check would pass on a panel that
 * rendered the three labels upside down.
 */
function indexOfNormative(haystack: string, needle: string, source: string): number {
  const at = flattenWhitespace(haystack).indexOf(flattenWhitespace(needle));
  expect(at, `${source} must contain the normative label "${needle}"`).toBeGreaterThanOrEqual(0);
  return at;
}

/** Assert a normative source states `copy`, ignoring how the source wraps. */
function expectStates(source: string, copy: string, label: string): void {
  expect(flattenWhitespace(source), `${label} ("${copy}")`).toContain(flattenWhitespace(copy));
}

test.describe('I9 consent-contract reconciliation', () => {
  test('the label constants are internally consistent', () => {
    const labels = Object.values(CONSENT_LABELS);
    expect(new Set(labels).size, 'the three labels must be distinct').toBe(3);
    for (const label of labels) {
      expect(label.trim(), 'no stray whitespace in a normative label').toBe(label);
      expect(label.length).toBeGreaterThan(0);
    }
    // The order list is a permutation of the labels — not a second, drifting
    // source of truth for what the labels are.
    expect([...CONSENT_LABEL_ORDER].sort()).toEqual([...labels].sort());
    // D3: the calm default is the pre-selected one, and it leads the list.
    expect(DEFAULT_CONSENT_LABEL).toBe('When I quit the app');
    expect(CONSENT_LABEL_ORDER[0]).toBe(DEFAULT_CONSENT_LABEL);
  });

  test('the labels and their order match spec §7.1', () => {
    const spec = readNormativeSource(SPEC_RELPATH);
    // Guard the guard: if §7.1 ever moves or is renamed, this assertion is
    // what stops the label checks below from passing against unrelated prose
    // that happens to quote a label somewhere else in a 700-line document.
    expect(spec, 'spec §7.1 is the normative section for I9').toContain(
      '### 7.1 Consent prompt — normative mockup',
    );

    // §7.1 renders the radios as an ASCII mockup: `(•)` marks the default.
    expectStates(
      spec,
      `(•) ${DEFAULT_CONSENT_LABEL}`,
      'the §7.1 mockup pre-selects the default radio',
    );
    for (const label of CONSENT_LABEL_ORDER) {
      if (label === DEFAULT_CONSENT_LABEL) continue;
      expectStates(spec, `( ) ${label}`, `§7.1 offers "${label}" as an unselected radio`);
    }

    // Order, by document position.
    const positions = CONSENT_LABEL_ORDER.map((label) => indexOfNormative(spec, label, '§7.1'));
    expect(positions, '§7.1 orders the radios quit → now → skip').toEqual(
      [...positions].sort((a, b) => a - b),
    );
  });

  test('the panel chrome and body variants match spec §7.1', () => {
    const spec = readNormativeSource(SPEC_RELPATH);
    for (const [key, copy] of Object.entries(PANEL_COPY)) {
      expectStates(spec, copy, `§7.1 must contain PANEL_COPY.${key}`);
    }
    // The two verbatim body variants. The other two are prefixes because
    // §7.1 interpolates a version / a reason code into them; asserting the
    // prefix is the strongest check that does not encode a placeholder.
    for (const [key, copy] of Object.entries(PANEL_BODY_VARIANTS)) {
      expectStates(spec, copy, `§7.1 must contain PANEL_BODY_VARIANTS.${key}`);
    }
  });

  test('the labels match the I9 pixel render', () => {
    const mockup = readNormativeSource(DESIGN_MOCKUP_RELPATH);
    for (const label of CONSENT_LABEL_ORDER) {
      expectStates(mockup, label, 'the render must show');
    }
    // Same order in the render as in the spec. I9 says the spec wins on a
    // disagreement — this assertion is how a disagreement becomes visible
    // instead of being silently resolved by whichever one a reader opened.
    const positions = CONSENT_LABEL_ORDER.map((label) =>
      indexOfNormative(mockup, label, DESIGN_MOCKUP_RELPATH),
    );
    expect(positions, 'the render orders the radios quit → now → skip').toEqual(
      [...positions].sort((a, b) => a - b),
    );

    // The render also carries the panel chrome; checking it here means a
    // future redesign that drops "What's new" cannot land unnoticed.
    for (const [key, copy] of Object.entries(PANEL_COPY)) {
      expectStates(mockup, copy, `the render must show PANEL_COPY.${key}`);
    }
  });
});
