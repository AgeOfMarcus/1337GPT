from dotenv import load_dotenv; load_dotenv()

from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.llms import GPT4All
# task_manager.py
from task_manager import TaskManager, convert_langchain_tools, EmptyCallbackHandler
# prompt.py - recycled
from prompt import AGENT_PREFIX, AGENT_FORMAT_INSTRUCTIONS, AGENT_SUFFIX
# tools/
from tools import TOOLS

# parse arguments
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('--goal', '-g', help='Goal for task manager to complete.', required=True)
parser.add_argument('--tui', help='Use the Terminal User Interface. Default False.', action='store_true', default=False)
parser.add_argument('--persist', '-p', help='File to persist data to. If not set, persist will be disabled.', default=False)
parser.add_argument('--repeat', '-r', help='Allow repeat tasks. Default False.', action='store_true', default=False)
parser.add_argument('--model', '-m', help='Model to use for chat. Default gpt-4.', default='gpt-4')
parser.add_argument('--temperature', help='Temperature for chat model. Default 0.', default=0)
parser.add_argument('--tools', '-t', help=f'Comma separated list of tools to use (from: {", ".join(TOOLS.keys())}) . Default: DDGSearch,Shell', default='DDGSearch,Shell')
parser.add_argument('--tool-args', help="A dictionary containing kwargs that will be passed to tools as they are initialized. Default: {'Shell': {'confirm_before_exec': True}}", type=dict, default={'Shell': {'confirm_before_exec': True}})
parser.add_argument('--use-smart-combine', help='Uses smart combination when formatting info for agents. Default False. Use this if your prompts are getting too large.', action='store_true', default=False)
parser.add_argument('--include-completed-tasks', help='Include completed tasks in the prompt for agents. Default True. Turn this off for less tokens used.', action='store_false', default=True)
args = parser.parse_args()

# chat model for agent
llm = GPT4All(
    model=args.model,
    temp=args.temperature,
    backend='gptj',
    verbose=(not args.tui) # if tui, don't print
)
# memory for agent
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    output_key='output', 
    return_messages=True
)
# tools i wrote for the agent, can be used with any langchain program, from ./tools/
tools = []
for tool in args.tools.split(','):
    obj = TOOLS[tool]
    if type(obj) == list:
        tools += list(map(lambda x: x(**args.tool_args.get(tool, {})), obj))
    else:
        tools.append(obj(**args.tool_args.get(tool, {})))

# create an instance of TaskManager
taskman = TaskManager(
    args.goal, # goal
    convert_langchain_tools(tools), # list of dicts of tools
    GPT4All(
        model=args.model,
        temp=0,
        backend='gptj',
        verbose=(not args.tui) # if tui, don't print
    ), # llm for taskmanager
    persist=args.persist, # i want to persist data
    allow_repeat_tasks=args.repeat, # so it doesn't get stuck in a loop
)

# now the agent for doing tasks
agent = initialize_agent(
    tools, # list of BaseTool objects
    llm, # our chat model
    memory=memory, # the memory we created
    agent = AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, # const
    agent_kwargs={
        'prefix': AGENT_PREFIX,
        'format_instructions': AGENT_FORMAT_INSTRUCTIONS,
        'suffix': AGENT_SUFFIX
    },
    callbacks=[EmptyCallbackHandler()], # so that we can dynamically add with taskman.init_agent
    verbose=True # so we can see when it runs each tool
)
# this lets us save tool outputs
taskman.init_agent(agent)

# lightweight example task loop
def main():
    while not taskman.goal_completed:
        if not taskman.current_tasks:
            if taskman.ensure_goal_complete(): # makes sure we're done
                break
            continue # if not complete, more tasks will be added
        task = taskman.current_tasks.pop(0) # get first task
        print('\n\nNext task:', task)
        cont = input('Continue? [Y]es/[n]o/[e]dit: ').lower()
        if cont.startswith('n'):
            continue # skips task
        elif cont.startswith('e'):
            task = input('New task: ')
        res = agent.run(taskman.format_task_str(
            task,
            smart_combine=args.use_smart_combine, # i don't recommend using this lol
            include_completed_tasks=args.include_completed_tasks # this one, maybe so
        )) # task result
        taskman.refine(task, res) # refine process for taskmanager

if __name__ == '__main__':
    if args.tui:
        from tui import main as tui_main
        tui_main(taskman, agent, args)
    else:
        main() # f it we ball
