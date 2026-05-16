/* HTML 단일 파일 번들러
 *   - src 의 모든 CSS <link> 를 <style> 로 인라인
 *   - 모든 <script type="module" src="..."> 를 IIFE 로 묶어 인라인
 *   - import/export 토큰만 제거 (트리쉐이크 없음)
 *   - 결과물: dist/index.html (file:// 호환)
 */
const fs = require('fs');
const path = require('path');

const SRC_HTML = path.join(__dirname, 'index.html');
const DIST_DIR = path.join(__dirname, '..', 'dist');
const DIST_HTML = path.join(DIST_DIR, 'index.html');

fs.mkdirSync(DIST_DIR, { recursive: true });

let html = fs.readFileSync(SRC_HTML, 'utf8');

// 1) CSS <link> 인라인
html = html.replace(/<link\s+rel="stylesheet"\s+href="([^"]+)"\s*\/?>/g, (_m, href) => {
  const filePath = path.join(__dirname, href);
  if (!fs.existsSync(filePath)) return _m;
  const css = fs.readFileSync(filePath, 'utf8');
  return `<style>\n${css}\n</style>`;
});

// 2) 모듈 스크립트 인라인 — 단일 IIFE 로 묶기
const moduleScriptRe = /<script\s+type="module"\s+src="([^"]+)"\s*><\/script>/g;
const modules = [];
let match;
while ((match = moduleScriptRe.exec(html)) !== null) {
  modules.push(match[1]);
}
if (modules.length > 0) {
  const collected = [];
  const seen = new Set();
  function inline(relPath, fromDir) {
    const filePath = path.resolve(fromDir, relPath);
    if (seen.has(filePath)) return;
    seen.add(filePath);
    let src = fs.readFileSync(filePath, 'utf8');
    // import 재귀 처리
    src = src.replace(/^\s*import\s+(?:\{[^}]*\}|\w+|\*\s+as\s+\w+)\s+from\s+["']([^"']+)["'];?\s*$/gm, (_m, p) => {
      inline(p, path.dirname(filePath));
      return '';
    });
    src = src.replace(/^\s*export\s+(default\s+)?/gm, '');
    src = src.replace(/^\s*export\s*\{[^}]*\};?\s*$/gm, '');
    collected.push(`/* === ${path.basename(filePath)} === */\n${src}`);
  }
  for (const m of modules) {
    inline(m, __dirname);
  }
  const bundled = `<script>\n(function () {\n${collected.join('\n\n')}\n})();\n</script>`;
  html = html.replace(moduleScriptRe, '');
  html = html.replace('</body>', bundled + '\n</body>');
}

fs.writeFileSync(DIST_HTML, html, 'utf8');
console.log(`OK dist/index.html (${(html.length / 1024).toFixed(1)} KB)`);
