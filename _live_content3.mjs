// 만월 → 메뉴 카드 진입 경로 추적
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

// "사주 풀이 들어가기" 버튼이 캐릭터 카드 안에 있었음 — 그걸 클릭
const ok = await page.evaluate(() => {
  const btns = document.querySelectorAll('button, a');
  for (const b of btns) {
    const t = (b.textContent || '').trim();
    if (t === '사주 풀이 들어가기' || t.includes('들어가기')) { b.click(); return t; }
  }
  return 'not_found';
});
console.log('Entry click:', ok);
await page.waitForTimeout(1500);

await page.screenshot({ path: '_live_step1.png' });

// 메뉴가 떴는지 확인 + "오늘의 운세" 노출 여부
const visible = await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('*'));
  return all
    .filter(e => {
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.top >= 0 && r.top < 932
        && (e.textContent || '').includes('오늘의 운세')
        && e.children.length < 5;
    })
    .slice(0, 5)
    .map(e => ({ tag: e.tagName, cls: e.className?.toString().slice(0,80), text: (e.textContent||'').trim().slice(0,40) }));
});
console.log('오늘의 운세 elements:', JSON.stringify(visible, null, 2));

// 그 중 하나 클릭
const clicked = await page.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button, a, div, li'));
  for (const e of all) {
    if (e.children.length > 5) continue;
    if ((e.textContent || '').trim().startsWith('오늘의 운세')) {
      e.click();
      return e.tagName + '.' + (e.className?.toString().slice(0,40) || '');
    }
  }
  return 'not_found';
});
console.log('Today click:', clicked);
await page.waitForTimeout(1500);

await page.screenshot({ path: '_live_step2.png' });

// 분홍 글자 점검
const pinks = await page.evaluate(() => {
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.top < 0 || r.top > 932 || r.width === 0) continue;
    const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3)
      ? el.textContent.trim() : '';
    if (!text || text.length > 40) continue;
    const cs = getComputedStyle(el);
    const m = cs.color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) continue;
    const [a, b, c] = [+m[1], +m[2], +m[3]];
    if (a > b + 15 && a > c + 15 && a > 120) {
      out.push({ tag: el.tagName, cls: (el.className?.toString()||'').slice(0,60),
                 color: cs.color, fontSize: cs.fontSize, text: text.slice(0,30) });
    }
  }
  return out.slice(0, 30);
});
console.log('\n=== 분홍 텍스트 ===');
for (const p of pinks) console.log(`[${p.tag}.${p.cls}] ${p.color} ${p.fontSize}  "${p.text}"`);

await browser.close();
console.log('\nSaved: _live_step1.png, _live_step2.png');
