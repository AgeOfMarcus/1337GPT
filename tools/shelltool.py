from langchain.tools import BaseTool
from subprocess import Popen, PIPE
from pydantic import Field
import platform

class ShellTool(BaseTool):
    name = 'RunCommand'
    description = (
        'Useful for running commands on the host system.'
        'Use this for testing code, or to execute shell commands.'
        'ONLY USE THIS WITH NON-BLOCKING COMMANDS. Always run commands with verbose mode when applicable.'
        f'Current host info: {str(platform.uname())}'
        'Accepts a string as input which will be executed.'
        'Returns a dict containing the keys "stdout" and "stderr".'
    )
    confirm_before_exec: bool = Field(default=True)

    def _sh(self, cmd: str) -> dict:
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        return {
            'stdout': stdout.decode(),
            'stderr': stderr.decode()
        }

    def input(self, prompt: str) -> str:
        if str(type(self.verbose)) == "<class 'method'>": # hack for tui
            return self.verbose(f'[red]{prompt}[/red]')
        else:
            return input(prompt)

    def _run(self, command: str) -> str:
        if self.confirm_before_exec:
            conf = self.input(f'[system] run the following command? `{command}`. [y]es/[N]o/[e]dit: ').lower()
            if conf.startswith('e'):
                new = self.input('enter new command: ')
                return self._sh(new)
            elif conf.startswith('y'):
                return self._sh(command)
            else:
                return {
                    'stdout':'',
                    'stderr':'User aborted the process before command was executed. Reformulate.'        
                }
    async def _arun(self, command):
        return self._run(command)