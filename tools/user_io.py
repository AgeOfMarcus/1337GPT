from langchain.tools import BaseTool

class TalkToUser(BaseTool):
    name = 'TalkToUser'
    description = (
        'Useful for asking the user for input.'
        'Use this when you need to ask the user for more information that you cannot find on your own.'
        'Do not ask the user something that you could find out yourself.'
        'Accepts a single argument type string, which will be displayed to the user.'
        'Returns a string response from the user.'
    )

    def _run(self, message: str) -> str:
        print(f'[ai: question]: {message}')
        return input('[user response]: ')
    async def _arun(self, message):
        return self._run(message)