"""인명용 한자 데이터 — 자주 쓰이는 약 350자.

각 한자: {
  "han": 한자,
  "ko": 한글 음,
  "strokes": 강희자전 원획수 (원획법),
  "wuxing": 자원오행 (목/화/토/금/수),
  "meaning": 짧은 뜻,
}

원획법: 부수의 원형을 기준으로 획수를 셈 (성명학 표준).
  - 삼수변 氵 = 4획 (水 부수)
  - 심방변 忄 = 4획 (心 부수)
  - 초두머리 艹 = 6획 (艸 부수)
  - 책받침 辶 = 4획 (辵 부수, 한 점 빠짐 시에도)
  - 칼도방 刂 = 2획 (刀 부수)
  - 손수변 扌 = 4획 (手 부수)
  - 옥부수 王/玉 = 5획 (玉 부수)
  - 보일시 礻 = 5획 (示 부수)
  - 옷의변 衤 = 6획 (衣 부수)
  - 그물머리 罒 = 6획 (网 부수)
  - 늙을로 耂 = 6획 (老 부수)
  - 책받침 辶 = 7획 (辵 부수)
  - 무릎병절 卩 = 2획
  - 사람인변 亻 = 2획
  - 흰개수 犭 = 4획 (犬 부수)
숫자 한자 특례: 一=1, 二=2, 三=3, 四=4, 五=5, 六=6, 七=7, 八=8, 九=9, 十=10
  (강희자전 원획)


자원오행은 강희자전 부수 기준 한국 성명학 표준:
  목 = 木,竹,艹,禾,米,糸 등 식물/실/이삭
  화 = 火,日,光,赤,丁 등 불/빛
  토 = 土,山,石,田,阜,玉 등 흙/돌/땅
  금 = 金,刀,斤,玉(보석),戈,矢 등 쇠/도구
  수 = 水,氵,雨,川,魚,舟 등 물/배
  (혼합 부수는 가장 강한 뜻 우선)
"""

from __future__ import annotations

HANJA_LIST: list[dict] = [
    # 성씨 (자주)
    {"han": "金", "ko": "김", "strokes": 8, "wuxing": "금", "meaning": "쇠"},
    {"han": "李", "ko": "이", "strokes": 7, "wuxing": "목", "meaning": "자두나무"},
    {"han": "朴", "ko": "박", "strokes": 6, "wuxing": "목", "meaning": "후박나무"},
    {"han": "崔", "ko": "최", "strokes": 11, "wuxing": "토", "meaning": "산이 높음"},
    {"han": "鄭", "ko": "정", "strokes": 19, "wuxing": "화", "meaning": "정중"},
    {"han": "姜", "ko": "강", "strokes": 9, "wuxing": "토", "meaning": "성씨"},
    {"han": "趙", "ko": "조", "strokes": 14, "wuxing": "화", "meaning": "성씨"},
    {"han": "尹", "ko": "윤", "strokes": 4, "wuxing": "토", "meaning": "다스리다"},
    {"han": "張", "ko": "장", "strokes": 11, "wuxing": "금", "meaning": "활을 당기다"},
    {"han": "林", "ko": "임", "strokes": 8, "wuxing": "목", "meaning": "수풀"},
    {"han": "韓", "ko": "한", "strokes": 17, "wuxing": "수", "meaning": "나라"},
    {"han": "吳", "ko": "오", "strokes": 7, "wuxing": "목", "meaning": "큰소리"},
    {"han": "申", "ko": "신", "strokes": 5, "wuxing": "금", "meaning": "거듭하다"},
    {"han": "權", "ko": "권", "strokes": 22, "wuxing": "목", "meaning": "저울"},
    {"han": "黃", "ko": "황", "strokes": 12, "wuxing": "토", "meaning": "누렇다"},
    {"han": "安", "ko": "안", "strokes": 6, "wuxing": "토", "meaning": "편안"},
    {"han": "宋", "ko": "송", "strokes": 7, "wuxing": "금", "meaning": "성씨"},
    {"han": "柳", "ko": "유", "strokes": 9, "wuxing": "목", "meaning": "버드나무"},
    {"han": "洪", "ko": "홍", "strokes": 10, "wuxing": "수", "meaning": "큰물"},
    {"han": "全", "ko": "전", "strokes": 6, "wuxing": "토", "meaning": "온전"},
    {"han": "高", "ko": "고", "strokes": 10, "wuxing": "화", "meaning": "높다"},
    {"han": "文", "ko": "문", "strokes": 4, "wuxing": "수", "meaning": "글"},
    {"han": "孫", "ko": "손", "strokes": 10, "wuxing": "금", "meaning": "손자"},
    {"han": "梁", "ko": "양", "strokes": 11, "wuxing": "목", "meaning": "들보"},
    {"han": "裵", "ko": "배", "strokes": 14, "wuxing": "수", "meaning": "성씨"},
    {"han": "白", "ko": "백", "strokes": 5, "wuxing": "금", "meaning": "흰빛"},
    {"han": "曺", "ko": "조", "strokes": 11, "wuxing": "화", "meaning": "관청"},
    {"han": "許", "ko": "허", "strokes": 11, "wuxing": "토", "meaning": "허락"},
    {"han": "南", "ko": "남", "strokes": 9, "wuxing": "화", "meaning": "남쪽"},
    {"han": "沈", "ko": "심", "strokes": 8, "wuxing": "수", "meaning": "가라앉다"},
    {"han": "盧", "ko": "노", "strokes": 16, "wuxing": "화", "meaning": "검다"},
    {"han": "河", "ko": "하", "strokes": 9, "wuxing": "수", "meaning": "큰 강"},

    # 이름용 — 가나다순 자주 쓰는 한자
    {"han": "嘉", "ko": "가", "strokes": 14, "wuxing": "화", "meaning": "아름다움"},
    {"han": "佳", "ko": "가", "strokes": 8, "wuxing": "토", "meaning": "아름답다"},
    {"han": "歌", "ko": "가", "strokes": 14, "wuxing": "수", "meaning": "노래"},
    {"han": "可", "ko": "가", "strokes": 5, "wuxing": "수", "meaning": "옳다"},

    {"han": "康", "ko": "강", "strokes": 11, "wuxing": "목", "meaning": "편안"},
    {"han": "綱", "ko": "강", "strokes": 14, "wuxing": "목", "meaning": "벼리"},
    {"han": "剛", "ko": "강", "strokes": 10, "wuxing": "금", "meaning": "굳세다"},

    {"han": "建", "ko": "건", "strokes": 9, "wuxing": "목", "meaning": "세우다"},
    {"han": "健", "ko": "건", "strokes": 11, "wuxing": "목", "meaning": "튼튼함"},

    {"han": "京", "ko": "경", "strokes": 8, "wuxing": "토", "meaning": "서울"},
    {"han": "敬", "ko": "경", "strokes": 13, "wuxing": "금", "meaning": "공경"},
    {"han": "慶", "ko": "경", "strokes": 15, "wuxing": "목", "meaning": "경사"},
    {"han": "炅", "ko": "경", "strokes": 8, "wuxing": "화", "meaning": "빛나다"},

    {"han": "高", "ko": "고", "strokes": 10, "wuxing": "화", "meaning": "높다"},
    {"han": "古", "ko": "고", "strokes": 5, "wuxing": "수", "meaning": "옛"},

    {"han": "光", "ko": "광", "strokes": 6, "wuxing": "화", "meaning": "빛"},
    {"han": "廣", "ko": "광", "strokes": 15, "wuxing": "목", "meaning": "넓다"},

    {"han": "求", "ko": "구", "strokes": 7, "wuxing": "수", "meaning": "구하다"},
    {"han": "九", "ko": "구", "strokes": 2, "wuxing": "수", "meaning": "아홉"},
    {"han": "具", "ko": "구", "strokes": 8, "wuxing": "목", "meaning": "갖추다"},

    {"han": "君", "ko": "군", "strokes": 7, "wuxing": "수", "meaning": "임금"},

    {"han": "貴", "ko": "귀", "strokes": 12, "wuxing": "목", "meaning": "귀하다"},

    {"han": "圭", "ko": "규", "strokes": 6, "wuxing": "토", "meaning": "홀"},
    {"han": "奎", "ko": "규", "strokes": 9, "wuxing": "토", "meaning": "별"},

    {"han": "根", "ko": "근", "strokes": 10, "wuxing": "목", "meaning": "뿌리"},
    {"han": "謹", "ko": "근", "strokes": 17, "wuxing": "금", "meaning": "삼가다"},

    {"han": "起", "ko": "기", "strokes": 10, "wuxing": "토", "meaning": "일어나다"},
    {"han": "基", "ko": "기", "strokes": 11, "wuxing": "토", "meaning": "터"},
    {"han": "麒", "ko": "기", "strokes": 19, "wuxing": "토", "meaning": "기린"},
    {"han": "紀", "ko": "기", "strokes": 9, "wuxing": "목", "meaning": "벼리"},

    {"han": "吉", "ko": "길", "strokes": 6, "wuxing": "수", "meaning": "길하다"},
    {"han": "桔", "ko": "길", "strokes": 10, "wuxing": "목", "meaning": "도라지"},

    {"han": "南", "ko": "남", "strokes": 9, "wuxing": "화", "meaning": "남쪽"},
    {"han": "男", "ko": "남", "strokes": 7, "wuxing": "토", "meaning": "사내"},

    {"han": "乃", "ko": "내", "strokes": 2, "wuxing": "화", "meaning": "이에"},

    {"han": "魯", "ko": "노", "strokes": 15, "wuxing": "수", "meaning": "노둔하다"},

    {"han": "達", "ko": "달", "strokes": 13, "wuxing": "토", "meaning": "통하다"},

    {"han": "大", "ko": "대", "strokes": 3, "wuxing": "목", "meaning": "크다"},
    {"han": "代", "ko": "대", "strokes": 5, "wuxing": "화", "meaning": "대신하다"},

    {"han": "德", "ko": "덕", "strokes": 15, "wuxing": "화", "meaning": "덕"},

    {"han": "道", "ko": "도", "strokes": 13, "wuxing": "토", "meaning": "길"},
    {"han": "桃", "ko": "도", "strokes": 10, "wuxing": "목", "meaning": "복숭아"},
    {"han": "都", "ko": "도", "strokes": 11, "wuxing": "화", "meaning": "도읍"},
    {"han": "圖", "ko": "도", "strokes": 14, "wuxing": "토", "meaning": "그림"},

    {"han": "東", "ko": "동", "strokes": 8, "wuxing": "목", "meaning": "동쪽"},
    {"han": "童", "ko": "동", "strokes": 12, "wuxing": "금", "meaning": "아이"},
    {"han": "棟", "ko": "동", "strokes": 12, "wuxing": "목", "meaning": "용마루"},
    {"han": "桐", "ko": "동", "strokes": 10, "wuxing": "목", "meaning": "오동나무"},

    {"han": "斗", "ko": "두", "strokes": 4, "wuxing": "화", "meaning": "말"},

    {"han": "良", "ko": "량/양", "strokes": 7, "wuxing": "토", "meaning": "좋다"},

    {"han": "麗", "ko": "려", "strokes": 19, "wuxing": "수", "meaning": "곱다"},

    {"han": "蓮", "ko": "련/연", "strokes": 17, "wuxing": "목", "meaning": "연꽃"},

    {"han": "龍", "ko": "룡/용", "strokes": 16, "wuxing": "토", "meaning": "용"},
    {"han": "勇", "ko": "용", "strokes": 9, "wuxing": "토", "meaning": "용감"},
    {"han": "容", "ko": "용", "strokes": 10, "wuxing": "토", "meaning": "얼굴"},

    {"han": "理", "ko": "리/이", "strokes": 11, "wuxing": "금", "meaning": "이치"},
    {"han": "利", "ko": "리/이", "strokes": 7, "wuxing": "금", "meaning": "이롭다"},

    {"han": "明", "ko": "명", "strokes": 8, "wuxing": "화", "meaning": "밝다"},
    {"han": "命", "ko": "명", "strokes": 8, "wuxing": "수", "meaning": "목숨"},
    {"han": "銘", "ko": "명", "strokes": 14, "wuxing": "금", "meaning": "새기다"},

    {"han": "茂", "ko": "무", "strokes": 11, "wuxing": "목", "meaning": "무성"},
    {"han": "武", "ko": "무", "strokes": 8, "wuxing": "금", "meaning": "굳세다"},

    {"han": "美", "ko": "미", "strokes": 9, "wuxing": "토", "meaning": "아름답다"},
    {"han": "敏", "ko": "민", "strokes": 11, "wuxing": "수", "meaning": "민첩"},
    {"han": "民", "ko": "민", "strokes": 5, "wuxing": "수", "meaning": "백성"},
    {"han": "玟", "ko": "민", "strokes": 8, "wuxing": "금", "meaning": "옥돌"},
    {"han": "珉", "ko": "민", "strokes": 9, "wuxing": "금", "meaning": "옥돌"},

    {"han": "博", "ko": "박", "strokes": 12, "wuxing": "수", "meaning": "넓다"},

    {"han": "範", "ko": "범", "strokes": 15, "wuxing": "목", "meaning": "법"},
    {"han": "凡", "ko": "범", "strokes": 3, "wuxing": "수", "meaning": "무릇"},

    {"han": "炳", "ko": "병", "strokes": 9, "wuxing": "화", "meaning": "빛나다"},
    {"han": "丙", "ko": "병", "strokes": 5, "wuxing": "화", "meaning": "남녘"},

    {"han": "甫", "ko": "보", "strokes": 7, "wuxing": "수", "meaning": "크다"},
    {"han": "寶", "ko": "보", "strokes": 20, "wuxing": "금", "meaning": "보배"},
    {"han": "輔", "ko": "보", "strokes": 14, "wuxing": "화", "meaning": "돕다"},

    {"han": "福", "ko": "복", "strokes": 14, "wuxing": "금", "meaning": "복"},

    {"han": "鳳", "ko": "봉", "strokes": 14, "wuxing": "수", "meaning": "봉황"},

    {"han": "夫", "ko": "부", "strokes": 4, "wuxing": "목", "meaning": "지아비"},

    {"han": "賓", "ko": "빈", "strokes": 14, "wuxing": "수", "meaning": "손님"},
    {"han": "彬", "ko": "빈", "strokes": 11, "wuxing": "목", "meaning": "빛나다"},

    {"han": "士", "ko": "사", "strokes": 3, "wuxing": "금", "meaning": "선비"},
    {"han": "思", "ko": "사", "strokes": 9, "wuxing": "금", "meaning": "생각"},
    {"han": "史", "ko": "사", "strokes": 5, "wuxing": "금", "meaning": "역사"},

    {"han": "尙", "ko": "상", "strokes": 8, "wuxing": "금", "meaning": "오히려"},
    {"han": "祥", "ko": "상", "strokes": 11, "wuxing": "금", "meaning": "상서"},
    {"han": "想", "ko": "상", "strokes": 13, "wuxing": "금", "meaning": "생각"},
    {"han": "上", "ko": "상", "strokes": 3, "wuxing": "금", "meaning": "위"},

    {"han": "瑞", "ko": "서", "strokes": 14, "wuxing": "금", "meaning": "상서롭다"},
    {"han": "書", "ko": "서", "strokes": 10, "wuxing": "화", "meaning": "글"},
    {"han": "西", "ko": "서", "strokes": 6, "wuxing": "금", "meaning": "서쪽"},
    {"han": "敍", "ko": "서", "strokes": 9, "wuxing": "금", "meaning": "차례"},

    {"han": "錫", "ko": "석", "strokes": 16, "wuxing": "금", "meaning": "주석"},
    {"han": "碩", "ko": "석", "strokes": 14, "wuxing": "토", "meaning": "크다"},
    {"han": "石", "ko": "석", "strokes": 5, "wuxing": "토", "meaning": "돌"},
    {"han": "奭", "ko": "석", "strokes": 15, "wuxing": "토", "meaning": "성하다"},

    {"han": "宣", "ko": "선", "strokes": 9, "wuxing": "금", "meaning": "베풀다"},
    {"han": "善", "ko": "선", "strokes": 12, "wuxing": "수", "meaning": "착하다"},
    {"han": "鮮", "ko": "선", "strokes": 17, "wuxing": "수", "meaning": "곱다"},
    {"han": "璿", "ko": "선", "strokes": 18, "wuxing": "금", "meaning": "옥"},

    {"han": "成", "ko": "성", "strokes": 7, "wuxing": "화", "meaning": "이루다"},
    {"han": "聖", "ko": "성", "strokes": 13, "wuxing": "화", "meaning": "성인"},
    {"han": "星", "ko": "성", "strokes": 9, "wuxing": "화", "meaning": "별"},
    {"han": "性", "ko": "성", "strokes": 9, "wuxing": "금", "meaning": "성품"},
    {"han": "省", "ko": "성", "strokes": 9, "wuxing": "금", "meaning": "살피다"},

    {"han": "世", "ko": "세", "strokes": 5, "wuxing": "금", "meaning": "세대"},

    {"han": "昭", "ko": "소", "strokes": 9, "wuxing": "화", "meaning": "밝다"},
    {"han": "素", "ko": "소", "strokes": 10, "wuxing": "목", "meaning": "본디"},
    {"han": "炤", "ko": "소", "strokes": 9, "wuxing": "화", "meaning": "밝다"},

    {"han": "秀", "ko": "수", "strokes": 7, "wuxing": "목", "meaning": "빼어나다"},
    {"han": "壽", "ko": "수", "strokes": 14, "wuxing": "수", "meaning": "수명"},
    {"han": "洙", "ko": "수", "strokes": 10, "wuxing": "수", "meaning": "물가"},
    {"han": "守", "ko": "수", "strokes": 6, "wuxing": "토", "meaning": "지키다"},

    {"han": "淑", "ko": "숙", "strokes": 12, "wuxing": "수", "meaning": "맑다"},

    {"han": "順", "ko": "순", "strokes": 12, "wuxing": "금", "meaning": "순하다"},
    {"han": "純", "ko": "순", "strokes": 10, "wuxing": "목", "meaning": "순수"},
    {"han": "舜", "ko": "순", "strokes": 12, "wuxing": "금", "meaning": "임금"},

    {"han": "勝", "ko": "승", "strokes": 12, "wuxing": "토", "meaning": "이기다"},
    {"han": "昇", "ko": "승", "strokes": 8, "wuxing": "화", "meaning": "오르다"},

    {"han": "始", "ko": "시", "strokes": 8, "wuxing": "토", "meaning": "처음"},
    {"han": "詩", "ko": "시", "strokes": 13, "wuxing": "금", "meaning": "시"},

    {"han": "信", "ko": "신", "strokes": 9, "wuxing": "금", "meaning": "믿다"},
    {"han": "新", "ko": "신", "strokes": 13, "wuxing": "금", "meaning": "새롭다"},
    {"han": "辛", "ko": "신", "strokes": 7, "wuxing": "금", "meaning": "맵다"},

    {"han": "兒", "ko": "아", "strokes": 8, "wuxing": "화", "meaning": "아이"},
    {"han": "亞", "ko": "아", "strokes": 8, "wuxing": "토", "meaning": "버금"},
    {"han": "雅", "ko": "아", "strokes": 12, "wuxing": "목", "meaning": "맑다"},

    {"han": "安", "ko": "안", "strokes": 6, "wuxing": "토", "meaning": "편안"},
    {"han": "顔", "ko": "안", "strokes": 18, "wuxing": "목", "meaning": "얼굴"},

    {"han": "陽", "ko": "양", "strokes": 17, "wuxing": "토", "meaning": "볕"},
    {"han": "洋", "ko": "양", "strokes": 10, "wuxing": "수", "meaning": "바다"},

    {"han": "彦", "ko": "언", "strokes": 9, "wuxing": "목", "meaning": "선비"},

    {"han": "妍", "ko": "연", "strokes": 9, "wuxing": "토", "meaning": "곱다"},
    {"han": "硏", "ko": "연", "strokes": 11, "wuxing": "토", "meaning": "갈다"},
    {"han": "演", "ko": "연", "strokes": 14, "wuxing": "수", "meaning": "펴다"},
    {"han": "燕", "ko": "연", "strokes": 16, "wuxing": "화", "meaning": "제비"},
    {"han": "蓮", "ko": "연", "strokes": 17, "wuxing": "목", "meaning": "연꽃"},

    {"han": "永", "ko": "영", "strokes": 5, "wuxing": "수", "meaning": "길다"},
    {"han": "英", "ko": "영", "strokes": 11, "wuxing": "목", "meaning": "꽃부리"},
    {"han": "榮", "ko": "영", "strokes": 14, "wuxing": "목", "meaning": "영화"},
    {"han": "瑛", "ko": "영", "strokes": 13, "wuxing": "금", "meaning": "옥빛"},

    {"han": "睿", "ko": "예", "strokes": 14, "wuxing": "토", "meaning": "슬기"},
    {"han": "藝", "ko": "예", "strokes": 21, "wuxing": "목", "meaning": "재주"},

    {"han": "吾", "ko": "오", "strokes": 7, "wuxing": "수", "meaning": "나"},
    {"han": "梧", "ko": "오", "strokes": 11, "wuxing": "목", "meaning": "오동"},

    {"han": "玉", "ko": "옥", "strokes": 5, "wuxing": "금", "meaning": "구슬"},

    {"han": "完", "ko": "완", "strokes": 7, "wuxing": "토", "meaning": "완전"},

    {"han": "雨", "ko": "우", "strokes": 8, "wuxing": "수", "meaning": "비"},
    {"han": "宇", "ko": "우", "strokes": 6, "wuxing": "토", "meaning": "집"},
    {"han": "祐", "ko": "우", "strokes": 10, "wuxing": "금", "meaning": "돕다"},
    {"han": "佑", "ko": "우", "strokes": 7, "wuxing": "토", "meaning": "돕다"},
    {"han": "牛", "ko": "우", "strokes": 4, "wuxing": "토", "meaning": "소"},

    {"han": "旭", "ko": "욱", "strokes": 6, "wuxing": "화", "meaning": "햇빛"},
    {"han": "煜", "ko": "욱", "strokes": 13, "wuxing": "화", "meaning": "빛나다"},

    {"han": "雲", "ko": "운", "strokes": 12, "wuxing": "수", "meaning": "구름"},

    {"han": "元", "ko": "원", "strokes": 4, "wuxing": "목", "meaning": "으뜸"},
    {"han": "源", "ko": "원", "strokes": 14, "wuxing": "수", "meaning": "근원"},
    {"han": "圓", "ko": "원", "strokes": 13, "wuxing": "토", "meaning": "둥글다"},
    {"han": "苑", "ko": "원", "strokes": 11, "wuxing": "목", "meaning": "동산"},

    {"han": "月", "ko": "월", "strokes": 4, "wuxing": "수", "meaning": "달"},

    {"han": "渭", "ko": "위", "strokes": 13, "wuxing": "수", "meaning": "물"},

    {"han": "有", "ko": "유", "strokes": 6, "wuxing": "토", "meaning": "있다"},
    {"han": "裕", "ko": "유", "strokes": 13, "wuxing": "목", "meaning": "넉넉"},
    {"han": "潤", "ko": "윤", "strokes": 16, "wuxing": "수", "meaning": "윤택"},
    {"han": "胤", "ko": "윤", "strokes": 9, "wuxing": "수", "meaning": "이을"},

    {"han": "恩", "ko": "은", "strokes": 10, "wuxing": "토", "meaning": "은혜"},
    {"han": "銀", "ko": "은", "strokes": 14, "wuxing": "금", "meaning": "은"},

    {"han": "義", "ko": "의", "strokes": 13, "wuxing": "금", "meaning": "옳다"},

    {"han": "二", "ko": "이", "strokes": 2, "wuxing": "화", "meaning": "둘"},
    {"han": "伊", "ko": "이", "strokes": 6, "wuxing": "토", "meaning": "저"},
    {"han": "怡", "ko": "이", "strokes": 9, "wuxing": "수", "meaning": "기쁘다"},

    {"han": "仁", "ko": "인", "strokes": 4, "wuxing": "금", "meaning": "어질다"},
    {"han": "印", "ko": "인", "strokes": 6, "wuxing": "수", "meaning": "도장"},
    {"han": "因", "ko": "인", "strokes": 6, "wuxing": "수", "meaning": "원인"},

    {"han": "日", "ko": "일", "strokes": 4, "wuxing": "화", "meaning": "날"},
    {"han": "一", "ko": "일", "strokes": 1, "wuxing": "토", "meaning": "한"},
    {"han": "逸", "ko": "일", "strokes": 15, "wuxing": "토", "meaning": "편안"},

    {"han": "壬", "ko": "임", "strokes": 4, "wuxing": "수", "meaning": "북녘"},
    {"han": "任", "ko": "임", "strokes": 6, "wuxing": "화", "meaning": "맡기다"},

    {"han": "子", "ko": "자", "strokes": 3, "wuxing": "수", "meaning": "아들"},
    {"han": "字", "ko": "자", "strokes": 6, "wuxing": "토", "meaning": "글자"},

    {"han": "在", "ko": "재", "strokes": 6, "wuxing": "토", "meaning": "있다"},
    {"han": "宰", "ko": "재", "strokes": 10, "wuxing": "토", "meaning": "재상"},
    {"han": "栽", "ko": "재", "strokes": 10, "wuxing": "목", "meaning": "심다"},
    {"han": "材", "ko": "재", "strokes": 7, "wuxing": "목", "meaning": "재목"},
    {"han": "載", "ko": "재", "strokes": 13, "wuxing": "금", "meaning": "싣다"},

    {"han": "貞", "ko": "정", "strokes": 9, "wuxing": "금", "meaning": "곧다"},
    {"han": "正", "ko": "정", "strokes": 5, "wuxing": "토", "meaning": "바르다"},
    {"han": "靜", "ko": "정", "strokes": 16, "wuxing": "금", "meaning": "고요"},
    {"han": "情", "ko": "정", "strokes": 11, "wuxing": "금", "meaning": "정"},
    {"han": "晶", "ko": "정", "strokes": 12, "wuxing": "화", "meaning": "맑다"},
    {"han": "廷", "ko": "정", "strokes": 7, "wuxing": "화", "meaning": "조정"},
    {"han": "汀", "ko": "정", "strokes": 5, "wuxing": "수", "meaning": "물가"},

    {"han": "濟", "ko": "제", "strokes": 17, "wuxing": "수", "meaning": "건너다"},

    {"han": "祚", "ko": "조", "strokes": 9, "wuxing": "금", "meaning": "복"},
    {"han": "助", "ko": "조", "strokes": 7, "wuxing": "토", "meaning": "돕다"},
    {"han": "朝", "ko": "조", "strokes": 12, "wuxing": "수", "meaning": "아침"},

    {"han": "鍾", "ko": "종", "strokes": 17, "wuxing": "금", "meaning": "쇠북"},
    {"han": "宗", "ko": "종", "strokes": 8, "wuxing": "토", "meaning": "마루"},

    {"han": "周", "ko": "주", "strokes": 8, "wuxing": "수", "meaning": "두루"},
    {"han": "柱", "ko": "주", "strokes": 9, "wuxing": "목", "meaning": "기둥"},
    {"han": "珠", "ko": "주", "strokes": 11, "wuxing": "금", "meaning": "구슬"},
    {"han": "晝", "ko": "주", "strokes": 11, "wuxing": "화", "meaning": "낮"},

    {"han": "俊", "ko": "준", "strokes": 9, "wuxing": "화", "meaning": "준걸"},
    {"han": "峻", "ko": "준", "strokes": 10, "wuxing": "토", "meaning": "높다"},
    {"han": "濬", "ko": "준", "strokes": 17, "wuxing": "수", "meaning": "깊다"},

    {"han": "重", "ko": "중", "strokes": 9, "wuxing": "화", "meaning": "무겁다"},

    {"han": "智", "ko": "지", "strokes": 12, "wuxing": "화", "meaning": "지혜"},
    {"han": "志", "ko": "지", "strokes": 7, "wuxing": "화", "meaning": "뜻"},
    {"han": "至", "ko": "지", "strokes": 6, "wuxing": "토", "meaning": "이르다"},
    {"han": "枝", "ko": "지", "strokes": 8, "wuxing": "목", "meaning": "가지"},
    {"han": "知", "ko": "지", "strokes": 8, "wuxing": "금", "meaning": "알다"},

    {"han": "鎭", "ko": "진", "strokes": 18, "wuxing": "금", "meaning": "진정"},
    {"han": "眞", "ko": "진", "strokes": 10, "wuxing": "금", "meaning": "참"},
    {"han": "進", "ko": "진", "strokes": 12, "wuxing": "화", "meaning": "나아가다"},
    {"han": "辰", "ko": "진", "strokes": 7, "wuxing": "토", "meaning": "별"},
    {"han": "璡", "ko": "진", "strokes": 16, "wuxing": "금", "meaning": "옥"},

    {"han": "燦", "ko": "찬", "strokes": 17, "wuxing": "화", "meaning": "빛나다"},
    {"han": "讚", "ko": "찬", "strokes": 26, "wuxing": "금", "meaning": "기리다"},
    {"han": "燁", "ko": "엽", "strokes": 16, "wuxing": "화", "meaning": "빛나다"},

    {"han": "昌", "ko": "창", "strokes": 8, "wuxing": "화", "meaning": "성하다"},
    {"han": "暢", "ko": "창", "strokes": 14, "wuxing": "화", "meaning": "통하다"},

    {"han": "天", "ko": "천", "strokes": 4, "wuxing": "화", "meaning": "하늘"},
    {"han": "千", "ko": "천", "strokes": 3, "wuxing": "금", "meaning": "일천"},

    {"han": "哲", "ko": "철", "strokes": 10, "wuxing": "화", "meaning": "밝다"},
    {"han": "鐵", "ko": "철", "strokes": 21, "wuxing": "금", "meaning": "쇠"},

    {"han": "靑", "ko": "청", "strokes": 8, "wuxing": "목", "meaning": "푸르다"},
    {"han": "淸", "ko": "청", "strokes": 11, "wuxing": "수", "meaning": "맑다"},

    {"han": "草", "ko": "초", "strokes": 12, "wuxing": "목", "meaning": "풀"},

    {"han": "秋", "ko": "추", "strokes": 9, "wuxing": "목", "meaning": "가을"},

    {"han": "春", "ko": "춘", "strokes": 9, "wuxing": "화", "meaning": "봄"},

    {"han": "忠", "ko": "충", "strokes": 8, "wuxing": "화", "meaning": "충성"},

    {"han": "致", "ko": "치", "strokes": 10, "wuxing": "화", "meaning": "이르다"},

    {"han": "卓", "ko": "탁", "strokes": 8, "wuxing": "화", "meaning": "높다"},

    {"han": "太", "ko": "태", "strokes": 4, "wuxing": "수", "meaning": "크다"},
    {"han": "泰", "ko": "태", "strokes": 9, "wuxing": "수", "meaning": "크다"},

    {"han": "澤", "ko": "택", "strokes": 17, "wuxing": "수", "meaning": "못"},

    {"han": "波", "ko": "파", "strokes": 9, "wuxing": "수", "meaning": "물결"},

    {"han": "平", "ko": "평", "strokes": 5, "wuxing": "목", "meaning": "평평"},

    {"han": "豊", "ko": "풍", "strokes": 13, "wuxing": "목", "meaning": "풍성"},

    {"han": "夏", "ko": "하", "strokes": 10, "wuxing": "화", "meaning": "여름"},
    {"han": "賀", "ko": "하", "strokes": 12, "wuxing": "수", "meaning": "축하"},
    {"han": "河", "ko": "하", "strokes": 9, "wuxing": "수", "meaning": "강"},

    {"han": "翰", "ko": "한", "strokes": 16, "wuxing": "수", "meaning": "글"},
    {"han": "漢", "ko": "한", "strokes": 15, "wuxing": "수", "meaning": "한나라"},

    {"han": "海", "ko": "해", "strokes": 11, "wuxing": "수", "meaning": "바다"},

    {"han": "革", "ko": "혁", "strokes": 9, "wuxing": "목", "meaning": "가죽"},
    {"han": "赫", "ko": "혁", "strokes": 14, "wuxing": "화", "meaning": "빛나다"},

    {"han": "賢", "ko": "현", "strokes": 15, "wuxing": "금", "meaning": "어질다"},
    {"han": "顯", "ko": "현", "strokes": 23, "wuxing": "화", "meaning": "드러나다"},
    {"han": "炫", "ko": "현", "strokes": 9, "wuxing": "화", "meaning": "빛나다"},
    {"han": "弦", "ko": "현", "strokes": 8, "wuxing": "토", "meaning": "줄"},

    {"han": "亨", "ko": "형", "strokes": 7, "wuxing": "토", "meaning": "통하다"},
    {"han": "炯", "ko": "형", "strokes": 9, "wuxing": "화", "meaning": "밝다"},
    {"han": "馨", "ko": "형", "strokes": 20, "wuxing": "토", "meaning": "향기"},

    {"han": "好", "ko": "호", "strokes": 6, "wuxing": "수", "meaning": "좋다"},
    {"han": "浩", "ko": "호", "strokes": 11, "wuxing": "수", "meaning": "넓다"},
    {"han": "晧", "ko": "호", "strokes": 11, "wuxing": "화", "meaning": "밝다"},
    {"han": "豪", "ko": "호", "strokes": 14, "wuxing": "수", "meaning": "호걸"},
    {"han": "湖", "ko": "호", "strokes": 13, "wuxing": "수", "meaning": "호수"},
    {"han": "皓", "ko": "호", "strokes": 12, "wuxing": "금", "meaning": "희다"},

    {"han": "弘", "ko": "홍", "strokes": 5, "wuxing": "토", "meaning": "크다"},
    {"han": "鴻", "ko": "홍", "strokes": 17, "wuxing": "수", "meaning": "기러기"},

    {"han": "和", "ko": "화", "strokes": 8, "wuxing": "수", "meaning": "화목"},
    {"han": "華", "ko": "화", "strokes": 14, "wuxing": "목", "meaning": "빛나다"},
    {"han": "花", "ko": "화", "strokes": 10, "wuxing": "목", "meaning": "꽃"},

    {"han": "桓", "ko": "환", "strokes": 10, "wuxing": "목", "meaning": "굳세다"},
    {"han": "煥", "ko": "환", "strokes": 13, "wuxing": "화", "meaning": "빛나다"},

    {"han": "回", "ko": "회", "strokes": 6, "wuxing": "수", "meaning": "돌아오다"},
    {"han": "會", "ko": "회", "strokes": 13, "wuxing": "수", "meaning": "모이다"},

    {"han": "孝", "ko": "효", "strokes": 7, "wuxing": "수", "meaning": "효도"},

    {"han": "勳", "ko": "훈", "strokes": 16, "wuxing": "화", "meaning": "공"},
    {"han": "薰", "ko": "훈", "strokes": 20, "wuxing": "목", "meaning": "향기"},

    {"han": "輝", "ko": "휘", "strokes": 15, "wuxing": "화", "meaning": "빛나다"},

    {"han": "熙", "ko": "희", "strokes": 13, "wuxing": "화", "meaning": "빛나다"},
    {"han": "喜", "ko": "희", "strokes": 12, "wuxing": "수", "meaning": "기쁘다"},
    {"han": "姬", "ko": "희", "strokes": 9, "wuxing": "토", "meaning": "여자"},

    {"han": "化", "ko": "화", "strokes": 4, "wuxing": "화", "meaning": "되다"},

    {"han": "東", "ko": "동", "strokes": 8, "wuxing": "목", "meaning": "동쪽"},
    {"han": "未", "ko": "미", "strokes": 5, "wuxing": "목", "meaning": "아니다"},
    {"han": "民", "ko": "민", "strokes": 5, "wuxing": "수", "meaning": "백성"},
    {"han": "旼", "ko": "민", "strokes": 8, "wuxing": "화", "meaning": "화락"},

    {"han": "潭", "ko": "담", "strokes": 16, "wuxing": "수", "meaning": "못"},

    # 추가 — 벤치마크/자주 쓰이는 한자
    {"han": "秉", "ko": "병", "strokes": 8, "wuxing": "목", "meaning": "잡다"},
    {"han": "喆", "ko": "철", "strokes": 12, "wuxing": "수", "meaning": "밝다"},
    {"han": "竹", "ko": "죽", "strokes": 6, "wuxing": "목", "meaning": "대"},
    {"han": "鎬", "ko": "호", "strokes": 18, "wuxing": "금", "meaning": "냄비"},
    {"han": "燮", "ko": "섭", "strokes": 17, "wuxing": "화", "meaning": "화락"},
    {"han": "倫", "ko": "륜/윤", "strokes": 10, "wuxing": "화", "meaning": "인륜"},
    {"han": "瑟", "ko": "슬", "strokes": 14, "wuxing": "금", "meaning": "큰 거문고"},
    {"han": "瑩", "ko": "영", "strokes": 15, "wuxing": "금", "meaning": "옥빛"},
    {"han": "畵", "ko": "화", "strokes": 13, "wuxing": "토", "meaning": "그림"},
    {"han": "娥", "ko": "아", "strokes": 10, "wuxing": "토", "meaning": "예쁘다"},
    {"han": "煕", "ko": "희", "strokes": 13, "wuxing": "화", "meaning": "빛나다"},
    {"han": "禧", "ko": "희", "strokes": 17, "wuxing": "금", "meaning": "복"},
    {"han": "羲", "ko": "희", "strokes": 16, "wuxing": "토", "meaning": "복희씨"},

    # Phase 2 추가 — 자주 쓰이는 인명용 한자 60자
    {"han": "嬉", "ko": "희", "strokes": 15, "wuxing": "토", "meaning": "놀다·즐기다"},
    {"han": "犧", "ko": "희", "strokes": 20, "wuxing": "토", "meaning": "희생"},

    {"han": "歡", "ko": "환", "strokes": 22, "wuxing": "금", "meaning": "기뻐하다"},
    {"han": "晥", "ko": "환", "strokes": 11, "wuxing": "화", "meaning": "환하다"},

    {"han": "勳", "ko": "훈", "strokes": 16, "wuxing": "화", "meaning": "공로"},
    {"han": "壎", "ko": "훈", "strokes": 17, "wuxing": "토", "meaning": "질나발"},

    {"han": "翰", "ko": "한", "strokes": 16, "wuxing": "수", "meaning": "글·붓"},
    {"han": "瀚", "ko": "한", "strokes": 20, "wuxing": "수", "meaning": "광대한 물"},

    {"han": "燁", "ko": "엽/엿", "strokes": 16, "wuxing": "화", "meaning": "빛나다"},
    {"han": "曄", "ko": "엽", "strokes": 16, "wuxing": "화", "meaning": "빛나다"},

    {"han": "圭", "ko": "규", "strokes": 6, "wuxing": "토", "meaning": "홀"},
    {"han": "珪", "ko": "규", "strokes": 10, "wuxing": "금", "meaning": "옥"},
    {"han": "揆", "ko": "규", "strokes": 13, "wuxing": "목", "meaning": "헤아리다"},
    {"han": "硅", "ko": "규", "strokes": 11, "wuxing": "토", "meaning": "규소"},

    {"han": "槿", "ko": "근", "strokes": 15, "wuxing": "목", "meaning": "무궁화"},
    {"han": "瑾", "ko": "근", "strokes": 16, "wuxing": "금", "meaning": "옥"},

    {"han": "曦", "ko": "희", "strokes": 20, "wuxing": "화", "meaning": "햇빛"},

    {"han": "煐", "ko": "영", "strokes": 13, "wuxing": "화", "meaning": "사람 이름"},
    {"han": "暎", "ko": "영", "strokes": 13, "wuxing": "화", "meaning": "비추다"},
    {"han": "瑛", "ko": "영", "strokes": 13, "wuxing": "금", "meaning": "옥빛"},

    {"han": "玗", "ko": "우", "strokes": 7, "wuxing": "금", "meaning": "옥돌"},
    {"han": "侑", "ko": "유", "strokes": 8, "wuxing": "화", "meaning": "권하다"},
    {"han": "宥", "ko": "유", "strokes": 9, "wuxing": "토", "meaning": "용서"},
    {"han": "誘", "ko": "유", "strokes": 14, "wuxing": "금", "meaning": "이끌다"},
    {"han": "悠", "ko": "유", "strokes": 11, "wuxing": "수", "meaning": "유유"},

    {"han": "津", "ko": "진", "strokes": 10, "wuxing": "수", "meaning": "나루"},

    {"han": "栗", "ko": "율/률", "strokes": 10, "wuxing": "목", "meaning": "밤"},
    {"han": "律", "ko": "율/률", "strokes": 9, "wuxing": "화", "meaning": "법"},
    {"han": "玏", "ko": "륵/늑", "strokes": 7, "wuxing": "금", "meaning": "옥돌"},

    {"han": "汎", "ko": "범", "strokes": 7, "wuxing": "수", "meaning": "넓다"},

    {"han": "靈", "ko": "령/영", "strokes": 24, "wuxing": "수", "meaning": "신령"},

    {"han": "玹", "ko": "현", "strokes": 10, "wuxing": "금", "meaning": "옥돌"},
    {"han": "賢", "ko": "현", "strokes": 15, "wuxing": "금", "meaning": "어질다"},
    {"han": "鉉", "ko": "현", "strokes": 13, "wuxing": "금", "meaning": "솥귀"},

    {"han": "炎", "ko": "염", "strokes": 8, "wuxing": "화", "meaning": "불꽃"},
    {"han": "艶", "ko": "염", "strokes": 24, "wuxing": "토", "meaning": "고와"},

    {"han": "蘭", "ko": "란", "strokes": 23, "wuxing": "목", "meaning": "난초"},

    {"han": "晟", "ko": "성", "strokes": 11, "wuxing": "화", "meaning": "밝다"},
    {"han": "宬", "ko": "성", "strokes": 10, "wuxing": "토", "meaning": "도서관"},

    {"han": "鏞", "ko": "용", "strokes": 19, "wuxing": "금", "meaning": "큰종"},
    {"han": "鎔", "ko": "용", "strokes": 18, "wuxing": "금", "meaning": "녹이다"},

    {"han": "渙", "ko": "환", "strokes": 13, "wuxing": "수", "meaning": "흩어지다"},

    {"han": "祿", "ko": "록", "strokes": 13, "wuxing": "금", "meaning": "녹·복록"},

    {"han": "煇", "ko": "휘", "strokes": 13, "wuxing": "화", "meaning": "빛"},
    {"han": "暉", "ko": "휘", "strokes": 13, "wuxing": "화", "meaning": "햇빛"},

    {"han": "曉", "ko": "효", "strokes": 16, "wuxing": "화", "meaning": "새벽"},

    {"han": "彬", "ko": "빈", "strokes": 11, "wuxing": "목", "meaning": "빛나다"},
    {"han": "斌", "ko": "빈", "strokes": 12, "wuxing": "수", "meaning": "빛나다"},

    {"han": "聲", "ko": "성", "strokes": 17, "wuxing": "금", "meaning": "소리"},

    {"han": "灝", "ko": "호", "strokes": 25, "wuxing": "수", "meaning": "넓다"},
    {"han": "晧", "ko": "호", "strokes": 11, "wuxing": "화", "meaning": "밝다"},

    {"han": "雲", "ko": "운", "strokes": 12, "wuxing": "수", "meaning": "구름"},
    {"han": "韻", "ko": "운", "strokes": 19, "wuxing": "금", "meaning": "운치"},

    {"han": "詠", "ko": "영", "strokes": 12, "wuxing": "금", "meaning": "읊다"},

    {"han": "祺", "ko": "기", "strokes": 13, "wuxing": "금", "meaning": "복"},
    {"han": "琪", "ko": "기", "strokes": 13, "wuxing": "금", "meaning": "옥"},

    {"han": "藝", "ko": "예", "strokes": 21, "wuxing": "목", "meaning": "재주"},
    {"han": "汭", "ko": "예", "strokes": 8, "wuxing": "수", "meaning": "물굽이"},

    {"han": "敦", "ko": "돈", "strokes": 12, "wuxing": "금", "meaning": "도탑다"},

    {"han": "采", "ko": "채", "strokes": 8, "wuxing": "목", "meaning": "캐다"},
    {"han": "彩", "ko": "채", "strokes": 11, "wuxing": "화", "meaning": "채색"},

    {"han": "睿", "ko": "예", "strokes": 14, "wuxing": "토", "meaning": "슬기롭다"},

    {"han": "嬿", "ko": "연", "strokes": 19, "wuxing": "토", "meaning": "예쁘다"},

    {"han": "凜", "ko": "름/늠", "strokes": 15, "wuxing": "수", "meaning": "씩씩하다"},

    {"han": "夢", "ko": "몽", "strokes": 14, "wuxing": "목", "meaning": "꿈"},

    # 추가 — 사용자 요청 한자
    {"han": "田", "ko": "전", "strokes": 5, "wuxing": "토", "meaning": "밭"},
    {"han": "紋", "ko": "문", "strokes": 10, "wuxing": "목", "meaning": "무늬"},
    {"han": "㒞", "ko": "준", "strokes": 12, "wuxing": "화", "meaning": "뛰어나다"},
    {"han": "寯", "ko": "준", "strokes": 16, "wuxing": "토", "meaning": "모일·영재"},

    # 추가 — 같은 음 인명용 한자 보강
    {"han": "錢", "ko": "전", "strokes": 16, "wuxing": "금", "meaning": "돈"},
    {"han": "鈿", "ko": "전", "strokes": 13, "wuxing": "금", "meaning": "비녀"},
    {"han": "典", "ko": "전", "strokes": 8, "wuxing": "금", "meaning": "법"},
    {"han": "佺", "ko": "전", "strokes": 8, "wuxing": "화", "meaning": "신선"},
    {"han": "悛", "ko": "전", "strokes": 11, "wuxing": "수", "meaning": "고치다"},

    {"han": "汶", "ko": "문", "strokes": 8, "wuxing": "수", "meaning": "물"},
    {"han": "雯", "ko": "문", "strokes": 12, "wuxing": "수", "meaning": "구름무늬"},
    {"han": "聞", "ko": "문", "strokes": 14, "wuxing": "수", "meaning": "듣다"},
    {"han": "問", "ko": "문", "strokes": 11, "wuxing": "수", "meaning": "묻다"},
    {"han": "門", "ko": "문", "strokes": 8, "wuxing": "목", "meaning": "문"},

    {"han": "埈", "ko": "준", "strokes": 10, "wuxing": "토", "meaning": "높다"},
    {"han": "雋", "ko": "준", "strokes": 13, "wuxing": "수", "meaning": "뛰어나다"},
    {"han": "晙", "ko": "준", "strokes": 11, "wuxing": "화", "meaning": "밝다"},
    {"han": "焌", "ko": "준", "strokes": 11, "wuxing": "화", "meaning": "타다"},
    {"han": "竣", "ko": "준", "strokes": 12, "wuxing": "토", "meaning": "마치다"},
    {"han": "駿", "ko": "준", "strokes": 17, "wuxing": "화", "meaning": "준마"},
]


# 한글 음 → 해당 음의 한자 후보 리스트
def candidates_by_ko(ko: str) -> list[dict]:
    """주어진 한글 음에 해당하는 모든 후보 한자."""
    if not ko:
        return []
    ko = ko.strip()
    out = []
    seen = set()
    for entry in HANJA_LIST:
        # 다중 음 (예: "량/양", "리/이") 지원
        kos = [k.strip() for k in entry["ko"].split("/")]
        if ko in kos and entry["han"] not in seen:
            out.append(entry)
            seen.add(entry["han"])
    return out


def lookup_han(han: str) -> dict | None:
    """한자 1글자 → 데이터 (없으면 None)."""
    for entry in HANJA_LIST:
        if entry["han"] == han:
            return entry
    return None


__all__ = ["HANJA_LIST", "candidates_by_ko", "lookup_han"]
