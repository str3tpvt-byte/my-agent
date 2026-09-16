from pathlib import Path
import re
import datetime
import json
import os
import shutil
import subprocess

from ai_client import ask_ai


MEMORY_FILE = "memory.json"
FACTS_FILE = "facts.json"

ANALYZABLE_FILES = [
    "agent.py",
    "ai_client.py",
    "config.py",
    "project.txt",
    "facts.json",
]


# =========================
# JSON STORAGE
# =========================

def load_json_file(filename, default):
    if not os.path.exists(filename):
        return default

    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def save_json_file(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_memory():
    return load_json_file(MEMORY_FILE, [])


def save_memory(memory):
    save_json_file(MEMORY_FILE, memory)


def load_facts():
    return load_json_file(FACTS_FILE, {})


def save_facts(facts):
    save_json_file(FACTS_FILE, facts)


# =========================
# HELP
# =========================

def show_help():
    print()
    print("Agent > MY AI AGENT v10 HELP")
    print("--------------------------------")
    print("Basic commands:")
    print("  help")
    print("  exit")
    print("  clear memory")
    print("  clear facts")
    print()
    print("Project:")
    print("  project info")
    print("  project tree")
    print("  project cleanup")
    print("  clean project")
    print("  backup project")
    print("  analyze project")
    print("  show current directory")
    print()
    print("Directory:")
    print("  create directory NAME")
    print("  list directory")
    print("  list directory NAME")
    print("  delete directory NAME")
    print()
    print("File:")
    print("  read file NAME")
    print("  create file NAME")
    print("  write file NAME")
    print("  write multiline file NAME")
    print("  append file NAME")
    print("  edit file")
    print("  edit multiline file NAME")
    print("  delete file NAME")
    print()
    print("Safe commands:")
    print("  run command pwd")
    print("  run command ls")
    print("  run command whoami")
    print("  run command uname")
    print("  run command git status")
    print()
    print("Gemini:")
    print("  Natural-language requests are sent to Gemini.")
    print("  Gemini can select read-only information tools.")
    print("  Project Analyzer can inspect important project files.")
    print()
    print("Destructive operations require approval.")
    print("--------------------------------")
    print()


# =========================
# SAFETY
# =========================

def safe_filename(filename):
    filename = filename.strip()

    if not filename:
        return None

    if os.path.basename(filename) != filename:
        return None

    return filename


def safe_directory(dirname):
    dirname = dirname.strip()

    if not dirname:
        return None

    if dirname in (".", "./"):
        return "."

    if os.path.isabs(dirname):
        return None

    if "/" in dirname or "\\" in dirname:
        return None

    if dirname in (".", ".."):
        return None

    return dirname


# =========================
# FILE TOOLS
# =========================

def tool_files():
    try:
        entries = sorted(os.listdir("."))

        if not entries:
            return "The project directory is empty."

        return "\n".join(f"- {entry}" for entry in entries)

    except OSError as error:
        return f"Could not list files: {error}"


def tool_read_file(filename):
    filename = safe_filename(filename)

    if not filename:
        return "Invalid filename."

    if not os.path.isfile(filename):
        return f"File not found: {filename}"

    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()

        if not content:
            return f"{filename} is empty."

        return content

    except (OSError, UnicodeDecodeError) as error:
        return f"Could not read {filename}: {error}"


def tool_write_file(filename, content):
    filename = safe_filename(filename)

    if not filename:
        return "Invalid filename."

    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)

        return f"File written successfully: {filename}"

    except OSError as error:
        return f"Could not write {filename}: {error}"


def tool_edit_file(filename, old_text, new_text):
    filename = safe_filename(filename)

    if not filename:
        return "Invalid filename."

    if not os.path.isfile(filename):
        return f"File not found: {filename}"

    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()

        if old_text not in content:
            return "The text to replace was not found."

        updated = content.replace(old_text, new_text, 1)

        with open(filename, "w", encoding="utf-8") as file:
            file.write(updated)

        return f"File edited successfully: {filename}"

    except (OSError, UnicodeDecodeError) as error:
        return f"Could not edit {filename}: {error}"


def tool_append_file(filename, content):
    filename = safe_filename(filename)

    if not filename:
        return "Invalid filename."

    try:
        with open(filename, "a", encoding="utf-8") as file:
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                file.write("\n")

            file.write(content)

        return f"File appended successfully: {filename}"

    except OSError as error:
        return f"Could not append to {filename}: {error}"


# =========================
# DIRECTORY TOOLS
# =========================

def tool_create_directory(dirname):
    dirname = safe_directory(dirname)

    if not dirname:
        return "Invalid directory name."

    try:
        os.mkdir(dirname)
        return f"Directory created successfully: {dirname}"

    except FileExistsError:
        return f"Directory already exists: {dirname}"

    except OSError as error:
        return f"Could not create directory: {error}"


def tool_list_directory(dirname="."):
    dirname = safe_directory(dirname)

    if not dirname:
        return "Invalid directory name."

    if not os.path.isdir(dirname):
        return f"Directory not found: {dirname}"

    try:
        entries = sorted(os.listdir(dirname))

        if not entries:
            return f"{dirname} is empty."

        return "\n".join(entries)

    except OSError as error:
        return f"Could not list directory: {error}"


def tool_project_tree():
    lines = ["."]

    try:
        for entry in sorted(os.listdir(".")):
            if entry == ".git":
                lines.append("├── .git/")
            elif os.path.isdir(entry):
                lines.append(f"├── {entry}/")
            else:
                lines.append(f"├── {entry}")

        return "\n".join(lines)

    except OSError as error:
        return f"Could not create project tree: {error}"


def tool_delete_directory(dirname):
    dirname = safe_directory(dirname)

    if not dirname:
        return "Invalid directory name."

    if not os.path.isdir(dirname):
        return f"Directory not found: {dirname}"

    try:
        if os.listdir(dirname):
            return (
                f"Directory is not empty: {dirname}. "
                "Delete its contents first."
            )

        os.rmdir(dirname)
        return f"Directory deleted successfully: {dirname}"

    except OSError as error:
        return f"Could not delete directory: {error}"


def tool_delete_file(filename):
    filename = safe_filename(filename)

    if not filename:
        return "Invalid filename."

    if not os.path.isfile(filename):
        return f"File not found: {filename}"

    try:
        os.remove(filename)
        return f"File deleted successfully: {filename}"

    except OSError as error:
        return f"Could not delete {filename}: {error}"


# =========================
# GIT / SYSTEM / TIME
# =========================

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

    if result.returncode != 0:
        return "Could not read system information."

    return result.stdout.strip()


def tool_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================
# SAFE COMMANDS
# =========================

SAFE_COMMANDS = {
    "pwd": ["pwd"],
    "ls": ["ls"],
    "whoami": ["whoami"],
    "uname": ["uname", "-a"],
    "git status": ["git", "status"],
}


def tool_command(command):
    command = command.strip()

    if command not in SAFE_COMMANDS:
        allowed = ", ".join(SAFE_COMMANDS.keys())
        return f"Command not allowed.\nAllowed commands: {allowed}"

    try:
        result = subprocess.run(
            SAFE_COMMANDS[command],
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode != 0:
            return (
                f"Command failed with exit code "
                f"{result.returncode}.\n{error}"
            )

        return output or "Command completed successfully."

    except subprocess.TimeoutExpired:
        return "Command timed out."

    except OSError as error:
        return f"Could not execute command: {error}"


# =========================
# APPROVAL
# =========================

def ask_approval(action):
    print()
    print("Agent > I want to:")
    print(f"Agent > {action}")
    print()
    print("Agent > Allow this operation? [y/N]")

    answer = input("Approval > ").strip().lower()

    return answer in ("y", "yes")


# =========================
# APPROVED OPERATIONS
# =========================

def execute_with_approval(command):
    if command not in SAFE_COMMANDS:
        print("Agent > Command not allowed.")
        print(
            "Agent > Allowed commands: "
            + ", ".join(SAFE_COMMANDS.keys())
        )
        return None

    if not ask_approval(f"run command: {command}"):
        print("Agent > Command cancelled.")
        return None

    print(f"Agent > Executing: {command}")

    result = tool_command(command)

    print("Agent > Command result:")
    print(result)

    return result


def execute_file_write_with_approval(filename, content):
    if not safe_filename(filename):
        print("Agent > Invalid filename.")
        return None

    if not ask_approval(f"write file: {filename}"):
        print("Agent > File write cancelled.")
        return None

    result = tool_write_file(filename, content)

    print("Agent > File operation result:")
    print(result)

    return result


def execute_file_edit_with_approval(filename, old_text, new_text):
    print()
    print("Agent > Proposed file change:")
    print(f"Agent > File: {filename}")
    print(f"Agent > Replace: {old_text!r}")
    print(f"Agent > With:    {new_text!r}")

    if not ask_approval(f"edit file: {filename}"):
        print("Agent > File edit cancelled.")
        return None

    result = tool_edit_file(filename, old_text, new_text)

    print("Agent > File operation result:")
    print(result)

    return result


def execute_file_append_with_approval(filename, content):
    if not safe_filename(filename):
        print("Agent > Invalid filename.")
        return None

    if not os.path.isfile(filename):
        print(f"Agent > File not found: {filename}")
        return None

    if not ask_approval(f"append to file: {filename}"):
        print("Agent > File append cancelled.")
        return None

    result = tool_append_file(filename, content)

    print("Agent > File operation result:")
    print(result)

    return result


def execute_file_delete_with_approval(filename):
    if not safe_filename(filename):
        print("Agent > Invalid filename.")
        return None

    if not os.path.isfile(filename):
        print(f"Agent > File not found: {filename}")
        return None

    if not ask_approval(f"delete file: {filename}"):
        print("Agent > File deletion cancelled.")
        return None

    result = tool_delete_file(filename)

    print("Agent > File operation result:")
    print(result)

    return result


def execute_directory_create_with_approval(dirname):
    if not safe_directory(dirname):
        print("Agent > Invalid directory name.")
        return None

    if os.path.exists(dirname):
        print(f"Agent > Directory already exists: {dirname}")
        return None

    if not ask_approval(f"create directory: {dirname}"):
        print("Agent > Directory creation cancelled.")
        return None

    result = tool_create_directory(dirname)

    print("Agent > Directory operation result:")
    print(result)

    return result


def execute_directory_delete_with_approval(dirname):
    if not safe_directory(dirname):
        print("Agent > Invalid directory name.")
        return None

    if not os.path.isdir(dirname):
        print(f"Agent > Directory not found: {dirname}")
        return None

    if os.listdir(dirname):
        print(f"Agent > Directory is not empty: {dirname}")
        print("Agent > Delete the contents first.")
        return None

    if not ask_approval(f"delete directory: {dirname}"):
        print("Agent > Directory deletion cancelled.")
        return None

    result = tool_delete_directory(dirname)

    print("Agent > Directory operation result:")
    print(result)

    return result


# =========================
# PROJECT CLEANUP
# =========================

def get_cleanup_candidates():
    cleanup_items = []

    for entry in sorted(os.listdir(".")):
        if entry == "__pycache__":
            cleanup_items.append(entry)

        elif entry.endswith(".pyc"):
            cleanup_items.append(entry)

        elif entry.startswith("test"):
            cleanup_items.append(entry)

        elif entry.startswith("append-test"):
            cleanup_items.append(entry)

    return cleanup_items


def backup_project():
    backup_name = "my-agent-backup"
    counter = 1

    while os.path.exists(backup_name):
        backup_name = f"my-agent-backup-{counter}"
        counter += 1

    try:
        shutil.copytree(
            ".",
            backup_name,
            ignore=shutil.ignore_patterns(
                ".git",
                "__pycache__",
                "*.pyc",
                "test*",
                "append-test*",
                "my-agent-backup*"
            )
        )

        return backup_name

    except OSError as error:
        if os.path.exists(backup_name):
            shutil.rmtree(backup_name, ignore_errors=True)

        return f"ERROR: Could not create backup: {error}"


# =========================
# PROJECT ANALYZER
# =========================

def redact_secrets(text):
    patterns = [
        (r'(?i)(GEMINI_API_KEY\s*[=:]\s*)([^\s,"\'}]+)', r'\1[REDACTED]'),
        (r'(?i)(AI_API_KEY\s*[=:]\s*)([^\s,"\'}]+)', r'\1[REDACTED]'),
        (r'AIza[0-9A-Za-z_-]{20,}', '[REDACTED_GEMINI_KEY]'),
        (r'(?i)(Bearer\s+)([A-Za-z0-9._-]{20,})', r'\1[REDACTED]'),
    ]

    result = text

    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)

    return result


def collect_project_source():
    collected = {}

    allowed_extensions = {
        ".py", ".txt", ".json", ".md", ".toml", ".yaml", ".yml"
    }

    skip_directories = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
    }

    skip_prefixes = (
        "agent_v",
        "my-agent-backup",
    )

    for path in sorted(Path(".").rglob("*")):
        if not path.is_file():
            continue

        if any(part in skip_directories for part in path.parts):
            continue

        if path.name.startswith(skip_prefixes):
            continue

        if path.suffix.lower() not in allowed_extensions:
            continue

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()

            content = redact_secrets(content)

            if len(content) > 30000:
                content = content[:30000] + "\n[TRUNCATED]"

            collected[str(path)] = content

        except OSError as error:
            collected[str(path)] = f"[Could not read file: {error}]"

    return collected


def local_git_dispatch(command):
    git_commands = {
        "git status": git_status_info,
        "git remote": git_remote_info,
        "git log": git_log_info,
        "git diff": git_diff_info,
        "git info": git_info,
    }

    command = command.strip().lower()

    if command in git_commands:
        git_commands[command]()
        return True

    return False


def git_status_info():
    print("\n=== GIT STATUS INSPECTOR ===")
    import subprocess

    try:
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            output = result.stdout.strip()

            if output:
                print(output)
            else:
                print("Working tree is clean.")
        else:
            error = result.stderr.strip()
            print(f"Git status failed: {error}")

    except Exception as e:
        print(f"Git status error: {e}")

    print("============================")
    print()


def git_remote_info():
    print("\n=== GIT REMOTE INSPECTOR ===")
    import subprocess

    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout.strip())
        elif result.returncode == 0:
            print("No Git remotes configured.")
        else:
            print("Git remote unavailable.")
    except Exception as error:
        print(f"Git remote failed: {type(error).__name__}")

    print("============================\n")


def git_log_info():
    print("\n=== GIT LOG INSPECTOR ===")
    import subprocess

    try:
        result = subprocess.run(
            ["git", "log", "-10", "--oneline", "--decorate"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout.strip())
        elif result.returncode == 0:
            print("No commits found.")
        else:
            print("Git log unavailable.")
    except Exception as error:
        print(f"Git log failed: {type(error).__name__}")

    print("=========================\n")


def git_diff_info():
    print("\n=== GIT DIFF INSPECTOR ===")
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout.strip())
        elif result.returncode == 0:
            print("No tracked file changes.")
        else:
            print("Git diff unavailable.")
    except Exception as error:
        print(f"Git diff failed: {type(error).__name__}")

    print("==========================\n")


def git_info():
    print("\n=== GIT INSPECTOR ===")
    import subprocess

    def git_cmd(*args):
        try:
            result = subprocess.run(
                ["git", *args],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    branch = git_cmd("branch", "--show-current")
    status = git_cmd("status", "--short")
    commit = git_cmd("log", "-1", "--oneline")

    print(f"Branch              {branch or "unknown"}")

    if status:
        lines = status.splitlines()
        print(f"Changed entries     {len(lines)}")
        for line in lines[:10]:
            print(f"  {line}")
        if len(lines) > 10:
            print(f"  ... and {len(lines) - 10} more")
    else:
        print("Working tree        ✓ clean")

    print(f"Latest commit       {commit or "none"}")
    print("====================\n")


def storage_advisor():
    print("\n=== STORAGE CLEANUP ADVISOR ===")
    files = []
    try:
        for path in Path(".").rglob("*"):
            if not path.is_file():
                continue
            if any(part in {".git", "__pycache__", "node_modules"} for part in path.parts):
                continue
            try:
                files.append((path.stat().st_size, path))
            except OSError:
                pass

        files.sort(reverse=True, key=lambda item: item[0])

        if not files:
            print("No files found.")
        else:
            print("Largest project files:")
            for size, path in files[:10]:
                print(f"{size / (1024**2):8.2f} MB  {path}")

        print("------------------------------")
        print("Advisor: review large files before deleting anything.")
        print("No files were deleted.")
    except Exception as error:
        print(f"Storage scan failed: {type(error).__name__}")

    print("===============================\n")


def resource_info():
    print("\n=== SYSTEM RESOURCE INSPECTOR ===")
    try:
        import os
        print(f"CPU cores           {os.cpu_count() or "unknown"}")
    except Exception:
        print("CPU cores           ⚠ unavailable")

    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        print(f"Storage total       {total / (1024**3):.2f} GB")
        print(f"Storage used        {used / (1024**3):.2f} GB")
        print(f"Storage free        {free / (1024**3):.2f} GB")
    except Exception:
        print("Storage             ⚠ unavailable")

    try:
        import os
        with open("/proc/meminfo", "r") as file:
            meminfo = file.read()
        values = {}
        for line in meminfo.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                values[parts[0].rstrip(":")] = int(parts[1])
        total_kb = values.get("MemTotal")
        available_kb = values.get("MemAvailable")
        if total_kb:
            print(f"RAM total           {total_kb / (1024**2):.2f} GB")
        if available_kb:
            print(f"RAM available       {available_kb / (1024**2):.2f} GB")
    except Exception:
        print("RAM                 ⚠ unavailable")

    try:
        project_size = sum(
            f.stat().st_size
            for f in Path(".").rglob("*")
            if f.is_file()
            and not any(x in f.parts for x in [".git", "__pycache__", "node_modules"])
        )
        print(f"Project size        {project_size / (1024**2):.2f} MB")
    except Exception:
        print("Project size        ⚠ unavailable")

    print("===============================\n")


def network_info():
    print("\n=== NETWORK INSPECTOR ===")
    try:
        import socket
        host = socket.gethostname()
        print(f"Hostname             {host}")
        try:
            ip = socket.gethostbyname(host)
            print(f"Local address        {ip}")
        except Exception:
            print("Local address        ⚠ unavailable")
    except Exception:
        print("Hostname             ⚠ unavailable")
    try:
        import requests
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            print("Internet connection  ✓ available")
        else:
            print(f"Internet connection  ⚠ HTTP {response.status_code}")
    except Exception as error:
        print(f"Internet connection  ✗ unavailable")
        print(f"Reason               {type(error).__name__}")
    print("========================\n")


def environment_info():
    print("\n=== ENVIRONMENT INSPECTOR ===")
    print(f"Python              {__import__("sys").version.split()[0]}")
    print(f"Platform             {__import__("platform").system()} {__import__("platform").release()}")
    print(f"Architecture         {__import__("platform").machine()}")
    print(f"Project directory   {Path.cwd()}")
    print(f"Gemini API key       {"✓ loaded" if __import__("os").getenv("GEMINI_API_KEY") else "✗ missing"}")
    print(f"Git                  {"✓ available" if __import__("shutil").which("git") else "✗ not found"}")
    print(f"Node.js              {"✓ available" if __import__("shutil").which("node") else "⚠ not found"}")
    print("==============================\n")


def environment_info():
    print("\n=== ENVIRONMENT INSPECTOR ===")
    print(f"Python              {__import__("sys").version.split()[0]}")
    print(f"Platform             {__import__("platform").system()} {__import__("platform").release()}")
    print(f"Architecture         {__import__("platform").machine()}")
    print(f"Project directory   {Path.cwd()}")
    print(f"Gemini API key       {"✓ loaded" if __import__("os").getenv("GEMINI_API_KEY") else "✗ missing"}")
    print(f"Git                  {"✓ available" if __import__("shutil").which("git") else "✗ not found"}")
    print(f"Node.js              {"✓ available" if __import__("shutil").which("node") else "⚠ not found"}")
    print("==============================\n")


def check_dependencies():
    modules = [("requests", "requests"), ("pathlib", "pathlib"), ("json", "json"), ("os", "os"), ("shutil", "shutil"), ("subprocess", "subprocess")]
    print("\n=== DEPENDENCY CHECK ===")
    missing = []
    for name, module in modules:
        try:
            __import__(module)
            print(f"{name:<18} ✓ available")
        except ImportError:
            print(f"{name:<18} ✗ missing")
            missing.append(name)
    print("------------------------")
    if missing:
        print("Missing dependencies:", ", ".join(missing))
        print("Status              ⚠ NEEDS ATTENTION")
    else:
        print("Status              ✓ ALL AVAILABLE")
    print("========================\n")

def diagnose_project():
    print("\n=== AGENT DIAGNOSTICS ===")
    problems=[]
    try: compile(Path("agent.py").read_text(), "agent.py", "exec"); print("Python syntax       ✓ OK")
    except Exception as e: print(f"Python syntax       ✗ {e}"); problems.append("Python syntax problem")
    for f in ["agent.py","ai_client.py","config.py","memory.json","facts.json"]:
        if Path(f).is_file(): print(f"Required file       ✓ {f}")
        else: print(f"Required file       ✗ {f} missing"); problems.append(f"{f} missing")
    if os.getenv("GEMINI_API_KEY"): print("Gemini configuration ✓ API key loaded")
    else: print("Gemini configuration ✗ API key missing"); problems.append("GEMINI_API_KEY missing")
    try: json.load(open(MEMORY_FILE)); print("Memory database     ✓ Valid JSON")
    except Exception: print("Memory database     ✗ Invalid or unreadable"); problems.append("memory.json problem")
    try: json.load(open(FACTS_FILE)); print("Facts database      ✓ Valid JSON")
    except Exception: print("Facts database      ✗ Invalid or unreadable"); problems.append("facts.json problem")
    print("Git repository      ✓ Present" if Path(".git").is_dir() else "Git repository      ⚠ Not found")
    total=sum(x.stat().st_size for x in Path(".").rglob("*") if x.is_file() and not any(z in x.parts for z in [".git","__pycache__","node_modules"])); print(f"Project size        {total/1024:.1f} KB")
    print(f"Potential problems  {len(problems)}")
    print("Overall status      ✓ No obvious problems detected" if not problems else "Overall status      ⚠ Review problems above")
    print("===========================\n")

def analyze_project():
    source = collect_project_source()

    if not source:
        return "No analyzable project files were found."

    prompt = f"""
You are the Project Analyzer for a Termux AI agent.

Project name:
My AI Agent

Analyze the following project files:

{json.dumps(source, indent=2, ensure_ascii=False)}

Give a concise but useful technical overview.

Include:

1. What the project is.
2. How the main agent works.
3. How Gemini is connected.
4. What tools are available.
5. How memory and facts work.
6. How approval protects destructive operations.
7. Important files and their roles.
8. Any obvious limitations or risks.

Rules:

- Only use information present in the supplied files.
- Do not invent features.
- Clearly say when something cannot be determined.
- Do not modify any files.
"""

    result = ask_ai(prompt).strip()

    if result.startswith("ERROR:"):
        return result

    return result or "Project analysis returned no answer."


# =========================
# FACTS
# =========================

def extract_facts(request, facts):
    text = request.strip()
    lower = text.lower()

    prefixes = [
        "my project is called ",
        "my project is ",
        "project is called ",
        "project is "
    ]

    for prefix in prefixes:
        if lower.startswith(prefix):
            project_name = text[len(prefix):].strip()

            if project_name:
                facts["project_name"] = project_name.rstrip(".")

            break

    save_facts(facts)
    return facts


# =========================
# GEMINI PLANNER
# =========================

def make_plan(request, memory, facts):
    recent_memory = memory[-10:]

    prompt = f"""
You are the planning component of a Termux AI agent.

Available tools:

- files: list files in the current project
- read_file: read a file
- git: show Git repository status
- system: show system/kernel information
- time: show current date and time
- analyze_project: inspect important project files and explain the project

Long-term facts:

{json.dumps(facts, indent=2)}

Recent conversation:

{json.dumps(recent_memory, indent=2)}

User request:

{request}

Return ONLY valid JSON.

Example:

{{"tools":["files"]}}

Rules:

- Use only the available tool names.
- Use the smallest number of tools necessary.
- If no tool is needed, return: {{"tools":[]}}
- For questions asking what the project is, how it works, its structure,
  tools, Gemini connection, memory, facts, or limitations, use
  analyze_project.
- Do not include markdown.
- Do not explain anything outside the JSON.
"""

    result = ask_ai(prompt).strip()

    if result.startswith("ERROR:"):
        return []

    try:
        plan = json.loads(result)
    except json.JSONDecodeError:
        return []

    selected = plan.get("tools", [])

    if not isinstance(selected, list):
        return []

    allowed = {
        "files",
        "read_file",
        "git",
        "system",
        "time",
        "analyze_project"
    }

    return [tool for tool in selected if tool in allowed]


# =========================
# FINAL ANSWER
# =========================

def create_final_answer(request, results, memory, facts):
    recent_memory = memory[-10:]

    prompt = f"""
You are the final-answer component of a Termux AI agent.

Long-term facts:

{json.dumps(facts, indent=2)}

Recent conversation:

{json.dumps(recent_memory, indent=2)}

Current user request:

{request}

Tool results:

{json.dumps(results, indent=2)}

Answer the user's request.

Rules:

- Be concise and factual.
- Use long-term facts when relevant.
- Use recent conversation when relevant.
- Use tool results when available.
- Do not invent information.
- Do not claim an action was performed unless a tool actually performed it.
"""

    result = ask_ai(prompt).strip()

    if not result:
        return "I could not generate an answer."

    return result


# =========================
# MAIN
# =========================

def main():
    memory = load_memory()
    facts = load_facts()

    print("================================")
    print("        MY AI AGENT v10")
    print("================================")
    print("Gemini-powered Termux agent.")
    print("Memory + facts + tools + Project Analyzer.")
    print()
    print("Type 'help' for commands.")
    print()

    while True:
        try:
            request = input("You > ").strip()

            if not request:
                continue

            lower_request = request.lower()

            # BATCH MODE
            if lower_request == "batch":
                print("Agent > Batch mode. Type commands one per line.")
                print("Agent > Type 'end' to execute them.")
                print()

                batch_commands = []

                while True:
                    line = input("Batch > ").strip()

                    if line.lower() == "end":
                        break

                    if line:
                        batch_commands.append(line.lower())

                if not batch_commands:
                    print("Agent > No commands entered.")
                    print()
                    continue

                if all(local_git_dispatch(command) for command in batch_commands):
                    continue

                print("Agent > Batch contains unsupported commands.")
                print("Agent > Supported local commands:")
                print("  git remote")
                print("  git log")
                print("  git diff")
                print("  git info")
                print()
                continue

            # HELP
            if lower_request in ("help", "commands", "?"):
                show_help()
                continue

            # EXIT
            if lower_request == "exit":
                print("Agent > Goodbye!")
                break

            # CLEAR MEMORY
            if lower_request == "clear memory":
                memory = []
                save_memory(memory)
                print("Agent > Conversation memory cleared.")
                print()
                continue

            # CLEAR FACTS
            if lower_request == "clear facts":
                facts = {}
                save_facts(facts)
                print("Agent > Long-term facts cleared.")
                print()
                continue

            
            # LOCAL GIT COMMAND DISPATCHER
            request_lines = [
                line.strip()
                for line in lower_request.splitlines()
                if line.strip()
            ]

            if request_lines and all(
                line.startswith("git ")
                for line in request_lines
            ):
                if all(local_git_dispatch(line) for line in request_lines):
                    continue

            # STORAGE CLEANUP ADVISOR
            if lower_request == "storage advisor":
                storage_advisor()
                continue

            # RESOURCE INSPECTOR
            if lower_request == "resources":
                resource_info()
                continue

            # NETWORK INSPECTOR
            if lower_request == "network":
                network_info()
                continue

            # ENVIRONMENT INSPECTOR
            if lower_request == "environment":
                environment_info()
                continue

            # DEPENDENCY CHECK
            if lower_request == "check dependencies":
                check_dependencies()
                continue

            # HEALTH CHECK
            if lower_request == "health":
                diagnose_project()
                continue

            # ANALYZE PROJECT
            if lower_request == "analyze project":
                print("Agent > Analyzing project...")
                result = analyze_project()
                print("Agent >")
                print(result)
                print()
                continue

            # DIAGNOSE PROJECT
            if lower_request == "diagnose project":
                diagnose_project()
                continue

            # BACKUP PROJECT
            if lower_request == "backup project":
                print(
                    "Agent > This will create a backup "
                    "directory inside the current project."
                )

                if not ask_approval("create a project backup"):
                    print("Agent > Project backup cancelled.")
                    print()
                    continue

                result = backup_project()

                if result.startswith("ERROR:"):
                    print(f"Agent > {result}")
                else:
                    print("Agent > Project backup created:")
                    print(f"Agent > {result}/")

                print()
                continue

            # DIRECT COMMAND
            if lower_request.startswith("run command "):
                command = request[len("run command "):].strip()
                command_result = execute_with_approval(command)

                if command_result is not None:
                    memory.append({
                        "role": "tool",
                        "content": (
                            f"Command '{command}' returned:\n"
                            f"{command_result}"
                        )
                    })
                    save_memory(memory)

                print()
                continue

            # READ FILE
            if lower_request.startswith("read file "):
                filename = request[len("read file "):].strip()
                result = tool_read_file(filename)

                print("Agent > File contents:")
                print(result)
                print()
                continue

            # WRITE FILE
            if lower_request.startswith("write file "):
                filename = request[len("write file "):].strip()

                if not safe_filename(filename):
                    print("Agent > Invalid filename.")
                    print()
                    continue

                print("Agent > Enter the file content.")
                content = input("Content > ")

                execute_file_write_with_approval(filename, content)
                print()
                continue

            # CREATE FILE
            if lower_request.startswith("create file "):
                filename = request[len("create file "):].strip()

                if not safe_filename(filename):
                    print("Agent > Invalid filename.")
                    print()
                    continue

                if os.path.exists(filename):
                    print(f"Agent > File already exists: {filename}")
                    print()
                    continue

                execute_file_write_with_approval(filename, "")
                print()
                continue

            # MULTILINE WRITE
            if lower_request.startswith("write multiline file "):
                filename = request[
                    len("write multiline file "):
                ].strip()

                if not safe_filename(filename):
                    print("Agent > Invalid filename.")
                    print()
                    continue

                print(
                    "Agent > Enter lines. "
                    "Type END on its own line when finished."
                )

                lines = []

                while True:
                    line = input("Content > ")

                    if line == "END":
                        break

                    lines.append(line)

                content = "\n".join(lines)

                execute_file_write_with_approval(
                    filename,
                    content
                )

                print()
                continue

            # APPEND
            if lower_request.startswith("append file "):
                filename = request[len("append file "):].strip()

                if not safe_filename(filename):
                    print("Agent > Invalid filename.")
                    print()
                    continue

                if not os.path.isfile(filename):
                    print(f"Agent > File not found: {filename}")
                    print()
                    continue

                print("Agent > Enter the text to append.")
                content = input("Content > ")

                execute_file_append_with_approval(
                    filename,
                    content
                )

                print()
                continue

            # DELETE DIRECTORY
            if lower_request.startswith("delete directory "):
                dirname = request[
                    len("delete directory "):
                ].strip()

                execute_directory_delete_with_approval(dirname)
                print()
                continue

            # DELETE FILE
            if lower_request.startswith("delete file "):
                filename = request[
                    len("delete file "):
                ].strip()

                execute_file_delete_with_approval(filename)
                print()
                continue

            # CREATE DIRECTORY
            if lower_request.startswith("create directory "):
                dirname = request[
                    len("create directory "):
                ].strip()

                execute_directory_create_with_approval(dirname)
                print()
                continue

            # LIST DIRECTORY
            if lower_request.startswith("list directory"):
                parts = request.split(maxsplit=2)
                dirname = "."

                if len(parts) == 3:
                    dirname = parts[2].strip()

                result = tool_list_directory(dirname)

                print("Agent > Directory contents:")
                print(result)
                print()
                continue

            # CLEAN PROJECT
            if lower_request == "clean project":
                cleanup_items = get_cleanup_candidates()

                print("Agent > Cleanup candidates:")

                if not cleanup_items:
                    print("No cleanup candidates found.")
                    print()
                    continue

                for index, item in enumerate(
                    cleanup_items,
                    start=1
                ):
                    print(f"{index}. {item}")

                print()

                if not ask_approval(
                    "delete the listed cleanup candidates"
                ):
                    print("Agent > Cleanup cancelled.")
                    print()
                    continue

                deleted = 0

                for item in cleanup_items:
                    try:
                        if os.path.isdir(item):
                            shutil.rmtree(item)
                        else:
                            os.remove(item)

                        print(f"Agent > Deleted: {item}")
                        deleted += 1

                    except OSError as error:
                        print(
                            f"Agent > Could not delete "
                            f"{item}: {error}"
                        )

                print()
                print(
                    f"Agent > Cleanup complete. "
                    f"Deleted {deleted} item(s)."
                )
                print()
                continue

            # CLEANUP PREVIEW
            if lower_request == "project cleanup":
                cleanup_items = get_cleanup_candidates()

                print("Agent > Cleanup preview:")

                if cleanup_items:
                    for item in cleanup_items:
                        if os.path.isdir(item):
                            print(
                                f"- {item}/ "
                                f"(Python cache)"
                            )
                        elif item.endswith(".pyc"):
                            print(
                                f"- {item} "
                                f"(Python bytecode)"
                            )
                        else:
                            print(
                                f"- {item} "
                                f"(test file)"
                            )
                else:
                    print(
                        "No obvious temporary/test "
                        "files found."
                    )

                print()
                print("Agent > Nothing was deleted.")
                print()
                continue

            # PROJECT INFO
            if lower_request == "project info":
                files = 0
                directories = 0
                total_size = 0

                for entry in os.listdir("."):
                    if entry == ".git":
                        continue

                    if os.path.isfile(entry):
                        files += 1
                        total_size += os.path.getsize(entry)

                    elif os.path.isdir(entry):
                        directories += 1

                print("Agent > Project information:")
                print(f"Current directory: {os.getcwd()}")
                print(f"Files: {files}")
                print(f"Directories: {directories}")
                print(
                    f"Project size: "
                    f"{total_size / 1024:.2f} KB"
                )
                print(
                    f"agent.py: "
                    f"{'yes' if os.path.isfile('agent.py') else 'no'}"
                )
                print(
                    f"ai_client.py: "
                    f"{'yes' if os.path.isfile('ai_client.py') else 'no'}"
                )
                print()
                continue

            # CURRENT DIRECTORY
            if lower_request == "show current directory":
                print("Agent > Current directory:")
                print(os.getcwd())
                print()
                continue

            # PROJECT TREE
            if lower_request == "project tree":
                result = tool_project_tree()
                print("Agent > Project tree:")
                print(result)
                print()
                continue

            # MULTILINE EDIT
            if lower_request.startswith("edit multiline file "):
                filename = request[
                    len("edit multiline file "):
                ].strip()

                if not safe_filename(filename):
                    print("Agent > Invalid filename.")
                    print()
                    continue

                if not os.path.isfile(filename):
                    print(f"Agent > File not found: {filename}")
                    print()
                    continue

                print("Agent > Current file contents:")
                print()

                current_content = tool_read_file(filename)
                print(current_content)
                print()

                print(
                    "Agent > Enter the new complete "
                    "file contents."
                )
                print(
                    "Agent > Type END on its own line "
                    "when finished."
                )

                lines = []

                while True:
                    line = input("Content > ")

                    if line == "END":
                        break

                    lines.append(line)

                new_content = "\n".join(lines)

                print()
                print("Agent > Proposed new file:")
                print("--------------------------------")
                print(new_content)
                print("--------------------------------")

                execute_file_write_with_approval(
                    filename,
                    new_content
                )

                print()
                continue

            # INTERACTIVE EDIT
            if lower_request.startswith("edit file "):
                print("Agent > Interactive edit mode.")
                filename = input("File > ").strip()

                if not safe_filename(filename):
                    print("Agent > Invalid filename.")
                    print()
                    continue

                if not os.path.isfile(filename):
                    print(f"Agent > File not found: {filename}")
                    print()
                    continue

                old_text = input("Replace > ")
                new_text = input("With > ")

                execute_file_edit_with_approval(
                    filename,
                    old_text,
                    new_text
                )

                print()
                continue

            # FACTS
            facts = extract_facts(request, facts)

            # MEMORY
            memory.append({
                "role": "user",
                "content": request
            })
            save_memory(memory)

            # GEMINI PLAN
            tools = make_plan(request, memory, facts)
            results = {}

            if tools:
                print(
                    "Agent > Gemini plan: "
                    + ", ".join(tools)
                )

                for tool in tools:
                    print(f"Agent > Running {tool}...")

                    try:
                        if tool == "files":
                            results[tool] = tool_files()

                        elif tool == "read_file":
                            words = request.split()

                            if len(words) >= 3:
                                filename = words[-1]
                                results[tool] = tool_read_file(
                                    filename
                                )
                            else:
                                results[tool] = (
                                    "No filename specified."
                                )

                        elif tool == "git":
                            results[tool] = tool_git()

                        elif tool == "system":
                            results[tool] = tool_system()

                        elif tool == "time":
                            results[tool] = tool_time()

                        elif tool == "analyze_project":
                            results[tool] = analyze_project()

                    except Exception as error:
                        results[tool] = f"Tool error: {error}"

            # FINAL ANSWER
            answer = create_final_answer(
                request,
                results,
                memory,
                facts
            )

            print("Agent >")
            print(answer)
            print()

            memory.append({
                "role": "assistant",
                "content": answer
            })

            save_memory(memory)

        except KeyboardInterrupt:
            print("\nAgent > Goodbye!")
            break

        except Exception as error:
            print(f"Agent > Unexpected error: {error}")
            print()


if __name__ == "__main__":
    main()
