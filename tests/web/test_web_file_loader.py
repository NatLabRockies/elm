# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""ELM Web file loading tests"""
import asyncio
import filecmp
from pathlib import Path
from functools import partial
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import pytest
import pdftotext

from elm import TEST_DATA_DIR
from elm.web.file_loader import AsyncWebFileLoader, AsyncLocalFileLoader
from elm.web.document import PDFDocument, HTMLDocument
import elm.web.html_pw
import elm.utilities.retry

GPT4_DOC_PATH = Path(TEST_DATA_DIR) / "GPT-4.pdf"
WHATCOM_DOC_PATH = Path(TEST_DATA_DIR) / "Whatcom.txt"


class MockResponse:
    """Mock web response for tests."""

    def __init__(self, read_return):
        """Store the desired read response."""
        self.read_return = read_return
        self.content_type = "application/pdf"
        self.charset = "utf-8"
        self.headers = {}

    async def read(self):
        """Return what class was initialized with."""
        return self.read_return


@asynccontextmanager
async def patched_get(session, url, *args, **kwargs):
    """Patched implementation for get that reads from disk."""
    if url == "gpt-4":
        with open(GPT4_DOC_PATH, "rb") as fh:
            content = fh.read()
    elif url == "Whatcom":
        with open(WHATCOM_DOC_PATH, "rb") as fh:
            content = fh.read()

    yield MockResponse(content)


async def patched_get_html(url, *args, **kwargs):
    """Patched implementation for html get that reads from disk."""
    with open(WHATCOM_DOC_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    return content


@pytest.mark.asyncio
async def test_async_file_loader_basic_pdf(monkeypatch):
    """Test `AsyncWebFileLoader` for a basic PDF doc"""

    monkeypatch.setattr(
        aiohttp.ClientSession,
        "get",
        patched_get,
        raising=True,
    )

    loader = AsyncWebFileLoader()
    doc = await loader.fetch("gpt-4")

    with open(GPT4_DOC_PATH, "rb") as fh:
        pdf = pdftotext.PDF(fh, physical=True)

    truth = PDFDocument(pdf)

    assert doc.text == truth.text
    assert doc.attrs["source"] == "gpt-4"
    assert "cache_fn" not in doc.attrs


@pytest.mark.asyncio
async def test_async_file_loader_basic_html(monkeypatch):
    """Test `AsyncWebFileLoader` for a basic HTML doc"""

    monkeypatch.setattr(
        aiohttp.ClientSession,
        "get",
        patched_get,
        raising=True,
    )
    monkeypatch.setattr(
        elm.web.html_pw,
        "_load_html",
        patched_get_html,
        raising=True,
    )

    loader = AsyncWebFileLoader()
    doc = await loader.fetch("Whatcom")

    with open(WHATCOM_DOC_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    truth = HTMLDocument([content])

    assert doc.text == truth.text
    assert doc.attrs["source"] == "Whatcom"
    assert "cache_fn" not in doc.attrs


@pytest.mark.asyncio
async def test_async_file_loader_fetch_all(monkeypatch, tmp_path):
    """Test `AsyncWebFileLoader.fetch_all` function for basic docs"""

    monkeypatch.setattr(
        aiohttp.ClientSession,
        "get",
        patched_get,
        raising=True,
    )
    monkeypatch.setattr(
        elm.web.html_pw,
        "_load_html",
        patched_get_html,
        raising=True,
    )

    def _write_file(doc, content):
        out_fn = doc.attrs["source"]
        out_fp = tmp_path / f"{out_fn}.{doc.FILE_EXTENSION}"
        with open(out_fp, **doc.WRITE_KWARGS) as fh:
            fh.write(content)
        if doc.attrs["source"] == "gpt-4":
            return None
        return out_fp

    async def _cache_file(doc, content):
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            pool, partial(_write_file, doc, content)
        )
        return result

    assert not list(tmp_path.glob("*"))

    with ThreadPoolExecutor() as pool:
        loader = AsyncWebFileLoader(file_cache_coroutine=_cache_file)
        docs = await loader.fetch_all("gpt-4", "Whatcom")

    assert len(docs) == 2

    with open(GPT4_DOC_PATH, "rb") as fh:
        pdf = pdftotext.PDF(fh, physical=True)

    truth_pdf = PDFDocument(pdf)

    with open(WHATCOM_DOC_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    truth_html = HTMLDocument([content])

    assert docs[0].text == truth_pdf.text
    assert docs[0].attrs["source"] == "gpt-4"
    assert "cache_fn" not in docs[0].attrs

    assert docs[1].text == truth_html.text
    assert docs[1].attrs["source"] == "Whatcom"
    assert docs[1].attrs["cache_fn"].stem == "Whatcom"

    assert len(list(tmp_path.glob("*"))) == 2
    assert filecmp.cmp(GPT4_DOC_PATH, list(tmp_path.glob("*.pdf"))[0])

    html_file = list(tmp_path.glob("*.txt"))[0]
    assert not filecmp.cmp(WHATCOM_DOC_PATH, html_file)
    with open(html_file, "r", encoding="utf-8") as fh:
        assert truth_html.text == fh.read()


@pytest.mark.asyncio
async def test_async_local_file_loader_basic_html():
    """Test `AsyncLocalFileLoader` for a basic HTML doc"""

    loader = AsyncLocalFileLoader(doc_attrs={"test_1": 1})
    doc = await loader.fetch(WHATCOM_DOC_PATH)

    with open(WHATCOM_DOC_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    truth = HTMLDocument([content])

    assert doc.text == truth.text
    assert doc.attrs["source_fp"] == WHATCOM_DOC_PATH
    assert doc.attrs["test_1"] == 1
    assert "cache_fn" not in doc.attrs


@pytest.mark.asyncio
async def test_async_local_file_loader_basic_pdf():
    """Test `AsyncLocalFileLoader` for a basic PDF doc"""

    loader = AsyncLocalFileLoader()
    doc = await loader.fetch(GPT4_DOC_PATH)

    with open(GPT4_DOC_PATH, "rb") as fh:
        pdf = pdftotext.PDF(fh, physical=True)

    truth = PDFDocument(pdf)

    assert doc.text == truth.text
    assert doc.attrs["source_fp"] == GPT4_DOC_PATH
    assert "test_1" not in doc.attrs
    assert "cache_fn" not in doc.attrs


@pytest.mark.asyncio
async def test_async_file_loader_response_hook(monkeypatch):
    """Test the response hook receives each fetched URL's response"""

    monkeypatch.setattr(
        aiohttp.ClientSession,
        "get",
        patched_get,
        raising=True,
    )

    seen = []

    async def hook(url, response, body):
        seen.append((url, response.content_type, len(body)))

    loader = AsyncWebFileLoader(on_response_hook=hook)
    assert loader.content_fetcher.on_response_hook is hook
    doc = await loader.fetch("gpt-4")

    assert not doc.empty
    assert seen == [("gpt-4", "application/pdf", GPT4_DOC_PATH.stat().st_size)]

    assert AsyncWebFileLoader().content_fetcher.on_response_hook is None


@pytest.mark.asyncio
async def test_async_file_loader_error_hook(monkeypatch):
    """Test the error hook reports why no response was received"""

    async def no_sleep(*__, **___):
        """Skip the wait between retries"""

    monkeypatch.setattr(elm.utilities.retry.asyncio, "sleep", no_sleep)

    def refuse(session, url, *args, **kwargs):
        raise aiohttp.ClientConnectionError("connection refused")

    monkeypatch.setattr(aiohttp.ClientSession, "get", refuse, raising=True)

    seen = []

    async def hook(url, error):
        seen.append((url, error))

    loader = AsyncWebFileLoader(on_error_hook=hook)
    assert loader.content_fetcher.on_error_hook is hook
    assert await loader.content_fetcher.fetch("gpt-4") is None

    assert len(seen) == 1
    url, error = seen[0]
    assert url == "gpt-4"
    assert isinstance(error, aiohttp.ClientConnectionError)
    assert str(error) == "connection refused"


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
