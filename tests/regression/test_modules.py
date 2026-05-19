"""ADR-046 회귀 테스트 — 외부 모듈 로딩 + window 노출 (ADR-037~045 검증)."""


def test_core_globals(page):
    """core JS 모듈 (LLMUtils·BaseReader·HtmlUtils·FaceVisualizations) 로드."""
    assert page.evaluate("typeof window.LLMUtils === 'object'")
    assert page.evaluate("typeof window.LLMUtils.fetchWithRetry === 'function'")
    assert page.evaluate("typeof window.LLMUtils.postJSON === 'function'")
    assert page.evaluate("typeof window.LLMUtils.downsampleDataUrl === 'function'")
    assert page.evaluate("typeof window.BaseReader === 'function'")
    assert page.evaluate("typeof window.HtmlUtils === 'object'")
    assert page.evaluate("typeof window.HtmlUtils.escapeHtml === 'function'")
    assert page.evaluate("typeof window.FaceVisualizations === 'object'")
    assert page.evaluate("typeof window.FaceVisualizations.renderVisualizations === 'function'")


def test_saju_engine(page):
    """saju-engine.js — 사주 데이터·계산·해석 글로벌 노출."""
    assert page.evaluate("typeof window.SAJU === 'object'")
    assert page.evaluate("typeof window.SAJU.calculateSaju === 'function'")
    assert page.evaluate("typeof window.SAJU.analyzeSaju === 'function'")
    assert page.evaluate("typeof window.SAJU.simpleMarkdown === 'function'")
    assert page.evaluate("Array.isArray(window.SAJU.천간_한자) && window.SAJU.천간_한자.length === 10")
    assert page.evaluate("typeof window.callFreeAI === 'function'")
    assert page.evaluate("typeof window.simpleMarkdown === 'function'")


def test_name_engine(page):
    """name-engine.js — 한자 데이터 + 성명학 함수 글로벌 노출."""
    assert page.evaluate("typeof window['한자획수'] === 'object'")
    assert page.evaluate("typeof window['한자_뜻'] === 'object'")
    assert page.evaluate("typeof window['한글음_한자'] === 'object'")
    assert page.evaluate("typeof window.splitName === 'function'")
    assert page.evaluate("typeof window.analyzeName === 'function'")


def test_readers(page):
    """3 Reader (Face·Palm·Name) class 인스턴스 + persona."""
    assert page.evaluate("window.faceReader?.persona === '운학 도사'")
    assert page.evaluate("window.palmReader?.persona === '옥선 할미'")
    assert page.evaluate("window.nameReader?.persona === '묵향 선생'")


def test_dream_reader(page):
    """Dream Reader 외부 모듈 (ADR-042)."""
    assert page.evaluate("typeof window.DreamReader === 'object'")
    assert page.evaluate("typeof window.DreamReader.onDreamSubmit === 'function'")
    assert page.evaluate("typeof window.DreamReader.renderDreamResultV2 === 'function'")
    # mock render
    out_len = page.evaluate("""() => {
      const data = { text: '꿈에서 하늘을 날았어요', agent_meta: {}, domain_analysis_summary: {} };
      return window.DreamReader.renderDreamResultV2(data).length;
    }""")
    assert out_len > 500


def test_hwapae_dom(page):
    """Hwapae 외부 모듈 (ADR-042) — DOM 요소 존재."""
    assert page.evaluate("!!document.getElementById('hwapaeGoToDrawBtn')")
    assert page.evaluate("!!document.getElementById('hwapaeDeck')")
    assert page.evaluate("document.querySelectorAll('.hw-menu-btn').length === 4")
    assert page.evaluate("document.querySelectorAll('.hw-cat-btn').length === 8")


def test_calculate_saju_execution(page):
    """calculateSaju 실 실행 검증 — 1990-05-15 14:30 KST."""
    result = page.evaluate("""() => {
      return window.SAJU.calculateSaju({
        year: 1990, month: 5, day: 15,
        hour: 14, minute: 30, second: 0,
        tzOffsetHours: 9,
      });
    }""")
    assert isinstance(result, dict)
    assert "pillars" in result
    assert "meta" in result
    p = result["pillars"]
    assert "year" in p and "month" in p and "day" in p and "time" in p
    # 1990 경오년 (year stem 6=庚, branch 6=午)
    assert p["year"]["stem"] == 6
    assert p["year"]["branch"] == 6
    # 24절기 boundaries 12개
    assert len(result["meta"]["boundaries"]) == 12


def test_name_hanja_selector(page):
    """name reader 한자 셀렉터 자동 생성 — '홍길동' → 3 셀."""
    page.evaluate("""() => {
      const inp = document.getElementById('nameFullKo');
      if (inp) { inp.value = '홍길동'; inp.dispatchEvent(new Event('input', {bubbles:true})); }
    }""")
    import time as _time
    _time.sleep(0.5)
    count = page.evaluate("document.querySelectorAll('#nameHanjaSelectors .hanja-cell').length")
    assert count == 3


def test_html_utils_xss(page):
    """HtmlUtils.escapeHtml XSS 방어."""
    escaped = page.evaluate("window.HtmlUtils.escapeHtml('<script>alert(1)</script>')")
    assert "&lt;script&gt;" in escaped
    assert "<script>" not in escaped


def test_css_loaded(page):
    """외부 CSS (main.css) 로드 + --gold 변수."""
    val = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--gold').trim()")
    assert val  # non-empty


def test_no_page_errors(page):
    """페이지 로드 중 console.error / pageerror 0건."""
    errs = page.errors  # type: ignore[attr-defined]
    # mp4·wav 영상 ERR_ABORTED는 브라우저 종료 시 자연 발생 — pageerror만 검사
    page_errs = [e for e in errs if e.startswith("pageerror:") or e.startswith("console.error:")]
    assert page_errs == [], f"unexpected errors: {page_errs}"
