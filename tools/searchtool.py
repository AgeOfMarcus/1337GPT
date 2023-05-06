from langchain.tools import BaseTool
from googlesearch_py import search
from duckduckgo_search import ddg

class GoogleSearchTool(BaseTool):
    name = "GoogleSearch"
    description = "searches google. Useful for when you need to get information about current events. The input to this tool should be a search query"

    def _run(self, query: str) -> list:
        return list(search(query))
        #return [str(res) for res in search(query)]

    async def _arun(self, query: str) -> list:
        return self._run(query)

class DDGSearchTool(BaseTool):
    name = 'DuckDuckGo'
    description = (
        "Searches DuckDuckGo."
        "Useful for when you need to get information about current events."
        "The input to this tool should be a search query."
        "Returns a list of dicts containing a url, title, and description."
    )

    def _run(self, query: str) -> list:
        return ddg(query)
    
    async def _arun(self, query: str) -> list:
        return self._run(query)