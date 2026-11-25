import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    commands = {
        "API": [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        "Worker": [
            sys.executable,
            "-m",
            "app.worker",
        ],
    }

    processes = []

    try:
        for name, command in commands.items():
            process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
            )
            processes.append((name, process))
            print(f"{name} started with process ID {process.pid}.", flush=True)

        print("Press Ctrl+C to stop the application.", flush=True)

        while True:
            for name, process in processes:
                exit_code = process.poll()

                if exit_code is not None:
                    print(
                        f"{name} exited with code {exit_code}.",
                        flush=True,
                    )
                    return exit_code or 1

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping the application...", flush=True)
        return 0

    except OSError as error:
        print(f"Could not start the application: {error}", flush=True)
        return 1

    finally:
        for name, process in processes:
            if process.poll() is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass

        for name, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())