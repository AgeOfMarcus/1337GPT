from langchain.tools import BaseTool
from googlesearch_py import search

class SearchTool(BaseTool):
    name = "Search"
    description = "searches google. Useful for when you need to get information about current events. The input to this tool should be a search query"

    def _run(self, query: str) -> list:
        return list(search(query))
        #return [str(res) for res in search(query)]

    async def _arun(self, query: str) -> list:
        return self._run(query)