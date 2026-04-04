---
id: temperature-load
zhName: 温度荷载施加
enName: Temperature Load Application
zhDescription: 识别并施加温度变化引起的荷载工况的 skill。
enDescription: Skill for identifying and applying temperature-induced load cases.
software: generic
analysisType: load
engineId: builtin-generic
adapterKey: builtin-generic
priority: 70
triggers: ["温度", "温度荷载", "温差", "temperature", "thermal load"]
stages: ["loads"]
capabilities: ["load-generation", "load-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Temperature Load Application

- `zh`: 当用户明确要求添加温度荷载时使用。支持温度变化引起的结构变形计算。
- `en`: Use when the request explicitly asks to add temperature loads. Supports calculation of structural deformation caused by temperature changes.
- Runtime: `load-boundary/temperature-load/runtime.py`
