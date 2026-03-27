from __future__ import annotations

from typing import Any, Dict, List

from structure_protocol.structure_model_v2 import StructureModelV2
import logging

logger = logging.getLogger(__name__)


class BoundaryConditionGenerator:
    """边界条件生成器 / Boundary Condition Generator"""

    def __init__(self, model: StructureModelV2):
        """
        初始化边界条件生成器

        Args:
            model: V2 结构模型
        """
        self.model = model
        self.nodal_constraints = {}
        self.member_end_releases = {}
        self.effective_lengths = {}

    def apply_fixed_support(
        self,
        node_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        施加固定支座 (约束所有6个自由度)

        Args:
            node_ids: 节点ID列表，如果为None则默认基础节点

        Returns:
            节点约束字典
        """
        if node_ids is None:
            # 自动识别基础节点 (z坐标最小的节点)
            min_z = min(node.z for node in self.model.nodes)
            node_ids = [node.id for node in self.model.nodes if abs(node.z - min_z) < 0.001]

        logger.info(f"Applying fixed supports to {len(node_ids)} nodes")

        for node_id in node_ids:
            self.nodal_constraints[node_id] = {
                "nodeId": node_id,
                "constraintType": "fixed",
                "restrainedDOFs": {
                    "ux": True,
                    "uy": True,
                    "uz": True,
                    "rx": True,
                    "ry": True,
                    "rz": True
                }
            }

        return {
            "constraints": self.nodal_constraints,
            "count": len(node_ids)
        }

    def apply_pinned_support(
        self,
        node_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        施加铰支座 (约束3个平动自由度)

        Args:
            node_ids: 节点ID列表

        Returns:
            节点约束字典
        """
        if node_ids is None:
            min_z = min(node.z for node in self.model.nodes)
            node_ids = [node.id for node in self.model.nodes if abs(node.z - min_z) < 0.001]

        logger.info(f"Applying pinned supports to {len(node_ids)} nodes")

        for node_id in node_ids:
            self.nodal_constraints[node_id] = {
                "nodeId": node_id,
                "constraintType": "pinned",
                "restrainedDOFs": {
                    "ux": True,
                    "uy": True,
                    "uz": True,
                    "rx": False,
                    "ry": False,
                    "rz": False
                }
            }

        return {
            "constraints": self.nodal_constraints,
            "count": len(node_ids)
        }

    def apply_rolling_support(
        self,
        node_ids: List[str],
        rolling_direction: str = 'y'
    ) -> Dict[str, Any]:
        """
        施加滚动支座 (约束部分平动自由度)

        Args:
            node_ids: 节点ID列表
            rolling_direction: 滚动方向 ('x', 'y', 'z')

        Returns:
            节点约束字典
        """
        logger.info(f"Applying rolling supports to {len(node_ids)} nodes, direction={rolling_direction}")

        for node_id in node_ids:
            # 根据滚动方向设置约束
            if rolling_direction == 'x':
                restrained_dofs = {
                    "ux": False,  # X方向自由滚动
                    "uy": True,
                    "uz": True,
                    "rx": False,
                    "ry": False,
                    "rz": False
                }
            elif rolling_direction == 'y':
                restrained_dofs = {
                    "ux": True,
                    "uy": False,  # Y方向自由滚动
                    "uz": True,
                    "rx": False,
                    "ry": False,
                    "rz": False
                }
            else:
                restrained_dofs = {
                    "ux": True,
                    "uy": True,
                    "uz": False,  # Z方向自由滚动
                    "rx": False,
                    "ry": False,
                    "rz": False
                }

            self.nodal_constraints[node_id] = {
                "node_id": node_id,
                "constraint_type": "rolling",
                "restrained_dofs": restrained_dofs
            }

        return {
            "constraints": self.nodal_constraints,
            "count": len(node_ids)
        }

    def apply_hinged_member_ends(
        self,
        member_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        施加杆端铰接 (两端释放转动自由度)

        Args:
            member_ids: 杆件ID列表，如果为None则应用于所有杆件

        Returns:
            杆端释放字典
        """
        if member_ids is None:
            member_ids = [elem.id for elem in self.model.elements if elem.type in ["beam", "column"]]

        logger.info(f"Applying hinged ends to {len(member_ids)} members")

        for member_id in member_ids:
            self.member_end_releases[member_id] = {
                "memberId": member_id,
                "releaseI": {
                    "ux": False,
                    "uy": False,
                    "uz": False,
                    "rx": True,   # I端释放转动
                    "ry": True,
                    "rz": True
                },
                "releaseJ": {
                    "ux": False,
                    "uy": False,
                    "uz": False,
                    "rx": True,   # J端释放转动
                    "ry": True,
                    "rz": True
                }
            }

        return {
            "releases": self.member_end_releases,
            "count": len(member_ids)
        }

    def apply_pinned_one_end(
        self,
        member_id: str,
        pinned_end: str = 'i'
    ) -> Dict[str, Any]:
        """
        施加一端铰接

        Args:
            member_id: 杆件ID
            pinned_end: 铰接端 ('i' 或 'j')

        Returns:
            杆端释放字典
        """
        logger.info(f"Applying pinned end at {pinned_end} for member {member_id}")

        if pinned_end.lower() == 'i':
            release_i = {
                "ux": False,
                "uy": False,
                "uz": False,
                "rx": True,
                "ry": True,
                "rz": True
            }
            release_j = {
                "ux": False,
                "uy": False,
                "uz": False,
                "rx": False,
                "ry": False,
                "rz": False
            }
        else:
            release_i = {
                "ux": False,
                "uy": False,
                "uz": False,
                "rx": False,
                "ry": False,
                "rz": False
            }
            release_j = {
                "ux": False,
                "uy": False,
                "uz": False,
                "rx": True,
                "ry": True,
                "rz": True
            }

        self.member_end_releases[member_id] = {
            "memberId": member_id,
            "releaseI": release_i,
            "releaseJ": release_j
        }

        return {
            "releases": self.member_end_releases,
            "count": 1
        }

    def calculate_effective_lengths(
        self,
        member_ids: List[str] = None,
        default_length_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        计算杆件计算长度

        Args:
            member_ids: 杆件ID列表，如果为None则应用于所有杆件
            default_length_factor: 默认长度系数

        Returns:
            计算长度字典
        """
        if member_ids is None:
            member_ids = [elem.id for elem in self.model.elements if elem.type in ["beam", "column"]]

        logger.info(f"Calculating effective lengths for {len(member_ids)} members")

        for member_id in member_ids:
            # 计算几何长度
            calc_length = self._calculate_member_length(member_id)

            if calc_length is None:
                logger.warning(f"Cannot calculate length for member {member_id}")
                continue

            # 应用长度系数
            effective_length = calc_length * default_length_factor

            # 为两个轴向方向创建计算长度
            self.effective_lengths[f"{member_id}_x"] = {
                "memberId": member_id,
                "direction": "x",
                "calcLength": calc_length,
                "lengthFactor": default_length_factor,
                "effectiveLength": effective_length
            }

            self.effective_lengths[f"{member_id}_y"] = {
                "memberId": member_id,
                "direction": "y",
                "calcLength": calc_length,
                "lengthFactor": default_length_factor,
                "effectiveLength": effective_length
            }

        return {
            "effective_lengths": self.effective_lengths,
            "count": len(member_ids)
        }

    def apply_column_effective_lengths(
        self,
        member_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        应用柱的计算长度 (根据边界条件自动确定长度系数)

        Args:
            member_ids: 柱ID列表

        Returns:
            计算长度字典
        """
        if member_ids is None:
            member_ids = [elem.id for elem in self.model.elements if elem.type == "column"]

        logger.info(f"Applying column effective lengths for {len(member_ids)} columns")

        for member_id in member_ids:
            # 计算几何长度
            calc_length = self._calculate_member_length(member_id)

            if calc_length is None:
                continue

            # 判断边界条件，确定长度系数
            length_factor_i = self._determine_column_length_factor(member_id, 'i')
            length_factor_j = self._determine_column_length_factor(member_id, 'j')

            # 创建弱轴和强轴的计算长度
            self.effective_lengths[f"{member_id}_weak"] = {
                "memberId": member_id,
                "direction": "y",  # 弱轴Y方向
                "calcLength": calc_length,
                "lengthFactor": length_factor_i,
                "effectiveLength": calc_length * length_factor_i
            }

            self.effective_lengths[f"{member_id}_strong"] = {
                "memberId": member_id,
                "direction": "x",  # 强轴X方向
                "calcLength": calc_length,
                "lengthFactor": length_factor_j,
                "effectiveLength": calc_length * length_factor_j
            }

        return {
            "effective_lengths": self.effective_lengths,
            "count": len(member_ids)
        }

    def get_nodal_constraints(self) -> Dict[str, Any]:
        """获取所有节点约束"""
        return self.nodal_constraints

    def get_member_end_releases(self) -> Dict[str, Any]:
        """获取所有杆端释放"""
        return self.member_end_releases

    def get_effective_lengths(self) -> Dict[str, Any]:
        """获取所有计算长度"""
        return self.effective_lengths

    def _calculate_member_length(self, member_id: str) -> float:
        """
        计算杆件几何长度

        Args:
            member_id: 杆件ID

        Returns:
            几何长度
        """
        elem = None
        for e in self.model.elements:
            if e.id == member_id:
                elem = e
                break

        if not elem or len(elem.nodes) < 2:
            return None

        # 获取两端节点坐标
        node_i = None
        node_j = None
        for node in self.model.nodes:
            if node.id == elem.nodes[0]:
                node_i = node
            elif node.id == elem.nodes[1]:
                node_j = node

        if not node_i or not node_j:
            return None

        # 计算距离
        import math
        dx = node_j.x - node_i.x
        dy = node_j.y - node_i.y
        dz = node_j.z - node_i.z
        length = math.sqrt(dx**2 + dy**2 + dz**2)

        return length

    def _determine_column_length_factor(self, member_id: str, end: str) -> float:
        """
        确定柱的计算长度系数 (简化版)

        Args:
            member_id: 杆件ID
            end: 端部 ('i' 或 'j')

        Returns:
            长度系数
        """
        # 简化处理: 检查节点是否有约束
        elem = None
        for e in self.model.elements:
            if e.id == member_id:
                elem = e
                break

        if not elem:
            return 1.0

        node_id = elem.nodes[0] if end == 'i' else elem.nodes[1]

        # 检查节点约束
        constraint = self.nodal_constraints.get(node_id)

        if constraint:
            if constraint["constraintType"] == "fixed":
                return 0.5  # 固定端
            elif constraint["constraintType"] == "pinned":
                return 0.7  # 铰接端
            else:
                return 1.0  # 其他
        else:
            return 1.0  # 无约束


def apply_boundary_conditions(model: StructureModelV2, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    施加边界条件的主函数

    Args:
        model: V2 结构模型
        parameters: 参数字典
            - support_type: 支座类型 (fixed, pinned, roller)
            - node_ids: 节点ID列表 (可选)
            - member_ids: 杆件ID列表 (可选)
            - apply_hinged_ends: 是否施加杆端铰接 (默认 False)
            - calculate_effective_lengths: 是否计算计算长度 (默认 True)

    Returns:
        生成结果
    """
    generator = BoundaryConditionGenerator(model)

    # 参数解析
    support_type = parameters.get("support_type", "fixed")
    node_ids = parameters.get("node_ids")
    member_ids = parameters.get("member_ids")
    apply_hinged_ends = parameters.get("apply_hinged_ends", False)
    calculate_effective_lengths = parameters.get("calculate_effective_lengths", True)
    roller_direction = parameters.get("roller_direction", "y")

    # 施加节点约束
    if support_type == "fixed":
        generator.apply_fixed_support(node_ids)
    elif support_type == "pinned":
        generator.apply_pinned_support(node_ids)
    elif support_type == "roller":
        generator.apply_roller_support(node_ids, roller_direction)

    # 施加杆端释放
    if apply_hinged_ends:
        generator.apply_hinged_member_ends(member_ids)

    # 计算计算长度
    if calculate_effective_lengths:
        if member_ids and all(m.startswith('C') for m in member_ids):
            generator.apply_column_effective_lengths(member_ids)
        else:
            generator.calculate_effective_lengths(member_ids)

    return {
        "status": "success",
        "nodal_constraints": generator.get_nodal_constraints(),
        "member_end_releases": generator.get_member_end_releases(),
        "effective_lengths": generator.get_effective_lengths(),
        "summary": {
            "constraint_count": len(generator.get_nodal_constraints()),
            "release_count": len(generator.get_member_end_releases()),
            "effective_length_count": len(generator.get_effective_lengths()),
            "support_type": support_type
        }
    }

    def apply_elastic_support(
        self,
        node_ids: List[str] = None,
        stiffness_matrix: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        施加弹性支座 (提供刚度约束)

        Args:
            node_ids: 节点ID列表，如果为None则默认基础节点
            stiffness_matrix: 6x6 刚度矩阵字典

        Returns:
            节点约束字典
        """
        if node_ids is None:
            min_z = min(node.z for node in self.model.nodes)
            node_ids = [node.id for node in self.model.nodes if abs(node.z - min_z) < 0.001]

        # 默认刚度矩阵 (对角矩阵)
        if stiffness_matrix is None:
            stiffness_matrix = {
                'kxx': 1e6, 'kyy': 1e6, 'kzz': 1e6,
                'kxx_rot': 1e5, 'kyy_rot': 1e5, 'kzz_rot': 1e5
            }

        logger.info(f"Applying elastic supports to {len(node_ids)} nodes")

        for node_id in node_ids:
            self.nodal_constraints[node_id] = {
                "node_id": node_id,
                "constraint_type": "elastic",
                "restraints": [False, False, False, False, False, False],  # V2 Schema 格式
                "stiffness": stiffness_matrix,
                "extra": {}
            }

        return {
            "constraints": self.nodal_constraints,
            "count": len(node_ids)
        }
