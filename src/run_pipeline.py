"""Simple wrapper to run main.py with output captured to a file."""
import subprocess
import sys
from pathlib import Path

log_path = Path(__file__).resolve().parent.parent / "artifacts" / "data" / "pipeline_output.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

print(f"Running main.py, output -> {log_path}")
with open(log_path, "w", encoding="utf-8") as f:
    result = subprocess.run(
        [sys.executable, "-u", str(Path(__file__).resolve().parent / "main.py")],
        capture_output=True,
        text=True,
        timeout=600,
    )
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr)

print(f"Exit code: {result.returncode}")
print(f"Output written to {log_path}")
if result.returncode != 0:
    print("ERRORS:")
    print(result.stderr[-2000:])
else:
    print(result.stdout[-2000:])
