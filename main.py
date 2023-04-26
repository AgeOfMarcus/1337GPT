from dotenv import load_dotenv; load_dotenv()

from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
# task_manager.py
from task_manager import TaskManager, convert_langchain_tools
# prompt.py - recycled
from prompt import SEARCHGPT_PREFIX, SEARCHGPT_FORMAT_INSTRUCTIONS, SEARCHGPT_SUFFIX
# tools/
from tools import SearchTool, TalkToUser, ShellTool, ShodanTool

# chat model for agent
llm = ChatOpenAI(
    temperature=0, 
    model_name='gpt-4'
)
# memory for agent
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    output_key='output', 
    return_messages=True
)
# tools i wrote for the agent, can be used with any langchain program, from ./tools/
tools = [SearchTool(), ShellTool(confirm_before_exec=True), TalkToUser(), ShodanTool()]

# create an instance of TaskManager
taskman = TaskManager(
    'Find outdated servers on the usf.edu network. Use the shodan.io api to find hosts.', # goal
    convert_langchain_tools(tools), # list of dicts of tools
    OpenAI(temperature=0), # llm for taskmanager
    persist='pentest.json', # i want to persist data
    allow_repeat_tasks=False # so it doesn't get stuck in a loop
)

# now the agent for doing tasks
agent = initialize_agent(
    tools, # list of BaseTool objects
    llm, # our chat model
    memory=memory, # the memory we created
    agent = AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, # const
    agent_kwargs={
        'prefix': SEARCHGPT_PREFIX,
        'format_instructions': SEARCHGPT_FORMAT_INSTRUCTIONS,
        'suffix': SEARCHGPT_SUFFIX
    },
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
            smart_combine=True, # i don't recommend using this lol
            include_completed_tasks=True # this one, maybe so
        )) # task result
        taskman.refine(task, res) # refine process for taskmanager

if __name__ == '__main__':
    print('fork this and try it out!')
    #main() # f it we ball