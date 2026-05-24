/**
 * Happy path — Name → Add → Analyze → Review → Save.
 *
 * Uses `kind=artist` + `mode=reference` so no audio file fixtures are needed:
 * the reference analyzer looks up the text against a curated table
 * (`reference_analyzer.py`) and returns a non-neutral trait tuple for known
 * names like "Surgeon". This keeps the test self-contained.
 *
 * After save, the wizard navigates back to the cockpit and the sidecar
 * emits `profile_created` + `profile_changed`. The cockpit renders the
 * active profile card with the new name; we assert on that card rather
 * than the chip list because the chip list is sourced from a static
 * `DEFAULT_AVAILABLE_PROFILES` constant (see `Cockpit.tsx`) and is not
 * refreshed from the sidecar's registry in Phase 2.
 */

import { expect, test } from './fixtures/wizard_fixture';

const PROFILE_NAME = 'buzzi-e2e';

test.describe('wizard happy path', () => {
  test('Name → Add → Analyze → Review → Save creates a new profile', async ({
    page,
    sidecar: _sidecar,
  }) => {
    test.setTimeout(60_000); // analyze + save round-trips push past the 30s default

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible();

    // ----- Launch the wizard -----
    await page.getByTestId('mutation-panel-launch-wizard').click();
    await expect(page.getByTestId('wizard-root')).toBeVisible();
    await expect(page.getByTestId('wizard-name-step')).toBeVisible();

    // ----- Name step -----
    await page.getByTestId('wizard-name-input').fill(PROFILE_NAME);
    await page.getByTestId('wizard-next').click();
    await expect(page.getByTestId('wizard-add-step')).toBeVisible();

    // ----- Add step: kind=artist, mode=reference, location/name="Surgeon" -----
    await page.getByTestId('wizard-add-artist').click();
    await expect(page.getByTestId('wizard-draft')).toBeVisible();
    await page.getByTestId('wizard-draft-location').fill('Surgeon');
    await page.getByTestId('wizard-draft-display-name').fill('Surgeon');
    await page.getByTestId('wizard-draft-confirm').click();

    // The draft closes once accepted; the new source shows up in the list.
    await expect(page.getByTestId('wizard-source-empty')).toBeHidden();

    await page.getByTestId('wizard-next').click();
    await expect(page.getByTestId('wizard-analyze-step')).toBeVisible();

    // ----- Analyze step -----
    await page.getByTestId('wizard-analyze-start').click();

    // Wait for the (single) job to reach 'ok'. The status text is rendered
    // by AnalyzeStep using `data-testid="wizard-job-status-<source_id>"`,
    // but the source id is server-minted so we can't address it directly.
    // Instead, look for "ok" inside the job list (only the terminal status
    // is "ok"; the others are "pending" / "analyzing" / "failed").
    await expect(page.getByTestId('wizard-job-list')).toContainText('ok', {
      timeout: 15_000,
    });

    await page.getByTestId('wizard-next').click();
    await expect(page.getByTestId('wizard-review-step')).toBeVisible();

    // The review header renders the profile name.
    await expect(
      page.getByTestId('wizard-review-step').getByRole('heading', { name: PROFILE_NAME }),
    ).toBeVisible();

    // ----- Save → cockpit -----
    await page.getByTestId('wizard-save').click();

    // Wizard.tsx navigates to `#/` once `profile_created` arrives, and the
    // cockpit re-mounts because the App-level routing should switch panels.
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    // The newly-saved profile becomes the active profile — its card appears
    // in MutationPanel (rendered by ProfileChips' ActiveProfileCard).
    await expect(page.getByTestId('profile-active-card')).toBeVisible();
    await expect(page.getByTestId('profile-active-card')).toContainText(PROFILE_NAME);
  });
});
