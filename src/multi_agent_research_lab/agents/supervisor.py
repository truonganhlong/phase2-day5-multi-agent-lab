"""Supervisor / router agent."""

from __future__ import annotations

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


ROUTE_RESEARCHER = "researcher"
ROUTE_ANALYST = "analyst"
ROUTE_WRITER = "writer"
ROUTE_DONE = "done"


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop.

    Deterministic policy (sufficient for the lab):
      1. If no research notes yet -> researcher.
      2. If notes but no analysis -> analyst.
      3. If analysis but no final answer -> writer.
      4. Otherwise -> done.
      5. Hard stop on max_iterations.
    """

    name = "supervisor"

    def __init__(self, max_iterations: int | None = None) -> None:
        settings = get_settings()
        self._max_iterations = max_iterations or settings.max_iterations

    def decide(self, state: ResearchState) -> str:
        if state.iteration >= self._max_iterations:
            logger.warning("Supervisor: max_iterations=%s reached", self._max_iterations)
            return ROUTE_DONE
        if state.errors and len(state.errors) >= 3:
            logger.warning("Supervisor: too many errors (%s), stopping", len(state.errors))
            return ROUTE_DONE
        if not state.research_notes:
            return ROUTE_RESEARCHER
        if not state.analysis_notes:
            return ROUTE_ANALYST
        if not state.final_answer:
            return ROUTE_WRITER
        return ROUTE_DONE

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("agent.supervisor", {"iteration": state.iteration}) as span:
            route = self.decide(state)
            state.record_route(route)
            span["attributes"]["route"] = route
            state.add_trace_event("supervisor.route", {"route": route})
        return state
