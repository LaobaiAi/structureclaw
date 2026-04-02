from __future__ import annotations

from typing import Any, Dict, List, Optional

from structure_protocol.structure_model_v2 import StructureModelV2, ElementV2, MaterialV2, SectionV2
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

        # 建立索引加速查找
        self._material_map = {m.id: m for m in model.materials}
        self._section_map = {s.id: s for s in model.sections}

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

                # 计算温度荷载（基于 F = E * A * α * ΔT）
                load_action = self._calculate_thermal_load(
                    element=elem,
                    material=material,
                    alpha=alpha,
                    temperature_change=temperature_change
                )

                if load_action:
                    load_case["loads"].append(load_action)
                    self.load_actions.append(load_action)

            except (ValueError, ArithmeticError) as error:
                logger.error(f"计算构件 '{elem.id}' 的温度荷载时发生数值错误: {error}")
                continue
            except RuntimeError as error:
                logger.error(f"计算构件 '{elem.id}' 的温度荷载时发生运行时错误: {error}")
                continue

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} temperature load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def _get_material(self, material_id: str) -> Optional[MaterialV2]:
        """获取材料信息"""
        return self._material_map.get(material_id)

    def _get_section(self, section_id: str) -> Optional[SectionV2]:
        """获取截面信息"""
        return self._section_map.get(section_id)

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
        element: ElementV2,
        material: MaterialV2,
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

        Notes:
            温度效应等效轴向力: F = E * A * α * ΔT
            E: 弹性模量 (MPa = N/mm²)
            A: 截面面积 (mm²)
            F: 轴向力 (N) → 转换为 kN
        """
        # 获取截面信息
        section = self._get_section(element.section)
        if not section:
            logger.warning(f"Section '{element.section}' not found for element '{element.id}'")
            return None

        # 计算截面面积 (mm²)
        area = self._calculate_section_area(section)
        if area is None:
            logger.warning(f"Could not calculate area for section '{section.id}'")
            return None

        # 计算热应变 (无量纲)
        thermal_strain = alpha * temperature_change

        # 计算等效轴向力: F = E * A * α * ΔT (N)
        E = material.E  # MPa = N/mm²
        axial_force_n = E * area * thermal_strain

        # 转换为 kN
        axial_force_kn = axial_force_n / 1000.0

        return {
            "id": f"TEMP_{element.id}",
            "case_id": f"LC_TEMPERATURE",
            "element_type": element.type,
            "element_id": element.id,
            "load_type": "axial_force",  # 温度荷载主要表现为轴向力
            "load_value": axial_force_kn,  # 单位: kN
            "load_direction": {"x": 1.0, "y": 0.0, "z": 0.0},
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},  # 简化，实际应根据构件位置
            "extra": {
                "thermal_strain": thermal_strain,
                "alpha": alpha,
                "temperature_change": temperature_change,
                "elastic_modulus": E,  # MPa
                "section_area": area,  # mm²
                "axial_force_n": axial_force_n,  # N
                "axial_force_kn": axial_force_kn  # kN
            }
        }

    def _calculate_section_area(self, section: SectionV2) -> Optional[float]:
        """
        计算截面面积

        Args:
            section: 截面对象

        Returns:
            截面面积 (mm²)，如果无法计算则返回 None
        """
        # 优先使用 properties 中的 area 字段
        if "area" in section.properties and section.properties["area"]:
            return float(section.properties["area"])

        # 根据截面类型和尺寸计算
        section_type = section.type.lower()

        if section_type == "rectangular":
            if section.width and section.height:
                return section.width * section.height

        elif section_type == "circular":
            if section.diameter:
                return 3.14159 * (section.diameter / 2) ** 2

        elif section_type == "tube":
            # 空心管/箱型截面
            if section.width and section.height and section.thickness:
                # 简化计算: 外部面积 - 内部面积 (假设均匀壁厚)
                outer_area = section.width * section.height
                inner_width = section.width - 2 * section.thickness
                inner_height = section.height - 2 * section.thickness
                if inner_width > 0 and inner_height > 0:
                    return outer_area - (inner_width * inner_height)

        # 尝试从 properties 中提取常用截面参数
        props = section.properties
        if "b" in props and "h" in props:  # 矩形截面
            return float(props["b"] * props["h"])
        if "d" in props:  # 圆形截面直径
            return 3.14159 * (float(props["d"]) / 2) ** 2
        if "area" in props:  # 显式面积字段
            return float(props["area"])

        logger.warning(f"Cannot calculate area for section type '{section_type}' with properties: {props}")
        return None
