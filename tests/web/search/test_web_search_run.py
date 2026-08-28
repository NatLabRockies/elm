# -*- coding: utf-8 -*-
"""ELM Web searches using search engines tests"""
from pathlib import Path

import pytest

import elm.web.search.run as run_module
from elm.web.search.run import (_single_se_search, _down_select_urls,
                                _init_se, load_docs, search_with_fallback,
                                search_with_fallback_with_attrs)
from elm.web.search.google import (APIGoogleCSESearch,
                                   PlaywrightGoogleLinkSearch)
from elm.web.file_loader import AsyncWebFileLoader
from elm.exceptions import ELMKeyError


@pytest.mark.asyncio
async def test_single_se_search_name_dne():
    """Test error for unknown search engine"""
    with pytest.raises(ELMKeyError) as err:
        await _single_se_search("DNE", None, None, None, None, None, None,
                                None)

    assert "'se_name' must be one of" in str(err)


def test_down_select_urls_empty():
    """Test down selecting empty list"""
    assert _down_select_urls([], []) == []


def test_down_select_urls_empty_queries():
    """Test down selecting when all URLs results are empty"""
    assert _down_select_urls([([], None), ([], None)], []) == []


def test_down_select_urls_diff_lens():
    """Test down selecting URLs result lengths differ"""
    assert _down_select_urls(
        [(['ab'], "A"), (['bc', 'cd'], "B")], ["A", "B"]
    ) == [
        {"url": "ab", "search_engines": ["A"]},
        {"url": "bc", "search_engines": ["B"]},
        {"url": "cd", "search_engines": ["B"]},
    ]


def test_down_select_urls_one_empty():
    """Test down selecting URLs when one result is empty"""
    assert _down_select_urls(
        [([], None), (['bc', 'cd'], "B")], ["B"]
    ) == [
        {"url": "bc", "search_engines": ["B"]},
        {"url": "cd", "search_engines": ["B"]},
    ]


def test_down_select_urls_keep_substrings_override_ignore():
    """Test keep substrings override ignored URLs"""
    results = [(
        ["https://blocked.com/keep-me", "https://blocked.com/drop-me"],
        "A",
    ), (["https://allowed.com/keep"], "B")]

    urls = _down_select_urls(
        results, ["A", "B"],
        url_ignore_substrings={"blocked.com"},
        url_keep_substrings={"keep-me"},
    )

    assert urls == [
        {
            "url": "https://blocked.com/keep-me",
            "search_engines": ["A"],
        },
        {"url": "https://allowed.com/keep", "search_engines": ["B"]},
    ]


def test_init_se():
    """Test initializing a playwright search engine"""
    test_kwargs = {"pw_launch_kwargs": {"test": 1}}
    se, *__ = _init_se("PlaywrightGoogleLinkSearch", test_kwargs)
    assert isinstance(se, PlaywrightGoogleLinkSearch)
    assert se.launch_kwargs["test"] == 1
    assert test_kwargs == {"pw_launch_kwargs": {"test": 1}}


def test_init_se_does_not_pop_kwargs():
    """Test that kwargs are not popped in _init_se"""
    test_kwargs = {"pw_launch_kwargs": {"test": 1},
                   "google_cse_api_kwargs": {"api_key": "test_key"}}
    original_kwargs = test_kwargs.copy()
    se, *__ = _init_se("APIGoogleCSESearch", test_kwargs)
    assert isinstance(se, APIGoogleCSESearch)
    assert se.api_key == "test_key"
    assert test_kwargs == original_kwargs


@pytest.mark.asyncio
async def test_load_docs_empty():
    """Test loading docs for no URLs"""
    assert await load_docs(set(), AsyncWebFileLoader()) == []


@pytest.mark.asyncio
async def test_single_se_search_bad_build():
    """Test that bad init of SE gives no results"""
    test_kwargs = {"google_cse_api_kwargs": {"dne_arg": "test_key"}}
    results = await _single_se_search("APIGoogleCSESearch", [""], None, None,
                                      None, None, None, test_kwargs)
    assert results == []


@pytest.mark.asyncio
async def test_search_with_fallback_with_attrs_tracks_engines(monkeypatch):
    """Track source engines for the selected fallback URLs"""
    responses = {
        ("APIDuckDuckGoSearch", "q1"): [[
            "https://example.com/a", "https://example.com/shared"
        ]],
        ("APIDuckDuckGoSearch", "q2"): [[]],
        ("DuxDistributedGlobalSearch", "q2"): [[
            "https://example.com/shared", "https://example.com/b"
        ]],
    }

    async def fake_run_search(se_name, queries, *_args, **_kwargs):
        return [responses[(se_name, query)] for query in queries]

    monkeypatch.setattr(run_module, "_run_search", fake_run_search)

    results = await search_with_fallback_with_attrs(
        ["q1", "q2"],
        search_engines=("APIDuckDuckGoSearch", "DuxDistributedGlobalSearch"),
        num_urls=2,
    )

    assert results == [
        {
            "url": "https://example.com/a",
            "search_engines": ["DuckDuckGo API"],
        },
        {
            "url": "https://example.com/shared",
            "search_engines": [
                "DuckDuckGo API", "DuxDistributedGlobalSearch"
            ],
        },
    ]


@pytest.mark.asyncio
async def test_search_with_fallback_projects_attr_results(monkeypatch):
    """Preserve the legacy URL set return type"""
    async def fake_search_with_attrs(*_args, **_kwargs):
        return [
            {"url": "https://example.com/a", "search_engines": ["Alpha"]},
            {"url": "https://example.com/b", "search_engines": ["Beta"]},
        ]

    monkeypatch.setattr(run_module, "search_with_fallback_with_attrs",
                        fake_search_with_attrs)

    assert await search_with_fallback(["query"]) == {
        "https://example.com/a", "https://example.com/b"
    }


@pytest.mark.asyncio
async def test_search_with_fallback_with_attrs_global_fallback(monkeypatch):
    """Assign the successful global fallback engine to each URL"""
    calls = []

    async def fake_run_search(se_name, queries, *_args, **_kwargs):
        calls.append(se_name)
        if se_name == "APIDuckDuckGoSearch":
            return [[[]] for _ in queries]
        return [[["https://example.com/result"]] for _ in queries]

    monkeypatch.setattr(run_module, "_run_search", fake_run_search)

    results = await search_with_fallback_with_attrs(
        ["query"],
        search_engines=("APIDuckDuckGoSearch", "DuxDistributedGlobalSearch"),
        use_fallback_per_query=False,
    )

    assert calls == ["APIDuckDuckGoSearch", "DuxDistributedGlobalSearch"]
    assert results == [{
        "url": "https://example.com/result",
        "search_engines": ["DuxDistributedGlobalSearch"],
    }]


@pytest.mark.asyncio
async def test_search_with_fallback_with_attrs_empty_queries(monkeypatch):
    """Return no records when no queries are supplied"""
    async def fake_run_search(*_args, **_kwargs):
        return []

    monkeypatch.setattr(run_module, "_run_search", fake_run_search)

    assert await search_with_fallback_with_attrs([]) == []


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
