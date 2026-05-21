"""/domain-priorities 실행 스크립트 — ADR 결손 5 차원 점수화."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
adr_dir = ROOT / 'vault/decisions'
gaps = []

for adr_file in sorted(adr_dir.glob('ADR-*.md')):
    src = adr_file.read_text(encoding='utf-8')
    title_m = re.search(r'^title: (.+)$', src, re.MULTILINE)
    title = (title_m.group(1) if title_m else adr_file.stem).strip()
    adr_num = adr_file.stem.split('-')[1]

    domain = 'general'
    title_lower = title.lower()
    if 'saju' in title_lower or '사주' in title or '십성' in title or '신살' in title or '명리' in title or 'pillars' in title_lower or 'shensha' in title_lower or 'tengods' in title_lower:
        domain = 'saju'
    elif 'face' in title_lower or '관상' in title:
        domain = 'face'
    elif 'palm' in title_lower or '손금' in title:
        domain = 'palm'
    elif 'name' in title_lower or '성명' in title or '작명' in title or 'baleum' in title_lower:
        domain = 'name'
    elif 'dream' in title_lower or '꿈' in title or '해몽' in title:
        domain = 'dream'
    elif 'hwapae' in title_lower or '화패' in title:
        domain = 'hwapae'
    elif 'star' in title_lower or '별' in title or '황도' in title:
        domain = 'star'
    elif 'mbti' in title_lower:
        domain = 'mbti'
    elif 'compat' in title_lower or '궁합' in title:
        domain = 'compat'

    limit_m = re.search(r'한계 \(정직\)\s*\n([\s\S]+?)(?=\n## |\Z)', src)
    if not limit_m:
        continue
    limits_text = limit_m.group(1)
    fails = re.findall(r'❌\s*\*\*([^*]+)\*\*[^\n—]*[—:]\s*([^\n]+)', limits_text)
    for marker, desc in fails:
        gaps.append({
            'adr': adr_num, 'title': title, 'domain': domain,
            'marker': marker.strip(), 'desc': desc.strip()[:250],
        })


def score(gap: dict) -> tuple:
    desc = (gap['desc'] + ' ' + gap['marker']).lower()

    # ① 사용자 위해
    if any(w in desc for w in ['결혼','이혼','의료','금융','파산','사망']):
        harm = 5
    elif any(w in desc for w in ['단정','자문','면책','크리시스','크라이시스']):
        harm = 4
    elif any(w in desc for w in ['프라이버시','동의','법무','변호사','gdpr','pipa']):
        harm = 3
    elif any(w in desc for w in ['평가','학파','다학파']):
        harm = 2
    else:
        harm = 1

    # ② 라이브 트래픽
    if any(w in desc for w in ['오늘의 운세','만월','라이브','content/reading','사용자 출력']):
        traffic = 5
    elif gap['domain'] in ['saju','dream','compat'] and any(w in desc for w in ['llm','인용','지시','시스템 프롬프트']):
        traffic = 4
    elif gap['domain'] in ['saju','dream','compat','name','face','palm']:
        traffic = 3
    elif gap['domain'] in ['star','hwapae','mbti']:
        traffic = 2
    else:
        traffic = 1

    # ③ 비용 (- 부호)
    if any(w in desc for w in ['사용자 결단','사업','법무','변호사','학술 구매','kci 폐쇄','구매']):
        cost = 5
    elif any(w in desc for w in ['외부 api','secret','권한','인증','fly cli','data.go.kr']):
        cost = 4
    elif any(w in desc for w in ['llm 100% 준수 보장 x','temperature','자율성','보장 x']):
        cost = 3
    elif any(w in desc for w in ['vision','keypoint','mediapipe','이미지 처리']):
        cost = 3
    elif any(w in desc for w in ['모듈','함수','wire','지시 추가','명시']):
        cost = 1
    else:
        cost = 2

    # ④ 출처
    if any(w in desc for w in ['kasi','kci','isbn','학파','학술','공인','출처 명시']):
        source = 5
    elif any(w in desc for w in ['추정','임의','검증 x','가짜']):
        source = 0
    else:
        source = 3

    # ⑤ ADR 위반
    if 'adr-006' in desc or '자문' in desc:
        risk = 5
    elif 'adr-010' in desc or '사실성' in desc or '환각' in desc:
        risk = 4
    elif 'adr-002' in desc or '학파' in desc:
        risk = 3
    elif 'adr-' in desc:
        risk = 2
    else:
        risk = 1

    total = (harm * 3) + (traffic * 3) + (source * 2) + (risk * 2) - cost
    return harm, traffic, cost, source, risk, total


for g in gaps:
    h, t, c, s, r, total = score(g)
    g.update(harm=h, traffic=t, cost=c, source=s, risk=r, total=total)
    g['solo'] = '✅' if c <= 2 else ('⚠' if c <= 3 else '🔵')

gaps.sort(key=lambda x: -x['total'])

immediate = [g for g in gaps if g['total'] >= 50]
short_term = [g for g in gaps if 30 <= g['total'] < 50]
ops = [g for g in gaps if 10 <= g['total'] < 30]
deferred = [g for g in gaps if g['total'] < 10]

print(f'=== 결손 총 {len(gaps)}건 ===')
print(f'🔴 즉시 (≥50): {len(immediate)}건')
print(f'🟡 단기 (30~49): {len(short_term)}건')
print(f'🟢 운영 후 (10~29): {len(ops)}건')
print(f'⏸ 보류 (<10): {len(deferred)}건')
print()
print('=== 상위 10건 ===')
for g in gaps[:10]:
    print(f"  [{g['total']}점·{g['solo']}] ADR-{g['adr']} {g['domain']}: {g['marker']}")
print()
print('=== 본 AI 단독 + 점수 30+ ===')
solo_imm = [g for g in gaps if g['solo'] == '✅' and g['total'] >= 30]
for g in solo_imm[:10]:
    print(f"  [{g['total']}] ADR-{g['adr']} {g['domain']}: {g['marker']}")

domain_label = {
    'saju': '사주(만월)', 'face': '관상(운학)', 'palm': '손금(옥선)',
    'name': '성명(묵향)', 'dream': '꿈(몽이)', 'hwapae': '화패(화선)',
    'star': '별(성하)', 'mbti': 'MBTI', 'compat': '궁합', 'general': '일반',
}


def render_table(gaps_list: list, hdr: str = '순위') -> str:
    if not gaps_list:
        return '_(해당 없음)_'
    lines = [f'| {hdr} | 점수 | 도메인 | ADR | 결손 | 본 AI 단독 |',
             '|---|---|---|---|---|---|']
    for i, g in enumerate(gaps_list, 1):
        marker = g['marker'][:60]
        lines.append(
            f"| {i} | {g['total']} | {domain_label.get(g['domain'], g['domain'])} | ADR-{g['adr']} | {marker} | {g['solo']} |"
        )
    return '\n'.join(lines)


out_dir = ROOT / 'vault/reports'
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'domain-priorities-2026-05-21.md'

md_parts = []
md_parts.append(f'''---
type: domain_priorities
generated: 2026-05-21
generated_by: /domain-priorities
total_gaps: {len(gaps)}
immediate: {len(immediate)}
short_term: {len(short_term)}
operational: {len(ops)}
deferred: {len(deferred)}
methodology: 5_dimension_scoring
formula: "(harm * 3) + (traffic * 3) + (source * 2) + (risk * 2) - cost"
max_score: 73
---

# /domain-priorities 결과 - 본 시스템 도메인 지식 우선순위 매트릭스

본 보고서는 https://saju-mbti-fusion.fly.dev/ 사주·MBTI·관상·작명·해몽·손금·화패 SaaS의
9 도메인 결손 영역을 5 차원 정량 점수화한 우선순위 매트릭스이다.

**총 {len(gaps)}건 결손** (vault/decisions/ ADR 한계 절에서 자동 추출).

## 1. 우선순위 매트릭스

### 🔴 즉시 진행 (점수 ≥ 50) - {len(immediate)}건
''')
md_parts.append(render_table(immediate))
md_parts.append(f'\n\n### 🟡 단기 진행 (30~49) - {len(short_term)}건\n')
md_parts.append(render_table(short_term[:20]))
if len(short_term) > 20:
    md_parts.append(f'\n\n_... 외 {len(short_term)-20}건_')

md_parts.append(f'\n\n### 🟢 운영 데이터 후 (10~29) - {len(ops)}건\n')
md_parts.append(render_table(ops[:15]))
if len(ops) > 15:
    md_parts.append(f'\n\n_... 외 {len(ops)-15}건_')

md_parts.append(f'\n\n### ⏸ 보류 (<10) - {len(deferred)}건\n')
md_parts.append(render_table(deferred[:10]))
if len(deferred) > 10:
    md_parts.append(f'\n\n_... 외 {len(deferred)-10}건_')

md_parts.append('\n\n## 2. 상위 5건 정밀 분석\n')
for i, g in enumerate(gaps[:5], 1):
    md_parts.append(f'''
### {i}. ADR-{g['adr']} ({domain_label.get(g['domain'], g['domain'])}) - **{g['total']}점**

- **결손**: {g['marker']}
- **상세**: {g['desc']}
- **차원 점수**: 위해={g['harm']}/5 · 트래픽={g['traffic']}/5 · 비용={g['cost']}/5 · 출처={g['source']}/5 · ADR위반={g['risk']}/5
- **본 AI 단독 진행**: {g['solo']}
''')

md_parts.append('\n## 3. 본 AI 단독 진행 가능 영역 (즉시 착수 가능)\n\n')
md_parts.append('본 AI가 사용자 결단 없이 즉시 진행 가능 (cost ≤ 2):\n\n')
md_parts.append(render_table(solo_imm[:15]))

md_parts.append('\n\n## 4. 사용자 결단 영역 (🔵 - cost ≥ 4)\n\n')
md_parts.append('본 AI 단독 진행 불가 - 사업·법무·학술 구매·외부 API 키 결단:\n\n')
biz = [g for g in gaps if g['solo'] == '🔵' and g['total'] >= 10]
md_parts.append(render_table(biz[:15]))

md_parts.append('''

## 5. 운영 데이터 의존 영역

실 트래픽 누적 후 측정·검증 가능한 영역:

- ADR-098 dream Flash A/B (현 사용자 미사용 단계)
- ADR-093 균형도 객관 측정 (실 사용자 트래픽 후)
- 라이브 LLM 실호출 검증 (E2E 테스트 미비 영역)

## 6. 다음 단계 추천

본 AI 단독 진행 가능 + 점수 ≥ 50 (즉시) 또는 ≥ 30 (단기) 우선.

상위 본 AI 단독 진행 가능 후보:
''')

for g in solo_imm[:5]:
    md_parts.append(f"\n- ADR-{g['adr']} {domain_label.get(g['domain'], g['domain'])}: **{g['marker']}** ({g['total']}점)")

md_parts.append('''

진행 신호 시 즉시 착수. 또는 옵션 결단 후 사용자 결단 영역 진행.

## 면책

본 보고서는 **결손 우선순위 결단 도구**이며 **사용자 운명 단정 X**. 본 점수는 메타 메트릭이며
사용자 출력 면책과 무관 (메타 명령어 영역).

본 점수 산출 방식 (휴리스틱)은 키워드 기반이며 LLM 추론 X. 시간 경과·신규 ADR 추가 시 재호출 권장.
''')

md = ''.join(md_parts)
out_path.write_text(md, encoding='utf-8')
print(f'\n저장: {out_path}')
print(f'크기: {len(md)}자')
