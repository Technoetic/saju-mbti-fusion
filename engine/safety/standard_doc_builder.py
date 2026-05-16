"""운영 표준 문서 빌더 — 운영표준 §14.5 본문화.

compliance_report.COMPLIANCE_MANIFEST를 사람-읽기 가능한 마크다운/JSON 운영
매뉴얼로 변환. 규제 감사·신규 입사자 온보딩·외부 공시에 즉시 사용 가능한 형식.

§14.5 출력:
  · build_markdown_report() — 마크다운 (운영 매뉴얼)
  · build_json_summary()    — 외부 시스템 인제스트용 구조화 JSON
  · build_audit_letter()    — 규제 감사용 1페이지 요약 (한국어)

본 모듈은 compliance_report에 의존하지만 역방향 의존은 없음. 정적 텍스트만
생성, 부수효과 X.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


# §14.5 헤더 텍스트
_REPORT_HEADER_KO = "# 운영표준 점검 보고서 — face_reading 시스템"
_REPORT_HEADER_EN = "# Operational Standard Compliance Report — face_reading"


# ─────────────────────────── markdown ───────────────────────────

def build_markdown_report(
    *,
    lang: str = "ko",
    include_evidence: bool = True,
) -> str:
    """compliance_report 결과를 마크다운 매뉴얼로 변환.

    Args:
        lang: 'ko'/'en' 헤더 언어
        include_evidence: 각 항목에 발견된 심볼 목록 포함 여부
    """
    from engine.safety.compliance_report import generate_report
    report = generate_report()
    lines: list[str] = []

    header = _REPORT_HEADER_KO if lang == "ko" else _REPORT_HEADER_EN
    lines.append(header)
    lines.append("")
    lines.append(f"_Generated at: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")
    lines.append(f"- **Coverage:** {report.coverage_percent}% "
                 f"({report.implemented_count}/{report.total_items})")
    if report.missing_items:
        lines.append(f"- **Missing items:** {len(report.missing_items)} "
                     f"({', '.join(report.missing_items[:5])}...)")
    else:
        lines.append("- **All items implemented.**")
    lines.append(f"- **Regulatory anchors:** {len(report.anchors_covered)} unique")
    lines.append("")
    lines.append("## Items")
    lines.append("")

    for item in report.items:
        status = "OK" if item.implemented else "MISSING"
        lines.append(f"### `{item.item_id}` — {status}")
        lines.append(f"- **Module:** `{item.module}`")
        if item.regulatory_anchors:
            lines.append(f"- **Regulatory anchors:** "
                         f"{', '.join(item.regulatory_anchors)}")
        if include_evidence and item.evidence:
            lines.append(f"- **Symbols (verified):** "
                         f"{', '.join(f'`{s}`' for s in item.evidence)}")
        if item.missing_symbols:
            lines.append(f"- **Missing symbols:** "
                         f"{', '.join(f'`{s}`' for s in item.missing_symbols)}")
        if item.error:
            lines.append(f"- **Error:** {item.error}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────── JSON ───────────────────────────

def build_json_summary() -> dict[str, Any]:
    """구조화 JSON 요약 — 외부 시스템 인제스트용 (Datadog/Splunk)."""
    from engine.safety.compliance_report import generate_report
    report = generate_report()
    return {
        "service": "face_reading",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "coverage_percent": report.coverage_percent,
        "implemented_count": report.implemented_count,
        "total_items": report.total_items,
        "missing_items": list(report.missing_items),
        "anchors_covered": list(report.anchors_covered),
        "items": [
            {
                "item_id": it.item_id,
                "implemented": it.implemented,
                "module": it.module,
                "evidence_count": len(it.evidence),
                "missing_symbols": list(it.missing_symbols),
                "anchors": list(it.regulatory_anchors),
                "error": it.error,
            }
            for it in report.items
        ],
    }


def build_json_string(*, indent: int = 2) -> str:
    """build_json_summary 결과를 마크다운 친화적 들여쓰기 문자열로."""
    return json.dumps(build_json_summary(), ensure_ascii=False, indent=indent)


# ─────────────────────────── 감사 1페이지 ───────────────────────────

def build_audit_letter(*, organization: str = "내부 감사팀") -> str:
    """규제 감사용 1페이지 요약 (한국어 사극풍 X, 격식체).

    GDPR Art.30 처리 활동 기록 / KR PIPA §31 자료 제출 시 사용.
    """
    from engine.safety.compliance_report import generate_report
    report = generate_report()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 핵심 규제 앵커만 선별 (앞 10개)
    key_anchors = report.anchors_covered[:10]

    lines: list[str] = []
    lines.append(f"수신: {organization}")
    lines.append(f"발신: face_reading 운영팀")
    lines.append(f"일자: {now_str}")
    lines.append("제목: face_reading 운영표준 점검 결과 통보")
    lines.append("")
    lines.append("귀 감사팀의 자료 제출 요청에 따라 face_reading 시스템의 운영표준 "
                 "준수 현황을 아래와 같이 보고드립니다.")
    lines.append("")
    lines.append("1. 점검 결과 요약")
    lines.append(f"   · 점검 항목 총수: {report.total_items}건")
    lines.append(f"   · 구현 완료: {report.implemented_count}건 "
                 f"({report.coverage_percent}%)")
    if report.missing_items:
        lines.append(f"   · 미구현: {len(report.missing_items)}건")
        lines.append(f"     ({', '.join(report.missing_items[:5])})")
    else:
        lines.append("   · 미구현: 0건")
    lines.append("")
    lines.append("2. 적용 규제 (주요)")
    for a in key_anchors:
        lines.append(f"   · {a}")
    lines.append("")
    lines.append("3. 자료 제출 형식")
    lines.append("   · 마크다운 보고서: build_markdown_report() 호출")
    lines.append("   · JSON 인제스트: build_json_summary() 호출")
    lines.append("   · 실시간 점검: engine.safety.run_quick_check()")
    lines.append("")
    lines.append("4. 후속 조치")
    if report.missing_items:
        lines.append("   · 미구현 항목 보강 후 재점검 일정 별도 보고 예정.")
    else:
        lines.append("   · 모든 항목 구현 확인. 분기별 정기 재점검 유지.")
    lines.append("")
    lines.append("이상 보고드립니다.")
    return "\n".join(lines)
