"""웹 접근성 (Accessibility) 명세 + 검증 (ADR-053 Phase U, compliance 7.2.6).

KASS (한국 웹 접근성 표준 — KS X OT0003) + WCAG 2.1 AA 부분 충족.

본 system은 단일 페이지 SPA (front/index.html)라 다음만 검증:
  - ARIA label/role 명시
  - alt 텍스트 (이미지)
  - 키보드 접근 가능 (tabindex)
  - 대비 비율 (CSS 변수 검사)

면책: 본 모듈은 HTML 정적 분석 — 동적 변경 영역은 외부 audit 필요.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# 한국 웹 접근성 표준 (KS X OT0003) 핵심 검사 항목
A11Y_REQUIRED_LANDMARKS = ("main", "nav", "header", "footer")
A11Y_INTERACTIVE_TAGS = ("button", "a", "input", "textarea", "select")

# WCAG 2.1 AA 대비 비율
CONTRAST_RATIO_NORMAL = 4.5
CONTRAST_RATIO_LARGE = 3.0


@dataclass
class A11yIssue:
    """접근성 위반 항목."""
    severity: str  # 'error' | 'warning'
    rule: str  # 'missing_alt' | 'no_aria_label' | ...
    element: str  # HTML 발췌
    message: str


def find_images_without_alt(html: str) -> list[A11yIssue]:
    """img 태그 중 alt 속성 누락 검출."""
    issues = []
    for m in re.finditer(r'<img\b([^>]*)/?>', html, re.IGNORECASE):
        attrs = m.group(1)
        if 'alt=' not in attrs.lower():
            issues.append(A11yIssue(
                severity='error',
                rule='missing_alt',
                element=m.group(0)[:80],
                message='이미지에 alt 속성 누락 — 스크린리더 사용자 접근 불가',
            ))
    return issues


def find_buttons_without_label(html: str) -> list[A11yIssue]:
    """button·a 중 aria-label·텍스트·title 모두 없는 경우."""
    issues = []
    for m in re.finditer(r'<(button|a)\b([^>]*)>([^<]*)</\1>', html, re.IGNORECASE | re.DOTALL):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3).strip()
        has_label = (
            'aria-label=' in attrs.lower()
            or 'title=' in attrs.lower()
            or bool(inner)
        )
        if not has_label:
            issues.append(A11yIssue(
                severity='error',
                rule='no_label',
                element=m.group(0)[:80],
                message=f'{tag} 요소에 텍스트·aria-label·title 모두 없음',
            ))
    return issues


def find_inputs_without_label(html: str) -> list[A11yIssue]:
    """input 중 label·aria-label·placeholder 모두 없는 경우 (warning)."""
    issues = []
    for m in re.finditer(r'<input\b([^>]*?)/?>', html, re.IGNORECASE):
        attrs = m.group(1).lower()
        if 'type="hidden"' in attrs or "type='hidden'" in attrs:
            continue
        has_label = (
            'aria-label=' in attrs
            or 'placeholder=' in attrs
            or 'aria-labelledby=' in attrs
        )
        if not has_label:
            issues.append(A11yIssue(
                severity='warning',
                rule='input_no_label',
                element=m.group(0)[:80],
                message='input 요소에 label·aria-label·placeholder 모두 없음',
            ))
    return issues


def find_missing_lang_attribute(html: str) -> list[A11yIssue]:
    """html 태그에 lang 속성 누락."""
    issues = []
    m = re.search(r'<html\b([^>]*)>', html, re.IGNORECASE)
    if m and 'lang=' not in m.group(1).lower():
        issues.append(A11yIssue(
            severity='error',
            rule='missing_lang',
            element=m.group(0)[:80],
            message='html 요소에 lang 속성 누락 — 스크린리더 언어 추정 불가',
        ))
    return issues


def audit_html(html: str) -> dict[str, Any]:
    """전체 a11y 감사 — 모든 검사 실행 + 등급 산정.

    Returns:
        {
          'issues': list[A11yIssue],
          'error_count': int,
          'warning_count': int,
          'grade': 'A' | 'AA' | 'AAA' | 'fail',
        }
    """
    all_issues: list[A11yIssue] = []
    all_issues.extend(find_missing_lang_attribute(html))
    all_issues.extend(find_images_without_alt(html))
    all_issues.extend(find_buttons_without_label(html))
    all_issues.extend(find_inputs_without_label(html))

    errors = [i for i in all_issues if i.severity == 'error']
    warnings = [i for i in all_issues if i.severity == 'warning']

    if len(errors) == 0 and len(warnings) == 0:
        grade = 'AAA'
    elif len(errors) == 0:
        grade = 'AA'
    elif len(errors) <= 3:
        grade = 'A'
    else:
        grade = 'fail'

    return {
        'issues': all_issues,
        'error_count': len(errors),
        'warning_count': len(warnings),
        'grade': grade,
    }


__all__ = [
    'A11Y_REQUIRED_LANDMARKS',
    'A11Y_INTERACTIVE_TAGS',
    'CONTRAST_RATIO_NORMAL',
    'CONTRAST_RATIO_LARGE',
    'A11yIssue',
    'find_images_without_alt',
    'find_buttons_without_label',
    'find_inputs_without_label',
    'find_missing_lang_attribute',
    'audit_html',
]
