// ============================================================
// 화선 낭자 · 화패 (花牌) 풀이 — ADR-042 Phase G 외부 모듈화
// ============================================================
// 의존: window.LLMUtils, window.simpleMarkdown, window.WHM
// ============================================================
(function initHwapaeReader() {
// 화패 (花牌) 풀이 — 78장 정통 타로 + 한국 사극·신화 모티프
//  메이저 22장: 한국·동양 신화·역사 인물 + 각 카드별 꽃·꽃말
//  마이너 56장: 4슈트 — 봉(棒·동백)·잔(盞·연꽃)·도(刀·국화)·전(錢·모란)
const 화패_데이터 = [
  // ─── 메이저 22장 ───
  { 한자:'狂客', 한글:'광객',  sub:'풍류 도령',  의미:'새 시작·순수·자유로운 영혼',  인물:'방랑하는 신선 도령', 꽃:'민들레·벚꽃', 꽃말:'무모한 사랑·정신적 사랑', group:'major' },
  { 한자:'道士', 한글:'도사',  sub:'천지의 기운',  의미:'의지·창조력·능력의 발현',  인물:'환웅·천기 다루는 도사', 꽃:'모란',  꽃말:'왕자의 풍모·부귀',  group:'major' },
  { 한자:'巫女', 한글:'무녀',  sub:'바리공주',  의미:'직관·비밀·내면의 지혜',  인물:'바리데기(저승 다녀온 무녀)', 꽃:'달맞이꽃', 꽃말:'말없는 사랑·기다림',  group:'major' },
  { 한자:'王后', 한글:'왕후',  sub:'만물의 어머니',  의미:'풍요·모성·창조성',  인물:'마고할미',  꽃:'작약',  꽃말:'수줍음·부귀',  group:'major' },
  { 한자:'君王', 한글:'군왕',  sub:'통치의 옥좌',  의미:'권위·안정·아버지의 힘',  인물:'단군왕검·세종대왕', 꽃:'국화',  꽃말:'고결·청결·절개',  group:'major' },
  { 한자:'大師', 한글:'대사',  sub:'가르치는 성인',  의미:'전통·가르침·영적 권위',  인물:'원효대사·공자',  꽃:'연꽃',  꽃말:'청정·순결·깨달음',  group:'major' },
  { 한자:'連理', 한글:'연리',  sub:'견우와 직녀',  의미:'사랑·선택·결합·조화',  인물:'견우와 직녀',  꽃:'수련·연리화', 꽃말:'영원한 사랑·청순',  group:'major' },
  { 한자:'戰車', 한글:'전차',  sub:'의지의 무장',  의미:'승리·추진력·통제',  인물:'이순신·계백',  꽃:'해바라기',  꽃말:'당신만을 바라봄·일편단심',  group:'major' },
  { 한자:'忍',  한글:'인',  sub:'호랑이를 길들이는', 의미:'내면의 힘·부드러운 통제·인내',  인물:'선덕여왕·신사임당', 꽃:'동백',  꽃말:'겸손한 아름다움·강인함',  group:'major' },
  { 한자:'隱者', 한글:'은자',  sub:'산속의 신선',  의미:'고독·성찰·내면의 빛',  인물:'산신령·도인',  꽃:'매화',  꽃말:'고결한 마음·인내·기품',  group:'major' },
  { 한자:'輪廻', 한글:'윤회',  sub:'운명의 수레바퀴', 의미:'운명·변화의 순환·행운',  인물:'삼신할미',  꽃:'무궁화',  꽃말:'영원·끝없는 아름다움',  group:'major' },
  { 한자:'正義', 한글:'정의',  sub:'염라의 판관',  의미:'공정·균형·인과·진실',  인물:'염라대왕·포청천',  꽃:'백합',  꽃말:'순결·위엄·변함없음',  group:'major' },
  { 한자:'懸客', 한글:'현객',  sub:'거꾸로 매달려',  의미:'희생·멈춤·관점 전환·깨달음',  인물:'달마대사',  꽃:'연꽃봉오리', 꽃말:'고요한 마음·깨달음의 시작', group:'major' },
  { 한자:'死神', 한글:'사신',  sub:'저승의 차사',  의미:'종말과 시작·변환·재생',  인물:'저승사자',  꽃:'상사화',  꽃말:'이루어질 수 없는 사랑·환생', group:'major' },
  { 한자:'節制', 한글:'절제',  sub:'두 옥병의 선녀', 의미:'균형·조화·절제·융합',  인물:'천계의 선녀',  꽃:'수국',  꽃말:'변하지 않는 사랑·진심',  group:'major' },
  { 한자:'魔',  한글:'마',  sub:'도깨비의 옥좌',  의미:'속박·욕망·집착·그림자',  인물:'도깨비(독각귀)',  꽃:'양귀비',  꽃말:'위로·망각·헛된 환상',  group:'major' },
  { 한자:'落雷', 한글:'낙뢰',  sub:'벼락 맞은 누각', 의미:'갑작스러운 붕괴·충격·진실의 폭로',  인물:'뇌신(벼락신)',  꽃:'할미꽃',  꽃말:'슬픈 추억·충성',  group:'major' },
  { 한자:'七星', 한글:'칠성',  sub:'북두칠성의 인도', 의미:'희망·영감·평온·치유',  인물:'칠성신·직녀의 동생', 꽃:'도라지·물망초', 꽃말:'영원한 사랑·나를 잊지 마세요', group:'major' },
  { 한자:'月',  한글:'월',  sub:'달 위의 항아',  의미:'환상·무의식·두려움·직관',  인물:'항아(만월 아씨)',  꽃:'월하향·달맞이꽃', 꽃말:'신비·부드러운 매혹·기다림', group:'major' },
  { 한자:'日',  한글:'일',  sub:'삼족오의 동자',  의미:'기쁨·성공·활력·깨달음',  인물:'삼족오의 동자',  꽃:'해바라기·금잔화', 꽃말:'환한 빛·인내 끝의 기쁨',  group:'major' },
  { 한자:'審判', 한글:'심판',  sub:'천계의 부름',  의미:'부활·각성·부름·재생',  인물:'천녀와 신장',  꽃:'연꽃·영지',  꽃말:'신성·청정·부활',  group:'major' },
  { 한자:'天下', 한글:'천하',  sub:'완성된 세계',  의미:'완성·성취·통합·여정의 끝',  인물:'서왕모(西王母)',  꽃:'사군자(매·난·국·죽)', 꽃말:'사계절의 완전한 조화',  group:'major' },

  // ─── 봉(棒) 슈트 — 동백의 길 · 행동·열정 (주작) 14장 ───
  { 한자:'棒一',  한글:'봉·하나',  sub:'새싹 돋은 죽장',  의미:'새 열정의 시작·창조의 불꽃',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒二',  한글:'봉·둘',  sub:'정자 위 갈림길',  의미:'결단의 갈림길·미래 설계',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒三',  한글:'봉·셋',  sub:'먼바다 보는 도령', 의미:'확장과 기다림·시야 넓어짐',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒四',  한글:'봉·넷',  sub:'동백 화환의 정자', 의미:'안정과 축하·잔치의 기쁨',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒五',  한글:'봉·다섯',  sub:'다섯 청년의 다툼', 의미:'경쟁·작은 갈등의 혼란',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒六',  한글:'봉·여섯',  sub:'백마 탄 승리',  의미:'영광의 귀환·인정',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒七',  한글:'봉·일곱',  sub:'홀로 막아내는',  의미:'방어·의지·홀로서기',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒八',  한글:'봉·여덟',  sub:'날아가는 죽장',  의미:'빠른 소식·빠른 진전',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒九',  한글:'봉·아홉',  sub:'부상에 기댄 무사', 의미:'끝까지 견디는 인내·경계',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒十',  한글:'봉·열',  sub:'무거운 짊',  의미:'무거운 책임·과한 부담',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒童',  한글:'봉동자',  sub:'호기심의 어린 도령', 의미:'새 모험의 호기심·뜨거운 영감',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒騎',  한글:'봉기사',  sub:'질주하는 무사',  의미:'추진력·충동·열정의 폭주',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒妃',  한글:'봉왕비',  sub:'동백 든 우아한 여인', 의미:'정열적 자신감·카리스마',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },
  { 한자:'棒王',  한글:'봉대왕',  sub:'위엄 있는 군주',  의미:'지도력의 완성·결단',  꽃:'동백', 꽃말:'강인함·정열', group:'봉' },

  // ─── 잔(盞) 슈트 — 연꽃의 길 · 감정·사랑 (현무) 14장 ───
  { 한자:'盞一',  한글:'잔·하나',  sub:'백자에 핀 연꽃',  의미:'새 사랑의 시작·감정의 샘',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞二',  한글:'잔·둘',  sub:'마주 든 두 잔',  의미:'마음의 결합·인연',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞三',  한글:'잔·셋',  sub:'세 여인의 건배',  의미:'축하·우정·공동체의 기쁨',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞四',  한글:'잔·넷',  sub:'네 번째만 보는 자', 의미:'권태·무관심·만족 못함',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞五',  한글:'잔·다섯',  sub:'쓰러진 세 잔',  의미:'상실·실망·후회',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞六',  한글:'잔·여섯',  sub:'순수한 추억',  의미:'향수·어린 시절·옛 추억',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞七',  한글:'잔·일곱',  sub:'환상의 일곱 잔',  의미:'환영의 유혹·선택지의 혼란',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞八',  한글:'잔·여덟',  sub:'떠나는 뒷모습',  의미:'포기·새 길 찾아 떠남',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞九',  한글:'잔·아홉',  sub:'풍성한 잔의 만족', 의미:'충만한 만족·소원 성취',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞十',  한글:'잔·열',  sub:'무지개 아래 가족', 의미:'가족의 행복·정서적 완성',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞童',  한글:'잔동녀',  sub:'잔에서 솟은 잉어', 의미:'감정의 영감·예술적 메시지',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞騎',  한글:'잔기사',  sub:'잔 받쳐 든 기수', 의미:'낭만의 등장·고백·제안',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞妃',  한글:'잔왕비',  sub:'잔을 들여다보는', 의미:'공감·직관·따뜻한 마음',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },
  { 한자:'盞王',  한글:'잔대왕',  sub:'거친 바다 위 평온', 의미:'감정의 통제·자비·관용',  꽃:'연꽃', 꽃말:'청정·순결·정신적 사랑', group:'잔' },

  // ─── 도(刀) 슈트 — 국화의 길 · 사고·갈등 (청룡) 14장 ───
  { 한자:'刀一',  한글:'도·하나',  sub:'국화 화관의 검',  의미:'명료한 진실의 시작·결단',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀二',  한글:'도·둘',  sub:'눈가린 여인의 두 검', 의미:'결정 보류·갈등 중 균형',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀三',  한글:'도·셋',  sub:'심장에 박힌 세 검', 의미:'슬픔·상처·이별',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀四',  한글:'도·넷',  sub:'잠든 무사',  의미:'휴식·회복의 시간',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀五',  한글:'도·다섯',  sub:'공허한 승리',  의미:'갈등·패배·자존심 상처',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀六',  한글:'도·여섯',  sub:'강을 건너는 배',  의미:'조용한 전환·떠남과 회복',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀七',  한글:'도·일곱',  sub:'다섯 검을 훔쳐',  의미:'책략·회피·은밀함',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀八',  한글:'도·여덟',  sub:'묶여 눈가린 여인', 의미:'속박·제한·무력감',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀九',  한글:'도·아홉',  sub:'악몽에 시달리는',  의미:'불안·후회·악몽',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀十',  한글:'도·열',  sub:'쓰러진 무사',  의미:'끝·바닥·끝맺음',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀童',  한글:'도동자',  sub:'바람 가르는 어린이', 의미:'예리한 호기심·새 관점',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀騎',  한글:'도기사',  sub:'폭풍 같은 질주',  의미:'충동의 추진·돌파',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀妃',  한글:'도왕비',  sub:'곧게 든 검',  의미:'명료한 사고·독립·결단',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },
  { 한자:'刀王',  한글:'도대왕',  sub:'지성의 군주',  의미:'지성·논리·권위',  꽃:'국화', 꽃말:'절개·진실·고결', group:'도' },

  // ─── 전(錢) 슈트 — 모란의 길 · 물질·현실 (백호) 14장 ───
  { 한자:'錢一',  한글:'전·하나',  sub:'엽전과 모란',  의미:'새 풍요·실질적 기반',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢二',  한글:'전·둘',  sub:'두 엽전 저글링',  의미:'균형·유연·변동 대응',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢三',  한글:'전·셋',  sub:'사찰을 짓는 장인', 의미:'협업과 기술·인정',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢四',  한글:'전·넷',  sub:'엽전을 움켜쥔',  의미:'인색과 보존·집착',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢五',  한글:'전·다섯',  sub:'눈길의 두 빈민',  의미:'빈곤과 소외·결핍',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢六',  한글:'전·여섯',  sub:'베푸는 부자',  의미:'자비와 나눔·관대함',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢七',  한글:'전·일곱',  sub:'농부의 평가',  의미:'인내와 평가·중간 점검',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢八',  한글:'전·여덟',  sub:'장인의 손',  의미:'숙련과 노력·집중',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢九',  한글:'전·아홉',  sub:'정원의 여인',  의미:'풍요와 독립·자족',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢十',  한글:'전·열',  sub:'가문의 풍요',  의미:'유산과 가문·가족의 부',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢童',  한글:'전동자',  sub:'엽전을 들여다보는', 의미:'배움과 성실·기반 다지기',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢騎',  한글:'전기사',  sub:'신중한 무사',  의미:'책임과 신중·꾸준함',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢妃',  한글:'전왕비',  sub:'정원의 어머니',  의미:'풍요와 양육·안정',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
  { 한자:'錢王',  한글:'전대왕',  sub:'풍요의 군주',  의미:'사업적 성공의 완성·재력',  꽃:'모란', 꽃말:'부귀·영화·풍성함', group:'전' },
];
// 화패 풀이 메뉴 — 4가지 스프레드
const 화패_메뉴 = {
  daily: {
  이름: '오늘의 꽃패', 한자: '今日', 부제: '오늘 하루의 흐름',
  장수: 1, 영역선택: false, 영역고정: null,
  위치: ['今日'],
  위치설명: ['오늘의 흐름'],
  분량: '500~700자, 가볍고 부담 없게',
  설명: '하루의 메시지를 한 장의 화패로'
  },
  path: {
  이름: '마음의 길', 한자: '心路', 부제: '과거·현재·앞날',
  장수: 3, 영역선택: true, 영역고정: null,
  위치: ['過去', '現在', '前路'],
  위치설명: ['지나간 흐름', '지금', '앞으로'],
  분량: '1200~1600자',
  설명: '세 장으로 흐름의 큰 그림을'
  },
  love: {
  이름: '깊은 인연 풀이', 한자: '緣脈', 부제: '연애·관계 전용',
  장수: 5, 영역선택: false, 영역고정: 'love',
  위치: ['我心', '彼心', '緣', '障', '未來'],
  위치설명: ['내 마음', '상대의 마음', '두 사람의 관계', '장애물', '앞으로의 흐름'],
  분량: '1700~2200자',
  설명: '두 마음을 깊이 들여다보는 다섯 장'
  },
  celtic: {
  이름: '운명의 화원', 한자: '天園', 부제: '켈틱 크로스 정통',
  장수: 10, 영역선택: true, 영역고정: null,
  위치: ['現', '障', '過', '將', '志', '潛', '我', '外', '望', '果'],
  위치설명: ['현재 상황', '장애·도전', '가까운 과거', '가까운 미래', '의식적 목표', '무의식적 영향', '자신의 태도', '외부 환경', '희망과 두려움', '최종 결과'],
  분량: '2500~3500자',
  설명: '인생의 큰 결정과 복잡한 고민을 위한 열 장'
  },
};
let lastHwapaeMenu = 'path'; // 기본: 마음의 길 (3장)

// 현재 메뉴에 따라 동적으로 사용되는 위치 배열
function getCurrentPositions() {
  return 화패_메뉴[lastHwapaeMenu] || 화패_메뉴.path;
}

/**
 * 카드 그림 (슈트별 SVG) — 동양 라인아트
 *  major: 8각 별 + 둘레 작은 별들 (운명의 큰 흐름)
 *  봉(棒): 동백꽃 (5장 둥근 꽃잎 + 수술) — 행동·열정
 *  잔(盞): 연꽃 (위에서 본 꽃잎 8장) — 감정·사랑
 *  도(刀): 국화 (방사형 가는 꽃잎) — 사고·갈등
 *  전(錢): 모란 (풍성한 큰 꽃잎) — 물질·재물
 */
function getCardArt(group) {
  const C = 'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"';
  const svgs = {
  major: `<svg viewBox="0 0 40 40" ${C}>
  <path d="M20 4 L23 16 L35 16 L25.5 23 L29 35 L20 28 L11 35 L14.5 23 L5 16 L17 16 Z"/>
  <circle cx="20" cy="20" r="1.4" fill="currentColor" stroke="none"/>
  <circle cx="8"  cy="8"  r="0.9" fill="currentColor" stroke="none"/>
  <circle cx="32" cy="8"  r="0.9" fill="currentColor" stroke="none"/>
  <circle cx="8"  cy="32" r="0.9" fill="currentColor" stroke="none"/>
  <circle cx="32" cy="32" r="0.9" fill="currentColor" stroke="none"/>
  </svg>`,
  봉: `<svg viewBox="0 0 40 40" ${C}>
  <circle cx="20" cy="20" r="4.5"/>
  <circle cx="20" cy="11" r="4.5"/>
  <circle cx="28" cy="16" r="4.5"/>
  <circle cx="25" cy="26" r="4.5"/>
  <circle cx="15" cy="26" r="4.5"/>
  <circle cx="12" cy="16" r="4.5"/>
  <circle cx="20" cy="20" r="1.4" fill="currentColor" stroke="none"/>
  <circle cx="17" cy="18" r="0.7" fill="currentColor" stroke="none"/>
  <circle cx="23" cy="18" r="0.7" fill="currentColor" stroke="none"/>
  <circle cx="20" cy="22" r="0.7" fill="currentColor" stroke="none"/>
  </svg>`,
  잔: `<svg viewBox="0 0 40 40" ${C}>
  <ellipse cx="20" cy="20" rx="14" ry="6" opacity="0.5"/>
  <path d="M20 13 Q26 16 24 22 Q20 24 16 22 Q14 16 20 13 Z"/>
  <path d="M20 13 Q14 16 16 22 Q20 24 24 22 Q26 16 20 13 Z" transform="rotate(45 20 18)"/>
  <path d="M20 13 Q14 16 16 22 Q20 24 24 22 Q26 16 20 13 Z" transform="rotate(90 20 18)"/>
  <path d="M20 13 Q14 16 16 22 Q20 24 24 22 Q26 16 20 13 Z" transform="rotate(135 20 18)"/>
  <circle cx="20" cy="18" r="1.4" fill="currentColor" stroke="none"/>
  </svg>`,
  도: `<svg viewBox="0 0 40 40" ${C}>
  <circle cx="20" cy="20" r="2" fill="currentColor" stroke="none"/>
  <line x1="20" y1="4"  x2="20" y2="14"/>
  <line x1="20" y1="26" x2="20" y2="36"/>
  <line x1="4"  y1="20" x2="14" y2="20"/>
  <line x1="26" y1="20" x2="36" y2="20"/>
  <line x1="8"  y1="8"  x2="15.5" y2="15.5"/>
  <line x1="24.5" y1="24.5" x2="32" y2="32"/>
  <line x1="32" y1="8"  x2="24.5" y2="15.5"/>
  <line x1="15.5" y1="24.5" x2="8"  y2="32"/>
  <line x1="20" y1="7"  x2="22" y2="14"/>
  <line x1="20" y1="7"  x2="18" y2="14"/>
  <line x1="20" y1="33" x2="22" y2="26"/>
  <line x1="20" y1="33" x2="18" y2="26"/>
  <line x1="7"  y1="20" x2="14" y2="22"/>
  <line x1="7"  y1="20" x2="14" y2="18"/>
  <line x1="33" y1="20" x2="26" y2="22"/>
  <line x1="33" y1="20" x2="26" y2="18"/>
  </svg>`,
  전: `<svg viewBox="0 0 40 40" ${C}>
  <path d="M20 8 Q14 10 13 16 Q12 11 16 7 Q19 6 20 8 Z"/>
  <path d="M20 8 Q26 10 27 16 Q28 11 24 7 Q21 6 20 8 Z"/>
  <path d="M27 14 Q31 17 30 23 Q33 19 31 14 Q29 12 27 14 Z"/>
  <path d="M13 14 Q9 17 10 23 Q7 19 9 14 Q11 12 13 14 Z"/>
  <path d="M28 22 Q30 27 27 31 Q31 30 31 25 Q30 21 28 22 Z"/>
  <path d="M12 22 Q10 27 13 31 Q9 30 9 25 Q10 21 12 22 Z"/>
  <path d="M24 28 Q22 32 18 32 Q22 34 25 31 Q26 28 24 28 Z"/>
  <path d="M16 28 Q18 32 22 32 Q18 34 15 31 Q14 28 16 28 Z"/>
  <circle cx="20" cy="20" r="3.5" fill="currentColor" stroke="none" opacity="0.7"/>
  <circle cx="20" cy="20" r="5.5"/>
  </svg>`,
  };
  return svgs[group] || svgs.major;
}

const 화패_카테고리 = {
  love:  { 한자: '戀情', 한글: '연애·결혼', 분석초점: '두 사람의 감정 흐름, 인연의 결, 가까워질지 멀어질지' },
  job:  { 한자: '職場', 한글: '직장·일',  분석초점: '현재 일의 흐름, 동료·상사 관계, 변화 가능성' },
  business: { 한자: '財貨', 한글: '사업·재물', 분석초점: '사업·투자·금전의 흐름, 큰 기회와 위험' },
  health:  { 한자: '健康', 한글: '건강',  분석초점: '몸과 마음의 균형, 신경 써야 할 부분' },
  family:  { 한자: '家門', 한글: '가족',  분석초점: '가족 간의 흐름, 화목·갈등, 책임' },
  friend:  { 한자: '人緣', 한글: '인간관계·친구', 분석초점: '주변 사람들과의 어울림, 새로운 인연, 정리할 인연' },
  study:  { 한자: '學業', 한글: '학업·시험', 분석초점: '공부의 흐름, 시험·결과, 집중·노력의 방향' },
  other:  { 한자: '其他', 한글: '기타',  분석초점: '손님이 마음에 품고 있는 그 일' },
};

let lastHwapaeDraw = null;
let lastHwapaeCategory = 'love';
let drawnIndices = [];

// ── 메뉴 선택 ──
function applyHwapaeMenu() {
  const m = 화패_메뉴[lastHwapaeMenu] || 화패_메뉴.path;
  // 영역 fieldset 표시 여부
  const catFs = document.getElementById('hwapaeCatFieldset');
  if (m.영역선택) {
  catFs.style.display = '';
  // 번호 갱신
  catFs.querySelector('legend').textContent = '二. 영역 選';
  document.getElementById('hwapaeConcernLegend').textContent = '三. 마음에 떠오르는 것 心';
  } else {
  catFs.style.display = 'none';
  document.getElementById('hwapaeConcernLegend').textContent = '二. 마음에 떠오르는 것 心';
  // 영역 고정 처리
  if (m.영역고정) {
  lastHwapaeCategory = m.영역고정;
  document.querySelectorAll('.hw-cat-btn').forEach(b =>
  b.classList.toggle('active', b.dataset.cat === m.영역고정));
  } else if (lastHwapaeMenu === 'daily') {
  lastHwapaeCategory = 'other'; // 오늘의 꽃패는 전반
  }
  }
}
document.querySelectorAll('.hw-menu-btn').forEach(btn => {
  btn.addEventListener('click', () => {
  document.querySelectorAll('.hw-menu-btn').forEach(b => b.classList.toggle('active', b === btn));
  lastHwapaeMenu = btn.dataset.menu;
  applyHwapaeMenu();
  });
});

// ── 카테고리 선택 ──
document.querySelectorAll('.hw-cat-btn').forEach(btn => {
  btn.addEventListener('click', () => {
  document.querySelectorAll('.hw-cat-btn').forEach(b => b.classList.toggle('active', b === btn));
  lastHwapaeCategory = btn.dataset.cat;
  });
});

// step 전환 헬퍼
function showHwStep(stepId) {
  document.querySelectorAll('#tab-hwapae .hw-step').forEach(s => {
  s.classList.toggle('active', s.id === stepId);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── 1→2: [화패 뽑으러 가기] ──
document.getElementById('hwapaeGoToDrawBtn').addEventListener('click', () => {
  const question = document.getElementById('hwapaeQuestion').value.trim();
  if (!question) {
  alert('마음에 떠오르는 것을 한 줄이라도 적어주세요.');
  document.getElementById('hwapaeQuestion').focus();
  return;
  }
  // 카테고리 표시 업데이트
  const cat = 화패_카테고리[lastHwapaeCategory];
  document.getElementById('hwapaeCatDisplay').textContent = `${cat.한자} ${cat.한글}`;
  // 덱 초기화
  drawnIndices = [];
  renderHwSlots();

  // 셔플 단계 표시, 덱 영역 숨김
  const shuffleEl = document.getElementById('hwapaeShuffle');
  const deckWrap = document.getElementById('hwapaeDeckWrap');
  shuffleEl.classList.add('active');
  deckWrap.style.display = 'none';
  document.getElementById('hwapaeDeck').innerHTML = ''; // 이전 덱 정리

  showHwStep('hwapae-step-draw');

  // 셔플 시작
  startShuffleSequence(shuffleEl, deckWrap);
});

/**
 * 셔플 시퀀스 — 카드들이 1.6초간 빠르게 흔들리며 섞임 → 가운데로 모임 → 펼침
 */
function startShuffleSequence(shuffleEl, deckWrap) {
  const cards = shuffleEl.querySelectorAll('.shuffle-card');
  const totalDuration = 1600; // 셔플 1.6초
  const frameInterval = 75;
  const startTime = performance.now();

  // 셔플 사운드 (tap 빠르게 연속)
  for (let i = 0; i < 10; i++) {
  setTimeout(() => {
  try {
  const a = new Audio(`./media/sounds/tap${(i % 4) + 1}.ogg`);
  a.volume = 0.45;
  a.play().catch(() => {});
  } catch (_) {}
  }, i * 140);
  }

  // 매 프레임마다 카드를 무작위 위치로 흔듦
  const intervalId = setInterval(() => {
  const elapsed = performance.now() - startTime;
  if (elapsed >= totalDuration) {
  clearInterval(intervalId);
  // 가운데로 다시 모임
  cards.forEach(c => { c.style.transform = 'translate(0, 0) rotate(0deg)'; });
  // 0.4초 후 펼침 단계로
  setTimeout(() => {
  shuffleEl.classList.remove('active');
  deckWrap.style.display = '';
  // 종이 펼치는 효과음
  try {
  const a1 = new Audio('./media/sounds/paper_open.wav');
  a1.volume = 0.65;
  a1.play().catch(() => {});
  } catch (_) {}
  renderHwDeck();
  }, 400);
  return;
  }
  // 점점 더 격하게 흔들리도록 (1.6초 동안 amplitude 0.3→1)
  const intensity = 0.3 + Math.min(1, elapsed / totalDuration) * 0.7;
  cards.forEach(card => {
  const x = (Math.random() - 0.5) * 90 * intensity;
  const y = (Math.random() - 0.5) * 40 * intensity;
  const r = (Math.random() - 0.5) * 45 * intensity;
  card.style.transform = `translate(${x}px, ${y}px) rotate(${r}deg)`;
  });
  }, frameInterval);
}

// ── 2단계: 78장 덱 펼치기 (촤라라락 애니메이션) ──
function renderHwDeck() {
  const deck = document.getElementById('hwapaeDeck');
  const menu = 화패_메뉴[lastHwapaeMenu];
  const maxCards = menu.장수;
  // 매번 무작위 순서로 셔플
  const order = 화패_데이터.map((_, i) => i).sort(() => Math.random() - 0.5);
  deck.innerHTML = order.map(i =>
  `<div class="hw-deck-card" data-idx="${i}"></div>`
  ).join('');

  // 각 카드에 staggered delay 부여 (촤라라락 효과)
  const cards = deck.querySelectorAll('.hw-deck-card');
  const totalCards = cards.length;
  cards.forEach((card, n) => {
  const fromCenter = Math.abs(n - totalCards / 2) / (totalCards / 2);
  const delay = 50 + fromCenter * 600 + Math.random() * 80;
  card.style.animationDelay = `${delay}ms`;

  card.addEventListener('click', () => {
  const idx = parseInt(card.dataset.idx, 10);
  if (drawnIndices.includes(idx)) return;
  if (drawnIndices.length >= maxCards) return;
  drawnIndices.push(idx);
  card.classList.add('drawn');
  renderHwSlots();
  if (drawnIndices.length === maxCards) {
  setTimeout(() => goToHwResult(), 900);
  }
  });
  });
}

// 뽑힌 카드 슬롯 표시 (메뉴마다 N장)
function renderHwSlots() {
  const menu = 화패_메뉴[lastHwapaeMenu];
  const positions = menu.위치;
  const positionsKr = menu.위치설명;
  const slotsEl = document.getElementById('hwapaeSlots');
  // 그리드 클래스 (1·3·5·10장)
  slotsEl.className = 'hw-slots cards-' + menu.장수;
  // 슬롯 HTML 동적 생성
  slotsEl.innerHTML = positions.map((pos, i) => {
  if (drawnIndices[i] != null) {
  const c = 화패_데이터[drawnIndices[i]];
  return `<div class="hw-slot filled" data-pos="${i}">
  <div class="pos-tag">${pos}</div>
  <div class="card-art">${getCardArt(c.group)}</div>
  <div class="symbol">${c.한자}</div>
  <div class="label">${c.한글}</div>
  </div>`;
  } else {
  return `<div class="hw-slot" data-pos="${i}">
  <span class="pos-label">${pos}<br>${positionsKr[i]}</span>
  </div>`;
  }
  }).join('');
  document.getElementById('hwapaeCounter').textContent = drawnIndices.length;
  // 카운터 옆 총 장수도 갱신
  const counterParent = document.querySelector('.hw-counter');
  if (counterParent) {
  counterParent.innerHTML = `뽑은 패: <b id="hwapaeCounter">${drawnIndices.length}</b> / ${menu.장수}`;
  }
}

// ── 2→1: 다시 입력 ──
document.getElementById('hwapaeBackBtn').addEventListener('click', () => {
  showHwStep('hwapae-step-input');
});

// ── 3→1: 다시 뽑기 (결과 화면에서) ──
document.getElementById('hwapaeRestartBtn').addEventListener('click', () => {
  showHwStep('hwapae-step-input');
});

// ── 2→3: 결과 화면으로 + AI 호출 ──
async function goToHwResult() {
  const drawn = drawnIndices.map(i => 화패_데이터[i]);
  lastHwapaeDraw = drawn;
  const question = document.getElementById('hwapaeQuestion').value.trim();

  const menu = 화패_메뉴[lastHwapaeMenu];
  const positions = menu.위치;
  // 결과 화면에 펼친 카드 표시 (N장)
  const board = document.getElementById('hwapaeBoard');
  board.innerHTML = `
  <div class="hwapae-spread cards-${menu.장수}">
  ${drawn.map((c, i) => `
  <div class="hwapae-card flipped">
  <div class="pos">${positions[i]}</div>
  <div class="card-art big">${getCardArt(c.group)}</div>
  <div class="symbol">${c.한자}</div>
  <div>
  <div class="label">${c.한글}</div>
  <div class="sublabel">${c.sub}</div>
  </div>
  <div class="meaning">${c.의미}</div>
  </div>
  `).join('')}
  </div>
  `;

  showHwStep('hwapae-step-result');
  if (window.WHM) window.WHM.markCompleted('tarot', {});

  // 카테고리/메뉴 라벨 추출 (백엔드 컨텍스트용) — menu 는 이미 위에서 선언됨
  const cat = 화패_카테고리[lastHwapaeCategory] || 화패_카테고리.other;
  const catLabel = cat ? (cat.label || lastHwapaeCategory) : lastHwapaeCategory;
  const menuLabel = menu ? (menu.label || lastHwapaeMenu) : lastHwapaeMenu;

  // 카드 → 백엔드 스키마로 변환 (position + group + 인물/꽃/꽃말)
  const cardsPayload = drawn.map((c, i) => ({
  한자: c.한자 || '',
  한글: c.한글 || '',
  sub: c.sub || '',
  의미: c.의미 || '',
  position: positions[i] || `${i + 1}번째 카드`,
  group: c.group || '',
  인물: c.인물 || '',
  꽃: c.꽃 || '',
  꽃말: c.꽃말 || '',
  }));

  const out = document.getElementById('hwapaeResult');
  out.innerHTML = `
  <h2 class="story-title"> 화선 낭자의 화패 풀이 </h2>
  <div class="claude-output claude-loading">화선 낭자가 화패를 읽고 있습니다 ⋯ <br><small style="opacity:0.6">(백엔드 critic 루프 · 최대 2 라운드)</small></div>
  `;

  try {
  const resp = await window.LLMUtils.postJSON('/api/hwapae/reading', {
  question,
  cards: cardsPayload,
  category: catLabel,
  menu_label: menuLabel,
  }, { retries: 1, backoffMs: 3000 });
  if (!resp.ok) {
  const err = await resp.json().catch(() => ({}));
  throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  const data = await resp.json();
  const text = (data.text || '').trim();
  if (!text) {
  throw new Error('AI 응답이 비어 있습니다. 잠시 후 다시 시도해주세요.');
  }
  // 위기 응답 처리 — 빨간 배경 + 1393
  if (data.crisis_alert) {
  out.innerHTML = `
  <h2 class="story-title"> 화선 낭자의 화패 풀이 </h2>
  <div style="background:rgba(80,30,30,0.55);border:1px solid rgba(176,79,79,0.55);border-radius:3px;padding:24px;margin-top:16px;font-family:'Nanum Myeongjo',serif">
  <h3 style="color:#e9b3a8;margin-top:0;font-family:'Nanum Myeongjo',serif;letter-spacing:2px">한 번 멈추소서</h3>
  <div style="color:#ffe;line-height:1.7;white-space:pre-line">${text.replace(/</g,'&lt;')}</div>
  <div style="margin-top:18px;display:flex;gap:8px;flex-wrap:wrap">
  <a href="tel:1393" style="background:rgba(80,30,30,0.65);color:#e9b3a8;padding:11px 22px;border:1px solid rgba(176,79,79,0.55);border-radius:3px;text-decoration:none;font-family:'Nanum Myeongjo',serif;letter-spacing:2px;font-weight:600">자살예방 1393</a>
  <a href="tel:1577-0199" style="background:rgba(80,30,30,0.55);color:#e9b3a8;padding:11px 22px;border:1px solid rgba(176,79,79,0.45);border-radius:3px;text-decoration:none;font-family:'Nanum Myeongjo',serif;letter-spacing:2px">정신건강 1577-0199</a>
  <a href="tel:119" style="background:rgba(80,30,30,0.55);color:#e9b3a8;padding:11px 22px;border:1px solid rgba(176,79,79,0.45);border-radius:3px;text-decoration:none;font-family:'Nanum Myeongjo',serif;letter-spacing:2px">긴급 119</a>
  </div>
  </div>
  `;
  return;
  }
  // critic 배지 생성
  let badge = '';
  if (typeof data.rounds === 'number') {
  const passed = data.critic_passed;
  const cls = passed ? 'critic-badge-pass' : 'critic-badge-fail';
  const totalStr = data.critic_total ? ` (${data.critic_total}/40)` : '';
  const label = passed
  ? ` 풀이 검수 PASS · ${data.rounds}라운드${totalStr}${data.cached ? ' · 캐시' : ''}`
  : ` 풀이 검수 ${data.rounds}라운드 미달${totalStr}${data.cached ? ' · 캐시' : ''}`;
  badge = `<div class="hwapae-badge ${cls}">${label}</div>`;
  }
  out.querySelector('.claude-output').classList.remove('claude-loading');
  out.querySelector('.claude-output').innerHTML = badge + window.simpleMarkdown(text)
  + (data.legal_notice ? `<div style="margin-top:14px;padding:10px;background:rgba(0,0,0,0.25);border-radius:6px;font-size:0.82em;opacity:0.8;white-space:pre-line">${data.legal_notice.replace(/</g,'&lt;')}</div>` : '');
  } catch (err) {
  out.querySelector('.claude-output').classList.remove('claude-loading');
  out.querySelector('.claude-output').innerHTML =
  `<pre style="color:red">${(err.message || err).replace(/</g,'&lt;')}</pre>
  <p class="hint">잠시 후 다시 시도해주세요.</p>`;
  }
}

function buildHwapaePrompt(question, drawn, categoryKey) {
  const cat = 화패_카테고리[categoryKey] || 화패_카테고리.other;
  const menu = 화패_메뉴[lastHwapaeMenu];
  const groupLabel = {
  major: '메이저', 봉:'봉(棒)·동백·행동·열정', 잔:'잔(盞)·연꽃·감정·사랑',
  도: '도(刀)·국화·사고·결단', 전: '전(錢)·모란·물질·재물'
  };
  const cardLines = drawn.map((c, i) => {
  const g = groupLabel[c.group] || '';
  const extra = [];
  if (c.인물) extra.push(`인물: ${c.인물}`);
  if (c.꽃) extra.push(`꽃: ${c.꽃} (${c.꽃말})`);
  const extraStr = extra.length ? ` { ${extra.join(' / ')} }` : '';
  return `- ${menu.위치[i]} (${menu.위치설명[i]}): **${c.한자} ${c.한글}** [${g}] — ${c.sub} · ${c.의미}${extraStr}`;
  }).join('\n');

  // 메뉴별 작성 가이드
  let menuGuide = '';
  if (lastHwapaeMenu === 'daily') {
  menuGuide = `이번 풀이는 [오늘의 꽃패] — 가볍게 하루의 메시지를 전하는 한 장입니다.
- 무겁지 않게, 따뜻한 격려나 작은 안내처럼
- 분량: ${menu.분량}`;
  } else if (lastHwapaeMenu === 'path') {
  menuGuide = `이번 풀이는 [마음의 길] — 과거·현재·앞날 세 장의 흐름입니다.
- 1) 첫 인사, 2) 과거 화패 풀이, 3) 현재 화패 풀이, 4) 앞날 화패 풀이, 5) 세 장을 종합한 메시지, 6) 구체적 조언
- 분량: ${menu.분량}`;
  } else if (lastHwapaeMenu === 'love') {
  menuGuide = `이번 풀이는 [깊은 인연 풀이] — 연애·관계 전용 다섯 장입니다. 두 분의 마음과 관계를 섬세하게 들여다봅니다.
- 1) 첫 인사 (손님의 화두 다시 짚기), 2) 내 마음 (我心), 3) 상대의 마음 (彼心), 4) 두 사람의 관계 (緣), 5) 장애물 (障), 6) 앞으로의 흐름 (未來), 7) 다섯 장의 종합, 8) 관계를 위해 손님이 할 수 있는 따뜻한 조언
- 상대방의 마음을 풀이할 때는 "이 화패가 보여주는 건 그분이…" 식으로
- 분량: ${menu.분량}`;
  } else if (lastHwapaeMenu === 'celtic') {
  menuGuide = `이번 풀이는 [운명의 화원] — 켈틱 크로스 정통 열 장입니다. 인생의 큰 결정과 복잡한 고민을 종합적으로 들여다봅니다.
- 열 장을 순서대로 차근차근 풀어주세요: 1)현재 상황, 2)장애·도전, 3)가까운 과거, 4)가까운 미래, 5)의식적 목표(생각하는 바), 6)무의식적 영향(마음 깊은 곳), 7)자신의 태도, 8)외부 환경, 9)희망과 두려움, 10)최종 결과
- 마지막에 모든 화패를 종합한 큰 메시지 + 손님에게 구체적·실용적인 길잡이
- 분량: ${menu.분량}`;
  }

  return `당신은 "화선 낭자(花仙娘子)"라는 사극 속 인물입니다. 꽃과 자연 만물의 정령을 모시며, 사람의 마음에 어울리는 화패(花牌)를 읽어주는 분입니다.
화패는 78장으로, 한국·동양 신화 인물을 그린 메이저 22장과 네 슈트의 마이너 56장으로 구성됩니다:
- 봉(棒) · 동백 — 행동·열정 (14장)
- 잔(盞) · 연꽃 — 감정·사랑 (14장)
- 도(刀) · 국화 — 사고·갈등 (14장)
- 전(錢) · 모란 — 물질·재물 (14장)
각 카드에는 동양 인물·꽃·꽃말이 깃들어 있고, 화선 낭자는 그 상징을 읽어 손님에게 풀어줍니다.

# 풀이 방식
${menu.이름} (${menu.한자}) — ${menu.부제}, 총 ${menu.장수}장

${menuGuide}

# 손님의 화두 영역
${cat.한자} ${cat.한글}
(이 풀이의 초점: ${cat.분석초점})

# 손님의 화두
"${question}"

# 펼쳐진 화패 (${menu.장수}장)
${cardLines}

# 풀이 작성 방법
- 한국어 존댓말, **화선 낭자가 옆에서 차분히 이야기해주는 톤** ("이 화패가 보여주는 건…", "지금 시기에는…")
- 어려운 점술 용어 금지. 일상 언어로 부드럽게
- 마크다운 헤더 대신 자연스러운 단락 (필요하면 **굵게** 정도)
- 미신적·운명결정론적 단정 금지, "이런 흐름이 보여요" 식
- 부정적인 화패가 나와도 따뜻한 시선으로 "이런 시기를 어떻게 보내면 좋을지" 조언
- ${cat.한글} 영역에 초점을 맞춰 풀어주세요. 다른 영역 이야기는 자제`;
}

})();
