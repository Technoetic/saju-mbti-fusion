---
type: done
status: applied
date: 2026-05-17
domain: [saju, meta]
related:
  - decisions/ADR-014-saju-mbti-prediction-exception.md
  - reports/saju-mbti-correlation.md
commit: TBD
---

# 사주 → MBTI 4축 경향성 추정 (ADR-014 예외 결정)

## 무엇

사용자 명시적 예외 결정 (2026-05-17). [[../reports/saju-mbti-correlation]]
거부 사례 1호에 대해 본 시스템 자체 매핑 규칙으로 부분 예외.

## 변경 사항

### 신규 모듈
- [engine/divination/saju_mbti_predictor.py](../../engine/divination/saju_mbti_predictor.py)
  · `MbtiTendency` 4축 라벨 + 결정 근거 데이터 모델
  · `derive_mbti_tendency(saju)` — 사주 dict → 4축 경향성
  · `format_tendency_for_persona(t)` — 만월 아씨 페르소나 출력 (면책 내장)
  · 4축 매핑 함수 4개 (`_map_ei`, `_map_sn`, `_map_tf`, `_map_jp`)
  · DISCLAIMER_KO 상수

### 신규 테스트
- [engine/divination/test_saju_mbti_predictor.py](../../engine/divination/test_saju_mbti_predictor.py) — 26 PASS
  · 데이터 모델 2
  · 음양 비율 3 (전양·전음·균형)
  · EI 매핑 3 (E·I·미정)
  · SN 매핑 3
  · TF 매핑 3
  · JP 매핑 3
  · 메인 진입 3 (full saju·empty·korean day master)
  · ADR-014 안전 장치 5
    - 16유형 단정 절대 금지
    - 면책 의무 검증
    - 페르소나 어투 검증
    - 단정 표현 금지
    - 4축 미정 안전 응답
  · 결정론 보장 1

## 매핑 규칙 (옵션 A 정신 유지, 본 시스템 자체)

| MBTI 축 | 매핑 | 미정 영역 |
|---|---|---|
| E vs I | 8글자 중 양 비율 | 0.45 ~ 0.55 |
| S vs N | (土+金)/total vs (木+水)/total | 둘 다 < 0.4 |
| T vs F | 金+양간 / 火+水+음간 | 명확 신호 부재 |
| J vs P | 오행 분포 표준편차 | 0.5 ~ 1.0 |

각 축은 명확한 신호 없으면 "미정" 반환 — 단정 회피의 핵심 안전 장치.

## ADR-014 사용자 출력 의무 모두 회귀로 검증

- ✅ 16유형 단정 (ENFJ 등) 절대 미출력
- ✅ "당신의 MBTI는 X입니다" 단정 표현 금지
- ✅ 면책 메시지("자체 매핑이며 정통 진단이 아닙니다") 의무 포함
- ✅ 페르소나 어투 ("결" / "기운") 유지
- ✅ 4축 모두 미정 시 안전 응답

## 라이브 시나리오 검증

사주 1990-05-15 14:00 입력:
- 4축 라벨: `미정-미정-F-미정` (3축 미정)
- 출력: "감정(F)의 기운이 흐르는구먼. 그대 본인이 알고 계신 MBTI와 견주어 보시게."
- 면책 자동 첨부

→ 단정 회피 정신 그대로 동작. 명확한 신호 없는 축은 미정 처리.

## vault

- vault/decisions/ADR-014-saju-mbti-prediction-exception.md 신규
- vault/decisions/INDEX.md / vault/done/INDEX.md 갱신
- reports/saju-mbti-correlation.md applied_to 갱신 (예외 명시)

## 통합 정책

본 PR은 **모듈 신설만**. 만월 아씨 페르소나 통합(web/server.py 또는
engine/saju/explain.py에서 호출)은 별도 PR — 프론트엔드 UX 흐름 결정
선행 필요:

- 사주 풀이 본문에 자동 포함?
- 별도 섹션으로 분리?
- 사용자 MBTI 입력 전/후 비교 표시?

## 면책

- 본 결정은 사용자 명시적 예외 (2026-05-17)
- ADR-002·010 정신은 출력 형식에 보존 (단정 회피·면책 의무)
- 본 시스템 매핑이 정통 명리학·심리학과 다를 수 있음 명시

## 향후

- SaaS 운영 후 매핑 정확도 측정 가능 (사용자 자기보고 MBTI와 비교)
- 정확도 표시는 절대 금지 (자기실현적 예언 회피)
- 매핑 규칙 보정 데이터 누적 후 검토 가능
