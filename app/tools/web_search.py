import asyncio
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class WebSearchTool:
    @staticmethod
    async def search_ddg(query: str, max_results: int = 5) -> list:
        loop = asyncio.get_running_loop()
        def _sync_search():
            try:
                with DDGS() as ddgs:
                    return [r for r in ddgs.text(query, max_results=max_results)]
            except Exception as e:
                logger.error(f"DuckDuckGo direct search error: {e}")
                return []
        return await loop.run_in_executor(None, _sync_search)
