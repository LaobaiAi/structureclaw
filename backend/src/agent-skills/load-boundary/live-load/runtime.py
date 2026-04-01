from __future__ import annotations

from typing import Any, Dict, Optional, List
from collections import defaultdict
from functools import lru_cache

from structure_protocol.structure_model_v2 import StructureModelV2
import logging
from .constants import (
    STANDARD_LIVE_LOADS,
    DEFAULT_WIDTH_BEAM,
    DEFAULT_WIDTH_SLAB,
    OutputMode,
    DEFAULT_OUTPUT_MODE,
    LoadDirection,
    LoadType,
    LoadCaseID,
    ElementType,
    TributaryWidthSource,
    get_standard_live_load,
    validate_floor_load_type,
    validate_live_load_value,
    get_default_tributary_width
)

logger = logging.getLogger(__name__)


class LiveLoadGenerator:
    """活载生成器 / Live Load Generator"""

    def __init__(self, model: StructureModelV2, output_mode: str = DEFAULT_OUTPUT_MODE):
        """
        初始化活载生成器

        Args:
            model: V2 结构模型
            output_mode: 荷载输出模式
                - "linear": 输出线荷载（kN/m），与现有分析引擎兼容
                - "area": 输出面荷载（kN/m²），供后续环节转换

        Raises:
            ValueError: 当输出模式无效时
        """
        # 验证输出模式
        if output_mode not in [OutputMode.LINEAR, OutputMode.AREA]:
            raise ValueError(
                f"无效的输出模式: {output_mode}. "
                f"有效值为: ['{OutputMode.LINEAR}', '{OutputMode.AREA}']"
            )

        self.model: StructureModelV2 = model
        self.load_cases = {}
        self.load_actions = []
        self.output_mode = output_mode

        # 优化：使用更高效的缓存
        self._section_cache: Dict[str, Any] = {}

        # 优化：预加载常用数据
        self._story_map = self._build_story_map()

    def generate_floor_live_loads(
        self,
        floor_load_type: str = "office",
        case_id: str = "LC_LL",
        case_name: str = "活载工况",
        description: str = "楼面活载"
    ) -> Dict[str, Any]:
        """
        生成楼面活载工况

        优先从结构模型中读取面荷载（model.stories[i].floor_loads），
        如果模型中没有定义，则使用标准活载值。

        Args:
            floor_load_type: 楼面荷载类型 (residential, office, classroom, etc.)
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述

        Returns:
            荷载工况和荷载动作

        Raises:
            ValueError: 当楼面荷载类型无效时

        Examples:
            >>> result = generator.generate_floor_live_loads(
            ...     floor_load_type='office',
            ...     case_id='LC_LL'
            ... )
            >>> result['status']
            'success'
        """
        # 参数验证
        validate_floor_load_type(floor_load_type)

        logger.info(f"Generating floor live loads for type: {floor_load_type}")

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
                if elem.type not in ["beam", "slab"]:
                    continue

                # 优先从模型读取面荷载
                load_value = self._get_floor_load_from_model(elem, "live")

                # 如果模型中没有定义，使用标准活载值
                if load_value is None:
                    load_value = self.STANDARD_LIVE_LOADS.get(floor_load_type, 2.0)
                    logger.info(
                        f"Element '{elem.id}' (story '{story_id}'): "
                        f"Using standard live load {load_value:.2f} kN/m² for '{floor_load_type}'"
                    )
                else:
                    logger.info(
                        f"Element '{elem.id}' (story '{story_id}'): "
                        f"Using live load from model: {load_value:.2f} kN/m²"
                    )

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
        load_direction: Optional[Dict[str, float]] = None,
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

    def _build_story_map(self) -> Dict[str, List[Any]]:
        """
        构建楼层映射（优化性能）

        预处理：按楼层分组并过滤构件

        Returns:
            楼层到构件列表的映射
        """
        story_map: Dict[str, List[Any]] = defaultdict(list)
        for elem in self.model.elements:
            if elem.type in [ElementType.BEAM, ElementType.SLAB] and elem.story:
                story_map[elem.story].append(elem)
        return story_map

    def _group_elements_by_story(self) -> Dict[str, list]:
        """
        按楼层分组构件

        Returns:
            楼层到构件列表的映射
        """
        # 优化：使用预加载的楼层映射
        return self._story_map

    def _create_floor_load_action(
        self,
        element: Any,
        load_value: float,
        case_id: str,
        floor_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        创建楼面荷载动作

        支持两种输出模式：
        1. 线荷载模式（默认）：输出 kN/m，与现有分析引擎兼容
           转换公式：linear_load = area_load × tributary_width
        2. 面荷载模式：输出 kN/m²，保留原始面荷载供后续处理
           未来优化时使用，无需受荷宽度

        Args:
            element: 单元
            load_value: 荷载值 (kN/m²)
            case_id: 荷载工况ID
            floor_type: 楼面类型

        Returns:
            荷载动作字典
        """
        element_type = element.type

        # 面荷载模式：直接输出面荷载，无需转换
        if self.output_mode == self.OUTPUT_MODE_AREA:
            load_action = {
                "actionId": f"LA_{element.id}_LL",
                "caseId": case_id,
                "elementType": element_type,
                "elementId": element.id,
                "loadType": "distributed_load",
                "loadValue": load_value,  # kN/m² - 面荷载
                "loadDirection": {"x": 0.0, "y": -1.0, "z": 0.0},
                "description": f"{floor_type} 活载: {load_value:.3f} kN/m² (面荷载)",
                "extra": {
                    "load_unit": "kN/m²",
                    "load_mode": "area",
                    "floor_type": floor_type
                }
            }
            logger.debug(
                f"Element '{element.id}' ({element_type}): "
                f"area_load={load_value:.3f} kN/m² (面荷载模式)"
            )
            return load_action

        # 线荷载模式（默认）：计算受荷宽度并转换为线荷载
        # 获取截面信息（仅用于警告，不影响计算）
        section = self._get_section(element.section)
        if not section:
            logger.warning(f"Section '{element.section}' not found for element '{element.id}'")
            # 继续处理，但使用默认受荷宽度

        # 计算受荷宽度
        tributary_width, width_source = self._calculate_tributary_width(element)

        # 面荷载转换为线荷载 (kN/m² × m = kN/m)
        linear_load = load_value * tributary_width

        logger.debug(
            f"Element '{element.id}' ({element_type}): "
            f"load_value={load_value:.3f} kN/m², "
            f"tributary_width={tributary_width:.3f}m (source: {width_source}), "
            f"linear_load={linear_load:.3f} kN/m"
        )

        load_action = {
            "actionId": f"LA_{element.id}_LL",
            "caseId": case_id,
            "elementType": element_type,
            "elementId": element.id,
            "loadType": "distributed_load",
            "loadValue": linear_load,  # kN/m - 线荷载
            "loadDirection": {"x": 0.0, "y": -1.0, "z": 0.0},
            "description": f"{floor_type} 活载: {load_value:.3f} kN/m² × {tributary_width:.2f}m = {linear_load:.3f} kN/m",
            "extra": {
                "area_load": load_value,  # 保留原始面荷载值 (kN/m²)
                "tributary_width": tributary_width,  # 保留受荷宽度 (m)
                "tributary_width_source": width_source,  # 'geometry' 或 'default'
                "calculation": f"{load_value:.3f} × {tributary_width:.3f} = {linear_load:.3f}",
                "load_unit": "kN/m",
                "load_mode": "linear",
                "floor_type": floor_type
            }
        }

        return load_action

    def _get_section(self, section_id: str) -> Any:
        """
        获取截面（带缓存）

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

    def _get_floor_load_from_model(
        self,
        element: Any,
        load_type: str
    ) -> Optional[float]:
        """
        从结构模型中读取楼面荷载

        Args:
            element: 单元对象
            load_type: 荷载类型 ("dead" 或 "live")

        Returns:
            面荷载值 (kN/m²)，如果未找到则返回 None

        Examples:
            >>> # 模型中有定义
            >>> load = generator._get_floor_load_from_model(element, "live")
            >>> load
            2.5

            >>> # 模型中无定义
            >>> load = generator._get_floor_load_from_model(element, "live")
            >>> load
            None
        """
        # 获取单元所属楼层
        story_id = element.story
        if not story_id:
            logger.warning(
                f"Element '{element.id}' has no story_id assigned. "
                f"Cannot retrieve floor load from model."
            )
            return None

        # 在 stories 列表中查找对应的楼层
        story = None
        for s in self.model.stories:
            if s.id == story_id:
                story = s
                break

        if not story:
            logger.warning(
                f"Story '{story_id}' not found in model.stories for element '{element.id}'"
            )
            return None

        # 查找指定类型的楼面荷载
        for floor_load in story.floor_loads:
            if floor_load.type == load_type:
                logger.debug(
                    f"Found floor_load: story='{story_id}', "
                    f"type='{load_type}', value={floor_load.value} kN/m²"
                )
                return float(floor_load.value)

        logger.debug(
            f"No floor_load of type '{load_type}' found in story '{story_id}' "
            f"for element '{element.id}'"
        )
        return None

    def _calculate_tributary_width_from_geometry(
        self,
        element: Any
    ) -> Optional[float]:
        """
        从结构模型的几何关系计算受荷宽度

        受荷宽度应该根据梁的间距、楼板布置等几何关系计算。
        这需要分析相邻梁的位置关系。

        Args:
            element: 单元对象

        Returns:
            受荷宽度（米），如果无法计算则返回 None
        """
        # TODO: 实现基于几何关系的受荷宽度计算
        # 需要分析：
        # 1. 梁的相邻平行梁的间距
        # 2. 楼板布置（单向板/双向板）
        # 3. 梁的相对位置（边梁/中间梁）

        # 目前返回 None，表示无法从几何关系计算
        return None

    def _calculate_tributary_width(
        self,
        element: Any
    ) -> tuple[float, str]:
        """
        计算构件受荷宽度

        优先级：
        1. 从模型几何关系计算（梁间距等）
        2. 使用默认值（并给出警告）

        Args:
            element: 单元对象

        Returns:
            (受荷宽度（米）, 来源标识)
            来源标识：'geometry' | 'default'
        """
        element_type = element.type

        # 尝试从几何关系计算
        tributary_width = self._calculate_tributary_width_from_geometry(element)
        if tributary_width is not None:
            logger.debug(
                f"Element '{element.id}' ({element_type}): "
                f"tributary_width={tributary_width:.3f}m (from geometry)"
            )
            return tributary_width, 'geometry'

        # 使用默认值并警告
        if element_type == ElementType.BEAM:
            logger.warning(
                f"==================================================\n"
                f"Element '{element.id}' (beam): 受荷宽度无法从模型几何关系计算\n"
                f"  → 使用默认值: {DEFAULT_WIDTH_BEAM/1000.0:.2f}m\n"
                f"  → 建议: 确保模型包含完整的楼板布置和梁间距信息\n"
                f"  → 或者: 手动指定受荷宽度\n"
                f"=================================================="
            )
            tributary_width_m = DEFAULT_WIDTH_BEAM / 1000.0

        elif element_type == "slab":
            # 板：楼面活载直接作用于板面，使用 1m 作为受荷宽度
            tributary_width_m = 1.0
            logger.debug(
                f"Element '{element.id}' (slab): "
                f"tributary_width={tributary_width_m:.3f}m (面荷载)"
            )

        else:
            # 其他类型（柱子、桁架等）不承受楼面活载
            logger.warning(
                f"Element '{element.id}' type '{element_type}' "
                f"not typically subjected to floor live loads, using 1.0m"
            )
            tributary_width_m = 1.0

        return tributary_width_m, 'default'

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

        Examples:
            >>> generator._validate_parameters(
            ...     element_id="B1",
            ...     element_type="beam",
            ...     load_value=2.5
            ... )
            >>> # 无异常，验证通过

            >>> generator._validate_parameters(
            ...     element_id="B1",
            ...     element_type="beam",
            ...     load_value=-1.0
            ... )
            ValueError: 荷载值不能为负数...
        """
        # 验证 element_id
        if not element_id or not isinstance(element_id, str):
            raise TypeError(
                f"单元ID必须是非空字符串，得到: {type(element_id)}"
            )

        # 验证 element_type
        valid_types = [
            ElementType.BEAM,
            ElementType.SLAB,
            ElementType.COLUMN,
            ElementType.WALL,
            ElementType.TRUSS
        ]
        if element_type not in valid_types:
            raise ValueError(
                f"无效的单元类型: {element_type}. "
                f"有效值为: {valid_types}"
            )

        # 验证 load_value
        if not isinstance(load_value, (int, float)):
            raise TypeError(
                f"荷载值必须是数字类型，得到: {type(load_value)}"
            )
        if load_value < 0:
            raise ValueError(
                f"荷载值不能为负数，得到: {load_value}"
            )

        # 验证 load_direction
        if load_direction is not None:
            if not isinstance(load_direction, dict):
                raise TypeError(
                    f"荷载方向必须是字典类型，得到: {type(load_direction)}"
                )
            required_keys = ['x', 'y', 'z']
            if not all(k in load_direction for k in required_keys):
                raise ValueError(
                    f"荷载方向必须包含 {required_keys} 键，"
                    f"得到: {list(load_direction.keys())}"
                )
            # 验证方向向量是数字
            for key, value in load_direction.items():
                if not isinstance(value, (int, float)):
                    raise TypeError(
                        f"荷载方向的 {key} 值必须是数字类型，"
                        f"得到: {type(value)}"
                    )


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
            - output_mode: 荷载输出模式 (可选，默认 "linear")
                * "linear": 输出线荷载（kN/m），与现有分析引擎兼容
                * "area": 输出面荷载（kN/m²），供后续环节转换

    Returns:
        生成结果
    """
    # 参数解析
    output_mode = parameters.get("output_mode", "linear")
    generator = LiveLoadGenerator(model, output_mode=output_mode)

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
            "output_mode": output_mode  # 添加输出模式到摘要
            "floor_type": floor_load_type
        }
    }
