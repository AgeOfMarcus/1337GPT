"""
Now unused as it's pretty useless.
"""
from langchain.tools import BaseTool
import requests, os

class ReadTool(BaseTool):
    name = "Read"
    description = "scrapes the main text content of a website (does not include HTML). Useful for when you need to read the plaintext content of a website. The input to this tool should be a URL"

    def scrape_website(self, url: str) -> str:
        if not url.startswith('http'):
            url = f'https://{url}'
        r = requests.get(f'https://extractorapi.com/api/v1/extractor/?apikey={os.getenv("EXTRACTOR")}&url={url}')
        return r.json()['text']

    def _run(self, url: str) -> str:
        return self.scrape_website(url)

    async def _arun(self, url) -> str:
        return self._run(url)