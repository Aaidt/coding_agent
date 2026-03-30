import os
import json
import subprocess
import dotenv
from langchain_core.tools import tool

dotenv.load_dotenv()

BASE_DIR = os.path.realpath(os.getcwd())


def resolve_path(user_path: str) -> str:
    full_path = os.path.join(BASE_DIR, user_path)
    full_path = os.path.relpath(full_path)

    if not full_path.startswith(BASE_DIR + os.sep):
        raise ValueError("Access outside working directory is not allowed")

    return full_path


@tool
def list_files(path: str) -> str:
    path = resolve_path(path)
    try:
        return json.dumps({"files": os.listdir(path)})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def read_file(path: str) -> str:
    path = resolve_path(path)
    try:
        if not os.path.isfile(path):
            return json.dumps({"error": "File not found"})

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return json.dumps({"content": content})

    except Exception as e:
        return json.dumps({"error": f"Could not read file: {e}"})


@tool
def write_file(path: str, code: str) -> str:
    path = resolve_path(path)
    try:
        dir = os.path.dirname(path)
        if dir:
            os.makedirs(dir, exist_ok=True)

        if os.path.isdir(path):
            return json.dumps({"error": "Cant write in a directory."})

        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        return json.dumps({"status": "success", "path": path, "bytes": len(code)})

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def run_python(code):
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return json.dumps(
            {
                "stdout": result.stdout[:2000] if result.stdout else "",
                "stderr": result.stderr[:2000] if result.stderr else "",
                "exit_code": result.returncode,
            }
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Timed out (15s limit)"})
    except Exception as e:
        return json.dumps({"error": str(e)})


tools = [read_file, write_file, list_files, run_python]
