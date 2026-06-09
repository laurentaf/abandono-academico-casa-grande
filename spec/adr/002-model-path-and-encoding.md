# ADR-002: Model path para src/ e categorical encoding via pandas .cat.codes

## Status

Accepted

## Context

Na Fase 1 (ADR-001), o modelo era salvo em `models/model.pkl` e o categorical encoding usava `sklearn.preprocessing.LabelEncoder`. Na Fase 3, a DataMission briefing e a reestruturação do pipeline exigem:

1. O modelo deve ficar em `src/model.pkl` (colocado junto ao código da pipeline, não em diretório separado).
2. `LabelEncoder` introduz ordinalidade artificial em `course_name` — o próprio ADR-001 já sinalizava isso como consequência negativa ("LabelEncoder em course_name introduz ordinalidade artificial — target encoding pode ser melhor na Fase 2").
3. Os 6 DQ baseline checks (DQ-01 a DQ-06) rodam antes do preprocessamento, exigindo que a função de preprocessamento seja separada de `train_model()`.

## Decision

1. **Model path:** `src/model.pkl` (antes: `models/model.pkl`). O pickle agora contém `{"model": clf, "course_categories": {int: str}}` — o mapping de categorias substitui o `LabelEncoder` que era salvo junto ao modelo.

2. **Categorical encoding:** `pandas .cat.codes` ao invés de `sklearn.LabelEncoder`. O mapeamento categoria→código é preservado via `df["course_name"].cat.categories` e salvo no pickle do modelo como `course_categories`.

3. **Separação de preprocessamento:** `preprocess_data(df)` é função separada que (a) faz drop de nulls com logging, (b) cria coluna target, (c) encodes `course_name` via `.cat.codes`. `train_model(df)` recebe o DataFrame já preprocessado.

## Alternatives

### A) Manter LabelEncoder
Vantagem: compatibilidade com o pickle da Fase 1. Desvantagem: ordinalidade artificial permanece; ADR-001 já recomendava evoluir.

### B) One-hot encoding (pd.get_dummies)
Vantagem: elimina ordinalidade completamente. Desvantagem: explode dimensionalidade se `course_name` tiver muitas categorias; RandomForest lida bem com ordinal encoding leve.

### C) Target encoding
Vantagem: melhor para modelos lineares. Desvantagem: requer hold-out para evitar leakage; complexidade desnecessária para baseline RandomForest.

## Consequences

+ Modelo e código no mesmo diretório (`src/`) — deploy simplificado
+ Sem dependência de `sklearn.preprocessing.LabelEncoder` no preprocessing — sklearn fica apenas no treino
+ `.cat.codes` é nativo do pandas, sem objeto auxiliar para serializar
+ Mapping de categorias preservado no pickle (course_categories) — inferência pode mapear de volta
+ Pipeline encadeada: fetch → DQ checks → preprocess → train → metrics (cada etapa é testável isoladamente)
- Pickle da Fase 1 (`models/model.pkl` com LabelEncoder) é incompatível — requer re-treino
- `.cat.codes` atribui -1 a NaN; como `preprocess_data()` faz `dropna()` antes, isso não ocorre

## Atualiza ao ADR-001

ADR-001 §Consequences listava: "LabelEncoder em course_name introduz ordinalidade artificial". Esta consequência negativa é resolvida por este ADR-002.
