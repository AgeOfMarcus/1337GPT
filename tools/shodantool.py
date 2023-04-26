from langchain.tools import BaseTool
from langchain.tools.base import Field
import os
try:
    from shodan import Shodan
except ImportError:
    if os.getenv('REPL_SLUG'):
        # replit workaround
        os.system('pip install shodan')
        from shodan import Shodan
    else:
        exit('Please install the python shodan library using `pip install shodan`.')

class ShodanTool(BaseTool):
    name = 'Shodan-io'
    description = (
        "Useful for searching the shodan.io API for servers."
        "Use this for information gathering on a target."
        "Accepts a single string argument containing the full search query."
        "Returns a list of matches in dict format with the keys 'data', 'hostname', 'ip', 'port', 'os', etc."
    )
    shodan_api_key: str = Field(default_factory=lambda: os.getenv('SHODAN'))

    def _run(self, query: str) -> list:
        shodan = Shodan(self.shodan_api_key)
        try:
            res = shodan.search(query)
        except Exception as e:
            return f'Error: {str(e)}'
        return res['matches']
    async def _arun(self, query):
        return self._run(query)