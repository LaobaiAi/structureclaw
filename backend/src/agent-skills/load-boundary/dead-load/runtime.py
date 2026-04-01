from __future__ import annotations

from typing import Any, Dict, Optional

from structure_protocol.structure_model_v2 import StructureModelV2
import logging
from .constants import (
    MATERIAL_DENSITIES,
    LINEAR_LOAD_CONVERSION,
    LoadDirection,
    LoadType,
    LoadCaseID,
    ElementType,
    get_material_density,
    validate_load_value,
    validate_element_type
)

logger = logging.getLogger(__name__)


class DeadLoadGenerator:
    """恒载生成器 / Dead Load Generator"""

    def __init__(self, model: StructureModelV2):
        """
        初始化恒载生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

    def generate_self_weight_loads(
        self,
        case_id: str = "LC_DE",
        case_name: str = "恒载工况",
        description: str = "结构自重及永久荷载"
    ) -> Dict[str, Any]:
        """
        生成结构自重荷载工况

        Args:
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述

        Returns:
            荷载工况和荷载动作
        """
        logger.info(f"Generating self-weight loads for case: {case_id}")

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "dead",  # 对齐 V2 Schema LoadCaseV2.type
            "description": description,
            "loads": []
        }

        # 遍历所有构件，计算自重
        for elem in self.model.elements:
            try:
                # 获取构件材料
                material = self._get_material(elem.material)
                if not material:
                    logger.warning(f"Material '{elem.material}' not found for element '{elem.id}'")
                    continue

                # 获取构件截面
                section = self._get_section(elem.section)
                if not section:
                    logger.warning(f"Section '{elem.section}' not found for element '{elem.id}'")
                    continue

                # 计算自重荷载
                load_action = self._calculate_self_weight(
                    element=elem,
                    material=material,
                    section=section
                )

                if load_action:
                    load_case["loads"].append(load_action)
                    self.load_actions.append(load_action)

            except Exception as error:
                logger.error(f"Failed to calculate self-weight for element '{elem.id}': {error}")
                continue

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} self-weight load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def add_uniform_dead_load(
        self,
        element_id: str,
        element_type: str,
        load_value: float,
        load_direction: Optional[Dict[str, float]] = None,
        case_id: str = "LC_DE",
        case_name: str = "恒载工况"
    ) -> Dict[str, Any]:
        """
        添加均布恒载

        Args:
            element_id: 单元ID
            element_type: 单元类型 (beam, column, etc.)
            load_value: 荷载值 (kN/m)
            load_direction: 荷载方向向量
            case_id: 荷载工况ID
            case_name: 荷载工况名称

        Returns:
            荷载动作

        Raises:
            ValueError: 当输入参数无效时

        Examples:
            >>> generator.add_uniform_dead_load(
            ...     element_id="B1",
            ...     element_type="beam",
            ...     load_value=10.5
            ... )
        """
        # 参数验证
        self._validate_parameters(
            element_id=element_id,
            element_type=element_type,
            load_value=load_value,
            load_direction=load_direction
        )

        # 设置默认荷载方向（重力方向）
        if load_direction is None:
            load_direction = LoadDirection.GRAVITY

        load_action = {
            "actionId": f"LA_{element_id}_DE",
            "caseId": case_id,
            "elementType": element_type,
            "elementId": element_id,
            "loadType": "distributed_load",
            "loadValue": load_value,
            "loadDirection": load_direction
        }

        self.load_actions.append(load_action)

        # 确保荷载工况存在
        if case_id not in self.load_cases:
            self.load_cases[case_id] = {
                "id": case_id,
                "type": "dead",
                "description": case_name,
                "loads": []
            }

        self.load_cases[case_id]["loads"].append(load_action)

        logger.info(f"Added dead load: {load_value} kN/m on element {element_id}")
        return load_action

    def add_point_dead_load(
        self,
        element_id: str,
        element_type: str,
        load_value: float,
        position: Dict[str, float],
        load_direction: Optional[Dict[str, float]] = None,
        case_id: str = "LC_DE"
    ) -> Dict[str, Any]:
        """
        添加集中恒载

        Args:
            element_id: 单元ID
            element_type: 单元类型
            load_value: 荷载值 (kN)
            position: 作用位置
            load_direction: 荷载方向向量
            case_id: 荷载工况ID

        Returns:
            荷载动作

        Raises:
            ValueError: 当输入参数无效时
        """
        # 参数验证
        self._validate_parameters(
            element_id=element_id,
            element_type=element_type,
            load_value=load_value,
            load_direction=load_direction
        )

        # 设置默认荷载方向（重力方向）
        if load_direction is None:
            load_direction = LoadDirection.GRAVITY

        load_action = {
            "actionId": f"LA_{element_id}_DE_POINT",
            "caseId": case_id,
            "elementType": element_type,
            "elementId": element_id,
            "loadType": "point_force",
            "loadValue": load_value,
            "loadDirection": load_direction,
            "position": position
        }

        self.load_actions.append(load_action)
        self.load_cases[case_id]["loads"].append(load_action)

        logger.info(f"Added point dead load: {load_value} kN on element {element_id} at {position}")
        return load_action

    def get_load_cases(self) -> Dict[str, Any]:
        """获取所有荷载工况"""
        return self.load_cases

    def get_load_actions(self) -> list:
        """获取所有荷载动作"""
        return self.load_actions

    def _get_material(self, material_id: str) -> Any:
        """获取材料"""
        for mat in self.model.materials:
            if mat.id == material_id:
                return mat
        return None

    def _get_section(self, section_id: str) -> Any:
        """获取截面"""
        for sec in self.model.sections:
            if sec.id == section_id:
                return sec
        return None

    def _calculate_self_weight(
        self,
        element: Any,
        material: Any,
        section: Any
    ) -> Dict[str, Any]:
        """
        计算构件自重

        Args:
            element: 单元
            material: 材料
            section: 截面

        Returns:
            荷载动作字典
        """
        # 获取材料密度
        density = self.MATERIAL_DENSITIES.get(material.category, 2500)
        if hasattr(material, 'rho') and material.rho:
            density = material.rho

        # 计算截面面积 (简化处理，实际应根据截面类型计算)
        area = self._calculate_section_area(section)

        if area is None or area <= 0:
            logger.warning(f"Cannot calculate area for section '{section.id}'")
            return None

        # 计算线荷载 (kN/m)
        # 线荷载 = 密度 * g * 截面积 * 转换系数 (kg/m³ * m/s² * mm² = kN/m)
        linear_load = density * LINEAR_LOAD_CONVERSION * area  # 使用常量

        # 创建荷载动作
        load_action = {
            "actionId": f"LA_{element.id}_SW",
            "caseId": "LC_DE",
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "distributed_load",
            "loadValue": linear_load,
            "loadDirection": {"x": 0.0, "y": -1.0, "z": 0.0},  # 重力方向向下
            "description": f"自重: {linear_load:.4f} kN/m"
        }

        return load_action

    def _calculate_section_area(self, section: Any) -> float:
        """
        计算截面面积 (简化版)

        Args:
            section: 截面

        Returns:
            截面面积 (mm²)，如果无法计算则返回 None

        Examples:
            >>> # 矩形截面
            >>> section = type('Section', (), {
            ...     'type': 'rectangular',
            ...     'width': 300,
            ...     'height': 500,
            ...     'properties': {}
            ... })()
            >>> generator._calculate_section_area(section)
            150000

            >>> # 圆形截面
            >>> section = type('Section', (), {
            ...     'type': 'circular',
            ...     'diameter': 500,
            ...     'properties': {}
            ... })()
            >>> import math
            >>> generator._calculate_section_area(section) == math.pi * 250 ** 2
            True
        """
        import math

        if section.type == "rectangular":
            if section.width and section.height:
                return float(section.width * section.height)
        elif section.type == "circular":
            if section.diameter:
                return float(math.pi * (section.diameter / 2) ** 2)
        elif section.type == "box":
            if section.width and section.height and section.thickness:
                # 箱形截面面积 = 2*(width + height)*thickness
                return float(2 * (section.width + section.height) * section.thickness)

        # 尝试从 properties 字段获取
        if hasattr(section, 'properties') and "area" in section.properties:
            try:
                return float(section.properties["area"])
            except (ValueError, TypeError):
                pass

        return None

    def _validate_parameters(
        self,
        element_id: str,
        element_type: str,
        load_value: float,
        load_direction: Optional[Dict[str, float]] = None
    ) -> None:
        """
        验证输入参数

        Args:
            element_id: 单元ID
            element_type: 单元类型
            load_value: 荷载值
            load_direction: 荷载方向向量

        Raises:
            ValueError: 当参数无效时
            TypeError: 当参数类型错误时
        """
        # 验证 element_id
        if not element_id or not isinstance(element_id, str):
            raise TypeError(f"单元ID必须是非空字符串，得到: {type(element_id)}")

        # 验证 element_type
        validate_element_type(element_type)

        # 验证 load_value
        validate_load_value(load_value, LoadType.DISTRIBUTED_LOAD)

        # 验证 load_direction
        if load_direction is not None:
            if not isinstance(load_direction, dict):
                raise TypeError(f"荷载方向必须是字典类型，得到: {type(load_direction)}")

            required_keys = ['x', 'y', 'z']
            if not all(k in load_direction for k in required_keys):
                raise ValueError(
                    f"荷载方向必须包含 {required_keys} 键，得到: {list(load_direction.keys())}"
                )

            # 验证方向向量是数字
            for key, value in load_direction.items():
                if not isinstance(value, (int, float)):
                    raise TypeError(
                        f"荷载方向的 {key} 值必须是数字类型，得到: {type(value)}"
                    )


def generate_dead_loads(model: StructureModelV2, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成恒载的主函数

    Args:
        model: V2 结构模型
        parameters: 参数字典
            - case_id: 荷载工况ID (可选)
            - case_name: 荷载工况名称 (可选)
            - include_self_weight: 是否包含自重 (默认 True)
            - uniform_loads: 均布荷载列表 (可选)

    Returns:
        生成结果
    """
    generator = DeadLoadGenerator(model)

    # 参数解析
    case_id = parameters.get("case_id", "LC_DE")
    case_name = parameters.get("case_name", "恒载工况")
    description = parameters.get("description", "结构自重及永久荷载")
    include_self_weight = parameters.get("include_self_weight", True)

    # 生成自重荷载
    if include_self_weight:
        result = generator.generate_self_weight_loads(
            case_id=case_id,
            case_name=case_name,
            description=description
        )
    else:
        # 创建空的荷载工况
        generator.load_cases[case_id] = {
            "id": case_id,
            "type": "dead",
            "description": description,
            "loads": []
        }
        result = {
            "load_case": generator.load_cases[case_id],
            "load_actions": []
        }

    # 添加额外的均布荷载
    uniform_loads = parameters.get("uniform_loads", [])
    for load_def in uniform_loads:
        generator.add_uniform_dead_load(
            element_id=load_def["element_id"],
            element_type=load_def.get("element_type", "beam"),
            load_value=load_def["load_value"],
            load_direction=load_def.get("load_direction"),
            case_id=case_id,
            case_name=case_name
        )

    return {
        "status": "success",
        "load_cases": generator.get_load_cases(),
        "load_actions": generator.get_load_actions(),
        "summary": {
            "case_count": len(generator.get_load_cases()),
            "action_count": len(generator.get_load_actions()),
            "case_id": case_id
        }
    }
