# engine

9 성격/명리/점술 시스템 통합 facade.

## 동기

```python
from engine import PersonalityEngine
from datetime import datetime

eng = PersonalityEngine()
saju = eng.assess_saju(
    dt_local=datetime(1990, 5, 15, 14, 30),
    gender="M",
)
tarot = eng.cast_tarot("오늘", seed=42)
iching = eng.cast_iching("오늘", seed=42)
fused = eng.fuse(saju=saju, mbti={"type": "ENTJ"})
```

## 비동기 (병렬)

```python
import asyncio
from engine import PersonalityEngine
from datetime import datetime

async def main():
    eng = PersonalityEngine()
    result = await eng.assess_all_async(
        nl_text="사람들과 어울리는 게 즐겁다",
        saju_kwargs=dict(dt_local=datetime(1990, 5, 15, 14, 30), gender="M"),
        oracle_question="오늘",
        oracle_seed=42,
    )
    print(result.systems())  # ['saju','mbti','bigfive','enneagram','hexaco','disc','tarot','iching','fusion']

asyncio.run(main())
```

## LLM 비동기 helper

```python
from engine.llm_async import call_llm_async

text = await call_llm_async(user_text="...", system_prompt="...")
```

각 라이브러리의 `*/interpret/explain.py` 에 `explain_from_dict_async()` 도 추가됨.
