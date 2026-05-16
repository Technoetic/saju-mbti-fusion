"""A9 Lakoff CMT 토폴로지 추출 에이전트 ⭐ (3대 차별화 핵심).

문서: narrative_text → 공간 도식(갇힘·추락·상승) + 힘 도식(저항·통과)
       → 목표 도메인(취업·연애·건강) 교차 매핑.
기반: 보강 6 Lakoff CMT + Griffin EFT.

기존 `lakoff_cmt.py`는 12 보편 은유 결정론 매칭. 본 에이전트는 그 위에 LLM으로
'공간·힘 도식'을 JSON 구조화 추출 → 사용자의 현실 목표 도메인과 교차 매핑.

표면 키워드 직역을 차단하는 핵심 엔진.
"""

from __future__ import annotations
from typing import Any
import json

from engine.divination.dream_lex.lakoff_cmt import map_metaphors


LAKOFF_TOPOLOGY_LABEL = (
    "A9 Lakoff 토폴로지 — 공간·힘 도식(image schema)을 추출해 사용자 목표 도메인과 교차 매핑. "
    "표면 키워드 직역 차단의 3대 차별화 엔진."
)


# 공간/힘 도식 enum (Lakoff·Johnson image schemas)
IMAGE_SCHEMAS = {
    "spatial": [
        "containment",      # 안/밖 (갇힘·탈출·내부)
        "verticality",      # 상/하 (상승·추락)
        "path",             # 경로 (도착·길 잃음·전환)
        "front_back",       # 앞/뒤 (접근·후퇴)
        "center_periphery", # 중심/주변
        "near_far",         # 가까움/멈
    ],
    "force": [
        "compulsion",       # 강제로 끌림
        "blockage",         # 막힘·차단
        "counterforce",     # 저항·충돌
        "diversion",        # 우회
        "removal_restraint",# 풀려남
        "enablement",       # 가능해짐
        "attraction",       # 끌림
    ],
    "topology_other": [
        "scale",            # 크기 변화
        "merge_split",      # 합쳐짐/분리
        "iteration",        # 반복
        "balance",          # 균형/불균형
    ],
}


# 목표 도메인 (사용자의 현실 고민 영역)
TARGET_DOMAINS = [
    "career",       # 일·진로
    "romance",      # 연애·관계
    "family",       # 가족
    "health",       # 건강
    "finance",      # 금전·재물
    "identity",     # 정체성·자기 인식
    "education",    # 학업·시험
    "creative",     # 창작·표현
]


# LLM 시스템 프롬프트 — JSON 구조화 추출
_LAKOFF_SYSTEM = (
    "당신은 Lakoff·Johnson 인지언어학의 image schema 추출기입니다.\n"
    "입력된 꿈 텍스트에서 표면 키워드를 직역하지 말고, 공간 도식과 힘 도식을 추출해 "
    "JSON으로만 출력하십시오.\n\n"
    "[엄격 규칙]\n"
    "  • 본문에 실제로 나타난 공간·힘 패턴만 추출 (추측 금지)\n"
    "  • 각 도식의 강도 1~5\n"
    "  • '근원 영역' = 신체·물리·공간 / '목표 영역' = 추상 현실 고민\n"
    "  • 단일 정답 강요 금지 — 가능성 위주로 2~3 목표 도메인 후보\n"
    "  • 출력은 valid JSON 1개. 마크다운 코드블록 금지.\n\n"
    "[출력 스키마]\n"
    "  {\n"
    '    "spatial_schemas": [{"schema": "containment|verticality|path|...", "intensity": 1-5, "evidence": "본문 인용"}],\n'
    '    "force_schemas": [{"schema": "blockage|counterforce|...", "intensity": 1-5, "evidence": "본문 인용"}],\n'
    '    "topology_other": [...],\n'
    '    "candidate_target_domains": ["career|romance|...", ...],\n'
    '    "cross_mapping_hypotheses": [\n'
    '      {"source_schema": "containment", "target_domain": "career", \n'
    '       "hypothesis": "현재 직장 환경에 갇혀 있다는 느낌의 가능성", "confidence": 0.0-1.0}\n'
    "    ]\n"
    "  }"
)


def extract_topology(
    dream_text: str,
    *,
    user_target_domain: str | None = None,
) -> dict[str, Any]:
    """LLM으로 image schema + cross-mapping 추출.

    Args:
        dream_text: 꿈 본문
        user_target_domain: 사용자가 명시한 현재 고민 도메인 (가중치 ↑)

    Returns:
        결정론 보편 은유 + LLM 도식 추출 통합 결과
    """
    from engine.llm_sync import call_llm_sync

    if not dream_text or not dream_text.strip():
        return _empty_result()

    # 1단계: 기존 결정론 보편 은유 매칭
    deterministic = map_metaphors(dream_text, user_target_domain=user_target_domain)

    # 2단계: LLM JSON 추출
    target_hint = (
        f"\n[사용자 현재 고민 도메인 힌트] {user_target_domain}"
        if user_target_domain else ""
    )
    user_msg = (
        f"[꿈 본문]\n{dream_text[:2000]}{target_hint}\n\n"
        f"위 본문에서 image schema와 cross-mapping을 JSON으로 추출."
    )
    try:
        raw = call_llm_sync(user_text=user_msg, system_prompt=_LAKOFF_SYSTEM)
    except Exception as e:
        return {
            "agent": "A9",
            "deterministic_metaphors": deterministic,
            "llm_topology": None,
            "error": f"LLM 호출 실패: {e}",
        }

    cleaned = _strip_codeblock(raw or "")
    try:
        topology = json.loads(cleaned)
        topology = _normalize_topology(topology)
    except json.JSONDecodeError as e:
        topology = {
            "spatial_schemas": [],
            "force_schemas": [],
            "topology_other": [],
            "candidate_target_domains": [],
            "cross_mapping_hypotheses": [],
            "parse_error": str(e),
            "raw": (raw or "")[:200],
        }

    # 3단계: 통합 요약
    summary = _summarize(deterministic, topology, user_target_domain)

    return {
        "agent": "A9",
        "deterministic_metaphors": deterministic,
        "llm_topology": topology,
        "summary": summary,
        "principle": (
            "표면 키워드를 직역하지 말 것. 공간·힘 도식(image schema)을 추출해 "
            "사용자의 현실 목표 도메인으로 교차 매핑."
        ),
    }


def _strip_codeblock(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if len(lines) > 2:
            t = "\n".join(lines[1:-1])
    first = t.find("{")
    last = t.rfind("}")
    if first >= 0 and last > first:
        t = t[first:last + 1]
    return t


def _empty_result() -> dict[str, Any]:
    return {
        "agent": "A9",
        "deterministic_metaphors": {"metaphor_count": 0, "metaphors_detected": []},
        "llm_topology": None,
        "summary": {"top_hypotheses": [], "note": "텍스트 없음."},
    }


def _normalize_topology(data: dict[str, Any]) -> dict[str, Any]:
    """LLM 응답 안전 정규화."""
    out: dict[str, Any] = {
        "spatial_schemas": [],
        "force_schemas": [],
        "topology_other": [],
        "candidate_target_domains": [],
        "cross_mapping_hypotheses": [],
    }
    for key in ("spatial_schemas", "force_schemas", "topology_other"):
        items = data.get(key) or []
        if isinstance(items, list):
            out[key] = [
                {
                    "schema": item.get("schema", "")[:40] if isinstance(item, dict) else "",
                    "intensity": int(item.get("intensity", 1)) if isinstance(item, dict) else 1,
                    "evidence": item.get("evidence", "")[:200] if isinstance(item, dict) else "",
                }
                for item in items[:8]
                if isinstance(item, dict)
            ]
    cd = data.get("candidate_target_domains") or []
    if isinstance(cd, list):
        out["candidate_target_domains"] = [d for d in cd[:5] if isinstance(d, str)]
    cmh = data.get("cross_mapping_hypotheses") or []
    if isinstance(cmh, list):
        out["cross_mapping_hypotheses"] = [
            {
                "source_schema": h.get("source_schema", "")[:40],
                "target_domain": h.get("target_domain", "")[:30],
                "hypothesis": h.get("hypothesis", "")[:300],
                "confidence": min(1.0, max(0.0, float(h.get("confidence", 0.5)))),
            }
            for h in cmh[:6]
            if isinstance(h, dict)
        ]
    return out


def _summarize(
    deterministic: dict[str, Any],
    llm: dict[str, Any],
    user_target_domain: str | None,
) -> dict[str, Any]:
    """결정론 + LLM 교차 매핑 상위 가설."""
    top_hypotheses: list[dict[str, Any]] = []

    # LLM 가설을 confidence 정렬
    for h in llm.get("cross_mapping_hypotheses") or []:
        score = h["confidence"]
        # 사용자 명시 도메인과 일치하면 가중치 +0.2
        if user_target_domain and user_target_domain == h["target_domain"]:
            score = min(1.0, score + 0.2)
        top_hypotheses.append({**h, "weighted_score": round(score, 2)})

    # 결정론 보편 은유 (보강 신호)
    for m in deterministic.get("metaphors_detected") or []:
        top_hypotheses.append({
            "source_schema": m.get("label"),
            "target_domain": m.get("target_domain"),
            "hypothesis": m.get("interpretation_hint"),
            "confidence": 0.6,
            "weighted_score": 0.6 * (m.get("relevance") or 1.0) / 2.0 + 0.3,
        })

    top_hypotheses.sort(key=lambda x: x["weighted_score"], reverse=True)

    return {
        "top_hypotheses": top_hypotheses[:5],
        "schema_count": (
            len(llm.get("spatial_schemas") or []) +
            len(llm.get("force_schemas") or []) +
            len(llm.get("topology_other") or [])
        ),
        "note": (
            "공간·힘 도식 기반 교차 매핑 가설들. LLM 본문 합성 시 표면 키워드 직역 대신 "
            "이 가설들을 다층 가능성으로 풀어야 함."
        ),
    }


__all__ = [
    "LAKOFF_TOPOLOGY_LABEL",
    "IMAGE_SCHEMAS",
    "TARGET_DOMAINS",
    "extract_topology",
]
