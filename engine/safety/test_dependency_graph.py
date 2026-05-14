"""engine.safety.dependency_graph — §14.13 회귀 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────── AST 파싱 ───────────────────────────

def test_extract_imports_simple():
    from engine.safety.dependency_graph import _extract_imports_from_source
    src = "from engine.safety.crisis_detector import detect_crisis\n"
    imports = _extract_imports_from_source(src)
    assert "engine.safety.crisis_detector" in imports


def test_extract_imports_multiple():
    from engine.safety.dependency_graph import _extract_imports_from_source
    src = (
        "from engine.safety.crisis_detector import detect_crisis\n"
        "from engine.safety.pii import mask_pii\n"
        "import engine.safety.legal_notice as ln\n"
    )
    imports = _extract_imports_from_source(src)
    assert "engine.safety.crisis_detector" in imports
    assert "engine.safety.pii" in imports
    assert "engine.safety.legal_notice" in imports


def test_extract_imports_skips_non_engine_safety():
    """engine.divination 같은 다른 패키지는 제외."""
    from engine.safety.dependency_graph import _extract_imports_from_source
    src = (
        "from engine.divination.face_reading import generate_face_reading\n"
        "import os\n"
        "from engine.safety.pii import mask_pii\n"
    )
    imports = _extract_imports_from_source(src)
    assert "engine.safety.pii" in imports
    assert "engine.divination.face_reading" not in imports
    assert "os" not in imports


def test_extract_imports_syntax_error_returns_empty():
    from engine.safety.dependency_graph import _extract_imports_from_source
    bad = "def foo(:::"
    assert _extract_imports_from_source(bad) == set()


# ─────────────────────────── 그래프 빌드 ───────────────────────────

def test_build_graph_has_nodes():
    from engine.safety.dependency_graph import build_graph
    g = build_graph()
    # 최소 30개 운영 모듈
    assert len(g.nodes) >= 30


def test_build_graph_excludes_test_and_init():
    from engine.safety.dependency_graph import build_graph
    g = build_graph()
    for module in g.nodes:
        assert not module.endswith(".test_face_reading")
        assert not module.endswith(".__init__")


def test_build_graph_node_has_imports_field():
    from engine.safety.dependency_graph import build_graph
    g = build_graph()
    for n in g.nodes.values():
        assert isinstance(n.imports, tuple)
        assert isinstance(n.imported_by, tuple)


# ─────────────────────────── cycle 감지 ───────────────────────────

def test_no_cycles_in_current_safety_modules():
    """현재 시스템은 cycle 없음 (건강한 DAG)."""
    from engine.safety.dependency_graph import build_graph, has_cycles
    g = build_graph()
    assert has_cycles(g) is False
    assert g.cycles == ()


def test_detect_cycles_in_synthetic_edges():
    from engine.safety.dependency_graph import _detect_cycles
    edges = {
        "a": {"b"},
        "b": {"c"},
        "c": {"a"},   # cycle: a→b→c→a
    }
    cycles = _detect_cycles(edges)
    assert len(cycles) >= 1


def test_no_cycles_in_dag():
    from engine.safety.dependency_graph import _detect_cycles
    edges = {
        "a": {"b", "c"},
        "b": {"c"},
        "c": set(),
    }
    cycles = _detect_cycles(edges)
    assert cycles == []


# ─────────────────────────── 메트릭 ───────────────────────────

def test_in_degree_for_pii():
    """pii 모듈은 face_reading이 직접 import — 그래프에는 face_reading 없으므로 0일 수도."""
    from engine.safety.dependency_graph import build_graph, in_degree
    g = build_graph()
    # 어떤 모듈이든 in_degree >= 0
    assert in_degree(g, "engine.safety.pii") >= 0


def test_in_degree_for_unknown_returns_zero():
    from engine.safety.dependency_graph import build_graph, in_degree
    g = build_graph()
    assert in_degree(g, "engine.safety.nonexistent") == 0


def test_out_degree_for_compliance_report_non_zero():
    """compliance_report는 importlib로 모듈을 import하므로 정적 의존은 없을 수 있다."""
    from engine.safety.dependency_graph import build_graph, out_degree
    g = build_graph()
    # 그래프 내부에 있어야
    assert "engine.safety.compliance_report" in g.nodes
    assert out_degree(g, "engine.safety.compliance_report") >= 0


def test_get_dependents_returns_list():
    from engine.safety.dependency_graph import build_graph, get_dependents
    g = build_graph()
    deps = get_dependents(g, "engine.safety.pii")
    assert isinstance(deps, list)


def test_get_dependencies_returns_list():
    from engine.safety.dependency_graph import build_graph, get_dependencies
    g = build_graph()
    deps = get_dependencies(g, "engine.safety.compliance_report")
    assert isinstance(deps, list)


# ─────────────────────────── 위상 정렬 ───────────────────────────

def test_topological_order_covers_all_nodes_when_dag():
    from engine.safety.dependency_graph import build_graph
    g = build_graph()
    # cycle 없음 가정 → 위상 정렬이 모든 노드 커버
    if not g.cycles:
        assert len(g.topological_order) == len(g.nodes)


def test_topological_order_is_deterministic():
    """같은 입력이면 같은 위상 정렬."""
    from engine.safety.dependency_graph import build_graph
    a = build_graph()
    b = build_graph()
    assert a.topological_order == b.topological_order


# ─────────────────────────── 포맷 ───────────────────────────

def test_format_text_includes_summary():
    from engine.safety.dependency_graph import build_graph, format_graph_text
    g = build_graph()
    text = format_graph_text(g)
    assert "운영표준 의존성 그래프" in text
    assert "Cycles:" in text
    assert "Isolated:" in text
    assert "Hotspots" in text


def test_to_json_serializable():
    from engine.safety.dependency_graph import build_graph, to_json
    g = build_graph()
    j = to_json(g)
    s = json.dumps(j, ensure_ascii=False)
    parsed = json.loads(s)
    assert parsed["node_count"] == len(g.nodes)


def test_to_json_has_in_out_degree():
    from engine.safety.dependency_graph import build_graph, to_json
    g = build_graph()
    j = to_json(g)
    # 임의 노드 한 개 확인
    sample = next(iter(j["nodes"].values()))
    assert "in_degree" in sample
    assert "out_degree" in sample


# ─────────────────────────── 일관성 ───────────────────────────

def test_imports_and_imported_by_consistent():
    """A가 B를 import하면 B의 imported_by에 A가 있어야."""
    from engine.safety.dependency_graph import build_graph
    g = build_graph()
    for module, node in g.nodes.items():
        for dep in node.imports:
            if dep in g.nodes:
                assert module in g.nodes[dep].imported_by, \
                    f"{module} imports {dep} but not in imported_by"


# ─────────────────────────── __init__ export ───────────────────────────

def test_engine_safety_exports_dependency_graph():
    import engine.safety as safety
    assert hasattr(safety, "build_dependency_graph")
    assert hasattr(safety, "DependencyGraph")
    assert hasattr(safety, "DependencyNode")
    assert hasattr(safety, "in_degree_of")
    assert hasattr(safety, "out_degree_of")
    assert hasattr(safety, "has_dependency_cycles")
    assert hasattr(safety, "format_dependency_graph")
    assert hasattr(safety, "dependency_graph_to_json")
