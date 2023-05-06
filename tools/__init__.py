from .readtool import ReadTool
from .searchtool import GoogleSearchTool, DDGSearchTool
from .user_io import TalkToUser
from .file_io import WriteFileTool, ReadFileTool, ListDirTool
from .shelltool import ShellTool
from .shodantool import ShodanTool

TOOLS = {
    'WebReader': ReadTool,
    'GoogleSearch': GoogleSearchTool,
    'DDGSearch': DDGSearchTool,
    'AskUser': TalkToUser,
    'ReadFile': ReadFileTool,
    'WriteFile': WriteFileTool,
    'ListDir': ListDirTool,
    'Files': [ReadFileTool, WriteFileTool, ListDirTool],
    'Shell': ShellTool,
    'Shodan': ShodanTool,
}