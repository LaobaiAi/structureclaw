from __future__ import annotations

from typing import Any, Dict

from structure_protocol.structure_model_v2 import StructureModelV2
import logging

logger = logging.getLogger(__name__)


class LiveLoadGenerator:
    """活载生成器 / Live Load Generator"""

    # 规范标准活载 (kN/m²)
    STANDARD_LIVE_LOADS = {
        'residential': 2.0,      # 住宅
        'office': 2.0,          # 办公
        'classroom': 2.5,       # 教室
        'corridor': 2.5,        # 走廊
        'stair': 3.5,           # 楼梯
        'roof': 0.5,            # 上人屋面
        'roof_uninhabited': 0.5,# 不上人屋面
        'equipment': 5.0,       # 设备房
        'storage': 5.0,         # 仓库
    }

    def __init__(self, model: StructureModelV2):
        """
        初始化活载生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

    def generate_floor_live_loads(
        self,
        floor_load_type: str = "office",
        case_id: str = "LC_LL",
        case_name: str = "活载工况",
        description: str = "楼面活载"
    ) -> Dict[str, Any]:
        """
        生成楼面活载工况

        Args:
            floor_load_type: 楼面荷载类型 (residential, office, classroom, etc.)
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述

        Returns:
            荷载工况和荷载动作
        """
        logger.info(f"Generating floor live loads for type: {floor_load_type}")

        # 获取标准活载值
        load_value = self.STANDARD_LIVE_LOADS.get(floor_load_type, 2.0)

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "live",  # 对齐 V2 Schema LoadCaseV2.type
            "description": description,
            "loads": []
        }

        # 遍历所有构件，按楼层分配活载
        elements_by_story = self._group_elements_by_story()

        for story_id, elements in elements_by_story.items():
            for elem in elements:
                if elem.type in ["beam", "slab"]:
                    load_action = self._create_floor_load_action(
                        element=elem,
                        load_value=load_value,
                        case_id=case_id,
                        floor_type=floor_load_type
                    )
                    if load_action:
                        load_case["loads"].append(load_action)
                        self.load_actions.append(load_action)

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} live load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def add_custom_live_load(
        self,
        element_id: str,
        element_type: str,
        load_value: float,
        load_direction: Dict[str, float] = None,
        case_id: str = "LC_LL"
    ) -> Dict[str, Any]:
        """
        添加自定义活载

        Args:
            element_id: 单元ID
            element_type: 单元类型
            load_value: 荷载值 (kN/m 或 kN)
            load_direction: 荷载方向向量
            case_id: 荷载工况ID

        Returns:
            荷载动作
        """
        if load_direction is None:
            load_direction = {"x": 0.0, "y": -1.0, "z": 0.0}

        load_action = {
            "actionId": f"LA_{element_id}_LL",
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
                "type": "live",
                "description": "活载工况",
                "loads": []
            }

        self.load_cases[case_id]["loads"].append(load_action)

        logger.info(f"Added live load: {load_value} on element {element_id}")
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

    def _create_floor_load_action(
        self,
        element: Any,
        load_value: float,
        case_id: str,
        floor_type: str
    ) -> Dict[str, Any]:
        """
        创建楼面荷载动作

        Args:
            element: 单元
            load_value: 荷载值 (kN/m²)
            case_id: 荷载工况ID
            floor_type: 楼面类型

        Returns:
            荷载动作字典
        """
        # 获取截面面积
        section = self._get_section(element.section)
        if not section:
            logger.warning(f"Section '{element.section}' not found for element '{element.id}'")
            return None

        # 简化处理: 将面荷载转换为线荷载
        # 实际应根据荷载传递路径计算
        linear_load = load_value  # kN/m

        load_action = {
            "actionId": f"LA_{element.id}_LL",
            "caseId": case_id,
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "distributed_load",
            "loadValue": linear_load,
            "loadDirection": {"x": 0.0, "y": -1.0, "z": 0.0},
            "description": f"{floor_type} 活载: {linear_load} kN/m"
        }

        return load_action

    def _get_section(self, section_id: str) -> Any:
        """获取截面"""
        for sec in self.model.sections:
            if sec.id == section_id:
                return sec
        return None


def generate_live_loads(model: StructureModelV2, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成活载的主函数

    Args:
        model: V2 结构模型
        parameters: 参数字典
            - case_id: 荷载工况ID (可选)
            - case_name: 荷载工况名称 (可选)
            - floor_load_type: 楼面荷载类型 (默认 office)
            - custom_loads: 自定义荷载列表 (可选)

    Returns:
        生成结果
    """
    generator = LiveLoadGenerator(model)

    # 参数解析
    case_id = parameters.get("case_id", "LC_LL")
    case_name = parameters.get("case_name", "活载工况")
    description = parameters.get("description", "楼面活载")
    floor_load_type = parameters.get("floor_load_type", "office")

    # 生成楼面活载
    result = generator.generate_floor_live_loads(
        floor_load_type=floor_load_type,
        case_id=case_id,
        case_name=case_name,
        description=description
    )

    # 添加自定义活载
    custom_loads = parameters.get("custom_loads", [])
    for load_def in custom_loads:
        generator.add_custom_live_load(
            element_id=load_def["element_id"],
            element_type=load_def.get("element_type", "beam"),
            load_value=load_def["load_value"],
            load_direction=load_def.get("load_direction"),
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
            "floor_type": floor_load_type
        }
    }
