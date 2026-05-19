"""캐시 키 결정기 — 운영표준 §7.2.23 본문화.

face_reading 캐시 키 생성을 단일 진입점으로 표준화. 무효화 정책을 명시.

§7.2.23 캐시 키 차원 (모두 결정론, 같은 입력은 같은 키):
  · system_prompt_hash — 시스템 프롬프트 변경 시 자동 무효화 (핵심)
  · image_hash         — 사진 SHA-256
  · age_bucket         — 정확한 나이 X, 10대/20대/... 버킷 (개인정보 축소)
  · gender             — male/female/none
  · question_hash      — 화두 본문 SHA-256
  · metrics_signature  — 메트릭 키 정렬 + 값 반올림
  · lang               — ko/en/ja/zh
  · region_class       — KR/EU/UK/JP/CN/other (정확한 region X)

§7.2.23 무효화 트리거:
  · 시스템 프롬프트 변경 → 모든 캐시 자동 무효화
  · metrics 값 변화 → 별도 캐시 항목 (사진은 같아도)
  · lang/region 변화 → 별도 캐시 (다국어 응답 분리)

본 모듈은 캐시 저장/조회 자체는 안 함 — face_reading._save_cache/_load_cache에 위임.
키 형식만 표준화.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


# §7.2.23 키 길이 (sha256 hex 첫 N자)
CACHE_KEY_LENGTH = 32

# §7.2.23 — 메트릭 키 화이트리스트. 캐시 키에 포함되는 메트릭만.
# 변경되면 캐시 분기가 달라지는 메트릭.
_METRICS_KEYS = (
    "face_count",
    "head_tilt_deg",
    "brightness",
    "z_variance",
    "three_thirds",
    "gaze_locked",
    "skin_hsv",
)

# region → 클래스 매핑 (개인정보 축소).
_REGION_CLASSES = {
    "KR": "kr",
    "EU": "eu", "DE": "eu", "FR": "eu", "IT": "eu", "ES": "eu", "NL": "eu",
    "PL": "eu", "SE": "eu", "FI": "eu", "AT": "eu", "BE": "eu",
    "UK": "uk", "GB": "uk",
    "JP": "jp",
    "CN": "cn",
    "US-CA": "us-ca",
    "US-IL": "us-il",
}


@dataclass(frozen=True)
class CacheKey:
    key: str
    system_prompt_hash: str
    image_hash: str
    age_bucket: str
    gender: str
    question_hash: str
    metrics_signature: str
    lang: str
    region_class: str


# ─────────────────────────── 헬퍼 ───────────────────────────

def _age_bucket(age: int | None) -> str:
    if age is None or not isinstance(age, int) or age < 0:
        return "unknown"
    if age < 20:
        return "teen"
    if age < 30:
        return "20s"
    if age < 40:
        return "30s"
    if age < 50:
        return "40s"
    if age < 60:
        return "50s"
    return "60s+"


def _normalize_gender(gender: str | None) -> str:
    if not gender or not isinstance(gender, str):
        return "none"
    g = gender.strip().lower()
    if g in ("male", "m", "남"):
        return "male"
    if g in ("female", "f", "여"):
        return "female"
    return "none"


def _classify_region(region: str | None) -> str:
    if not region:
        return "other"
    return _REGION_CLASSES.get(region.strip().upper(), "other")


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _hash_image(image_b64: str | None) -> str:
    """1MB 상한 — 큰 사진은 첫 1MB만 해시 (cost 보호)."""
    if not image_b64:
        return _hash_str("")
    payload = image_b64.encode("utf-8")[:1_000_000]
    return hashlib.sha256(payload).hexdigest()


def _metrics_signature(metrics: dict[str, Any] | None) -> str:
    """캐시 키에 포함될 메트릭만 정규화 후 해시.

    값은 float면 소수점 4자리로 반올림 (잡음에 안정).
    """
    if not metrics or not isinstance(metrics, dict):
        return _hash_str("")
    pairs: list[tuple[str, Any]] = []
    for k in _METRICS_KEYS:
        if k not in metrics:
            continue
        v = metrics[k]
        if isinstance(v, float):
            v = round(v, 4)
        elif isinstance(v, list):
            v = tuple(round(x, 4) if isinstance(x, float) else x for x in v)
        pairs.append((k, v))
    # 키 정렬 — 입력 dict 순서에 무관하게 같은 키
    pairs.sort()
    return _hash_str(repr(pairs))


# ─────────────────────────── Public API ───────────────────────────

def resolve_cache_key(
    *,
    system_prompt_hash: str,
    image_b64: str | None,
    age: int | None,
    gender: str | None,
    question: str | None,
    metrics: dict[str, Any] | None,
    lang: str = "ko",
    region: str | None = None,
) -> CacheKey:
    """face_reading 입력 → §7.2.23 표준 캐시 키."""
    if not system_prompt_hash:
        raise ValueError("system_prompt_hash is required for cache key")

    img_h = _hash_image(image_b64)
    age_b = _age_bucket(age)
    gnd = _normalize_gender(gender)
    q_h = _hash_str(question or "")
    mtr_sig = _metrics_signature(metrics)
    norm_lang = lang if lang in ("ko", "en", "ja", "zh") else "en"
    rg = _classify_region(region)

    # 결합 — 각 차원이 변하면 키가 달라짐
    composite = "|".join([
        system_prompt_hash,
        img_h,
        age_b,
        gnd,
        q_h,
        mtr_sig,
        norm_lang,
        rg,
    ])
    key = _hash_str(composite)[:CACHE_KEY_LENGTH]

    return CacheKey(
        key=key,
        system_prompt_hash=system_prompt_hash,
        image_hash=img_h,
        age_bucket=age_b,
        gender=gnd,
        question_hash=q_h,
        metrics_signature=mtr_sig,
        lang=norm_lang,
        region_class=rg,
    )


def invalidates_on_prompt_change(
    old_prompt_hash: str,
    new_prompt_hash: str,
) -> bool:
    """시스템 프롬프트 해시가 다르면 같은 입력이라도 새 캐시 키가 됨 → 무효화 트리거."""
    return (old_prompt_hash or "") != (new_prompt_hash or "")


def to_trace_event(key: CacheKey) -> dict[str, Any]:
    """§7.3.4 tracing 호환 — 디버깅용 (원본 PII 미포함)."""
    return {
        "cache_key": key.key,
        "cache_age_bucket": key.age_bucket,
        "cache_gender": key.gender,
        "cache_lang": key.lang,
        "cache_region_class": key.region_class,
    }
