import datetime
import json
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


def make_plan(request):
    prompt = f"""
You are the planning component of a Termux AI agent.

Available tools:
- files: list files in the current project
- git: show Git repository status
- system: show system/kernel information
- time: show current date and time

User request:
{request}

Return ONLY valid JSON in this exact format:

{{"tools":["files","git"]}}

Rules:
- Use only the available tool names.
- Use the smallest number of tools necessary.
- If no tool is needed, return {{"tools":[]}}.
- Do not include markdown.
- Do not explain anything outside the JSON.
"""

    result = ask_ai(prompt).strip()

    try:
        plan = json.loads(result)
    except json.JSONDecodeError:
        return []

    selected = plan.get("tools", [])

    if not isinstance(selected, list):
        return []

    return [
        tool for tool in selected
        if tool in TOOLS
    ]


def create_final_answer(request, results):
    prompt = f"""
You are the final-answer component of a Termux AI agent.

User request:
{request}

Tool results:
{json.dumps(results, indent=2)}

Answer the user's request using the tool results.
Be concise and factual.
Do not claim that you performed actions that the tools did not perform.
"""

    return ask_ai(prompt).strip()


def main():
    print("================================")
    print("        MY AI AGENT v5")
    print("================================")
    print("Gemini-powered multi-tool agent.")
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

            tools = make_plan(request)

            if not tools:
                print("Agent > No available tool is needed.")
                print()
                continue

            print(
                "Agent > Gemini plan: "
                + ", ".join(tools)
            )

            results = {}

            for tool in tools:
                print(f"Agent > Running {tool}...")
                results[tool] = TOOLS[tool]()

            answer = create_final_answer(
                request,
                results
            )

            print("Agent >")
            print(answer)
            print()

        except KeyboardInterrupt:
            print("\nAgent > Goodbye!")
            break


if __name__ == "__main__":
    main()
