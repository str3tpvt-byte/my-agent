import datetime
import os
import subprocess

from ai_client import ask_ai


def tool_files():
    files = os.listdir(".")
    if not files:
        return "The project directory is empty."

    return "\n".join(f"- {file}" for file in files)


def tool_git():
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return "This is not a Git repository."

    return result.stdout.strip() or "Git working tree is clean."


def tool_system():
    result = subprocess.run(
        ["uname", "-a"],
        capture_output=True,
        text=True
    )

    return result.stdout.strip()


def tool_time():
    return datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


TOOLS = {
    "files": tool_files,
    "git": tool_git,
    "system": tool_system,
    "time": tool_time,
}


def choose_tool_with_ai(request):
    prompt = f"""
You are the tool selector for a Termux AI agent.

Available tools:
- files: list files in the current project
- git: show Git repository status
- system: show system/kernel information
- time: show the current date and time

User request:
{request}

Return ONLY one of these exact words:
files
git
system
time
none
"""

    result = ask_ai(prompt).strip().lower()

    for tool in TOOLS:
        if result == tool:
            return tool

    return None


def main():
    print("================================")
    print("        MY AI AGENT v4")
    print("================================")
    print("Gemini-powered tool selection.")
    print("Type 'exit' to quit.")
    print()

    while True:
        try:
            request = input("You > ").strip()

            if not request:
                continue

            if request.lower() == "exit":
                print("Agent > Goodbye!")
                break

            tool = choose_tool_with_ai(request)

            if tool is None:
                print(
                    "Agent > I don't know which available tool "
                    "can handle that request."
                )
                print()
                continue

            print(f"Agent > Gemini selected: {tool}")
            result = TOOLS[tool]()

            print("Agent >")
            print(result)
            print()

        except KeyboardInterrupt:
            print("\nAgent > Goodbye!")
            break


if __name__ == "__main__":
    main()
