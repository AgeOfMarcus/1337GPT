# About

These are tools I have written to extend the functionality of `1337GPT`. Here is a basic example of how to build a [langchain tool](https://python.langchain.com/en/latest/modules/agents/tools.html):

```python
from langchain.tools import BaseTool

class MyTool(BaseTool):
    name = 'ToolName'
    description = (
        "Description of tool"
        "Useful for ..."
        "Use this when ..."
        "Accepts ... as input, returns ..."
    )

    # gets called when ran synchronously
    def _run(self, argument):
        return 'thing'
    
    # gets called when ran asynchronously
    async def _arun(self, argument):
        # if you don't want to implement, do the following
        return self._run(argument)
```

# Tools with requirements

* **GoogleSearch** requires `googlesearch.py`
* **DDGSearch** requires `duckduckgo-search`
* **Shodan** requires `shodan`

# Tools requiring an API key

* **Shodan** - If you are using a **free API key**, it helps to specify that in your goal for `1337GPT`