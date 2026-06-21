"""ADR-072 회귀 — 결정론 엔진 실 필드 정합 검증.

ADR-070 'BaleumReport.score' 가짜 속성 → 실 필드 (grade·reason·ohaeng_sequence)
+ compute_ten_gods 입력 형식 정정 검증.
"""

from pathlib import Path
import dataclasses

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_PY = ROOT / "web" / "server.py"


def _src() -> str:
    """server.py + web/handlers/*.py + web/schemas.py 합본 소스.

    핸들러 메서드가 web/server.py → web/handlers/ Mixin 으로 물리 분리되고
    (구조 리팩터링, 동작 불변), 요청 모델이 web/schemas.py 로 이동했으므로,
    핸들러 본문/모델 정의를 grep 하는 검사가 어느 파일에 있든 통과하도록
    합본 텍스트를 반환한다. 라우트 등록(_register_routes)·핸들러명 검사는
    server.py 만으로도 통과하며 합본에도 당연히 포함된다.
    """
    parts = [SERVER_PY.read_text(encoding="utf-8")]
    hdir = ROOT / "web" / "handlers"
    if hdir.is_dir():
        for p in sorted(hdir.glob("*.py")):
            parts.append(p.read_text(encoding="utf-8"))
    schemas = ROOT / "web" / "schemas.py"
    if schemas.is_file():
        parts.append(schemas.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_baleum_report_actual_fields():
    """BaleumReport 실 dataclass 필드 — syllables·ohaeng_sequence·relations·grade·reason."""
    from engine.divination.name.baleum import BaleumReport
    fields = {f.name for f in dataclasses.fields(BaleumReport)}
    assert "grade" in fields
    assert "reason" in fields
    assert "ohaeng_sequence" in fields
    # 'score' 필드는 존재하지 않음 — ADR-070 가짜 속성 회수
    assert "score" not in fields


def test_server_uses_actual_baleum_fields():
    """server.py가 BaleumReport.grade·reason·ohaeng_sequence 인용."""
    src = _src()
    assert 'getattr(baleum_report, "grade"' in src
    assert 'getattr(baleum_report, "reason"' in src
    assert 'getattr(baleum_report, "ohaeng_sequence"' in src


def test_server_no_fake_score_attribute():
    """server.py에 'baleum_report, score' 잘못된 호출 부재."""
    src = _src()
    # 이전 ADR-070 패턴 잔존 차단
    assert 'getattr(baleum_report, "score"' not in src
    assert "baleum_report.score" not in src


def test_baleum_block_includes_grade():
    """결정론 블록에 등급·사유 명시."""
    src = _src()
    assert "음 조화 등급" in src
    assert "평가 사유" in src
    assert "음절 오행 흐름" in src


def test_compute_ten_gods_correct_input_format():
    """compute_ten_gods 입력 형식 정정 — {'year':'甲子',...} 문자열."""
    src = _src()
    # 이전 잘못된 dict 형식 잔존 X
    assert '"year_pillar": user_day_pillar' not in src
    assert '"hour_pillar": today_pillar_data' not in src
    # 정정된 형식 (문자열 갑자)
    assert '"year": user_gz' in src
    assert '"hour": today_gz' in src


def test_ten_gods_uses_hour_gan_and_ji():
    """천간 + 지지 두 십성 모두 인용 (이전 hour_gan만 사용)."""
    src = _src()
    assert 'ten_gods_data.get("hour_gan"' in src
    assert 'ten_gods_data.get("hour_ji"' in src


def test_tengod_label_format():
    """십성 라벨 — '천간 X·지지 Y' 형식 또는 (미산출)."""
    src = _src()
    assert "천간" in src and "지지" in src
    assert "(미산출)" in src


def test_baleum_real_output_for_홍길동():
    """실 호출 — 홍길동의 grade는 'bad', ohaeng_sequence는 ['토','목','화']."""
    from engine.divination.name.baleum import evaluate_baleum
    br = evaluate_baleum("홍길동", include_jongsung=False)
    assert br.grade == "bad"
    assert br.ohaeng_sequence == ["토", "목", "화"]
    assert "상극" in br.reason or "충돌" in br.reason


def test_day_pillar_for_1990_05_15():
    """결정론 day_pillar(1990,5,15) → 庚辰 (KASI 공식 회신, ADR-085)."""
    from engine.saju.pillars import day_pillar
    p = day_pillar(1990, 5, 15)
    assert p["gan"] == "경"
    assert p["ji"] == "진"
    assert p["gan_han"] == "庚"
    assert p["ji_han"] == "辰"


def test_compute_ten_gods_with_string_input():
    """compute_ten_gods 문자열 입력 형식 — 본 시스템 사용 패턴 정합."""
    from engine.saju.ten_gods import compute_ten_gods
    result = compute_ten_gods({
        "year": "乙巳", "month": "乙巳", "day": "乙巳", "hour": "己未",
    })
    # day_master = '乙' (을목)
    # hour_gan = '己' (기토) → 을목 입장 십성
    assert "hour_gan" in result
    assert result["hour_gan"]  # 빈 문자열 X
