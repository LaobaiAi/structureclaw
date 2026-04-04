---
id: snow-load
zhName: 雪荷载施加
enName: Snow Load Application
zhDescription: 识别并施加屋面积雪荷载的 skill。
enDescription: Skill for identifying and applying snow loads on roofs.
software: generic
analysisType: load
engineId: builtin-generic
adapterKey: builtin-generic
priority: 65
triggers: ["雪载", "雪荷载", "积雪", "snow load"]
stages: ["loads"]
capabilities: ["load-generation", "load-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Snow Load Application

- `zh`: 当用户明确要求添加雪荷载时使用。支持根据规范标准自动生成或指定雪载值。
- `en`: Use when the request explicitly asks to add snow loads. Supports automatic generation based on code standards or specified snow load values.
- Runtime: `load-boundary/snow-load/runtime.py`
