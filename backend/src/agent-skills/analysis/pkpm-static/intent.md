---
id: pkpm-static
zhName: PKPM 静力分析
enName: PKPM Static Analysis
zhDescription: 使用 PKPM SATWE 引擎执行静力分析的 skill（需安装 PKPM 及 JWSCYCLE.exe）。
enDescription: Skill for static analysis using the PKPM SATWE engine (requires PKPM installation and JWSCYCLE.exe).
software: pkpm
analysisType: static
engineId: builtin-pkpm
adapterKey: builtin-pkpm
priority: 130
triggers: ["PKPM 静力分析", "PKPM 计算", "SATWE", "pkpm static", "pkpm analysis"]
stages: ["analysis"]
capabilities: ["analysis-policy", "analysis-execution"]
supportedModelFamilies: ["frame", "generic"]
autoLoadByDefault: true
runtimeRelativePath: runtime.py
---
# PKPM Static Analysis

- `zh`: 当用户要求使用 PKPM 进行结构静力计算、设计验算、施工图生成时使用。需要已安装 PKPM 并配置 `PKPM_CYCLE_PATH` 环境变量。
- `en`: Use when the request asks for PKPM-based structural static analysis, design checks, or construction drawing generation. Requires PKPM installation and the `PKPM_CYCLE_PATH` environment variable.
- Runtime: `analysis/pkpm-static/runtime.py`
