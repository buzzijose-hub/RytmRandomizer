/** Bounded, one-browser acceptance against the production appliance runtime.
 * Usage: node scripts/appliance-visual-qa.mjs <private launch.html> <output directory> <runtime source SHA> [simulation|production]
 * The private bootstrap is navigated without reading, printing or copying its secrets.
 */
import { chromium } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const bootstrap = process.argv[2];
const output = process.argv[3];
const sourceSha = process.argv[4];
const mode = process.argv[5] ?? 'simulation';
if (!bootstrap || !output || !/^[a-f0-9]{40}$/.test(sourceSha ?? '')) throw new Error('Expected private launch.html path, screenshot output directory and exact runtime source SHA.');
if (!['simulation', 'production'].includes(mode)) throw new Error('Expected explicit simulation or production mode.');
const directory = resolve(output);
mkdirSync(directory, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 800, height: 480 }, hasTouch: true, reducedMotion: 'reduce' });
const page = await context.newPage();
page.setDefaultTimeout(12000);
const browserErrors = [];
page.on('pageerror', (error) => { browserErrors.push(error.name); });
const receipts = [];

async function clickNav(label) {
  await page.getByRole('navigation', { name: 'Appliance pages' }).getByRole('button', { name: label, exact: true }).click();
  await page.getByRole('status').filter({ has: page.locator('p') }).waitFor();
  await page.waitForFunction(() => !document.querySelector('.appliance-notice')?.textContent?.includes('BUSY'));
}
async function check(name, width, height) {
  const metrics = await page.evaluate(() => {
    const root = document.querySelector('.appliance');
    const surface = document.querySelector('[role="dialog"]') ?? root;
    const boxes = [...surface.querySelectorAll('button, select, a[href]')].map((element) => {
      const rect = element.getBoundingClientRect();
      const clip = element.closest('.appliance-dialog-body, .appliance-content')?.getBoundingClientRect() ?? { top: 0, bottom: innerHeight, left: 0, right: innerWidth };
      return { label: element.textContent?.trim().slice(0, 50), width: Math.round(rect.width), height: Math.round(rect.height), visible: rect.height > 0 && rect.bottom > Math.max(0, clip.top) && rect.top < Math.min(innerHeight, clip.bottom) && rect.right > 0 && rect.left < innerWidth };
    }).filter((box) => box.visible);
    const dialog = document.querySelector('[role="dialog"]');
    const modalChromeFailures = dialog ? [...dialog.querySelectorAll(':scope > header h2, :scope > header button, :scope > footer button')].filter((element) => {
      const rect = element.getBoundingClientRect();
      const bounds = dialog.getBoundingClientRect();
      return rect.height <= 0 || rect.top < Math.max(0, bounds.top) - .5 || rect.bottom > Math.min(innerHeight, bounds.bottom) + .5 || rect.left < Math.max(0, bounds.left) - .5 || rect.right > Math.min(innerWidth, bounds.right) + .5;
    }).map((element) => element.textContent?.trim()) : [];
    const body = dialog?.querySelector('.appliance-dialog-body');
    if (dialog) {
      const header = dialog.querySelector(':scope > header');
      const footer = dialog.querySelector(':scope > footer');
      if (!header || !body || !footer?.querySelector('button')) modalChromeFailures.push('Missing fixed dialog header/body/actions');
      else if (body.getBoundingClientRect().top < header.getBoundingClientRect().bottom - .5 || body.getBoundingClientRect().bottom > footer.getBoundingClientRect().top + .5) modalChromeFailures.push('Dialog body overlaps fixed controls');
    }
    return { viewport: [innerWidth, innerHeight], documentWidth: document.documentElement.scrollWidth, applianceWidth: root.scrollWidth, touchFailures: boxes.filter((box) => box.width < 44 || box.height < 44), visibleTouchControls: boxes.length, modalChromeFailures, modalBodyScroll: body ? { top: body.scrollTop, height: body.clientHeight, contentHeight: body.scrollHeight } : null, pixelFontLoaded: [...document.fonts].some((font) => font.family === 'Appliance Pixel' && font.status === 'loaded') };
  });
  const screenshot = `${name}-${width}x${height}.png`;
  await page.screenshot({ path: resolve(directory, screenshot), fullPage: false });
  receipts.push({ screenshot, ...metrics });
  if (metrics.documentWidth > width || metrics.applianceWidth > width || metrics.touchFailures.length || metrics.modalChromeFailures.length || !metrics.pixelFontLoaded) {
    throw new Error(`Visual/touch check failed: ${JSON.stringify({ screenshot, ...metrics })}`);
  }
}
async function checkFullyVisible(locator) {
  const visible = await locator.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const clip = element.closest('.appliance-dialog-body, .appliance-content').getBoundingClientRect();
    return rect.height > 0 && rect.top >= Math.max(0, clip.top) - .5 && rect.bottom <= Math.min(innerHeight, clip.bottom) + .5 && rect.left >= 0 && rect.right <= innerWidth;
  });
  if (!visible) throw new Error(`Required capture evidence is clipped: ${await locator.textContent()}`);
}
async function checkTargetMatrix(expectedCount) {
  const result = await page.evaluate(() => {
    const surface = document.querySelector('.appliance-dialog-body') ?? document.querySelector('.appliance-content');
    const clip = surface.getBoundingClientRect();
    const targets = [...surface.querySelectorAll('.appliance-target-grid > button')].filter((button) => button.getBoundingClientRect().height > 0);
    return { count: targets.length, clipped: targets.some((button) => {
      const rect = button.getBoundingClientRect();
      return rect.top < Math.max(0, clip.top) || rect.bottom > Math.min(innerHeight, clip.bottom) || rect.left < 0 || rect.right > innerWidth;
    }) };
  });
  if (result.count !== expectedCount || result.clipped) throw new Error(`Target matrix visibility failed: ${JSON.stringify(result)}`);
}
try {
  await page.goto(pathToFileURL(resolve(bootstrap)).href);
  await page.getByRole('heading', { name: 'HOME / PERFORM' }).waitFor();
  await page.getByText(mode === 'simulation' ? 'SIMULATION / NO MIDI' : 'PASSIVE / DISARMED', { exact: true }).waitFor();
  await page.evaluate(() => document.fonts.ready);
  if (mode === 'production') {
    for (const [width, height] of [[800, 480], [480, 320], [1024, 600]]) {
      await page.setViewportSize({ width, height });
      await clickNav('RYTM');
      await clickNav('HOME');
      if (!await page.getByRole('button', { name: 'APPLY…', exact: true }).isDisabled()) throw new Error('Disconnected production apply must be blocked.');
      await check('production-disconnected-home', width, height);
      if (width >= 650) await checkTargetMatrix(12);
      for (const label of ['RYTM', 'A4', 'BOTH']) {
        await clickNav(label);
        await check(`production-disconnected-${label.toLowerCase()}`, width, height);
      }
      await clickNav('MORE');
      await page.getByRole('button', { name: 'CAPTURE', exact: true }).click();
      const blocker = page.getByText('Capture input is unavailable. Scan inputs or launch with the passive capture provider.', { exact: true });
      await blocker.waitFor();
      const scan = page.getByRole('button', { name: 'SCAN INPUTS', exact: true });
      await scan.evaluate((element) => element.scrollIntoView({ block: 'start' }));
      await checkFullyVisible(scan);
      await checkFullyVisible(page.getByRole('button', { name: 'RESYNC APP STATE', exact: true }));
      await check('production-capture-controls', width, height);
      const listen = page.getByRole('button', { name: 'LISTEN FOR KIT CAPTURE', exact: true });
      if (!await listen.isDisabled()) throw new Error('Unavailable capture must be blocked.');
      await listen.evaluate((element) => element.scrollIntoView({ block: 'start' }));
      await checkFullyVisible(listen);
      await checkFullyVisible(blocker);
      await check('production-capture-unavailable', width, height);
      await page.getByRole('button', { name: 'DIAGNOSTICS', exact: true }).click();
      await check('production-diagnostics', width, height);
      if (await page.getByText(/SIMULATION \/ NO MIDI|SIMULATED 7-BIT VALUES/).count()) throw new Error('Production disconnected state displayed simulated authority.');
    }
  } else {
  for (const [width, height] of [[800, 480], [480, 320], [1024, 600]]) {
    await page.setViewportSize({ width, height });
    await clickNav('RYTM');
    await clickNav('HOME');
    await check('home', width, height);
    if (width >= 650) await checkTargetMatrix(12);
    if (width < 650) {
      await page.getByRole('button', { name: /RYTM TARGETS|A4 TARGETS/ }).first().click();
      await check('compact-target-picker', width, height);
      await checkTargetMatrix(12);
      await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
    }
    await clickNav('RYTM');
    await check('rytm-targets', width, height);
    await page.getByRole('button', { name: 'PAGES', exact: true }).click();
    await check('rytm-pages', width, height);
    await page.getByRole('button', { name: 'PROTECT', exact: true }).click();
    await check('rytm-protection', width, height);
    await clickNav('A4');
    await check('a4-targets', width, height);
    await clickNav('BOTH');
    await check('both', width, height);
    await clickNav('HISTORY');
    await check('history', width, height);
    await page.getByRole('button', { name: 'NEW ANCHOR…', exact: true }).click();
    await check('anchor-confirmation', width, height);
    await page.getByRole('button', { name: 'CANCEL', exact: true }).click();
    await clickNav('MORE');
    await page.getByRole('button', { name: 'PROFILES', exact: true }).click();
    await check('profiles', width, height);
    await page.getByRole('button', { name: 'NAME: PERFORMANCE 1', exact: true }).click();
    await check('touch-keyboard', width, height);
    await page.locator('.appliance-dialog-body').evaluate((body) => { body.scrollTop = body.scrollHeight; });
    await check('touch-keyboard-scrolled', width, height);
    await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
    await page.getByRole('button', { name: 'CAPTURE', exact: true }).click();
    await page.getByRole('button', { name: 'SCAN INPUTS', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('.appliance-notice')?.textContent?.includes('BUSY'));
    await check('capture-blocked', width, height);
    await page.getByRole('button', { name: 'DIAGNOSTICS', exact: true }).click();
    await page.getByRole('button', { name: 'READ HEALTH', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('.appliance-notice')?.textContent?.includes('BUSY'));
    await check('diagnostics', width, height);
    await clickNav('HOME');
    await page.getByRole('button', { name: /^MASTER \d+ percent\. Adjust$/ }).click();
    await check('touch-depth', width, height);
    await page.getByRole('button', { name: '0%', exact: true }).click();
    await page.locator('.appliance-dialog-body').evaluate((body) => { body.scrollTop = body.scrollHeight; });
    await check('touch-depth-scrolled', width, height);
    await page.getByRole('button', { name: 'SET 0%', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('.appliance-notice')?.textContent?.includes('BUSY'));
    if (!await page.getByRole('button', { name: 'MUTATE', exact: true }).isDisabled()) throw new Error('Zero depth did not disable mutation.');
    await check('zero-depth-blocked', width, height);
    await page.getByRole('button', { name: 'MASTER 0 percent. Adjust', exact: true }).click();
    await page.getByRole('button', { name: '25%', exact: true }).click();
    await page.getByRole('button', { name: 'SET 25%', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('.appliance-notice')?.textContent?.includes('BUSY'));
  }
  await page.setViewportSize({ width: 800, height: 480 });
  await clickNav('RYTM');
  await page.getByRole('button', { name: 'ALL 12', exact: true }).click();
  await page.waitForFunction(() => !document.querySelector('.appliance-notice')?.textContent?.includes('BUSY'));
  await clickNav('HOME');
  await page.getByRole('button', { name: 'MUTATE', exact: true }).click();
  await page.getByText('EXACT NEXT APPLY', { exact: true }).waitFor();
  await check('mutation-preview', 800, 480);
  await page.getByRole('button', { name: 'LOCAL APPLY…', exact: true }).click();
  for (const [width, height] of [[800, 480], [480, 320], [1024, 600]]) {
    await page.setViewportSize({ width, height });
    await check('exact-apply-confirmation', width, height);
    await page.locator('.appliance-dialog-body').evaluate((body) => { body.scrollTop = body.scrollHeight; });
    await check('exact-apply-confirmation-scrolled', width, height);
  }
  await page.setViewportSize({ width: 800, height: 480 });
  await page.getByRole('button', { name: 'CONFIRM LOCAL APPLY', exact: true }).click();
  await page.locator('.appliance-receipt').waitFor();
  await check('local-apply-receipt', 800, 480);
  }
  await page.setViewportSize({ width: 800, height: 480 });
  await clickNav('MORE');
  await page.getByRole('button', { name: 'DIAGNOSTICS', exact: true }).click();
  await page.getByRole('link', { name: 'STUDIO VIEW', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('.appliance') === null);
  await page.screenshot({ path: resolve(directory, 'studio-navigation-800x480.png'), fullPage: false });
  await page.evaluate(() => { location.hash = '/appliance'; });
  await page.getByRole('heading', { name: 'HOME / PERFORM' }).waitFor();
  await page.getByText(mode === 'simulation' ? 'SIMULATION / NO MIDI' : 'PASSIVE / DISARMED', { exact: true }).waitFor();
  await check('studio-return', 800, 480);
  if (browserErrors.length) throw new Error(`Browser page errors: ${browserErrors.join(', ')}`);
  writeFileSync(resolve(directory, 'visual-qa-receipt.json'), JSON.stringify({ sourceSha, mode, tested: `production frontend + ${mode === 'simulation' ? 'explicitly simulated backend' : 'disconnected passive production backend'}; no hardware authority`, browser: await browser.version(), screenshots: receipts, studioNavigation: true, browserErrors }, null, 2));
  console.log(JSON.stringify({ passed: true, mode, screenshots: receipts.length, targetSizes: [[800, 480], [480, 320], [1024, 600]], browserErrors: 0 }));
} finally {
  await context.close();
  await browser.close();
}
