![붉은 보름달을 가로지르는 두 마리 학. 금빛 글씨로 새긴 사주경, 월하몽.](docs/readme/moon-gate.svg)

# 사주경 · 월하몽

**꽃패 78장이 뒤집혀 있습니다. 딱 세 장만 고른다면, 어떤 패에 손이 갈까요?**

화선 낭자의 ‘마음의 길’에서는 첫 번째 패가 지나온 일을, 두 번째 패가 지금을, 마지막 패가 앞으로의 흐름을 들려줍니다. 그 옆방에는 생일을 들고 찾아가는 만월 아씨와 어젯밤 꿈 이야기를 기다리는 몽이 도령이 있습니다.

[시각화 도감 보기 ↓](#월하몽-시각화-도감)

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

## 월하몽 시각화 도감

꽃패를 고르는 화면부터 달력 엔진까지, 궁금한 질문을 펼쳐 보세요. 본문의 [꽃패 장수 그림](#달-아래-세-사람에게-건네는-세-가지)은 D3로, [MBTI 네 축의 흐름](#사주의-어떤-부분을-보고-mbti-네-축을-읽을까)은 Mermaid로 그렸습니다. 아래에서는 나머지 23개 도구의 결과를 볼 수 있습니다.

<details>
<summary><strong>꽃패 78장 중 무엇을 뽑을까?</strong></summary>

![메이저 22장과 봉·잔·도·전 각 14장으로 이뤄진 78장](docs/readme/atlas/data/vega-lite-deck.svg)

**Vega-Lite** · 점 하나가 꽃패 한 장입니다. 78장 중 메이저는 22장이고, 나머지 56장은 네 무늬에 14장씩 나뉩니다.

![봉은 동백, 잔은 연꽃, 도는 국화, 전은 모란으로 이어지는 가지 그림](docs/readme/atlas/structure/flower-suits.png)

**markmap** · 화패 속 꽃은 무늬를 읽는 단서입니다. 연꽃이 핀 ‘잔’은 감정과 관계로, 국화가 핀 ‘도’는 사고와 결단으로 이어집니다.

![균등 비복원 추출에서 1·3·5·10장을 뽑을 때 메이저가 하나 이상 나올 확률](docs/readme/atlas/data/altair-major-chance.svg)

**Altair** · 한 장이라면 메이저를 만날 확률은 28.2%, 세 장이라면 63.6%입니다. 모든 패가 같은 확률로 뽑히고 한 번 뽑은 패는 되돌리지 않는다고 가정한 이론값입니다.

![서로 다른 세 장을 순서대로 뽑는 경우의 수는 78 곱하기 77 곱하기 76, 총 456,456가지](docs/readme/atlas/type/katex.png)

**KaTeX** · ‘마음의 길’에서는 첫 패가 과거, 둘째가 현재, 셋째가 앞날입니다. 세 자리의 순서를 구분하면 `78 × 77 × 76 = 456,456`가지로 펼칠 수 있습니다.

![오늘의 꽃패 500~700자에서 운명의 화원 2,500~3,500자까지 네 메뉴의 권장 풀이 분량](docs/readme/atlas/web/observable.png)

**Observable Plot** · 선의 양 끝은 메뉴에 설정된 권장 글자 수입니다. 오늘의 꽃패에는 짧은 메시지를, 운명의 화원에는 긴 풀이를 요청합니다. [메뉴 설정](front/js/readers/hwapae-reader.js)

</details>

<details>
<summary><strong>달력은 생일·시각·출생지를 어떻게 읽을까?</strong></summary>

![브라우저에서 일진 API를 거쳐 정오 기준 계산 결과 무오를 받는 순서](docs/readme/atlas/structure/daily-request.png)

**PlantUML** · `2000-01-01`로 일진을 조회하면 API는 정오를 기준으로 만세력을 호출하고, 브라우저에 일주 ‘무오’를 돌려줍니다. [도식 원본](docs/readme/atlas/structure/daily-request.puml)

![2000년 1월 1일부터 3월 1일까지 천간과 지지가 원래 조합에 돌아오는 주기](docs/readme/atlas/data/matplotlib-day-cycle.png)

**Matplotlib** · 첫 글자는 10일, 둘째 글자는 12일마다 돌아옵니다. 두 글자가 동시에 ‘무오’로 돌아오는 날은 60일 뒤인 2000년 3월 1일입니다.

![연도에서 4를 뺀 나머지로 천간과 지지 번호를 구하는 Python 원문](docs/readme/atlas/type/shiki.png)

**Shiki** · 연주를 계산하는 두 줄입니다. `idx = (year - 4) % 60`으로 순번을 구하고, `return _pack(idx % 10, idx % 12)`로 두 글자를 고릅니다. [복사 가능한 Python 원문](engine/saju/pillars.py)

![24시간을 두 시간씩 나눈 12개의 시지. 자시는 23시와 0시를 포함한다](docs/readme/atlas/data/ggplot2-hour-branches.svg)

**ggplot2** · 하루를 두 시간씩 묶으면 열두 시지가 됩니다. 23시와 0시는 날짜 경계를 사이에 두고 같은 자시(子時)에 속합니다.

![출생지 좌표표에서 고른 서울·강릉·대전·광주·부산·제주의 위치](docs/readme/atlas/web/leaflet.png)

**Leaflet** · 앱은 출생지 이름에 대응하는 경도를 시간 보정에 씁니다. 지도는 좌표표에서 고른 여섯 도시를 보여줍니다. [출생지 좌표표](engine/saju/geo_lut.py)

</details>

<details>
<summary><strong>‘무오’ 두 글자에서 토와 화는 어떻게 나올까?</strong></summary>

![무(戊)는 토 1.0점, 오(午)는 화 0.7점과 토 0.3점에 기여하는 구조](docs/readme/atlas/structure/pillar-elements.png)

**Graphviz** · 천간 ‘무’가 토에 1점을 보탭니다. 지지 ‘오’의 몫까지 합치면 무오 한 기둥의 결과는 토 1.3점, 화 0.7점입니다. [도식 원본](docs/readme/atlas/structure/pillar-elements.dot)

![지지 오 한 글자의 가중치 중 화는 0.7, 토는 0.3](docs/readme/atlas/web/chartjs.png)

**Chart.js** · 둘째 글자 ‘오’만 확대하면 한 글자의 1점이 화 70%, 토 30%로 나뉩니다. [앱의 오행 가중치](engine/saju/wuxing.py)

![목에서 화, 토, 금, 수를 거쳐 다시 목으로 이어지는 상생 관계](docs/readme/atlas/web/cytoscape.png)

**Cytoscape.js** · 오행을 관계로 읽을 때는 화살표를 따라갑니다. 앱의 상생 규칙에서 목은 화를 돕고, 다섯 화살표를 모두 지나면 다시 목에 닿습니다. [상생 규칙](engine/saju/compat.py)

</details>

<details>
<summary><strong>사주 × MBTI에서 ‘미정’은 언제 나올까?</strong></summary>

![여덟 글자 중 양이 넷이면 비율은 0.50으로 0.45와 0.55 사이](docs/readme/atlas/type/mathjax.png)

**MathJax** · 양이 네 개면 `4 ÷ 8 = 0.50`입니다. E/I 규칙의 두 경계 사이에 있어 이 축은 미정으로 남습니다.

![오행 합계 8점의 정수 조합에서 S, N, 미정으로 갈리는 구역](docs/readme/atlas/data/seaborn-sn-grid.png)

**seaborn** · 토·금을 합한 점수와 목·수를 합한 점수를 한 칸씩 바꿔 본 예시입니다. 두 그룹에 넣지 않은 점수는 화에 배정했습니다. 색은 월하몽 S/N 함수의 반환값입니다.

![오행 합계가 8점인 세 사례의 표준편차 0.49, 0.80, 1.36과 각각의 J, 미정, P 판정](docs/readme/atlas/data/plotly-element-spread.svg)

**Plotly** · 합계가 8점으로 같아도 고르게 퍼진 사례는 J, 한쪽에 몰린 사례는 P를 반환합니다. 중간 사례는 미정입니다. [네 축의 계산 규칙](engine/divination/saju_mbti/predictor.py)

![INFJ·ENFJ·INTJ·ENTJ의 네 인지 기능을 유형별 순서로 비교](docs/readme/atlas/web/echarts.png)

**Apache ECharts** · MBTI 유형을 입력받는 별도 모듈에는 유형별 기능 순서가 있습니다. 같은 N을 가진 네 유형을 골라, 각각 어떤 기능을 첫자리에 놓는지 비교했습니다. [유형별 기능표](engine/saju/mbti_functions.py)

</details>

<details>
<summary><strong>화면에서 패를 눌렀을 때, 앱 안에서는?</strong></summary>

![화면 하단의 홈·일지·프로필 탭을 그린 스케치](docs/readme/atlas/web/excalidraw.png)

**Excalidraw** · 화면 아래의 세 탭은 홈·일지·프로필입니다. 앱의 하단 탐색 영역을 손그림으로 옮겼습니다. [화면 원본](front/index.html)

![카드를 A·A·B·C 순으로 누른 예시에서 선택한 장수는 1·1·2·3](docs/readme/atlas/web/wavedrom.png)

**WaveDrom** · 같은 패 A를 연달아 눌러도 선택한 패는 한 장입니다. 예시의 클릭과 장수 변화를 위아래로 맞춰 보면 두 번째 클릭에서 차이가 드러납니다.

![이미 고른 카드나 정원을 넘은 클릭은 반환하고 새 카드 번호만 추가하는 JavaScript](docs/readme/atlas/type/highlight.png)

**highlight.js** · 방금 본 동작의 원문입니다. 이미 고른 번호면 돌아가고, 자리가 남아 있을 때만 목록에 넣습니다. [복사 가능한 JavaScript 원문](front/js/readers/hwapae-reader.js)

<img src="docs/readme/atlas/structure/flower-reading.png" width="360" alt="화패 화면에서 서버를 거쳐 화패 풀이 엔진으로 패와 질문이 전달되는 경로">

**D2** · 선택이 끝나면 화면이 뽑은 패와 질문을 서버에 전달합니다. 각 상자의 파일을 따라가면 요청을 받는 곳과 풀이를 호출하는 곳을 찾을 수 있습니다. [도식 원본](docs/readme/atlas/structure/flower-reading.d2)

![방문자, 월하몽, 생성형 풀이를 요청받는 외부 서비스 BizRouter의 관계](docs/readme/atlas/structure/story-context.png)

**Structurizr** · 한 걸음 물러서 보면 방문자는 월하몽에 풀이를 요청하고, 생성형 이야기가 필요한 경로에서는 월하몽이 BizRouter를 호출합니다. [시스템 구성 원본](docs/readme/atlas/structure/story-context.dsl)

![배경음 Moon Over Han의 20초 지점부터 0.5초마다 골라낸 대표음 여덟 개를 오선에 표시](docs/readme/atlas/web/abcjs.png)

**abcjs** · 월하몽에서 들리는 배경음의 20초 지점부터 0.5초마다 대표음 하나를 골랐습니다. 여덟 음표의 간격은 분석 시점에 맞췄습니다. [원곡 Moon Over Han](front/media/bg/Moon%20Over%20Han.wav)

</details>
