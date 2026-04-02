from __future__ import annotations

from typing import Any, Dict, List

from structure_protocol.structure_model_v2 import StructureModelV2
import logging
from ..shared.constants import (
    LoadType,
    ElementType,
    validate_element_type,
    validate_numeric_value,
    validate_string_id,
)

logger = logging.getLogger(__name__)


class CraneLoadGenerator:
    """吊车荷载生成器 / Crane Load Generator"""

    def __init__(self, model: StructureModelV2):
        """
        初始化吊车荷载生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.load_cases = {}
        self.load_actions = []

    def generate_crane_loads(
        self,
        case_id: str = "LC_CRANE",
        case_name: str = "吊车荷载工况",
        description: str = "桥式起重机荷载",
        crane_capacity: float = 50.0,  # 吊车起重量 (kN)
        crane_span: float = 30.0,       # 吊车跨度 (m)
        load_positions: List[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        生成吊车荷载工况

        Args:
            case_id: 荷载工况ID
            case_name: 荷载工况名称
            description: 荷载工况描述
            crane_capacity: 吊车起重量 (kN)
            crane_span: 吊车跨度 (m)
            load_positions: 荷载位置列表

        Returns:
            荷载工况和荷载动作

        Raises:
            ValueError: 当输入参数无效时
        """
        # 参数验证
        validate_string_id(case_id, "工况ID")
        validate_numeric_value(crane_capacity, "吊车起重量", min_value=0.1, max_value=1000.0)
        validate_numeric_value(crane_span, "吊车跨度", min_value=1.0, max_value=200.0)
        
        logger.info(f"Generating crane loads for case: {case_id}, capacity={crane_capacity}kN, span={crane_span}m")

        # 创建荷载工况 - 对齐 V2 Schema
        load_case = {
            "id": case_id,
            "type": "crane",  # 对齐 V2 Schema LoadCaseV2.type
            "description": f"吊车容量: {crane_capacity} kN, 跨度: {crane_span} m",
            "loads": []
        }

        # 如果没有指定位置，生成典型位置
        if load_positions is None:
            # 简化：在跨中施加最大荷载
            load_positions = [
                {"x": crane_span / 2, "y": 0.0, "z": 0.0}
            ]

        # 遍历所有构件，对梁施加吊车荷载
        for elem in self.model.elements:
            try:
                # 只对梁施加吊车荷载
                if elem.type == "beam":
                    for pos in load_positions:
                        load_action = self._calculate_crane_load(
                            element=elem,
                            position=pos,
                            crane_capacity=crane_capacity,
                            crane_span=crane_span
                        )

                        if load_action:
                            load_case["loads"].append(load_action)
                            self.load_actions.append(load_action)

            except (ValueError, ArithmeticError) as error:
                logger.error(f"计算构件 '{elem.id}' 的吊车荷载时发生数值错误: {error}")
                continue
            except RuntimeError as error:
                logger.error(f"计算构件 '{elem.id}' 的吊车荷载时发生运行时错误: {error}")
                continue

        self.load_cases[case_id] = load_case
        logger.info(f"Generated {len(load_case['loads'])} crane load actions")

        return {
            "load_case": load_case,
            "load_actions": self.load_actions
        }

    def _calculate_crane_load(
        self,
        element: Any,
        position: Dict[str, float],
        crane_capacity: float,
        crane_span: float
    ) -> Dict[str, Any]:
        """
        计算吊车荷载

        Args:
            element: 构件对象
            position: 荷载位置
            crane_capacity: 吊车起重量
            crane_span: 吊车跨度

        Returns:
            荷载动作字典
        """
        # 简化：集中力作用于指定位置
        return {
            "id": f"CRANE_{element.id}_{position['x']}",
            "caseId": "LC_CRANE",
            "elementType": element.type,
            "elementId": element.id,
            "loadType": "point_force",  # 集中力
            "loadValue": crane_capacity,
            "loadDirection": {"x": 0.0, "y": 0.0, "z": -1.0},  # 向下
            "position": position,
            "extra": {
                "crane_capacity": crane_capacity,
                "crane_span": crane_span,
                "dynamic_factor": 1.1  # 吊车动力系数
            }
        }
