from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from structure_protocol.structure_model_v2 import StructureModelV2, SectionV2
import logging
from ..shared.constants import (
    LoadType,
    ElementType,
    validate_load_value,
    validate_element_type,
    validate_numeric_value,
)

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
    
    # 默认受风宽度（单位：mm）
    DEFAULT_WIDTH_COLUMN = 500.0  # 柱子默认宽度
    DEFAULT_WIDTH_BEAM = 600.0    # 梁默认高度
    DEFAULT_WIDTH_TRUSS = 200.0   # 桁架默认尺寸
    DEFAULT_WIDTH_GENERAL = 1000.0  # 通用默认宽度

    def __init__(self, model: StructureModelV2):
        """
        初始化风载生成器

        Args:
            model: V2 结构模型
        """
        self.model: StructureModelV2 = model
        self.load_cases: Dict[str, Any] = {}
        self.load_actions: List[Dict[str, Any]] = []
        self._section_cache: Dict[str, Optional[SectionV2]] = {}  # 截面缓存，提高查询效率
        self.warnings: List[Dict[str, Any]] = []  # 存储计算过程中的警告信息
        self._warnings_by_element: Dict[str, str] = {}  # 按单元ID索引的警告缓存

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
                    
        # 优化警告查询：创建按单元ID索引的警告缓存
        for warning in self.warnings:
            element_id = warning.get("element_id")
            if element_id:
                self._warnings_by_element[element_id] = warning["message"]

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} wind load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions,
            "warnings": self.warnings  # 添加警告信息
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

        Raises:
            ValueError: 当输入参数无效时
            TypeError: 当参数类型错误时
        """
        # 参数验证
        if not element_id or not isinstance(element_id, str):
            raise TypeError(f"单元ID必须是非空字符串，得到: {type(element_id)}")
        
        validate_element_type(element_type)
        validate_load_value(load_value, LoadType.DISTRIBUTED_LOAD)
        
        # 验证风向
        valid_directions = ['x', '-x', 'y', '-y']
        if wind_direction not in valid_directions:
            raise ValueError(
                f"无效的风向: {wind_direction}. "
                f"有效值为: {valid_directions}"
            )
        
        # 确定荷载方向向量
        if wind_direction == 'x':
            load_direction = {"x": 1.0, "y": 0.0, "z": 0.0}
        elif wind_direction == '-x':
            load_direction = {"x": -1.0, "y": 0.0, "z": 0.0}
        elif wind_direction == 'y':
            load_direction = {"x": 0.0, "y": 1.0, "z": 0.0}
        else:  # '-y'
            load_direction = {"x": 0.0, "y": -1.0, "z": 0.0}

        load_action = {
            "id": f"LA_{element_id}_W",
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

    def _get_section(self, section_id: str) -> Optional[SectionV2]:
        """
        从模型中获取截面定义（带缓存）
        
        Args:
            section_id: 截面ID
            
        Returns:
            截面对象或None
        """
        if section_id in self._section_cache:
            return self._section_cache[section_id]
            
        for sec in self.model.sections:
            if sec.id == section_id:
                self._section_cache[section_id] = sec
                return sec
                
        self._section_cache[section_id] = None
        return None

    def _calculate_wind_width(self, element: Any, wind_direction: str) -> float:
        """
        计算构件受风宽度（核心改进，考虑风向）
        
        Args:
            element: 单元对象
            wind_direction: 风向（x, -x, y, -y）
            
        Returns:
            受风宽度（米）
        """
        element_type = element.type
        
        # 获取截面信息
        section = self._get_section(element.section)
        if not section:
            warning_msg = (
                f"截面缺失: 单元 '{element.id}' 引用的截面 '{element.section}' 未找到，"
                f"使用默认受风宽度 1.0m 计算"
            )
            logger.warning(warning_msg)
            self.warnings.append({
                "type": "section_not_found",
                "element_id": element.id,
                "section_id": element.section,
                "message": warning_msg,
                "default_width": 1.0,
                "timestamp": datetime.now().isoformat(),
                "story_id": element.story
            })
            return 1.0
        
        # 根据构件类型确定受风宽度
        if element_type == "column":
            # 柱子：根据风向决定受力面
            # X向风（-x/x）：作用在柱子的高度方向（截面高度）
            # Y向风（-y/y）：作用在柱子的宽度方向（截面宽度）
            if wind_direction in ['x', '-x']:
                wind_width_mm = section.height if section.height is not None else 500.0
                face_description = "高度方向"
            else:
                wind_width_mm = section.width if section.width is not None else 500.0
                face_description = "宽度方向"
            
            wind_width_m = wind_width_mm / 1000.0
            logger.debug(
                f"Element '{element.id}' (column): {face_description}受力，"
                f"section={'height=' + str(section.height) if wind_direction in ['x', '-x'] else 'width=' + str(section.width)}mm, "
                f"wind_width={wind_width_m:.3f}m"
            )
            return wind_width_m
            
        elif element_type == "beam":
            # 梁：高度方向受力（梁侧面受风）
            # 明确处理None和0的情况
            if section.height is not None:
                wind_width_mm = section.height
            elif section.width is not None:
                wind_width_mm = section.width
            else:
                wind_width_mm = 600.0  # 默认600mm
            
            wind_width_m = wind_width_mm / 1000.0
            logger.debug(
                f"Element '{element.id}' (beam): 侧面受风，"
                f"section.height={section.height}mm, "
                f"wind_width={wind_width_m:.3f}m"
            )
            return wind_width_m
            
        elif element_type == "truss":
            # 桁架：支持多种截面类型
            if section.type == "box" and section.thickness is not None:
                # 箱型截面：使用壁厚
                wind_width_mm = section.thickness * 2  # 两侧壁厚
                logger.debug(f"Element '{element.id}' (truss, box): thickness={section.thickness}mm")
            elif section.diameter is not None:
                # 圆形截面：使用直径
                wind_width_mm = section.diameter
                logger.debug(f"Element '{element.id}' (truss, circular): diameter={section.diameter}mm")
            elif section.height is not None:
                # 矩形截面：使用高度
                wind_width_mm = section.height
                logger.debug(f"Element '{element.id}' (truss, rectangular): height={section.height}mm")
            else:
                wind_width_mm = 200.0  # 默认200mm
            
            wind_width_m = wind_width_mm / 1000.0
            logger.debug(f"Element '{element.id}' (truss): wind_width={wind_width_m:.3f}m")
            return wind_width_m
        
        elif element_type in ["wall", "shell", "slab"]:
            # 面单元：直接返回1.0m，后续会处理为面荷载
            logger.debug(f"Element '{element.id}' ({element_type}): 面单元，将使用面荷载")
            return 1.0
        
        else:
            # 其他类型默认1.0m
            warning_msg = (
                f"默认宽度: 单元 '{element.id}' 类型 '{element_type}' 未定义受风宽度计算规则，"
                f"使用默认受风宽度 1.0m 计算"
            )
            logger.warning(warning_msg)
            self.warnings.append({
                "type": "unsupported_element_type",
                "element_id": element.id,
                "element_type": element_type,
                "message": warning_msg,
                "default_width": 1.0,
                "timestamp": datetime.now().isoformat(),
                "story_id": element.story
            })
            return 1.0

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

        # 核心改进: 基于截面尺寸计算受风宽度（考虑风向）
        wind_width = self._calculate_wind_width(element, wind_direction)
        
        # 面风压 → 线荷载转换 (kN/m² × m = kN/m)
        linear_load = wind_pressure * wind_width
        
        logger.debug(
            f"Element '{element.id}' ({element.type}): "
            f"wind_pressure={wind_pressure:.3f} kN/m², "
            f"wind_width={wind_width:.3f}m, "
            f"linear_load={linear_load:.3f} kN/m"
        )

        # 检查是否有针对此单元的警告（使用优化后的缓存）
        warning_notes = ""
        if element.id in self._warnings_by_element:
            warning_notes = f" [注意: {self._warnings_by_element[element.id]}]"
        
        load_action = {
            "id": f"LA_{element.id}_W",
            "caseId": case_id,
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "distributed_load",
            "loadValue": linear_load,
            "loadDirection": load_direction,
            "description": f"风载: {wind_pressure:.3f} kN/m² × {wind_width:.2f}m = {linear_load:.3f} kN/m, 方向: {wind_direction}{warning_notes}"
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
        "warnings": generator.warnings,  # 添加警告信息
        "summary": {
            "case_count": len(generator.get_load_cases()),
            "action_count": len(generator.get_load_actions()),
            "warning_count": len(generator.warnings),  # 添加警告数量统计
            "case_id": case_id,
            "basic_pressure": basic_pressure,
            "wind_direction": wind_direction
        }
    }
