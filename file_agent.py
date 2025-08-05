#!/usr/bin/env python3
"""
File Agent - Natural language file system operations using local GPT-OSS models

Perform file operations, run shell commands, and manage your system using natural language.
Everything runs locally using GPT-OSS models via Ollama for complete privacy.
"""

import os
import sys
import json
import shutil
import subprocess
import glob
from pathlib import Path
from typing import List, Dict
import ollama

# File operation functions
def list_files(path="."):
    """List files in directory"""
    try:
        return os.listdir(path)
    except Exception as e:
        return f"Error: {e}"

def read_file(path):
    """Read file content"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def write_file(path, content):
    """Write content to file"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File '{path}' written successfully."
    except Exception as e:
        return f"Error: {e}"

def create_directory(path):
    """Create directory"""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Directory '{path}' created successfully."
    except Exception as e:
        return f"Error: {e}"

def delete_file(path):
    """Delete file or directory"""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Directory '{path}' deleted successfully."
        else:
            os.remove(path)
            return f"File '{path}' deleted successfully."
    except Exception as e:
        return f"Error: {e}"

def move_file(source, destination):
    """Move or rename file/directory"""
    try:
        shutil.move(source, destination)
        return f"Moved '{source}' to '{destination}' successfully."
    except Exception as e:
        return f"Error: {e}"

def search_file_content(file_path, search_string):
    """Search for text within a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            matching_lines = [line.strip() for line in f if search_string in line]
        if not matching_lines:
            return "No matching lines found."
        return "\n".join(matching_lines)
    except Exception as e:
        return f"Error: {e}"

def run_shell_command(command):
    """Run shell command"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"Output: {result.stdout}\nErrors: {result.stderr}\nExit code: {result.returncode}"
    except Exception as e:
        return f"Error: {e}"

def change_directory(path):
    """Change current working directory"""
    try:
        os.chdir(path)
        return f"Changed directory to {os.getcwd()}"
    except Exception as e:
        return f"Error: {e}"

def git_status():
    """Git status"""
    return run_shell_command("git status")

def git_add(path="."):
    """Stage files for commit"""
    return run_shell_command(f"git add {path}")

def git_commit(message):
    """Commit changes"""
    return run_shell_command(f"git commit -m \"{message}\"")

def glob_files(pattern):
    """Find files by pattern"""
    try:
        matches = glob.glob(pattern, recursive=True)
        return matches if matches else f"No files found matching: {pattern}"
    except Exception as e:
        return f"Error: {e}"

def read_json_file(file_path):
    """Read JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return f"Error: {e}"

def write_json_file(file_path, data):
    """Write JSON file"""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return f"JSON data written to {file_path}"
    except Exception as e:
        return f"Error: {e}"

# Tool registry
TOOLS = {
    'list_files': list_files,
    'read_file': read_file,
    'write_file': write_file,
    'create_directory': create_directory,
    'delete_file': delete_file,
    'move_file': move_file,
    'search_file_content': search_file_content,
    'run_shell_command': run_shell_command,
    'change_directory': change_directory,
    'git_status': git_status,
    'git_add': git_add,
    'git_commit': git_commit,
    'glob_files': glob_files,
    'read_json_file': read_json_file,
    'write_json_file': write_json_file,
}

class FileAgent:
    """AI agent for natural language file system operations using GPT-OSS."""
    
    def __init__(self, model: str = "gpt-oss:20b"):
        self.model = model
        self.conversation_history = []
        
        # Test Ollama connection
        try:
            ollama.list()
            print(f"✅ Connected to Ollama")
        except Exception as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            print("Make sure Ollama is running: ollama serve")
            sys.exit(1)
        
        print(f"🤖 Using model: {model}")
    
    def _get_system_prompt(self) -> str:
        """Get system instruction for file operations."""
        return """You are an AI file system agent that helps users perform operations using natural language.

Available tools:
- list_files(path) - List files in directory
- read_file(path) - Read file content  
- write_file(path, content) - Write content to file
- create_directory(path) - Create directory
- delete_file(path) - Delete file/directory
- move_file(source, dest) - Move/rename file
- search_file_content(path, text) - Search for text in file
- run_shell_command(cmd) - Execute shell command
- change_directory(path) - Change working directory
- git_status() - Git repository status
- git_add(path) - Stage files for commit
- git_commit(message) - Commit changes
- glob_files(pattern) - Find files by pattern
- read_json_file(path) - Read JSON file
- write_json_file(path, data) - Write JSON file

When a user asks you to perform file operations:
1. Understand what they want to accomplish
2. Call the appropriate tools by writing: function_name(arguments)
3. Provide clear feedback about what was done

Example: If user says "list files", respond with: list_files(.)

Be helpful, efficient, and safe. Always confirm destructive operations."""
    
    def _parse_tool_calls(self, response_text: str) -> List[Dict]:
        """Parse tool calls from AI response"""
        tool_calls = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
                
            # Look for function call pattern
            for tool_name in TOOLS:
                if line.startswith(tool_name + '(') and line.endswith(')'):
                    try:
                        # Extract arguments
                        args_str = line[len(tool_name)+1:-1]
                        
                        # Parse arguments
                        if not args_str.strip():
                            args = []
                        else:
                            # Special handling for write_file with content
                            if tool_name == 'write_file' and ',' in args_str:
                                # Split only on first comma for write_file
                                parts = args_str.split(',', 1)
                                path = parts[0].strip(' "\'')
                                content = parts[1].strip(' "\'')
                                args = [path, content]
                            else:
                                # Split by comma and clean up
                                args = [arg.strip(' "\'') for arg in args_str.split(',')]
                        
                        tool_calls.append({
                            'name': tool_name,
                            'args': args
                        })
                        
                    except Exception as e:
                        print(f"❌ Error parsing {tool_name}: {e}")
                    break
        
        return tool_calls
    
    def _execute_tool(self, tool_name: str, args: List[str]) -> str:
        """Execute a tool with given arguments"""
        if tool_name not in TOOLS:
            return f"Error: Unknown tool '{tool_name}'"
        
        try:
            tool_func = TOOLS[tool_name]
            result = tool_func(*args)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
    
    def execute_command(self, user_input: str):
        """Execute user command with AI assistance"""
        
        # Quick commands for common operations
        simple_commands = {
            'list': ('list_files', ['.']),
            'ls': ('list_files', ['.']),
            'pwd': ('run_shell_command', ['pwd']),
            'git status': ('git_status', []),
        }
        
        user_lower = user_input.lower().strip()
        
        if user_lower in simple_commands:
            tool_name, args = simple_commands[user_lower]
            print(f"🔧 Executing: {tool_name}({', '.join(args)})")
            result = self._execute_tool(tool_name, args)
            print(f"✅ Result: {result}")
            return
        
        # Use AI for more complex requests
        prompt = f"""I need help with a file system task. Here's what the user wants:

"{user_input}"

Available tools and their syntax:
- list_files(path) - lists files in directory
- read_file(path) - reads file content
- write_file(path, content) - writes content to file
- create_directory(path) - creates directory
- delete_file(path) - deletes file/directory
- move_file(source, dest) - moves/renames file
- search_file_content(path, text) - searches for text in file
- run_shell_command(command) - runs shell command
- change_directory(path) - changes directory
- git_status() - shows git status
- git_add(path) - stages files
- git_commit(message) - commits changes
- glob_files(pattern) - finds files by pattern
- read_json_file(path) - reads JSON file
- write_json_file(path, data) - writes JSON file

Respond with the exact tool call(s) needed, one per line, like:
list_files(.)
or
write_file(example.txt, Hello World)

If you need multiple steps, list them all."""

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            response_text = response['message']['content']
            print(f"🤖 AI suggests: {response_text}")
            
            # Parse and execute tool calls
            tool_calls = self._parse_tool_calls(response_text)
            
            if tool_calls:
                print(f"🔧 Executing {len(tool_calls)} operation(s)...")
                for tool_call in tool_calls:
                    tool_name = tool_call['name']
                    args = tool_call['args']
                    
                    print(f"   🛠️  {tool_name}({', '.join(args)})")
                    result = self._execute_tool(tool_name, args)
                    print(f"   ✅ {result}")
            else:
                print("💡 No specific operations detected")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def run_interactive(self):
        """Interactive mode"""
        print("🤖 GPT-OSS File Agent")
        print("Natural language file operations using local AI!")
        print("Type 'exit' to quit, 'help' for examples")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💻 What would you like to do? > ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    print("\n💡 Example commands:")
                    print("  • 'list files' or 'ls' - List current directory")
                    print("  • 'create a file called test.txt with hello world'")
                    print("  • 'find all python files'")
                    print("  • 'show me the git status'")
                    print("  • 'create a directory called new_project'")
                    print("  • 'move file.txt to backup/'")
                    continue
                
                if not user_input:
                    continue
                
                self.execute_command(user_input)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPT-OSS File Agent")
    parser.add_argument("command", nargs="*", help="Command to execute")
    parser.add_argument("-m", "--model", default="gpt-oss:20b", help="GPT-OSS model to use")
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = FileAgent(model=args.model)
    
    if args.command:
        # Single command mode
        command = ' '.join(args.command)
        agent.execute_command(command)
    else:
        # Interactive mode
        agent.run_interactive()

if __name__ == "__main__":
    main()
