from __future__ import annotations

from typing import Any, Dict, List

from structure_protocol.structure_model_v2 import StructureModelV2
import logging

logger = logging.getLogger(__name__)


class TemperatureLoadGenerator:
    """温度荷载生成器 / Temperature Load Generator"""

    # 材料热膨胀系数 (1/°C)
    THERMAL_EXPANSION_COEFFICIENTS = {
        'steel': 1.2e-5,       # 钢材
        'concrete': 1.0e-5,     # 混凝土
        'aluminum': 2.3e-5,     # 铝材
        'glass': 8.5e-6,        # 玻璃
    }

    def __init__(self, model: StructureModelV2):
        """
        初始化温度荷载生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

    def generate_thermal_loads(
        self,
        case_id: str = "LC_TEMPERATURE",
        case_name: str = "温度荷载工况",
        description: str = "温度变化引起的结构变形",
        temperature_change: float = 30.0,
        reference_temperature: float = 20.0
    ) -> Dict[str, Any]:
        """
        生成温度荷载工况

        Args:
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述
            temperature_change: 温度变化量 (°C)
            reference_temperature: 参考温度 (°C)

        Returns:
            荷载工况和荷载动作
        """
        logger.info(f"Generating temperature loads for case: {case_id}, ΔT={temperature_change}°C")

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "temperature",  # 对齐 V2 Schema LoadCaseV2.type
            "description": f"参考温度: {reference_temperature}°C, 温度变化: {temperature_change}°C",
            "loads": []
        }

        # 遍历所有构件，计算温度荷载
        for elem in self.model.elements:
            try:
                # 获取构件材料
                material = self._get_material(elem.material)
                if not material:
                    logger.warning(f"Material '{elem.material}' not found for element '{elem.id}'")
                    continue

                # 获取材料热膨胀系数
                alpha = self._get_thermal_expansion_coefficient(material)

                # 计算温度荷载（简化：热应变引起的等效力）
                load_action = self._calculate_thermal_load(
                    element=elem,
                    material=material,
                    alpha=alpha,
                    temperature_change=temperature_change
                )

                if load_action:
                    load_case["loads"].append(load_action)
                    self.load_actions.append(load_action)

            except Exception as error:
                logger.error(f"Failed to calculate temperature load for element '{elem.id}': {error}")
                continue

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} temperature load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def _get_material(self, material_id: str) -> Dict[str, Any]:
        """获取材料信息"""
        for material in self.model.materials:
            if material.id == material_id:
                return material
        return None

    def _get_thermal_expansion_coefficient(self, material: Dict[str, Any]) -> float:
        """获取热膨胀系数"""
        # 优先使用材料的 grade 字段
        if material.grade and material.grade in self.THERMAL_EXPANSION_COEFFICIENTS:
            return self.THERMAL_EXPANSION_COEFFICIENTS[material.grade]
        # 使用 category
        if material.category and material.category in self.THERMAL_EXPANSION_COEFFICIENTS:
            return self.THERMAL_EXPANSION_COEFFICIENTS[material.category]
        # 默认使用钢材的系数
        return self.THERMAL_EXPANSION_COEFFICIENTS['steel']

    def _calculate_thermal_load(
        self,
        element: Any,
        material: Dict[str, Any],
        alpha: float,
        temperature_change: float
    ) -> Dict[str, Any]:
        """
        计算温度荷载

        Args:
            element: 构件对象
            material: 材料信息
            alpha: 热膨胀系数
            temperature_change: 温度变化量

        Returns:
            荷载动作字典
        """
        # 简化计算：热应变 = α * ΔT
        thermal_strain = alpha * temperature_change

        return {
            "id": f"TEMP_{element.id}",
            "case_id": f"LC_TEMPERATURE",
            "element_type": element.type,
            "element_id": element.id,
            "load_type": "axial_force",  # 温度荷载主要表现为轴向力
            "load_value": thermal_strain,
            "load_direction": {"x": 1.0, "y": 0.0, "z": 0.0},
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},  # 简化，实际应根据构件位置
            "extra": {
                "thermal_strain": thermal_strain,
                "alpha": alpha,
                "temperature_change": temperature_change
            }
        }
