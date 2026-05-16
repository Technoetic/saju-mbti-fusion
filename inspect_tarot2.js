// 보강 점검: lazy-load 강제 + 카드 클릭(lightbox) + 필터 동작
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const URL = 'https://technoetic.github.io/wolha-mong-tarot/';
  const OUT = __dirname;

  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(2000);

  // 모든 이미지 강제 로드: 페이지를 끝까지 스크롤
  await page.evaluate(async () => {
    await new Promise(resolve => {
      let y = 0;
      const step = 400;
      const timer = setInterval(() => {
        window.scrollBy(0, step);
        y += step;
        if (y >= document.body.scrollHeight) { clearInterval(timer); resolve(); }
      }, 80);
    });
  });
  await page.waitForTimeout(3000);
  // 모든 이미지 로드 대기
  await page.evaluate(() => Promise.all(
    Array.from(document.images).map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; }))
  ));
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);

  // 이미지 로드 상태 통계
  const imgStats = await page.evaluate(() => {
    const imgs = Array.from(document.images);
    const broken = imgs.filter(i => i.naturalWidth === 0).map(i => ({ src: i.src, alt: i.alt }));
    return {
      total: imgs.length,
      loaded: imgs.filter(i => i.naturalWidth > 0).length,
      broken: broken.length,
      brokenList: broken
    };
  });

  // 풀페이지 스크린샷 (이미지 모두 로드된 상태)
  const loadedShot = path.join(OUT, 'tarot_loaded_full.png');
  await page.screenshot({ path: loadedShot, fullPage: true });

  // 필터 버튼 동작 점검: "보강 필요" 클릭
  await page.click('button:has-text("보강 필요")');
  await page.waitForTimeout(800);
  const filterStats = await page.evaluate(() => {
    const visible = Array.from(document.querySelectorAll('[class*="card"], li, article, figure, .item')).filter(el => el.offsetParent !== null && el.querySelector && el.querySelector('img'));
    return { visibleCardLike: visible.length };
  });
  await page.screenshot({ path: path.join(OUT, 'tarot_filter_repair.png'), fullPage: false });

  // 다시 전체로
  await page.click('button:has-text("전체")');
  await page.waitForTimeout(500);

  // 첫번째 카드 클릭해서 lightbox 동작 확인
  // 이미지가 있는 첫 요소 클릭
  const firstImg = await page.locator('img').first();
  await firstImg.click({ force: true });
  await page.waitForTimeout(1000);

  const lightboxState = await page.evaluate(() => {
    const close = document.querySelector('.close');
    const prev = document.querySelector('.nav.prev');
    const next = document.querySelector('.nav.next');
    return {
      closeVisible: close ? close.offsetParent !== null : false,
      prevVisible: prev ? prev.offsetParent !== null : false,
      nextVisible: next ? next.offsetParent !== null : false,
      bodyHasModalClass: document.body.className
    };
  });
  await page.screenshot({ path: path.join(OUT, 'tarot_lightbox.png') });

  // next 버튼 클릭
  const nextBtn = page.locator('.nav.next');
  if (await nextBtn.isVisible()) {
    await nextBtn.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: path.join(OUT, 'tarot_lightbox_next.png') });
  }

  // 모바일 시뮬레이션
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => { const c = document.querySelector('.close'); if (c) c.click(); });
  await page.waitForTimeout(500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: path.join(OUT, 'tarot_mobile_top.png') });

  await browser.close();

  const out = { imgStats, filterStats, lightboxState };
  fs.writeFileSync(path.join(OUT, 'tarot_report2.json'), JSON.stringify(out, null, 2), 'utf-8');
  console.log(JSON.stringify(out, null, 2));
})();
