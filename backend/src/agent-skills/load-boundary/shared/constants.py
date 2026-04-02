"""
荷载与边界条件共享常量
Load and Boundary Shared Constants
统一管理所有荷载类型、单位等常量
"""

from enum import Enum
from typing import Dict, Any, Optional


# ============================================================================
# 荷载类型枚举 (Load Type Enum) - 对齐 V2 Schema
# ============================================================================

class LoadType(str, Enum):
    """荷载类型枚举 / Load Type Enumeration - 对齐 V2 Schema"""
    DISTRIBUTED_LOAD = "distributed_load"  # 均布荷载
    POINT_FORCE = "point_force"         # 集中力
    MOMENT = "moment"                 # 弯矩
    TORQUE = "torque"                # 扭矩
    AXIAL_FORCE = "axial_force"        # 轴向力


# ============================================================================
# 单元类型枚举 (Element Type Enum)
# ============================================================================

class ElementType(str, Enum):
    """单元类型枚举 / Element Type Enumeration"""
    BEAM = "beam"       # 梁
    COLUMN = "column"   # 柱
    SLAB = "slab"       # 板
    WALL = "wall"       # 墙
    TRUSS = "truss"     # 桁架
    BRACE = "brace"     # 支撑
    SHELL = "shell"     # 壳
    SOLID = "solid"     # 实体
    LINK = "link"       # 连接单元


# ============================================================================
# 荷载方向常量 (Load Direction Constants)
# ============================================================================

class LoadDirection:
    """荷载方向常量 / Load Direction Constants"""
    # 主方向
    POSITIVE_X = {"x": 1.0, "y": 0.0, "z": 0.0}   # +X方向
    NEGATIVE_X = {"x": -1.0, "y": 0.0, "z": 0.0}  # -X方向
    POSITIVE_Y = {"x": 0.0, "y": 1.0, "z": 0.0}   # +Y方向
    NEGATIVE_Y = {"x": 0.0, "y": -1.0, "z": 0.0}  # -Y方向
    POSITIVE_Z = {"x": 0.0, "y": 0.0, "z": 1.0}   # +Z方向
    NEGATIVE_Z = {"x": 0.0, "y": 0.0, "z": -1.0}  # -Z方向 (重力方向)
    
    # 重力方向 (默认)
    GRAVITY = NEGATIVE_Z


# ============================================================================
# 荷载值范围 (Load Value Ranges)
# ============================================================================

MIN_LOAD_VALUE = 0.0           # 最小荷载值 (kN/m² 或 kN)
MAX_DISTRIBUTED_LOAD = 1000.0  # 最大均布荷载 (kN/m)
MAX_POINT_LOAD = 10000.0        # 最大集中荷载 (kN)
MAX_AREA_LOAD = 50.0           # 最大面荷载 (kN/m²)


# ============================================================================
# 验证辅助函数 (Validation Helper Functions)
# ============================================================================

def validate_load_value(
    load_value: float,
    load_type: str = LoadType.DISTRIBUTED_LOAD
) -> bool:
    """
    验证荷载值是否在合理范围内
    
    Args:
        load_value: 荷载值
        load_type: 荷载类型
    
    Returns:
        是否有效
    
    Raises:
        TypeError: 当参数类型错误时
        ValueError: 当荷载值无效时
    """
    # 检查是否为数字
    if not isinstance(load_value, (int, float)):
        raise TypeError(f"荷载值必须是数字类型，得到: {type(load_value)}")
    
    # 检查是否为负数
    if load_value < MIN_LOAD_VALUE:
        raise ValueError(f"荷载值不能为负数，得到: {load_value}")
    
    # 检查是否超过最大值
    if load_type == LoadType.DISTRIBUTED_LOAD:
        max_value = MAX_DISTRIBUTED_LOAD
    elif load_type == LoadType.AXIAL_FORCE or load_type == LoadType.POINT_FORCE:
        max_value = MAX_POINT_LOAD
    else:
        max_value = MAX_AREA_LOAD
    
    if load_value > max_value:
        raise ValueError(
            f"荷载值超过最大值 {max_value}，得到: {load_value}"
        )
    
    return True


def validate_element_type(element_type: str) -> bool:
    """
    验证单元类型是否有效
    
    Args:
        element_type: 单元类型
    
    Returns:
        是否有效
    
    Raises:
        ValueError: 当单元类型无效时
    """
    valid_types = [
        ElementType.BEAM,
        ElementType.COLUMN,
        ElementType.SLAB,
        ElementType.WALL,
        ElementType.TRUSS,
        ElementType.BRACE,
        ElementType.SHELL,
        ElementType.SOLID,
        ElementType.LINK
    ]
    
    if element_type not in valid_types:
        raise ValueError(
            f"无效的单元类型: {element_type}. "
            f"有效值为: {valid_types}"
        )
    
    return True


def validate_string_id(
    value: str,
    field_name: str = "ID"
) -> bool:
    """
    验证字符串ID
    
    Args:
        value: 字符串值
        field_name: 字段名称
    
    Returns:
        是否有效
    
    Raises:
        TypeError: 当类型错误时
        ValueError: 当值为空时
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name}必须是字符串类型，得到: {type(value)}"
        )
    
    if not value or not value.strip():
        raise ValueError(
            f"{field_name}不能为空"
        )
    
    return True


def validate_dict_value(
    value: Dict[str, Any],
    field_name: str = "字典值",
    required_keys: Optional[list] = None
) -> bool:
    """
    验证字典值
    
    Args:
        value: 字典值
        field_name: 字段名称
        required_keys: 必需的键列表
    
    Returns:
        是否有效
    
    Raises:
        TypeError: 当类型错误时
        ValueError: 当缺少必需键时
    """
    if not isinstance(value, dict):
        raise TypeError(
            f"{field_name}必须是字典类型，得到: {type(value)}"
        )
    
    if required_keys:
        missing_keys = [k for k in required_keys if k not in value]
        if missing_keys:
            raise ValueError(
                f"{field_name}缺少必需键: {missing_keys}"
            )
    
    return True


def validate_numeric_value(
    value: float,
    field_name: str = "数值",
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    allow_negative: bool = False
) -> bool:
    """
    验证数值
    
    Args:
        value: 数值
        field_name: 字段名称
        min_value: 最小值
        max_value: 最大值
        allow_negative: 是否允许负数
    
    Returns:
        是否有效
    
    Raises:
        TypeError: 当类型错误时
        ValueError: 当数值无效时
    """
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_name}必须是数字类型，得到: {type(value)}"
        )
    
    if not allow_negative and value < 0:
        raise ValueError(
            f"{field_name}不能为负数，得到: {value}"
        )
    
    if min_value is not None and value < min_value:
        raise ValueError(
            f"{field_name}不能小于 {min_value}，得到: {value}"
        )
    
    if max_value is not None and value > max_value:
        raise ValueError(
            f"{field_name}不能大于 {max_value}，得到: {value}"
        )
    
    return True
