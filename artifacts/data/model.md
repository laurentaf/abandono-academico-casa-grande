# Data Model — Abandono Acadêmico Casa Grande

## Source
- **API:** `https://api.datamission.com.br/projects/2e4ce469-1a75-45fb-a41e-160196c7b989/dataset?format=parquet`
- **Format:** Parquet (alternativa: JSON, CSV)
- **Rows:** 1000
- **Refresh:** on-demand (Fase 1 batch)

## Schema

| Column | Type | Description | Role |
|--------|------|-------------|------|
| student_id | UUID | Identificador do estudante | dimension key |
| timestamp | ISO datetime | Momento do registro | temporal |
| course_name | string | Nome do curso (categorical) | feature |
| enrollment_status | string | ACTIVE / SUSPENDED / DROPPED / GRADUATED | **target** |
| grade_point_average | float | CRA do estudante (0-4?) | feature |
| attendance_rate | int | Percentual de presença (0-100) | feature |
| scholarship_percent | int | Percentual de bolsa (0-100) | feature |

## Grain
One row per student observation (timestamped).

## Target encoding
- `SUSPENDED` → 1 (abandono)
- `ACTIVE`, `DROPPED`, `GRADUATED` → 0 (não-abandono)

## Feature engineering (Fase 1)
- `course_name` → LabelEncoder (`course_name_enc`)
- `grade_point_average`, `attendance_rate`, `scholarship_percent` → usados como-is

## Keys
- **PK:** (student_id, timestamp)
- **FK:** none (flat dataset)

## Partitioning strategy
N/A (Fase 1 — arquivo único parquet)

## Refresh cadence
On-demand (batch), via `fetch_dataset()` in `src/main.py`.

## Source lineage
API DataMission → parquet local → pandas DataFrame → sklearn model

## Owner
Laurent (data-architect)
