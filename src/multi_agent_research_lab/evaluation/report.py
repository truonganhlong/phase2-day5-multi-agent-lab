"""Benchmark report rendering."""

from __future__ import annotations

from collections.abc import Iterable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(
    metrics: list[BenchmarkMetrics],
    examples: Iterable[dict[str, str]] | None = None,
) -> str:
    """Render benchmark metrics + optional answer examples to markdown."""

    lines: list[str] = ["# Benchmark Report", ""]

    lines.extend(
        [
            "## Summary table",
            "",
            "| Run | Latency (s) | Cost (USD) | Quality (0-10) | Notes |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {item.notes} |"
        )

    baseline = [m for m in metrics if m.run_name.startswith("baseline")]
    multi = [m for m in metrics if m.run_name.startswith("multi-agent")]
    if baseline and multi:
        avg_lat_b = sum(m.latency_seconds for m in baseline) / len(baseline)
        avg_lat_m = sum(m.latency_seconds for m in multi) / len(multi)
        avg_cost_b = _avg_optional(m.estimated_cost_usd for m in baseline)
        avg_cost_m = _avg_optional(m.estimated_cost_usd for m in multi)
        avg_qual_b = _avg_optional(m.quality_score for m in baseline)
        avg_qual_m = _avg_optional(m.quality_score for m in multi)
        lines.extend(
            [
                "",
                "## Aggregate",
                "",
                f"- Avg latency — baseline: {avg_lat_b:.2f}s, multi-agent: {avg_lat_m:.2f}s",
                f"- Avg cost — baseline: {_fmt(avg_cost_b)}, multi-agent: {_fmt(avg_cost_m)}",
                f"- Avg quality — baseline: {_fmt(avg_qual_b, '.2f')}, multi-agent: {_fmt(avg_qual_m, '.2f')}",
            ]
        )

    if examples:
        lines.extend(["", "## Example outputs", ""])
        for i, ex in enumerate(examples, start=1):
            lines.extend(
                [
                    f"### Q{i}: {ex.get('query', '')}",
                    "",
                    "**Baseline answer**",
                    "",
                    "```",
                    (ex.get("baseline_answer") or "(empty)").strip(),
                    "```",
                    "",
                    "**Multi-agent answer**",
                    "",
                    "```",
                    (ex.get("multi_answer") or "(empty)").strip(),
                    "```",
                    "",
                ]
            )

    lines.extend(
        [
            "",
            "## Failure mode notes",
            "",
            "- Quality score above is a coarse heuristic; replace with peer review (rubric 0-10).",
            "- Cost is estimated from token usage and a static price table — verify against provider billing.",
            "- Tracing buffer can be exported via `observability.tracing.dump_traces()` for trace links.",
        ]
    )
    return "\n".join(lines) + "\n"


def _avg_optional(values: Iterable[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    return sum(nums) / len(nums) if nums else None


def _fmt(value: float | None, spec: str = ".4f") -> str:
    return "n/a" if value is None else format(value, spec)
