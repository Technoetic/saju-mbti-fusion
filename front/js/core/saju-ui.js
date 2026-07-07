// ============================================================
// 사주 UI 컨트롤러 — ADR-045 외부 모듈화 (front/index.html SECTION 9)
// ============================================================
// performCalculation·triggerAICall·fmtPillar·renderResult + window.SAJU 통합 export
//
// 의존: window.{ 천간·지지·천간_한자·지지_한자·오행_색깔·천간_오행·지지_오행 } (saju-engine.js)
//      + window.{ calculateSaju·analyzeSaju·buildSajuPrompt·callFreeAI·simpleMarkdown }
//      + window.{ analyzeName·splitName·한글음_한자·한자획수·한자_뜻·불용한자 } (name-engine.js)
//      + window.LLMUtils (llm-utils.js)
//
// 본 파일은 DOM 이벤트 핸들러 다수 등록 → DOMContentLoaded 가드 필요.
// classic <script src> + defer로 body 로드 후 실행.
// ============================================================
'use strict';

// ============================================================
// SECTION 9: UI — 임시 (마지막 단계에서 전면 재작업)
// ============================================================

function fmtPillar(stem, branch) {
  const s = 천간[stem],  sh = 천간_한자[stem];
  const b = 지지[branch],  bh = 지지_한자[branch];
  const so = 오행_색깔[천간_오행[stem]];
  const bo = 오행_색깔[지지_오행[branch]];
  return {
  stemKor: s, stemHan: sh, branchKor: b, branchHan: bh,
  stemClass: so, branchClass: bo,
  };
}

function fmtJD(jd, tz = 9) {
  const [y, mo, d, h, mi, s] = localFromJD(jd, tz);
  return `${y}-${String(mo).padStart(2,'0')}-${String(d).padStart(2,'0')} ${String(h).padStart(2,'0')}:${String(mi).padStart(2,'0')}:${String(Math.round(s)).padStart(2,'0')}`;
}

function pillarBlock(stem, branch, dayStem, sipsung, unseong, shinsal, jg, title) {
  const f = fmtPillar(stem, branch);
  const sipsungLabel = (sipsung === -1) ? '<b>본원</b>' : 십성명[sipsung];
  // 장간: 여기·중기·정기 + 각 십성
  const jgRows = [];
  const slots = [['여기', jg.여기, jg.십성[0]], ['중기', jg.중기, jg.십성[1]], ['정기', jg.정기, jg.십성[2]]];
  for (const [lbl, stIdx, spIdx] of slots) {
  if (stIdx < 0) continue;
  const cls = 오행_색깔[천간_오행[stIdx]];
  jgRows.push(`<div class="jg-row"><span class="jg-lbl">${lbl}</span> <span class="${cls}">${천간_한자[stIdx]}</span> <span class="jg-sip">${십성명[spIdx]}</span></div>`);
  }
  return `
  <div class="pillar">
  <div class="title">${title}</div>
  <div class="sipsung">${sipsungLabel}</div>
  <div class="stem ${f.stemClass}">${f.stemHan}<br><span class="kor">${f.stemKor}</span></div>
  <div class="branch ${f.branchClass}">${f.branchHan}<br><span class="kor">${f.branchKor}</span></div>
  <div class="unseong">${십이운성명[unseong]}</div>
  <div class="shinsal">${십이신살명[shinsal]}</div>
  <div class="janggan">${jgRows.join('')}</div>
  </div>
  `;
}

function renderOhaengBar(ohaengArr, label) {
  const total = ohaengArr.reduce((a, b) => a + b, 0) || 1;
  const cells = ohaengArr.map((v, i) =>
  `<td class="${오행_색깔[i]}">${오행명[i]}<br><b>${v.toFixed(2)}</b><br>${(v / total * 100).toFixed(1)}%</td>`
  ).join('');
  return `<table class="kv ohaeng"><tr><td><b>${label}</b></td>${cells}</tr></table>`;
}

function renderDaewoonTable(dwResult, sajuYear, birthYear) {
  const rows = dwResult.daewoon.map((d, i) => {
  const yearStart = birthYear + Math.floor(d.startAge);
  const sipsungOhaeng = 오행_색깔[천간_오행[d.stem]];
  const branchOhaeng = 오행_색깔[지지_오행[d.branch]];
  return `
  <tr>
  <td>${i + 1}운</td>
  <td>${d.startAge.toFixed(1)}세~</td>
  <td>${yearStart}~</td>
  <td class="${sipsungOhaeng}">${천간_한자[d.stem]}<br><span class="kor">${천간[d.stem]}</span></td>
  <td class="${branchOhaeng}">${지지_한자[d.branch]}<br><span class="kor">${지지[d.branch]}</span></td>
  <td>${십성명[d.sipsung]}</td>
  <td>${십이운성명[d.unseong]}</td>
  <td>${십이신살명[d.shinsal]}</td>
  </tr>
  `;
  }).join('');
  const dir = dwResult.순행 ? '순행 (順行)' : '역행 (逆行)';
  return `
  <h3>대운 (${dir}, 시작 ${dwResult.startAge.toFixed(2)}세, 절기까지 ${dwResult.days.toFixed(2)}일)</h3>
  <table class="kv daewoon-tbl">
  <tr><th>순서</th><th>나이</th><th>연도</th><th>천간</th><th>지지</th><th>십성</th><th>12운성</th><th>12신살</th></tr>
  ${rows}
  </table>
  `;
}

function renderSewoonTable(swList) {
  const rows = swList.map(s => {
  const stemCls = 오행_색깔[천간_오행[s.stem]];
  const branchCls = 오행_색깔[지지_오행[s.branch]];
  return `
  <tr>
  <td>${s.year}</td>
  <td class="${stemCls}">${천간_한자[s.stem]}${지지_한자[s.branch]}<br><span class="kor">${천간[s.stem]}${지지[s.branch]}</span></td>
  <td>${십성명[s.sipsung]}</td>
  <td>${십이운성명[s.unseong]}</td>
  <td>${십이신살명[s.shinsal]}</td>
  </tr>
  `;
  }).join('');
  return `
  <h3>세운 (年運) ${swList[0].year} ~ ${swList[swList.length-1].year}</h3>
  <table class="kv sewoon-tbl">
  <tr><th>연도</th><th>간지</th><th>십성</th><th>12운성</th><th>12신살</th></tr>
  ${rows}
  </table>
  `;
}

function renderInterpretation(interp, analysis, dayStem) {
  const sipsungBars = interp.십성_분포.map((c, i) => {
  const max = Math.max(...interp.십성_분포);
  const w = max > 0 ? (c / max * 100) : 0;
  return `<tr><td>${십성명[i]}</td><td><div class="sip-bar" style="width:${w}%">&nbsp;</div></td><td>${c}</td></tr>`;
  }).join('');

  const currentDaeHTML = interp.현재대운
  ? `<p><b>${천간_한자[interp.현재대운.stem]}${지지_한자[interp.현재대운.branch]}</b> (${천간[interp.현재대운.stem]}${지지[interp.현재대운.branch]}) · ${십성명[interp.현재대운.sipsung]} · ${십이운성명[interp.현재대운.unseong]} · ${십이신살명[interp.현재대운.shinsal]}<br>시작 나이: ${interp.현재대운.startAge.toFixed(1)}세</p>`
  : '<p class="hint">해당 나이대의 대운 정보 없음</p>';

  return `
  <h2>해석 (룰셋 기반)</h2>
  <div class="interp-box">
  <h3>종합</h3>
  <p>${interp.종합}</p>
  </div>

  <div class="interp-grid">
  <div class="interp-box">
  <h3>일간 본성 — ${천간_한자[dayStem]}(${천간[dayStem]}) · ${interp.일간_본성.상징}</h3>
  <p><b>본성:</b> ${interp.일간_본성.본성}</p>
  <p><b>장점:</b> ${interp.일간_본성.장점}</p>
  <p><b>주의:</b> ${interp.일간_본성.주의}</p>
  <p><b>어울리는 분야:</b> ${interp.일간_본성.직업.join(' · ')}</p>
  </div>
  <div class="interp-box">
  <h3>격국 — ${analysis.격국.명}</h3>
  <p><b>특성:</b> ${interp.격국_해설.특성}</p>
  <p><b>적성:</b> ${interp.격국_해설.직업}</p>
  <p><b>키워드:</b> ${interp.격국_해설.키워드}</p>
  <p><b>정기 투출:</b> ${analysis.격국.정기투출 ? '○ (격이 분명)' : '× (격이 약함)'}</p>
  </div>
  </div>

  <div class="interp-grid">
  <div class="interp-box">
  <h3>용신 방향</h3>
  <p><b>신강 등급:</b> ${analysis.신강신약.등급} (${(analysis.신강신약.비율*100).toFixed(1)}%)</p>
  <p><b>용신:</b> ${interp.용신방향}</p>
  <p><b>기신:</b> ${interp.기신방향}</p>
  </div>
  <div class="interp-box">
  <h3>십성 분포</h3>
  <table class="kv sipsung-tbl">${sipsungBars}</table>
  <p><b>가장 강한 십성:</b> ${interp.가장강한십성}</p>
  <p><b>부족한 십성:</b> ${interp.부족한십성.length > 0 ? interp.부족한십성.join(', ') : '없음 (10성 모두 갖춤)'}</p>
  </div>
  </div>

  <div class="interp-box">
  <h3>현재 대운 (${interp.나이}세)</h3>
  ${currentDaeHTML}
  </div>

  <div class="interp-grid">
  <div class="interp-box"><h3>성격</h3><p>${interp.성격}</p></div>
  <div class="interp-box"><h3>직업·재능</h3><p>${interp.직업}</p></div>
  <div class="interp-box"><h3>재물</h3><p>${interp.재물}</p></div>
  <div class="interp-box"><h3>대인 관계</h3><p>${interp.관계}</p></div>
  <div class="interp-box"><h3>건강</h3><p>${interp.건강}</p></div>
  </div>
  `;
}

function renderNameAnalysis(nameAnalysis, name) {
  if (!nameAnalysis) return '';
  const eo = nameAnalysis.음오행분석;
  const eumOhaengHTML = eo.글자.map((c, i) => {
  const ohaengIdx = eo.초성오행[i];
  const cls = ohaengIdx >= 0 ? 오행_색깔[ohaengIdx] : '';
  const label = ohaengIdx >= 0 ? 오행명[ohaengIdx] : '?';
  return `<td class="${cls}"><b>${c}</b><br>${label}</td>`;
  }).join('');
  const relationHTML = eo.관계.map(r => `<td style="font-size:11px">${r}</td>`).join('<td></td>');

  let hanjaHTML = '';
  if (nameAnalysis.한자분석) {
  const ha = nameAnalysis.한자분석;
  const charsHTML = [...ha.성씨한자, ...ha.이름한자].map(c =>
  `<td><b style="font-size:20px">${c.한자 || '?'}</b><br>${c.한글}<br><small>${c.획수 || '?'}획 / ${c.획수 % 2 === 1 ? '양' : '음'}</small></td>`
  ).join('');
  const ogyeokHTML = ['원격','형격','이격','정격','외격'].map(k => {
  const o = ha.오격[k];
  const evalClass = o.평가 === '대길' ? 'eval-daekil' : o.평가 === '길' ? 'eval-gil'
  : o.평가 === '흉' ? 'eval-hyung' : o.평가 === '대흉' ? 'eval-daehyung' : 'eval-pyong';
  return `<tr><td><b>${k}</b></td><td>${o.수}</td><td class="${evalClass}"><b>${o.평가}</b></td><td>${o.명}</td><td style="font-size:12px">${o.의미}</td></tr>`;
  }).join('');
  hanjaHTML = `
  <h3>한자 분석 (강희자전 원획)</h3>
  <table class="kv name-tbl">
  <tr>${charsHTML}</tr>
  </table>
  <h4>오격 (五格)</h4>
  <table class="kv ogyeok-tbl">
  <tr><th>격</th><th>수</th><th>평가</th><th>격명</th><th>의미</th></tr>
  ${ogyeokHTML}
  </table>
  <p><b>음양 조화:</b> 양 ${ha.음양.양}자 / 음 ${ha.음양.음}자 → ${ha.음양.평가}</p>
  `;
  } else if (name && (name.surname || name.givenName)) {
  hanjaHTML = '<p class="hint">한자 미입력 또는 일부만 입력됨 → 음오행 분석만 진행</p>';
  }

  return `
  <h2>성명학 분석</h2>
  ${hanjaHTML}
  <h3>음오행 (音五行) — 한글 초성 기반</h3>
  <table class="kv name-tbl">
  <tr>${eumOhaengHTML}</tr>
  <tr><td colspan="${eo.글자.length}" style="text-align:center;font-size:11px;color:#666">${eo.관계.map(r => `[${r}]`).join(' → ')}</td></tr>
  </table>
  <p><b>음오행 평가:</b> ${eo.평가}</p>
  <p><b>종합:</b> ${nameAnalysis.종합}</p>
  `;
}

function renderResult(r) {
  const p = r.pillars;
  const a = analyzeSaju(r);
  const dw = calculateDaewoon(r);
  const interp = generateInterpretation(r, a, dw);
  const currentYear = new Date().getFullYear();
  const sw = calculateSewoon(r, currentYear - 2, 13); // 현재 -2 ~ +10

  // 이름이 있으면 호칭 사용 (사극·신비 톤으로)
  const nameHeader = r.name && (r.name.surname || r.name.givenName)
  ? `<h1>${r.name.surname}${r.name.givenName}<span style="color:var(--text-dim);font-size:0.7em;font-weight:400;letter-spacing:2px;margin-left:8px">${r.name.hanja ? '(' + r.name.hanja + ')' : ''}</span>님의 명리</h1>`
  : '<h1>사주 풀이 결과</h1>';

  // 4기둥 블록 (시·일·월·년 순서)
  const dayStem = p.day.stem;
  const pillarsHTML = `
  <div class="pillars">
  ${pillarBlock(p.time.stem,  p.time.branch,  dayStem, a.천간십성.time,  a.운성.time,  a.신살.time,  a.장간.time,  '時柱 시주')}
  ${pillarBlock(p.day.stem,  p.day.branch,  dayStem, a.천간십성.day,  a.운성.day,  a.신살.day,  a.장간.day,  '日柱 일주')}
  ${pillarBlock(p.month.stem, p.month.branch, dayStem, a.천간십성.month, a.운성.month, a.신살.month, a.장간.month, '月柱 월주')}
  ${pillarBlock(p.year.stem,  p.year.branch,  dayStem, a.천간십성.year,  a.운성.year,  a.신살.year,  a.장간.year,  '年柱 년주')}
  </div>
  `;

  // 오행 + 신강·신약 + 격국
  const summaryHTML = `
  <h3>오행 분포</h3>
  ${renderOhaengBar(a.오행.단순, '단순 (천간1 + 지지정기1)')}
  ${renderOhaengBar(a.오행.가중, '장간 가중 (천간1 + 장간일수비율)')}
  <h3>신강·신약 / 격국</h3>
  <table class="kv">
  <tr><td>일간</td><td><b>${천간_한자[dayStem]} (${천간[dayStem]} · ${오행명[천간_오행[dayStem]]})</b></td></tr>
  <tr><td>신강 등급</td><td><b>${a.신강신약.등급}</b> (도움/약화 비율 ${(a.신강신약.비율 * 100).toFixed(1)}%)</td></tr>
  <tr><td>득령/실령</td><td>${a.신강신약.득령 ? '득령(得令) — 월지가 일간 도움' : a.신강신약.실령 ? '실령(失令) — 월지가 일간 약화' : '평'}</td></tr>
  <tr><td>도움점수</td><td>${a.신강신약.도움.toFixed(2)}</td></tr>
  <tr><td>약화점수</td><td>${a.신강신약.약화.toFixed(2)}</td></tr>
  <tr><td>격국</td><td><b>${a.격국.명}</b> ${a.격국.정기투출 ? '(정기 투출)' : '(정기 미투출 — 격이 약함)'}</td></tr>
  </table>
  `;

  // 메타데이터
  const m = r.meta;
  const boundariesRows = m.boundaries.map(b =>
  `<tr><td>${b.명}</td><td>${b.황경}°</td><td>${지지[b.월지]}월</td><td>${fmtJD(b.JD, r.input.timezoneOffset)}</td></tr>`
  ).join('');
  const metaHTML = `
  <details><summary>계산 메타데이터 (검증용)</summary>
  <table class="kv">
  <tr><td>시민력(입력) JD (UT)</td><td>${m.civilJD.toFixed(6)}</td></tr>
  <tr><td>진태양시 JD (UT)</td><td>${m.solarJD.toFixed(6)}</td></tr>
  <tr><td>경도 보정 (분)</td><td>${m.longCorrectionMinutes.toFixed(2)}</td></tr>
  <tr><td>균시차 (분)</td><td>${m.eotMinutes.toFixed(2)}</td></tr>
  <tr><td>사주 연도</td><td>${m.sajuYear}</td></tr>
  <tr><td>입춘 시각 (사주연도)</td><td>${fmtJD(m.lichunJD, r.input.timezoneOffset)}</td></tr>
  <tr><td>일주 자시 보정</td><td>${m.dayPillarOffset === 1 ? '다음날 일주 적용' : '당일 일주'}</td></tr>
  <tr><td>시주 천간 기준</td><td>${m.timeStemFromNextDay ? '다음날 일간' : '당일 일간'}</td></tr>
  </table>
  <h4>12절(월 경계) 시각 — 사주 ${m.sajuYear}년</h4>
  <table class="kv">
  <tr><th>절기</th><th>황경</th><th>월지</th><th>시각</th></tr>
  ${boundariesRows}
  </table>
  </details>
  `;

  const html = `
  ${nameHeader}
  <details class="saju-details">
  <summary>◇ 자세한 사주 분석표 보기 (전문 용어 포함)</summary>
  <div style="padding-top:14px">
  <h3>四柱八字 · 사주 8글자</h3>
  ${pillarsHTML}
  ${summaryHTML}
  ${renderInterpretation(interp, a, p.day.stem)}
  ${renderDaewoonTable(dw, m.sajuYear, r.input.year)}
  ${renderSewoonTable(sw)}
  ${renderNameAnalysis(r.nameAnalysis, r.name)}
  ${metaHTML}
  </div>
  </details>
  <div id="saju-school-toggle-guk" class="saju-school-toggle-slot"></div>
  <div id="saju-school-toggle-sinsal" class="saju-school-toggle-slot"></div>
  <div id="saju-school-toggle-synergy" class="saju-school-toggle-slot"></div>
  `;
  document.getElementById('result').innerHTML = html;

  // ADR-153 학파 토글 마운트 (동적 import — 결과 영역에만 노출).
  // 사용자가 학파 선택 시 localStorage 저장 (다음 호출 시 디폴트 반영은 별건).
  import('../ui/school-toggle.js').then((mod) => {
    mod.renderSchoolToggle({
      containerId: 'saju-school-toggle-guk',
      title: '사주 합국 강도 학파',
      options: mod.SAJU_GUK_STRENGTH_OPTIONS,
      adrRef: 'ADR-141',
      onSelect: (key) => {
        try { localStorage.setItem('whm.school.guk', key); } catch (e) {}
      },
    });
    mod.renderSchoolToggle({
      containerId: 'saju-school-toggle-sinsal',
      title: '12 신살 기준 학파',
      options: mod.SAJU_SINSAL_BASIS_OPTIONS,
      adrRef: 'ADR-142',
      onSelect: (key) => {
        try { localStorage.setItem('whm.school.sinsal_basis', key); } catch (e) {}
      },
    });
    mod.renderSchoolToggle({
      containerId: 'saju-school-toggle-synergy',
      title: '신살 시너지 가중치 학파',
      options: mod.SAJU_SYNERGY_SCHOOL_OPTIONS,
      adrRef: 'ADR-153',
      onSelect: (key) => {
        try { localStorage.setItem('whm.school.synergy', key); } catch (e) {}
      },
    });
  }).catch((err) => {
    console.warn('[saju-ui] school-toggle 마운트 실패:', err);
  });
}

/**
 * 한글 성/이름 입력 시 각 글자별 한자 드롭다운을 동적 생성
 * 예: "박형민" → 박:[朴,博,泊...], 형:[亨,兄,型,形...], 민:[敏,玟,珉,旻...]
 */
function updateHanjaSelectors() {
  const fullName = document.getElementById('fullName').value.trim();
  const { surname, givenName } = splitName(fullName);

  // 분리 결과 안내 업데이트
  const splitHint = document.getElementById('splitHint');
  if (splitHint) {
  if (fullName) {
  splitHint.textContent = `→ 성: ${surname || '-'}  이름: ${givenName || '-'}`;
  if (splitHint.style) splitHint.style.color = '#1f5fb3';
  } else {
  splitHint.textContent = '— 적은 이름에서 성과 이름을 자동으로 나눕니다.';
  if (splitHint.style) splitHint.style.color = '';
  }
  }

  const container = document.getElementById('hanjaSelectors');
  const surnameChars = Array.from(surname);
  const nameChars = Array.from(givenName);
  const allChars = [...surnameChars, ...nameChars];

  if (allChars.length === 0) {
  container.innerHTML = '<span class="hint">이름을 적으면 글자마다 쓸 수 있는 한자가 아래에 나옵니다. 한자를 모르면 그냥 두셔도 분석은 됩니다.</span>';
  updateStrokeTotal();
  return;
  }

  // 기존 선택 보존
  const previous = {};
  container.querySelectorAll('.hanja-select').forEach(sel => {
  if (sel.value) previous[sel.dataset.char + ':' + sel.dataset.idx] = sel.value;
  });

  let html = '<div style="margin-bottom:6px;color:var(--gold);font-weight:600">한자 고르기 <span style="font-weight:normal;color:var(--text-dim);font-size:12px">(모르면 그냥 두세요)</span></div>';
  let hasUnknown = false;
  for (let i = 0; i < allChars.length; i++) {
  const ch = allChars[i];
  const isSurname = i < surnameChars.length;
  // 획수가 있는 한자는 모두 드롭다운에 노출 (뜻 없어도 표시 — Unihan 보강 후)
  const candidates = (한글음_한자[ch] || []).filter(h => 한자획수[h]);
  if (candidates.length === 0) hasUnknown = true;
  const key = ch + ':' + i;
  const prevSel = previous[key] || '';
  const opts = [`<option value="">✦ 한글이름 (순우리말)</option>`,
  ...candidates.map(h => {
  const stroke = 한자획수[h];
  const meaning = 한자_뜻[h] || '';
  const sel = (h === prevSel) ? ' selected' : '';
  const strokePart = stroke ? ` (${stroke}획)` : '';
  const unusable = 불용한자.has(h) ? ' · [불용]' : '';
  return `<option value="${h}"${sel}>${h} ${meaning}${strokePart}${unusable}</option>`;
  })
  ].join('');
  const isBulyongSelected = prevSel && 불용한자.has(prevSel);
  const cellClass = isBulyongSelected ? 'hanja-cell hanja-cell-bulyong' : 'hanja-cell';
  const warnTag = isBulyongSelected
    ? `<div class="hanja-bulyong-warn">⚠ 불용한자 — 의미가 어둡거나 흉운으로 분류되어 작명에서 잘 쓰지 않습니다</div>`
    : '';
  html += `<span class="${cellClass}" data-cell-idx="${i}">
  <div class="hanja-han"><b>${ch}</b><small>${isSurname ? '성' : '이름'}</small></div>
  <select class="hanja-select" data-char="${ch}" data-idx="${i}">${opts}</select>
  ${warnTag}
  </span>`;
  }
  if (hasUnknown) {
  html += '<div class="hint" style="margin-top:6px">※ "—" 표시된 글자는 후보가 없는 한자라 분석에서 제외됩니다. 한글 음오행 분석은 됩니다.</div>';
  }
  html += '<div class="hint" style="margin-top:4px;color:var(--text-dim)">※ [불용] 표시는 의미가 어둡거나 흉운으로 분류되어 작명에서 잘 쓰지 않는 한자 (참고용).</div>';
  container.innerHTML = html;

  // 셀렉터 변경 시 불용한자 경고 토글
  container.querySelectorAll('.hanja-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const cell = e.target.closest('.hanja-cell');
      if (!cell) return;
      const h = e.target.value;
      const isBad = h && 불용한자.has(h);
      cell.classList.toggle('hanja-cell-bulyong', !!isBad);
      let warn = cell.querySelector('.hanja-bulyong-warn');
      if (isBad) {
        if (!warn) {
          warn = document.createElement('div');
          warn.className = 'hanja-bulyong-warn';
          warn.textContent = '⚠ 불용한자 — 의미가 어둡거나 흉운으로 분류되어 작명에서 잘 쓰지 않습니다';
          cell.appendChild(warn);
        }
      } else if (warn) {
        warn.remove();
      }
    });
  });

  updateStrokeTotal();
}

/**
 * 한자 선택 결과 + 총 획수를 친근하게 표시
 */
function updateStrokeTotal() {
  const target = document.getElementById('strokeTotal');
  if (!target) return;
  const cells = document.querySelectorAll('#hanjaSelectors .hanja-cell');
  if (cells.length === 0) {
  target.textContent = '이름을 적어주세요';
  return;
  }
  let total = 0;
  let pickedCount = 0;
  const rows = [];
  cells.forEach(cell => {
  const ch = cell.querySelector('.hanja-han b')?.textContent || '';
  const sel = cell.querySelector('.hanja-select');
  const han = sel ? sel.value : '';
  if (!han) {
  rows.push(`<span class="stroke-row stroke-empty">${ch} → 한자 없음</span>`);
  return;
  }
  pickedCount++;
  const stroke = 한자획수[han] || 0;
  const meaning = 한자_뜻[han] || '';
  if (stroke) total += stroke;
  rows.push(`<span class="stroke-row"><b>${ch}</b> → <b>${han}</b> ${meaning} <span class="stroke-num">${stroke || '?'}획</span></span>`);
  });
  if (pickedCount === 0) {
  target.innerHTML = `<div class="stroke-rows">${rows.join('')}</div><div class="stroke-sum-empty">한자를 골라야 획수가 계산됩니다</div>`;
  } else {
  target.innerHTML = `<div class="stroke-rows">${rows.join('')}</div><div class="stroke-sum">총 획수 <b>${total}</b>획</div>`;
  }
}

// 드롭다운 선택·직접 입력 시 합계 즉시 갱신 (이벤트 위임)
document.getElementById('hanjaSelectors').addEventListener('change', updateStrokeTotal);
document.getElementById('hanjaSelectors').addEventListener('input',  updateStrokeTotal);

document.getElementById('fullName').addEventListener('input', updateHanjaSelectors);

// ── 상대방(궁합) 이름 한자 선택 — 개인 모드와 동일 로직 (id에 'p' 접두사) ──
function updatePartnerHanjaSelectors() {
  const fullName = (document.getElementById('pFullName')?.value || '').trim();
  const { surname, givenName } = splitName(fullName);

  const splitHint = document.getElementById('pSplitHint');
  if (splitHint) {
    if (fullName) {
      splitHint.textContent = `→ 성: ${surname || '-'}  이름: ${givenName || '-'}`;
      splitHint.style.color = '#d4af37';
    } else {
      splitHint.textContent = '— 적은 이름에서 성과 이름을 자동으로 나눕니다.';
      splitHint.style.color = '';
    }
  }

  const container = document.getElementById('pHanjaSelectors');
  if (!container) return;
  const surnameChars = Array.from(surname);
  const nameChars = Array.from(givenName);
  const allChars = [...surnameChars, ...nameChars];

  if (allChars.length === 0) {
    container.innerHTML = '<span class="hint">이름을 적으면 글자마다 쓸 수 있는 한자가 아래에 나옵니다. 한자를 모르면 그냥 두셔도 분석은 됩니다.</span>';
    updatePartnerStrokeTotal();
    return;
  }

  const previous = {};
  container.querySelectorAll('.hanja-select').forEach(sel => {
    if (sel.value) previous[sel.dataset.char + ':' + sel.dataset.idx] = sel.value;
  });

  let html = '<div style="margin-bottom:6px;color:#d4af37;font-weight:600">한자 고르기 <span style="font-weight:normal;color:#8b7e5d;font-size:12px">(모르면 그냥 두세요)</span></div>';
  let hasUnknown = false;
  for (let i = 0; i < allChars.length; i++) {
    const ch = allChars[i];
    const isSurname = i < surnameChars.length;
    const candidates = (한글음_한자[ch] || []).filter(h => 한자획수[h] && 한자_뜻[h]);
    if (candidates.length === 0) hasUnknown = true;
    const key = ch + ':' + i;
    const prevSel = previous[key] || '';
    const opts = [`<option value="">✦ 한글이름 (순우리말)</option>`,
      ...candidates.map(h => {
        const stroke = 한자획수[h];
        const meaning = 한자_뜻[h] || '';
        const sel = (h === prevSel) ? ' selected' : '';
        const strokePart = stroke ? ` (${stroke}획)` : '';
        const unusable = 불용한자.has(h) ? ' · [불용]' : '';
        return `<option value="${h}"${sel}>${h} ${meaning}${strokePart}${unusable}</option>`;
      })
    ].join('');
    html += `<span class="hanja-cell">
      <div class="hanja-han"><b>${ch}</b><small>${isSurname ? '성' : '이름'}</small></div>
      <select class="hanja-select" data-char="${ch}" data-idx="${i}">${opts}</select>
    </span>`;
  }
  if (hasUnknown) {
    html += '<div class="hint" style="margin-top:6px">※ "—" 표시된 글자는 후보가 없는 한자라 분석에서 제외됩니다.</div>';
  }
  html += '<div class="hint" style="margin-top:4px;color:var(--text-dim)">※ [불용] 표시는 의미가 어둡거나 흉운으로 분류되어 작명에서 잘 쓰지 않는 한자 (참고용).</div>';
  container.innerHTML = html;
  updatePartnerStrokeTotal();
}

function updatePartnerStrokeTotal() {
  const target = document.getElementById('pStrokeTotal');
  if (!target) return;
  const cells = document.querySelectorAll('#pHanjaSelectors .hanja-cell');
  if (cells.length === 0) {
    target.textContent = '이름을 적어주세요';
    return;
  }
  let total = 0;
  const rows = [];
  cells.forEach(cell => {
    const ch = cell.querySelector('.hanja-han b')?.textContent || '';
    const sel = cell.querySelector('.hanja-select');
    const han = sel ? sel.value : '';
    if (!han) {
      rows.push(`<span class="stroke-row stroke-empty">${ch} → 한자 없음</span>`);
      return;
    }
    const stroke = 한자획수[han] || 0;
    total += stroke;
    rows.push(`<span class="stroke-row">${ch}(${han}) ${stroke}획</span>`);
  });
  target.innerHTML = `${rows.join(' ')} <b style="color:var(--gold);margin-left:8px">총 ${total}획</b>`;
}

const pFullNameEl = document.getElementById('pFullName');
if (pFullNameEl) {
  pFullNameEl.addEventListener('input', updatePartnerHanjaSelectors);
}
const pHanjaContainer = document.getElementById('pHanjaSelectors');
if (pHanjaContainer) {
  pHanjaContainer.addEventListener('change', updatePartnerStrokeTotal);
  pHanjaContainer.addEventListener('input', updatePartnerStrokeTotal);
}

document.getElementById('birthplace').addEventListener('change', (e) => {
  const opt = e.target.selectedOptions[0];
  const lon = opt.dataset.lon, tz = opt.dataset.tz;
  if (lon) document.getElementById('longitude').value = lon;
  if (tz)  document.getElementById('timezone').value = tz;
});

let lastSajuResult = null;
let currentMode = 'personal'; // personal | couple | friend | coworker
const MODE_LABEL = {
  personal: '개인',
  couple:  '연인 궁합',
  friend:  '친구 궁합',
  coworker: '동료 궁합',
};

// 분석 종류 선택 바
document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b === btn));
  currentMode = btn.dataset.mode;
  const showPartner = currentMode !== 'personal';
  const pf = document.getElementById('partnerFieldset');
  if (pf) pf.style.display = showPartner ? 'block' : 'none';

  // 고민 fieldset 번호 동적 갱신 (궁합 모드면 六, 개인이면 五)
  const cf = document.getElementById('concernFieldset');
  if (cf) {
  const lg = cf.querySelector('legend');
  if (lg) lg.textContent = showPartner ? '六. 고민 心' : '五. 고민 心';
  }

  // 안내 문구
  const hint = document.getElementById('partnerHint');
  if (hint) {
  const map = {
  couple:  '연인·배우자 정보를 적어주세요. 두 분의 사주를 함께 비교해드립니다.',
  friend:  '친구 정보를 적어주세요. 두 분의 사주를 함께 비교해드립니다.',
  coworker: '동료·상사 정보를 적어주세요. 두 분의 사주를 함께 비교해드립니다.',
  };
  hint.textContent = map[currentMode] || '';
  }
  });
});

/**
 * 입력 폼에서 값을 읽어 사주를 계산하고 결과를 렌더링한다.
 * 반환값: 성공 시 true, 실패 시 false (에러는 result 영역에 표시)
 */
function performCalculation() {
  let yIn = parseInt(document.getElementById('year').value, 10);
  let mIn = parseInt(document.getElementById('month').value, 10);
  let dIn = parseInt(document.getElementById('day').value, 10);

  // 음력/양력 토글 — 음력 선택 시 lunar-javascript로 양력으로 변환
  const calEl = document.getElementById('calendarType');
  const calMode = calEl ? calEl.value : 'solar';  // solar / lunar / lunar_leap

  if (calMode !== 'solar') {
    try {
      const isLeap = (calMode === 'lunar_leap');
      // lunar-javascript: Lunar.fromYmd(year, month, day, isLeap?)
      // 윤달이면 month를 음수로 표기 (lunar-javascript 관행)
      const lunarMonth = isLeap ? -mIn : mIn;
      if (window.Lunar && typeof window.Lunar.fromYmd === 'function') {
        const lunar = window.Lunar.fromYmd(yIn, lunarMonth, dIn);
        const solar = lunar.getSolar();
        yIn = solar.getYear();
        mIn = solar.getMonth();
        dIn = solar.getDay();
      } else {
        console.warn('[lunar] lunar-javascript 미로드 — 양력으로 그대로 처리');
      }
    } catch (e) {
      console.warn('[lunar] 변환 실패, 양력 그대로 처리:', e);
    }
  }

  const input = {
  year:  yIn,
  month:  mIn,
  day:  dIn,
  hour:  parseInt(document.getElementById('hour').value, 10),
  minute:  parseInt(document.getElementById('minute').value, 10),
  timezoneOffset: parseFloat(document.getElementById('timezone').value),
  longitude:  parseFloat(document.getElementById('longitude').value),
  useTrueSolar:  document.getElementById('trueSolar').value === 'true',
  ziShiOption:  document.getElementById('ziShi').value,
  gender:  document.getElementById('gender').value,
  };
  try {
  lastSajuResult = calculateSaju(input);

  // 이름 (선택) → 성명학 분석
  const fullName = document.getElementById('fullName').value.trim();
  const { surname, givenName } = splitName(fullName);
  if (surname || givenName) {
  // 드롭다운 선택값 수집 — 인덱스 기준 (같은 한글이 반복돼도 위치별로 다른 한자 가능)
  const hangulChars = Array.from(surname + givenName);
  const indexedHanja = new Array(hangulChars.length).fill('');
  document.querySelectorAll('.hanja-select').forEach(sel => {
  const idx = parseInt(sel.dataset.idx, 10);
  if (sel.value && idx >= 0 && idx < indexedHanja.length) indexedHanja[idx] = sel.value;
  });
  // 한글 → 한자 매핑 (analyzeName 인터페이스용)
  const hanjaMap = {};
  for (let i = 0; i < hangulChars.length; i++) {
  if (indexedHanja[i]) hanjaMap[hangulChars[i]] = indexedHanja[i];
  }
  lastSajuResult.nameAnalysis = analyzeName(surname, givenName, hanjaMap);
  const hanjaString = indexedHanja.join('');
  lastSajuResult.name = { surname, givenName, hanja: hanjaString };
  } else {
  lastSajuResult.nameAnalysis = null;
  lastSajuResult.name = null;
  }

  // 지금 상황(직장·연애) 수집
  const jobStatusMap = {
  working:'재직 중', business:'사업·자영업', freelance:'프리랜서',
  seeking:'구직 중', student:'학생', rest:'휴직·이직 준비',
  homemaker:'전업 주부·육아', none:'없음·기타'
  };
  const loveStatusMap = {
  dating:'연애 중', married:'결혼(기혼)', single:'솔로', separated:'이별·이혼·사별 후'
  };
  const jobS = document.getElementById('jobStatus').value;
  const jobD = document.getElementById('jobDuration').value;
  const loveS = document.getElementById('loveStatus').value;
  const loveD = document.getElementById('loveDuration').value;
  lastSajuResult.lifeContext = {
  job:  jobS  ? { 상태: jobStatusMap[jobS] || jobS,  기간: jobD  || '' } : null,
  love: loveS ? { 상태: loveStatusMap[loveS] || loveS, 기간: loveD || '' } : null,
  mbti: document.getElementById('mbti').value || null,
  };

  // 궁합 모드 — 상대방 사주도 함께 계산
  lastSajuResult.mode = currentMode;
  lastSajuResult.partnerResult = null;
  if (currentMode !== 'personal') {
  try {
  // 상대방 출생지에서 경도·시간대 추출
  const pBpEl = document.getElementById('pBirthplace');
  const pOpt = pBpEl && pBpEl.selectedOptions[0];
  const pLon = pOpt ? parseFloat(pOpt.dataset.lon) : input.longitude;
  const pTz  = pOpt ? parseFloat(pOpt.dataset.tz)  : input.timezoneOffset;
  const partnerInput = {
  year:  parseInt(document.getElementById('pYear').value, 10),
  month:  parseInt(document.getElementById('pMonth').value, 10),
  day:  parseInt(document.getElementById('pDay').value, 10),
  hour:  parseInt(document.getElementById('pHour').value, 10),
  minute:  parseInt(document.getElementById('pMinute').value, 10),
  timezoneOffset: pTz,
  longitude:  pLon,
  useTrueSolar:  input.useTrueSolar,
  ziShiOption:  input.ziShiOption,
  gender:  document.getElementById('pGender').value,
  };
  const pResult = calculateSaju(partnerInput);
  pResult.name = {
  surname: '',
  givenName: document.getElementById('pFullName').value.trim() || '상대',
  hanja: '',
  };
  pResult.lifeContext = {
  job: null, love: null,
  mbti: document.getElementById('pMbti').value || null,
  };
  lastSajuResult.partnerResult = pResult;
  } catch (e) {
  console.error('[궁합] 상대방 사주 계산 실패:', e);
  }
  }

  renderResult(lastSajuResult);
  document.getElementById('claudeResult').innerHTML = ''; // 이전 AI 결과 초기화
  return true;
  } catch (err) {
  document.getElementById('result').innerHTML = `<pre style="color:red">${err.stack || err}</pre>`;
  return false;
  }
}

/**
 * 만월아씨 통합 서사 페이로드 구성 · 결정론 데이터만 담아 백엔드로 전달.
 *
 * lastSajuResult 는 원본 사주 (pillars stem 이 정수 인덱스).
 * analyzeSaju/calculateDaewoon 결과를 파생해서 한자로 정규화한 뒤 전달한다.
 */
function buildManwolPayload(concern) {
  if (!lastSajuResult) return null;
  const r = lastSajuResult;

  // 파생 계산 · 실패해도 최소 페이로드는 보내지도록 try/catch
  let a = null;
  let dw = null;
  try { a = analyzeSaju(r); } catch (e) { console.warn('[manwol] analyzeSaju 실패:', e); }
  try { dw = calculateDaewoon(r); } catch (e) { console.warn('[manwol] calculateDaewoon 실패:', e); }

  const chz = (typeof 천간_한자 !== 'undefined' && 천간_한자) || ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
  const brz = (typeof 지지_한자 !== 'undefined' && 지지_한자) || ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
  const ELEMENT_KO = ['木','火','土','金','水'];

  // pillar 정규화 · stem/branch 정수 → gan/ji 한자
  function normPillar(p) {
    if (!p) return null;
    return {
      gan_han: p.stem != null ? chz[p.stem] : (p.gan_han || p.gan || ''),
      ji_han: p.branch != null ? brz[p.branch] : (p.ji_han || p.ji || ''),
      gan: p.stem != null ? chz[p.stem] : (p.gan || ''),
      ji: p.branch != null ? brz[p.branch] : (p.ji || ''),
    };
  }
  const pillarsNorm = r.pillars ? {
    year:  normPillar(r.pillars.year),
    month: normPillar(r.pillars.month),
    day:   normPillar(r.pillars.day),
    hour:  normPillar(r.pillars.time || r.pillars.hour),
  } : null;
  const dayMaster = pillarsNorm?.day?.gan_han || '';

  // 오행 분포 · 인덱스 배열 → {木, 火, 土, 金, 水} 딕셔너리
  let wuxingDist = null;
  if (a && a.오행 && Array.isArray(a.오행.가중)) {
    wuxingDist = {};
    a.오행.가중.forEach((v, i) => { wuxingDist[ELEMENT_KO[i]] = +(+v).toFixed(2); });
  }

  // 대운 · [{stem, branch, startAge, sipsung}...] → [{age, gan_han, ji_han}...]
  let luckCycle = null;
  if (dw && Array.isArray(dw.daewoon)) {
    luckCycle = dw.daewoon.map(d => ({
      age: d.startAge != null ? Math.floor(d.startAge) : null,
      gan_han: d.stem != null ? chz[d.stem] : '',
      ji_han: d.branch != null ? brz[d.branch] : '',
    }));
  }

  const strength = a && a.신강신약 ? { grade: a.신강신약.등급, ratio: a.신강신약.비율 } : null;
  const gyeokguk = a && a.격국 ? { name: a.격국.명 } : null;

  const payload = {
    saju: {
      pillars: pillarsNorm,
      day_master: dayMaster,
      wuxing_dist: wuxingDist,
      luck_cycle: luckCycle,
      strength,
      gyeokguk,
      gender: r.gender,
    },
    name_analysis: r.nameAnalysis
      ? {
          surname: r.name?.surname || '',
          givenName: r.name?.givenName || '',
          음오행분석: r.nameAnalysis?.음오행분석,
          오격: r.nameAnalysis?.오격,
        }
      : null,
    life_context: r.lifeContext || null,
    concern: concern || null,
    gender: r.gender,
  };
  // 종합 옵션 (꿈 원문 · 사용자가 입력했을 때만)
  const dreamEl = document.getElementById('dreamText');
  if (dreamEl && dreamEl.value && dreamEl.value.trim()) {
    payload.dream_text = dreamEl.value.trim();
  }
  return payload;
}

/**
 * 현재 lastSajuResult 로 만월아씨 통합 서사를 호출.
 * 웹툰 렌더러 대체 · /api/manwol/reading 스트리밍 → 심야 방송실 톤 산문 카드.
 */
async function triggerAICall() {
  if (!lastSajuResult) return;
  const concern = (document.getElementById('userConcern')?.value || '').trim();

  const 호칭 = (lastSajuResult.name && (lastSajuResult.name.surname || lastSajuResult.name.givenName))
    ? `${lastSajuResult.name.surname}${lastSajuResult.name.givenName}`
    : '';
  const title = (호칭 ? 호칭 + ' · ' : '') + '심야 사연 풀이';

  const out = document.getElementById('claudeResult');
  out.innerHTML = `
    <div class="claude-output manwol-loading">
      <div class="manwol-loading-inner">
        <div class="manwol-loading-sign">ON AIR</div>
        <div class="manwol-loading-title">${title}</div>
        <div class="manwol-loading-sub">만월아씨가 사연을 짚는 중.</div>
      </div>
    </div>
  `;

  const payload = buildManwolPayload(concern);
  if (!payload) {
    out.querySelector('.claude-output').innerHTML =
      `<p class="manwol-error">사주 계산이 안 됐어. 다시 입력해봐.</p>`;
    return;
  }

  try {
    const { renderManwolReading } = await import('../ui/manwol-renderer.js');
    // 로딩 클래스 제거 후 렌더러가 카드 뼈대 구성
    const box = out.querySelector('.claude-output');
    box.classList.remove('manwol-loading');
    await renderManwolReading(box, payload, { title });
  } catch (err) {
    out.querySelector('.claude-output').innerHTML =
      `<p class="manwol-error">사연 풀이 도중 신호가 끊겼어. (${(err.message || err).toString().replace(/</g, '&lt;')})</p>`;
  }
}

// [풀이 보기] — 입력 화면에서 클릭 시 사주 계산 + 결과 화면 전환 + AI 자동 호출
document.getElementById('goResultBtn').addEventListener('click', async () => {
  const ok = performCalculation();
  if (!ok) return;
  // 결과 화면으로 전환
  document.getElementById('step-input').classList.remove('active');
  document.getElementById('step-result').classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  // 릴레이 시스템 — 사주 풀이 완료 표시 (요약은 백엔드 결과 들어오면 채워짐)
  if (window.WHM) window.WHM.markCompleted('saju', {
  name: document.getElementById('fullName')?.value || '',
  ilju: null, keyMessage: null,
  });
  // 종합검진 개별 카드(자미·관상·꿈·타로) 폐기 — 만월아씨 통합 서사에 흡수됨.
  // 필요 시 데이터는 buildManwolPayload 에서 직접 실어 백엔드로 전달.
  // AI 풀이 자동 시작
  await triggerAICall();
});

// [← 다시 입력하기]
document.getElementById('backToInputBtn').addEventListener('click', () => {
  document.getElementById('step-result').classList.remove('active');
  document.getElementById('step-input').classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// [더 깊이 풀어보기] — 결과 화면에서 MBTI·고민을 추가 입력받음 (백엔드 미연결)
(function setupGoDeeper() {
  const btn = document.getElementById('goDeeperBtn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const mbtiAfter = document.getElementById('mbtiAfter');
    const concernAfter = document.getElementById('userConcernAfter');
    const hint = document.getElementById('goDeeperHint');
    // 숨겨진 원래 입력으로 값 동기화 (mbti 는 lifeContext 에 이미 담기지만
    // 결과 페이지에서 새로 골랐다면 lastSajuResult.lifeContext 도 반영)
    const mbtiVal = mbtiAfter?.value || '';
    const concernVal = (concernAfter?.value || '').trim();
    if (concernVal) document.getElementById('userConcern').value = concernVal;
    if (mbtiVal && lastSajuResult) {
      lastSajuResult.lifeContext = lastSajuResult.lifeContext || {};
      lastSajuResult.lifeContext.mbti = mbtiVal;
    }
    if (hint) {
      hint.textContent = '다시 짚어보는 중.';
      hint.style.color = 'var(--gold-bri)';
    }
    // 상단으로 스크롤 후 만월아씨 서사 재실행
    document.getElementById('claudeResult')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    await triggerAICall();
  });
})();

// 전역 노출 — 콘솔에서 직접 테스트 가능
window.SAJU = {
  // 핵심 계산
  calculateSaju, calcSolarTerms, sunApparentLongitude, equationOfTime,
  toJD, fromJD, jdFromLocal, localFromJD, findSunLongitudeJD, dayPillarIndex,
  // 분석
  analyzeSaju, gzIdx, getSipsung, get12Unseong, get12Shinsal,
  // 대운·세운
  calculateDaewoon, calculateSewoon,
  // 해석
  generateInterpretation,
  해석_일간, 해석_십성, 해석_격국, 해석_12운성, 해석_12신살,
  // AI API
  buildSajuPrompt, buildDreamPrompt, callFreeAI, simpleMarkdown,
  // 성명학
  analyzeName, calculateOgyeok, analyzeEumOhaeng, analyzeEumYang, 수리환원,
  splitName, 복성_목록,
  한자획수, 한자_뜻, 수리길흉, 한글_초성_오행, 한글음_한자,
  불용한자,
  updateHanjaSelectors,
  // 데이터
  천간, 지지, 천간_한자, 지지_한자, 천간_오행, 지지_오행,
  십성명, 십이운성명, 십이신살명, 지지_장간, 오행명,
  // ADR-052: UI 핸들러 (인라인 autoInit 호출 호환)
  performCalculation, triggerAICall,
  fmtPillar, fmtJD, renderResult,
};



// ── lastSajuResult 외부 접근용 getter (let은 자동 글로벌 X) ──
Object.defineProperty(window, 'lastSajuResult', { get: () => lastSajuResult, configurable: true });
