// Playwright 점검 스크립트 — https://technoetic.github.io/wolha-mong-tarot/
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const URL = 'https://technoetic.github.io/wolha-mong-tarot/';
  const OUT = __dirname;

  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const consoleLogs = [];
  const requests = [];
  const failedRequests = [];

  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));
  page.on('request', req => requests.push({ url: req.url(), type: req.resourceType() }));
  page.on('requestfailed', req => failedRequests.push({ url: req.url(), failure: req.failure()?.errorText }));

  const resp = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForLoadState('load', { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(3000); // JS 렌더링 여유

  const title = await page.title();
  const viewportShot = path.join(OUT, 'tarot_viewport.png');
  const fullShot = path.join(OUT, 'tarot_fullpage.png');
  await page.screenshot({ path: viewportShot });
  await page.screenshot({ path: fullShot, fullPage: true });

  // 모바일 뷰 스크린샷도
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileShot = path.join(OUT, 'tarot_mobile.png');
  await page.screenshot({ path: mobileShot, fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });

  // DOM 정보 수집
  const meta = await page.evaluate(() => {
    const pick = sel => Array.from(document.querySelectorAll(sel));
    return {
      lang: document.documentElement.lang,
      charset: document.characterSet,
      headings: pick('h1,h2,h3').map(h => ({ tag: h.tagName, text: h.innerText.trim() })),
      buttons: pick('button').map(b => ({
        text: b.innerText.trim().slice(0, 60),
        ariaLabel: b.getAttribute('aria-label'),
        className: b.className.slice(0, 80),
        visible: b.offsetParent !== null
      })),
      links: pick('a').slice(0, 20).map(a => ({ text: a.innerText.trim().slice(0, 60), href: a.href })),
      images: pick('img').map(i => ({ src: i.src, alt: i.alt, naturalW: i.naturalWidth, naturalH: i.naturalHeight })).slice(0, 30),
      imageCount: pick('img').length,
      stylesheets: pick('link[rel=stylesheet]').map(l => l.href),
      scripts: pick('script[src]').map(s => s.src),
      inlineScriptCount: pick('script:not([src])').length,
      bodyTextLen: document.body.innerText.length,
      bodyTextPreview: document.body.innerText.slice(0, 2000),
      htmlSize: document.documentElement.outerHTML.length,
      structure: {
        nav: !!document.querySelector('nav'),
        header: !!document.querySelector('header'),
        main: !!document.querySelector('main'),
        footer: !!document.querySelector('footer'),
        sections: pick('section').length,
        articles: pick('article').length
      }
    };
  });

  await browser.close();

  const report = {
    url: URL,
    status: resp?.status(),
    title,
    meta,
    requestSummary: {
      total: requests.length,
      byType: requests.reduce((acc, r) => { acc[r.type] = (acc[r.type]||0)+1; return acc; }, {}),
      failed: failedRequests
    },
    consoleErrors: consoleLogs.filter(l => l.type === 'error'),
    consoleWarnings: consoleLogs.filter(l => l.type === 'warning'),
    screenshots: { desktop: viewportShot, full: fullShot, mobile: mobileShot }
  };

  fs.writeFileSync(path.join(OUT, 'tarot_report.json'), JSON.stringify(report, null, 2), 'utf-8');
  console.log(JSON.stringify(report, null, 2));
})();
