@echo off
cd /d "E:\projects\abandono-academico-casa-grande"
uv run python -u src\main.py > artifacts\data\pipeline_output.log 2>&1
echo Exit code: %errorlevel%
