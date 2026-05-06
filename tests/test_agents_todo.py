"""Behavioral tests for the implemented Supervisor routing policy."""

from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.agents.supervisor import (
    ROUTE_ANALYST,
    ROUTE_DONE,
    ROUTE_RESEARCHER,
    ROUTE_WRITER,
)
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def _state() -> ResearchState:
    return ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))


def test_supervisor_routes_to_researcher_when_empty() -> None:
    assert SupervisorAgent().decide(_state()) == ROUTE_RESEARCHER


def test_supervisor_routes_to_analyst_after_research() -> None:
    s = _state()
    s.research_notes = "some notes"
    assert SupervisorAgent().decide(s) == ROUTE_ANALYST


def test_supervisor_routes_to_writer_after_analysis() -> None:
    s = _state()
    s.research_notes = "notes"
    s.analysis_notes = "analysis"
    assert SupervisorAgent().decide(s) == ROUTE_WRITER


def test_supervisor_routes_done_when_complete() -> None:
    s = _state()
    s.research_notes = "notes"
    s.analysis_notes = "analysis"
    s.final_answer = "answer"
    assert SupervisorAgent().decide(s) == ROUTE_DONE


def test_supervisor_stops_on_max_iterations() -> None:
    s = _state()
    sup = SupervisorAgent(max_iterations=2)
    s.iteration = 2
    assert sup.decide(s) == ROUTE_DONE


def test_supervisor_run_records_route() -> None:
    s = _state()
    SupervisorAgent().run(s)
    assert s.route_history == [ROUTE_RESEARCHER]
    assert s.iteration == 1
