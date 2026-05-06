"""Search client abstraction for ResearcherAgent."""

from __future__ import annotations

import logging

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client. Uses Tavily when configured, otherwise a mock."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.tavily_api_key

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        if self._api_key:
            try:
                return self._tavily_search(query, max_results)
            except Exception as exc:
                logger.warning("Tavily search failed (%s); falling back to mock results.", exc)
        return self._mock_search(query, max_results)

    def _tavily_search(self, query: str, max_results: int) -> list[SourceDocument]:
        import requests

        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
        }
        response = requests.post(
            "https://api.tavily.com/search", json=payload, timeout=20
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", []) or []
        docs: list[SourceDocument] = []
        for item in results[:max_results]:
            docs.append(
                SourceDocument(
                    title=item.get("title") or "(untitled)",
                    url=item.get("url"),
                    snippet=(item.get("content") or "")[:1200],
                    metadata={"score": item.get("score")},
                )
            )
        return docs

    @staticmethod
    def _mock_search(query: str, max_results: int) -> list[SourceDocument]:
        logger.info("Using mock search for query=%r", query)
        return [
            SourceDocument(
                title=f"Mock source {i + 1} for {query}",
                url=f"https://example.com/mock/{i + 1}",
                snippet=(
                    f"This is a synthetic snippet #{i + 1} discussing the topic '{query}'. "
                    "Use a real search provider (Tavily/Bing/SerpAPI) for production."
                ),
                metadata={"mock": True},
            )
            for i in range(max_results)
        ]
