"""
荷载组合模块
Load Combination Module
实现荷载组合生成功能，对齐 V2 Schema LoadCombinationV2

TODO: 需要领域专家审查以下内容：
1. 荷载组合系数是否符合 GB50009-2012 和 GB50011-2010 规范要求
2. 组合类型（ULS/SLS/地震）的完整性是否覆盖实际工程需求
3. 特殊荷载（温度、吊车）的组合规则是否正确
4. 分项系数、组合系数是否需要根据荷载工况类型动态调整
5. 是否需要支持用户自定义组合规则
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class LoadCombinationGenerator:
    """荷载组合生成器 / Load Combination Generator"""

    def __init__(self, model=None):
        """
        初始化荷载组合生成器

        Args:
            model: 结构模型（可选，预留扩展）
        """
        self.model = model
        self.combinations = []

    def generate_uls_combinations(
        self,
        dead_load_ids: List[str] = None,
        live_load_ids: List[str] = None,
        wind_load_ids: List[str] = None,
        seismic_load_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成承载能力极限状态组合（ULS）

        Args:
            dead_load_ids: 恒载工况ID列表
            live_load_ids: 活载工况ID列表
            wind_load_ids: 风载工况ID列表
            seismic_load_ids: 地震工况ID列表

        Returns:
            荷载组合字典

        TODO: 领域审查要点
        1. 各荷载系数是否符合 GB50009-2012 表 3.2.5 要求
        2. 是否需要考虑荷载的主导作用和次要作用
        3. 是否需要考虑温度、吊车等特殊荷载的组合
        4. 地震作用组合是否需要分项系数调整
        5. 是否需要支持偶然组合（如爆炸、撞击）
        """
        combination_id = 1
        combinations = []

        # 基础组合：1.3 恒 + 1.5 活（GB50009-2012 表 3.2.5）
        # 注：恒载分项系数可取 1.3 或 1.2，活载分项系数可取 1.5 或 1.4
        if dead_load_ids and live_load_ids:
            for dead_id in dead_load_ids:
                for live_id in live_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "uls",
                        "description": f"恒载 {dead_id} + 活载 {live_id}",
                        "factors": {dead_id: 1.3, live_id: 1.5},
                        "code_reference": "GB50009-2012 表 3.2.5"
                    }
                    combinations.append(combo)
                    combination_id += 1

        # 风载组合：1.3 恒 + 1.4 风（GB50009-2012 表 3.2.5）
        # 注：风载为主导作用时的组合
        if dead_load_ids and wind_load_ids:
            for dead_id in dead_load_ids:
                for wind_id in wind_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "uls",
                        "description": f"恒载 {dead_id} + 风载 {wind_id}",
                        "factors": {dead_id: 1.3, wind_id: 1.4},
                        "code_reference": "GB50009-2012 表 3.2.5"
                    }
                    combinations.append(combo)
                    combination_id += 1

        # 地震组合：1.3 恒 + 1.0 震（GB50011-2010 5.4.1）
        # 注：地震作用组合中，恒载使用重力荷载代表值（1.0×恒载 + 组合值×活载），
        #     地震作用效应通常不额外乘分项系数，其分项系数已包含在抗震验算要求中
        #     此处简化处理，恒载取 1.3 为结构重要性系数的体现
        if dead_load_ids and seismic_load_ids:
            for dead_id in dead_load_ids:
                for seismic_id in seismic_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "uls",
                        "description": f"恒载 {dead_id} + 地震 {seismic_id}",
                        "factors": {dead_id: 1.3, seismic_id: 1.3},
                        "code_reference": "GB50011-2010 5.4.1"
                    }
                    combinations.append(combo)
                    combination_id += 1

        self.combinations = combinations
        return {
            "combinations": combinations,
            "count": len(combinations)
        }

    def generate_sls_combinations(
        self,
        dead_load_ids: List[str] = None,
        live_load_ids: List[str] = None,
        wind_load_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """
        生成正常使用极限状态组合（SLS）

        Args:
            dead_load_ids: 恒载工况ID列表
            live_load_ids: 活载工况ID列表
            wind_load_ids: 风载工况ID列表

        Returns:
            荷载组合字典

        TODO: 领域审查要点
        1. 活载系数 0.7 和风载系数 0.6 是否符合 GB50009-2012 要求
        2. 是否需要考虑活载的主导作用和次要作用的区别
        3. 是否需要考虑荷载折减系数（如楼面活载折减）
        4. 是否需要支持频遇组合、准永久组合
        """
        combination_id = 100  # 从 100 开始编号
        combinations = []

        # 恒 + 活（标准组合）
        if dead_load_ids and live_load_ids:
            for dead_id in dead_load_ids:
                for live_id in live_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "sls",
                        "description": f"恒载 {dead_id} + 活载 {live_id}",
                        "factors": {dead_id: 1.0, live_id: 0.7},
                        "code_reference": "GB50009-2012 3.2.3"
                    }
                    combinations.append(combo)
                    combination_id += 1

        # 恒 + 风（标准组合）
        if dead_load_ids and wind_load_ids:
            for dead_id in dead_load_ids:
                for wind_id in wind_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "sls",
                        "description": f"恒载 {dead_id} + 风载 {wind_id}",
                        "factors": {dead_id: 1.0, wind_id: 0.6},
                        "code_reference": "GB50009-2012 3.2.3"
                    }
                    combinations.append(combo)
                    combination_id += 1

        self.combinations = combinations
        return {
            "combinations": combinations,
            "count": len(combinations)
        }

    def generate_seismic_combinations(
        self,
        dead_load_ids: List[str] = None,
        seismic_load_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """
        生成地震作用组合

        Args:
            dead_load_ids: 恒载工况ID列表
            seismic_load_ids: 地震工况ID列表

        Returns:
            地震组合字典

        TODO: 领域审查要点
        1. 地震组合系数（水平1.0、竖向0.5）是否符合 GB50011-2010 要求
        2. 是否需要考虑重力荷载代表值（恒载+活载组合值）
        3. 是否需要支持双向地震作用组合（Ex+Ey）
        4. 是否需要考虑地震作用效应折减
        5. 不同抗震等级下的组合规则是否需要差异化
        """
        combination_id = 200  # 从 200 开始编号
        combinations = []

        if not (dead_load_ids and seismic_load_ids):
            return {
                "combinations": [],
                "count": 0
            }

        # 水平地震 + 竖向地震
        for dead_id in dead_load_ids:
            for seismic_id in seismic_load_ids:
                # 水平 + 竖向
                combo = {
                    "id": f"COMB_{combination_id}",
                    "type": "seismic",
                    "description": f"恒载 {dead_id} + 地震 {seismic_id} (水平+竖向)",
                    "factors": {dead_id: 1.0, f"{seismic_id}_h": 1.0, f"{seismic_id}_v": 0.5},
                    "code_reference": "GB50011-2010 5.4.1"
                }
                combinations.append(combo)
                combination_id += 1

        self.combinations = combinations
        return {
            "combinations": combinations,
            "count": len(combinations)
        }

    def create_combination(
        self,
        combo_id: str,
        combination_type: str,
        factors: Dict[str, float],
        description: str = "",
        code_reference: str = ""
    ) -> Dict[str, Any]:
        """
        创建荷载组合

        Args:
            combo_id: 组合ID
            combination_type: 组合类型 (uls, sls, seismic, accidental)
            factors: 荷载系数字典
            description: 组合描述
            code_reference: 规范条文号

        Returns:
            荷载组合字典
        """
        combo = {
            "id": combo_id,
            "type": combination_type,
            "factors": factors,
            "description": description,
            "code_reference": code_reference,
            "extra": {}
        }

        self.combinations.append(combo)
        return combo

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "combinations": self.combinations,
            "count": len(self.combinations)
        }
