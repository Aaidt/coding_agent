import os
import json
import subprocess


def list_files(path: str) -> str:
    try:
        return json.dumps({"files": os.listdir(path)})
    except Exception as e:
        return json.dumps({"error": str(e)})


def read_file(path: str) -> str:
    try:
        if not os.path.isfile(path):
            return json.dumps({"error": "File not found"})

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return json.dumps({"content": content})

    except Exception as e:
        return json.dumps({"error": f"Could not read file: {e}"})


def write_file(path: str, code: str) -> str:
    try:
        dir = os.path.dirname(path)
        if dir:
            os.makedirs(path, exist_ok=True)

        if os.path.isdir(path):
            return json.dumps({"error": "Cant write in a directory."})

        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        return json.dumps({"status": "success", "path": path, "bytes": len(code)})

    except Exception as e:
        return json.dumps({"error": str(e)})


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


def main():
    print("Hello from coding-agent!")


if __name__ == "__main__":
    main()
