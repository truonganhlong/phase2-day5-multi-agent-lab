"""Critic agent: lightweight fact-check / quality review of the final answer."""

from __future__ import annotations

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


SYSTEM_PROMPT = (
    "You are a critical reviewer. Check the answer against the research notes for: "
    "(1) unsupported claims, (2) missing citations, (3) hallucinations or contradictions, "
    "(4) clarity issues. Return a short report with bullet findings and a final verdict: "
    "PASS or REVISE. Do NOT rewrite the answer."
)


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient(temperature=0.0)

    def run(self, state: ResearchState) -> ResearchState:
        if not state.final_answer:
            raise AgentExecutionError("CriticAgent requires state.final_answer")

        with trace_span("agent.critic", {"iteration": state.iteration}) as span:
            user_prompt = (
                f"Query: {state.request.query}\n\n"
                f"Research notes:\n{state.research_notes or '(none)'}\n\n"
                f"Final answer to review:\n{state.final_answer}\n\n"
                "Produce the critique now."
            )
            response = self._llm.complete(SYSTEM_PROMPT, user_prompt)
            verdict = "PASS" if "PASS" in response.content.upper() else "REVISE"
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.CRITIC,
                    content=response.content,
                    metadata={
                        "verdict": verdict,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
            span["attributes"]["verdict"] = verdict
            state.add_trace_event("critic.done", {"verdict": verdict})
        return state
