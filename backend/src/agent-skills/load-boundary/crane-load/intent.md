---
id: crane-load
zhName: 吊车荷载施加
enName: Crane Load Application
zhDescription: 识别并施加吊车荷载的 skill。
enDescription: Skill for identifying and applying crane loads.
software: generic
analysisType: load
engineId: builtin-generic
adapterKey: builtin-generic
priority: 60
triggers: ["吊车", "吊车荷载", "桥式起重机", "crane load", "overhead crane"]
stages: ["loads"]
capabilities: ["load-generation", "load-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Crane Load Application

- `zh`: 当用户明确要求添加吊车荷载时使用。支持桥式起重机、悬挂起重机等吊车荷载计算。
- `en`: Use when the request explicitly asks to add crane loads. Supports calculation of overhead crane, suspended crane, and other crane loads.
- Runtime: `load-boundary/crane-load/runtime.py`
