# SPEC-000: Bootstrap — Abandono Acadêmico Casa Grande

**Status:** ACEITO
**Version:** 1.0
**Authors:** Laurent
**Owner:** Laurent

---

## Contexto

Pipeline de previsão de abandono acadêmico para a Universidade Casa Grande,
via DataMission (project ID: 2e4ce469-1a75-45fb-a41e-160196c7b989).
Dataset: 1000 registros, 7 colunas (student_id, timestamp, course_name,
enrollment_status, grade_point_average, attendance_rate, scholarship_percent).
Target: enrollment_status (SUSPENDED = possível abandono).

## Decisão inicial

- Stack: Python (pandas, scikit-learn, requests, dbt)
- Ingestão: API DataMission → parquet local
- Modelagem: classificador scikit-learn (baseline)
- 3 fases + fase 4 opcional (dashboard + simulação)

## Critérios de pronto

- [ ] src/main.py com main(), fetch_dataset(), train_model()
- [ ] requirements.txt com pandas, scikit-learn, requests, dbt
- [ ] Modelo treinado e salvo
- [ ] Métricas documentadas em reports/
