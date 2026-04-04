---
id: boundary-condition
zhName: 边界条件施加
enName: Boundary Condition Application
zhDescription: 识别并施加节点约束、杆端释放、计算长度等边界条件的 skill。
enDescription: Skill for identifying and applying boundary conditions such as nodal constraints, member end releases, and effective lengths.
software: generic
analysisType: boundary
engineId: builtin-generic
adapterKey: builtin-generic
priority: 95
triggers: ["边界条件", "约束", "支座", "铰接", "固结", "boundary condition", "constraint", "support", "hinge", "fix"]
stages: ["loads"]
capabilities: ["boundary-generation", "boundary-validation"]
supportedModelFamilies: ["frame", "truss", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# Boundary Condition Application

- `zh`: 当用户明确要求添加边界条件、节点约束、杆端释放、计算长度时使用。支持常见边界条件的快速设置。
- `en`: Use when the request explicitly asks to add boundary conditions, nodal constraints, member end releases, or effective lengths. Supports quick setup of common boundary conditions.
- Runtime: `load-boundary/boundary-condition/runtime.py`
