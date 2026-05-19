// ============================================================
// 사주 + 해몽 핵심 엔진 — ADR-043 외부 모듈화
// ============================================================
// SECTION 1: 데이터 상수 (천간·지지·오행·십성·12운성·12신살)
// SECTION 2: 천문 계산 (Meeus AA — JD·태양 경도·equation of time)
// SECTION 3: 사주 4기둥 (dayPillarIndex·calculateSaju)
// SECTION 4: 분석 엔진 (analyzeSaju·gzIdx·getSipsung·get12Unseong·get12Shinsal)
// SECTION 5: 대운·세운
// SECTION 6: 룰셋 해석 데이터 (해석_일간·해석_십성·해석_격국·해석_12운성·해석_12신살)
// SECTION 7: AI prompt (buildSajuPrompt·buildDreamPrompt) + simpleMarkdown
//
// 본 파일의 모든 함수·const는 같은 <script src> 로드 후 글로벌 스코프 노출.
// window.SAJU 통합 export는 index.html 인라인 부분에서 유지.
// ============================================================
'use strict';

// ============================================================
// SECTION 1: 데이터 상수 — 천간/지지/오행/십성 등
// ============================================================

const 천간  = ['갑','을','병','정','무','기','경','신','임','계'];
const 천간_한자 = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const 지지  = ['자','축','인','묘','진','사','오','미','신','유','술','해'];
const 지지_한자 = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];

// 오행: 0=목 1=화 2=토 3=금 4=수
const 천간_오행 = [0,0, 1,1, 2,2, 3,3, 4,4]; // 갑을 병정 무기 경신 임계
const 지지_오행 = [4,2, 0,0,2, 1,1,2, 3,3,2, 4]; // 자축 인묘진 사오미 신유술 해

// 음양: 0=양 1=음
const 천간_음양 = [0,1, 0,1, 0,1, 0,1, 0,1];
const 지지_음양 = [0,1, 0,1, 0,1, 0,1, 0,1, 0,1];

const 오행명  = ['목','화','토','금','수'];
const 오행_한자  = ['木','火','土','金','水'];
const 오행_색깔  = ['o-목','o-화','o-토','o-금','o-수'];

// 지지 장간 [여기, 중기, 정기] — 천간 인덱스. -1은 없음.
// 출처: 자평진전(子平眞詮) / 한국 표준 만세력
const 지지_장간 = [
  // 자(子): 임 / -, 계
  { 여기: 8, 중기: -1, 정기: 9, 일수: [10, 0, 20] },
  // 축(丑): 계 9일, 신 3일, 기 18일
  { 여기: 9, 중기: 7, 정기: 5, 일수: [9, 3, 18] },
  // 인(寅): 무 7일, 병 7일, 갑 16일
  { 여기: 4, 중기: 2, 정기: 0, 일수: [7, 7, 16] },
  // 묘(卯): 갑 10일, -, 을 20일
  { 여기: 0, 중기: -1, 정기: 1, 일수: [10, 0, 20] },
  // 진(辰): 을 9일, 계 3일, 무 18일
  { 여기: 1, 중기: 9, 정기: 4, 일수: [9, 3, 18] },
  // 사(巳): 무 7일, 경 7일, 병 16일
  { 여기: 4, 중기: 6, 정기: 2, 일수: [7, 7, 16] },
  // 오(午): 병 10일, 기 9일, 정 11일
  { 여기: 2, 중기: 5, 정기: 3, 일수: [10, 9, 11] },
  // 미(未): 정 9일, 을 3일, 기 18일
  { 여기: 3, 중기: 1, 정기: 5, 일수: [9, 3, 18] },
  // 신(申): 무 7일, 임 7일, 경 16일
  { 여기: 4, 중기: 8, 정기: 6, 일수: [7, 7, 16] },
  // 유(酉): 경 10일, -, 신 20일
  { 여기: 6, 중기: -1, 정기: 7, 일수: [10, 0, 20] },
  // 술(戌): 신 9일, 정 3일, 무 18일
  { 여기: 7, 중기: 3, 정기: 4, 일수: [9, 3, 18] },
  // 해(亥): 무 7일, 갑 5일, 임 18일
  { 여기: 4, 중기: 0, 정기: 8, 일수: [7, 5, 18] },
];

// 12절 (월 경계용) 황경 — 사주 월주는 12절기 기준
//  인월=입춘(315°), 묘월=경칩(345°), 진월=청명(15°), 사월=입하(45°),
//  오월=망종(75°), 미월=소서(105°), 신월=입추(135°), 유월=백로(165°),
//  술월=한로(195°), 해월=입동(225°), 자월=대설(255°), 축월=소한(285°)
const 절_정보 = [
  { 명: '입춘', 황경: 315, 월지: 2  }, // 인월
  { 명: '경칩', 황경: 345, 월지: 3  }, // 묘월
  { 명: '청명', 황경:  15, 월지: 4  }, // 진월
  { 명: '입하', 황경:  45, 월지: 5  }, // 사월
  { 명: '망종', 황경:  75, 월지: 6  }, // 오월
  { 명: '소서', 황경: 105, 월지: 7  }, // 미월
  { 명: '입추', 황경: 135, 월지: 8  }, // 신월
  { 명: '백로', 황경: 165, 월지: 9  }, // 유월
  { 명: '한로', 황경: 195, 월지: 10 }, // 술월
  { 명: '입동', 황경: 225, 월지: 11 }, // 해월
  { 명: '대설', 황경: 255, 월지: 0  }, // 자월
  { 명: '소한', 황경: 285, 월지: 1  }, // 축월
];

// 24절기 (12절 + 12중기, 황경 15°씩) — 절기 표시용
const 절기_24 = [
  '춘분','청명','곡우','입하','소만','망종','하지','소서','대서','입추','처서','백로',
  '추분','한로','상강','입동','소설','대설','동지','소한','대한','입춘','우수','경칩'
];

// 오호둔(五虎遁): 년간(0-9) → 인월(첫 월)의 천간 인덱스
//  갑기년 → 병인월, 을경년 → 무인월, 병신년 → 경인월,
//  정임년 → 임인월, 무계년 → 갑인월
const 오호둔 = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0];

// 오서둔(五鼠遁): 일간(0-9) → 자시(첫 시)의 천간 인덱스
//  갑기일 → 갑자시, 을경일 → 병자시, 병신일 → 무자시,
//  정임일 → 경자시, 무계일 → 임자시
const 오서둔 = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8];

// 십성명 (일간 기준, 음양 같으면 +0, 다르면 +1)
//  0:비견 1:겁재 2:식신 3:상관 4:편재 5:정재 6:편관 7:정관 8:편인 9:정인
const 십성명 = ['비견','겁재','식신','상관','편재','정재','편관','정관','편인','정인'];

// 12운성: 일간별 장생지 (지지 인덱스) + 순/역행
//  양간(갑병무경임): 장생부터 순행
//  음간(을정기신계): 장생부터 역행
const 십이운성_장생 = {
  0: { 지지: 11, 순행: true  }, // 갑(목양) → 해 장생
  1: { 지지:  6, 순행: false }, // 을(목음) → 오 장생
  2: { 지지:  2, 순행: true  }, // 병(화양) → 인 장생
  3: { 지지:  9, 순행: false }, // 정(화음) → 유 장생
  4: { 지지:  2, 순행: true  }, // 무(토양) → 인 장생 (병화 따라감)
  5: { 지지:  9, 순행: false }, // 기(토음) → 유 장생 (정화 따라감)
  6: { 지지:  5, 순행: true  }, // 경(금양) → 사 장생
  7: { 지지:  0, 순행: false }, // 신(금음) → 자 장생
  8: { 지지:  8, 순행: true  }, // 임(수양) → 신 장생
  9: { 지지:  3, 순행: false }, // 계(수음) → 묘 장생
};
const 십이운성명 = ['장생','목욕','관대','건록','제왕','쇠','병','사','묘','절','태','양'];

// 십이신살명 (삼합국 기준 시작점)
const 십이신살명 = ['겁살','재살','천살','지살','년살','월살','망신','장성','반안','역마','육해','화개'];
// 삼합국별 겁살 시작 지지: 신자진→사, 인오술→해, 사유축→인, 해묘미→신
const 십이신살_시작 = {
  8: 5, 0: 5, 4: 5,  // 신자진 수국 → 겁살=사
  2:11, 6:11,10:11,  // 인오술 화국 → 겁살=해
  5: 2, 9: 2, 1: 2,  // 사유축 금국 → 겁살=인
 11: 8, 3: 8, 7: 8,  // 해묘미 목국 → 겁살=신
};

// 60갑자 일주 기준일
// 검증값: 2024-01-01 (KST) = 신축일(辛丑, 인덱스 37)
// (검증: 신=7, 축=1 → 60갑자에서 i%10=7 & i%12=1 → i=37 )
const 일주_기준_JD_정오 = null; // 동적 계산 (아래 함수에서)

// ============================================================
// SECTION 2: 천문 계산 (Meeus Astronomical Algorithms)
// ============================================================

const DEG = Math.PI / 180;
const RAD = 180 / Math.PI;
const toRad = d => d * DEG;
const toDeg = r => r * RAD;
const norm360 = d => ((d % 360) + 360) % 360;

/**
 * 그레고리력 → 율리우스 일자 (Julian Date, UT 기준)
 * Meeus chapter 7
 */
function toJD(year, month, day, hour = 0, min = 0, sec = 0) {
  let y = year, m = month;
  if (m <= 2) { y -= 1; m += 12; }
  const A = Math.floor(y / 100);
  const B = 2 - A + Math.floor(A / 4); // 그레고리력 보정
  const JD0 = Math.floor(365.25 * (y + 4716))
  + Math.floor(30.6001 * (m + 1))
  + day + B - 1524.5;
  return JD0 + (hour + min / 60 + sec / 3600) / 24;
}

/**
 * 현지 시각 → UT 기준 JD
 * tzOffsetHours: 현지 시각의 timezone (예: KST=9)
 */
function jdFromLocal(y, mo, d, h, mi, s, tzOffsetHours) {
  // 현지 0시 0분 0초의 JD에서 (현지시간 - tz) / 24 만큼 더함
  return toJD(y, mo, d, 0, 0, 0) + (h - tzOffsetHours + mi / 60 + s / 3600) / 24;
}

/**
 * 율리우스 일자 → 그레고리력 [year, month, day, hour, min, sec]
 * Meeus chapter 7
 */
function fromJD(JD) {
  const JD2 = JD + 0.5;
  const Z = Math.floor(JD2);
  const F = JD2 - Z;
  let A;
  if (Z < 2299161) { A = Z; }
  else {
  const alpha = Math.floor((Z - 1867216.25) / 36524.25);
  A = Z + 1 + alpha - Math.floor(alpha / 4);
  }
  const B = A + 1524;
  const C = Math.floor((B - 122.1) / 365.25);
  const D = Math.floor(365.25 * C);
  const E = Math.floor((B - D) / 30.6001);
  const day = B - D - Math.floor(30.6001 * E) + F;
  const month = E < 14 ? E - 1 : E - 13;
  const year = month > 2 ? C - 4716 : C - 4715;
  const dayInt = Math.floor(day);
  const frac = (day - dayInt) * 24;
  const hour = Math.floor(frac);
  const minFrac = (frac - hour) * 60;
  const min = Math.floor(minFrac);
  const sec = (minFrac - min) * 60;
  return [year, month, dayInt, hour, min, sec];
}

/**
 * UT JD → 현지 시각 [year, month, day, hour, min, sec]
 */
function localFromJD(JD, tzOffsetHours) {
  return fromJD(JD + tzOffsetHours / 24);
}

/**
 * 태양의 겉보기 황경 (도) — Meeus chapter 25
 * 정밀도: 약 0.01° (~24"), 24절기 시각 결정에 충분.
 */
function sunApparentLongitude(JD) {
  const T = (JD - 2451545.0) / 36525.0;
  // 태양 평균 황경 L0
  const L0 = norm360(280.46646 + 36000.76983 * T + 0.0003032 * T * T);
  // 태양 평균 근점이각 M
  const M = norm360(357.52911 + 35999.05029 * T - 0.0001537 * T * T);
  const Mrad = toRad(M);
  // 중심방정식 C
  const C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(Mrad)
  + (0.019993 - 0.000101 * T)  * Math.sin(2 * Mrad)
  +  0.000289  * Math.sin(3 * Mrad);
  // 진황경
  const trueL = L0 + C;
  // 겉보기 황경 (장동·광행차 보정)
  const omega = 125.04 - 1934.136 * T;
  const lambda = trueL - 0.00569 - 0.00478 * Math.sin(toRad(omega));
  return norm360(lambda);
}

/**
 * 황도 경사각 (도) — Meeus 22.2 평균값
 */
function obliquity(T) {
  return 23 + 26/60 + 21.448/3600
  - (46.8150/3600) * T
  - (0.00059/3600) * T * T
  + (0.001813/3600) * T * T * T;
}

/**
 * 균시차 (분 단위) — Meeus chapter 28
 * 진태양시 = 평균태양시 + 균시차
 * 양수: 진태양이 평균태양보다 동쪽(빠름)
 */
function equationOfTime(JD) {
  const T = (JD - 2451545.0) / 36525.0;
  const epsilon = obliquity(T);
  const L0 = norm360(280.46646 + 36000.76983 * T + 0.0003032 * T * T);
  const e  = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T;
  const M  = norm360(357.52911 + 35999.05029 * T - 0.0001537 * T * T);
  const y  = Math.tan(toRad(epsilon) / 2) ** 2;
  const EoT_rad = y * Math.sin(2 * toRad(L0))
  - 2 * e * Math.sin(toRad(M))
  + 4 * e * y * Math.sin(toRad(M)) * Math.cos(2 * toRad(L0))
  - 0.5 * y * y * Math.sin(4 * toRad(L0))
  - 1.25 * e * e * Math.sin(2 * toRad(M));
  return toDeg(EoT_rad) * 4; // 분
}

/**
 * 태양 황경이 targetLon (도)에 도달하는 시각 (UT JD)
 * 뉴턴 반복법으로 정밀화. nearJD 부근에서 검색.
 */
function findSunLongitudeJD(targetLon, nearJD) {
  let JD = nearJD;
  // 8회 반복: 0.9856°/day 평균 공전 속도 사용
  for (let i = 0; i < 12; i++) {
  const lon = sunApparentLongitude(JD);
  let diff = targetLon - lon;
  if (diff > 180)  diff -= 360;
  if (diff < -180) diff += 360;
  if (Math.abs(diff) < 1e-9) break;
  JD += diff / 0.9856473;
  }
  return JD;
}

/**
 * 특정 사주 연도(입춘 ~ 다음해 입춘)의 12절 시각 목록
 * @returns [{명, 황경, 월지, JD}, ...] (입춘부터 소한까지)
 */
function calcSolarTerms(sajuYear) {
  // 입춘은 양력 2월 4일 근처 → 1월 30일 + 황경 변환
  // 단순화: 절기마다 1월 1일부터의 대략적 일수를 추정한 후 뉴턴 반복
  // 황경 0°(춘분)는 약 3월 20-21일 (= year-1-1로부터 약 79일)
  // 황경 X° → year-1-1로부터 약 (X * 365.25 / 360 + 79) 일 (보정 필요)
  // 더 안전: 1월 1일 UT + (대략 일수)로 시작 → 뉴턴 반복

  // 입춘부터 시작 (sajuYear의 입춘)
  // sajuYear의 입춘은 sajuYear년 2월 초
  // 소한은 sajuYear+1년 1월 초
  const out = [];
  for (let i = 0; i < 12; i++) {
  const info = 절_정보[i];
  // 절기가 sajuYear에 있는 절: 입춘(i=0)부터 대설(i=10)까지
  // 소한(i=11)은 sajuYear+1에 있음
  const calYear = (i === 11) ? sajuYear + 1 : sajuYear;
  // 초기 추정: calYear-1-1 + (황경 × 365.25 / 360 + offset)
  // 황경 0(춘분) → 약 3월 20일 → day ~79
  let approxDay = (info.황경 * 365.25 / 360) + 79;
  if (approxDay > 365) approxDay -= 365.25;
  const nearJD = toJD(calYear, 1, 1, 0, 0, 0) + approxDay;
  const exactJD = findSunLongitudeJD(info.황경, nearJD);
  out.push({ 명: info.명, 황경: info.황경, 월지: info.월지, JD: exactJD });
  }
  return out;
}

// ============================================================
// SECTION 3: 사주 4기둥 계산
// ============================================================

/**
 * 일주 60갑자 인덱스 계산
 * 기준: 2024-01-01 KST 정오 = 신축일(인덱스 37)
 *  - 검증: 신축 = 천간 신(7) + 지지 축(1)
 *  - 60갑자 인덱스 i: i%10=7, i%12=1 → i=37
 *
 * @param {number} targetJD - 대상일의 KST 정오 JD (정수 일자 결정용)
 */
function dayPillarIndex(targetJD, tzOffsetHours = 9) {
  const baseJD = jdFromLocal(2024, 1, 1, 12, 0, 0, tzOffsetHours);
  const baseGZ = 37; // 신축
  const diff = Math.round(targetJD - baseJD);
  return ((baseGZ + diff) % 60 + 60) % 60;
}

/**
 * 메인 사주 계산
 *
 * @param {object} input
 *  year, month, day, hour, minute: 출생 시각 (현지 시각)
 *  timezoneOffset: 시간대 (KST=9)
 *  longitude: 출생지 동경(°)
 *  useTrueSolar: 진태양시 보정 여부 (boolean)
 *  ziShiOption: 'late' | 'early' | 'midnight'
 *  gender: 'M' | 'F'
 */
function calculateSaju(input) {
  const {
  year, month, day,
  hour, minute = 0,
  timezoneOffset = 9,
  longitude = 126.978,
  useTrueSolar = true,
  ziShiOption = 'late',
  gender = 'M',
  } = input;

  // 1. 입력 시각을 UT JD로 변환 (시민력)
  const civilJD = jdFromLocal(year, month, day, hour, minute, 0, timezoneOffset);

  // 2. 진태양시 보정
  let solarJD = civilJD;
  let eotMinutes = 0;
  let longCorrectionMinutes = 0;
  if (useTrueSolar) {
  const stdLongitude = timezoneOffset * 15; // 표준시 자오선
  longCorrectionMinutes = (longitude - stdLongitude) * 4; // 분
  eotMinutes = equationOfTime(civilJD);
  solarJD = civilJD + (longCorrectionMinutes + eotMinutes) / (60 * 24);
  }

  // 3. 사주 연도 결정 (입춘 기준)
  //  solarJD < (해당 연도 입춘 JD) 이면 전년도로 간주
  let sajuYear = year;
  // sajuYear의 입춘 시각 — 단순 추정 (2월 4일경)
  const lichunNearJD = toJD(year, 2, 4, 0, 0, 0);
  const lichunJD = findSunLongitudeJD(315, lichunNearJD);
  if (solarJD < lichunJD) sajuYear -= 1;

  // 4. 12절 경계 계산 (사주 연도 기준)
  const boundaries = calcSolarTerms(sajuYear);

  // 5. 년주 (사주연도 60갑자)
  //  1984년 = 갑자년 (인덱스 0) → (sajuYear - 1984) mod 60
  //  또는 표준식: (sajuYear - 4) mod 60 (서기 4년이 갑자)
  const yearGZ = ((sajuYear - 4) % 60 + 60) % 60;
  const yearStem = yearGZ % 10;
  const yearBranch = yearGZ % 12;

  // 6. 월주
  //  boundaries[i].JD ≤ solarJD < boundaries[i+1].JD 인 i를 찾음
  let monthIdx = 11; // 기본: 마지막 절(소한) 이후
  for (let i = 11; i >= 0; i--) {
  if (solarJD >= boundaries[i].JD) { monthIdx = i; break; }
  }
  // monthIdx=0이면 인월, 1이면 묘월, ..., 11이면 축월
  const monthBranch = 절_정보[monthIdx].월지;
  // 인월 천간(오호둔) + monthIdx
  const monthStem = (오호둔[yearStem] + monthIdx) % 10;
  const monthGZ = monthStem + monthBranch * 10; // 표기용 (60갑자 인덱스는 별도 계산 필요)

  // 7. 일주
  //  일자는 출생일의 KST 정오 JD를 기준으로 결정 (자정 부근 정확도 ↑)
  const dayNoonJD = jdFromLocal(year, month, day, 12, 0, 0, timezoneOffset);
  const baseDayIdx = dayPillarIndex(dayNoonJD, timezoneOffset);

  // 자시 처리 옵션
  let dayPillarOffset = 0;  // 0: 당일, 1: 다음날 일주
  let timeStemFromNextDay = false;  // 시주 천간 산출 시 다음날 일간 사용?
  if (hour >= 23) {
  if (ziShiOption === 'late') {
  // 야자시법: 일주는 당일, 시주 천간은 다음날 일간 기준
  dayPillarOffset = 0;
  timeStemFromNextDay = true;
  } else if (ziShiOption === 'early') {
  // 명자시법: 일주는 다음날, 시주 천간도 다음날 일간 기준
  dayPillarOffset = 1;
  timeStemFromNextDay = true;
  } else { // midnight
  // 자정 기준: 일주 당일, 시주도 당일 일간 기준
  }
  }
  const dayGZ = ((baseDayIdx + dayPillarOffset) % 60 + 60) % 60;
  const dayStem = dayGZ % 10;
  const dayBranch = dayGZ % 12;

  // 8. 시주
  //  시지: 23-01=자(0), 01-03=축(1), ..., 21-23=해(11)
  //  한국식에서는 진태양시 적용된 시각으로 시지 결정
  //  (사주 학파에 따라 시민력 시각을 그대로 쓰기도 함 — 옵션화 가능)
  const solarLocal = localFromJD(solarJD, timezoneOffset);
  const solarHour = solarLocal[3] + solarLocal[4] / 60 + solarLocal[5] / 3600;
  let timeBranch;
  if (solarHour >= 23 || solarHour < 1) timeBranch = 0;  // 자시
  else timeBranch = Math.floor((solarHour + 1) / 2);  // 축시(1)~해시(11)
  // 시간 천간: 오서둔
  const stemForTime = timeStemFromNextDay
  ? ((baseDayIdx + 1) % 60) % 10
  : dayStem;
  const timeStem = (오서둔[stemForTime] + timeBranch) % 10;

  return {
  input,
  pillars: {
  year:  { stem: yearStem,  branch: yearBranch,  gzIdx: yearGZ },
  month: { stem: monthStem, branch: monthBranch, idx: monthIdx },
  day:  { stem: dayStem,  branch: dayBranch,  gzIdx: dayGZ },
  time:  { stem: timeStem,  branch: timeBranch },
  },
  meta: {
  sajuYear,
  civilJD, solarJD,
  eotMinutes, longCorrectionMinutes,
  lichunJD,
  boundaries,
  dayPillarOffset, timeStemFromNextDay,
  },
  };
}

// ============================================================
// SECTION 4: 분석 엔진 — 십성·12운성·12신살·오행분포·신강신약·격국
// ============================================================

/**
 * (천간, 지지) → 60갑자 인덱스 (0~59)
 * 10과 12의 lcm=60이므로 유일하게 결정됨
 */
function gzIdx(stem, branch) {
  for (let i = 0; i < 60; i++) {
  if (i % 10 === stem && i % 12 === branch) return i;
  }
  return -1;
}

/**
 * 십성 인덱스 (0~9)
 *  0:비견 1:겁재 2:식신 3:상관 4:편재
 *  5:정재 6:편관 7:정관 8:편인 9:정인
 *
 * 오행 관계 + 음양 일치 여부로 결정
 */
function getSipsung(dayStem, targetStem) {
  const 일오 = 천간_오행[dayStem];
  const 대오 = 천간_오행[targetStem];
  const 동성 = 천간_음양[dayStem] === 천간_음양[targetStem];
  // 오행 차이: 0=같음 1=일간이생 2=일간이극 3=일간을극 4=일간을생
  const diff = (대오 - 일오 + 5) % 5;
  return diff * 2 + (동성 ? 0 : 1);
}

/**
 * 12운성 인덱스 (0~11)
 *  양간(갑병무경임)은 장생부터 순행, 음간은 역행
 */
function get12Unseong(dayStem, branch) {
  const info = 십이운성_장생[dayStem];
  return info.순행
  ? (branch - info.지지 + 12) % 12
  : (info.지지 - branch + 12) % 12;
}

/**
 * 12신살 인덱스 (0~11)
 * @param {number} refBranch - 기준 지지 (보통 년지, 일지도 가능)
 */
function get12Shinsal(refBranch, targetBranch) {
  const 시작 = 십이신살_시작[refBranch];
  return (targetBranch - 시작 + 12) % 12;
}

/**
 * 사주 종합 분석
 *  - 각 기둥별 십성·12운성·12신살
 *  - 지지 장간(여기·중기·정기)별 십성
 *  - 오행 분포 (단순 카운트 / 장간 일수 가중)
 *  - 신강신약 판정 (월령·기·세 종합)
 *  - 격국 자동 추출
 */
function analyzeSaju(saju) {
  const p = saju.pillars;
  const dayStem = p.day.stem;
  const yearBranch = p.year.branch;

  // 천간 십성 (일간 자기 자신은 본원)
  const 천간십성 = {
  year:  getSipsung(dayStem, p.year.stem),
  month: getSipsung(dayStem, p.month.stem),
  day:  -1,
  time:  getSipsung(dayStem, p.time.stem),
  };

  // 지지 12운성 (일간 기준)
  const 운성 = {
  year:  get12Unseong(dayStem, p.year.branch),
  month: get12Unseong(dayStem, p.month.branch),
  day:  get12Unseong(dayStem, p.day.branch),
  time:  get12Unseong(dayStem, p.time.branch),
  };

  // 지지 12신살 (년지 기준)
  const 신살 = {
  year:  get12Shinsal(yearBranch, p.year.branch),
  month: get12Shinsal(yearBranch, p.month.branch),
  day:  get12Shinsal(yearBranch, p.day.branch),
  time:  get12Shinsal(yearBranch, p.time.branch),
  };

  // 지지 장간 + 장간 십성
  function 장간십성(jg) {
  return [jg.여기, jg.중기, jg.정기].map(s => s >= 0 ? getSipsung(dayStem, s) : -1);
  }
  const 장간 = {
  year:  { ...지지_장간[p.year.branch],  십성: 장간십성(지지_장간[p.year.branch]) },
  month: { ...지지_장간[p.month.branch], 십성: 장간십성(지지_장간[p.month.branch]) },
  day:  { ...지지_장간[p.day.branch],  십성: 장간십성(지지_장간[p.day.branch]) },
  time:  { ...지지_장간[p.time.branch],  십성: 장간십성(지지_장간[p.time.branch]) },
  };

  // 오행 분포 — 두 가지 방식
  const allStems = [p.year.stem, p.month.stem, p.day.stem, p.time.stem];
  const allBranches = [p.year.branch, p.month.branch, p.day.branch, p.time.branch];

  // (1) 단순 카운트: 천간 1점 + 지지 정기 1점
  const 오행_단순 = [0, 0, 0, 0, 0];
  for (const s of allStems)  오행_단순[천간_오행[s]] += 1;
  for (const b of allBranches) 오행_단순[지지_오행[b]] += 1;

  // (2) 장간 일수 가중: 천간 1점 + 지지장간 일수 비율
  const 오행_가중 = [0, 0, 0, 0, 0];
  for (const s of allStems) 오행_가중[천간_오행[s]] += 1;
  for (const b of allBranches) {
  const jg = 지지_장간[b];
  const sum = jg.일수[0] + jg.일수[1] + jg.일수[2];
  if (jg.여기 >= 0) 오행_가중[천간_오행[jg.여기]] += jg.일수[0] / sum;
  if (jg.중기 >= 0) 오행_가중[천간_오행[jg.중기]] += jg.일수[1] / sum;
  if (jg.정기 >= 0) 오행_가중[천간_오행[jg.정기]] += jg.일수[2] / sum;
  }

  // 신강·신약 판정
  //  비겁(같은 오행) + 인성(생하는 오행) = 도움
  //  식상(내가 생) + 재성(내가 극) + 관성(나를 극) = 약화
  const dayOhaeng = 천간_오행[dayStem];
  const 도움오행 = [dayOhaeng, (dayOhaeng + 4) % 5];  // 비겁 + 인성
  const 약화오행 = [(dayOhaeng + 1) % 5,  // 식상
  (dayOhaeng + 2) % 5,  // 재성
  (dayOhaeng + 3) % 5];  // 관성

  // 기본 점수: 장간 가중 오행 분포 기준
  let 도움점수 = 0, 약화점수 = 0;
  for (let i = 0; i < 5; i++) {
  if (도움오행.includes(i)) 도움점수 += 오행_가중[i];
  if (약화오행.includes(i)) 약화점수 += 오행_가중[i];
  }

  // 월령 가중 (월지가 일간 도우면 ×1.5, 약화시키면 ÷1.5)
  const 월지오행 = 지지_오행[p.month.branch];
  let 득령 = false, 실령 = false;
  if (도움오행.includes(월지오행)) {
  득령 = true;
  도움점수 *= 1.5;
  } else if (약화오행.includes(월지오행)) {
  실령 = true;
  도움점수 /= 1.3;
  }

  // 일지 가중 (일지가 일간을 도우면 +0.5)
  if (도움오행.includes(지지_오행[p.day.branch])) {
  도움점수 += 0.5;
  }

  const 신강비율 = 도움점수 / (도움점수 + 약화점수);
  let 신강등급;
  if (신강비율 >= 0.65)  신강등급 = '신강';
  else if (신강비율 >= 0.55) 신강등급 = '중상';
  else if (신강비율 >= 0.45) 신강등급 = '중화';
  else if (신강비율 >= 0.35) 신강등급 = '중하';
  else  신강등급 = '신약';

  // 격국 판정
  //  1. 월지 정기의 십성을 기본 격으로
  //  2. 비견 → 건록격, 겁재 → 양인격 (특수)
  //  3. 그 외엔 십성명 + '격'
  //  4. 정기가 천간에 투출되어 있으면 명확한 격, 아니면 격 미투출(약격)
  const 월지정기 = 장간.month.정기;
  const 월지본기십성 = getSipsung(dayStem, 월지정기);
  let 격국명;
  if (월지본기십성 === 0)  격국명 = '건록격';
  else if (월지본기십성 === 1) 격국명 = '양인격';
  else  격국명 = 십성명[월지본기십성] + '격';
  const 정기투출 = allStems.some((s, idx) => idx !== 2 && s === 월지정기); // 일간 제외

  return {
  천간십성, 운성, 신살, 장간,
  오행: { 단순: 오행_단순, 가중: 오행_가중 },
  신강신약: {
  등급: 신강등급, 비율: 신강비율,
  도움: 도움점수, 약화: 약화점수,
  득령, 실령,
  },
  격국: { 명: 격국명, 정기투출, 월지정기십성: 월지본기십성 },
  };
}

// ============================================================
// SECTION 5: 대운·세운
// ============================================================

/**
 * 대운 계산
 *  - 순행: 양년 남자 또는 음년 여자
 *  - 역행: 음년 남자 또는 양년 여자
 *  - 시작 갑자: 월주의 다음(순행) 또는 이전(역행)
 *  - 대운수: 출생 → 다음(순행)/이전(역행) 절기까지 일수 ÷ 3
 *
 * @returns { 순행, startAge, days, daewoon: [{stem, branch, gzIdx, startAge, sipsung, unseong, shinsal}] }
 */
function calculateDaewoon(saju, count = 10) {
  const yearStem = saju.pillars.year.stem;
  const yearYinYang = 천간_음양[yearStem]; // 0=양 1=음
  const gender = saju.input.gender || 'M';
  const 순행 = (yearYinYang === 0 && gender === 'M') || (yearYinYang === 1 && gender === 'F');

  const solarJD = saju.meta.solarJD;
  const boundaries = saju.meta.boundaries; // 사주연도의 12절

  // 다음/이전 절 JD
  let targetJD = null;
  if (순행) {
  for (const b of boundaries) {
  if (b.JD > solarJD) { targetJD = b.JD; break; }
  }
  if (targetJD === null) {
  // 다음 해 입춘
  const near = toJD(saju.meta.sajuYear + 1, 2, 4);
  targetJD = findSunLongitudeJD(315, near);
  }
  } else {
  for (let i = boundaries.length - 1; i >= 0; i--) {
  if (boundaries[i].JD < solarJD) { targetJD = boundaries[i].JD; break; }
  }
  if (targetJD === null) {
  // 전 해 소한
  const near = toJD(saju.meta.sajuYear, 1, 5);
  targetJD = findSunLongitudeJD(285, near);
  }
  }
  const days = Math.abs(targetJD - solarJD);
  const startAge = days / 3; // 3일 = 1년

  // 월주 60갑자 인덱스
  const monthGZ = gzIdx(saju.pillars.month.stem, saju.pillars.month.branch);

  // 대운 10기 (10년 단위)
  const daewoon = [];
  const dayStem = saju.pillars.day.stem;
  const yrBranch = saju.pillars.year.branch;
  for (let i = 0; i < count; i++) {
  const gz = 순행
  ? (monthGZ + i + 1) % 60
  : ((monthGZ - i - 1) % 60 + 60) % 60;
  const stem = gz % 10, branch = gz % 12;
  daewoon.push({
  stem, branch, gzIdx: gz,
  startAge: startAge + i * 10,
  sipsung: getSipsung(dayStem, stem),
  unseong: get12Unseong(dayStem, branch),
  shinsal: get12Shinsal(yrBranch, branch),
  });
  }
  return { 순행, startAge, days, daewoon };
}

/**
 * 세운 (연운) 계산
 * @param {number} fromYear - 시작 연도 (양력 기준, 입춘 전후로 사주연도 변환 별도)
 * @param {number} count - 출력 개수
 */
function calculateSewoon(saju, fromYear, count) {
  const dayStem = saju.pillars.day.stem;
  const yearBranch = saju.pillars.year.branch;
  const out = [];
  for (let i = 0; i < count; i++) {
  const y = fromYear + i;
  const gz = ((y - 4) % 60 + 60) % 60;
  const stem = gz % 10, branch = gz % 12;
  out.push({
  year: y, stem, branch, gzIdx: gz,
  sipsung: getSipsung(dayStem, stem),
  unseong: get12Unseong(dayStem, branch),
  shinsal: get12Shinsal(yearBranch, branch),
  });
  }
  return out;
}

// ============================================================
// SECTION 6: 룰셋 해석 데이터 — 일간·십성·격국·12운성
// ============================================================

// 10개 일간별 본성 (자평진전·궁통보감 기반 압축 해설)
const 해석_일간 = [
  // 0 갑(甲) 양목
  {
  상징: '동량지목 (棟樑之木) — 큰 나무, 우두머리',
  본성: '곧고 우직하며 위로 뻗어가려는 기상이 강하다. 한 분야의 시작과 리더십을 상징한다.',
  장점: '추진력 · 자존심 · 인자함 · 곧음 · 책임감',
  주의: '고집·융통성 부족·자기주장 과다·꺾이면 회복이 더디다',
  직업: ['교육', '공무', '의료', '경영', '건축·임업'],
  },
  // 1 을(乙) 음목
  {
  상징: '화초목 (花草木) — 등나무, 풀',
  본성: '부드럽고 끈질기다. 환경에 맞춰 휘어지지만 결코 꺾이지 않는 적응의 달인.',
  장점: '유연성 · 끈기 · 친화력 · 섬세함 · 실용감각',
  주의: '의존성·우유부단·속내를 감춤·기복이 잦음',
  직업: ['디자인', '문화·예술', '상담', '교육', '원예·요식'],
  },
  // 2 병(丙) 양화
  {
  상징: '태양화 (太陽火) — 빛, 광명',
  본성: '밝고 호쾌하다. 빛을 사방에 비추듯 만인의 주목을 받는 양기의 정점.',
  장점: '명랑 · 정열 · 솔직 · 추진력 · 베푸는 성품',
  주의: '다혈질·변덕·깊이 부족·소비 과다',
  직업: ['방송·연예', '영업·마케팅', '정치', '교육', '의료'],
  },
  // 3 정(丁) 음화
  {
  상징: '등촉화 (燈燭火) — 촛불, 화로',
  본성: '은은하고 따뜻하다. 어둠 속에서 길을 비추듯 사색적이고 통찰력이 깊다.',
  장점: '섬세 · 사려깊음 · 봉사정신 · 예술적 감각 · 따뜻함',
  주의: '우유부단·기복·예민·자기소모',
  직업: ['예술', '연구', '의료', '교육', '상담·심리'],
  },
  // 4 무(戊) 양토
  {
  상징: '성원토 (城垣土) — 큰 산, 성벽',
  본성: '중후하고 신뢰감 있다. 묵직하게 자리를 지키며 모든 것을 품는 대지의 기상.',
  장점: '신뢰 · 포용 · 중용 · 책임감 · 안정감',
  주의: '답답함·융통성 부족·고집·결단 느림',
  직업: ['부동산·건설', '농업', '공무', '금융', '종교'],
  },
  // 5 기(己) 음토
  {
  상징: '전원토 (田園土) — 옥토, 텃밭',
  본성: '부드럽고 양육적이다. 만물을 길러내는 어머니 같은 흙, 실속과 포용을 함께 갖춤.',
  장점: '인내 · 자상함 · 실용성 · 양육·중재 능력',
  주의: '의존성·결단 부족·속앓이·소심',
  직업: ['교육·보육', '농업', '요식', '의료', '서비스'],
  },
  // 6 경(庚) 양금
  {
  상징: '검극금 (劍戟金) — 무쇠, 도끼',
  본성: '강직하고 결단력 있다. 의리를 중시하며 옳은 일에 거침이 없는 무관의 기질.',
  장점: '의리 · 결단력 · 추진력 · 정의감 · 솔직',
  주의: '거칠음·고집·충돌·자기 과신',
  직업: ['군·경·법', '의료(외과)', '스포츠', '기계·공학', '금융'],
  },
  // 7 신(辛) 음금
  {
  상징: '주옥금 (珠玉金) — 보석, 정련금',
  본성: '섬세하고 예리하다. 정제된 보석처럼 자존감이 높고 미적 감각이 뛰어남.',
  장점: '섬세 · 미적 감각 · 분석력 · 자존감 · 깔끔함',
  주의: '예민·결벽·자기중심·차가움',
  직업: ['예술·디자인', '의료', '연구', '회계·법무', '뷰티'],
  },
  // 8 임(壬) 양수
  {
  상징: '강하수 (江河水) — 큰물, 강',
  본성: '넓고 유연하다. 흘러 모이는 바닷물처럼 정보와 사람을 끌어모으는 지혜의 기질.',
  장점: '지혜 · 포용 · 융통성 · 사교성 · 통찰',
  주의: '변덕·산만·계획성 부족·범람의 위험',
  직업: ['무역·유통', '외교', '언론·방송', '학문', '해양·물류'],
  },
  // 9 계(癸) 음수
  {
  상징: '우로수 (雨露水) — 빗물, 이슬',
  본성: '맑고 깊다. 작은 물방울이지만 만물을 적시는 순수와 직관의 기운.',
  장점: '직관 · 청정 · 사색 · 적응력 · 섬세함',
  주의: '비관·의기소침·소심·기복',
  직업: ['교육·연구', '예술', '심리·상담', '의료', '종교·영성'],
  },
];

// 십성 해설
const 해석_십성 = [
  // 0 비견
  { 의미: '나와 같은 오행·같은 음양. 형제·동료·동업자·경쟁자.',
  많으면: '자존심 강하고 독립적이나 협력 부족, 형제·동업 갈등 가능',
  없으면: '의존성·자립심 약화, 외로움' },
  // 1 겁재
  { 의미: '같은 오행·다른 음양. 강한 추진·도전·경쟁의식.',
  많으면: '경쟁심·투쟁·재물 손실(군겁쟁재) 위험',
  없으면: '추진력 부족·소극적' },
  // 2 식신
  { 의미: '내가 생하는 오행·같은 음양. 표현·식록·낙천·여유.',
  많으면: '게으름·향락·의지박약',
  없으면: '표현력 약화·여유 부족' },
  // 3 상관
  { 의미: '내가 생하는 오행·다른 음양. 창의·비판·화려·재능.',
  많으면: '비판·반항·명예 손상·관(官) 손상',
  없으면: '창의성 부족·평범' },
  // 4 편재
  { 의미: '내가 극하는 오행·같은 음양. 활동·투자·유동 재물·인연.',
  많으면: '분주·산만·풍류·여색',
  없으면: '재물 활동성 약화·소극적' },
  // 5 정재
  { 의미: '내가 극하는 오행·다른 음양. 정직한 재물·근면·아내(남명).',
  많으면: '재물 집착·답답함·인색',
  없으면: '재물·실리 감각 부족' },
  // 6 편관
  { 의미: '나를 극하는 오행·같은 음양. 권위·통솔·위엄·시련.',
  많으면: '압박·시비·관재·건강 손상',
  없으면: '결단력·위엄 부족' },
  // 7 정관
  { 의미: '나를 극하는 오행·다른 음양. 명예·직위·책임·남편(여명).',
  많으면: '경직·책임 과중·구속감',
  없으면: '명예·체면 의식 약화·자유분방' },
  // 8 편인
  { 의미: '나를 생하는 오행·같은 음양. 직관·통찰·전문·종교.',
  많으면: '고독·집착·식신 손상(밥줄 끊김)·잔머리',
  없으면: '직관·통찰력 부족' },
  // 9 정인
  { 의미: '나를 생하는 오행·다른 음양. 학문·자애·문서·어머니.',
  많으면: '의존성·게으름·실행력 부족',
  없으면: '학문·문서 약화·어머니 인연 박' },
];

// 격국 해설
const 해석_격국 = {
  '정관격': { 특성: '명예·질서·책임을 중시하는 군자형. 안정된 직장·학문이 발전축.',
  직업: '공무원·법조·교육·대기업·연구', 키워드: '명예·체통' },
  '편관격': { 특성: '위엄과 추진력으로 난세를 헤쳐가는 무관형. 강한 책임감과 위기관리력.',
  직업: '군·경·법·의료·정치', 키워드: '권위·위세' },
  '정재격': { 특성: '근면·성실로 정직한 재물을 쌓는 실무형. 가정·결혼이 안정적.',
  직업: '회계·금융·실업·관리·중소기업', 키워드: '근면·실속' },
  '편재격': { 특성: '활동성·풍류·국제감각의 사업가형. 큰 재물의 흐름을 잡는 안목.',
  직업: '무역·유통·금융·부동산·국제', 키워드: '활동·기회' },
  '식신격': { 특성: '여유와 표현력이 뛰어난 식록형. 예술·요리·교육에 재능.',
  직업: '교육·요식·예술·작가·치유', 키워드: '여유·식록' },
  '상관격': { 특성: '뛰어난 창의력과 비평력. 예술·언변·기술로 두각, 다만 관성과 충돌 주의.',
  직업: '예술·연예·방송·기술·창업', 키워드: '재능·반항' },
  '정인격': { 특성: '학문·문서·인덕이 두터운 학자형. 자애로움과 명예를 중시.',
  직업: '학자·교사·연구·문화·종교', 키워드: '학문·인덕' },
  '편인격': { 특성: '직관과 통찰이 뛰어난 전문가형. 비주류 학문·종교·예술에 인연.',
  직업: '의료(한의·심리)·종교·예술·역학', 키워드: '직관·전문' },
  '건록격': { 특성: '월지 본기에 자립하는 독립형. 자수성가와 자영업의 기질.',
  직업: '자영업·전문직·독립 사업', 키워드: '자립·독립' },
  '양인격': { 특성: '강건·과단의 무관 기질. 양인+편관 조합 시 큰 인물의 명조 다수.',
  직업: '군·경·체육·외과·강도 높은 직종', 키워드: '강건·과단' },
};

// 12운성 해설
const 해석_12운성 = [
  { 명: '장생', 의미: '갓 태어남 — 시작·성장·희망' },
  { 명: '목욕', 의미: '갓난아이의 목욕 — 변화·도화·흔들림' },
  { 명: '관대', 의미: '청년의 관례 — 자립·발전·도전' },
  { 명: '건록', 의미: '벼슬에 오름 — 안정·전성기 진입' },
  { 명: '제왕', 의미: '왕의 자리 — 정점·강함·교만 주의' },
  { 명: '쇠',  의미: '기운이 꺾임 — 신중·은퇴 준비' },
  { 명: '병',  의미: '병이 듦 — 침체·휴식·내면 정리' },
  { 명: '사',  의미: '죽음 — 단절·전환·정신화' },
  { 명: '묘',  의미: '무덤 — 저장·은둔·정리' },
  { 명: '절',  의미: '끊김 — 새 출발·고립' },
  { 명: '태',  의미: '잉태 — 미약하나 가능성' },
  { 명: '양',  의미: '양육 — 준비·기다림' },
];

// 12신살 의미
const 해석_12신살 = [
  '겁살: 빼앗김·이별·돌발의 살',
  '재살: 갇힘·구속·관재의 살',
  '천살: 천재지변·예기치 못한 변동',
  '지살: 이동·역마와 유사, 환경 변화',
  '년살: 도화·풍류·인기',
  '월살: 고초·고독·소모',
  '망신: 손실·체면 손상',
  '장성: 무관·권력·우두머리',
  '반안: 출세·승진·안정',
  '역마: 이동·여행·해외',
  '육해: 질병·구설·고독',
  '화개: 학문·예술·종교·고독',
];

/**
 * 종합 해석 텍스트 생성
 * @returns { 요약, 일간_본성, 격국, 신강신약, 십성_강약, 현재대운, 카테고리 }
 */
function generateInterpretation(saju, analysis, daewoonResult) {
  const dayStem = saju.pillars.day.stem;
  const il = 해석_일간[dayStem];
  const gyeok = 해석_격국[analysis.격국.명] || { 특성: '특수 격국', 직업: '-', 키워드: '-' };

  // 십성 카운트 (천간 + 지지 정기)
  const sipsungCount = Array(10).fill(0);
  // 천간 (일간 제외)
  for (const k of ['year', 'month', 'time']) {
  const sip = analysis.천간십성[k];
  if (sip >= 0) sipsungCount[sip] += 1;
  }
  // 지지 정기 십성
  for (const k of ['year', 'month', 'day', 'time']) {
  const sip = analysis.장간[k].십성[2]; // 정기
  if (sip >= 0) sipsungCount[sip] += 1;
  }

  const strongestSip = sipsungCount.indexOf(Math.max(...sipsungCount));
  const weakSips = [];
  for (let i = 0; i < 10; i++) if (sipsungCount[i] === 0) weakSips.push(i);

  // 신강·신약 → 용신 방향
  const isStrong = (analysis.신강신약.등급 === '신강' || analysis.신강신약.등급 === '중상');
  const isWeak = (analysis.신강신약.등급 === '신약' || analysis.신강신약.등급 === '중하');
  let 용신방향, 기신방향;
  if (isStrong) {
  용신방향 = '식상·재성·관성 (설기·억부)';
  기신방향 = '인성·비겁 (도움 과다)';
  } else if (isWeak) {
  용신방향 = '인성·비겁 (생조)';
  기신방향 = '식상·재성·관성 (설기·극제 과다)';
  } else {
  용신방향 = '중화 — 균형 유지, 통관/조후 위주';
  기신방향 = '편향된 오행 발생 시 조정';
  }

  // 현재 대운 (지금 나이에 해당)
  const currentYear = new Date().getFullYear();
  const age = currentYear - saju.input.year + 1; // 한국식 만 나이가 아닌 단순 햇수
  let currentDae = null;
  for (let i = daewoonResult.daewoon.length - 1; i >= 0; i--) {
  if (age >= daewoonResult.daewoon[i].startAge) {
  currentDae = daewoonResult.daewoon[i];
  break;
  }
  }

  // 카테고리별 해설 조합
  const 성격 = `${il.본성} 격국이 ${analysis.격국.명}이므로 ${gyeok.특성}`;
  const 직업 = `타고난 적성: ${il.직업.join(' · ')}. 격국 적성: ${gyeok.직업}.`;
  const 재물 = (() => {
  const 재성 = sipsungCount[4] + sipsungCount[5];
  if (재성 === 0) return '사주에 재성(편재·정재)이 직접 드러나지 않아 재물 활동 동기보다는 학문·관성·인성 위주의 삶이 더 자연스럽다.';
  if (재성 >= 3) return '재성이 왕성하여 재물 활동에 대한 관심·기회가 많다. 다만 신약하면 재다신약으로 재물에 휘둘릴 위험.';
  return '재성이 적절히 자리하여 정직한 노력에 따른 결실을 거두는 명조.';
  })();
  const 관계 = (() => {
  const 관성 = sipsungCount[6] + sipsungCount[7];
  const 비겁 = sipsungCount[0] + sipsungCount[1];
  if (비겁 >= 3) return '비겁이 많아 형제·동료·동업자 인연이 두텁다. 다만 군겁쟁재(재성 다툼) 주의.';
  if (관성 === 0) return '관성이 없어 외부 규제에 얽매이지 않는 자유분방한 인간관계.';
  return '관성과 비겁이 조화를 이루는 균형 잡힌 인간관계.';
  })();
  const 건강 = (() => {
  const 최약오행 = analysis.오행.가중.indexOf(Math.min(...analysis.오행.가중));
  return `사주에서 가장 약한 오행은 ${오행명[최약오행]}이다. ${오행명[최약오행]}에 해당하는 장기(${{0:'간·담', 1:'심·소장', 2:'비·위', 3:'폐·대장', 4:'신·방광'}[최약오행]})를 평소 관리해야 한다.`;
  })();

  const 종합 = (() => {
  const 등급 = analysis.신강신약.등급;
  const 강약설명 = 등급 === '신강' ? '일간이 강하므로 설기(식상·재성·관성)로 흐름을 내보내야 발달한다.'
  : 등급 === '신약' ? '일간이 약하므로 인성·비겁으로 도와야 사주가 안정된다.'
  : '신강·신약이 어느 한쪽으로 치우치지 않은 중화에 가까운 명조다.';
  const 현재운설명 = currentDae
  ? `현재 대운은 ${천간_한자[currentDae.stem]}${지지_한자[currentDae.branch]}(${천간[currentDae.stem]}${지지[currentDae.branch]}) — ${십성명[currentDae.sipsung]} 운으로, ${해석_십성[currentDae.sipsung].의미.split('.')[0]}의 흐름이 강조되는 시기.`
  : '';
  return `${il.상징}. ${il.본성} ${강약설명} ${현재운설명}`;
  })();

  return {
  종합, 성격, 직업, 재물, 관계, 건강,
  일간_본성: il,
  격국_해설: gyeok,
  십성_분포: sipsungCount,
  가장강한십성: 십성명[strongestSip],
  부족한십성: weakSips.map(i => 십성명[i]),
  용신방향, 기신방향,
  현재대운: currentDae,
  나이: age,
  };
}

// ============================================================
// SECTION 7: Claude API 연동
// ============================================================

/**
 * 사주 분석 결과를 Claude에 보낼 프롬프트로 변환
 */
function buildSajuPrompt(saju, analysis, daewoonResult, interp, nameAnalysis = null, name = null, concern = '', lifeContext = null) {
  const p = saju.pillars;
  const dayStem = p.day.stem;
  const fmt = (stem, branch) => `${천간_한자[stem]}${지지_한자[branch]}(${천간[stem]}${지지[branch]})`;
  const sajuStr = `${fmt(p.year.stem, p.year.branch)} ${fmt(p.month.stem, p.month.branch)} ${fmt(p.day.stem, p.day.branch)} ${fmt(p.time.stem, p.time.branch)}`;

  const 천간십성표 = ['년주', '월주', '일주', '시주'].map((k, i) => {
  const key = ['year', 'month', 'day', 'time'][i];
  const sip = analysis.천간십성[key];
  return `${k}: ${sip === -1 ? '본원' : 십성명[sip]}`;
  }).join(', ');

  const 지지운성표 = ['년지', '월지', '일지', '시지'].map((k, i) => {
  const key = ['year', 'month', 'day', 'time'][i];
  return `${k}: ${십이운성명[analysis.운성[key]]}`;
  }).join(', ');

  const 장간표 = ['년지', '월지', '일지', '시지'].map((k, i) => {
  const key = ['year', 'month', 'day', 'time'][i];
  const jg = analysis.장간[key];
  const parts = [];
  if (jg.여기 >= 0) parts.push(`${천간_한자[jg.여기]}(${십성명[jg.십성[0]]})`);
  if (jg.중기 >= 0) parts.push(`${천간_한자[jg.중기]}(${십성명[jg.십성[1]]})`);
  if (jg.정기 >= 0) parts.push(`${천간_한자[jg.정기]}(${십성명[jg.십성[2]]})`);
  return `${k}: ${parts.join(' · ')}`;
  }).join('\n  ');

  const 오행분포 = 오행명.map((n, i) => `${n} ${analysis.오행.가중[i].toFixed(2)}`).join(', ');

  const 대운요약 = daewoonResult.daewoon.slice(0, 8).map((d, i) =>
  `${i+1}운(${d.startAge.toFixed(1)}세~): ${천간_한자[d.stem]}${지지_한자[d.branch]} ${십성명[d.sipsung]}/${십이운성명[d.unseong]}`
  ).join('\n  ');

  // 이름 정보 (선택)
  let nameSection = '';
  let 호칭 = '의뢰인';
  if (name && (name.surname || name.givenName)) {
  호칭 = `${name.surname}${name.givenName}님`;
  nameSection = `\n- 이름: ${name.surname}${name.givenName}${name.hanja ? ` (${name.hanja})` : ''}`;
  }
  // 성명학 분석 (선택)
  let nameAnalysisSection = '';
  if (nameAnalysis) {
  const parts = [];
  if (nameAnalysis.한자분석) {
  const o = nameAnalysis.한자분석.오격;
  parts.push(`## 성명학 — 오격 (五格)`);
  for (const k of ['원격','형격','이격','정격','외격']) {
  parts.push(`- ${k}: ${o[k].수}수 · ${o[k].평가} · ${o[k].명} (${o[k].의미})`);
  }
  parts.push(`- 음양 조화: 양 ${nameAnalysis.한자분석.음양.양} / 음 ${nameAnalysis.한자분석.음양.음} → ${nameAnalysis.한자분석.음양.평가}`);
  }
  parts.push(`## 성명학 — 음오행 (音五行)`);
  const eo = nameAnalysis.음오행분석;
  parts.push(`- 글자별 초성 오행: ${eo.글자.map((c,i) => `${c}(${eo.초성오행[i]>=0 ? 오행명[eo.초성오행[i]] : '?'})`).join(' · ')}`);
  parts.push(`- 인접 관계: ${eo.관계.join(' → ')}`);
  parts.push(`- 평가: ${eo.평가}`);
  parts.push(`- **종합:** ${nameAnalysis.종합}`);
  nameAnalysisSection = '\n\n' + parts.join('\n');
  }

  // 지금 상황 (MBTI + 직장 + 연애)
  let lifeSection = '';
  if (lifeContext && (lifeContext.job || lifeContext.love || lifeContext.mbti)) {
  const parts = ['\n\n# 의뢰인의 지금 상황'];
  if (lifeContext.mbti) {
  parts.push(`- MBTI 성격유형: ${lifeContext.mbti}`);
  }
  if (lifeContext.job) {
  parts.push(`- 직장·일: ${lifeContext.job.상태}${lifeContext.job.기간 ? ` (기간 ${lifeContext.job.기간})` : ''}`);
  }
  if (lifeContext.love) {
  parts.push(`- 연애·결혼: ${lifeContext.love.상태}${lifeContext.love.기간 ? ` (기간 ${lifeContext.love.기간})` : ''}`);
  }
  parts.push('→ 풀이 작성 시 이 정보를 자연스럽게 반영해주세요. MBTI가 있으면 사주가 보여주는 기질과 평소 보이는 성격(MBTI)이 어떻게 어울리거나 다른지 살펴보고, 직장·연애 상황은 "지금 직장에서의 흐름은…" / "지금 만나고 계신 분과의…" 식으로 자연스럽게 연결.');
  lifeSection = parts.join('\n');
  }

  // 고민거리 (선택)
  const concernSection = concern && concern.trim()
  ? `\n\n# 의뢰인의 고민·질문\n"${concern.trim()}"\n→ 이 고민에 대해 사주·대운·성명학을 근거로 직접적이고 구체적인 조언을 풀이에 반드시 포함할 것.`
  : '';

  return `당신은 자평명리학 정통 사주풀이 전문가입니다. 아래 분석 데이터를 바탕으로 ${호칭}의 사주를 풀이해주세요.

# 입력 정보${nameSection}
- 양력 ${saju.input.year}년 ${saju.input.month}월 ${saju.input.day}일 ${saju.input.hour}시 ${saju.input.minute}분 ${saju.input.gender === 'M' ? '남자' : '여자'}
- 출생지 경도: ${saju.input.longitude}°, 진태양시 보정: ${saju.input.useTrueSolar ? '적용' : '미적용'}

# 사주 8글자 (년주 월주 일주 시주)
**${sajuStr}**
- 일간(본원): ${천간_한자[dayStem]} (${천간[dayStem]}, ${오행명[천간_오행[dayStem]]} ${천간_음양[dayStem] === 0 ? '양' : '음'})

# 천간 십성
${천간십성표}

# 지지 12운성 (일간 기준)
${지지운성표}

# 지지 장간 (여기·중기·정기, 십성)
  ${장간표}

# 오행 분포 (장간 가중치 적용)
${오행분포}

# 격국 / 신강·신약
- 격국: **${analysis.격국.명}** (월지 정기 ${analysis.격국.정기투출 ? '천간 투출 → 격이 분명' : '미투출 → 격이 약함'})
- 신강 등급: **${analysis.신강신약.등급}** (도움/약화 비율 ${(analysis.신강신약.비율*100).toFixed(1)}%)
- 득령/실령: ${analysis.신강신약.득령 ? '득령(月令이 일간을 도움)' : analysis.신강신약.실령 ? '실령(月令이 일간 약화)' : '평'}
- 가장 강한 십성: ${interp.가장강한십성}
- 부족한 십성: ${interp.부족한십성.join(', ') || '없음 (10성 모두 갖춤)'}
- 룰셋 용신 방향: ${interp.용신방향}

# 대운 흐름 (순/역: ${daewoonResult.순행 ? '순행' : '역행'}, 시작 ${daewoonResult.startAge.toFixed(2)}세)
  ${대운요약}

# 현재 시점 (${interp.나이}세) 대운
${interp.현재대운
  ? `${천간_한자[interp.현재대운.stem]}${지지_한자[interp.현재대운.branch]} — ${십성명[interp.현재대운.sipsung]} / ${십이운성명[interp.현재대운.unseong]} / ${십이신살명[interp.현재대운.shinsal]}`
  : '해당 나이의 대운 자료 없음'}${nameAnalysisSection}${lifeSection}${concernSection}

# 작성 방법 (아주 중요)
- 한국어 존댓말, **친한 친구나 따뜻한 상담사가 이야기하듯** 부드러운 톤
- ${호칭}을 호칭으로 자연스럽게 사용 ("${호칭}은 ~한 분이세요", "${호칭}, 사실은요…" 등)
- **어려운 사주 용어는 절대 쓰지 마세요**: 격국·십성·일간·용신·천간·지지·비견·식신·상관·편재·정재·편관·정관·편인·정인·12운성·12신살·대운·세운·오행·음양·신강·신약·득령·실령 같은 단어 사용 금지
- 위에 있는 사주 분석 데이터는 당신이 풀이의 근거로 참고만 하고, **결과만 일상적인 말로** 전달
- 마크다운 헤더(#, ##) 대신 자연스럽게 흐르는 글로 작성. 항목 구분이 꼭 필요하면 작은 소제목(**굵게**) 정도만
- 점쟁이가 단정짓듯 말하지 말고, "그런 경향이 있어요", "이런 부분을 신경 쓰시면 좋아요" 같이 부드럽게
- 부정적인 면도 솔직히 다루되, 따뜻한 시선으로 "이런 점에 주의하시면 더 좋아질 수 있어요"

# 풀이에 담을 내용 (자연스럽게 연결해서 풀어주세요)
1. 어떤 사람인지 — 타고난 성격·기질·매력을 따뜻하게
2. 잘 맞는 일·재능 — 어떤 분야가 어울리는지 구체적으로
3. 돈 문제의 흐름 — 어떤 방식으로 재물을 다루면 좋은지
4. 인간관계와 사랑 — 어떤 사람과 잘 맞는지, 관계에서 주의할 점
5. 건강에서 신경 쓸 부분 — 어느 쪽이 약한 편이니 관리하면 좋을지
6. 지금 시기는 어떤 흐름인지 (${interp.나이}세 즈음) — 앞으로의 큰 흐름도 살짝
${nameAnalysis ? '7. 이름이 본인과 어떻게 어울리는지 — 이름의 좋은 점과 보완할 점\n' : ''}${concern && concern.trim() ? `${nameAnalysis ? '8' : '7'}. ${호칭}의 고민("${concern.trim()}")에 대한 답 — 마지막에 가장 자세하게. 구체적으로 "지금은 ~하시는 게 좋아요", "~를 시도해보세요", "~는 잠시 미루세요" 처럼 명확하고 따뜻하게 조언\n` : ''}
# 분량
${concern && concern.trim() ? '2000~2500자' : (nameAnalysis ? '1700~2200자' : '1500~2000자')} 정도, 너무 길지 않게.`;
}

// LLMUtils + BaseReader 외부 모듈 (ADR-038 Phase 2) — js/core/llm-utils.js + base-reader.js
// 본 위치에서 window.LLMUtils + window.BaseReader 글로벌 사용 가능 (이미 로드됨)

/**
 * Bizrouter LLM API 호출 — 우리 백엔드 /api/llm/chat 사용
 *  - Gemini 2.5 Flash Lite (또는 BIZROUTER_MODEL env)
 *  - 적대적 비판 루프·캐시·rate limit 등 백엔드 인프라 활용
 *  - 스트리밍은 text/plain chunks (SSE 가 아닌 raw chunk)
 *  - model 파라미터는 호환을 위해 받지만 백엔드가 결정
 */
async function callFreeAI(model, prompt, onChunk = null, timeoutMs = 120000) {
  const url = '/api/llm/chat';
  const body = {
  prompt,
  model: model || null,
  stream: !!onChunk,
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let resp;
  try {
  resp = await fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
  signal: controller.signal,
  });
  } catch (e) {
  clearTimeout(timeoutId);
  if (e.name === 'AbortError') throw new Error(`응답 시간 초과 (${timeoutMs / 1000}초)`);
  throw e;
  }

  if (!resp.ok) {
  clearTimeout(timeoutId);
  const errText = await resp.text();
  throw new Error(`API ${resp.status}: ${errText.slice(0, 200)}`);
  }

  if (!onChunk) {
  clearTimeout(timeoutId);
  const text = await resp.text();
  try {
  const data = JSON.parse(text);
  return data.text || data.choices?.[0]?.message?.content || text;
  } catch {
  return text;
  }
  }

  // 스트리밍 — text/plain 청크를 누적
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';
  try {
  while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value, { stream: true });
  if (chunk) {
  fullText += chunk;
  onChunk(chunk, fullText);
  }
  }
  } finally {
  clearTimeout(timeoutId);
  }
  return fullText;
}

/**
 * 사람 한 명의 사주 요약 텍스트 (궁합 프롬프트에 두 명 정보 포함용)
 */
function buildPersonSummary(saju, label) {
  const p = saju.pillars;
  const a = analyzeSaju(saju);
  const dayStem = p.day.stem;
  const fmt = (s, b) => `${천간_한자[s]}${지지_한자[b]}(${천간[s]}${지지[b]})`;
  const name = saju.name && (saju.name.surname || saju.name.givenName)
  ? `${saju.name.surname}${saju.name.givenName}`
  : (label || '의뢰인');
  const mbti = saju.lifeContext && saju.lifeContext.mbti ? saju.lifeContext.mbti : '미상';
  return `## ${label} — ${name}
- 양력 ${saju.input.year}년 ${saju.input.month}월 ${saju.input.day}일 ${saju.input.hour}시 ${saju.input.minute}분 ${saju.input.gender === 'M' ? '남자' : '여자'}
- 사주 8글자: ${fmt(p.year.stem,p.year.branch)} ${fmt(p.month.stem,p.month.branch)} ${fmt(p.day.stem,p.day.branch)} ${fmt(p.time.stem,p.time.branch)}
- 일간(본원): ${천간_한자[dayStem]}(${천간[dayStem]}, ${오행명[천간_오행[dayStem]]} ${천간_음양[dayStem]===0?'양':'음'})
- 격국: ${a.격국.명}
- 신강 등급: ${a.신강신약.등급}
- 오행 분포(가중): 목 ${a.오행.가중[0].toFixed(1)} / 화 ${a.오행.가중[1].toFixed(1)} / 토 ${a.오행.가중[2].toFixed(1)} / 금 ${a.오행.가중[3].toFixed(1)} / 수 ${a.오행.가중[4].toFixed(1)}
- MBTI: ${mbti}`;
}

/**
 * 궁합 분석용 프롬프트 (두 사람 비교)
 */
function buildCompatPrompt(mySaju, partnerSaju, mode, concern) {
  const myInterp = generateInterpretation(mySaju, analyzeSaju(mySaju), calculateDaewoon(mySaju));
  const 호칭 = (mySaju.name && (mySaju.name.surname || mySaju.name.givenName))
  ? `${mySaju.name.surname}${mySaju.name.givenName}님`
  : '의뢰인';
  const partnerName = (partnerSaju.name && partnerSaju.name.givenName) || '상대방';
  const modeLabel = { couple: '연인·배우자', friend: '친구', coworker: '동료·상사' }[mode] || '관계';
  const relationFocus = {
  couple: '연애·결혼 궁합 — 감정의 결, 의사소통 방식, 가치관 차이, 갈등 패턴, 함께 살 때 시너지·주의점',
  friend: '친구 궁합 — 어울림의 결, 함께 있을 때 편안함, 서로의 기질 차이, 오래 가는 관계가 될지',
  coworker: '동료·상사 궁합 — 일할 때 시너지, 역할 분담, 의사결정 스타일 차이, 협업에서 조심할 점',
  }[mode] || '';

  const concernSection = concern && concern.trim()
  ? `\n\n# ${호칭}의 고민·질문\n"${concern.trim()}"`
  : '';

  return `당신은 자평명리학 정통 사주풀이 전문가이자 두 사람의 사주 궁합을 봐주는 분입니다.
${호칭}과 ${partnerName}의 ${modeLabel} 궁합을 풀어주세요.

# 두 분의 정보
${buildPersonSummary(mySaju, '의뢰인')}

${buildPersonSummary(partnerSaju, '상대방')}${concernSection}

# 분석 초점
${relationFocus}

# 작성 방법
- 한국어 존댓말, 친한 친구·상담사가 이야기하듯 부드럽게
- ${호칭}을 호칭으로 사용 (상대방은 "${partnerName}" 또는 "그분")
- **어려운 사주 용어 절대 금지**: 격국·십성·일간·용신·천간·지지·비견·식신·상관·재성·관성·인성·오행·음양·신강·신약·득령·실령
- 분석 데이터는 근거로만 참고하고, 결과만 일상적인 말로
- 마크다운 헤더 대신 자연스러운 단락. 항목 구분 필요하면 **굵게**만
- 미신적·운명결정론적 단정 금지, "그런 경향이 있어요" 식

# 풀이에 담을 내용 (자연스럽게 연결)
1. 두 분이 처음 만나면 어떤 느낌인지 (서로의 첫인상·매력)
2. 잘 맞는 부분 — 어떤 점에서 시너지가 나는지
3. 부딪칠 수 있는 부분 — 서로 다른 기질·가치관
4. 의사소통할 때 주의할 점 — 구체적으로 (예: "${호칭}이 직설적으로 말하면 ${partnerName}은 상처받을 수 있어요" 같은 톤)
5. 이 관계가 오래 가려면 무엇이 필요한지
${concern && concern.trim() ? `6. ${호칭}의 고민("${concern.trim()}")에 대한 구체적이고 따뜻한 조언` : ''}

# 분량
${concern && concern.trim() ? '1800~2300자' : '1500~2000자'} 정도, 너무 길지 않게.`;
}

/**
 * 꿈 해몽용 프롬프트 생성
 *  동양 전통 해몽(주공해몽·한국 민간 해몽) + 융 심리학 결합
 */
function buildDreamPrompt(dreamText) {
  return `당신은 동양 전통 해몽학(주공해몽·한국 민간 해몽·이븐 시린)과 융(Jung) 심리학적 꿈 해석에 모두 능통한 해몽 전문가입니다.

# 꿈 내용
"${dreamText.trim()}"

# 해몽 작성 가이드
- 한국어 존댓말, 마크다운 형식
- 다음 구조로 작성:
  1. **꿈의 핵심 상징** — 등장한 주요 인물·동물·사물·장소·색깔·숫자가 상징하는 바를 짚어주기
  2. **동양 전통 해몽** — 주공해몽·한국 민간 해몽 기준의 길흉 판단. 태몽 가능성이 있으면 짚어주기
  3. **융(Jung) 심리학적 해석** — 원형(Archetype)·그림자·아니마/아니무스·집단무의식 관점에서 무의식이 보내는 메시지
  4. **종합 메시지** — 이 꿈이 꿈꾼 사람의 현재 심리·생활·관계에 시사하는 바
  5. **실생활 조언** — 이 꿈을 어떻게 받아들이고 무엇에 주의·노력하면 좋을지 (구체적이고 실용적으로)
- 미신적·운명결정론적 단정은 피하고, 가능성·경향성으로 표현
- 부정적 상징도 솔직히 다루되, 그것이 의미하는 심리적 과제·성장 기회로 재해석
- 1000~1500자 내외`;
}

/**
 * 간단한 마크다운 → HTML 변환 (헤더·볼드·줄바꿈만 처리)
 */
function simpleMarkdown(md) {
  let html = window.HtmlUtils.escapeHtml(md)
  .replace(/^### (.+)$/gm, '<h4>$1</h4>')
  .replace(/^## (.+)$/gm, '<h3>$1</h3>')
  .replace(/^# (.+)$/gm, '<h2>$1</h2>')
  .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
  .replace(/\*(.+?)\*/g, '<i>$1</i>')
  .replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>')
  .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
  .replace(/\n\n/g, '</p><p>')
  .replace(/\n/g, '<br>');
  return `<p>${html}</p>`;
}

// ── 외부 모듈 (saju-engine.js) 끝 — body 인라인 script 접근용 window 노출 ──
// 별도 <script> 태그라 top-level 식별자가 자동 글로벌 안 됨 → 명시 노출.
Object.assign(window, {
  // 데이터 const
  천간, 천간_한자, 지지, 지지_한자,
  천간_오행, 지지_오행, 천간_음양, 지지_음양,
  오행명, 오행_한자, 오행_색깔,
  지지_장간, 절_정보, 절기_24, 오호둔, 오서둔,
  십성명, 십이운성_장생, 십이운성명, 십이신살명, 십이신살_시작,
  // 천문 const
  DEG, RAD, norm360, toRad, toDeg,
  // SECTION 2 함수
  toJD, jdFromLocal, fromJD, localFromJD,
  sunApparentLongitude, obliquity, equationOfTime, findSunLongitudeJD, calcSolarTerms,
  // SECTION 3
  dayPillarIndex, calculateSaju,
  // SECTION 4
  analyzeSaju, gzIdx, getSipsung, get12Unseong, get12Shinsal,
  // SECTION 5
  calculateDaewoon, calculateSewoon,
  // SECTION 6
  generateInterpretation, 해석_일간, 해석_십성, 해석_격국, 해석_12운성, 해석_12신살,
  // SECTION 7
  buildSajuPrompt, buildDreamPrompt, buildCompatPrompt, buildPersonSummary,
  callFreeAI, simpleMarkdown,
});
