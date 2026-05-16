"""대운(Luck Cycle) 계산 모듈.

월주(月柱)의 천간/지지를 기준으로 10년 단위 대운을 순행 또는 역행으로 산출한다.

순행 조건: 양남(양년 + 남자) 또는 음녀(음년 + 여자)
역행 조건: 음남(음년 + 남자) 또는 양녀(양년 + 여자)

시작 나이는 절기까지의 일수를 3으로 나눈 값(간이 공식)이며,
일수 정보가 없을 경우 기본값 8세를 사용한다. (정확 계산은 후속 Step)
"""

from __future__ import annotations

GAN_LIST = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI_LIST = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 양간(양년): 갑, 병, 무, 경, 임 (짝수 인덱스 0,2,4,6,8)
YANG_GAN = {"甲", "丙", "戊", "庚", "壬"}

# 한자 -> 한글 매핑 (대운 표기용)
GAN_HANGUL = {
    "甲": "갑",
    "乙": "을",
    "丙": "병",
    "丁": "정",
    "戊": "무",
    "己": "기",
    "庚": "경",
    "辛": "신",
    "壬": "임",
    "癸": "계",
}
JI_HANGUL = {
    "子": "자",
    "丑": "축",
    "寅": "인",
    "卯": "묘",
    "辰": "진",
    "巳": "사",
    "午": "오",
    "未": "미",
    "申": "신",
    "酉": "유",
    "戌": "술",
    "亥": "해",
}


def _is_forward(year_gan_han: str, gender: str) -> bool:
    """순행 여부 판정.

    - 양남(양년 + 남): 순행
    - 음녀(음년 + 여): 순행
    - 음남, 양녀: 역행
    """
    is_yang_year = year_gan_han in YANG_GAN
    is_male = gender.lower() in ("m", "male", "남", "남자")
    return (is_yang_year and is_male) or (not is_yang_year and not is_male)


def _start_age(days_to_jeolgi: int | None) -> int:
    """시작 나이 계산 (간이 공식: 일수 / 3). 정보 없을 시 기본 8세."""
    if days_to_jeolgi is None:
        return 8
    age = days_to_jeolgi // 3
    return max(1, age)


def compute_luck_cycle(
    year_gan_han: str,
    gender: str,
    month_gan_han: str,
    month_ji_han: str,
    count: int = 8,
    days_to_jeolgi: int | None = None,
) -> list[dict]:
    """대운 산출.

    Args:
        year_gan_han: 연주 천간 (한자, 예: "甲")
        gender: 성별 ("M"/"F"/"남"/"여" 등)
        month_gan_han: 월주 천간 (한자)
        month_ji_han: 월주 지지 (한자)
        count: 산출할 대운 개수 (기본 8개 = 80년)
        days_to_jeolgi: 절기까지의 일수 (없으면 기본 8세 시작)

    Returns:
        [{start_age, ganzhi, gan, ji}, ...] count 개
    """
    if month_gan_han not in GAN_LIST:
        raise ValueError(f"Invalid month_gan_han: {month_gan_han}")
    if month_ji_han not in JI_LIST:
        raise ValueError(f"Invalid month_ji_han: {month_ji_han}")

    forward = _is_forward(year_gan_han, gender)
    direction = 1 if forward else -1
    start_age = _start_age(days_to_jeolgi)

    gan_idx = GAN_LIST.index(month_gan_han)
    ji_idx = JI_LIST.index(month_ji_han)

    cycles: list[dict] = []
    for i in range(count):
        # 첫 대운은 월주 다음 간지부터 시작 (i=0 -> direction 1칸 이동)
        step = i + 1
        g_idx = (gan_idx + direction * step) % 10
        j_idx = (ji_idx + direction * step) % 12
        gan = GAN_LIST[g_idx]
        ji = JI_LIST[j_idx]
        gan_kr = GAN_HANGUL[gan]
        ji_kr = JI_HANGUL[ji]
        ganzhi = f"{gan_kr}{ji_kr}({gan}{ji})"
        cycles.append(
            {
                "start_age": start_age + i * 10,
                "ganzhi": ganzhi,
                "gan": gan,
                "ji": ji,
            }
        )
    return cycles


__all__ = ["compute_luck_cycle", "GAN_LIST", "JI_LIST"]
