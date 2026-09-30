/** Bounded, one-browser acceptance against the production appliance runtime.
 * Usage: node scripts/appliance-visual-qa.mjs <private launch.html> <output directory> <runtime source SHA>
 * The private bootstrap is navigated without reading, printing or copying its secrets.
 */
import { chromium } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const bootstrap = process.argv[2];
const output = process.argv[3];
const sourceSha = process.argv[4];
if (!bootstrap || !output || !/^[a-f0-9]{40}$/.test(sourceSha ?? '')) throw new Error('Expected private launch.html path, screenshot output directory and exact runtime source SHA.');
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
      const clip = element.closest('.appliance-content')?.getBoundingClientRect() ?? { top: 0, bottom: innerHeight, left: 0, right: innerWidth };
      return { label: element.textContent?.trim().slice(0, 50), width: Math.round(rect.width), height: Math.round(rect.height), visible: rect.height > 0 && rect.bottom > Math.max(0, clip.top) && rect.top < Math.min(innerHeight, clip.bottom) && rect.right > 0 && rect.left < innerWidth };
    }).filter((box) => box.visible);
    return { viewport: [innerWidth, innerHeight], documentWidth: document.documentElement.scrollWidth, applianceWidth: root.scrollWidth, touchFailures: boxes.filter((box) => box.width < 44 || box.height < 44), visibleTouchControls: boxes.length, pixelFontLoaded: [...document.fonts].some((font) => font.family === 'Appliance Pixel' && font.status === 'loaded') };
  });
  const screenshot = `${name}-${width}x${height}.png`;
  await page.screenshot({ path: resolve(directory, screenshot), fullPage: false });
  receipts.push({ screenshot, ...metrics });
  if (metrics.documentWidth > width || metrics.applianceWidth > width || metrics.touchFailures.length || !metrics.pixelFontLoaded) {
    throw new Error(`Visual/touch check failed: ${JSON.stringify({ screenshot, ...metrics })}`);
  }
}
async function checkTargetMatrix(expectedCount) {
  const result = await page.evaluate(() => {
    const surface = document.querySelector('[role="dialog"]') ?? document.querySelector('.appliance-content');
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
  await page.getByText('SIMULATION / NO MIDI', { exact: true }).waitFor();
  await page.evaluate(() => document.fonts.ready);
  for (const [width, height] of [[800, 480], [480, 320], [1024, 600]]) {
    await page.setViewportSize({ width, height });
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
  await check('exact-apply-confirmation', 800, 480);
  await page.getByRole('button', { name: 'CONFIRM LOCAL APPLY', exact: true }).click();
  await page.locator('.appliance-receipt').waitFor();
  await check('local-apply-receipt', 800, 480);
  await clickNav('MORE');
  await page.getByRole('button', { name: 'DIAGNOSTICS', exact: true }).click();
  await page.getByRole('link', { name: 'STUDIO VIEW', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('.appliance') === null);
  await page.screenshot({ path: resolve(directory, 'studio-navigation-800x480.png'), fullPage: false });
  await page.evaluate(() => { location.hash = '/appliance'; });
  await page.getByRole('heading', { name: 'HOME / PERFORM' }).waitFor();
  await page.getByText('SIMULATION / NO MIDI', { exact: true }).waitFor();
  await check('studio-return', 800, 480);
  if (browserErrors.length) throw new Error(`Browser page errors: ${browserErrors.join(', ')}`);
  writeFileSync(resolve(directory, 'visual-qa-receipt.json'), JSON.stringify({ sourceSha, tested: 'production frontend + explicitly simulated backend; no hardware authority', browser: await browser.version(), screenshots: receipts, studioNavigation: true, browserErrors }, null, 2));
  console.log(JSON.stringify({ passed: true, screenshots: receipts.length, targetSizes: [[800, 480], [480, 320], [1024, 600]], browserErrors: 0 }));
} finally {
  await context.close();
  await browser.close();
}
