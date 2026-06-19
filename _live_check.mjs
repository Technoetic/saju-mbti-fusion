// 라이브 사이트 가독성 점검 — 분홍 글자가 얼마나 진한지 실제 렌더링으로 확인
import { chromium } from 'playwright';

const URL = 'https://saju-mbti-fusion.fly.dev/';

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 430, height: 932 },  // iPhone 14 Pro Max 사이즈
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1500);

// 첫 화면 캡처
await page.screenshot({ path: '_live_home.png', fullPage: false });

// CSS 변수 실측
const tokens = await page.evaluate(() => {
  const s = getComputedStyle(document.documentElement);
  return {
    'pink-dp': s.getPropertyValue('--pink-dp').trim(),
    'pink-soft': s.getPropertyValue('--pink-soft').trim(),
    'pink': s.getPropertyValue('--pink').trim(),
    'ink': s.getPropertyValue('--ink').trim(),
  };
});

// pink-dp가 실제로 적용된 텍스트 요소들 샘플 — 색·폰트사이즈·요소 위치
const pinkTextSamples = await page.evaluate(() => {
  const out = [];
  const all = document.querySelectorAll('h1, h2, h3, h4, p, span, button, label, summary, a, b');
  for (const el of all) {
    const cs = getComputedStyle(el);
    const color = cs.color;
    // RGB 추출
    const m = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) continue;
    const [r, g, b] = [+m[1], +m[2], +m[3]];
    // 분홍 계열만 추리기 (R>G, R>B, R-G>30)
    if (r > g + 20 && r > b + 20 && r > 100 && el.offsetWidth > 0 && el.offsetHeight > 0) {
      const text = (el.textContent || '').trim().slice(0, 30);
      if (!text) continue;
      const rect = el.getBoundingClientRect();
      if (rect.top < 0 || rect.top > 932) continue;
      out.push({
        tag: el.tagName,
        cls: el.className || '',
        color,
        fontSize: cs.fontSize,
        fontWeight: cs.fontWeight,
        text,
        top: Math.round(rect.top),
      });
      if (out.length >= 15) break;
    }
  }
  return out;
});

console.log('=== CSS tokens (live) ===');
console.log(JSON.stringify(tokens, null, 2));
console.log('\n=== Pink-tinted text samples on first viewport ===');
for (const s of pinkTextSamples) {
  console.log(`[${s.tag}.${s.cls}] ${s.color} ${s.fontSize} w${s.fontWeight} top=${s.top}px  "${s.text}"`);
}

// 사주 탭으로 들어가 폼 라벨 색까지 점검
try {
  await page.click('text=만월', { timeout: 5000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: '_live_saju.png', fullPage: false });
} catch (e) {
  console.log('\n(사주 탭 진입 실패: ' + e.message + ')');
}

await browser.close();
console.log('\nSaved: _live_home.png, _live_saju.png');
