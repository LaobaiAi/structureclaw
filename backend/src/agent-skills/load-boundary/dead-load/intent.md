---
id: dead-load
zhName: 恒载施加
enName: Dead Load Application
zhDescription: 识别并施加结构自重、永久荷载等恒载工况的 skill。
enDescription: Skill for identifying and applying dead load cases such as structural self-weight and permanent loads.
software: generic
analysisType: load
engineId: builtin-generic
adapterKey: builtin-generic
priority: 100
triggers: ["恒载", "自重", "永久荷载", "dead load", "self-weight", "permanent load"]
stages: ["loads"]
capabilities: ["load-generation", "load-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Dead Load Application

- `zh`: 当用户明确要求添加恒载、结构自重、永久荷载时使用。支持自动计算构件自重或指定恒载值。
- `en`: Use when the request explicitly asks to add dead load, structural self-weight, or permanent loads. Supports automatic member self-weight calculation or specified dead load values.
- Runtime: `load-boundary/dead-load/runtime.py`
