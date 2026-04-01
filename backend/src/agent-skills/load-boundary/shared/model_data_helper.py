"""
共享数据辅助类 / Shared Data Helper Classes

本模块定义了 load-boundary 技能中使用的共享数据辅助类，
用于消除代码重复，提高代码复用性和可维护性。

主要功能：
- 材料和截面的缓存查找
- 几何计算辅助函数
- 模型数据预加载
"""

from typing import Optional, Dict, Any, List
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class ModelDataHelper:
    """
    模型数据辅助类 / Model Data Helper

    提供高效的模型数据访问，支持缓存和预加载。
    用于消除 dead-load、live-load 等模块中的代码重复。
    """

    def __init__(self, model: Any, cache_size: int = 1000):
        """
        初始化模型数据辅助类

        Args:
            model: V2 结构模型
            cache_size: 缓存大小
        """
        self.model = model

        # 材料缓存
        self._material_cache: Dict[str, Optional[Any]] = {}

        # 截面缓存
        self._section_cache: Dict[str, Optional[Any]] = {}

        # 节点缓存
        self._node_cache: Dict[str, Optional[Any]] = {}

        # 楼层缓存
        self._story_cache: Dict[str, Optional[Any]] = {}

        # 设置 LRU 缓存大小
        self._cache_size = cache_size

        # 预加载标志
        self._is_preloaded = False

    def preload_data(self):
        """
        预加载常用数据

        在初始化时预加载所有材料、截面、节点、楼层，
        提高后续访问性能。
        """
        if self._is_preloaded:
            logger.debug("数据已预加载，跳过")
            return

        logger.info("预加载模型数据...")

        # 预加载材料
        if hasattr(self.model, 'materials'):
            for mat in self.model.materials:
                if mat.id not in self._material_cache:
                    self._material_cache[mat.id] = mat

        # 预加载截面
        if hasattr(self.model, 'sections'):
            for sec in self.model.sections:
                if sec.id not in self._section_cache:
                    self._section_cache[sec.id] = sec

        # 预加载节点
        if hasattr(self.model, 'nodes'):
            for node in self.model.nodes:
                if node.id not in self._node_cache:
                    self._node_cache[node.id] = node

        # 预加载楼层
        if hasattr(self.model, 'stories'):
            for story in self.model.stories:
                if story.id not in self._story_cache:
                    self._story_cache[story.id] = story

        self._is_preloaded = True
        logger.info(f"数据预加载完成: "
                    f"{len(self._material_cache)} 材料, "
                    f"{len(self._section_cache)} 截面, "
                    f"{len(self._node_cache)} 节点, "
                    f"{len(self._story_cache)} 楼层")

    def get_material(self, material_id: str) -> Optional[Any]:
        """
        获取材料（带缓存）

        Args:
            material_id: 材料ID

        Returns:
            材料对象，如果未找到则返回 None

        Examples:
            >>> material = helper.get_material("MAT1")
            >>> if material:
            ...     print(f"Found material: {material.id}")
        """
        # 检查缓存
        if material_id in self._material_cache:
            return self._material_cache[material_id]

        # 从模型查找
        if hasattr(self.model, 'materials'):
            for mat in self.model.materials:
                if mat.id == material_id:
                    self._material_cache[material_id] = mat
                    return mat

        # 缓存未找到的结果
        self._material_cache[material_id] = None
        logger.warning(f"Material '{material_id}' not found in model")
        return None

    def get_section(self, section_id: str) -> Optional[Any]:
        """
        获取截面（带缓存）

        Args:
            section_id: 截面ID

        Returns:
            截面对象，如果未找到则返回 None

        Examples:
            >>> section = helper.get_section("SEC1")
            >>> if section:
            ...     print(f"Found section: {section.id}")
        """
        # 检查缓存
        if section_id in self._section_cache:
            return self._section_cache[section_id]

        # 从模型查找
        if hasattr(self.model, 'sections'):
            for sec in self.model.sections:
                if sec.id == section_id:
                    self._section_cache[section_id] = sec
                    return sec

        # 缓存未找到的结果
        self._section_cache[section_id] = None
        logger.warning(f"Section '{section_id}' not found in model")
        return None

    def get_node(self, node_id: str) -> Optional[Any]:
        """
        获取节点（带缓存）

        Args:
            node_id: 节点ID

        Returns:
            节点对象，如果未找到则返回 None

        Examples:
            >>> node = helper.get_node("N1")
            >>> if node:
            ...     print(f"Found node: {node.id}")
        """
        # 检查缓存
        if node_id in self._node_cache:
            return self._node_cache[node_id]

        # 从模型查找
        if hasattr(self.model, 'nodes'):
            for node in self.model.nodes:
                if node.id == node_id:
                    self._node_cache[node_id] = node
                    return node

        # 缓存未找到的结果
        self._node_cache[node_id] = None
        logger.warning(f"Node '{node_id}' not found in model")
        return None

    def get_story(self, story_id: str) -> Optional[Any]:
        """
        获取楼层（带缓存）

        Args:
            story_id: 楼层ID

        Returns:
            楼层对象，如果未找到则返回 None

        Examples:
            >>> story = helper.get_story("F1")
            >>> if story:
            ...     print(f"Found story: {story.id}")
        """
        # 检查缓存
        if story_id in self._story_cache:
            return self._story_cache[story_id]

        # 从模型查找
        if hasattr(self.model, 'stories'):
            for story in self.model.stories:
                if story.id == story_id:
                    self._story_cache[story_id] = story
                    return story

        # 缓存未找到的结果
        self._story_cache[story_id] = None
        logger.warning(f"Story '{story_id}' not found in model")
        return None

    def clear_cache(self):
        """清除所有缓存"""
        self._material_cache.clear()
        self._section_cache.clear()
        self._node_cache.clear()
        self._story_cache.clear()
        self._is_preloaded = False
        logger.debug("所有缓存已清除")


class GeometryHelper:
    """
    几何计算辅助类 / Geometry Calculation Helper

    提供常用的几何计算函数，用于消除代码重复。
    """

    @staticmethod
    def calculate_distance_3d(
        x1: float, y1: float, z1: float,
        x2: float, y2: float, z2: float
    ) -> float:
        """
        计算两点之间的3D距离

        Args:
            x1, y1, z1: 第一个点的坐标
            x2, y2, z2: 第二个点的坐标

        Returns:
            两点之间的距离

        Examples:
            >>> distance = GeometryHelper.calculate_distance_3d(0, 0, 0, 1, 0, 0)
            >>> distance
            1.0
        """
        import math

        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        return math.sqrt(dx**2 + dy**2 + dz**2)

    @staticmethod
    def calculate_element_length(element: Any, node_helper: ModelDataHelper) -> Optional[float]:
        """
        计算构件几何长度

        Args:
            element: 构件对象
            node_helper: 节点数据辅助类

        Returns:
            构件几何长度，如果无法计算则返回 None

        Examples:
            >>> length = GeometryHelper.calculate_element_length(element, node_helper)
            >>> if length:
            ...     print(f"Element length: {length:.2f} m")
        """
        if not hasattr(element, 'nodes') or len(element.nodes) < 2:
            logger.warning(f"Element '{getattr(element, 'id', 'unknown')}' has invalid nodes")
            return None

        # 获取两端节点
        node_i = node_helper.get_node(element.nodes[0])
        node_j = node_helper.get_node(element.nodes[1])

        if not node_i or not node_j:
            logger.warning(
                f"Cannot find nodes for element '{getattr(element, 'id', 'unknown')}': "
                f"{element.nodes[0]}, {element.nodes[1]}"
            )
            return None

        # 计算距离
        return GeometryHelper.calculate_distance_3d(
            node_i.x, node_i.y, node_i.z,
            node_j.x, node_j.y, node_j.z
        )

    @staticmethod
    def calculate_section_area(section: Any) -> Optional[float]:
        """
        计算截面面积

        Args:
            section: 截面对象

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
            >>> area = GeometryHelper.calculate_section_area(section)
            >>> area
            150000

            >>> # 圆形截面
            >>> section = type('Section', (), {
            ...     'type': 'circular',
            ...     'diameter': 500,
            ...     'properties': {}
            ... })()
            >>> import math
            >>> area = GeometryHelper.calculate_section_area(section)
            >>> area == math.pi * 250 ** 2
            True
        """
        import math

        # 根据截面类型计算面积
        if hasattr(section, 'type'):
            section_type = section.type

            if section_type == "rectangular":
                if hasattr(section, 'width') and hasattr(section, 'height'):
                    return float(section.width * section.height)

            elif section_type == "circular":
                if hasattr(section, 'diameter'):
                    return float(math.pi * (section.diameter / 2) ** 2)

            elif section_type == "box":
                if all(hasattr(section, attr) for attr in ['width', 'height', 'thickness']):
                    # 箱形截面面积 = 2*(width + height)*thickness
                    return float(2 * (section.width + section.height) * section.thickness)

        # 尝试从 properties 字段获取
        if hasattr(section, 'properties') and isinstance(section.properties, dict):
            if "area" in section.properties:
                try:
                    return float(section.properties["area"])
                except (ValueError, TypeError):
                    pass

        logger.warning(f"Cannot calculate area for section '{getattr(section, 'id', 'unknown')}'")
        return None

    @staticmethod
    def calculate_tributary_width_from_geometry(
        element: Any,
        model: Any,
        model_helper: ModelDataHelper = None
    ) -> Optional[float]:
        """
        从结构模型的几何关系计算受荷宽度（梁的受荷宽度）

        受荷宽度应该根据梁的间距、楼板布置等几何关系计算。
        这需要分析相邻梁的位置关系。

        Args:
            element: 单元对象
            model: 结构模型
            model_helper: 模型数据辅助类（可选）

        Returns:
            受荷宽度（米），如果无法计算则返回 None

        Note:
            这是一个简化的几何计算，实际应用中可能需要更复杂的楼板分析。
        """
        try:
            import math

            # 检查是否为梁
            if not hasattr(element, 'type') or element.type != 'beam':
                return None

            # 获取梁的两端节点
            if not hasattr(element, 'nodes') or len(element.nodes) < 2:
                return None

            # 使用模型辅助类获取节点（如果提供）
            if model_helper:
                node_i = model_helper.get_node(element.nodes[0])
                node_j = model_helper.get_node(element.nodes[1])
            else:
                # 从模型直接获取
                node_i = None
                node_j = None
                if hasattr(model, 'nodes'):
                    for node in model.nodes:
                        if node.id == element.nodes[0]:
                            node_i = node
                        elif node.id == element.nodes[1]:
                            node_j = node

            if not node_i or not node_j:
                return None

            # 计算梁的方向向量
            dx = node_j.x - node_i.x
            dy = node_j.y - node_i.y
            dz = node_j.z - node_i.z

            # 判断梁的方向（X向或Y向）
            # 忽略Z方向的差异（只考虑平面内的梁）
            if abs(dx) > abs(dy):
                # 梁沿X方向，寻找Y方向相邻的梁
                beam_direction = 'x'
                avg_y = (node_i.y + node_j.y) / 2
            else:
                # 梁沿Y方向，寻找X方向相邻的梁
                beam_direction = 'y'
                avg_x = (node_i.x + node_j.x) / 2

            # 查找同一楼层的所有梁
            if not hasattr(model, 'elements'):
                return None

            story_id = getattr(element, 'story', None)
            parallel_beams = []

            for elem in model.elements:
                # 只考虑同一楼层的梁
                if elem.id == element.id:
                    continue
                if not hasattr(elem, 'type') or elem.type != 'beam':
                    continue
                if story_id and hasattr(elem, 'story') and elem.story != story_id:
                    continue

                # 获取梁的节点
                if model_helper:
                    n_i = model_helper.get_node(elem.nodes[0])
                    n_j = model_helper.get_node(elem.nodes[1])
                else:
                    n_i = None
                    n_j = None
                    if hasattr(model, 'nodes'):
                        for node in model.nodes:
                            if node.id == elem.nodes[0]:
                                n_i = node
                            elif node.id == elem.nodes[1]:
                                n_j = node

                if not n_i or not n_j:
                    continue

                # 计算方向
                bdx = n_j.x - n_i.x
                bdy = n_j.y - n_i.y

                # 判断是否平行
                if beam_direction == 'x':
                    # 当前梁沿X方向，检查其他梁是否也沿X方向
                    if abs(bdx) > abs(bdy):
                        # 计算Y方向的距离
                        other_avg_y = (n_i.y + n_j.y) / 2
                        distance = abs(avg_y - other_avg_y)
                        parallel_beams.append((distance, elem))
                else:
                    # 当前梁沿Y方向，检查其他梁是否也沿Y方向
                    if abs(bdy) > abs(bdx):
                        # 计算X方向的距离
                        other_avg_x = (n_i.x + n_j.x) / 2
                        distance = abs(avg_x - other_avg_x)
                        parallel_beams.append((distance, elem))

            # 按距离排序
            parallel_beams.sort(key=lambda x: x[0])

            # 计算受荷宽度
            if len(parallel_beams) >= 2:
                # 有两侧的平行梁，受荷宽度 = (左侧距离 + 右侧距离) / 2
                left_distance = parallel_beams[0][0]
                right_distance = parallel_beams[1][0]
                tributary_width = (left_distance + right_distance) / 2
                logger.debug(
                    f"Calculated tributary width for {element.id}: "
                    f"{tributary_width:.2f} m (left={left_distance:.2f}, right={right_distance:.2f})"
                )
                return tributary_width
            elif len(parallel_beams) == 1:
                # 只有一侧的平行梁，受荷宽度 = 单侧距离
                tributary_width = parallel_beams[0][0]
                logger.debug(
                    f"Calculated tributary width for {element.id}: "
                    f"{tributary_width:.2f} m (single side)"
                )
                return tributary_width
            else:
                # 没有找到平行梁
                logger.debug(f"No parallel beams found for {element.id}")
                return None

        except Exception as e:
            logger.warning(f"Error calculating tributary width for {getattr(element, 'id', 'unknown')}: {e}")
            return None


class ValidationHelper:
    """
    验证辅助类 / Validation Helper

    提供常用的验证函数，用于消除代码重复。
    """

    @staticmethod
    def validate_string_id(value: Any, field_name: str = "ID") -> bool:
        """
        验证字符串ID是否有效

        Args:
            value: 要验证的值
            field_name: 字段名称（用于错误消息）

        Returns:
            是否有效

        Raises:
            TypeError: 当值不是字符串时
            ValueError: 当值为空时

        Examples:
            >>> ValidationHelper.validate_string_id("B1")
            True
            >>> ValidationHelper.validate_string_id("")
            ValueError: ID 不能为空
        """
        if not isinstance(value, str):
            raise TypeError(f"{field_name} 必须是字符串类型，得到: {type(value)}")

        if not value or not value.strip():
            raise ValueError(f"{field_name} 不能为空")

        return True

    @staticmethod
    def validate_numeric_value(
        value: Any,
        field_name: str = "值",
        min_value: float = 0.0,
        max_value: float = None,
        allow_negative: bool = False
    ) -> bool:
        """
        验证数值是否有效

        Args:
            value: 要验证的值
            field_name: 字段名称（用于错误消息）
            min_value: 最小值
            max_value: 最大值（可选）
            allow_negative: 是否允许负数

        Returns:
            是否有效

        Raises:
            TypeError: 当值不是数字时
            ValueError: 当值超出范围时

        Examples:
            >>> ValidationHelper.validate_numeric_value(10.5)
            True
            >>> ValidationHelper.validate_numeric_value(-1.0, allow_negative=False)
            ValueError: 值不能为负数
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"{field_name} 必须是数字类型，得到: {type(value)}")

        # 检查负数
        if not allow_negative and value < 0:
            raise ValueError(f"{field_name} 不能为负数，得到: {value}")

        # 检查最小值
        if value < min_value:
            raise ValueError(
                f"{field_name} 不能小于 {min_value}，得到: {value}"
            )

        # 检查最大值
        if max_value is not None and value > max_value:
            raise ValueError(
                f"{field_name} 不能大于 {max_value}，得到: {value}"
            )

        return True

    @staticmethod
    def validate_dict_value(
        value: Any,
        field_name: str = "字典",
        required_keys: List[str] = None
    ) -> bool:
        """
        验证字典值是否有效

        Args:
            value: 要验证的值
            field_name: 字段名称（用于错误消息）
            required_keys: 必需的键列表

        Returns:
            是否有效

        Raises:
            TypeError: 当值不是字典时
            ValueError: 当缺少必需的键时

        Examples:
            >>> ValidationHelper.validate_dict_value(
            ...     {"x": 0.0, "y": -1.0, "z": 0.0},
            ...     "荷载方向",
            ...     ["x", "y", "z"]
            ... )
            True
        """
        if not isinstance(value, dict):
            raise TypeError(f"{field_name} 必须是字典类型，得到: {type(value)}")

        if required_keys:
            missing_keys = [k for k in required_keys if k not in value]
            if missing_keys:
                raise ValueError(
                    f"{field_name} 缺少必需的键: {missing_keys}"
                )

        return True
