from langchain.tools import BaseTool
from subprocess import Popen, PIPE
from pydantic import Field
import platform

class ShellTool(BaseTool):
    name = 'RunCommand'
    description = (
        'Useful for running commands on the host system.'
        'Use this for testing code, or to execute shell commands.'
        'ONLY USE THIS WITH NON-BLOCKING COMMANDS.'
        f'Current host info: {str(platform.uname())}'
        'Accepts a string as input which will be executed.'
        'Returns a dict containing the keys "stdout" and "stderr".'
    )
    confirm_before_exec: bool = Field(default=True)

    def _run(self, command: str) -> str:
        if input(f'[system] run the following command? `{command}`. y/N: ').lower().startswith('y'):
            proc = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
            res = proc.communicate()
            return {'stdout': res[0].decode(), 'stderr': res[1].decode()}
        else:
            return 'Error: User aborted before command could execute.'
    async def _arun(self, command):
        return self._run(command)