"""
Download OULAD dataset from Figshare.
Creates data/oulad/ directory with all 7 CSV files.
"""
import io
import zipfile
from pathlib import Path

import requests
import duckdb

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "oulad"
DUCKDB_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "data" / "oulad.duckdb"

# Correct download URL from Figshare API
OULAD_URL = "https://ndownloader.figshare.com/files/8606371"

EXPECTED_CSVS = {
    "studentInfo.csv",
    "studentRegistration.csv",
    "studentAssessment.csv",
    "studentVle.csv",
    "assessments.csv",
    "courses.csv",
    "vle.csv",
}


def download_oulad():
    """Download OULAD zip and extract CSVs."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    existing = set(p.name for p in DATA_DIR.glob("*.csv"))
    if EXPECTED_CSVS.issubset(existing):
        file_sizes = [(p.name, p.stat().st_size) for p in DATA_DIR.glob("*.csv")]
        print(f"[download] All CSVs already present in {DATA_DIR}")
        for name, size in sorted(file_sizes):
            print(f"  {name}: {size:,} bytes")
        return

    print(f"[download] Downloading OULAD dataset from Figshare...")
    print(f"[download] URL: {OULAD_URL}")
    resp = requests.get(OULAD_URL, stream=True, timeout=600)
    resp.raise_for_status()

    # Verify it's a zip
    content_type = resp.headers.get("content-type", "")
    print(f"[download] Content-Type: {content_type}")
    print(f"[download] Content-Length: {resp.headers.get('content-length', 'unknown')}")

    # The response is a zip file containing the CSV files
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    extracted = 0
    for file_info in z.infolist():
        # Files in the zip have paths like "anonymisedData/studentInfo.csv"
        # or just "studentInfo.csv"
        filename = Path(file_info.filename).name
        if filename in EXPECTED_CSVS:
            target_path = DATA_DIR / filename
            if not target_path.exists():
                with z.open(file_info) as source, open(target_path, "wb") as target:
                    target.write(source.read())
                extracted += 1
                print(f"[download] Extracted: {filename}")

    print(f"[download] Extracted {extracted} files")

    # Verify
    existing = set(p.name for p in DATA_DIR.glob("*.csv"))
    missing = EXPECTED_CSVS - existing
    if missing:
        print(f"[download] WARNING: Missing CSVs: {missing}")
        # Try listing what's in the zip
        print("[download] Files in zip:")
        for fi in z.infolist():
            print(f"  {fi.filename}")
    else:
        print(f"[download] All {len(EXPECTED_CSVS)} OULAD CSV files ready")


def create_duckdb():
    """Create oulad.duckdb from CSV files."""
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DUCKDB_PATH.exists():
        print(f"[duckdb] {DUCKDB_PATH} already exists, recreating...")
        DUCKDB_PATH.unlink()

    con = duckdb.connect(str(DUCKDB_PATH))

    # Load Bronze tables
    files_and_tables = [
        ("studentInfo.csv", "bronze_student_info"),
        ("studentRegistration.csv", "bronze_student_registration"),
        ("studentAssessment.csv", "bronze_student_assessment"),
        ("studentVle.csv", "bronze_student_vle"),
        ("assessments.csv", "bronze_assessments"),
        ("courses.csv", "bronze_courses"),
        ("vle.csv", "bronze_vle"),
    ]

    for filename, table_name in files_and_tables:
        csv_path = DATA_DIR / filename
        if not csv_path.exists():
            print(f"[duckdb] ERROR: {csv_path} not found!")
            continue

        con.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_csv_auto('{csv_path.as_posix()}', header=True)
        """)
        row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"[duckdb] {table_name}: {row_count:,} rows")

    # Silver: VLE aggregation
    con.execute("""
        CREATE OR REPLACE TABLE silver_vle_agg AS
        SELECT
            code_module, code_presentation, id_student,
            SUM(sum_click) AS total_clicks,
            COUNT(DISTINCT date) AS days_active,
            MAX(date) AS last_activity_day,
            MIN(date) AS first_activity_day,
            SUM(CASE WHEN date >= 0 THEN sum_click ELSE 0 END)::DOUBLE /
                NULLIF(SUM(sum_click), 0) AS click_trend
        FROM bronze_student_vle
        GROUP BY code_module, code_presentation, id_student
    """)
    print(f"[duckdb] silver_vle_agg: {con.execute('SELECT COUNT(*) FROM silver_vle_agg').fetchone()[0]:,} rows")

    # Silver: Assessment aggregation
    con.execute("""
        CREATE OR REPLACE TABLE silver_assessment_agg AS
        SELECT
            sa.id_student, a.code_module, a.code_presentation,
            SUM(sa.score * a.weight) / NULLIF(SUM(a.weight), 0) AS weighted_avg_score,
            COUNT(CASE WHEN a.assessment_type = 'TMA' THEN 1 END) AS num_tma,
            COUNT(CASE WHEN a.assessment_type = 'CMA' THEN 1 END) AS num_cma,
            COUNT(CASE WHEN a.assessment_type = 'Exam' THEN 1 END) AS num_exams,
            AVG(sa.score) AS avg_score,
            MIN(sa.score) AS min_score,
            MAX(sa.score) AS max_score,
            AVG(sa.date_submitted - a.date) AS avg_submission_delta
        FROM bronze_student_assessment sa
        JOIN bronze_assessments a ON sa.id_assessment = a.id_assessment
        GROUP BY sa.id_student, a.code_module, a.code_presentation
    """)
    print(f"[duckdb] silver_assessment_agg: {con.execute('SELECT COUNT(*) FROM silver_assessment_agg').fetchone()[0]:,} rows")

    # Gold table
    con.execute("""
        CREATE OR REPLACE TABLE gold_oulad_features AS
        SELECT
            si.code_module, si.code_presentation, si.id_student,
            si.gender, si.region, si.highest_education, si.imd_band, si.age_band,
            si.num_of_prev_attempts, si.studied_credits, si.disability,
            sr.date_registration, sr.date_unregistration,
            COALESCE(va.total_clicks, 0) AS total_clicks,
            COALESCE(va.days_active, 0) AS days_active,
            COALESCE(va.last_activity_day, -999) AS last_activity_day,
            COALESCE(va.first_activity_day, -999) AS first_activity_day,
            COALESCE(va.click_trend, 0.5) AS click_trend,
            CASE WHEN COALESCE(va.days_active, 0) > 0
                 THEN COALESCE(va.total_clicks, 0)::DOUBLE / va.days_active
                 ELSE 0 END AS avg_daily_clicks,
            COALESCE(aa.weighted_avg_score, 0) AS weighted_avg_score,
            COALESCE(aa.num_tma, 0) AS num_tma,
            COALESCE(aa.num_cma, 0) AS num_cma,
            COALESCE(aa.num_exams, 0) AS num_exams,
            COALESCE(aa.avg_score, 0) AS avg_assessment_score,
            COALESCE(aa.avg_submission_delta, 0) AS avg_submission_delta,
            c.module_presentation_length,
            CASE WHEN si.final_result = 'Withdrawn' THEN 1 ELSE 0 END AS is_dropout,
            si.final_result AS final_result_label
        FROM bronze_student_info si
        LEFT JOIN bronze_student_registration sr
            ON si.code_module = sr.code_module AND si.code_presentation = sr.code_presentation AND si.id_student = sr.id_student
        LEFT JOIN silver_vle_agg va
            ON si.code_module = va.code_module AND si.code_presentation = va.code_presentation AND si.id_student = va.id_student
        LEFT JOIN silver_assessment_agg aa
            ON si.code_module = aa.code_module AND si.code_presentation = aa.code_presentation AND si.id_student = aa.id_student
        LEFT JOIN bronze_courses c
            ON si.code_module = c.code_module AND si.code_presentation = c.code_presentation
    """)
    gold_rows = con.execute("SELECT COUNT(*) FROM gold_oulad_features").fetchone()[0]
    dropout_rate = con.execute("SELECT AVG(is_dropout) FROM gold_oulad_features").fetchone()[0]
    print(f"[duckdb] gold_oulad_features: {gold_rows:,} rows (dropout rate: {dropout_rate:.1%})")

    con.close()
    print(f"[duckdb] Database saved: {DUCKDB_PATH} ({DUCKDB_PATH.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    download_oulad()
    create_duckdb()
    print("[download] Done!")
