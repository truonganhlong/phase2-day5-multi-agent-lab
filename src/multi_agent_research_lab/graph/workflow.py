"""Multi-agent workflow.

The lab guide suggests LangGraph, but the contract is the same: a routed loop where
the Supervisor selects the next worker until a stop condition fires. We implement it
with plain Python here — readable, testable, and easy to swap for a LangGraph build()
later.
"""

from __future__ import annotations

import logging

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import (
    ROUTE_ANALYST,
    ROUTE_DONE,
    ROUTE_RESEARCHER,
    ROUTE_WRITER,
    SupervisorAgent,
)
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """Builds and runs the multi-agent loop."""

    def __init__(
        self,
        supervisor: SupervisorAgent | None = None,
        researcher: BaseAgent | None = None,
        analyst: BaseAgent | None = None,
        writer: BaseAgent | None = None,
        max_iterations: int | None = None,
    ) -> None:
        settings = get_settings()
        self._max_iterations = max_iterations or settings.max_iterations
        self._supervisor = supervisor or SupervisorAgent(max_iterations=self._max_iterations)
        self._researcher = researcher or ResearcherAgent()
        self._analyst = analyst or AnalystAgent()
        self._writer = writer or WriterAgent()

    def build(self) -> dict[str, BaseAgent]:
        """Return the routing table that drives the loop."""

        return {
            ROUTE_RESEARCHER: self._researcher,
            ROUTE_ANALYST: self._analyst,
            ROUTE_WRITER: self._writer,
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute supervisor -> worker loop until DONE or max_iterations."""

        workers = self.build()

        with trace_span("workflow.run", {"query": state.request.query}) as span:
            for _ in range(self._max_iterations + 1):
                self._supervisor.run(state)
                route = state.route_history[-1] if state.route_history else ROUTE_DONE
                if route == ROUTE_DONE:
                    break
                worker = workers.get(route)
                if worker is None:
                    state.errors.append(f"workflow: unknown route {route}")
                    break
                try:
                    worker.run(state)
                except AgentExecutionError as exc:
                    state.errors.append(f"{route}: {exc}")
                    logger.exception("Worker %s failed", route)
                    break
            else:
                state.errors.append("workflow: exceeded max_iterations safety bound")

            if not state.final_answer:
                state.final_answer = (
                    "Multi-agent workflow ended without a final answer. "
                    f"Errors: {state.errors or 'none'}"
                )

            span["attributes"].update(
                {
                    "iterations": state.iteration,
                    "errors": len(state.errors),
                    "route_history": list(state.route_history),
                }
            )
        return state
