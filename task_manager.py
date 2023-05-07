from langchain.callbacks.base import BaseCallbackHandler
from langchain.llms.base import BaseLLM
from langchain.tools import BaseTool
from code import InteractiveConsole
import json
import os

class EmptyCallbackHandler(BaseCallbackHandler):
    pass

def save_to_file(goal: str, result: dict):
    """Saves the results dict (second argument) to a file ending in '.result.txt' with the name set to the goal (first argument)"""
    fn = goal.replace(' ','_') + '.result.txt'
    print(f'saving final result to {fn}')
    with open(fn, 'w') as f:
        json.dump(result, f)

def convert_langchain_tools(tools: list[BaseTool]) -> list[dict]:
    """Converts a list of BaseTools (used in langchain) to a list of dictionaries containing the keys: 'name', and 'description'."""
    return [{'name': tool.name, 'description': tool.description} for tool in tools if type(tool) == BaseTool]

class TaskManager(object):
    """Task Manager"""
    current_tasks: list = []
    final_goal: str
    goal_completed: bool = False
    tools: list
    verbose: bool = True
    llm: BaseLLM
    final_result: dict = {}
    stored_info: dict = {}
    persist: str = None
    completed_tasks: dict = {}
    BASE_PROMPT: str = """
    You are a task management system. Your job is to create, reformulate, and refine a set of tasks. The tasks must be focused on achieving your final goal. It is very important you keep the final goal in mind as you think. Your goal is a constant, throughout, and will never change. 
    As tasks are completed, update your stored info with any info you will need to output at the end. As you go, add on to your final result. Your final result will be returned once, either, you cannot come up with any more reasonable tasks and all are complete, or your final result satisfies your final goal. 
    The language models assigned to your tasks will have access to a list of tools available. As language models, you cannot interact with the internet, however the following tools have been made available so that the final goal can be met. As the tasks you create will be given to other agents, make sure to be specific with each tasks instructions.

    Tools
    -----
    {tools_str}
    -----

    Final Goal
    ----------
    {final_goal}
    ----------

    Current values
    --------------
    current_tasks: {current_tasks}
    stored_info: {stored_info}
    final_result: {final_result}
    --------------
    """
    ENSURE_COMPLETE_PROMPT: str = '''
    Based on your current values, assess whether you have completed your final_goal. Respond with a dictionary in valid JSON format with the following keys:
    "final_result" - dict - reformat your final result to better meet your final goal,
    "goal_complete" - bool - True if you have completed your final_goal, otherwise False if you need to continue
    "current_tasks" - list - list of strings containing tasks in natural language which you will need to complete to meet your final_goal. leave this empty if you set "goal_complete" to True.

    You always give your responses in VALID, JSON READABLE FORMAT.
    '''
    REFINE_PROMPT: str = '''
    Task Result
    -----------
    task: {task}
    result: {result}
    -----------
    
    Refine your current set of tasks based on the task result above. E.g., if information has already been gathered that satisfies the requests in a task, it is not needed anymore. However, if information gathered shows a new task needs to be added, include it.
    If the result included any info you may need to complete later tasks, add it to your stored_info.
    If the result included any info you may need to satisfy your final goal, add it to the final result. Format it as necessary, but make sure it includes all information needed.
    You always give your response in valid JSON format so that it can be parsed (in python) with `json.loads`. Return a dictionary with the keys: "current_tasks" a list of strings (your complete set of tasks, if you need to, add any new tasks and reorder as you see fit), "final_result" a dict (your final result to satisfy your final goal, add to this as you go), "stored_info" a dict (info you may need for later tasks), if you have any thoughts to output to the user, include them as a string with the key "thoughts", and lastly, the key "goal_complete" should contain a boolean value True or False indicating if the final goal has been reached. 
    Make sure your list of tasks ends with a final task like "show results and terminate".
    '''
    TASK_PROMPT = '''
    You are one of many language models working on the same final goal: {final_goal}.

    Here is the list of tasks after yours needed to achieve this: {current_tasks}. Your job is to complete this one task: {task}.

    Here is some context from previous task results: {combined_info}. 

    {task}
    '''
    CREATE_PROMPT: str = 'Based on your end goal, come up with a list of tasks (in order) that you will need to take to achieve your goal.\nGive your response in valid JSON format so that it can be parsed (in python) with `json.loads`. Return a dictionary with the key "current_tasks" containing a list of strings. Make sure your list of tasks ends with a final step such as "show results and terminate".'
    FIX_JSON_PROMPT: str = """
    Reformat the following JSON without losing content so that it can be loaded without errors in python using `json.loads`. The following output returned an error when trying to parse. Make sure your response doesn't contain things like: new lines, tabs. Make sure your response uses double quotes as according to the JSON spec. Your response must include an ending quote and ending bracket as needed. ONLY RETURN VALID JSON WITHOUT FORMATTING. 

    Example of valid JSON: {example}

    Bad JSON: {bad_json}

    Error: {err}

    Good JSON: """
    GOOD_JSON_EXAMPLE: str = '''{"current_tasks": ["Research Amjad Masad's career and background.", "Create a CSV called \"career.csv\" and write his careers to it."], "stored_info": {"username": "amasad"}, "thoughts": "I will research his career and background, and then save the results to \"career.csv\"."}'''

    def _make_tools_str(self, tools: list) -> str:
        """Tools should be a list of dictionaries with the keys: "name" and "description"."""
        return '-----\n'.join(['\n'.join([f'{k}: {v}' for k, v in tool.items()]) for tool in tools]) # the fn name has an _ so it doesn't have to be readable, right?

    def _load_persist(self):
        if os.path.exists(self.persist):
            with open(self.persist, 'r') as f:
                saved = json.load(f)
            self.output_func(f'[system] Loaded stored info from: {self.persist}')
        else:
            saved = {}
            self.output_func(f'[system] Could not read {self.persist}, assuming new file. It will be created later.')
        self.stored_info = saved.get('stored_info', {})
        self.final_result = saved.get('final_result', {})
        self.current_tasks = saved.get('current_tasks', [])
        self.completed_tasks = saved.get('completed_tasks', {})
    def _save_persist(self):
        with open(self.persist, 'w') as f:
            json.dump({
                'stored_info': self.stored_info,
                'final_result': self.final_result,
                'current_tasks': self.current_tasks,
                'completed_tasks': self.completed_tasks
            }, f)
        self.output_func(f'saved stored info to: {self.persist}')
    
    def __init__(self, goal: str, tools: list, llm: BaseLLM, verbose: bool = True, output_func: callable = print, complete_func: callable = save_to_file, input_func: callable = input, current_tasks: list = None, final_result: dict = None, allow_repeat_tasks: bool = True, completed_tasks: dict = None, persist: str = None, confirm_tool: bool = False):
        """
        :param goal: str - final goal in natrual language
        :param tools: list - a list of tools (dicts) containing keys "name" and "description"
        :param llm: BaseLLM - LLM instance from langchain.llms

        :kwarg verbose: bool - defaults to True, if False, will not print updated info
        :kwarg allow_repeat_tasks: bool - defaults to True but you might want to disable, will not allow the bot to add tasks that have already been completed
        :kwarg output_func: callable - defaults to print, for verbose outout
        :kwarg input_func: callable - defaults to input, for user input
        :kwarg complete_func: callable - func to run when complete, accepts a goal (str) and results (dict), defaults to a func that saves to file
        :kwarg persist: str - defaults to None, but if set to a filepath, [stored_info, final_result, current_tasks] will be loaded and saved there
        :kwarg confirm_tool: bool - require user confirmation before running tools (default: False)
        :kwarg completed_tasks: dict - defaults to None for empty, already completed tasks for when allow_repeat_tasks=False (key = task name, value = task result), overwrites loaded tasks
        :kwarg current_tasks: list - defaults to None for empty, contains a list of (strings) tasks in natural language, overwrites loaded tasks
        :kwarg final_result: dict - defaults to None for empty, contains a dict of any results for the final goal, overwrites loaded result
        """
        self.llm = llm
        self.final_goal = goal
        self.tools = tools
        self.output_func = output_func
        self.complete_func = complete_func
        self.input_func = input_func
        self.allow_repeat_tasks = allow_repeat_tasks
        self.confirm_tool = confirm_tool
        self.verbose = verbose
        if persist: # load from file
            self.persist = persist
            self._load_persist()
        # overwrite from kwargs
        if current_tasks:
            self.current_tasks = current_tasks
        if final_result:
            self.final_result = final_result
        if completed_tasks:
            self.completed_tasks = completed_tasks
        

        if not self.current_tasks: # if no loaded tasks
            self._create_initial_tasks()

    def init_agent(self, agent, on_tool_start: callable = None, on_tool_end: callable = None):
        agent.callbacks[0].on_tool_start = on_tool_start or self._on_tool_start
        agent.callbacks[0].on_tool_end = on_tool_end or self._on_tool_end

    def format_task_str(self, task: str, smart_combine: bool = False, include_completed_tasks: bool = False):
        """
        Formats a task as a prompt which can be passed to an agent.

        :param task: str - task in natrual language
        :kwarg smart_combine: bool - defaults to False, I don't recommend using this, but if True will choose to include the larger out of final_result and stored_info
        :kwarg include_completed_tasks: bool - defaults to False, will include completed tasks (and results) if True, however this uses more tokens
        """
        if smart_combine:
            # its really not so smart but hey it works for me
            if len(str(self.final_result)) > len(str(self.stored_info)):
                combined_info = self.final_result
            else:
                combined_info = self.stored_info
        else:
            combined_info = {'final_result': self.final_result, 'stored_info': self.stored_info}
        if include_completed_tasks:
            combined_info['completed_tasks'] = self.completed_tasks
        
        return self.TASK_PROMPT.format(
            task=task, # task for agent, the rest is context
            current_tasks=self.current_tasks,
            final_goal=self.final_goal,
            combined_info=combined_info
        )

    def _base(self):
        return self.BASE_PROMPT.format(
            tools_str = self._make_tools_str(self.tools),
            final_goal = self.final_goal,
            current_tasks = self.current_tasks,
            final_result = self.final_result,
            stored_info=self.stored_info
        )

    def fix_json(self, bad_json: str, err: Exception = None, retry: int = 1) -> dict:
        """
        Uses the LLM to try fix JSON response. Prompt: `self.FIX_JSON_PROMPT`

        :param bad_json: str - invalid json
        :kwarg err: Exception - err that it caused when tryna load
        :kwarg retry: int - number of times to retry
        """
        
        self.output_func(f'[system] fixing ai JSON output ({retry} retries left)...')
        resp = self.llm(self.FIX_JSON_PROMPT.format(bad_json=bad_json, err=err, example=self.GOOD_JSON_EXAMPLE))
        try:
            return json.loads(resp.strip())
        except json.JSONDecodeError as e:
            self.output_func('[system] cannot parse ai result as JSON: ' + str(e))
            if retry > 0:
                return self.fix_json(resp, err=e, retry=(retry - 1))
            else:
                console = InteractiveConsole(locals())
                console.interact('dropping into debug shell, if you can fix it, set the variable "fixed" to the loaded json. data is in "resp". use ctrl+d to exit')
                return console.locals.get('fixed', {'error': 'could not parse json response'})
                
    def _load_json(self, json_str: str):
        json_str = json_str.replace('\t', '').replace('    ', '').replace('        ', '').replace('\n', '').replace('            ', '').strip()
        try:
            return True, json.loads(json_str)
        except json.JSONDecodeError:
            pass
        if not json_str.endswith('}'):
            if not (json_str.endswith('"') or json_str.endswith("'")):
                json_str += '"' if '"' in json_str else "'"
            json_str += '}'
        try:
            return True, json.loads(json_str)
        except json.JSONDecodeError:
            return False, json_str
            
    def load_json(self, json_str: str, retry: int = 1) -> dict:
        """
        Try loading a json_str, retrying 1 times by default. 
        First tries manually, then uses LLM.
        """
        try:
            ok, res = self._load_json(json_str) # try fix manually
            return res if ok else json.loads(res) # trigger err if not ok
        except json.JSONDecodeError as e:
            return self.fix_json(json_str, err=e, retry=retry)

    def _create_initial_tasks(self):
        """This gets called during __init__"""
        prompt = self._base() + self.CREATE_PROMPT
        resp = self.llm(prompt)
        res = self.load_json(resp)

        if self.verbose:
            self.output_func('[system] ai created task list: ' + ', '.join(res['current_tasks']))
        self.current_tasks = res['current_tasks']

    def _on_tool_start(self, tool, input_str, **kwargs):
        """Set the agent.callback_manager.on_tool_start to this to save tool inputs to self.stored_info['tools_used']."""
        self.stored_info['tools_used'] = [*self.stored_info.get('tools_used', []), {'tool': tool, 'input': input_str}]
    def _on_tool_end(self, output, **kwargs):
        """Set the agent.callback_manager.on_tool_end to this to save tool outputs to self.stored_info['tool_used']."""
        self.stored_info['tools_used'][-1]['output'] = output
    
    def refine(self, task_name: str, task_result: str):
        """
        Use this after a task has been completed. This will update the current_tasks, final_result, stored_info, and completed_tasks - saving if persist is set. Uses base prompt plus `self.REFINE_PROMPT`. Returns True if goal has been met.

        :param task_name: str - task in natural language
        :param task_result: str - output from agent
        """
        self.completed_tasks[task_name] = task_result
        needs_save = False
        prompt = self._base() + self.REFINE_PROMPT.format(
            task = task_name,
            result = task_result
        )
        resp = self.llm(prompt)
        res = self.load_json(resp)

        if (err := res.get('error')):
            self.output_func(f'[system] skipping due to error: {err}')
            return
        
        if (thoughts := res.get('thoughts')):
            self.output_func(f'[ai] {thoughts}')
        if res.get('goal_complete'):
            self.current_tasks = [] # clear remaining tasks
            self.output_func('[system] goal complete')
            self.complete_func(self.final_goal, {
                'final_result': {**self.final_result, **res['final_result']},
                'completed_tasks': self.completed_tasks,
                'stored_info': self.stored_info,
            })
            self.goal_completed = True

        if (current_tasks := res.get('current_tasks')):
            needs_save = True
            self.add_tasks(current_tasks)
        if (stored_info := res.get('stored_info')):
            needs_save = True
            if self.verbose:
                self.output_func(f'[system] new info: {stored_info}')
            self.stored_info.update(stored_info)
        if (final_result := res.get('final_result')):
            needs_save = True
            if self.verbose:
                self.output_func(f'[system] new final result: {final_result}')
            self.final_result.update(final_result)

        if needs_save and self.persist:
            self._save_persist()

    def add_tasks(self, current_tasks: list):
        if self.allow_repeat_tasks:
            if self.verbose:
                self.output_func(f'[system] new tasks: {current_tasks}')
            self.current_tasks = current_tasks
        else:
            new_current_tasks = []
            for task in current_tasks:
                if not task in self.completed_tasks.keys():
                    new_current_tasks.append(task)
            self.output_func(f'[system] new tasks: {new_current_tasks} (skipped: {", ".join(t for t in new_current_tasks if not t in current_tasks)})')
            self.current_tasks = new_current_tasks

    def ensure_goal_complete(self):
        prompt = self._base() + self.ENSURE_COMPLETE_PROMPT
        resp = self.llm(prompt)
        res = self.load_json(resp)

        if (final_result := res.get('final_result')):
            if self.verbose:
                self.output_func(f'[system] new final result: {final_result}')
            self.final_result.update(final_result)
        if (current_tasks := res.get('current_tasks')):
            self.add_tasks(current_tasks)

        if res.get('goal_complete'):
            self.output_func('[system] Goal completed!')
            self.complete_func(self.final_goal, {
                'final_result': self.final_result,
                'completed_tasks': self.completed_tasks,
                'stored_info': self.stored_info,
            })
            self.current_tasks = []
            self.goal_completed = True
            return True
        else:
            return False