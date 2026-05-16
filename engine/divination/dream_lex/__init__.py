"""dream_lex — 꿈 해몽 도메인 지식 모듈 (총 22 모듈, MVP+v2 완전체).

각 모듈은 결정론적 키워드 매칭·매핑 함수만 제공.
LLM은 호출하지 않으며 (단 #25 hvdc_llm 예외),
결과는 dream.py 통합 에이전트가 user 메시지에 [도메인 사실 블록]으로 주입한다.

26개 이론 중 본 패키지가 담당 (clinical/ 패키지가 #23·#24·#26):
  MVP:
    #1 incubation, #2 artemidorus, #3 wuxing, #4 paja,
    #5 freud, #6 jung_archetypes, #7 hobson, #8 revonsuo_tst,
    #9 domhoff, #10 hallvandecastle, #11 dreambank,
    #12 zhougong, #13/14 hanbang/, #22 schredl_diary
  v2:
    #15 ibn_sirin, #17 solms_seeking, #18 cartwright,
    #19 stickgold, #20 lucid, #21 sst, #25 hvdc_llm
"""

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
from engine.divination.dream_lex import personal_context
from engine.divination.dream_lex import zhougong
from engine.divination.dream_lex import schredl_diary
from engine.divination.dream_lex import incubation
from engine.divination.dream_lex import hanbang
from engine.divination.dream_lex import ibn_sirin
from engine.divination.dream_lex import solms_seeking
from engine.divination.dream_lex import cartwright
from engine.divination.dream_lex import stickgold
from engine.divination.dream_lex import lucid
from engine.divination.dream_lex import sst
from engine.divination.dream_lex import hvdc_llm
from engine.divination.dream_lex import myoe
# Phase A — 추가 6 모듈 (보강 이론)
from engine.divination.dream_lex import hoel_obh
from engine.divination.dream_lex import friston_fep
from engine.divination.dream_lex import lakoff_cmt
from engine.divination.dream_lex import griffin_eft
from engine.divination.dream_lex import self_organization
from engine.divination.dream_lex import cathartic
# Phase B+C — 동양 + 임상 UX 4 모듈
from engine.divination.dream_lex import iching
from engine.divination.dream_lex import dormio
from engine.divination.dream_lex import ullman
from engine.divination.dream_lex import clara_hill

__all__ = [
    "artemidorus", "wuxing", "korean_folk", "jung_archetypes",
    "freud", "hobson", "revonsuo_tst", "domhoff",
    "hallvandecastle", "dreambank", "paja", "personal_context",
    "zhougong", "schredl_diary", "incubation", "hanbang",
    "ibn_sirin", "solms_seeking", "cartwright", "stickgold",
    "lucid", "sst", "hvdc_llm", "myoe",
    "hoel_obh", "friston_fep", "lakoff_cmt", "griffin_eft",
    "self_organization", "cathartic",
    "iching", "dormio", "ullman", "clara_hill",
]
