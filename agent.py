import os
import datetime
import subprocess


def list_files():
    files = os.listdir(".")
    if not files:
        return "Directory is empty."

    return "\n".join(f"- {file}" for file in files)


def system_info():
    result = subprocess.run(
        ["uname", "-a"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def git_status():
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return "This directory is not a Git repository."

    return result.stdout.strip() or "Git working tree is clean."


def show_help():
    print("""
Commands:

  hello       Test the agent
  time        Show current time
  pwd         Show current directory
  files       List files
  system      Show system information
  git         Show Git status
  help        Show commands
  exit        Quit
""")


def agent(command):
    command = command.strip().lower()

    if command == "hello":
        return "Hello! Agent is working."

    if command == "time":
        return datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    if command == "pwd":
        return os.getcwd()

    if command == "files":
        return list_files()

    if command == "system":
        return system_info()

    if command == "git":
        return git_status()

    if command == "help":
        return show_help()

    if command == "exit":
        return None

    return "I don't know that command yet. Type 'help'."


print("================================")
print("        MY AI AGENT v2")
print("================================")
print("Type 'help' for commands.")
print()

while True:
    try:
        user_input = input("You > ")
        result = agent(user_input)

        if result is None:
            print("Agent > Goodbye!")
            break

        print("Agent >", result)

    except KeyboardInterrupt:
        print("\nAgent > Goodbye!")
        break
