from __future__ import annotations

from typing import Any, Dict, List, Optional

from structure_protocol.structure_model_v2 import StructureModelV2, ElementV2, MaterialV2, SectionV2
import logging

logger = logging.getLogger(__name__)


class TemperatureLoadGenerator:
    THERMAL_EXPANSION_COEFFICIENTS = {
        'steel': 1.2e-5,
        'concrete': 1.0e-5,
        'aluminum': 2.3e-5,
        'glass': 8.5e-6,
    }

    def __init__(self, model: StructureModelV2):
        self.model = model
        self.load_cases = {}
        self.load_actions = []
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
        logger.info(f"Temperature loads: {case_id}, ΔT={temperature_change}°C")

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
                material = self._get_material(elem.material)
                if not material:
                    continue

                alpha = self._get_thermal_expansion_coefficient(material)

                load_action = self._calculate_thermal_load(
                    element=elem,
                    material=material,
                    alpha=alpha,
                    temperature_change=temperature_change,
                    case_id=case_id
                )

                if load_action:
                    load_case["loads"].append(load_action)
                    self.load_actions.append(load_action)

            except (ValueError, ArithmeticError) as error:
                logger.debug(f"Element {elem.id}: {error}")
                continue
            except RuntimeError as error:
                logger.debug(f"Element {elem.id}: {error}")
                continue

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def _get_material(self, material_id: str) -> Optional[MaterialV2]:
        return self._material_map.get(material_id)

    def _get_section(self, section_id: str) -> Optional[SectionV2]:
        return self._section_map.get(section_id)

    def _get_thermal_expansion_coefficient(self, material: Dict[str, Any]) -> float:
        if material.grade and material.grade in self.THERMAL_EXPANSION_COEFFICIENTS:
            return self.THERMAL_EXPANSION_COEFFICIENTS[material.grade]
        if material.category and material.category in self.THERMAL_EXPANSION_COEFFICIENTS:
            return self.THERMAL_EXPANSION_COEFFICIENTS[material.category]
        return self.THERMAL_EXPANSION_COEFFICIENTS['steel']

    def _calculate_thermal_load(
        self,
        element: ElementV2,
        material: MaterialV2,
        alpha: float,
        temperature_change: float,
        case_id: str = "LC_TEMPERATURE"
    ) -> Dict[str, Any]:
        section = self._get_section(element.section)
        if not section:
            return None

        area = self._calculate_section_area(section)
        if area is None:
            return None

        thermal_strain = alpha * temperature_change
        E = material.E
        axial_force_n = E * area * thermal_strain
        axial_force_kn = axial_force_n / 1000.0

        # 计算构件轴向方向向量
        from geometry_helper import GeometryHelper
        load_direction = GeometryHelper.calculate_element_direction_vector(element, self.model)
        if load_direction is None:
            # 如果无法计算方向，默认使用X方向
            load_direction = {"x": 1.0, "y": 0.0, "z": 0.0}

        return {
            "id": f"TEMP_{element.id}",
            "caseId": case_id,
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "axial_force",
            "loadValue": axial_force_kn,
            "loadDirection": load_direction,
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "extra": {
                "thermal_strain": thermal_strain,
                "alpha": alpha,
                "temperature_change": temperature_change,
                "elastic_modulus": E,
                "section_area": area,
                "axial_force_n": axial_force_n,
                "axial_force_kn": axial_force_kn
            }
        }

    def _calculate_section_area(self, section: SectionV2) -> Optional[float]:
        if "area" in section.properties and section.properties["area"]:
            return float(section.properties["area"])

        section_type = section.type.lower()

        if section_type == "rectangular":
            if section.width and section.height:
                return section.width * section.height

        elif section_type == "circular":
            if section.diameter:
                return 3.14159 * (section.diameter / 2) ** 2

        elif section_type == "tube":
            if section.width and section.height and section.thickness:
                outer_area = section.width * section.height
                inner_width = section.width - 2 * section.thickness
                inner_height = section.height - 2 * section.thickness
                if inner_width > 0 and inner_height > 0:
                    return outer_area - (inner_width * inner_height)

        props = section.properties
        if "b" in props and "h" in props:
            return float(props["b"] * props["h"])
        if "d" in props:
            return 3.14159 * (float(props["d"]) / 2) ** 2
        if "area" in props:
            return float(props["area"])

        return None
