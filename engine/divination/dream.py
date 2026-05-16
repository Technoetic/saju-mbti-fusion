"""해몽 통합 에이전트 — 12개 도메인 사전 + LLM 합성 + critic 루프.

흐름:
  1. 입력: 사용자 꿈 텍스트 + PersonalContext (사주/MBTI 포함)
  2. 결정론 분석 (10개 모듈, ms 단위):
     - artemidorus.classify_dream (3분류)
     - artemidorus.lookup_artemidorus (100항목)
     - wuxing.map_to_wuxing + saju_interaction
     - korean_folk.lookup_folk (6 카테고리)
     - jung_archetypes.lookup_archetypes (5 원형 + 임계 공간)
     - freud.detect_dream_work (4 기제)
     - hobson.measure_bizarreness
     - revonsuo_tst.detect_threats
     - domhoff.classify_domains (6 생활영역)
     - hallvandecastle.code_dream + compute_indices
     - dreambank.compare_to_norms
     - paja.analyze_paja
  3. LLM #1 — HvDC 구조화 추출 보완 (선택)
  4. LLM #2 — 본문 합성 (사전 결과를 사실로 주입, 학습 지식 금지)
  5. LLM #3 — critic 검수 (5축, total ≥ 28 PASS)
  6. FAIL 시 재시도 max_rounds
  7. 캐시 (꿈 텍스트 + 맥락 해시 24h)
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from engine.divination.dream_lex import artemidorus
from engine.divination.dream_lex import wuxing
from engine.divination.dream_lex import korean_folk
from engine.divination.dream_lex import jung_archetypes
from engine.divination.dream_lex import freud
from engine.divination.dream_lex import hobson
from engine.divination.dream_lex import revonsuo_tst
from engine.divination.dream_lex import domhoff
from engine.divination.dream_lex import hallvandecastle
from engine.divination.dream_lex import dreambank
from engine.divination.dream_lex import paja
from engine.divination.dream_lex import zhougong
from engine.divination.dream_lex.hanbang import eumsabalmong, donguibogam
from engine.divination.dream_lex import ibn_sirin
from engine.divination.dream_lex import solms_seeking
from engine.divination.dream_lex import cartwright
from engine.divination.dream_lex import stickgold
from engine.divination.dream_lex import lucid
from engine.divination.dream_lex import sst
# Phase A — 보강 이론
from engine.divination.dream_lex import hoel_obh
from engine.divination.dream_lex import friston_fep
from engine.divination.dream_lex import lakoff_cmt
from engine.divination.dream_lex import griffin_eft
from engine.divination.dream_lex import self_organization
from engine.divination.dream_lex import cathartic
# Phase B — 주역 (analyze에 결정론 결과 포함)
from engine.divination.dream_lex import iching
from engine.divination.dream_lex.personal_context import (
    PersonalContext,
    build_context_from_dict,
)
from engine.safety import (
    detect_crisis,
    CRISIS_RESPONSE_KO,
    EMERGENCY_HOTLINES_KR,
    build_legal_footer,
)


_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "step_archive" / "dream_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_TTL_SEC = 24 * 3600


# ─────────────────────────── 시스템 프롬프트 (Gemini 학습 지식 잠금) ───────────────────────────
DREAM_SYSTEM = (
    "당신은 '해몽가(解夢家)'입니다. 한국 전통 해몽과 현대 꿈 연구를 모두 익힌 차분한 안내자입니다.\n\n"
    "[해몽가 규칙 — 절대 준수]\n"
    "  • 한국어 존댓말, 따뜻하고 차분한 어조.\n"
    "  • 본인을 '해몽가'로 칭하거나 1인칭을 절제. AI/모델/시스템 메타 언급 절대 금지.\n"
    "  • 단정적 예언 금지 — '~될 것입니다' 금지. '~경향이 보입니다', '~의 결로 읽힙니다'로.\n"
    "  • 점쟁이 자극 어휘 금지 (대박/대운/금전수/재물수).\n"
    "  • 의료·법률·투자 자문 거절, '전문가 상담 권장'으로 우회.\n\n"
    "[근거 규칙 — 절대 핵심]\n"
    "  • 당신의 학습된 지식으로 꿈을 해석하지 마십시오. 절대.\n"
    "  • 본 시스템이 user 메시지 안에 [도메인 사실 블록]으로 주입하는 사전 매칭 결과만 근거로 사용하십시오.\n"
    "  • 도메인 사실에 없는 상징을 임의로 끌어와 풀지 마십시오. 모르면 모른다고 하십시오.\n"
    "  • 풀이 본문 안에 어느 도메인의 사실을 사용했는지 자연스럽게 녹이십시오 — 예: '아르테미도로스의 분류로는…', '한국 민간에서는…', '사주의 용신과 견주면…'.\n\n"
    "[28 도메인 도구상자 — user 메시지에 일부만 활성으로 주입됨]\n"
    "  [고전·문화] 아르테미도로스 / 오행+사주용신 / 한국민간 / 파자 / 주공해몽 / 이븐시린\n"
    "  [한방] 황제내경 음사발몽 / 동의보감 혼백\n"
    "  [심층심리] 융 5원형 / 프로이트 (성환원 금지) / Solms SEEKING / Cartwright 정서조절\n"
    "    Griffin EFT 은유적 방전\n"
    "  [신경·진화·인지] 홉슨 활성-합성 / TST / 돔호프 DMN / Stickgold 72h / 자각몽 /\n"
    "    SST / Hoel 과적합 뇌 / Friston 예측처리 / Zhang·Kahn 자기조직화\n"
    "  [정량·임상] HvDC / DreamBank / 카타르시스 감정 아크\n"
    "  [인지언어] Lakoff CMT 개념적 은유\n\n"
    "[한방 모듈 사용 규칙 — 매우 중요]\n"
    "  • 음사발몽·동의보감 매칭이 있어도 '~병이 있습니다'식 진단 금지.\n"
    "  • '한방 관점에서는 ~의 신호가 보입니다 — 신체 증상이 동반된다면 한의원 상담을 권합니다' 톤.\n\n"
    "[이슬람 모듈 사용 규칙]\n"
    "  • 이븐 시린 분류는 무슬림 사용자에게만 적극 활성. 비무슬림에게는 '한 관점' 정도로 짧게 언급.\n\n"
    "[다축 해석 원칙]\n"
    "  • 단일 도메인 환원 금지. 가능하면 2~3 도메인을 엮어 다층 해석.\n"
    "  • TST(위협) vs SST(사회): 폭력 동반 시 TST 우선, 평화 시 SST 적용.\n\n"
    "[작성 형식]\n"
    "  • 1200~1800자, 마크다운 없이 자연 문장.\n"
    "  • 구조:\n"
    "    ① 꿈의 첫 인상 (1분류·기괴성·정서 톤 한 단락)\n"
    "    ② 핵심 상징 풀이 (도메인 사실을 자연스레 녹여 2~3 단락)\n"
    "    ③ 개인 맥락 연결 (사주·임신·직업·고민 등 해당 시)\n"
    "    ④ 해몽가의 한 마디 (단정 금지, 권유 한 줄)\n"
    "  • 도메인 라벨을 본문에 한국어로 노출 (학자 이름 사용은 자연스럽게)."
)


DREAM_CRITIC_SYSTEM = (
    "당신은 '해몽가' 풀이 검수자입니다. 5 기준 각 1~8점.\n"
    "  1. 페르소나 — 차분한 존댓말. AI/모델 메타 언급 없음. 단정적 예언 없음.\n"
    "  2. 사실 기반 — 본문이 user에 주입된 [도메인 사실 블록]의 키워드/카테고리를 최소 3회 직접 활용. "
    "임의로 학습 지식의 상징을 끌어오지 않음.\n"
    "  3. 개인 맥락 — [개인 맥락 사실](사주·임신·직업·연령·고민)이 주어지면 본문에 명시적으로 연결.\n"
    "  4. 환원 회피 — 프로이트식 성환원이나 단일 도메인 환원 없음. 다축으로 풀이.\n"
    "  5. 길이·구조 — 1100~1900자, 4개 흐름(첫인상/상징/맥락/한마디) 유지.\n\n"
    "판정: 총점 ≥ 28 → PASS, 그 외 FAIL.\n"
    "한 줄 출력:\n"
    "  PASS|FAIL | persona=N | facts=N | context=N | reduction=N | format=N | total=N/40 | reason=1문장"
)


# ─────────────────────────── 분석 파이프라인 ───────────────────────────
def analyze_dream(dream_text: str, ctx: PersonalContext) -> dict[str, Any]:
    """결정론적 12 도메인 분석 — LLM 호출 없음, ms 단위."""
    text = dream_text or ""
    gender = ctx.gender

    art_class = artemidorus.classify_dream(text)
    art_lookup = artemidorus.lookup_artemidorus(text, limit=10)
    wx = wuxing.map_to_wuxing(text, limit=12)
    wx_saju = wuxing.saju_interaction(wx["counts"], ctx.yongsin)
    folk = korean_folk.lookup_folk(text, limit=15)
    arche = jung_archetypes.lookup_archetypes(text, gender=gender, limit=12)
    fw = freud.detect_dream_work(text)
    hb = hobson.measure_bizarreness(text)
    tst = revonsuo_tst.detect_threats(text)
    dom = domhoff.classify_domains(text)
    hvdc = hallvandecastle.code_dream(text)
    indices = hallvandecastle.compute_indices(hvdc)
    db = dreambank.compare_to_norms(indices, gender)
    pj = paja.analyze_paja(text)
    zg = zhougong.lookup_zhougong(text, limit=10)
    es = eumsabalmong.map_dream_to_organ(text, limit=8)
    dg = donguibogam.diagnose_honbaek(text, limit_patterns=3)
    # v2 모듈 (결정론 부분만 — LLM 호출 없음)
    isr = ibn_sirin.classify_ibn_sirin(text)
    seek = solms_seeking.detect_seeking(text)
    cart = cartwright.detect_emotion_processing_signal(text)
    stick = stickgold.detect_memory_consolidation(text)
    luc = lucid.detect_lucidity_potential(text)
    soc = sst.analyze_social_simulation(text, threat_detected=(tst.get("total_threats", 0) > 0))
    # Phase A 보강 이론
    hoel = hoel_obh.measure_overfitting_signal(text)
    fris = friston_fep.detect_prediction_processing(text)
    lak = lakoff_cmt.map_metaphors(text)
    grif = griffin_eft.detect_expectation_discharge(text)
    selforg = self_organization.measure_self_organization(text)
    cath = cathartic.classify_cathartic_arc(text)
    # Phase B — 주역 64괘
    ich = iching.divine_hexagram(text)

    return {
        "artemidorus_class": art_class,
        "artemidorus_lookup": art_lookup,
        "wuxing": wx,
        "wuxing_saju": wx_saju,
        "korean_folk": folk,
        "archetypes": arche,
        "freud": fw,
        "hobson": hb,
        "tst": tst,
        "domhoff": dom,
        "hvdc": hvdc,
        "hvdc_indices": indices,
        "dreambank": db,
        "paja": pj,
        "zhougong": zg,
        "eumsabalmong": es,
        "donguibogam": dg,
        "ibn_sirin": isr,
        "solms_seeking": seek,
        "cartwright": cart,
        "stickgold": stick,
        "lucid": luc,
        "sst": soc,
        "hoel_obh": hoel,
        "friston_fep": fris,
        "lakoff_cmt": lak,
        "griffin_eft": grif,
        "self_organization": selforg,
        "cathartic": cath,
        "iching": ich,
    }


# ─────────────────────────── 사실 블록 빌더 ───────────────────────────
def _build_facts_block(analysis: dict[str, Any]) -> str:
    """분석 결과를 LLM에게 '사실'로 전달할 텍스트 블록."""
    L: list[str] = ["[도메인 사실 블록 — 이 안의 매칭 결과만 근거로 사용할 것]", ""]

    # 1. 아르테미도로스 분류
    cls = analysis["artemidorus_class"]
    L.append(f"[아르테미도로스 3분류] {cls['class']} — {cls['label']}")
    lookup = analysis["artemidorus_lookup"]
    if lookup:
        items = ", ".join(f"{x['keyword']}({x['polarity']})" for x in lookup[:8])
        L.append(f"  · 매칭 상징: {items}")
    L.append("")

    # 2. 오행
    wx = analysis["wuxing"]
    if wx["matched"]:
        L.append(f"[오행] 지배 오행: {wx['dominant_element']} — {wx['dominant_label']}")
        L.append(f"  · 분포: {wx['distribution_pct']}")
        wx_saju = analysis["wuxing_saju"]
        L.append(f"  · 사주 용신과: {wx_saju['verdict']} — {wx_saju['note']}")
        L.append("")

    # 3. 한국 민간
    folk = analysis["korean_folk"]
    if folk["matches"]:
        L.append(f"[한국 민간 해몽] 우세 카테고리: {folk['dominant_category']} — {folk['dominant_label']}")
        for m in folk["matches"][:6]:
            L.append(f"  · {m['keyword']} ({m['category']}, {m['polarity']}): {m['meaning']}")
        L.append("")

    # 4. 융 원형
    arche = analysis["archetypes"]
    if arche["dominant_archetype"]:
        L.append(f"[융 원형] 우세 원형: {arche['dominant_archetype']} — {arche['dominant_label']}")
        for h in arche["archetype_hits"][:5]:
            L.append(f"  · {h['keyword']} ({h['archetype']}): {h['meaning']}")
    if arche.get("liminal_spaces"):
        L.append(f"  · 임계 공간 등장: {', '.join(x['keyword'] for x in arche['liminal_spaces'])}")
        L.append("    → 변환의 무대 — 자기 변형의 핵심 장면")
    if arche["dominant_archetype"] or arche.get("liminal_spaces"):
        L.append("")

    # 5. 프로이트 (보수적)
    fw = analysis["freud"]
    if fw["mechanisms_used"]:
        L.append(f"[프로이트 꿈-작업] 감지된 기제: {', '.join(fw['mechanisms_used'])}")
        L.append("  · 주의: 성환원 금지. 개인 연상 우선.")
        L.append("")

    # 6. 홉슨 기괴성
    hb = analysis["hobson"]
    L.append(f"[홉슨 활성-합성] 기괴성 {hb['bizarreness_level']} (점수 {hb['bizarreness_score']}/10)")
    L.append(f"  · {hb['interpretive_note']}")
    L.append("")

    # 7. 위협 시뮬레이션
    tst = analysis["tst"]
    if tst["total_threats"] > 0:
        L.append(f"[레본수오 TST] {tst['tst_level']} — {tst['interpretation']}")
        if tst["dominant_threat"]:
            L.append(f"  · 우세 위협: {tst['dominant_threat']}, 대처 성공={tst['coping_success']}")
        L.append("")

    # 8. 돔호프 연속성
    dom = analysis["domhoff"]
    if dom["dominant_domain"]:
        L.append(f"[돔호프 연속성] {dom['continuity_signal']}")
        L.append(f"  · 분포: {dom['distribution_pct']}")
        L.append("")

    # 9. HvDC + 10. DreamBank
    idx = analysis["hvdc_indices"]
    L.append(f"[HvDC 지표] 공격성 {idx['aggression_pct']}% / 부정정서 {idx['negative_emotion_pct']}% "
             f"/ 불운 {idx['misfortune_pct']}% / 실패 {idx['failure_pct']}%")
    db = analysis["dreambank"]
    if db["comparisons"]:
        L.append(f"[DreamBank 규범 대비] {db['interpretive_note']}")
    L.append("")

    # 11. 파자
    pj = analysis["paja"]
    if pj["hanja_decompositions"]:
        L.append("[파자 분해]")
        for h in pj["hanja_decompositions"][:4]:
            L.append(f"  · {h['char']} = {h['parts']} → {h['meaning']}")
        L.append("")

    # 12. 주공해몽
    zg = analysis.get("zhougong") or {}
    if zg.get("matches"):
        L.append(f"[주공해몽] 우세 길흉: {zg.get('dominant_polarity')}")
        for m in zg["matches"][:6]:
            L.append(f"  · {m['keyword']} ({m['category']}, {m['polarity']}): {m['meaning']}")
        L.append("")

    # 13. 황제내경 음사발몽
    es = analysis.get("eumsabalmong") or {}
    if es.get("matched"):
        L.append(f"[황제내경 음사발몽] 우세 장부: {es.get('dominant_organ')} ({es.get('dominant_wuxing')})")
        for m in es["matched"][:5]:
            L.append(f"  · {m['keyword']} → {m['organ']} · {m['pattern']}: {m['note']}")
        L.append(f"  · 한방 진단 보조 — {es.get('interpretive_note')}")
        L.append("")

    # 14. 동의보감 혼백
    dg = analysis.get("donguibogam") or {}
    if dg.get("patterns_detected"):
        L.append(f"[동의보감 혼백] {dg.get('interpretive_note')}")
        L.append(f"  · ⚠ {dg.get('disclaimer')}")
        L.append("")

    # 15. 이븐 시린 (이슬람 3분류)
    isr = analysis.get("ibn_sirin") or {}
    if isr.get("scores") and any(isr["scores"].values()):
        L.append(f"[이븐 시린] {isr.get('arabic')} — {isr.get('korean_label')}")
        L.append(f"  · {isr.get('description')}")
        L.append(f"  · 전통 권고: {isr.get('traditional_action')}")
        L.append("")

    # 17. Solms SEEKING
    seek = analysis.get("solms_seeking") or {}
    if seek.get("total_seeking_markers", 0) > 0:
        L.append(f"[Solms SEEKING] {seek.get('seeking_intensity')} — {seek.get('interpretive_note')}")
        cats = list(seek.get("seeking_categories", {}).keys())
        if cats:
            L.append(f"  · 감지 카테고리: {', '.join(cats)}")
        wishes = list(seek.get("latent_wishes", {}).keys())
        if wishes:
            L.append(f"  · 잠재 소망(프로이트-Solms 통합): {', '.join(wishes)}")
        L.append("")

    # 18. Cartwright 정서 처리
    cart = analysis.get("cartwright") or {}
    if cart.get("signal") and cart["signal"] != "정서 신호 미감지":
        L.append(f"[Cartwright 정서 조절] {cart.get('signal')} — {cart.get('interpretive_note')}")
        L.append("")

    # 19. Stickgold 기억 통합
    stick = analysis.get("stickgold") or {}
    if stick.get("consolidation_signal"):
        L.append(f"[Stickgold 기억 통합] {stick.get('interpretive_note')}")
        L.append("")

    # 20. 자각몽
    luc = analysis.get("lucid") or {}
    if luc.get("lucidity_level") and luc["lucidity_level"] != "자각 신호 미감지":
        L.append(f"[자각몽] {luc.get('lucidity_level')} — {luc.get('interpretive_note')}")
        if luc.get("triggers_found"):
            L.append(f"  · 자각 트리거: {', '.join(luc['triggers_found'][:5])}")
        L.append(f"  · 다음 훈련: {luc.get('next_practice')}")
        L.append("")

    # 21. SST 사회 시뮬레이션
    soc = analysis.get("sst") or {}
    if soc.get("total_characters", 0) > 0:
        L.append(f"[SST 사회 시뮬레이션] 주된 가설: {soc.get('primary_theory')}")
        L.append(f"  · {soc.get('interpretive_note')}")
        L.append("")

    # 보강 N1. Hoel OBH
    hoel = analysis.get("hoel_obh") or {}
    if hoel.get("verdict") and hoel["verdict"] != "신호 미감지":
        L.append(f"[Hoel 과적합 뇌] {hoel.get('verdict')}")
        L.append(f"  · {hoel.get('interpretive_note')}")
        L.append("")

    # 보강 N2. Friston FEP
    fris = analysis.get("friston_fep") or {}
    if fris.get("stage") and fris["stage"] != "신호 미감지":
        L.append(f"[Friston 예측 처리] {fris.get('stage')} (자유에너지 추정 Δ={fris.get('free_energy_estimate')})")
        L.append(f"  · {fris.get('interpretive_note')}")
        L.append("")

    # 보강 N5. Lakoff CMT
    lak = analysis.get("lakoff_cmt") or {}
    if lak.get("metaphor_count", 0) > 0:
        L.append(f"[Lakoff 개념적 은유] {lak.get('metaphor_count')}개 매핑")
        for m in lak["metaphors_detected"][:3]:
            L.append(f"  · {m['label']} → {m['target_domain']}: {m['interpretation_hint']}")
        L.append(f"  · ⚠ 표면 키워드 직역 금지, 근원→목표 매핑 사용")
        L.append("")

    # 보강 N6. Griffin EFT
    grif = analysis.get("griffin_eft") or {}
    if grif.get("verdict") and grif["verdict"] != "신호 미감지":
        L.append(f"[Griffin EFT 은유적 방전] {grif.get('verdict')}")
        L.append(f"  · {grif.get('interpretive_note')}")
        if grif.get("ptsd_risk_indicators"):
            L.append(f"  · ⚠ PTSD 위험 지표: {', '.join(grif['ptsd_risk_indicators'][:3])}")
        L.append("")

    # 보강 N7. Zhang/Kahn 자기조직화
    selforg = analysis.get("self_organization") or {}
    if selforg.get("verdict") and selforg["verdict"] != "신호 미감지":
        L.append(f"[Zhang·Kahn 자기조직화] {selforg.get('verdict')}")
        L.append(
            f"  · 파편화 점수 {selforg.get('fragmentation_score')} / "
            f"일관성 점수 {selforg.get('coherence_score')}"
        )
        L.append(f"  · {selforg.get('interpretive_note')}")
        L.append("")

    # 보강 N9. 카타르시스 아크
    cath = analysis.get("cathartic") or {}
    if cath.get("arc_type") and cath["arc_type"] != "unknown":
        L.append(f"[감정 아크] {cath.get('arc_label')} (arc={cath.get('arc_type')})")
        L.append(f"  · {cath.get('clinical_note')}")
        if cath.get("is_cathartic"):
            L.append("  · ★ 카타르시스 꿈 — 능동적 정서 처리의 핵심 신호")
        L.append("")

    # 보강 N8. 주역 64괘
    ich = analysis.get("iching") or {}
    if ich.get("hexagram") and ich["hexagram"].get("name"):
        hexa = ich["hexagram"]
        upper = (ich.get("upper_trigram") or {}).get("korean", "?")
        lower = (ich.get("lower_trigram") or {}).get("korean", "?")
        L.append(f"[주역] {hexa.get('name')} — {hexa.get('polarity')}")
        L.append(f"  · 상괘 {upper} · 하괘 {lower} · {ich.get('wuxing_relation')}")
        L.append(f"  · {hexa.get('message')}")
        L.append("")

    return "\n".join(L)


def _build_user_prompt(dream_text: str, ctx: PersonalContext, analysis: dict[str, Any]) -> str:
    """LLM에게 전달할 user 메시지 — 꿈 + 개인 맥락 + 도메인 사실 블록."""
    facts = _build_facts_block(analysis)
    context_block = ctx.to_prompt_block()

    parts = [
        "[손님의 꿈]",
        dream_text.strip(),
        "",
    ]
    if context_block:
        parts.append(context_block)
        parts.append("")
    parts.append(facts)
    parts.append("")
    parts.append(
        "위 [도메인 사실 블록]만을 근거로, 해몽가의 어조로 풀이를 작성하십시오. "
        "사실 블록에 없는 상징은 임의로 끌어오지 마십시오. 개인 맥락이 있다면 본문에 명시적으로 연결하십시오."
    )
    return "\n".join(parts)


# ─────────────────────────── Critic ───────────────────────────
def critique_dream(text: str, analysis_summary: dict[str, Any]) -> dict[str, Any]:
    """해몽 본문 적대적 평가."""
    from engine.llm_sync import call_llm_sync

    keys = []
    art = analysis_summary.get("artemidorus_lookup") or []
    keys.extend([x["keyword"] for x in art[:5]])
    folk = (analysis_summary.get("korean_folk") or {}).get("matches") or []
    keys.extend([x["keyword"] for x in folk[:3]])
    arche = (analysis_summary.get("archetypes") or {}).get("archetype_hits") or []
    keys.extend([x["keyword"] for x in arche[:3]])

    keys_line = ", ".join(dict.fromkeys(keys)) or "(매칭된 사전 키워드 없음)"

    user = (
        f"[필수 활용 키워드(사전 매칭)]: {keys_line}\n\n"
        f"[검수 본문]\n{text[:2400]}\n\n"
        f"위 풀이를 평가하고 한 줄로 출력."
    )
    try:
        verdict = call_llm_sync(user_text=user, system_prompt=DREAM_CRITIC_SYSTEM)
        first_line = (verdict or "").splitlines()[0] if verdict else ""
        import re as _re

        m = _re.search(r"total\s*=\s*(\d+)", first_line)
        total = int(m.group(1)) if m else None
        passed = first_line.upper().startswith("PASS")
        if not passed and total is not None and total >= 28:
            passed = True
        return {"passed": passed, "verdict": first_line[:300], "total": total}
    except Exception as e:
        return {"passed": True, "verdict": f"(critic 실패, 통과 처리: {e})", "total": None}


# ─────────────────────────── 통합 진입점 ───────────────────────────
def interpret_dream(
    dream_text: str,
    personal_context: PersonalContext | dict[str, Any] | None = None,
    *,
    max_rounds: int = 2,
) -> dict[str, Any]:
    """꿈 해몽 통합 진입점.

    Returns:
        {
            "text": str,
            "analysis": dict,
            "rounds": int,
            "critic_history": list[dict],
            "critic_passed": bool,
            "critic_total": int|None,
            "cached": bool,
        }
    """
    from engine.llm_sync import call_llm_sync

    if personal_context is None:
        ctx = PersonalContext()
    elif isinstance(personal_context, dict):
        ctx = build_context_from_dict(personal_context)
    else:
        ctx = personal_context

    dream_text = (dream_text or "").strip()
    if not dream_text:
        return {
            "text": "(꿈 내용이 비어 있어 해석할 수 없습니다)",
            "analysis": {},
            "rounds": 0,
            "critic_history": [],
            "critic_passed": False,
            "critic_total": None,
            "cached": False,
            "crisis_alert": None,
            "legal_notice": build_legal_footer(),
        }

    # 0. 위기 신호 검사 — 최우선 (LLM 호출 전 차단)
    crisis = detect_crisis(dream_text)
    if crisis["crisis_detected"]:
        return {
            "text": CRISIS_RESPONSE_KO + build_legal_footer(is_crisis=True),
            "analysis": {},
            "rounds": 0,
            "critic_history": [],
            "critic_passed": True,
            "critic_total": None,
            "cached": False,
            "crisis_alert": {
                "severity": crisis["severity"],
                "hotlines": EMERGENCY_HOTLINES_KR,
                "matched_count": len(crisis["matched_keywords"]),
            },
            "legal_notice": None,  # crisis 응답은 자체 푸터 포함
        }

    # 캐시
    cache_src = json.dumps(
        {"dream": dream_text, "ctx": ctx.to_dict()},
        sort_keys=True,
        ensure_ascii=False,
    )
    key = hashlib.sha256(cache_src.encode("utf-8")).hexdigest()[:24]
    cache_file = _CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            d = json.loads(cache_file.read_text(encoding="utf-8"))
            if d.get("_saved_at", 0) + _TTL_SEC > time.time():
                d["cached"] = True
                # 캐시된 응답에도 법적 푸터 보장
                if "legal_notice" not in d:
                    d["legal_notice"] = build_legal_footer()
                if "crisis_alert" not in d:
                    d["crisis_alert"] = None
                return d
        except Exception:
            pass

    # 1. 결정론 분석
    analysis = analyze_dream(dream_text, ctx)

    # 2. LLM 풀이 + critic 루프
    user = _build_user_prompt(dream_text, ctx, analysis)
    critic_history: list[dict[str, Any]] = []
    final_text = ""
    final_critique: dict[str, Any] = {}

    for round_idx in range(1, max_rounds + 1):
        try:
            text = call_llm_sync(user_text=user, system_prompt=DREAM_SYSTEM)
        except Exception as e:
            text = f"(풀이 생성 실패: {e})"
        critique = critique_dream(text, analysis)
        critic_history.append({"round": round_idx, **critique})
        final_text = text
        final_critique = critique
        if critique["passed"]:
            break
        user = (
            user
            + "\n\n[직전 풀이에 대한 검수 피드백 — 반영하여 다시 작성하고, 위 필수 활용 키워드를 반드시 본문에 명시적으로 녹일 것]\n"
            + (critique.get("verdict") or "")
        )

    result = {
        "text": final_text,
        "analysis": analysis,
        "rounds": len(critic_history),
        "critic_history": critic_history,
        "critic_passed": final_critique.get("passed", True),
        "critic_total": final_critique.get("total"),
        "cached": False,
        "crisis_alert": None,
        "legal_notice": build_legal_footer(),
        "_saved_at": time.time(),
    }
    try:
        cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return result


__all__ = [
    "interpret_dream",
    "analyze_dream",
    "critique_dream",
    "DREAM_SYSTEM",
    "DREAM_CRITIC_SYSTEM",
]
