from langchain.callbacks.base import BaseCallbackHandler
# rich
from rich.live import Live
from rich.table import Table, Row
from rich.json import JSON
import json, os, math
# task_manager.py
from task_manager import TaskManager

try:
    if os.name == 'nt':
        # windows
        from msvcrt import getch as _getch
        getch = lambda: _getch().decode()
    else:
        # linux based
        from getch import getch
except ImportError as e:
    lib = str(e).split("'")[1]
    exit(f'This program requires the {lib} library. Please install it with `pip install {lib}`')

# by god I will turn this Table into a TUI
class TUI(object):
    def __init__(self):
        self.max_lines = os.get_terminal_size().lines - 12
        self.total_cols = os.get_terminal_size().columns - 6

        # if total_cols is odd, make it even
        if self.total_cols % 2 == 1:
            self.total_cols -= 1
        
        self.half_cols = self.total_cols // 2

        self.table = Table(title='1337GPT')
        self.table.add_column('Data')
        self.table.add_column('Console')

        for i in range(self.max_lines):
            self.table.add_row(' ' * self.half_cols, ' ' * self.half_cols)

        self.console = Console(self)
    
    def pad(self, text):
        return text.ljust(self.half_cols)

class Console(object):
    def __init__(self, tui: TUI):
        self.tui = tui
        self.history = []
        self._input = ''
    
    def getlines(self):
        return self.tui.table.columns[1]._cells

    def checklines(self, line):
        chars = len(line)
        if chars > self.tui.half_cols:
            over = chars / self.tui.half_cols
            return math.ceil(over)
        return 1
    
    def add_line(self, line):
        # pad line
        line = self.tui.pad(line)
        _lines = self.checklines(line)

        lines = self.getlines()
        for i in range(_lines):
            self.history.append(lines.pop(0))
        lines.append(line)
        self.tui.table.columns[1]._cells = lines
    
    def print(self, *args):
        self.add_line(' '.join(map(repr, args)))
    
    def update_last(self, text):
        lines = self.getlines()
        lines[-1] = self.tui.pad(text)
        if (_ := self.checklines(text)) > 1:
            for i in range(_ - 1):
                self.history.append(lines.pop(0))
        self.tui.table.columns[1]._cells = lines
    
    def input(self, prompt):
        self.add_line(prompt)
        while True:
            ch = getch()
            if ch == '\x03':
                raise KeyboardInterrupt
            elif ch in ('\n', '\r'):
                inp = self._input
                self._input = ''
                return inp
            elif (ord(ch) == 127) or (ch in ('\b', '\x08')):
                self._input = self._input[:-1]
                self.update_last(prompt + self._input)
            else:
                self._input += ch
                self.update_last(prompt + self._input)

def update_data_from_taskman(taskman: TaskManager, tui: TUI):
    data = JSON(json.dumps({
        'Goal': taskman.final_goal,
        'Next Task': taskman.current_tasks[0],
        'Stored Info': taskman.stored_info,
        'Final Result': taskman.final_result
    })).text
    for i, line in enumerate(data.split('\n')):
        try:
            tui.table.columns[0]._cells[i] = line
        except IndexError:
            tui.table.columns[0]._cells.append(line) # not gonna show but oh well its there


def main(taskman: TaskManager, agent, args):
    tui = TUI()
    taskman.output_func = tui.console.print
    taskman.input_func = tui.console.input

    class TUIHandler(BaseCallbackHandler):
        def on_tool_start(self, tool, args, **kwargs):
            tui.console.add_line(f'Starting tool [green]{tool["name"]}[/green] with args [green]{args}[/green]')
        
        def on_tool_end(self, out, **kwargs):
            tui.console.add_line(f'Tool finished with output [darkgreen]{out}[/darkgreen]')
    
    cb_handler = TUIHandler()
    
    taskman.verbose = False # not needed as left pane shows info
    agent.verbose = False # cant redirect these outputs

    # patch input func
    for tool in agent.tools:
        if tool.name == 'RunCommand':
            tool.verbose = tui.console.input # yes this is dirty, but i cant create my own attr

    with Live(tui.table, refresh_per_second=30):

        # main loop
        while not taskman.goal_completed:
            update_data_from_taskman(taskman, tui)
            if not taskman.current_tasks:
                if taskman.ensure_goal_complete():
                    break
                continue
            
            task = taskman.current_tasks.pop(0)
            tui.console.add_line(f'[grey]Next task: {task}[/grey]')
            cont = tui.console.input('[blue]Continue?[/blue] \[Y]es/\[n]o/\[e]dit: ')[0].lower()
            if cont == 'n':
                continue
            elif cont == 'e':
                task = tui.console.input('[cyan]Enter task[/cyan]: ')
            
            res = agent.run(taskman.format_task_str(
                task,
                smart_combine=args.use_smart_combine,
                include_completed_tasks=args.include_completed_tasks
            ), callbacks=[cb_handler])
            taskman.refine(task, res)