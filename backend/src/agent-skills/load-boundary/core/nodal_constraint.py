"""
节点约束管理模块
提供节点约束的 CRUD 操作
对齐 V2 Schema NodeV2.restraints
"""

from typing import Any, Dict, List, Optional


class NodalConstraint:
    """节点约束类 - 对齐 V2 Schema"""

    def __init__(
        self,
        node_id: str,
        constraint_type: str,
        restrained_dofs: Optional[Dict[str, bool]] = None,
        restraints: Optional[List[bool]] = None,
        stiffness: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        初始化节点约束

        Args:
            node_id: 节点ID
            constraint_type: 约束类型 (fixed, pinned, sliding, elastic)
            restrained_dofs: 约束的自由度字典 {ux: bool, uy: bool, ...}
            restraints: V2 Schema 格式的约束列表 [ux, uy, uz, rx, ry, rz]
            stiffness: 弹簧刚度矩阵 (仅 elastic 类型)
            extra: 扩展字段 (对齐 V2 Schema)
        """
        self.node_id = node_id
        self.constraint_type = constraint_type
        self.restrained_dofs = restrained_dofs or {}
        self.restraints = restraints  # V2 Schema 格式
        self.stiffness = stiffness
        self.extra: Dict[str, Any] = extra or {}

    def create_nodal_constraint(self) -> Dict[str, Any]:
        """创建节点约束"""
        return self.to_dict()

    def modify_nodal_constraint(self, **kwargs) -> Dict[str, Any]:
        """修改节点约束"""
        if 'restraints' in kwargs:
            self.restraints = kwargs['restraints']
        if 'stiffness' in kwargs:
            self.stiffness = kwargs['stiffness']
        if 'extra' in kwargs:
            self.extra = kwargs['extra']
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - 使用下划线命名，对齐 V2 Schema"""
        result = {
            "node_id": self.node_id,
            "constraint_type": self.constraint_type,
            "restrained_dofs": self.restrained_dofs,
            "extra": self.extra
        }
        if self.restraints is not None:
            result["restraints"] = self.restraints
        if self.stiffness is not None:
            result["stiffness"] = self.stiffness
        return result
