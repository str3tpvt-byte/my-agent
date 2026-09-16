import os
import datetime
import subprocess


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


def choose_tool(request):
    text = request.lower()

    if any(word in text for word in [
        "file", "files", "folder", "directory"
    ]):
        return "files"

    if any(word in text for word in [
        "git", "commit", "repository", "repo", "changes"
    ]):
        return "git"

    if any(word in text for word in [
        "system", "device", "kernel", "architecture"
    ]):
        return "system"

    if any(word in text for word in [
        "time", "date"
    ]):
        return "time"

    return None


def run_tool(tool):
    if tool == "files":
        return tool_files()

    if tool == "git":
        return tool_git()

    if tool == "system":
        return tool_system()

    if tool == "time":
        return tool_time()

    return "No suitable tool found."


def main():
    print("================================")
    print("        MY AI AGENT v3")
    print("================================")
    print("Use natural language.")
    print("Type 'exit' to quit.")
    print()

    while True:
        try:
            request = input("You > ").strip()

            if request.lower() == "exit":
                print("Agent > Goodbye!")
                break

            tool = choose_tool(request)

            if tool is None:
                print(
                    "Agent > I don't know which tool to use yet."
                )
                continue

            print(f"Agent > Using {tool} tool...")
            result = run_tool(tool)

            print("Agent >")
            print(result)
            print()

        except KeyboardInterrupt:
            print("\nAgent > Goodbye!")
            break


if __name__ == "__main__":
    main()
