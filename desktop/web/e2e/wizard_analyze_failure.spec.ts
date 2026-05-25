/**
 * Analyzer failure surfaces in the UI as `failed` + a Retry button.
 *
 * Adds an audio source (`kind=sound`) pointing at a path that does not exist.
 * The Python sidecar's audio analyzer raises `WizardSourcePathError` (a
 * subclass of `FileNotFoundError`), which `_handle_wizard_analyze` traps and
 * turns into a job with `status="failed"`. The AnalyzeStep renders the
 * `failed` status and a Retry button (see `wizard-job-retry-<id>`).
 */

import { expect, test } from './fixtures/wizard_fixture';

test.describe('wizard analyze failure', () => {
  test('missing audio path → failed job + Retry button', async ({
    page,
    sidecar: _sidecar,
  }) => {
    test.setTimeout(45_000);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible();

    await page.getByTestId('mutation-panel-launch-wizard').click();
    await expect(page.getByTestId('wizard-name-step')).toBeVisible();

    await page.getByTestId('wizard-name-input').fill('analyze-failure-e2e');
    await page.getByTestId('wizard-next').click();
    await expect(page.getByTestId('wizard-add-step')).toBeVisible();

    // Add a sound source pointing at a bogus path. The draft starts in `file`
    // mode for `sound` (see DEFAULT_MODE_FOR_KIND in AddStep.tsx).
    await page.getByTestId('wizard-add-sound').click();
    await expect(page.getByTestId('wizard-draft')).toBeVisible();
    await page
      .getByTestId('wizard-draft-location')
      .fill('/definitely/does/not/exist/ghost.wav');
    await page.getByTestId('wizard-draft-display-name').fill('ghost.wav');
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

    // Review is disabled because no job is OK — guards against the operator
    // accidentally building an empty profile.
    await expect(page.getByTestId('wizard-next')).toBeDisabled();
  });
});
