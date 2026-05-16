---
type: adr
adr_number: 7
status: accepted
date: 2026-05-17
authors: [Technoetic]
domain: [meta, infra]
---

# ADR-007: 지식 저장소로 Obsidian Vault (Git) 도입

## 배경

- 2인 개발 + SaaS 사업 목표
- 외부 보고서(딥리서치·명리학자 자문) 누적 시작
- 의사결정 근거 추적 필요 (왜 옵션 A 채택? 왜 §6 거부?)
- 운영 코드(engine/)와 인간 지식의 분리 필요

## 검토한 옵션

### A. Obsidian Vault (Git) — 채택
- 마크다운 평문, 도구 록인 0
- Git PR 리뷰 자연스러움
- AI 친화 (Claude/GPT가 직접 .md 읽고 쓰기)
- 추가 인프라 0, 비용 0

### B. Neo4j (그래프 DB)
- 풍부한 관계 쿼리 가능
- 인프라·호스팅 비용 + 학습 부담
- 2인 개발에 과한 무게

### C. Notion 외부 도구
- 록인 위험, repo 분리, AI 컨텍스트 부담

## 채택

**A 채택**. 단, Neo4j는 향후 점진 도입 가능성 열어둠 (Obsidian frontmatter → Cypher import).

## 폴더 구조

```
vault/
├── README.md
├── decisions/    — ADR
├── roadmap/      — 앞으로 할 작업
├── done/         — 완료 작업
├── schools/      — 학파 정리
├── reports/      — 외부 보고서
├── references/   — 출처 문헌
├── runbook/      — 운영 가이드
├── templates/    — 노트 양식
└── daily/        — 작업 일지
```

## 운영 원칙

1. 마크다운 평문 + frontmatter YAML 메타데이터
2. Git PR과 함께 vault 변경
3. 출처 명시 → references/ 별도 노트
4. ADR immutable — 새 결정은 새 ADR

## 결과

- 본 PR에서 vault/ 골격 + 7개 ADR + 3개 done 노트 + 템플릿 작성
- 코드 변경 0 (운영 영향 0)

## 향후

- Neo4j 도입 시점: 외부 보고서 누적되어 정형 데이터 많아질 때
- Obsidian Sync 유료 도입: 모바일 액세스 필요 시
