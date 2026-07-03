"""Check installed packages."""
import sys
print(f"Python {sys.version}")

packages = [
    ("sklearn", "sklearn"),
    ("xgboost", "xgboost"),
    ("lightgbm", "lightgbm"),
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("duckdb", "duckdb"),
    ("joblib", "joblib"),
]

for import_name, display_name in packages:
    try:
        pkg = __import__(import_name)
        ver = getattr(pkg, "__version__", "unknown")
        print(f"  {display_name}: {ver} OK")
    except ImportError as e:
        print(f"  {display_name}: NOT FOUND ({e})")
