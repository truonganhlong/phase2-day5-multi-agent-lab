"""Command-line entrypoint for the lab starter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import LabError
from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient, flush_langsmith
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()


BASELINE_SYSTEM_PROMPT = (
    "You are a senior research assistant. Given a query, deliver a well-structured "
    "answer with key findings, brief analysis, and (when applicable) caveats. "
    "Do all reasoning in a single response — no tools, no follow-ups."
)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def run_single_agent(query: str) -> ResearchState:
    """Run the single-agent baseline: one LLM call, no tools, no orchestration."""

    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    state.add_trace_event("baseline_start", {"query": query})

    client = LLMClient(temperature=0.3)
    response = client.complete(
        system_prompt=BASELINE_SYSTEM_PROMPT,
        user_prompt=f"Audience: {request.audience}\n\nQuery: {query}",
    )
    state.final_answer = response.content
    state.add_trace_event(
        "baseline_done",
        {
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd,
        },
    )
    return state


def run_multi_agent(query: str) -> ResearchState:
    """Run the multi-agent workflow."""

    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent baseline (one LLM call)."""

    _init()
    try:
        state = run_single_agent(query)
    except LabError as exc:
        console.print(Panel.fit(str(exc), title="Error", style="red"))
        raise typer.Exit(code=2) from exc
    console.print(Panel.fit(state.final_answer or "(empty)", title="Single-Agent Baseline"))
    flush_langsmith()


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    show_state: Annotated[bool, typer.Option("--show-state", help="Print full state JSON")] = False,
) -> None:
    """Run the multi-agent workflow."""

    _init()
    try:
        state = run_multi_agent(query)
    except LabError as exc:
        console.print(Panel.fit(str(exc), title="Error", style="red"))
        raise typer.Exit(code=2) from exc

    console.print(Panel.fit(state.final_answer or "(empty)", title="Multi-Agent Final Answer"))
    if show_state:
        console.print_json(state.model_dump_json(indent=2))
    flush_langsmith()


@app.command()
def benchmark(
    config: Annotated[
        Path, typer.Option("--config", "-c", help="YAML config with benchmark.queries")
    ] = Path("configs/lab_default.yaml"),
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Output markdown report path")
    ] = Path("reports/benchmark_report.md"),
    queries: Annotated[
        list[str] | None,
        typer.Option("--query", "-q", help="Override queries from config (repeatable)"),
    ] = None,
) -> None:
    """Benchmark single-agent vs multi-agent across queries and write a markdown report."""

    _init()
    if queries:
        query_list = list(queries)
    else:
        if not config.exists():
            console.print(Panel.fit(f"Config not found: {config}", title="Error", style="red"))
            raise typer.Exit(code=2)
        cfg = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        query_list = cfg.get("benchmark", {}).get("queries", []) or []
        if not query_list:
            console.print(Panel.fit("No queries to benchmark.", title="Error", style="red"))
            raise typer.Exit(code=2)

    metrics: list[BenchmarkMetrics] = []
    examples: list[dict[str, str]] = []

    for idx, q in enumerate(query_list, start=1):
        console.print(f"[bold]Q{idx}:[/bold] {q}")

        baseline_state, baseline_metrics = run_benchmark(
            run_name=f"baseline-q{idx}", query=q, runner=run_single_agent
        )
        metrics.append(baseline_metrics)

        try:
            multi_state, multi_metrics = run_benchmark(
                run_name=f"multi-agent-q{idx}", query=q, runner=run_multi_agent
            )
        except LabError as exc:
            console.print(f"[red]multi-agent failed:[/red] {exc}")
            multi_state = None
            multi_metrics = BenchmarkMetrics(
                run_name=f"multi-agent-q{idx}",
                latency_seconds=0.0,
                notes=f"failed: {exc}",
            )
        metrics.append(multi_metrics)

        examples.append(
            {
                "query": q,
                "baseline_answer": baseline_state.final_answer or "",
                "multi_answer": (multi_state.final_answer if multi_state else "") or "",
            }
        )

    table = Table(title="Benchmark summary")
    table.add_column("Run")
    table.add_column("Latency (s)", justify="right")
    table.add_column("Cost (USD)", justify="right")
    table.add_column("Notes")
    for m in metrics:
        table.add_row(
            m.run_name,
            f"{m.latency_seconds:.2f}",
            "" if m.estimated_cost_usd is None else f"{m.estimated_cost_usd:.4f}",
            m.notes,
        )
    console.print(table)

    report = render_markdown_report(metrics, examples=examples)
    store = LocalArtifactStore(root=output.parent if str(output.parent) else Path("."))
    written = store.write_text(output.name, report)
    console.print(f"[green]Wrote report:[/green] {written}")


@app.command()
def todos() -> None:
    """List remaining TODO(student) markers (sanity check)."""

    _init()
    base = Path(__file__).resolve().parent
    hits = []
    for path in base.rglob("*.py"):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "TODO(student)" in content:
            hits.append(str(path))
    if hits:
        console.print(Panel.fit("\n".join(hits), title="Remaining TODOs", style="yellow"))
    else:
        console.print(Panel.fit("No TODO(student) markers left in src/.", title="Clean", style="green"))


def _dump(state: ResearchState) -> str:
    return json.dumps(state.model_dump(), indent=2, default=str)


if __name__ == "__main__":
    app()
