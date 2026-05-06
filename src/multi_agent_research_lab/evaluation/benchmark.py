"""Benchmark single-agent vs multi-agent runs."""

from __future__ import annotations

import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def _aggregate_cost(state: ResearchState) -> float | None:
    costs: list[float] = []
    for r in state.agent_results:
        c = r.metadata.get("cost_usd")
        if isinstance(c, (int, float)):
            costs.append(float(c))
    for ev in state.trace:
        c = ev.get("payload", {}).get("cost_usd") if isinstance(ev, dict) else None
        if isinstance(c, (int, float)):
            costs.append(float(c))
    return round(sum(costs), 6) if costs else None


def _citation_coverage(state: ResearchState) -> float | None:
    if not state.final_answer or not state.sources:
        return None
    citations = set(re.findall(r"\[(\d+)\]", state.final_answer))
    n_sources = len(state.sources)
    if n_sources == 0:
        return None
    cited = sum(1 for s in citations if 1 <= int(s) <= n_sources)
    return round(cited / n_sources, 3)


def _quality_heuristic(state: ResearchState) -> float | None:
    """Crude rubric-style score (0-10) — replace with peer review for the deliverable."""

    if not state.final_answer:
        return 0.0
    text = state.final_answer
    score = 0.0
    score += min(4.0, len(text) / 400)  # length up to 4 points (~1600 chars)
    if "[1]" in text or "Sources" in text or "Source" in text:
        score += 2.0
    if state.analysis_notes:
        score += 1.5
    if state.research_notes:
        score += 1.5
    if state.errors:
        score -= 1.0
    return round(max(0.0, min(10.0, score)), 2)


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, quality and citation coverage for a runner."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    cost = _aggregate_cost(state)
    quality = _quality_heuristic(state)
    coverage = _citation_coverage(state)
    error_rate = 1.0 if state.errors else 0.0

    notes_parts: list[str] = []
    if coverage is not None:
        notes_parts.append(f"citation_coverage={coverage}")
    notes_parts.append(f"errors={len(state.errors)}")
    if state.route_history:
        notes_parts.append(f"routes={'>'.join(state.route_history)}")

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=round(latency, 3),
        estimated_cost_usd=cost,
        quality_score=quality,
        notes="; ".join(notes_parts),
    )
    return state, metrics


__all__ = ["run_benchmark", "Runner"]
