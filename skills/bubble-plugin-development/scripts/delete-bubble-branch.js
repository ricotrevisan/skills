const { chromium } = require('playwright');
// Deletes Bubble app branches through the Bubble editor UI.
// Usage: node delete-bubble-branch.js <branch-name> [more names...]
// Requires: BUBBLE_COOKIE env var (editor cookies, same one Pled uses),
// playwright installed, and a Chromium executable (edit EXEC below).
const D = 'tiptap-plugin.bubbleapps.io';
const EXEC = '/home/rico/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome';
const TARGETS = process.argv.slice(2);
(async () => {
  const cookies = process.env.BUBBLE_COOKIE.split(/;\s*/).map(p => {
    const i = p.indexOf('=');
    return { name: p.slice(0, i), value: p.slice(i + 1) };
  });
  const b = await chromium.launch({ executablePath: EXEC });
  const ctx = await b.newContext({
    httpCredentials: { username: 'tippy', password: 'tappy' },
    viewport: { width: 1700, height: 1050 },
  });
  const all = [];
  for (const c of cookies)
    for (const d of [D, '.bubbleapps.io', 'bubble.io', 'app.bubble.io'])
      all.push({ ...c, domain: d, path: '/' });
  await ctx.addCookies(all);
  const p = await ctx.newPage();
  try {
    await p.goto(`https://bubble.io/page?id=tiptap-plugin&tab=Design`, { waitUntil: 'load', timeout: 60000 });
  } catch (e) {}
  await p.waitForTimeout(12000);
  const openPanel = async () => { await p.mouse.click(110, 20); await p.waitForTimeout(3000); };
  for (const name of TARGETS) {
    console.log('=== deleting', name);
    await openPanel();
    const row = p.getByText(name, { exact: true }).first();
    if (await row.isHidden().catch(() => true)) { console.log('  not listed, skipping'); continue; }
    await row.click();
    await p.waitForFunction(() => !document.body.innerText.includes('We are loading'), null, { timeout: 90000 }).catch(() => {});
    await p.waitForTimeout(6000);
    await openPanel();
    await p.mouse.click(276, 66); // "..." menu next to branch title
    await p.waitForTimeout(1500);
    await p.getByText('Delete', { exact: true }).first().click();
    await p.waitForTimeout(1500);
    await p.locator('input:visible').last().fill(name); // confirm box
    await p.waitForTimeout(800);
    await p.mouse.click(777, 307); // red Delete in dialog
    await p.waitForTimeout(10000);
    const gone = await p.getByText(name, { exact: true }).first().isHidden().catch(() => true);
    console.log('  deleted (no longer listed):', gone);
    await p.screenshot({ path: `/tmp/opencode/after-${name}.png` });
  }
  await b.close();
})();
