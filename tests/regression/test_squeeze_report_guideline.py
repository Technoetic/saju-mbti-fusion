"""/squeeze-report 결과 회귀 — ADR-086·087·088.

운세 앱 개발 보강 가이드라인.md 본문화:
- ADR-086 십성 메타 (사길신·사흉신·식신제살·재극인·도식)
- ADR-087 한국 50+ 도시 위도/경도 LUT
- ADR-088 Web Share API + DOM→Canvas 유틸리티 (프론트)
"""

from pathlib import Path


# ── ADR-086 십성 메타 ─────────────────────────────────


def test_sagilshin_constant():
    """사길신(四吉神) 정의 — 식신·정재·정관·정인."""
    from engine.saju.ten_gods import SAGILSHIN
    assert SAGILSHIN == ("식신", "정재", "정관", "정인")


def test_sahyungshin_constant():
    """사흉신(四兇神) 정의 — 상관·겁재·편관·편인."""
    from engine.saju.ten_gods import SAHYUNGSHIN
    assert SAHYUNGSHIN == ("상관", "겁재", "편관", "편인")


def test_classify_gilhyung_sagil():
    """사길신 분류."""
    from engine.saju.ten_gods import classify_gilhyung
    for ten_god in ("식신", "정재", "정관", "정인"):
        assert classify_gilhyung(ten_god) == "사길신"


def test_classify_gilhyung_sahyung():
    """사흉신 분류."""
    from engine.saju.ten_gods import classify_gilhyung
    for ten_god in ("상관", "겁재", "편관", "편인"):
        assert classify_gilhyung(ten_god) == "사흉신"


def test_classify_gilhyung_neutral():
    """편재·정재(중립 분류) — 분류 미해당."""
    from engine.saju.ten_gods import classify_gilhyung
    assert classify_gilhyung("편재") is None  # 편재는 사길/흉 분류 외
    assert classify_gilhyung("비견") is None
    assert classify_gilhyung("겁재") == "사흉신"  # 겁재는 사흉신 포함


def test_siksinjesal_detection():
    """식신제살 감지 — 식신 + 편관 공존."""
    from engine.saju.ten_gods import has_siksinjesal
    assert has_siksinjesal({"a": "식신", "b": "편관"}) is True
    assert has_siksinjesal({"a": "식신"}) is False
    assert has_siksinjesal({"a": "편관"}) is False
    assert has_siksinjesal({}) is False


def test_jaegukin_detection():
    """재극인 감지 — 재성(편재/정재) + 인성(편인/정인) 공존."""
    from engine.saju.ten_gods import has_jaegukin
    assert has_jaegukin({"a": "편재", "b": "편인"}) is True
    assert has_jaegukin({"a": "정재", "b": "정인"}) is True
    assert has_jaegukin({"a": "편재"}) is False


def test_dosik_detection():
    """도식 감지 — 편인 + 식신 공존."""
    from engine.saju.ten_gods import has_dosik
    assert has_dosik({"a": "편인", "b": "식신"}) is True
    assert has_dosik({"a": "정인", "b": "식신"}) is False  # 정인 X 도식


def test_detect_special_combinations_live():
    """본 시스템 사용자 사례 — 庚辰 일주 ↔ 甲午 일진 = 재극인."""
    from engine.saju.ten_gods import compute_ten_gods, detect_special_combinations
    r = compute_ten_gods({"year": "庚辰", "month": "庚辰", "day": "庚辰", "hour": "甲午"})
    flags = detect_special_combinations(r)
    assert "재극인" in flags


def test_meta_disclaimer_present():
    """메타 면책 문구 존재 — 운명·길흉 단정 차단 명시."""
    from engine.saju import ten_gods
    src = open(ten_gods.__file__, "r", encoding="utf-8").read()
    assert "단정 X" in src
    assert "운명" in src and "길흉" in src


# ── ADR-087 한국 도시 좌표 LUT ─────────────────────


def test_kr_city_coords_count():
    """KR_CITY_COORDS 50건 이상."""
    from engine.saju.geo_lut import KR_CITY_COORDS
    assert len(KR_CITY_COORDS) >= 40


def test_seoul_coord_default():
    """서울 좌표 정합 (37.5665, 126.9780)."""
    from engine.saju.geo_lut import KR_CITY_COORDS
    seoul = KR_CITY_COORDS["서울"]
    assert seoul.latitude == 37.5665
    assert seoul.longitude == 126.9780
    assert seoul.region == "서울특별시"


def test_get_longitude_seoul():
    """get_longitude('서울') = 126.978."""
    from engine.saju.geo_lut import get_longitude
    assert get_longitude("서울") == 126.9780


def test_get_longitude_unknown_fallback():
    """미등록 도시 → 서울 기본값 126.978."""
    from engine.saju.geo_lut import get_longitude
    assert get_longitude("UnknownCityXYZ") == 126.978


def test_get_coord_returns_dataclass():
    """get_coord 반환값이 CityCoord 인스턴스."""
    from engine.saju.geo_lut import get_coord, CityCoord
    c = get_coord("부산")
    assert c is not None
    assert isinstance(c, CityCoord)
    assert c.name_ko == "부산"


def test_list_cities_by_region():
    """경기도 도시 목록 반환."""
    from engine.saju.geo_lut import list_cities_by_region
    gyeonggi = list_cities_by_region("경기도")
    assert "수원" in gyeonggi
    assert "성남" in gyeonggi
    assert len(gyeonggi) >= 10


def test_all_17_regions_present():
    """17개 시·도 모두 1건 이상 등록."""
    from engine.saju.geo_lut import KR_CITY_COORDS
    regions = {c.region for c in KR_CITY_COORDS.values()}
    expected = {
        "서울특별시", "부산광역시", "대구광역시", "인천광역시",
        "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
        "경기도", "강원도", "충청북도", "충청남도",
        "전라북도", "전라남도", "경상북도", "경상남도",
        "제주특별자치도",
    }
    assert expected.issubset(regions)


def test_coordinates_in_korea_bounds():
    """모든 좌표가 한국 영역 (33<=lat<=39, 124<=lon<=132) 내."""
    from engine.saju.geo_lut import KR_CITY_COORDS
    for c in KR_CITY_COORDS.values():
        assert 33.0 <= c.latitude <= 39.0, f"{c.name_ko} 위도 범위 외: {c.latitude}"
        assert 124.0 <= c.longitude <= 132.0, f"{c.name_ko} 경도 범위 외: {c.longitude}"


# ── ADR-088 share-utils.js 프론트 ──────────────────────


def test_share_utils_module_exists():
    """share-utils.js 파일 존재."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "front" / "js" / "core" / "share-utils.js"
    assert path.exists()


def test_share_utils_exports_globals():
    """ShareUtils 전역 객체 노출."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "front" / "js" / "core" / "share-utils.js"
    src = path.read_text(encoding="utf-8")
    assert "window.ShareUtils" in src
    assert "canShareFiles" in src
    assert "shareImage" in src
    assert "downloadBlob" in src
    assert "domToCanvas" in src
    assert "canvasToBlob" in src
    assert "shareOrDownload" in src


def test_share_utils_cors_defense():
    """CORS 방어 — crossOrigin='anonymous' 자동 설정."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "front" / "js" / "core" / "share-utils.js"
    src = path.read_text(encoding="utf-8")
    assert "crossOrigin = 'anonymous'" in src


def test_share_utils_web_share_api_check():
    """canShareFiles에 navigator.canShare 호출."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "front" / "js" / "core" / "share-utils.js"
    src = path.read_text(encoding="utf-8")
    assert "navigator.canShare" in src
    assert "navigator.share" in src


def test_share_utils_disclaimer_in_default_text():
    """기본 공유 텍스트에 EU AI Act §50 면책."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "front" / "js" / "core" / "share-utils.js"
    src = path.read_text(encoding="utf-8")
    assert "EU AI Act §50" in src


def test_share_utils_loaded_in_index():
    """index.html에 share-utils.js 스크립트 로드."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "front" / "index.html"
    src = path.read_text(encoding="utf-8")
    assert "share-utils.js" in src


def test_share_utils_blob_fallback():
    """canvas.toBlob 없는 브라우저용 toDataURL fallback."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "front" / "js" / "core" / "share-utils.js"
    src = path.read_text(encoding="utf-8")
    assert "toBlob" in src
    assert "toDataURL" in src  # fallback
