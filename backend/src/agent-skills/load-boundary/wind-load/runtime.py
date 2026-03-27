from __future__ import annotations

from typing import Any, Dict, List

from structure_protocol.structure_model_v2 import StructureModelV2
import logging

logger = logging.getLogger(__name__)


class WindLoadGenerator:
    """风载生成器 / Wind Load Generator"""

    # 地面粗糙度类别
    TERRAIN_ROUGHNESS = {
        'A': {'alpha': 0.12, 'gradient_height': 300},
        'B': {'alpha': 0.16, 'gradient_height': 350},
        'C': {'alpha': 0.22, 'gradient_height': 450},
        'D': {'alpha': 0.30, 'gradient_height': 550},
    }

    def __init__(self, model: StructureModelV2):
        """
        初始化风载生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

    def generate_wind_loads(
        self,
        basic_pressure: float = 0.55,  # kN/m²
        terrain_roughness: str = 'B',
        shape_factor: float = 1.3,
        wind_direction: str = 'x',
        case_id: str = "LC_W",
        case_name: str = "风载工况",
        description: str = "风荷载"
    ) -> Dict[str, Any]:
        """
        生成风荷载工况

        Args:
            basic_pressure: 基本风压 (kN/m²)
            terrain_roughness: 地面粗糙度类别 (A, B, C, D)
            shape_factor: 风荷载体型系数
            wind_direction: 风向 (x, y, -x, -y)
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述

        Returns:
            荷载工况和荷载动作
        """
        logger.info(f"Generating wind loads: basic_pressure={basic_pressure}, direction={wind_direction}")

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "wind",  # 对齐 V2 Schema LoadCaseV2.type
            "description": description,
            "loads": []
        }

        # 遍历所有构件，计算风荷载
        elements_by_story = self._group_elements_by_story()

        for story_id, elements in elements_by_story.items():
            # 计算楼层平均标高
            story_height = self._get_story_height(story_id)

            # 计算风压高度变化系数
            height_factor = self._calculate_height_factor(
                story_height=story_height,
                terrain_roughness=terrain_roughness
            )

            # 计算设计风压
            design_pressure = basic_pressure * height_factor * shape_factor

            logger.info(f"Story {story_id}: height={story_height}m, μz={height_factor:.3f}, w0={design_pressure:.3f} kN/m²")

            # 为每个构件创建风荷载
            for elem in elements:
                load_action = self._create_wind_load_action(
                    element=elem,
                    wind_pressure=design_pressure,
                    wind_direction=wind_direction,
                    case_id=case_id
                )
                if load_action:
                    load_case["loads"].append(load_action)
                    self.load_actions.append(load_action)

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} wind load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def add_custom_wind_load(
        self,
        element_id: str,
        element_type: str,
        load_value: float,
        wind_direction: str = 'x',
        case_id: str = "LC_W"
    ) -> Dict[str, Any]:
        """
        添加自定义风载

        Args:
            element_id: 单元ID
            element_type: 单元类型
            load_value: 荷载值 (kN/m 或 kN)
            wind_direction: 风向
            case_id: 荷载工况ID

        Returns:
            荷载动作
        """
        # 确定荷载方向向量
        if wind_direction == 'x':
            load_direction = {"x": 1.0, "y": 0.0, "z": 0.0}
        elif wind_direction == '-x':
            load_direction = {"x": -1.0, "y": 0.0, "z": 0.0}
        elif wind_direction == 'y':
            load_direction = {"x": 0.0, "y": 1.0, "z": 0.0}
        elif wind_direction == '-y':
            load_direction = {"x": 0.0, "y": -1.0, "z": 0.0}
        else:
            load_direction = {"x": 0.0, "y": 0.0, "z": 0.0}

        load_action = {
            "actionId": f"LA_{element_id}_W",
            "caseId": case_id,
            "elementType": element_type,
            "elementId": element_id,
            "loadType": "distributed_load",
            "loadValue": load_value,
            "loadDirection": load_direction
        }

        self.load_actions.append(load_action)

        if case_id not in self.load_cases:
            self.load_cases[case_id] = {
                "id": case_id,
                "type": "wind",
                "description": "风荷载",
                "loads": []
            }

        self.load_cases[case_id]["loads"].append(load_action)

        logger.info(f"Added wind load: {load_value} on element {element_id}, direction={wind_direction}")
        return load_action

    def get_load_cases(self) -> Dict[str, Any]:
        """获取所有荷载工况"""
        return self.load_cases

    def get_load_actions(self) -> list:
        """获取所有荷载动作"""
        return self.load_actions

    def _group_elements_by_story(self) -> Dict[str, list]:
        """按楼层分组构件"""
        elements_by_story = {}
        for elem in self.model.elements:
            story_id = elem.story or "undefined"
            if story_id not in elements_by_story:
                elements_by_story[story_id] = []
            elements_by_story[story_id].append(elem)
        return elements_by_story

    def _get_story_height(self, story_id: str) -> float:
        """
        获取楼层标高

        Args:
            story_id: 楼层ID

        Returns:
            楼层标高 (m)
        """
        for story in self.model.stories:
            if story.id == story_id:
                return story.elevation if story.elevation else 0.0

        # 如果没有找到，从节点计算
        node_z_values = []
        for node in self.model.nodes:
            if node.story == story_id:
                node_z_values.append(node.z)

        if node_z_values:
            return sum(node_z_values) / len(node_z_values)

        return 0.0

    def _calculate_height_factor(
        self,
        story_height: float,
        terrain_roughness: str = 'B'
    ) -> float:
        """
        计算风压高度变化系数

        Args:
            story_height: 楼层标高 (m)
            terrain_roughness: 地面粗糙度类别

        Returns:
            风压高度变化系数 μz
        """
        if terrain_roughness not in self.TERRAIN_ROUGHNESS:
            logger.warning(f"Unknown terrain roughness '{terrain_roughness}', using 'B'")
            terrain_roughness = 'B'

        alpha = self.TERRAIN_ROUGHNESS[terrain_roughness]['alpha']
        gradient_height = self.TERRAIN_ROUGHNESS[terrain_roughness]['gradient_height']

        if story_height < 10:
            # 对于高度小于 10m 的建筑，取 10m 处的值
            story_height = 10

        # 计算高度变化系数
        mu_z = 0.616 * (story_height / 10) ** alpha

        return min(mu_z, 2.0)  # 不超过 2.0

    def _create_wind_load_action(
        self,
        element: Any,
        wind_pressure: float,
        wind_direction: str,
        case_id: str
    ) -> Dict[str, Any]:
        """
        创建风荷载动作

        Args:
            element: 单元
            wind_pressure: 风压 (kN/m²)
            wind_direction: 风向
            case_id: 荷载工况ID

        Returns:
            荷载动作字典
        """
        # 确定荷载方向向量
        if wind_direction == 'x':
            load_direction = {"x": 1.0, "y": 0.0, "z": 0.0}
        elif wind_direction == '-x':
            load_direction = {"x": -1.0, "y": 0.0, "z": 0.0}
        elif wind_direction == 'y':
            load_direction = {"x": 0.0, "y": 1.0, "z": 0.0}
        elif wind_direction == '-y':
            load_direction = {"x": 0.0, "y": -1.0, "z": 0.0}
        else:
            load_direction = {"x": 0.0, "y": 0.0, "z": 0.0}

        # 简化处理: 将面风压转换为线荷载
        linear_load = wind_pressure  # kN/m

        load_action = {
            "actionId": f"LA_{element.id}_W",
            "caseId": case_id,
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "distributed_load",
            "loadValue": linear_load,
            "loadDirection": load_direction,
            "description": f"风载: {wind_pressure:.3f} kN/m, 方向: {wind_direction}"
        }

        return load_action


def generate_wind_loads(model: StructureModelV2, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成风荷载的主函数

    Args:
        model: V2 结构模型
        parameters: 参数字典
            - basic_pressure: 基本风压 (kN/m², 默认 0.55)
            - terrain_roughness: 地面粗糙度类别 (默认 B)
            - shape_factor: 风荷载体型系数 (默认 1.3)
            - wind_direction: 风向 (默认 x)
            - case_id: 荷载工况ID (可选)
            - custom_loads: 自定义荷载列表 (可选)

    Returns:
        生成结果
    """
    generator = WindLoadGenerator(model)

    # 参数解析
    case_id = parameters.get("case_id", "LC_W")
    case_name = parameters.get("case_name", "风载工况")
    description = parameters.get("description", "风荷载")
    basic_pressure = parameters.get("basic_pressure", 0.55)
    terrain_roughness = parameters.get("terrain_roughness", "B")
    shape_factor = parameters.get("shape_factor", 1.3)
    wind_direction = parameters.get("wind_direction", "x")

    # 生成风荷载
    result = generator.generate_wind_loads(
        basic_pressure=basic_pressure,
        terrain_roughness=terrain_roughness,
        shape_factor=shape_factor,
        wind_direction=wind_direction,
        case_id=case_id,
        case_name=case_name,
        description=description
    )

    # 添加自定义风载
    custom_loads = parameters.get("custom_loads", [])
    for load_def in custom_loads:
        generator.add_custom_wind_load(
            element_id=load_def["element_id"],
            element_type=load_def.get("element_type", "beam"),
            load_value=load_def["load_value"],
            wind_direction=load_def.get("wind_direction", "x"),
            case_id=case_id
        )

    return {
        "status": "success",
        "load_cases": generator.get_load_cases(),
        "load_actions": generator.get_load_actions(),
        "summary": {
            "case_count": len(generator.get_load_cases()),
            "action_count": len(generator.get_load_actions()),
            "case_id": case_id,
            "basic_pressure": basic_pressure,
            "wind_direction": wind_direction
        }
    }
