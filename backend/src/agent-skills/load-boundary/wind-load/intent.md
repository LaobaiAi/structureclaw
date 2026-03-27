---
id: wind-load
zhName: 风荷载施加
enName: Wind Load Application
zhDescription: 识别并施加风荷载工况的 skill，支持风压、风吸力计算。
enDescription: Skill for identifying and applying wind load cases, supporting wind pressure and suction calculations.
software: generic
analysisType: load
engineId: builtin-generic
adapterKey: builtin-generic
priority: 85
triggers: ["风载", "风荷载", "wind load", "wind pressure"]
stages: ["loads"]
capabilities: ["load-generation", "load-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Wind Load Application

- `zh`: 当用户明确要求添加风荷载时使用。支持根据基本风压、高度系数、体型系数计算风压。
- `en`: Use when the request explicitly asks to add wind loads. Supports wind pressure calculation based on basic wind pressure, height factor, and shape factor.
- Runtime: `load-boundary/wind-load/runtime.py`
