"""운영표준 의존성 그래프 — §14.13 본문화.

engine.safety 모듈 간 import 의존을 정적 분석해 그래프로 표현. 순환 의존·
고립 모듈·중심 모듈(핫스팟) 식별로 운영표준의 구조적 건강도를 측정.

§14.13 분석 차원:
  · DAG 검증 (cycle 감지)
  · in_degree / out_degree per node
  · 고립 모듈 (도달 불가능, leaf 노드)
  · 핫스팟 (in_degree ≥ 5인 중심 모듈)
  · 위상 정렬 (안전한 import 순서)

본 모듈은 AST 파싱으로 import 문을 추출 (importlib 실행 X).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


# §14.13 hotspot 임계
HOTSPOT_IN_DEGREE = 5


@dataclass(frozen=True)
class DependencyNode:
    module: str
    imports: tuple[str, ...]      # 이 모듈이 의존하는 다른 engine.safety 모듈
    imported_by: tuple[str, ...]  # 이 모듈을 의존하는 다른 모듈


@dataclass(frozen=True)
class DependencyGraph:
    nodes: dict[str, DependencyNode]   # module → node
    cycles: tuple[tuple[str, ...], ...]  # 발견된 순환 (각 cycle = 노드 리스트)
    isolated: tuple[str, ...]           # 의존도 0인 모듈 (in=0, out=0)
    hotspots: tuple[str, ...]           # in_degree ≥ HOTSPOT_IN_DEGREE
    topological_order: tuple[str, ...]  # DAG 위상 정렬 (cycle 있으면 부분만)


# ─────────────────────────── AST 파싱 ───────────────────────────

def _extract_imports_from_source(source: str) -> set[str]:
    """Python 소스 → engine.safety.* 임포트 집합."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("engine.safety."):
                out.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("engine.safety."):
                    out.add(alias.name)
    return out


def collect_module_imports(
    safety_dir: Path,
) -> dict[str, set[str]]:
    """engine/safety 디렉터리 안의 모든 .py (서브폴더 재귀) 에서 engine.safety.* import 추출.

    ADR-051: ADR-040 후 9 카테고리 서브폴더 구조 — iterdir() 단일 디렉토리 X,
    rglob('*.py') 재귀 탐색으로 모든 카테고리·모듈 수집.

    Returns:
        {module_name: set_of_imported_modules}
        (테스트 파일·__init__·quick_check은 제외 — 운영 모듈만)
    """
    out: dict[str, set[str]] = {}
    if not safety_dir.exists():
        return out
    for path in safety_dir.rglob("*.py"):
        if not path.is_file():
            continue
        if path.name in ("__init__.py", "quick_check.py"):
            continue
        if path.name.startswith("test_"):
            continue
        if "__pycache__" in path.parts:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # path → engine.safety.{cat}.{mod} 또는 engine.safety.{mod}
        rel = path.relative_to(safety_dir)
        parts = list(rel.parts[:-1]) + [rel.stem]
        module = "engine.safety." + ".".join(parts)
        imports = _extract_imports_from_source(source)
        imports.discard(module)
        out[module] = imports
    return out


# ─────────────────────────── 그래프 분석 ───────────────────────────

def _detect_cycles(
    edges: dict[str, set[str]],
) -> list[tuple[str, ...]]:
    """간단한 DFS 기반 cycle 감지. 발견된 cycle = 노드 시퀀스."""
    cycles: list[tuple[str, ...]] = []
    color: dict[str, int] = {n: 0 for n in edges}  # 0=white, 1=gray, 2=black
    stack: list[str] = []
    seen_cycles: set[tuple[str, ...]] = set()

    def dfs(node: str) -> None:
        if color.get(node, 0) == 2:
            return
        if color.get(node, 0) == 1:
            # back-edge → cycle
            try:
                idx = stack.index(node)
                cycle = tuple(stack[idx:])
                # 정규화 — 가장 작은 노드를 시작점으로
                if cycle:
                    min_idx = min(range(len(cycle)), key=lambda i: cycle[i])
                    normalized = cycle[min_idx:] + cycle[:min_idx]
                    if normalized not in seen_cycles:
                        seen_cycles.add(normalized)
                        cycles.append(normalized)
            except ValueError:
                pass
            return
        color[node] = 1
        stack.append(node)
        for nbr in edges.get(node, set()):
            if nbr in color:  # 그래프 안의 노드만
                dfs(nbr)
        stack.pop()
        color[node] = 2

    for n in list(edges.keys()):
        if color.get(n, 0) == 0:
            dfs(n)
    return cycles


def _topological_sort(
    edges: dict[str, set[str]],
) -> list[str]:
    """Kahn 알고리즘 — cycle 있어도 가능한 만큼 정렬."""
    in_degree: dict[str, int] = {n: 0 for n in edges}
    for n, deps in edges.items():
        for d in deps:
            if d in in_degree:
                in_degree[d] += 1
    queue = [n for n, d in in_degree.items() if d == 0]
    order: list[str] = []
    while queue:
        # 결정론적 정렬
        queue.sort()
        n = queue.pop(0)
        order.append(n)
        for m in edges.get(n, set()):
            if m in in_degree:
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    queue.append(m)
    return order


def build_graph(
    safety_dir: Path | None = None,
) -> DependencyGraph:
    """엔진 안전 모듈 그래프 분석.

    ADR-051: ADR-040 후 9 카테고리 서브폴더 구조 — safety_dir은 audit/ 가 아닌
    engine/safety/ 루트여야 모든 모듈 수집.
    """
    if safety_dir is None:
        safety_dir = Path(__file__).resolve().parent.parent  # engine/safety/
    raw = collect_module_imports(safety_dir)

    # imported_by 역방향 인덱스
    rev: dict[str, set[str]] = {m: set() for m in raw}
    for m, imports in raw.items():
        for dep in imports:
            if dep in rev:
                rev[dep].add(m)

    nodes: dict[str, DependencyNode] = {}
    for m in sorted(raw.keys()):
        nodes[m] = DependencyNode(
            module=m,
            imports=tuple(sorted(raw[m])),
            imported_by=tuple(sorted(rev.get(m, set()))),
        )

    cycles_list = _detect_cycles(raw)
    cycles = tuple(cycles_list)

    isolated = tuple(sorted(
        m for m in nodes
        if not nodes[m].imports and not nodes[m].imported_by
    ))

    hotspots = tuple(sorted(
        m for m, node in nodes.items()
        if len(node.imported_by) >= HOTSPOT_IN_DEGREE
    ))

    topo = tuple(_topological_sort(raw))

    return DependencyGraph(
        nodes=nodes,
        cycles=cycles,
        isolated=isolated,
        hotspots=hotspots,
        topological_order=topo,
    )


# ─────────────────────────── 메트릭 ───────────────────────────

def in_degree(graph: DependencyGraph, module: str) -> int:
    node = graph.nodes.get(module)
    return len(node.imported_by) if node else 0


def out_degree(graph: DependencyGraph, module: str) -> int:
    node = graph.nodes.get(module)
    return len(node.imports) if node else 0


def has_cycles(graph: DependencyGraph) -> bool:
    return len(graph.cycles) > 0


def get_dependents(graph: DependencyGraph, module: str) -> list[str]:
    """이 모듈에 직접 의존하는 다른 모듈 목록."""
    node = graph.nodes.get(module)
    return list(node.imported_by) if node else []


def get_dependencies(graph: DependencyGraph, module: str) -> list[str]:
    """이 모듈이 직접 의존하는 모듈 목록."""
    node = graph.nodes.get(module)
    return list(node.imports) if node else []


# ─────────────────────────── 직렬화 ───────────────────────────

def format_graph_text(graph: DependencyGraph) -> str:
    """터미널 표시용 사람-읽기 텍스트."""
    lines: list[str] = []
    lines.append(f"# 운영표준 의존성 그래프 ({len(graph.nodes)} nodes)")
    lines.append("")
    lines.append(f"- Cycles: {len(graph.cycles)}")
    if graph.cycles:
        for c in graph.cycles[:5]:
            lines.append(f"  · {' → '.join(c)} → {c[0]}")
    lines.append(f"- Isolated: {len(graph.isolated)}")
    if graph.isolated:
        lines.append(f"  · {', '.join(graph.isolated[:10])}")
    lines.append(f"- Hotspots (in_degree ≥ {HOTSPOT_IN_DEGREE}): "
                 f"{len(graph.hotspots)}")
    for h in graph.hotspots[:10]:
        lines.append(f"  · {h} (imported by {in_degree(graph, h)})")
    lines.append(f"- Topological order: {len(graph.topological_order)} nodes")
    return "\n".join(lines)


def to_json(graph: DependencyGraph) -> dict[str, object]:
    return {
        "node_count": len(graph.nodes),
        "cycles": [list(c) for c in graph.cycles],
        "isolated": list(graph.isolated),
        "hotspots": list(graph.hotspots),
        "topological_order": list(graph.topological_order),
        "nodes": {
            m: {
                "imports": list(n.imports),
                "imported_by": list(n.imported_by),
                "in_degree": len(n.imported_by),
                "out_degree": len(n.imports),
            }
            for m, n in graph.nodes.items()
        },
    }
