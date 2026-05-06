"""Analyst agent: turns research notes into structured insights."""

from __future__ import annotations

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


SYSTEM_PROMPT = (
    "You are an analyst. Given research notes with [n] citations, extract: "
    "(1) key claims, (2) points of agreement, (3) points of disagreement, "
    "(4) gaps or weak evidence, (5) practical implications. Keep each section "
    "to 2-5 bullets. Preserve [n] citations from the input."
)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient(temperature=0.1)

    def run(self, state: ResearchState) -> ResearchState:
        if not state.research_notes:
            raise AgentExecutionError("AnalystAgent requires state.research_notes")

        with trace_span("agent.analyst", {"iteration": state.iteration}) as span:
            user_prompt = (
                f"Query: {state.request.query}\n"
                f"Audience: {state.request.audience}\n\n"
                f"Research notes:\n{state.research_notes}\n\n"
                "Produce the structured analysis."
            )
            response = self._llm.complete(SYSTEM_PROMPT, user_prompt)
            state.analysis_notes = response.content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=response.content,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
            span["attributes"]["cost_usd"] = response.cost_usd
            state.add_trace_event("analyst.done", {})
        return state
