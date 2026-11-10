// Read-only local visual review; screenshots stay in an ignored run directory.
import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
const [base, output] = process.argv.slice(2);
if (!base || !output) throw Error('Usage: node scripts/capture.mjs BASE_URL UNIQUE_OUTPUT_DIRECTORY');
await mkdir(output, {recursive:false});
const browser = await chromium.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
const page = await browser.newPage();
await page.goto(base);
await page.getByTestId('sigma-canvas-container').waitFor();
await page.waitForFunction(()=>/Displayed: [1-9][\d,]* nodes/.test(document.querySelector('[data-testid="displayed-counts"]')?.textContent || ''));
for (const width of [390,768,1024,1440]) {
 await page.setViewportSize({width,height:900});
 for (const dark of [true,false]) {
  await page.evaluate(async d=>{const s=window.__explorerStore || (await import("/src/stores/useExplorerStore.ts")).useExplorerStore;if(s.getState().darkMode!==d)s.getState().toggleDarkMode()},dark);
  await page.waitForTimeout(250);
  await page.screenshot({path:path.join(output,`graph-${width}-${dark?'dark':'light'}.png`)});
 }
}
if (process.argv.includes('--baseline')) { await browser.close(); process.exit(0); }
await page.evaluate(() => window.__explorerStore.getState().selectEdge(document.querySelector('[data-testid="sigma-canvas-container"]').__sigma.getGraph().edges()[0]));
for (const width of [390,768,1024,1440]) {
 await page.setViewportSize({width,height:900});
 for (const dark of [true,false]) {
  await page.evaluate(d=>{const s=window.__explorerStore;if(s.getState().darkMode!==d)s.getState().toggleDarkMode()},dark);
  await page.waitForTimeout(250);
  await page.screenshot({path:path.join(output,`edge-${width}-${dark?'dark':'light'}.png`)});
 }
}
await page.setViewportSize({width:1440,height:1100});
for(const dark of [true,false]) {
 await page.evaluate(d=>{const s=window.__explorerStore;if(s.getState().darkMode!==d)s.getState().toggleDarkMode();s.getState().setWorkspaceTab('analytics')},dark);
 await page.getByTestId('analytics-view').waitFor();
 for(const section of ['robustness','topics','communities','sectors','trajectories']) {
  await page.evaluate(section=>window.__explorerStore.setState({analyticsSection:section}),section);
  await page.waitForTimeout(450);
  await page.screenshot({path:path.join(output,`${section}-${dark?'dark':'light'}.png`)});
 }
}
await browser.close();
