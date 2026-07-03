"""
Full pipeline runner. This script exists to be called via uv run with file-based logging.
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

log_path = Path(__file__).resolve().parent.parent / "artifacts" / "data" / "pipeline_run.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

# Redirect all print output to both stdout and log file
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

log_file = open(log_path, "w", encoding="utf-8")
sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)

print(f"[runner] Starting pipeline at {__import__('datetime').datetime.now()}")
print(f"[runner] Python: {sys.version}")

# Import and run main
from src.main import main
main()

print(f"[runner] Pipeline finished at {__import__('datetime').datetime.now()}")
log_file.close()
