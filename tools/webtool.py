from langchain.tools import BaseTool
from bs4 import BeautifulSoup
import requests, os

class ScrapeTool(BaseTool):
    name = "ScrapeTool"
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

class WebReadTool(BaseTool):
    name = 'WebsiteReader'
    description = (
        "Reads the HTML content of a website excluding script and style tags."
        "Useful for reading the contents of a website URL."
        "The input to this tool should be a URL."
    )

    def _run(self, url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'
        }
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        for script in soup(['script', 'style']):
            script.extract()
        
        text = soup.get_text()
        lines = [line.strip() for line in text.splitlines()]
        chunks = [phrase.strip() for line in lines for phrase in line.split('  ')]
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    async def _arun(self, url: str) -> str:
        return self._run(url)