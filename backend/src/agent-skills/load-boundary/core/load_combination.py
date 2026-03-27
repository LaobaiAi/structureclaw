"""
荷载组合模块
Load Combination Module
实现荷载组合生成功能，对齐 V2 Schema LoadCombinationV2
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
        """
        combination_id = 1
        combinations = []

        # 基础组合：1.0 恒 + 1.0 活
        if dead_load_ids and live_load_ids:
            for dead_id in dead_load_ids:
                for live_id in live_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "uls",
                        "description": f"恒载 {dead_id} + 活载 {live_id}",
                        "factors": {dead_id: 1.0, live_id: 1.0},
                        "code_reference": "GB50009-2012 3.2.4"
                    }
                    combinations.append(combo)
                    combination_id += 1

        # 风载组合：1.0 恒 + 1.4 风
        if dead_load_ids and wind_load_ids:
            for dead_id in dead_load_ids:
                for wind_id in wind_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "uls",
                        "description": f"恒载 {dead_id} + 风载 {wind_id}",
                        "factors": {dead_id: 1.0, wind_id: 1.4},
                        "code_reference": "GB50009-2012 3.2.4"
                    }
                    combinations.append(combo)
                    combination_id += 1

        # 地震组合：1.0 恒 + 1.0 震
        if dead_load_ids and seismic_load_ids:
            for dead_id in dead_load_ids:
                for seismic_id in seismic_load_ids:
                    combo = {
                        "id": f"COMB_{combination_id}",
                        "type": "uls",
                        "description": f"恒载 {dead_id} + 地震 {seismic_id}",
                        "factors": {dead_id: 1.0, seismic_id: 1.0},
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
        """
        combination_id = 100  # 从 100 开始编号
        combinations = []

        # 恒 + 活（标准组合）
        if dead_load_ids and live_load_ids:
            for dead_id in dead_load_ids:
                combo = {
                    "id": f"COMB_{combination_id}",
                    "type": "sls",
                    "description": f"恒载 {dead_id} + 活载 {live_load_ids[0] if live_load_ids else '...'}",
                    "factors": {dead_id: 1.0},
                    "code_reference": "GB50009-2012 3.2.3"
                }
                combinations.append(combo)
                combination_id += 1

        # 恒 + 风（标准组合）
        if dead_load_ids and wind_load_ids:
            for dead_id in dead_load_ids:
                combo = {
                    "id": f"COMB_{combination_id}",
                    "type": "sls",
                    "description": f"恒载 {dead_id} + 风载 {wind_load_ids[0] if wind_load_ids else '...'}",
                    "factors": {dead_id: 1.0},
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
