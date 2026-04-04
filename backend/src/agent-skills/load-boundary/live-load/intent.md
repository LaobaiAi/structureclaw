---
id: live-load
zhName: 活载施加
enName: Live Load Application
zhDescription: 识别并施加楼面活载、屋面活载、设备荷载等活载工况的 skill。
enDescription: Skill for identifying and applying live load cases such as floor live loads, roof live loads, and equipment loads.
software: generic
analysisType: load
engineId: builtin-generic
adapterKey: builtin-generic
priority: 90
triggers: ["活载", "楼面荷载", "可变荷载", "live load", "floor load", "variable load"]
stages: ["loads"]
capabilities: ["load-generation", "load-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Live Load Application

- `zh`: 当用户明确要求添加活载、楼面荷载、可变荷载时使用。支持根据规范标准自动生成或指定活载值。
- `en`: Use when the request explicitly asks to add live load, floor load, or variable load. Supports automatic generation based on code standards or specified live load values.
- Runtime: `load-boundary/live-load/runtime.py`
