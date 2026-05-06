"""Writer agent: produces the final answer."""

from __future__ import annotations

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


SYSTEM_PROMPT = (
    "You are a senior technical writer. Synthesize a clear, well-structured answer "
    "for the given audience. Use the analysis and research notes faithfully. Keep "
    "[n] citations inline. End with a 'Sources' section listing each [n] as "
    "'[n] Title — URL'. Avoid filler. Aim for the requested length."
)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient(temperature=0.4)

    def run(self, state: ResearchState) -> ResearchState:
        if not state.research_notes or not state.analysis_notes:
            raise AgentExecutionError(
                "WriterAgent requires both research_notes and analysis_notes"
            )

        with trace_span("agent.writer", {"iteration": state.iteration}) as span:
            sources_list = "\n".join(
                f"[{i + 1}] {d.title} — {d.url or 'n/a'}" for i, d in enumerate(state.sources)
            ) or "(none)"
            user_prompt = (
                f"Query: {state.request.query}\n"
                f"Audience: {state.request.audience}\n\n"
                f"Research notes:\n{state.research_notes}\n\n"
                f"Analysis:\n{state.analysis_notes}\n\n"
                f"Source index:\n{sources_list}\n\n"
                "Write the final answer now."
            )
            response = self._llm.complete(SYSTEM_PROMPT, user_prompt)
            state.final_answer = response.content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=response.content,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
            span["attributes"]["cost_usd"] = response.cost_usd
            state.add_trace_event("writer.done", {})
        return state
