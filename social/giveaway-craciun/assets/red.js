const { chromium } = require('playwright');
(async () => { const d = process.argv[2]; const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1512, height: 2016 } });
  await p.goto(`file://${d}/hat2.html`); await p.waitForTimeout(200);
  await p.screenshot({ path: `${d}/red.png`, omitBackground: true }); await b.close(); })();
