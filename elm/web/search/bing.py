# -*- coding: utf-8 -*-
"""ELM Web Scraping - Bing search"""
import random
import asyncio
import logging

from elm.web.search.base import (PlaywrightSearchEngineLinkSearch,
                                 APISearchEngineLinkSearch,
                                 PatchedSerpApiClient,
                                 format_search_results)


logger = logging.getLogger(__name__)


class PlaywrightBingLinkSearch(PlaywrightSearchEngineLinkSearch):
    """Search for top links on the main Bing search engine"""

    MAX_RESULTS_CONSIDERED_PER_PAGE = 3
    """Number of results considered per Bing page.

    This value used to be 10, but the addition of extra divs like a set
    of youtube links has brought this number down."""

    _SE_NAME = "Bing"
    _SE_URL = "https://www.bing.com/"
    _SE_SR_TAG = '[redirecturl]'
    _SE_QUERY_URL = "https://www.bing.com/search?q={}&FORM=QBLH"

    async def _perform_homepage_search(self, page, search_query):
        """Fill in search bar with user query and hit enter"""
        await self._move_mouse(page)

        logger.trace("Finding search bar for query: %r", search_query)
        search_bar = page.locator('[id="sb_form_q"]')
        await self._move_and_click(page, search_bar)
        await asyncio.sleep(random.uniform(0.5, 1.5))

        logger.trace("Typing in query: %r", search_query)
        await page.keyboard.type(search_query, delay=random.randint(80, 150))
        await asyncio.sleep(random.uniform(0.5, 1.5))

        logger.trace("Hitting enter for query: %r", search_query)
        await page.keyboard.press('Enter')


class SerpAPIBingSearch(APISearchEngineLinkSearch):
    """Search Bing for links using the SerpAPI service"""

    _SE_NAME = "SerpAPI (Bing)"

    API_KEY_VAR = "SERPAPI_KEY"
    """Environment variable that should contain the SerpAPI key"""

    def __init__(self, api_key=None, verify=False, param_kwargs=None):
        """

        Parameters
        ----------
        api_key : str, optional
            API key for serper search API. If ``None``, will look up the
            API key using the ``"SERPAPI_KEY"`` environment variable.
            By default, ``None``.
        verify : bool, default=False
            Option to use SSL verification when making request to API
            endpoint. By default, ``False``.
        param_kwargs : dict, optional
            Additional parameters to be passed to the SerpAPI client.
            By default, ``None``.
        """
        super().__init__(api_key=api_key)
        self.verify = verify
        self.param_kwargs = param_kwargs or {}

    async def _search(self, query, num_results=10, raw=False):
        """Search web for links related to a query"""

        params = {"q": query, "cc": "us", "api_key": self.api_key}
        params.update(self.param_kwargs)

        client = PatchedSerpApiClient(params, engine="bing",
                                      verify=self.verify)
        results = await client.async_get_dict()
        results = (results or {}).get("organic_results", [])
        return format_search_results(self._SE_NAME, query, results,
                                     url_key="link", raw=raw)[:num_results]
