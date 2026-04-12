---
id: yjk-static
zhName: YJK 静力分析
enName: YJK Static Analysis
zhDescription: 使用 YJK (盈建科) 引擎自动建模并执行静力分析，提取节点位移、构件内力、楼层刚度等结构化结果（需安装 YJK 8.0 并配置 YJKS_ROOT 或 YJK_PATH）。
enDescription: Automated modeling and static analysis using the YJK engine. Extracts node displacements, member forces, and floor statistics as structured results (requires YJK 8.0 and YJKS_ROOT or YJK_PATH).
software: yjk
analysisType: static
engineId: builtin-yjk
adapterKey: builtin-yjk
priority: 125
triggers: ["YJK 静力分析", "YJK 计算", "盈建科", "yjk static", "yjk analysis"]
stages: ["analysis"]
capabilities: ["analysis-policy", "analysis-execution"]
supportedModelFamilies: ["frame", "generic"]
autoLoadByDefault: false
runtimeRelativePath: runtime.py
---
# YJK Static Analysis

- `zh`: 当用户要求使用 YJK（盈建科）进行结构静力计算、设计验算时使用。自动将 V2 模型转换为 YJK 格式，启动盈建科软件执行建模、前处理、整体计算，并通过 yjks_pyload 提取结构化分析结果（节点位移、构件内力、楼层刚度/受剪承载力）。需要已安装 YJK 8.0 并配置 `YJKS_ROOT` 或 `YJK_PATH` 指向安装根目录（与官方 SDK 示例一致）。
- `en`: Use when the request asks for YJK-based structural static analysis or design checks. Automatically converts V2 model to YJK format, launches YJK for modeling, preprocessing, and full calculation, then extracts structured results (node displacements, member forces, floor stiffness/shear capacity) via yjks_pyload. Requires YJK 8.0 and `YJKS_ROOT` or `YJK_PATH` pointing to the install root (same convention as the official YJK SDK samples).
- Runtime: `analysis/yjk-static/runtime.py`
