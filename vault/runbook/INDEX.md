---
type: index
section: runbook
last_updated: 2026-05-17
---

# 운영 가이드

배포·롤백·라이브 점검·일상 운영.

## 배포

- 자동 배포: GitHub Actions (`.github/workflows/deploy.yml`)
- 트리거: `main` 브랜치 push
- 워크플로 상태: `gh run list --limit 3`

## 라이브 점검

```bash
# Railway SSH
railway ssh "python3 -c 'from engine.divination.name_unihan import total_chars; print(total_chars())'"
# 정상: 8525
```

## 한자 풀 데이터 갱신

```bash
# Unihan 원본 zip 갱신 (드물게)
cd data/unihan && python -c "
import urllib.request
urllib.request.urlretrieve('https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip', 'Unihan.zip')
"
# JSON 재생성
python data/unihan/build_korean_hanja.py
# Docker 재배포 — Dockerfile이 COPY data 자동 포함
git add data/korean_hanja_unihan.json && git commit && git push
```

## 운영표준 점검 (관상 영역)

`engine/safety/quick_check` 모듈 + 라이브 호출.

## 알람 채널

(TODO: 운영 시작 시 작성)
- Slack 채널·PagerDuty·이메일 등

## 사고 대응

(TODO: 운영표준 §14.7 incident_playbook 모듈 매핑)

## 백업·복구

- DB: 현재 없음 (stateless API)
- 캐시: `step_archive/face_reading_cache/` — Railway volume
- 한자 풀: Docker image에 내장 (재배포로 복원)
