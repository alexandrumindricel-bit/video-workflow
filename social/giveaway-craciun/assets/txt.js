const { chromium } = require('playwright');
(async () => { const [d, qs] = process.argv.slice(2); const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1512, height: 2016 } });
  await p.goto(`file://${d}/txt.html?${qs}`); await p.waitForFunction(() => document.title.startsWith('ok'));
  console.log(await p.title());
  await p.screenshot({ path: `${d}/gw/txtnew.png`, omitBackground: true }); await b.close(); })();
