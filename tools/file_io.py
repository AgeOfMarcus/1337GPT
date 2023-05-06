from langchain.tools import BaseTool
import json
import os

class WriteFileTool(BaseTool):
    name = 'WriteFileTool'
    description = (
        'Useful for writing text to files.'
        'Use this when asked to save data to a file, or write a file.'
        'Accepts a single argument in JSON format containing the keys "filename" and "content". The optional key "overwrite" can be set to True if you want to replace existing files, otherwise it is disabled by default.'
        'Returns the filename if written successfully, or an error string.'
    )

    def _run(self, *args, **kwargs):
        if args:
            if type(args[0]) == dict:
                args = args[0]
            else:
                try:
                    args = json.loads(args[0])
                except json.JSONDecodeError:
                    return 'Error: invalid JSON argument. Make sure you are passing a single, string, argument containing VALID JSON with the keys "filename" containing a string, "content" containing a string, and the optional "overwrite" containing a boolean.'
        else:
            args = kwargs

        if not (filename := args.get('filename')):
            return 'Error: no "filename" specified.'
        if not (content := args.get('content')):
            return 'Error: no "content" provided.'

        if os.path.exists(filename) and not args.get('overwrite'):
            return 'Error: "overwrite" was not set to True, but the specified "filename" already exists.'

        with open(filename, 'w') as f:
            f.write(content)
        return filename

    async def _arun(self, args):
        return self._run(args)

class ReadFileTool(BaseTool):
    name = 'ReadFileTool'
    description = (
        'Useful for reading file contents.'
        'Use this to read code when debugging errors.'
        'Accepts a filename as argument.'
        'Returns the file contents as a string, or an error message beginning with "Error:".'
    )

    def _run(self, filename: str) -> str:
        try:
            file = open(filename, 'r')
        except:
            return f'Error: cannot open file: {filename}'
        return file.read()
    async def _arun(self, filename):
        return self._run(filename)

class ListDirTool(BaseTool):
    name = 'ListDirTool'
    description = (
        'Useful for listing directory contents.'
        'Accepts a directory path string as argument (allows "." and such).'
        'Returns a list of filenames, or an error message.'
    )

    def _run(self, path: str) -> list:
        try:
            return os.listdir(path)
        except:
            return f'Error: cannot list directory: {path}'
    
    async def _arun(self, path):
        return self._run(path)