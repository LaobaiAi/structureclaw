from __future__ import annotations

from typing import Any, Dict, List

from structure_protocol.structure_model_v2 import StructureModelV2
import logging

logger = logging.getLogger(__name__)


class SeismicLoadGenerator:
    """地震荷载生成器 / Seismic Load Generator"""

    # 地震影响系数最大值
    ALPHA_MAX = {
        6.0: 0.04,  # 6度
        6.5: 0.05,
        7.0: 0.08,  # 7度 (0.10g)
        7.5: 0.12,  # 7.5度 (0.15g)
        8.0: 0.16,  # 8度 (0.20g)
        8.5: 0.24,  # 8.5度 (0.30g)
        9.0: 0.32,  # 9度 (0.40g)
    }

    # 场地类别对应的特征周期
    CHARACTERISTIC_PERIOD = {
        ('I', '第一组'): 0.25,
        ('I', '第二组'): 0.30,
        ('I', '第三组'): 0.35,
        ('II', '第一组'): 0.35,
        ('II', '第二组'): 0.40,
        ('II', '第三组'): 0.45,
        ('III', '第一组'): 0.45,
        ('III', '第二组'): 0.55,
        ('III', '第三组'): 0.65,
        ('IV', '第一组'): 0.65,
        ('IV', '第二组'): 0.75,
        ('IV', '第三组'): 0.90,
    }

    def __init__(self, model: StructureModelV2):
        """
        初始化地震荷载生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

    def generate_seismic_loads(
        self,
        intensity: float = 7.0,
        site_category: str = 'II',
        design_group: str = '第二组',
        damping_ratio: float = 0.05,
        seismic_direction: str = 'x',
        case_id: str = "LC_E",
        case_name: str = "地震工况",
        description: str = "地震荷载"
    ) -> Dict[str, Any]:
        """
        生成地震荷载工况

        Args:
            intensity: 设防烈度 (6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0)
            site_category: 场地类别 (I, II, III, IV)
            design_group: 设计地震分组 (第一组, 第二组, 第三组)
            damping_ratio: 阻尼比 (默认 0.05)
            seismic_direction: 地震作用方向 (x, y, z)
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述

        Returns:
            荷载工况和荷载动作
        """
        logger.info(f"Generating seismic loads: intensity={intensity}, site={site_category}, direction={seismic_direction}")

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "seismic",  # 对齐 V2 Schema LoadCaseV2.type
            "description": description,
            "loads": []
        }

        # 计算地震影响系数最大值
        alpha_max = self._get_alpha_max(intensity)

        # 获取特征周期
        characteristic_period = self._get_characteristic_period(site_category, design_group)

        # 计算地震作用 (简化版: 底部剪力法)
        seismic_force = self._calculate_base_shear(
            alpha_max=alpha_max,
            characteristic_period=characteristic_period,
            damping_ratio=damping_ratio
        )

        logger.info(f"Seismic parameters: αmax={alpha_max}, Tg={characteristic_period}s, Fek={seismic_force:.2f} kN")

        # 将地震力分配到各楼层
        elements_by_story = self._group_elements_by_story()
        story_forces = self._distribute_seismic_force(
            story_count=len(elements_by_story),
            base_shear=seismic_force
        )

        # 为每个楼层的构件创建地震荷载
        for story_idx, (story_id, elements) in enumerate(elements_by_story.items()):
            story_force = story_forces[story_idx]

            for elem in elements:
                load_action = self._create_seismic_load_action(
                    element=elem,
                    seismic_force=story_force,
                    seismic_direction=seismic_direction,
                    case_id=case_id
                )
                if load_action:
                    load_case["loads"].append(load_action)
                    self.load_actions.append(load_action)

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} seismic load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def add_custom_seismic_load(
        self,
        element_id: str,
        element_type: str,
        load_value: float,
        seismic_direction: str = 'x',
        case_id: str = "LC_E"
    ) -> Dict[str, Any]:
        """
        添加自定义地震荷载

        Args:
            element_id: 单元ID
            element_type: 单元类型
            load_value: 荷载值 (kN)
            seismic_direction: 地震作用方向
            case_id: 荷载工况ID

        Returns:
            荷载动作
        """
        # 确定荷载方向向量
        if seismic_direction == 'x':
            load_direction = {"x": 1.0, "y": 0.0, "z": 0.0}
        elif seismic_direction == '-x':
            load_direction = {"x": -1.0, "y": 0.0, "z": 0.0}
        elif seismic_direction == 'y':
            load_direction = {"x": 0.0, "y": 1.0, "z": 0.0}
        elif seismic_direction == '-y':
            load_direction = {"x": 0.0, "y": -1.0, "z": 0.0}
        elif seismic_direction == 'z':
            load_direction = {"x": 0.0, "y": 0.0, "z": 1.0}
        else:
            load_direction = {"x": 0.0, "y": 0.0, "z": 0.0}

        load_action = {
            "actionId": f"LA_{element_id}_E",
            "caseId": case_id,
            "elementType": element_type,
            "elementId": element_id,
            "loadType": "point_force",
            "loadValue": load_value,
            "loadDirection": load_direction
        }

        self.load_actions.append(load_action)

        if case_id not in self.load_cases:
            self.load_cases[case_id] = {
                "id": case_id,
                "type": "seismic",
                "description": "地震荷载",
                "loads": []
            }

        self.load_cases[case_id]["loads"].append(load_action)

        logger.info(f"Added seismic load: {load_value} kN on element {element_id}, direction={seismic_direction}")
        return load_action

    def get_load_cases(self) -> Dict[str, Any]:
        """获取所有荷载工况"""
        return self.load_cases

    def get_load_actions(self) -> list:
        """获取所有荷载动作"""
        return self.load_actions

    def _get_alpha_max(self, intensity: float) -> float:
        """获取地震影响系数最大值"""
        for key, value in sorted(self.ALPHA_MAX.items()):
            if intensity <= key:
                return value
        return self.ALPHA_MAX[9.0]

    def _get_characteristic_period(self, site_category: str, design_group: str) -> float:
        """获取特征周期"""
        key = (site_category, design_group)
        return self.CHARACTERISTIC_PERIOD.get(key, 0.40)

    def _calculate_base_shear(
        self,
        alpha_max: float,
        characteristic_period: float,
        damping_ratio: float
    ) -> float:
        """
        计算底部剪力 (简化版)

        Args:
            alpha_max: 地震影响系数最大值
            characteristic_period: 特征周期
            damping_ratio: 阻尼比

        Returns:
            底部剪力 (kN)
        """
        # 简化计算: 假设结构总重量为 10000 kN
        total_weight = 10000.0  # kN

        # 地震影响系数 (简化: 取最大值)
        alpha1 = alpha_max

        # 底部剪力
        base_shear = alpha1 * total_weight

        # 阻尼调整系数
        if damping_ratio != 0.05:
            eta1 = 0.02 + (0.05 - damping_ratio) / 8
            eta1 = max(eta1, 0.55)
            base_shear *= eta1

        return base_shear

    def _distribute_seismic_force(self, story_count: int, base_shear: float) -> List[float]:
        """
        将地震力分配到各楼层 (简化版: 倒三角形分布)

        Args:
            story_count: 楼层数
            base_shear: 底部剪力

        Returns:
            各层地震力列表
        """
        if story_count == 0:
            return []

        # 倒三角形分布: 顶层最大，底层最小
        story_forces = []
        total_weight = sum(range(1, story_count + 1))

        for i in range(1, story_count + 1):
            weight = i  # 假设各层重量相同，按高度分配
            force = base_shear * weight / total_weight
            story_forces.append(force)

        return story_forces

    def _group_elements_by_story(self) -> Dict[str, list]:
        """按楼层分组构件"""
        elements_by_story = {}
        for elem in self.model.elements:
            story_id = elem.story or "undefined"
            if story_id not in elements_by_story:
                elements_by_story[story_id] = []
            elements_by_story[story_id].append(elem)
        return elements_by_story

    def _create_seismic_load_action(
        self,
        element: Any,
        seismic_force: float,
        seismic_direction: str,
        case_id: str
    ) -> Dict[str, Any]:
        """
        创建地震荷载动作

        Args:
            element: 单元
            seismic_force: 地震力 (kN)
            seismic_direction: 地震作用方向
            case_id: 荷载工况ID

        Returns:
            荷载动作字典
        """
        # 确定荷载方向向量
        if seismic_direction == 'x':
            load_direction = {"x": 1.0, "y": 0.0, "z": 0.0}
        elif seismic_direction == '-x':
            load_direction = {"x": -1.0, "y": 0.0, "z": 0.0}
        elif seismic_direction == 'y':
            load_direction = {"x": 0.0, "y": 1.0, "z": 0.0}
        elif seismic_direction == '-y':
            load_direction = {"x": 0.0, "y": -1.0, "z": 0.0}
        elif seismic_direction == 'z':
            load_direction = {"x": 0.0, "y": 0.0, "z": 1.0}
        else:
            load_direction = {"x": 0.0, "y": 0.0, "z": 0.0}

        # 简化处理: 将楼层地震力分配到构件
        element_force = seismic_force / 2  # 假设每层2个主要构件

        load_action = {
            "actionId": f"LA_{element.id}_E",
            "caseId": case_id,
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "point_force",
            "loadValue": element_force,
            "loadDirection": load_direction,
            "description": f"地震力: {element_force:.2f} kN, 方向: {seismic_direction}"
        }

        return load_action


def generate_seismic_loads(model: StructureModelV2, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成地震荷载的主函数

    Args:
        model: V2 结构模型
        parameters: 参数字典
            - intensity: 设防烈度 (默认 7.0)
            - site_category: 场地类别 (默认 II)
            - design_group: 设计地震分组 (默认 第二组)
            - damping_ratio: 阻尼比 (默认 0.05)
            - seismic_direction: 地震作用方向 (默认 x)
            - case_id: 荷载工况ID (可选)
            - custom_loads: 自定义荷载列表 (可选)

    Returns:
        生成结果
    """
    generator = SeismicLoadGenerator(model)

    # 参数解析
    case_id = parameters.get("case_id", "LC_E")
    case_name = parameters.get("case_name", "地震工况")
    description = parameters.get("description", "地震荷载")
    intensity = parameters.get("intensity", 7.0)
    site_category = parameters.get("site_category", "II")
    design_group = parameters.get("design_group", "第二组")
    damping_ratio = parameters.get("damping_ratio", 0.05)
    seismic_direction = parameters.get("seismic_direction", "x")

    # 生成地震荷载
    result = generator.generate_seismic_loads(
        intensity=intensity,
        site_category=site_category,
        design_group=design_group,
        damping_ratio=damping_ratio,
        seismic_direction=seismic_direction,
        case_id=case_id,
        case_name=case_name,
        description=description
    )

    # 添加自定义地震荷载
    custom_loads = parameters.get("custom_loads", [])
    for load_def in custom_loads:
        generator.add_custom_seismic_load(
            element_id=load_def["element_id"],
            element_type=load_def.get("element_type", "beam"),
            load_value=load_def["load_value"],
            seismic_direction=load_def.get("seismic_direction", "x"),
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
            "intensity": intensity,
            "site_category": site_category,
            "seismic_direction": seismic_direction
        }
    }
