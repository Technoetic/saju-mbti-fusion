// ============================================================
// comprehensive-reading.js — 정통 사주 종합검진 (자미두수·관상·꿈·타로)
// 사주 풀이 완료 후 추가로 4개 도메인을 병렬 호출하여 결과 페이지에 섹션으로 표시.
//   1. 자미두수 — 사주 데이터 → LLM 풀이 (12궁·14주성 기반 프롬프트)
//   2. 관상 — 사진 업로드 시 /api/face/reading (한국 학파)
//   3. 꿈해몽 — 텍스트 입력 시 /api/dream/interpret_v2
//   4. 타로 — 3장 random + LLM 풀이 (과거/현재/미래 스프레드)
// ============================================================

const TAROT_DECK = [
  '바보(The Fool)', '마법사(The Magician)', '여사제(The High Priestess)',
  '여황제(The Empress)', '황제(The Emperor)', '교황(The Hierophant)',
  '연인(The Lovers)', '전차(The Chariot)', '힘(Strength)',
  '은둔자(The Hermit)', '운명의 수레바퀴(Wheel of Fortune)', '정의(Justice)',
  '매달린 사람(The Hanged Man)', '죽음(Death)', '절제(Temperance)',
  '악마(The Devil)', '탑(The Tower)', '별(The Star)',
  '달(The Moon)', '태양(The Sun)', '심판(Judgement)', '세계(The World)',
];

function fileToBase64(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result);
    r.onerror = rej;
    r.readAsDataURL(file);
  });
}

async function callLLM(prompt) {
  // /api/llm/chat 형식: { prompt: str, stream: bool, model?: str, system?: str, max_tokens?: int }
  const r = await fetch('/api/llm/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      stream: false, // 비스트리밍 — 단일 JSON 응답 { text: "..." }
      max_tokens: 2048,
    }),
  });
  if (!r.ok) {
    const errText = await r.text().catch(() => '');
    throw new Error('LLM HTTP ' + r.status + ' — ' + errText.slice(0, 200));
  }
  const j = await r.json();
  return j.text || '';
}

// 자미두수 — 결정론 명반(命盤)을 백엔드에서 산출(ADR-010) 후 LLM 해석 주입.
//   1. /api/ziwei/chart 로 안성법 결정론 명반 산출 (명궁·12궁·14주성·오행국·사화)
//   2. 결정론 결과(prompt_meta)를 시스템 프롬프트에 주입 — LLM은 배치를 자체산출하지 않음
async function fetchZiwei({ year, month, day, birthHour, gender, name }) {
  // 결정론 명반 산출
  const iso = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  const chartRes = await fetch('/api/ziwei/chart', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      birth: iso,
      birth_hour: (typeof birthHour === 'number') ? birthHour : 12,
      gender: gender || 'M',
    }),
  });
  if (!chartRes.ok) {
    const errText = await chartRes.text().catch(() => '');
    throw new Error('ziwei chart HTTP ' + chartRes.status + ' — ' + errText.slice(0, 200));
  }
  const chart = await chartRes.json();

  // 결정론 배치를 프롬프트에 주입 (LLM은 해석만, 배치 변경 금지)
  const prompt = `당신은 자미두수(紫微斗數) 명리학 마스터입니다. 아래 결정론 엔진이 산출한 명반(命盤) 배치를 근거로만 한국어 400~600자 풀이를 해주세요.

${chart.prompt_meta}

[풀이 지침]
- 위 확정 배치(명궁·오행국·자미성·4대 궁 주성·생년사화)를 근거로만 풀이. 배치를 새로 만들지 마세요.
- 명궁(命宮)·재백궁(財帛宮)·관록궁(官祿宮)·복덕궁(福德宮) 4궁 중심으로.
- 명궁 주성과 생년사화의 결(흐름)을 부드럽게 연결.
- 단정 어조("반드시", "확실히", "운명적으로") 피하고 "결의 흐름이 보입니다", "기운이 흘러갑니다" 같이.
- 시작은 "✦ 자미두수로 보아 그대의 명궁(${chart.ming_branch_ko}궁)에는..." 같이 자연스럽게.
- 한자(漢字)는 처음 등장 시에만 괄호로 표기.`;
  return await callLLM(prompt);
}

async function fetchFace(base64DataUrl, gender, age) {
  // 카메라 캡쳐된 base64 dataURL을 그대로 사용 (face-camera.js)
  const r = await fetch('/api/face/reading', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_base64: base64DataUrl,
      gender,
      age: age || 30,
      school: 'korean',
    }),
  });
  if (!r.ok) {
    const errText = await r.text().catch(() => '');
    throw new Error('face HTTP ' + r.status + ' — ' + errText.slice(0, 200));
  }
  const j = await r.json();
  return j.text || j.reading || '관상 풀이 응답 없음';
}

async function fetchDream({ dreamText, name, gender, age }) {
  const r = await fetch('/api/dream/interpret', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dream_text: dreamText,
      name: name || null,
      gender,
      age: age || 30,
    }),
  });
  if (!r.ok) throw new Error('dream HTTP ' + r.status);
  const j = await r.json();
  return j.text || j.interpretation || j.body || '꿈 풀이 응답 없음';
}

async function fetchTarot(name) {
  // 3장 random — 메이저 아르카나 22장 중
  const drawn = [];
  const pool = [...TAROT_DECK];
  while (drawn.length < 3 && pool.length) {
    const idx = Math.floor(Math.random() * pool.length);
    drawn.push(pool.splice(idx, 1)[0]);
  }
  const prompt = `당신은 타로 리더입니다. ${name ? name + '님의' : '의뢰자의'} 종합 운세에 대해 다음 3장 카드로 한국어 풀이를 해주세요 (총 300~400자):

[과거 / 현재 / 미래] 스프레드
1. 과거: ${drawn[0]}
2. 현재: ${drawn[1]}
3. 미래: ${drawn[2]}

[풀이 지침]
- 각 카드 의미를 80~120자로 짚어주세요.
- 마지막에 종합 메시지 1~2문장.
- 단정 표현 피하고 흐름·결 중심. "보여집니다", "기운이 흐릅니다" 같이.
- 시작은 "✦ 첫 장 ${drawn[0]} ─ ..." 식으로.`;
  const text = await callLLM(prompt);
  return `**뽑은 카드**: ${drawn.join(' · ')}\n\n${text}`;
}

/**
 * 종합검진 실행 — 사주 결과 페이지에 자미두수/관상/꿈/타로 섹션 추가
 * @param {object} ctx - { name, surname, givenName, gender, year, month, day, hourBranch, birthHour }
 */
export async function runComprehensiveReadings(ctx) {
  const container = document.getElementById('comprehensiveResults');
  if (!container) return;

  const facePhotoBase64 = (typeof window.__getCapturedFacePhoto === 'function') ? window.__getCapturedFacePhoto() : null;
  const dreamText = document.getElementById('dreamTextInput')?.value?.trim();
  const age = ctx.year ? Math.max(1, new Date().getFullYear() - ctx.year) : 30;

  const sections = [];
  sections.push({ key: 'ziwei', emoji: '✦', title: '자미두수 (紫微斗數)', fetcher: () => fetchZiwei(ctx) });
  if (facePhotoBase64) sections.push({ key: 'face', emoji: '✦', title: '관상 (觀相)', fetcher: () => fetchFace(facePhotoBase64, ctx.gender, age) });
  if (dreamText) sections.push({ key: 'dream', emoji: '✦', title: '꿈해몽 (解夢)', fetcher: () => fetchDream({ dreamText, name: ctx.name, gender: ctx.gender, age }) });
  sections.push({ key: 'tarot', emoji: '✦', title: '타로 (Tarot)', fetcher: () => fetchTarot(ctx.name) });

  // 섹션 컨테이너 렌더링 (모두 로딩 상태)
  container.innerHTML = `
    <div class="comp-header">
      <h2 class="comp-title">✦ 종합검진 풀이</h2>
      <p class="comp-sub">사주 외에 ${sections.length}개 도메인을 함께 풀어드립니다</p>
    </div>
    ${sections.map(s => `
      <div class="comp-section" data-section="${s.key}">
        <h3 class="comp-section-title">${s.emoji} ${s.title}</h3>
        <div class="comp-section-content comp-loading">
          <span class="comp-spinner"></span> 풀이 중...
        </div>
      </div>
    `).join('')}
  `;

  // 병렬 호출 — 결과 도착 순서대로 표시
  await Promise.allSettled(sections.map(async (s) => {
    const sel = container.querySelector(`[data-section="${s.key}"] .comp-section-content`);
    try {
      const text = await s.fetcher();
      sel.classList.remove('comp-loading');
      const html = (window.simpleMarkdown ? window.simpleMarkdown(text) : `<p>${text.replace(/\n/g, '<br>')}</p>`);
      sel.innerHTML = html;
    } catch (e) {
      sel.classList.remove('comp-loading');
      sel.innerHTML = `<p class="comp-error">${s.title} 풀이를 받지 못했습니다. <small>${(e.message || e).toString().slice(0, 120)}</small></p>`;
    }
  }));
}

window.runComprehensiveReadings = runComprehensiveReadings;
