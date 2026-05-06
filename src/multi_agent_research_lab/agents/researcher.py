"""Researcher agent: gathers sources and writes research notes."""

from __future__ import annotations

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a research analyst. Read the provided sources and produce concise, "
    "factual notes. Group findings by theme. Cite sources inline as [n] using their "
    "numeric index. Do NOT invent facts; if sources disagree, note the disagreement."
)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(
        self,
        llm: LLMClient | None = None,
        search: SearchClient | None = None,
    ) -> None:
        self._llm = llm or LLMClient(temperature=0.2)
        self._search = search or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("agent.researcher", {"iteration": state.iteration}) as span:
            try:
                docs = self._search.search(
                    query=state.request.query, max_results=state.request.max_sources
                )
            except Exception as exc:
                state.errors.append(f"researcher.search: {exc}")
                raise AgentExecutionError(f"Researcher search failed: {exc}") from exc

            if not docs:
                state.errors.append("researcher: empty source list")

            state.sources = docs
            sources_block = "\n\n".join(
                f"[{i + 1}] {d.title}\nURL: {d.url or 'n/a'}\nSnippet: {d.snippet}"
                for i, d in enumerate(docs)
            ) or "(no sources retrieved)"

            user_prompt = (
                f"Query: {state.request.query}\n"
                f"Audience: {state.request.audience}\n\n"
                f"Sources:\n{sources_block}\n\n"
                "Write 6-10 bullet research notes with [n] citations."
            )
            response = self._llm.complete(SYSTEM_PROMPT, user_prompt)
            state.research_notes = response.content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=response.content,
                    metadata={
                        "sources": len(docs),
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
            span["attributes"].update(
                {"sources": len(docs), "cost_usd": response.cost_usd}
            )
            state.add_trace_event("researcher.done", {"sources": len(docs)})
        return state
