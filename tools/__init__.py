from .readtool import ReadTool
from .searchtool import SearchTool
from .user_io import TalkToUser
from .file_io import WriteFileTool, ReadFileTool
from .shelltool import ShellTool
from .shodantool import ShodanTool

TOOLS = {
    'WebReader': ReadTool,
    'GoogleSearch': SearchTool,
    'AskUser': TalkToUser,
    'ReadFile': ReadFileTool,
    'WriteFile': WriteFileTool,
    'Shell': ShellTool,
    'Shodan': ShodanTool,
}