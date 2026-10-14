/** Actual analysis, retained native files and browser UI; never instrument evidence. */
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import * as path from 'node:path';

import type { ReferenceSoundSession } from '../src/ws/referenceSound';
import { trackConsoleErrors, WS_DIAL_FAILURE } from './fixtures/console_guard';
import { expect, injectTokenLive, primeToken, resolveRepoRoot, test } from './fixtures/wizard_fixture';

test.use({ actionTimeout: 10_000 });

function pcmTone(frequency: number, secondHarmonic = 0): Buffer {
  const count = 55125;
  const audio = Buffer.alloc(44 + count * 2);
  audio.write('RIFF'); audio.writeUInt32LE(audio.length - 8, 4); audio.write('WAVEfmt ', 8);
  audio.writeUInt32LE(16, 16); audio.writeUInt16LE(1, 20); audio.writeUInt16LE(1, 22);
  audio.writeUInt32LE(22050, 24); audio.writeUInt32LE(44100, 28);
  audio.writeUInt16LE(2, 32); audio.writeUInt16LE(16, 34); audio.write('data', 36);
  audio.writeUInt32LE(count * 2, 40);
  for (let index = 0; index < count; index++) {
    const phase = 2 * Math.PI * frequency * index / 22050;
    audio.writeInt16LE(Math.round(16000 * (Math.sin(phase) + secondHarmonic * Math.sin(2 * phase))), 44 + index * 2);
  }
  return audio;
}

test('both native reference paths retain exact audio, scope, recordings and favorites across restart', async ({ page, sidecarControl }, testInfo) => {
  // Six bounded analysis operations may each take up to the worker's 60s limit.
  test.setTimeout(420_000);
  const guard = trackConsoleErrors(page, [WS_DIAL_FAILURE]);
  const sessions: ReferenceSoundSession[] = [];
  const commands: string[] = [];
  page.on('websocket', (socket) => {
    socket.on('framesent', ({ payload }) => {
      const frame = JSON.parse(String(payload)) as { command?: { type: string } };
      if (frame.command) commands.push(frame.command.type);
    });
    socket.on('framereceived', ({ payload }) => {
      const frame = JSON.parse(String(payload)) as { reference_sound?: { session?: ReferenceSoundSession }; ok?: boolean };
      if (frame.ok && frame.reference_sound?.session) sessions.push(frame.reference_sound.session);
    });
  });
  const repo = resolveRepoRoot();
  const cwd = path.join(sidecarControl.tmpRoot, 'work');
  mkdirSync(path.join(cwd, 'captures'), { recursive: true });
  for (const name of ['RYTM_RIO145_AR_CORE_RETURN_Kit.syx', 'A4_RIO145_CORE_RETURN_Kit.syx']) copyFileSync(path.join(repo, 'tests', 'fixtures', 'rio145', name), path.join(cwd, 'captures', name));
  const env = { RYTM_RAND_MIDI_BACKEND: 'off', HOME: sidecarControl.tmpRoot, PYTHONPATH: repo };
  const first = await sidecarControl.start({ env, cwd, onToken: (token) => primeToken(page, token) });
  await page.goto('/');
  await expect(page.getByTestId('safety-rail').getByText('Hardware Off')).toBeVisible();
  const panel = page.getByTestId('reference-sound-panel');
  await expect(panel).toBeVisible();
  await panel.getByRole('button', { name: 'Open reference sound' }).click();
  await panel.getByRole('button', { name: 'Import captures', exact: true }).click();
  await expect(panel.getByRole('combobox', { name: 'Source Library record', exact: true }).locator('option')).toHaveCount(2);
  const retained: ReferenceSoundSession[] = [];
  for (const [device, target, parameter] of [['analog_rytm_mk2', 2, 'filter_frequency'], ['analog_four_mk2', 3, 'filter1_frequency']] as const) {
    const audio = pcmTone(440);
    await panel.getByLabel('Original WAV', { exact: true }).setInputFiles({ name: `${device}.wav`, mimeType: 'audio/wav', buffer: audio });
    await expect.poll(() => sessions.at(-1)?.title).toBe(`${device}.wav`);
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    await expect(panel.getByLabel('Original reference playback')).toBeVisible();
    expect(sessions.at(-1)!.segment.original.sha256).toBe(createHash('sha256').update(audio).digest('hex'));
    await panel.getByLabel('Start frame', { exact: true }).fill('2205');
    await panel.getByLabel('Frame count', { exact: true }).fill('44100');
    await panel.getByRole('button', { name: 'Retain segment', exact: true }).click();
    await expect.poll(() => sessions.at(-1)!.segment.start_frame).toBe(2205);
    expect(sessions.at(-1)!.segment.frame_count).toBe(44100);
    await panel.getByRole('combobox', { name: 'Device', exact: true }).selectOption(device);
    await panel.getByRole('combobox', { name: 'Source Library record', exact: true }).selectOption({ index: 1 });
    await panel.getByLabel(device === 'analog_four_mk2' ? 'Target track' : 'Target pad', { exact: true }).fill(String(target));
    await expect(panel.getByLabel(`Mutate ${parameter}`, { exact: true })).toBeEnabled();
    for (const field of await panel.getByRole('checkbox', { name: /^Mutate / }).all()) if (await field.isEnabled() && await field.isChecked()) await field.uncheck();
    await panel.getByLabel(`Mutate ${parameter}`, { exact: true }).check();
    await panel.getByRole('button', { name: 'Generate eight alternatives', exact: true }).click();
    await expect(panel.getByRole('group', { name: 'Native alternatives' }).getByRole('radio')).toHaveCount(8, { timeout: 65_000 });
    const generated = sessions.at(-1)!;
    expect(generated.context!.parameters).toEqual([parameter]);
    expect(generated.context!.target).toBe(target);
    expect(generated.candidates.every((item) => item.hardware_send_validated === false && item.roundtrip_redecoded && item.changes.every((change) => change.parameter === parameter))).toBe(true);
    await expect(panel.getByRole('table', { name: 'Exact native changes', exact: true })).toBeVisible();
    await panel.getByRole('button', { name: 'Favorite candidate', exact: true }).click();
    await expect(panel.getByRole('button', { name: 'Remove favorite', exact: true })).toBeVisible();
    await panel.getByLabel('Supplied candidate recording WAV (0.05-8s)', { exact: true }).setInputFiles({ name: 'synthetic-comparison.wav', mimeType: 'audio/wav', buffer: pcmTone(880) });
    await expect.poll(() => sessions.at(-1)!.recordings.length, { timeout: 65_000 }).toBe(1);
    expect(sessions.at(-1)!.recordings[0]!.physical_validation).toBe(false);
    expect(sessions.at(-1)!.recordings[0]!.pitch_comparison!.support_status).toBe('held');
    expect(sessions.at(-1)!.recordings[0]!.pitch_comparison!.blockers).toContain('pitch_mismatch');
    expect(sessions.at(-1)!.recordings[0]!.pitch_comparison!.octave_difference).toBe(1);
    await expect(panel.getByRole('button', { name: 'Refine candidate (0/3)', exact: true })).toBeDisabled();
    await expect(panel.getByRole('table', { name: 'Controlled audition diagnostics', exact: true })).toBeVisible();
    await expect(panel.getByRole('table', { name: 'Measured reference and supplied recording (normalized 0-1)' })).toBeVisible();
    await panel.getByLabel('Supplied candidate recording WAV (0.05-8s)', { exact: true }).setInputFiles({ name: 'synthetic-same-pitch-timbre.wav', mimeType: 'audio/wav', buffer: pcmTone(440, 0.25) });
    await expect.poll(() => sessions.at(-1)!.recordings.length, { timeout: 65_000 }).toBe(2);
    expect(sessions.at(-1)!.recordings[1]!.pitch_comparison!.support_status).toBe('supported');
    expect(sessions.at(-1)!.recordings[1]!.pitch_comparison!.blockers).toEqual([]);
    await expect(panel.getByRole('button', { name: 'Refine candidate (0/3)', exact: true })).toBeEnabled();
    await panel.getByRole('button', { name: 'Refine candidate (0/3)', exact: true }).click();
    await expect.poll(() => sessions.at(-1)!.refinements.length, { timeout: 65_000 }).toBe(1);
    await panel.getByLabel('Scratch KIT slot (1-128)', { exact: true }).fill('128');
    const downloadPromise = page.waitForEvent('download');
    await panel.getByRole('button', { name: 'Download .syx', exact: true }).click();
    const download = await downloadPromise;
    const downloadedPath = await download.path();
    expect(downloadedPath).not.toBeNull();
    const sysex = readFileSync(downloadedPath!);
    expect(sysex[0]).toBe(0xf0); expect(sysex.at(-1)).toBe(0xf7);
    expect([...sysex.subarray(1, -1)].every((byte) => byte < 128)).toBe(true);
    retained.push(structuredClone(sessions.at(-1)!));
    await expect(page.getByTestId('action-send')).toBeDisabled();
  }
  await page.setViewportSize({ width: 600, height: 900 });
  await panel.scrollIntoViewIfNeeded();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('reference-sound-narrow.png') });
  await sidecarControl.stop();
  await sidecarControl.start({ env, cwd, previousToken: first.token, onToken: (token) => injectTokenLive(page, token) });
  await expect(page.getByTestId('safety-rail').getByText('Connected', { exact: true })).toBeVisible({ timeout: 30_000 });
  await panel.getByRole('button', { name: 'Refresh sessions', exact: true }).click();
  for (const session of retained) {
    await panel.getByRole('combobox', { name: 'Retained session', exact: true }).selectOption(session.session_id);
    await panel.getByRole('button', { name: 'Reopen session', exact: true }).click();
    await expect.poll(() => sessions.at(-1)!.session_id).toBe(session.session_id);
    expect(sessions.at(-1)).toEqual(session);
    await expect(page.getByTestId('action-send')).toBeDisabled();
    await expect(page.getByTestId('safety-rail').getByText('Hardware Off')).toBeVisible();
  }
  expect(commands.some((command) => ['arm', 'send', 'save', 'capture_current_kit', 'list_capture_inputs'].includes(command))).toBe(false);
  guard.assertClean();
});
