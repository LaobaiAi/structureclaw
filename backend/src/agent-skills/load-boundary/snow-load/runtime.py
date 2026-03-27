from __future__ import annotations

from typing import Any, Dict, List

from structure_protocol.structure_model_v2 import StructureModelV2
import logging

logger = logging.getLogger(__name__)


class SnowLoadGenerator:
    """雪荷载生成器 / Snow Load Generator"""

    # 雪荷载基本值 (kN/m²) - 参考 GB50009-2012
    SNOW_LOAD_BASE_VALUES = {
        "region_1": 0.3,   # 地区I
        "region_2": 0.5,   # 地区II
        "region_3": 0.7,   # 地区III
    }

    # 屋面类型修正系数
    ROOF_TYPE_FACTORS = {
        "flat": 1.0,          # 平屋面
        "sloped_25": 0.8,     # 坡度 < 25°
        "sloped_25_50": 0.6,  # 坡度 25°-50°
        "slopped_50": 0.0,    # 坡度 > 50°
    }

    def __init__(self, model: StructureModelV2):
        """
        初始化雪荷载生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

    def generate_snow_loads(
        self,
        case_id: str = "LC_SNOW",
        case_name: str = "雪荷载工况",
        description: str = "屋面积雪荷载",
        region: str = "region_2",
        roof_type: str = "flat"
    ) -> Dict[str, Any]:
        """
        生成雪荷载工况

        Args:
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述
            region: 地区类型
            roof_type: 屋面类型

        Returns:
            荷载工况和荷载动作
        """
        logger.info(f"Generating snow loads for case: {case_id}, region={region}, roof_type={roof_type}")

        # 获取雪荷载基本值和修正系数
        base_snow_load = self.SNOW_LOAD_BASE_VALUES.get(region, 0.5)
        roof_factor = self.ROOF_TYPE_FACTORS.get(roof_type, 1.0)

        # 计算设计雪荷载
        design_snow_load = base_snow_load * roof_factor

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "snow",  # 对齐 V2 Schema LoadCaseV2.type
            "description": f"基本雪载: {base_snow_load} kN/m², 修正系数: {roof_factor}",
            "loads": []
        }

        # 遍历所有构件，对楼板施加雪荷载
        for elem in self.model.elements:
            try:
                # 只对楼板施加雪荷载
                if elem.type == "slab":
                    load_action = self._calculate_snow_load(
                        element=elem,
                        snow_load=design_snow_load
                    )

                    if load_action:
                        load_case["loads"].append(load_action)
                        self.load_actions.append(load_action)

            except Exception as error:
                logger.error(f"Failed to calculate snow load for element '{elem.id}': {error}")
                continue

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} snow load actions, design_snow_load={design_snow_load} kN/m²")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def _calculate_snow_load(
        self,
        element: Any,
        snow_load: float
    ) -> Dict[str, Any]:
        """
        计算雪荷载

        Args:
            element: 构件对象
            snow_load: 设计雪荷载 (kN/m²)

        Returns:
            荷载动作字典
        """
        # 简化：均布荷载作用于楼板
        return {
            "id": f"SNOW_{element.id}",
            "case_id": "LC_SNOW",
            "element_type": element.type,
            "element_id": element.id,
            "load_type": "distributed_load",  # 均布荷载
            "load_value": snow_load,
            "load_direction": {"x": 0.0, "y": 0.0, "z": -1.0},  # 向下
            "extra": {
                "snow_load": snow_load,
                "distribution_type": "uniform"
            }
        }
