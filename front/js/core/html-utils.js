/**
 * window.HtmlUtils — HTML 이스케이프·렌더링 공용 유틸 (ADR-038 Phase 2 확장)
 *  - escapeHtml(s): &, <, > 이스케이프 (가장 자주 쓰는 4중 패턴 통합)
 *  - escapeAttr(s): " 추가 이스케이프 (attribute 안전)
 *  - pct01(v): 0~1 값을 0~100% 정수로 (face-viz _pct와 통일)
 *
 * 본 모듈은 face·name·palm·hwapae·dream 등 모든 reader가 공유.
 * 코드 중복 4곳(.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')) 통합.
 */
(function(){
  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, '&quot;');
  }
  function pct01(v) {
    return Math.max(0, Math.min(100, Math.round(Number(v || 0) * 100)));
  }
  window.HtmlUtils = { escapeHtml, escapeAttr, pct01 };
})();
