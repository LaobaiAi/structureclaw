---
id: seismic-load
zhName: 地震荷载施加
enName: Seismic Load Application
zhDescription: 识别并施加地震荷载工况的 skill，支持反应谱法、时程分析法。
enDescription: Skill for identifying and applying seismic load cases, supporting response spectrum analysis and time history analysis.
software: generic
analysisType: load
engineId: builtin-generic
adapterKey: builtin-generic
priority: 80
triggers: ["地震", "地震荷载", "抗震", "seismic", "earthquake", "seismic load"]
stages: ["loads"]
capabilities: ["load-generation", "load-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Seismic Load Application

- `zh`: 当用户明确要求添加地震荷载时使用。支持根据设防烈度、场地类别计算地震作用。
- `en`: Use when the request explicitly asks to add seismic loads. Supports earthquake action calculation based on seismic intensity and site category.
- Runtime: `load-boundary/seismic-load/runtime.py`
