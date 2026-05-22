// ADR-153 (2026-05-23) — 학파 옵션 토글 UI 컴포넌트
//
// /domain-priorities #10 (사용자 결단) 해소.
// ADR-141·142·145·153 학파 옵션 (option A 디폴트 + option B/C) 사용자 노출.
//
// 사용처:
//   · saju 합국 강도 (ADR-141 — 학파 가중치 옵션)
//   · saju 12 신살 (ADR-142 — basis="year"|"day")
//   · yutjeom (ADR-145 — school="folkmuseum"|"mo_separate")
//   · saju 신살 시너지 (ADR-153 — school="standard"|"conservative"|"emphatic")
//
// 정책 (CLAUDE.md §6, ADR-006·010·015 정합):
//   · 디폴트 옵션 명시 (별도 학파 선택 안 했을 때 표시)
//   · 옵션 변경 시 사용자에게 학파 의미 짧게 설명
//   · 단정 어휘 0건 (반드시·확실히·100%·절대 금지)
//   · 면책 자동 포함 (ADR-006 정합)

/**
 * @typedef {Object} SchoolOption
 * @property {string} key - 옵션 키 (예: 'standard', 'conservative')
 * @property {string} label - 사용자 노출 한국어 라벨
 * @property {string} description - 짧은 설명 (1줄)
 * @property {boolean} isDefault - 디폴트 여부
 */

/**
 * @typedef {Object} SchoolToggleConfig
 * @property {string} containerId - 토글 컨테이너 DOM id
 * @property {string} title - 토글 영역 제목 (예: "신살 학파 선택")
 * @property {SchoolOption[]} options - 옵션 배열
 * @property {function(string): void} onSelect - 옵션 변경 콜백 (key 전달)
 * @property {string} [adrRef] - ADR 참조 (예: 'ADR-153')
 */

/**
 * 학파 옵션 토글 UI 렌더링.
 * @param {SchoolToggleConfig} config
 * @returns {{select: function(string): void, getSelected: function(): string}}
 */
export function renderSchoolToggle(config) {
  const container = document.getElementById(config.containerId);
  if (!container) {
    console.warn(`[school-toggle] container '${config.containerId}' not found`);
    return { select: () => {}, getSelected: () => '' };
  }

  const defaultOpt = config.options.find((o) => o.isDefault) || config.options[0];
  let selected = defaultOpt.key;

  function render() {
    const adrTag = config.adrRef ? `<span class="school-toggle-adr">[${config.adrRef}]</span>` : '';
    const buttons = config.options
      .map(
        (opt) => `
        <button type="button"
                class="school-toggle-btn ${opt.key === selected ? 'school-toggle-btn-active' : ''}"
                data-school-key="${opt.key}"
                title="${opt.description}">
          ${opt.label}
          ${opt.isDefault ? '<span class="school-toggle-default-mark">★</span>' : ''}
        </button>
      `
      )
      .join('');

    const currentOpt = config.options.find((o) => o.key === selected);
    const description = currentOpt ? currentOpt.description : '';

    container.innerHTML = `
      <div class="school-toggle">
        <div class="school-toggle-header">
          <span class="school-toggle-title">${config.title}</span>
          ${adrTag}
        </div>
        <div class="school-toggle-buttons">
          ${buttons}
        </div>
        <p class="school-toggle-description">${description}</p>
        <p class="school-toggle-disclaimer">
          ※ 학파 선택은 결정론 계산 옵션이며, 운명·결혼·이별 단정 X.
          참고용으로만 사용하시오 (ADR-006 정합).
        </p>
      </div>
    `;

    // 이벤트 바인딩
    container.querySelectorAll('.school-toggle-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.schoolKey;
        if (!key || key === selected) return;
        selected = key;
        render();
        if (typeof config.onSelect === 'function') {
          config.onSelect(key);
        }
      });
    });
  }

  render();

  return {
    select: (key) => {
      if (config.options.some((o) => o.key === key)) {
        selected = key;
        render();
      }
    },
    getSelected: () => selected,
  };
}

// ─────────────────────────── 사전 정의 학파 옵션 풀 ───────────────────────────

/** ADR-141 saju 합국 강도 (월지·일지·년시지 가중치) */
export const SAJU_GUK_STRENGTH_OPTIONS = [
  {
    key: 'jajeong_jinjeon',
    label: '자평진전 (정통)',
    description: '월지 1.0 / 일지 0.7 / 년·시지 0.5 (자평진전 정통 표준).',
    isDefault: true,
  },
];

/** ADR-142 saju 12 신살 기준 (연주 vs 일주) */
export const SAJU_SINSAL_BASIS_OPTIONS = [
  {
    key: 'year',
    label: '연주 기준 (자평진전)',
    description: '출생 연도 지지 기준 12 신살 — 자평진전 정통 디폴트.',
    isDefault: true,
  },
  {
    key: 'day',
    label: '일주 기준 (명리정종)',
    description: '일주 지지 기준 12 신살 — 명리정종 옵션 B.',
    isDefault: false,
  },
];

/** ADR-145 yutjeom 사위 학파 (4사위 vs 5사위) */
export const YUTJEOM_SCHOOL_OPTIONS = [
  {
    key: 'folkmuseum',
    label: '4사위 64괘 (정통)',
    description: '도·개·걸·윷 4사위 — 국립민속박물관 정통 (모는 윷과 동일).',
    isDefault: true,
  },
  {
    key: 'mo_separate',
    label: '5사위 125괘 (지역 변형)',
    description: '도·개·걸·윷·모 5사위 — 모를 별개 사위로 처리 (옵션 B).',
    isDefault: false,
  },
];

/** ADR-153 saju 신살 시너지 가중치 학파 */
export const SAJU_SYNERGY_SCHOOL_OPTIONS = [
  {
    key: 'standard',
    label: '표준 (ADR-133)',
    description: '시너지 1개 1.0 / 2개 1.5 / 3개 2.0 — 보고서 §6.3 정통.',
    isDefault: true,
  },
  {
    key: 'conservative',
    label: '보수 학파',
    description: '시너지 1개 0.8 / 2개 1.4 / 3개 1.8 — 신살 영향 약화 학파.',
    isDefault: false,
  },
  {
    key: 'emphatic',
    label: '강조 학파',
    description: '시너지 1개 1.2 / 2개 1.8 / 3개 2.5 — 신살 영향 강화 학파.',
    isDefault: false,
  },
];

/** ADR-155 star compatibility 분석 학파 (element vs element+modality) */
export const STAR_COMPATIBILITY_OPTIONS = [
  {
    key: 'element_only',
    label: 'element 호환 (디폴트)',
    description: '4 element (불·흙·바람·물) 동기·보완·이질 분류 — Liz Greene 1976 정통.',
    isDefault: true,
  },
  {
    key: 'element_modality',
    label: 'element + modality',
    description: '4 element + 3 modality (활동·고정·변동) 가중 — Stephen Arroyo 1975 정밀.',
    isDefault: false,
  },
];

/** ADR-155 tojeong 시구 출처 학파 (ADR-134 11괘 본문화 + 합성) */
export const TOJEONG_VERSE_SOURCE_OPTIONS = [
  {
    key: 'synthesized_only',
    label: '흐름 톤만 (디폴트)',
    description: '본 시스템 자체 흐름 톤 144괘 — 운명 단정 X.',
    isDefault: true,
  },
  {
    key: 'mixed_original',
    label: '원문 시구 우선 (11괘)',
    description: 'ADR-134 한국학중앙연구원 인증본 11괘는 원문 시구 + 나머지 흐름 톤.',
    isDefault: false,
  },
];
