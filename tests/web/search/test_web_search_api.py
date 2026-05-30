# -*- coding: utf-8 -*-
"""ELM Web searches using search engines tests"""
import os
from pathlib import Path

import pytest

import elm.web.search.duckduckgo
import elm.web.search.google
from elm.web.search.base import (APISearchEngineLinkSearch,
                                 SearchEngineLinkSearch,
                                 format_search_results,
                                 _format_url_results)
from elm.web.search.run import _single_query_api


SE_API_TO_TEST = [(elm.web.search.duckduckgo.APIDuckDuckGoSearch,
                   {"verify": False})]
if os.getenv(elm.web.search.google.APIGoogleCSESearch.API_KEY_VAR):
    SE_API_TO_TEST.append((elm.web.search.google.APIGoogleCSESearch, {}))


def test_api_key_read_from_env(monkeypatch):
    """Test that API search engine reads environ"""
    monkeypatch.setenv("TEST_API_KEY_VAR", "TEST-KEY")

    class MockAPISearchEngine(APISearchEngineLinkSearch):
        """MockAPISearchEngine"""

        API_KEY_VAR = "TEST_API_KEY_VAR"

        async def _search(self, *__, **___):
            return []

    assert MockAPISearchEngine().api_key == "TEST-KEY"


def test_no_api_key_var():
    """Test that API search engine does not break if var name is None"""

    class MockAPISearchEngine(APISearchEngineLinkSearch):
        """MockAPISearchEngine"""

        async def _search(self, *__, **___):
            return []

    assert MockAPISearchEngine().api_key is None


def test_format_search_results_raw():
    """Test raw structured results preserve URL and attrs"""
    results = [{"href": "https://example.com/a+b", "title": "Result A"},
               {"href": "", "title": "Missing URL"}]

    out = format_search_results("test_se", "query", results, "href", raw=False)
    assert out == ["https://example.com/a%20b"]

    out = format_search_results("test_se", "query", results, "href", raw=True)
    assert out == [{
        "url": "https://example.com/a%20b",
        "query": "query",
        "search_engine": "test_se",
        "query_rank": 1,
        "attrs": {"href": "https://example.com/a+b", "title": "Result A"},
    }]


def test_format_url_results_raw():
    """Test raw URL-only results still include URL keys"""
    out = _format_url_results("test_se", "query",
                              ["https://example.com/a+b", ""])
    assert out == ["https://example.com/a%20b"]

    out = _format_url_results("test_se", "query",
                              ["https://example.com/a+b", ""], raw=True)
    assert out == [
        {
            "url": "https://example.com/a%20b",
            "query": "query",
            "search_engine": "test_se",
            "query_rank": 1,
        }
    ]


@pytest.mark.asyncio
async def test_results_passes_raw_flag():
    """Test SearchEngineLinkSearch.results forwards raw to _search"""

    class MockSearchEngine(SearchEngineLinkSearch):
        """MockSearchEngine"""

        async def _search(self, query, num_results=10, raw=False):
            if raw:
                return [{"url": query, "attrs": {"query": query}}]
            return [query]

    search_engine = MockSearchEngine()

    assert await search_engine.results("https://example.com") == [[
        "https://example.com"
    ]]
    assert await search_engine.results("https://example.com", raw=True) == [[{
        "url": "https://example.com",
        'attrs': {'query': 'https://example.com'},
    }]]


@pytest.mark.asyncio
async def test_single_query_api_passes_raw_flag():
    """Test internal API runner preserves raw search outputs"""

    class MockSearchEngine:
        """MockSearchEngine"""

        _SE_NAME = "Mock"

        async def results(self, *queries, num_results=10, raw=False):
            assert queries == ("query",)
            assert num_results > 0
            return [[{"url": "https://example.com", "attrs": {}}]] if raw else [[
                "https://example.com"
            ]]

    search_engine = MockSearchEngine()

    assert await _single_query_api(search_engine, "query", raw=True) == [[{
        "url": "https://example.com",
        "attrs": {},
    }]]


@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true",
                    reason="Fails in GHA due to rate limiting")
@pytest.mark.parametrize("queries", [['1. "NatLabRockies elm"'],
                                     ['1. "NatLabRockies elm"',
                                      "NatLabRockies reV"],])
@pytest.mark.parametrize("se", SE_API_TO_TEST)
@pytest.mark.asyncio
async def test_basic_search_query(queries, se):
    """Test basic web search query functionality"""

    num_results = 7
    se_class, kwargs = se
    search_engine = se_class(**kwargs)
    out = await search_engine.results(*queries, num_results=num_results)

    assert len(out) == len(queries)
    for results in out:
        assert 0 < len(results) <= num_results
        assert all(link.startswith("http") for link in results)
        assert all("+" not in link for link in results)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
