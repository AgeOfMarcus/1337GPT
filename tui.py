from rich.live import Live
from rich.table import Table, Row
from rich.json import JSON
import json, os
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
        self.max_lines = os.get_terminal_size().lines - 7
        self.total_cols = os.get_terminal_size().columns - 4

        # if total_cols is odd, make it even
        if self.total_cols % 2 == 1:
            self.total_cols -= 1
        
        self.half_cols = self.total_cols // 2

        self.table = Table(title='1337GPT')
        self.table.add_column('Data')
        self.table.add_column('Console')

        for i in range(os.get_terminal_size().lines - 7):
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
    
    def add_line(self, line):
        # pad line
        line = self.tui.pad(line)

        lines = self.getlines()
        self.history.append(lines.pop(0))
        lines.append(line)
        self.tui.table.columns[1]._cells = lines
    
    def print(self, *args):
        self.add_line(' '.join(map(repr, args)))
    
    def update_last(self, text):
        lines = self.getlines()
        lines[-1] = self.tui.pad(text)
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
            elif ord(ch) == 127:
                self._input = self._input[:-1]
                self.update_last(prompt + self._input)
            else:
                self._input += ch
                self.update_last(prompt + self._input)

def update_data_from_taskman(taskman: TaskManager, tui: TUI):
    data = JSON(json.dumps({
        'Goal': taskman.final_goal,
        'Tasks': taskman.current_tasks,
        'Stored Info': taskman.stored_info,
        'Final Result': taskman.final_result
    })).text
    for i, line in enumerate(data.split('\n')):
        tui.table.columns[0]._cells[i] = line

def test():
    # put this at the end of the file
    tui = TUI()
    console = Console(tui)

    with Live(tui.table, refresh_per_second=10): # increased refresh for typing
        while True:
            cmd = console.input('>>> ')
            if cmd in ('exit', 'break', 'exit()'):
                break
            res = eval(cmd)
            console.print(cmd)

def main(taskman: TaskManager, agent, args):
    tui = TUI()
    update_data_from_taskman(taskman, tui)
    taskman.output_func = tui.console.print
    taskman.input_func = tui.console.input
    taskman.init_agent(
        agent,
        on_tool_start = lambda tool, args: tui.console.add_line(f'Starting tool {tool} with args {args}'),
        on_tool_end = lambda out: tui.console.add_line(f'Tool finished with output {out}')
    )
    taskman.verbose = False
    agent.verbose = False

    with Live(tui.table, refresh_per_second=10):
        __import__('time').sleep(0.5) # for some reason the first line doesn't show up
        while not taskman.goal_completed:
            if not taskman.current_tasks:
                if taskman.ensure_goal_complete():
                    break
                continue
            
            task = taskman.current_tasks.pop(0)
            tui.console.add_line(f'Next task: {task}')
            cont = tui.console.input('Continue? [Y]es/\[n]o/\[e]dit: ')
            if cont == 'n':
                continue
            elif cont == 'e':
                task = input('Enter task: ')
            
            res = agent.run(taskman.format_task_str(
                task,
                smart_combine=args.use_smart_combine,
                include_completed_tasks=args.include_completed_tasks
            ))
            taskman.refine(task, res)
            update_data_from_taskman(taskman, tui)