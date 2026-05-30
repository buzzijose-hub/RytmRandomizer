/**
 * Analyzer failure surfaces in the UI as `failed` + a Retry button.
 *
 * Adds a filesystem source that is valid according to the sidecar path policy
 * but unsupported by the analyzer dispatcher (`kind=artist`, `mode=file`).
 * `_handle_wizard_analyze` traps the dispatcher's `ValueError` and turns it
 * into a job with `status="failed"`. The AnalyzeStep renders the `failed`
 * status and a Retry button (see `wizard-job-retry-<id>`).
 */

import { writeFileSync } from 'node:fs';
import * as path from 'node:path';

import { expect, test } from './fixtures/wizard_fixture';

test.describe('wizard analyze failure', () => {
  test('unsupported filesystem source -> failed job + Retry button', async ({
    page,
    sidecar,
  }) => {
    test.setTimeout(45_000);
    const unsupportedSource = path.join(sidecar.profilesRoot, 'unsupported-artist.bin');
    writeFileSync(unsupportedSource, 'not an analyzer-supported artist reference');

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible();

    await page.getByTestId('mutation-panel-launch-wizard').click();
    await expect(page.getByTestId('wizard-name-step')).toBeVisible();

    await page.getByTestId('wizard-name-input').fill('analyze-failure-e2e');
    await page.getByTestId('wizard-next').click();
    await expect(page.getByTestId('wizard-add-step')).toBeVisible();

    // Add an existing file path with an unsupported kind/mode pair. The sidecar
    // accepts the source, then the Analyze step reports the analyzer failure.
    await page.getByTestId('wizard-add-artist').click();
    await expect(page.getByTestId('wizard-draft')).toBeVisible();
    await page.getByTestId('wizard-draft-mode').selectOption('file');
    await page.getByTestId('wizard-draft-location').fill(unsupportedSource);
    await page.getByTestId('wizard-draft-display-name').fill('unsupported-artist.bin');
    await page.getByTestId('wizard-draft-confirm').click();

    // Wait for the sidecar to echo the server-minted source into the list before
    // advancing; the Analyze button is disabled while the source list is still empty.
    await expect(page.getByTestId('wizard-source-empty')).toBeHidden();

    await page.getByTestId('wizard-next').click();
    await expect(page.getByTestId('wizard-analyze-step')).toBeVisible();

    await page.getByTestId('wizard-analyze-start').click();

    // The job list eventually contains 'failed' (terminal status).
    await expect(page.getByTestId('wizard-job-list')).toContainText('failed', {
      timeout: 15_000,
    });

    // A Retry button is rendered for failed jobs. We don't know the
    // server-minted source_id, so address by the button's `Retry` text
    // inside the job list.
    await expect(
      page.getByTestId('wizard-job-list').getByRole('button', { name: 'Retry' }),
    ).toBeVisible();

    // Review is disabled because no job is OK - guards against the operator
    // accidentally building an empty profile.
    await expect(page.getByTestId('wizard-next')).toBeDisabled();
  });
});
