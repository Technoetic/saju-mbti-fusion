/**
 * window.FaceVisualizations — 관상 풀이 시각화 헬퍼 (ADR-038 Phase 2 확장)
 *  - 7개 헬퍼 + renderVisualizations 통합 (Phase 22a)
 *  - 순수 string template 반환 (DOM 직접 조작 X)
 *  - FaceReader IIFE에서 사용
 *
 * 시각화 종류:
 *  - [A] 12궁 가로 막대 차트 (renderPalaceBars)
 *  - [B] 삼정 도넛 (renderSamjeongDonut)
 *  - [C] 오관 5각 레이더 (renderOgwanRadar)
 *  - [D] 5형 배지 (renderFaceShapeBadge)
 *  - [E] 신·기 게이지 (renderShenQi)
 *  - [F] 해부학 묘사 카드 (renderAnatomicalTable)
 *  - 통합 (renderVisualizations)
 */
(function(){
  function _esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function _pct(v) { return Math.max(0, Math.min(100, Math.round(Number(v || 0) * 100))); }

  // [D] 5형 배지
  function renderFaceShapeBadge(faceShape) {
    if (!faceShape || !faceShape.shape_type) return '';
    const shape = String(faceShape.shape_type);
    const morph = faceShape.morphological_name ? String(faceShape.morphological_name) : '';
    const glyph = ({ '목형':'木', '화형':'火', '토형':'土', '금형':'金', '수형':'水' })[shape] || '◯';
    return `
      <div class="face-viz-section">
        <div class="face-viz-title">오 행 분 류</div>
        <div class="face-viz-subtitle">MediaPipe 키포인트 기반 결정론 (ADR-022)</div>
        <div style="text-align:center">
          <span class="face-shape-badge">
            <span class="face-shape-badge-glyph">${_esc(glyph)}</span>
            <span class="face-shape-badge-name">${_esc(shape)}</span>
            ${morph ? `<span class="face-shape-badge-sub">${_esc(morph)}</span>` : ''}
          </span>
        </div>
      </div>`;
  }

  // [B] 삼정 도넛
  function renderSamjeongDonut(samjeong) {
    if (!samjeong || typeof samjeong !== 'object') return '';
    const entries = Object.entries(samjeong);
    if (!entries.length) return '';
    const items = entries.map(([k, v]) => ({
      label: (v && v.label_ko) ? v.label_ko : k,
      score: (v && typeof v.score === 'number') ? v.score : 0,
    }));
    const total = items.reduce((s, x) => s + x.score, 0) || 1;
    const sang = (items[0] ? items[0].score : 0) / total * 360;
    const jung = sang + ((items[1] ? items[1].score : 0) / total * 360);
    return `
      <div class="face-viz-panel">
        <h4 class="face-viz-panel-title">삼 정 (三停)</h4>
        <div class="face-samjeong-donut-wrap">
          <div class="face-samjeong-donut" style="--sang:${sang}deg; --jung:${jung}deg"></div>
          <div class="face-samjeong-legend">
            ${items.map((it, i) => `
              <div class="face-samjeong-legend-row">
                <span class="face-samjeong-swatch ${['sang','jung','ha'][i] || ''}"></span>
                <span>${_esc(it.label)} · ${it.score.toFixed(2)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>`;
  }

  // [C] 오관 5각 레이더
  function renderOgwanRadar(ogwan) {
    if (!ogwan || typeof ogwan !== 'object') return '';
    const entries = Object.entries(ogwan);
    if (!entries.length) return '';
    const items = entries.slice(0, 5).map(([k, v]) => ({
      label: (v && v.label_ko) ? v.label_ko : k,
      score: Math.max(0, Math.min(1, (v && typeof v.score === 'number') ? v.score : 0)),
    }));
    const N = items.length;
    const cx = 100, cy = 100, R = 70;
    const angle = (i) => (-Math.PI / 2) + (i * 2 * Math.PI / N);
    const point = (i, r) => [cx + r * Math.cos(angle(i)), cy + r * Math.sin(angle(i))];
    const gridLevels = [0.25, 0.5, 0.75, 1.0];
    const gridPolys = gridLevels.map(lvl => {
      const pts = items.map((_, i) => point(i, R * lvl).map(v => v.toFixed(1)).join(',')).join(' ');
      return `<polygon class="radar-grid" points="${pts}"/>`;
    }).join('');
    const axes = items.map((_, i) => {
      const [x, y] = point(i, R);
      return `<line class="radar-axis" x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`;
    }).join('');
    const dataPts = items.map((it, i) => point(i, R * it.score));
    const polyPts = dataPts.map(p => p.map(v => v.toFixed(1)).join(',')).join(' ');
    const points = dataPts.map(([x, y]) => `<circle class="radar-point" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2"/>`).join('');
    const labels = items.map((it, i) => {
      const [x, y] = point(i, R + 14);
      const anchor = Math.abs(x - cx) < 5 ? 'middle' : (x > cx ? 'start' : 'end');
      return `<text class="radar-label" x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="${anchor}" dominant-baseline="middle">${_esc(it.label)}</text>`;
    }).join('');
    return `
      <div class="face-viz-panel">
        <h4 class="face-viz-panel-title">오 관 (五官)</h4>
        <svg class="face-ogwan-radar" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          ${gridPolys}
          ${axes}
          <polygon class="radar-poly" points="${polyPts}"/>
          ${points}
          ${labels}
        </svg>
      </div>`;
  }

  // [E] 신·기 게이지
  function renderShenQi(shen, qi) {
    if (shen == null && qi == null) return '';
    const sPct = _pct(shen);
    const qPct = _pct(qi);
    return `
      <div class="face-viz-panel">
        <h4 class="face-viz-panel-title">신 · 기 (神 · 氣)</h4>
        <div class="face-shenqi-row">
          <span class="face-shenqi-label">神</span>
          <div class="face-shenqi-track"><div class="face-shenqi-fill" style="width:${sPct}%"></div></div>
          <span class="face-bar-val">${(shen || 0).toFixed(2)}</span>
        </div>
        <div class="face-shenqi-row">
          <span class="face-shenqi-label">氣</span>
          <div class="face-shenqi-track"><div class="face-shenqi-fill" style="width:${qPct}%"></div></div>
          <span class="face-bar-val">${(qi || 0).toFixed(2)}</span>
        </div>
      </div>`;
  }

  // [A] 12궁 가로 막대 차트
  function renderPalaceBars(palaces, topKey, weakKey) {
    if (!palaces || typeof palaces !== 'object') return '';
    const entries = Object.entries(palaces);
    if (!entries.length) return '';
    const items = entries.map(([k, v]) => ({
      key: k,
      label: (v && v.label_ko) ? v.label_ko : k,
      score: Math.max(0, Math.min(1, (v && typeof v.score === 'number') ? v.score : 0)),
    })).sort((a, b) => b.score - a.score);
    const rows = items.map(it => {
      const cls = (it.key === topKey) ? 'top' : (it.key === weakKey ? 'weak' : '');
      return `
        <div class="face-bar-row">
          <span class="face-bar-label">${_esc(it.label)}</span>
          <div class="face-bar-track"><div class="face-bar-fill ${cls}" style="width:${_pct(it.score)}%"></div></div>
          <span class="face-bar-val">${it.score.toFixed(2)}</span>
        </div>`;
    }).join('');
    return `
      <div class="face-viz-section">
        <div class="face-viz-title">십 이 궁 점 수</div>
        <div class="face-viz-subtitle">MediaPipe 478 키포인트 비율·대칭 (ADR-004)</div>
        ${rows}
      </div>`;
  }

  // [F] 해부학 묘사 카드
  function renderAnatomicalTable(anat) {
    if (!anat || typeof anat !== 'object') return '';
    const fmtObj = (o) => {
      if (!o || typeof o !== 'object') return '';
      return Object.values(o).filter(v => v && String(v).trim()).join(' · ');
    };
    const rows = [
      ['윤곽', fmtObj(anat.face_outline)],
      ['이마', fmtObj(anat.forehead)],
      ['눈썹', fmtObj(anat.eyebrow)],
      ['눈', fmtObj(anat.eye)],
      ['코', fmtObj(anat.nose)],
      ['입', fmtObj(anat.mouth)],
      ['턱', fmtObj(anat.chin)],
      ['뺨·광대', fmtObj(anat.cheek_zygomatic)],
      ['기색', fmtObj(anat.complexion)],
      ['특징', anat.distinctive_feature || ''],
    ].filter(([_, v]) => v && String(v).trim());
    if (!rows.length) return '';
    return `
      <div class="face-viz-section">
        <div class="face-viz-title">해 부 학 묘 사</div>
        <div class="face-viz-subtitle">Opus Vision 객관 분석 (ADR-005 Supplement 4)</div>
        <table class="face-anat-table">
          <tbody>
            ${rows.map(([k, v]) => `<tr><th>${_esc(k)}</th><td>${_esc(v)}</td></tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  }

  // 통합 시각화 블록 — 응답 dict에서 자동 발췌
  function renderVisualizations(data) {
    if (!data) return '';
    const ps = data.palace_scores || {};
    const fs = data.face_shape;
    const anat = data.anatomical_description;

    let mid = '';
    const samj = renderSamjeongDonut(ps.samjeong);
    const ogw = renderOgwanRadar(ps.ogwan);
    if (samj || ogw) mid += `<div class="face-viz-grid">${samj}${ogw}</div>`;
    const shenqi = renderShenQi(ps.shen_score, ps.qi_score);
    if (shenqi) mid += `<div class="face-viz-grid full">${shenqi}</div>`;

    return [
      renderFaceShapeBadge(fs),
      mid ? `<div class="face-viz-section"><div class="face-viz-title">결 정 론 점 수</div><div class="face-viz-subtitle">MediaPipe 478 키포인트 (ADR-004·022)</div>${mid}</div>` : '',
      renderPalaceBars(ps.palaces, ps.top_palace, ps.weakest_palace),
      renderAnatomicalTable(anat),
    ].filter(Boolean).join('');
  }

  window.FaceVisualizations = {
    renderFaceShapeBadge,
    renderSamjeongDonut,
    renderOgwanRadar,
    renderShenQi,
    renderPalaceBars,
    renderAnatomicalTable,
    renderVisualizations,
  };
})();
