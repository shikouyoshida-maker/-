const { chromium } = require('playwright');
const dir = process.argv[2];
const html = process.argv[3] || 'logos.html';
const od = process.argv[4] || 'out';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1000, height: 1000 }, deviceScaleFactor: 2 });
  await p.goto('file://' + dir + '/' + html);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(1500);
  for (const el of await p.$$('svg')) {
    const id = await el.getAttribute('id');
    await el.screenshot({ path: `${dir}/${od}/${id}.png`, omitBackground: true });
  }
  await b.close();
})();
