from __future__ import annotations

from typing import Any, Dict, List, Optional

from structure_protocol.structure_model_v2 import StructureModelV2
import logging

from .base_shear_calculator import BaseShearCalculator, WeightCalculationMethod
from .force_distributor import ForceDistributor, ForceDistributeMethod
from .model_reader import ModelDataReader
from .utils import validate_seismic_parameters
from .constants import (
    KG_TO_KN,
    MM2_TO_M2,
    DEFAULT_FLOOR_HEIGHT,
    DEFAULT_SECTION_AREA
)

logger = logging.getLogger(__name__)


class SeismicLoadGenerator:
    """地震荷载生成器 / Seismic Load Generator"""

    # 注意：ALPHA_MAX 和 CHARACTERISTIC_PERIOD 已移至 BaseShearCalculator
    # 如需访问，请使用 base_shear_calculator.ALPHA_MAX / CHARACTERISTIC_PERIOD

    def __init__(
        self,
        model: StructureModelV2,
        weight_calculation_method: Optional[WeightCalculationMethod] = None,
        force_distribute_method: Optional[ForceDistributeMethod] = None
    ):
        """
        初始化地震荷载生成器

        Args:
            model: V2 结构模型
            weight_calculation_method: 重量计算方法
            force_distribute_method: 地震力分配方法
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

        # 初始化模块化组件
        self.model_reader = ModelDataReader(model)
        self.base_shear_calculator = BaseShearCalculator(
            model,
            weight_calculation_method or WeightCalculationMethod.AUTO
        )
        self.force_distributor = ForceDistributor(
            model,
            force_distribute_method or ForceDistributeMethod.AUTO
        )

    def generate_seismic_loads(
        self,
        intensity: float = 7.0,
        site_category: str = 'II',
        design_group: str = '第二组',
        damping_ratio: float = 0.05,
        seismic_direction: str = 'x',
        case_id: str = "LC_E",
        case_name: str = "地震工况",
        description: str = "地震荷载",
        weight_calculation_method: Optional[WeightCalculationMethod] = None,
        force_distribute_method: Optional[ForceDistributeMethod] = None,
        live_load_factor: float = 0.5
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
            weight_calculation_method: 重量计算方法 (from_model_direct, from_elements, from_floors, default_value, auto)
            force_distribute_method: 地震力分配方法 (by_stiffness, by_distance, evenly, auto)
            live_load_factor: 活载组合值系数 (默认 0.5)

        Returns:
            荷载工况和荷载动作

        Raises:
            ValueError: 当输入参数无效时
        """
        # 验证输入参数
        is_valid, errors = validate_seismic_parameters(
            intensity=intensity,
            site_category=site_category,
            design_group=design_group,
            damping_ratio=damping_ratio,
            live_load_factor=live_load_factor
        )

        if not is_valid:
            error_msg = "地震荷载参数验证失败:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(
            f"Generating seismic loads: intensity={intensity}, site={site_category}, "
            f"direction={seismic_direction}, weight_method={weight_calculation_method or 'auto'}, "
            f"distribute_method={force_distribute_method or 'auto'}"
        )

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "seismic",  # 对齐 V2 Schema LoadCaseV2.type
            "description": description,
            "loads": []
        }

        # 计算底部剪力 (使用专业计算模块)
        base_shear_result = self.base_shear_calculator.calculate_base_shear(
            intensity=intensity,
            site_category=site_category,
            design_group=design_group,
            damping_ratio=damping_ratio,
            live_load_factor=live_load_factor,
            weight_calculation_method=weight_calculation_method
        )

        base_shear = base_shear_result["base_shear"]
        logger.info(f"底部剪力: {base_shear:.2f} kN (方法: {base_shear_result['weight_calculation_method']})")

        # 将地震力分配到各楼层 (GB 50011-2010 第5.2.1条: 按楼层重量分配)
        elements_by_story = self._group_elements_by_story()
        story_forces = self._distribute_seismic_force(
            elements_by_story=elements_by_story,
            base_shear=base_shear
        )

        # 为每个楼层的构件创建地震荷载
        for story_idx, (story_id, elements) in enumerate(elements_by_story.items()):
            story_force = story_forces[story_idx]

            # 使用专业分配模块分配力
            distributed_forces = self.force_distributor.distribute_force_to_floor(
                floor_elements=elements,
                total_force=story_force,
                direction=seismic_direction,
                distribute_method=force_distribute_method
            )

            # 创建荷载动作
            for elem in elements:
                if elem.id in distributed_forces:
                    force_data = distributed_forces[elem.id]
                    load_action = self._create_seismic_load_action(
                        element=elem,
                        force_data=force_data,
                        case_id=case_id,
                        story_id=story_id
                    )
                    if load_action:
                        load_case["loads"].append(load_action)
                        self.load_actions.append(load_action)

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} seismic load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions,
            "base_shear_result": base_shear_result,
            "story_forces": story_forces
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
            "id": f"LA_{element_id}_E",
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

    def _distribute_seismic_force(self, elements_by_story: Dict[str, list], base_shear: float) -> List[float]:
        """
        将地震力分配到各楼层 (GB 50011-2010 第5.2.1条: 倒三角形分布)

        F_i = (G_i * H_i / ΣG_j * H_j) * F_ek

        Args:
            elements_by_story: 按楼层分组的构件字典 {story_id: [elements]}
            base_shear: 底部剪力

        Returns:
            各层地震力列表 (按楼层ID排序)
        """
        if not elements_by_story:
            return []

        # 获取所有楼层ID并按楼层号排序
        story_ids = sorted(elements_by_story.keys(), key=lambda x: int(''.join(filter(str.isdigit, x)) or '0'))

        # 计算每个楼层的重量和高度
        story_data = []
        total_weighted_height = 0.0

        for i, story_id in enumerate(story_ids, start=1):
            # 获取楼层重量
            story_weight = self._calculate_story_weight(elements_by_story[story_id])

            # 获取楼层高度 (简化: 按楼层号假设每层 DEFAULT_FLOOR_HEIGHT m)
            story_height = i * DEFAULT_FLOOR_HEIGHT

            # 计算重量×高度
            weighted_height = story_weight * story_height
            total_weighted_height += weighted_height

            story_data.append({
                'id': story_id,
                'weight': story_weight,
                'height': story_height,
                'weighted_height': weighted_height
            })

            logger.info(f"楼层 {story_id}: 重量={story_weight:.2f}kN, 高度={story_height:.2f}m")

        # 按重量×高度比例分配地震力
        story_forces = []
        for data in story_data:
            force = base_shear * data['weighted_height'] / total_weighted_height
            story_forces.append(force)

        logger.info(f"楼层力分配: 总力={base_shear:.2f}kN, 各层力={[f'{f:.2f}kN' for f in story_forces]}")

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

    def _calculate_story_weight(self, elements: list) -> float:
        """
        计算楼层总重量

        Args:
            elements: 楼层构件列表

        Returns:
            楼层重量 (kN)
        """
        total_weight = 0.0
        material_dict = {m.id: m for m in self.model.materials}
        section_dict = {s.id: s for s in self.model.sections}

        for elem in elements:
            # 跳过非结构构件
            if elem.type not in ["beam", "column", "wall", "slab"]:
                continue

            material = material_dict.get(elem.material)
            section = section_dict.get(elem.section)

            if not material or not section:
                continue

            # 计算构件重量
            element_weight = self._calculate_element_weight(elem, material, section)
            total_weight += element_weight

        return total_weight

    def _calculate_element_weight(
        self,
        element: Any,
        material: Any,
        section: Any
    ) -> float:
        """
        计算单个构件重量

        Args:
            element: 构件
            material: 材料
            section: 截面

        Returns:
            重量 (kN)
        """
        # 计算构件长度 (m)
        elem_length = self._calculate_element_length(element)
        if elem_length <= 0:
            return 0.0

        # 计算构件面积 (m²)
        area = self._calculate_section_area(section)

        # 计算体积 (m³)
        volume = area * elem_length

        # 计算重量 (kg -> kN)
        weight_kg = volume * material.rho
        weight_kn = weight_kg * KG_TO_KN

        return weight_kn

    def _calculate_element_length(self, element: Any) -> float:
        """计算构件长度 (m)"""
        if len(element.nodes) < 2:
            return 0.0

        node_dict = {n.id: n for n in self.model.nodes}

        start_node = node_dict.get(element.nodes[0])
        end_node = node_dict.get(element.nodes[1])

        if not start_node or not end_node:
            return 0.0

        dx = end_node.x - start_node.x
        dy = end_node.y - start_node.y
        dz = end_node.z - start_node.z

        length = (dx**2 + dy**2 + dz**2) ** 0.5

        return length

    def _calculate_section_area(self, section: Any) -> float:
        """计算截面面积 (m²)"""
        # 优先使用 properties 中的面积
        if hasattr(section, 'properties') and 'area' in section.properties:
            return float(section.properties['area'])

        # 根据截面类型计算面积
        section_type = section.type.lower()

        if section_type == "rectangular" and section.width and section.height:
            # 矩形截面: A = b × h (mm² -> m²)
            area_mm2 = section.width * section.height
            return area_mm2 * MM2_TO_M2

        elif section_type == "circular" and section.diameter:
            # 圆形截面: A = π × d² / 4 (mm² -> m²)
            area_mm2 = 3.14159 * (section.diameter ** 2) / 4
            return area_mm2 * MM2_TO_M2

        elif section_type in ["i", "t", "box"]:
            if section.width and section.height and section.thickness:
                # I形、T形、箱形截面 (简化估算)
                outer_area = section.width * section.height
                inner_area = 0.8 * (section.width - 2 * section.thickness) * (section.height - 2 * section.thickness)
                area_mm2 = outer_area - inner_area
                return max(area_mm2, 0.0) * MM2_TO_M2

        logger.warning(f"无法计算截面 {section.id} 的面积，使用默认值 {DEFAULT_SECTION_AREA:.2f} m²")
        return DEFAULT_SECTION_AREA

    def _create_seismic_load_action(
        self,
        element: Any,
        force_data: Dict[str, Any],
        case_id: str,
        story_id: str
    ) -> Dict[str, Any]:
        """
        创建地震荷载动作

        Args:
            element: 单元
            force_data: 力数据字典 (包含 force, direction 等)
            case_id: 荷载工况ID
            story_id: 楼层ID

        Returns:
            荷载动作字典
        """
        element_force = force_data.get("force", 0.0)
        load_direction = force_data.get("direction", {"x": 0.0, "y": 0.0, "z": 0.0})

        load_action = {
            "id": f"LA_{element.id}_E",
            "caseId": case_id,
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "point_force",
            "loadValue": element_force,
            "loadDirection": load_direction,
            "description": f"地震力: {element_force:.2f} kN"
        }

        # 添加额外信息
        if "stiffness" in force_data:
            load_action["stiffness"] = force_data["stiffness"]
        if "stiffness_ratio" in force_data:
            load_action["stiffness_ratio"] = force_data["stiffness_ratio"]
        if "distribution_ratio" in force_data:
            load_action["distribution_ratio"] = force_data["distribution_ratio"]

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
            - weight_calculation_method: 重量计算方法 (可选: auto, from_model_direct, from_elements, from_floors, default_value)
            - force_distribute_method: 地震力分配方法 (可选: auto, by_stiffness, by_distance, evenly)
            - live_load_factor: 活载组合值系数 (默认 0.5)
            - custom_loads: 自定义荷载列表 (可选)

    Returns:
        生成结果
    """
    from .utils import validate_seismic_parameters

    # 参数解析
    case_id = parameters.get("case_id", "LC_E")
    case_name = parameters.get("case_name", "地震工况")
    description = parameters.get("description", "地震荷载")
    intensity = parameters.get("intensity", 7.0)
    site_category = parameters.get("site_category", "II")
    design_group = parameters.get("design_group", "第二组")
    damping_ratio = parameters.get("damping_ratio", 0.05)
    seismic_direction = parameters.get("seismic_direction", "x")

    # 验证输入参数
    is_valid, errors = validate_seismic_parameters(
        intensity=intensity,
        site_category=site_category,
        design_group=design_group,
        damping_ratio=damping_ratio,
        live_load_factor=parameters.get("live_load_factor", 0.5)
    )

    if not is_valid:
        error_msg = "地震荷载参数验证失败:\n" + "\n".join(errors)
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "errors": errors
        }

    # 解析重量计算方法
    weight_method_str = parameters.get("weight_calculation_method", "auto")
    weight_calculation_method = _parse_weight_calculation_method(weight_method_str)

    # 解析地震力分配方法
    distribute_method_str = parameters.get("force_distribute_method", "auto")
    force_distribute_method = _parse_force_distribute_method(distribute_method_str)

    # 活载组合值系数
    live_load_factor = parameters.get("live_load_factor", 0.5)

    # 创建生成器
    generator = SeismicLoadGenerator(
        model,
        weight_calculation_method=weight_calculation_method,
        force_distribute_method=force_distribute_method
    )

    # 生成地震荷载
    result = generator.generate_seismic_loads(
        intensity=intensity,
        site_category=site_category,
        design_group=design_group,
        damping_ratio=damping_ratio,
        seismic_direction=seismic_direction,
        case_id=case_id,
        case_name=case_name,
        description=description,
        weight_calculation_method=weight_calculation_method,
        force_distribute_method=force_distribute_method,
        live_load_factor=live_load_factor
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
            "design_group": design_group,
            "seismic_direction": seismic_direction,
            "weight_calculation_method": weight_calculation_method.value,
            "force_distribute_method": force_distribute_method.value,
            "live_load_factor": live_load_factor
        },
        "calculation_details": {
            "base_shear": result.get("base_shear_result", {}).get("base_shear", 0),
            "total_weight": result.get("base_shear_result", {}).get("total_weight", 0),
            "alpha_max": result.get("base_shear_result", {}).get("alpha_max", 0),
            "story_forces": result.get("story_forces", [])
        }
    }


def _parse_weight_calculation_method(method_str: str) -> WeightCalculationMethod:
    """解析重量计算方法字符串"""
    method_map = {
        "auto": WeightCalculationMethod.AUTO,
        "from_model_direct": WeightCalculationMethod.FROM_MODEL_DIRECT,
        "from_elements": WeightCalculationMethod.FROM_ELEMENTS,
        "from_floors": WeightCalculationMethod.FROM_FLOORS,
        "default_value": WeightCalculationMethod.DEFAULT_VALUE
    }
    return method_map.get(method_str.lower(), WeightCalculationMethod.AUTO)


def _parse_force_distribute_method(method_str: str) -> ForceDistributeMethod:
    """解析地震力分配方法字符串"""
    method_map = {
        "auto": ForceDistributeMethod.AUTO,
        "by_stiffness": ForceDistributeMethod.BY_STIFFNESS,
        "by_distance": ForceDistributeMethod.BY_DISTANCE,
        "evenly": ForceDistributeMethod.EVENLY
    }
    return method_map.get(method_str.lower(), ForceDistributeMethod.AUTO)

