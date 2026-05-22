// 심리 테스트 — 달밤에 마주한 그대의 마음
// 12 문항 × 4지선다 × 4축 (음양 / 동정 / 인의 / 강유) → 8 유형 결과
//
// 본 시스템 ADR-006·010·014 정합:
//   · 각 문항은 검증된 심리학 학파 (Jung·Freud·Bowlby·Big Five·Schwartz·
//     Csikszentmihalyi·Kohlberg·Erikson·Batson·Hofstede·Hazan&Shaver·
//     Big Five Neuroticism) 기반
//   · 결정론 산출 — 동일 선택 동일 유형
//   · MBTI 16유형 단정 회피 (ADR-014) — 동양 4축 음양/동정/인의/강유 8유형
//   · 단정 어휘 차단 — 흐름 톤 ("결의 결·그림자")
//
// 학파 출처:
//   · Carl Jung 외향/내향 (1921 Psychological Types)
//   · John Bowlby 애착 안전기지 (1969 Attachment and Loss)
//   · Costa & McCrae 우호성/신경성 (1992 NEO-PI-R)
//   · Sigmund Freud 자아방어 (1923 Das Ich und das Es)
//   · Lawrence Kohlberg 도덕발달 (1981 Essays on Moral Development)
//   · Mihaly Csikszentmihalyi 몰입 (1990 Flow)
//   · Daniel Batson 공감-이타 (1991 The Altruism Question)
//   · Geert Hofstede 권위 거리 (1980 Culture's Consequences)
//   · Shalom Schwartz 가치관 (1992 Universals in Values)
//   · Hazan & Shaver 성인 애착 4유형 (1987 J Pers Soc Psychol)
//   · Erik Erikson 자아 통합 (1959 Identity and the Life Cycle)

export const PSYCHOTEST = {
  title: '달밤에 마주한 그대의 마음',
  subtitle: '心 · 12 문항으로 알아보는 본성',

  // 4축: 각 축에 +/- 부호로 누적
  axes: {
    yang_yin:    { plus: '陽 (밝음)', minus: '陰 (그늘)' },
    dong_jeong:  { plus: '動 (움직임)', minus: '靜 (고요)' },
    in_ui:       { plus: '仁 (마음)', minus: '義 (이치)' },
    gang_yu:     { plus: '剛 (굳셈)', minus: '柔 (부드러움)' },
  },

  questions: [
    {
      // 학파: Jung 외향(E)/내향(I) — Psychological Types (1921)
      q: '달이 가장 밝은 밤, 그대가 머무는 곳은?',
      school: 'Jung (1921) 외향/내향',
      choices: [
        { text: '벗들과 둘러앉아 술잔을 기울이며 시를 짓는다',  s: { yang_yin: +2, dong_jeong: +1, in_ui: +1 } },
        { text: '홀로 정자에 올라 달을 바라보며 거문고를 켠다', s: { yang_yin: -2, dong_jeong: -1, in_ui: -1 } },
        { text: '서책 한 권 들고 등불 곁에 앉아 고요히 읽는다', s: { yang_yin: -1, dong_jeong: -2 } },
        { text: '말을 타고 달빛 아래 들판을 가로지른다',         s: { yang_yin: +1, dong_jeong: +2, gang_yu: +1 } },
      ],
    },
    {
      // 학파: Bowlby 애착 — 안전기지 vs 경계 (1969 Attachment and Loss)
      q: '낯선 길손이 그대의 사립문을 두드린다.',
      school: 'Bowlby (1969) 애착 이론',
      choices: [
        { text: '문을 활짝 열고 따뜻한 국밥 한 그릇을 권한다',     s: { in_ui: +2, yang_yin: +1 } },
        { text: '먼저 그가 누구인지 까닭을 묻고 살핀다',           s: { in_ui: -1, gang_yu: +1 } },
        { text: '문틈으로만 살피고 도움 줄 만한 다른 곳을 일러준다', s: { in_ui: +1, dong_jeong: -1, yang_yin: -1 } },
        { text: '아예 응대하지 않고 조용히 안으로 들어간다',       s: { in_ui: -2, yang_yin: -1, gang_yu: -1 } },
      ],
    },
    {
      // 학파: Big Five 우호성(A) — Costa & McCrae (1992) NEO-PI-R
      q: '저잣거리에서 다툼이 일었다. 그대는?',
      school: 'Big Five 우호성 (Costa & McCrae 1992)',
      choices: [
        { text: '소매를 걷고 사이에 끼어들어 옳고 그름을 가른다',   s: { dong_jeong: +2, gang_yu: +2, in_ui: -1 } },
        { text: '먼저 말려 두 사람의 화부터 가라앉히려 든다',       s: { dong_jeong: +1, in_ui: +2 } },
        { text: '멀찍이 서서 형국을 살핀 뒤 조용히 자리를 뜬다',   s: { dong_jeong: -2, gang_yu: -1 } },
        { text: '주변 사람에게 누가 옳은지 의견을 묻고 따른다',     s: { dong_jeong: -1, gang_yu: -2 } },
      ],
    },
    {
      // 학파: Freud 자아방어 (1923 Das Ich und das Es)
      q: '꿈에 호랑이가 나타나 길을 막는다. 그대는?',
      school: 'Freud (1923) 자아방어 기제',
      choices: [
        { text: '눈을 똑바로 쳐다보고 한 걸음 나선다',                s: { gang_yu: +2, yang_yin: +1, dong_jeong: +1 } },
        { text: '몸을 낮추고 천천히 옆길로 비켜선다',                 s: { gang_yu: -2, dong_jeong: -1 } },
        { text: '먹을 것을 내어 호랑이의 노여움을 풀어보려 한다',     s: { in_ui: +2, gang_yu: -1 } },
        { text: '잠시 멈춰 호랑이가 무엇을 원하는지 그 결을 헤아린다', s: { dong_jeong: -2, in_ui: -1 } },
      ],
    },
    {
      // 학파: Kohlberg 도덕발달 6단계 (1981 Essays on Moral Development)
      q: '벗이 큰 죄를 짓고 그대에게 숨겨달라 청한다.',
      school: 'Kohlberg (1981) 도덕발달 단계',
      choices: [
        { text: '의리는 의리, 한 끼 재워 보내준다',                  s: { in_ui: +2, gang_yu: -1 } },
        { text: '벗이라도 옳지 않다 일러 관아로 향한다',              s: { in_ui: -2, gang_yu: +2 } },
        { text: '벗에게 직접 자수하라 권하고 끝까지 곁에 선다',       s: { in_ui: +1, gang_yu: +1, yang_yin: -1 } },
        { text: '도와주지도 신고하지도 않고 조용히 거리를 둔다',      s: { in_ui: -1, dong_jeong: -2, gang_yu: -2 } },
      ],
    },
    {
      // 학파: Csikszentmihalyi 몰입 (1990 Flow)
      q: '한적한 산속 절에서 하룻밤, 그대가 가장 먼저 하는 일은?',
      school: 'Csikszentmihalyi (1990) Flow',
      choices: [
        { text: '스님과 차를 나누며 세상 이야기를 듣는다',           s: { yang_yin: +1, in_ui: +1, dong_jeong: +1 } },
        { text: '법당에 들어 오롯이 정좌하여 마음을 비운다',         s: { yang_yin: -2, dong_jeong: -2 } },
        { text: '산길을 한 바퀴 돌며 새소리·바람결을 듣는다',         s: { yang_yin: -1, dong_jeong: +1, gang_yu: -1 } },
        { text: '필묵을 꺼내 마음에 떠오르는 한 구절을 적는다',       s: { yang_yin: -1, dong_jeong: -1, in_ui: -1 } },
      ],
    },
    {
      // 학파: Big Five 신경성(N) — Costa & McCrae (1992)
      q: '관아의 부름이 닿았다. 그대의 마음은?',
      school: 'Big Five 신경성 (Costa & McCrae 1992)',
      choices: [
        { text: '두근거리며 의관을 정제하고 길을 나선다',             s: { dong_jeong: +2, yang_yin: +1 } },
        { text: '무슨 일인지 먼저 헤아리고 가벼이 움직이지 않는다',   s: { dong_jeong: -2, in_ui: -1, gang_yu: +1 } },
        { text: '걱정이 앞서나 표내지 않고 마음을 다잡고 나선다',     s: { dong_jeong: +1, gang_yu: +1, yang_yin: -1 } },
        { text: '두려움이 일어 손이 떨리나 그래도 가야 한다',         s: { dong_jeong: -1, gang_yu: -2, yang_yin: -2 } },
      ],
    },
    {
      // 학파: Batson 공감-이타 가설 (1991 The Altruism Question)
      q: '시장에서 어린아이가 우물에 빠질 뻔한 순간.',
      school: 'Batson (1991) 공감-이타 가설',
      choices: [
        { text: '셈할 새 없이 손부터 뻗는다',                          s: { in_ui: +2, dong_jeong: +2, gang_yu: +1 } },
        { text: '소리쳐 주위 사람을 부르고 함께 막는다',                s: { in_ui: +1, dong_jeong: +1, yang_yin: +1 } },
        { text: '주위를 보고 가장 가까운 어른을 부른다',                s: { dong_jeong: -1, gang_yu: -1, in_ui: -1 } },
        { text: '굳어서 잠시 멈춘 뒤 정신 차리고 다가간다',             s: { in_ui: 0, dong_jeong: -2, yang_yin: -2 } },
      ],
    },
    {
      // 학파: Hofstede 권위 거리 (1980 Culture's Consequences)
      q: '그대의 부모님이 그릇된 결정을 내리려 한다.',
      school: 'Hofstede (1980) 권위 거리 차원',
      choices: [
        { text: '예를 갖춰 따르되 마음으로는 깊이 한숨짓는다',        s: { gang_yu: -2, in_ui: +1, yang_yin: -1 } },
        { text: '간곡히 말씀드리고 끝까지 뜻을 굽히지 않는다',        s: { gang_yu: +2, in_ui: -1, dong_jeong: +1 } },
        { text: '먼저 다른 가족과 의논해 함께 말씀드린다',            s: { gang_yu: 0, in_ui: +2, dong_jeong: +1 } },
        { text: '시간이 지나면 자연스레 결이 풀린다 보고 기다린다',  s: { gang_yu: -1, dong_jeong: -2, yang_yin: -1 } },
      ],
    },
    {
      // 학파: Schwartz 인생 가치관 10 차원 (1992 Universals in Values)
      q: '큰 재물이 굴러들어왔다. 그대는?',
      school: 'Schwartz (1992) 인생 가치관',
      choices: [
        { text: '이웃과 곳간을 나눠 잔치를 연다',                     s: { yang_yin: +2, in_ui: +2 } },
        { text: '훗날을 생각해 깊이 갈무리한다',                       s: { yang_yin: -1, gang_yu: +1, dong_jeong: -1 } },
        { text: '책과 학문에 투자해 결실을 길게 본다',                  s: { yang_yin: -1, in_ui: -1, gang_yu: 0 } },
        { text: '어려운 이웃에게 조용히 나누고 이름을 남기지 않는다',   s: { yang_yin: -2, in_ui: +2 } },
      ],
    },
    {
      // 학파: Hazan & Shaver 성인 애착 4유형 (1987 J Pers Soc Psychol)
      q: '오랜 정인이 떠나간다고 한다. 그대는?',
      school: 'Hazan & Shaver (1987) 성인 애착 4유형',
      choices: [
        { text: '울며 매달려 한 번만 더 머물러달라 청한다',           s: { yang_yin: +1, gang_yu: -2, in_ui: +2 } },
        { text: '아무 말 없이 짐을 싸 주고 그저 절을 한다',             s: { yang_yin: -2, gang_yu: +2, in_ui: -1 } },
        { text: '한 번 깊이 마주 앉아 마음을 다 말한 뒤 보내준다',    s: { yang_yin: 0, gang_yu: +1, in_ui: +1 } },
        { text: '담담히 받아들이는 듯 보이나 혼자 있는 밤이면 무너진다', s: { yang_yin: -2, gang_yu: -1, in_ui: 0 } },
      ],
    },
    {
      // 학파: Erikson 자아 통합 vs 절망 (1959 Identity and the Life Cycle)
      q: '마지막 묻겠소. 그대는 무엇을 좇으며 살아왔는가?',
      school: 'Erikson (1959) 자아 통합',
      choices: [
        { text: '사람과 정 — 곁에 누군가가 있으면 그것으로 족하다',   s: { yang_yin: +2, in_ui: +2 } },
        { text: '뜻과 도리 — 옳음을 잃으면 살아도 죽은 것이다',       s: { yang_yin: -1, in_ui: -2, gang_yu: +2 } },
        { text: '깊이와 사색 — 답하지 못해도 묻기를 멈추지 않았다',   s: { yang_yin: -2, dong_jeong: -2, in_ui: -1 } },
        { text: '걸음과 자취 — 무엇이든 시도하고 부딪쳐 살아왔다',     s: { yang_yin: +1, dong_jeong: +2, gang_yu: +1 } },
      ],
    },
  ],

  // 결과 유형 — 4축의 부호 조합 (음양·강유·인의 기준)
  // 8 유형: 陽剛·陽柔·陰剛·陰柔 × 仁/義 = 8
  // ADR-014 정합 — MBTI 16유형 단정 회피, 동양 8 분류 흐름 톤
  types: {
    'yang_gang_in':  {
      title: '천하의 협객 (陽剛仁)',
      subtitle: '햇살 같은 의기, 뜨거운 마음',
      body: '그대는 한낮의 햇살을 닮았다. 강하고 곧되 따스하며, 약한 자를 보면 먼저 손을 내미는 사람.\n무리 가운데 있어도 늘 앞장서며, 의를 본 즉 망설이지 않는다.\n\n다만 너무 뜨거워 자신을 태우기 쉬우니, 때로 한 발 물러서 달빛 아래 숨을 고르라.',
    },
    'yang_gang_ui': {
      title: '곧은 칼 (陽剛義)',
      subtitle: '햇빛 아래 푸르게 빛나는 칼날',
      body: '그대는 옳고 그름을 가르는 데 엄정하다.\n사람보다 도리를, 정보다 이치를 먼저 본다.\n그래서 더러 차갑다 오해받으나, 사실은 세상을 곧게 세우려는 의로움이다.\n\n다만 가까운 이들의 약함도 헤아릴 줄 알아야 진짜 어른이 된다.',
    },
    'yang_yu_in': {
      title: '봄바람 같은 이 (陽柔仁)',
      subtitle: '햇살에 풀어지는 봄눈',
      body: '그대 곁에 있으면 사람들이 마음을 연다.\n부드러우나 환하고, 다정하나 가볍지 않다.\n무리에 활기를 더하는 사람, 모두가 함께 있고 싶어 하는 사람.\n\n다만 모두를 안으려다 그대 자신이 비어버릴 수 있으니, 가끔은 "싫다" 한 마디도 익혀두라.',
    },
    'yang_yu_ui': {
      title: '미소짓는 책사 (陽柔義)',
      subtitle: '겉은 부드러우나 속은 명료한 사람',
      body: '그대는 웃는 얼굴로 사람을 대하나, 내면에는 흔들리지 않는 잣대가 있다.\n경솔히 휘둘리지 않고, 자기 길을 알며 그 길에서 벗어나지 않는다.\n\n다만 그 명료함을 누구에게도 보이지 않으면 외로움이 따르니, 신뢰하는 한 사람에게는 솔직히 풀어놓아라.',
    },
    'yin_gang_in': {
      title: '달빛 아래 의인 (陰剛仁)',
      subtitle: '말없이 약자의 곁에 서는 사람',
      body: '그대는 떠들지 않는다. 그러나 결정적인 순간, 가장 굳건히 서 있는 이는 그대다.\n외롭게 행하되 한 번 마음을 두면 끝까지 지킨다.\n\n다만 안에 너무 많은 것을 담아 두니 가끔은 흘려보내야 한다. 강함도 쉬어야 강함이 된다.',
    },
    'yin_gang_ui': {
      title: '서릿발 같은 선비 (陰剛義)',
      subtitle: '깊은 밤의 칼날, 흔들림 없는 도리',
      body: '그대는 자신에게 가장 엄정한 사람이다.\n남이 보든 보지 않든 어긋난 일은 하지 않는다.\n그 곧음이 더러 사람을 외롭게 하나, 시대가 어두울수록 그대 같은 이가 빛난다.\n\n다만 자신에게 베푼 만큼의 자비를 남에게도 베풀어야 한다.',
    },
    'yin_yu_in': {
      title: '고요한 옹달샘 (陰柔仁)',
      subtitle: '그늘에 머무르며 깊은 정을 길어 올리는 이',
      body: '그대는 부산스럽지 않다. 조용히 곁에 있어 주는 것만으로 사람의 슬픔이 가벼워진다.\n섬세하고 다정하며, 작은 신호도 놓치지 않는다.\n\n다만 모두의 짐을 혼자 들지 마라. 그대도 누군가에게 기댈 권리가 있다.',
    },
    'yin_yu_ui': {
      title: '깊은 산속 거문고 (陰柔義)',
      subtitle: '말 없되 내면이 가지런한 사람',
      body: '그대는 좀처럼 자신을 드러내지 않는다.\n그러나 한 번 가까이 다가가본 사람은 안다 — 그 안에 단단하고 맑은 가락이 흐른다는 것을.\n자기 길을 알고, 무리에 휩쓸리지 않는다.\n\n다만 그대의 거문고를 가끔은 들려주어도 좋다. 누군가는 그 소리를 평생 그리워할지도 모른다.',
    },
  },
};

// 점수 → 유형 키 산출
export function resolvePsychoType(scores) {
  const yangYin = scores.yang_yin >= 0 ? 'yang' : 'yin';
  const gangYu  = scores.gang_yu  >= 0 ? 'gang' : 'yu';
  const inUi    = scores.in_ui    >= 0 ? 'in'   : 'ui';
  return `${yangYin}_${gangYu}_${inUi}`;
}
