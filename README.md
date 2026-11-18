![붉은 보름달을 가로지르는 두 마리 학. 금빛 글씨로 새긴 사주경, 월하몽.](docs/readme/moon-gate.svg)

# 사주경 · 월하몽

**꽃패 78장이 뒤집혀 있습니다. 딱 세 장만 고른다면, 어떤 패에 손이 갈까요?**

화선 낭자의 ‘마음의 길’에서는 첫 번째 패가 지나온 일을, 두 번째 패가 지금을, 마지막 패가 앞으로의 흐름을 들려줍니다. 그 옆방에는 생일을 들고 찾아가는 만월 아씨와 어젯밤 꿈 이야기를 기다리는 몽이 도령이 있습니다.

<p align="center">
  <a href="front/media/characters/hwaseon_nangja.mp4"><img src="docs/readme/gallery-hwaseon.webp" width="235" alt="화선 낭자가 있는 점술 선택 화면. 누르면 캐릭터 영상이 열립니다."></a>
  <a href="_hwapae_deck.png"><img src="docs/readme/gallery-flower-deck.webp" width="235" alt="화패를 펼쳐 놓고 세 장을 고르는 실제 화면. 누르면 원본을 볼 수 있습니다."></a>
  <a href="_webtoon_p3.png"><img src="docs/readme/gallery-webtoon.webp" width="235" alt="사주 풀이가 만화 장면으로 이어지는 웹툰 화면. 누르면 원본을 볼 수 있습니다."></a>
</p>

<details>
<summary><strong>🂠 꽃패 세 장 뒤집기</strong> · 실제 결과 화면 펼쳐 보기</summary>

이 판의 첫 패는 <strong>도사(道士)</strong>입니다. 같은 패라도 어느 자리에 놓였는지에 따라 읽는 맥락이 달라집니다.

<img src="docs/readme/gallery-flower-result.webp" width="640" alt="세 장의 화패가 나란히 펼쳐진 결과. 과거는 도사(道士), 현재는 도·여섯(刀六), 앞날은 잔·넷(盞四)입니다.">

</details>

## 달 아래, 세 사람에게 건네는 세 가지

| 찾아갈 사람 | 건네는 것 | 돌아오는 것 |
| --- | --- | --- |
| **화선 낭자** | 내가 고른 꽃패 세 장 | 지나온 흐름부터 앞날까지, 패의 그림과 자리를 연결한 풀이 |
| **만월 아씨** | 태어난 날짜와 시각 | 연·월·일·시의 네 기둥을 바탕으로 풀어낸 내 사주 이야기 |
| **몽이 도령** | “어젯밤 꿈에 호랑이가 나왔어요” 같은 한 장면 | 꿈속 상징을 짚어 주는 해몽 |

![오늘의 꽃패는 1장, 마음의 길은 3장, 깊은 인연 풀이는 5장, 운명의 화원은 10장을 펼칩니다.](docs/readme/flower-spreads.svg)

오늘 하루가 궁금하면 한 장을 고릅니다. 같은 고민을 과거·현재·앞날로 나누어 보고 싶으면 ‘마음의 길’로, 내 마음과 상대의 마음을 따로 읽고 싶으면 ‘깊은 인연 풀이’로 들어갑니다. [꽃패 메뉴와 각 자리의 뜻](front/js/readers/hwapae-reader.js)

## 생일 하나가 이야기로 바뀌는 과정

**2000년 1월 1일**을 넣으면 달력 엔진은 그날의 일주를 <strong>무오(戊午)</strong>로 계산합니다. 일주는 태어난 *날*을 나타내는 두 글자입니다. 사주경은 이렇게 계산한 값에 인물의 목소리와 그림을 더해, 같은 생일을 숫자로도 이야기로도 읽게 합니다.

### 사주의 어떤 부분을 보고 MBTI 네 축을 읽을까?

달력 엔진이 계산한 사주를 받아, 월하몽의 자체 규칙이 네 축의 경향을 각각 해석합니다. ‘일간’은 태어난 날을 나타내는 두 글자 중 첫 글자이고, ‘오행’은 목·화·토·금·수입니다.

```mermaid
---
config:
  flowchart:
    padding: 8
    rankSpacing: 24
---
flowchart LR
    accTitle: 사주에서 읽는 네 가지 성향
    accDescr: E/I는 음양 비율, S/N은 토·금과 목·수의 비중, T/F는 일간의 음양과 금·화·수 비중, J/P는 오행 분포의 고른 정도를 봅니다.
    yin["음양 비율"] --> ei["E/I · 외향/내향"]
    elements["토·금 대 목·수"] --> sn["S/N · 감각/직관"]
    day["일간 음양과 금·화·수"] --> tf["T/F · 사고/감정"]
    balance["오행 균형도"] --> jp["J/P · 판단/인식"]
```

예를 들어 여덟 글자 중 양이 네 개면 양의 비율은 50%입니다. 이때 E/I 칸에는 **미정**이 남습니다. 모듈은 각 축에서 어떤 값이 판단의 근거였는지도 함께 돌려줍니다. [사주 달력 엔진](engine/saju/pillars.py) · [사주 × MBTI 모듈](engine/divination/saju_mbti/) · [화패 풀이 엔진](engine/divination/hwapae/)

## 내 컴퓨터에서 첫 장 열기

Python 3.12에서 다음 명령으로 시작합니다.

```sh
git clone https://github.com/Technoetic/saju-mbti-fusion.git
cd saju-mbti-fusion
python -m venv .venv
```

가상환경은 Windows PowerShell에서 `.\.venv\Scripts\Activate.ps1`, macOS·Linux에서는 `source .venv/bin/activate`로 엽니다.

```sh
python -m pip install -r requirements.txt
python -m uvicorn web.server:app --host 127.0.0.1 --port 8000
```

브라우저에서 `http://127.0.0.1:8000`을 열면 월하몽에 들어갑니다. 키 없이 첫 계산을 해보려면 `http://127.0.0.1:8000/api/saju/daily?date=2000-01-01`을 여세요. 응답의 `day_pillar.ganzhi_ko`에서 **무오**를 확인할 수 있습니다. 생성형 이야기 기능에 쓸 키는 [환경 설정 예시](.env.example)에 안내되어 있습니다.
