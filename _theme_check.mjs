// 다크 테마 전체 점검 — 홈/콘텐츠 폼/사주 결과 등 3-4컷
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/?nocache=' + Date.now();

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 430, height: 932 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1200);
await page.evaluate(() => document.getElementById('swipeHint')?.remove());

// 1) 홈
await page.screenshot({ path: '_theme_home.png' });

// 2) 만월 → 메뉴
await page.evaluate(() => {
  const btns = document.querySelectorAll('button, a');
  for (const b of btns) {
    const t = (b.textContent || '').trim();
    if (t === '사주 풀이 들어가기' || t.includes('들어가기')) { b.click(); return; }
  }
});
await page.waitForTimeout(1200);
await page.screenshot({ path: '_theme_menu.png' });

// 3) "오늘의 운세" 폼
await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button, a, div, li'));
  for (const e of all) {
    if (e.children.length > 5) continue;
    if ((e.textContent || '').trim().startsWith('오늘의 운세')) { e.click(); return; }
  }
});
await page.waitForTimeout(1500);
await page.screenshot({ path: '_theme_form.png' });

// 4) 가독성 점검 — 본문 글자 색·대비
const readability = await page.evaluate(() => {
  const bgColor = getComputedStyle(document.body).backgroundColor;
  const out = [];
  for (const el of document.querySelectorAll('h1, h2, h3, p, label, span, button')) {
    const r = el.getBoundingClientRect();
    if (r.top < 0 || r.top > 932 || r.width === 0 || r.height === 0) continue;
    const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3)
      ? el.textContent.trim() : '';
    if (!text || text.length > 30) continue;
    const cs = getComputedStyle(el);
    out.push({ tag: el.tagName, color: cs.color, bg: cs.backgroundColor, text: text.slice(0,20) });
    if (out.length >= 20) break;
  }
  return { bg: bgColor, items: out };
});
console.log('Body BG:', readability.bg);
console.log('\nText samples:');
for (const it of readability.items) {
  console.log(`[${it.tag}] color=${it.color}  "${it.text}"`);
}

await browser.close();
console.log('\nSaved: _theme_home.png, _theme_menu.png, _theme_form.png');
