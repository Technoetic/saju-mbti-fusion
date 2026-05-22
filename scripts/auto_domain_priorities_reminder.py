"""ADR-155 — /domain-priorities 재호출 자동 알림 영속.

/domain-priorities 잔여 #5 부분 해소 — 슬래시 명령어 직접 호출은 Claude Code 인터랙티브
세션 의존이라 cron 불가하나, 호출 시점 도래 + 결손 자동 추출은 본 AI 단독 가능.

본 스크립트:
  1. 마지막 /domain-priorities 호출 일자 추출 (vault/reports/domain-priorities-*.md)
  2. 경과 일수 계산
  3. 1개월+ 경과 시 재호출 알림 메시지 출력 (GitHub Actions로 cron 가능)
  4. 결손 영역 자동 추출 (ADR-*.md frontmatter "한계 (정직)" 절)

GitHub Actions cron (.github/workflows/domain-priorities-reminder.yml)에서 매월 1일 호출 가능.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path


VAULT_REPORTS = Path("vault/reports")
VAULT_DECISIONS = Path("vault/decisions")
REMINDER_INTERVAL_DAYS = 30


def get_last_domain_priorities_date() -> date | None:
    """vault/reports/domain-priorities-YYYY-MM-DD.md 최신 일자 추출."""
    if not VAULT_REPORTS.exists():
        return None
    files = list(VAULT_REPORTS.glob("domain-priorities-*.md"))
    dates: list[date] = []
    for f in files:
        m = re.match(r"domain-priorities-(\d{4})-(\d{2})-(\d{2})\.md", f.name)
        if m:
            dates.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return max(dates) if dates else None


def days_since_last_call(today: date | None = None) -> int | None:
    """마지막 호출 이후 경과 일수."""
    last = get_last_domain_priorities_date()
    if last is None:
        return None
    today = today or date.today()
    return (today - last).days


def is_recall_due(today: date | None = None) -> bool:
    """재호출 시점 도래 여부 (1개월+ 경과)."""
    days = days_since_last_call(today)
    return days is not None and days >= REMINDER_INTERVAL_DAYS


def extract_limit_sections_from_adrs() -> dict[str, list[str]]:
    """ADR-*.md frontmatter '## 한계 (정직)' 절 자동 추출.

    Returns:
        {ADR-NNN: [한계 텍스트 라인...]}
    """
    if not VAULT_DECISIONS.exists():
        return {}
    out: dict[str, list[str]] = {}
    for f in sorted(VAULT_DECISIONS.glob("ADR-*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.search(r"##\s*한계\s*\(정직\)\s*\n+(.*?)(?=\n##|\Z)", text, re.DOTALL)
        if m:
            lines = [ln.strip("- ").strip() for ln in m.group(1).strip().split("\n") if ln.strip().startswith("-")]
            if lines:
                out[f.stem] = lines
    return out


def format_reminder_message(today: date | None = None) -> str:
    """알림 메시지 (GitHub Actions stdout 또는 Slack 알림용)."""
    today = today or date.today()
    days = days_since_last_call(today)
    last = get_last_domain_priorities_date()
    limits = extract_limit_sections_from_adrs()
    total_gaps = sum(len(v) for v in limits.values())

    if days is None:
        return "[ADR-155 reminder] /domain-priorities 호출 기록 부재 — 초기 호출 권장."
    if not is_recall_due(today):
        return (
            f"[ADR-155 reminder] 마지막 /domain-priorities 호출: {last} ({days}일 전). "
            f"재호출 임계 {REMINDER_INTERVAL_DAYS}일 미도래."
        )
    return (
        f"[ADR-155 reminder] /domain-priorities 재호출 권장 — "
        f"마지막 호출 {last} ({days}일 전, 임계 {REMINDER_INTERVAL_DAYS}일 초과). "
        f"ADR 한계 절 자동 추출 결과 {len(limits)} ADR × {total_gaps} 결손 잠재."
    )


def main() -> int:
    print(format_reminder_message())
    return 0 if not is_recall_due() else 1  # exit 1 = Actions 알림 트리거


if __name__ == "__main__":
    sys.exit(main())
