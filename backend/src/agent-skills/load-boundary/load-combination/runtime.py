"""
荷载组合技能运行时
Load Combination Skill Runtime
实现荷载组合生成功能，基于 GB50009-2012 和 GB50011-2010
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加核心模块路径
core_path = Path(__file__).parent.parent / "core"
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from load_combination_enhanced import (
    LoadCombinationGenerator,
    CombinationFactor,
    CombinationMethod
)


def generate_load_combinations(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成荷载组合
    
    Args:
        params: 输入参数字典
        
    Returns:
        组合结果字典
    """
    try:
        # 提取输入参数
        load_cases = params.get("load_cases", {})
        combination_type = params.get("combination_type", "uls")
        combination_factors = params.get("combination_factors", {})
        expand_cases = params.get("expand_cases", False)
        include_favorable = params.get("include_favorable", True)
        
        # 验证输入
        if not load_cases:
            return {
                "status": "error",
                "error": "无有效的荷载工况",
                "message": "至少需要提供一个荷载工况才能生成组合"
            }
        
        # 初始化组合系数
        if combination_factors:
            factors = CombinationFactor(**combination_factors)
        else:
            factors = None
        
        # 创建组合生成器
        generator = LoadCombinationGenerator(factors=factors)
        
        # 展开工况（如果需要）
        expanded_cases = {}
        if expand_cases:
            # 将 load_cases 转换为内部格式
            internal_load_cases = {}
            for case_type, case_ids in load_cases.items():
                if case_ids:
                    for case_id in case_ids:
                        internal_load_cases[case_id] = {
                            "id": case_id,
                            "type": case_type.replace("_load", "_load").replace("_", "_"),
                            "description": f"{case_type} {case_id}",
                            "extra": {}
                        }
            
            expanded_cases = generator.expand_load_cases_for_combination(
                internal_load_cases
            )
            
            # 更新 load_cases 使用展开后的工况
            load_cases = {}
            for exp_id, exp_data in expanded_cases.items():
                base_type = exp_data["type"]
                if base_type not in load_cases:
                    load_cases[base_type] = []
                load_cases[base_type].append(exp_id)
        
        # 提取各类荷载工况ID
        dead_load_ids = load_cases.get("dead_load_load", load_cases.get("dead_load", []))
        live_load_ids = load_cases.get("live_load_load", load_cases.get("live_load", []))
        wind_load_ids = load_cases.get("wind_load_load", load_cases.get("wind_load", []))
        seismic_load_ids = load_cases.get("seismic_load_load", load_cases.get("seismic_load", []))
        crane_load_ids = load_cases.get("crane_load_load", load_cases.get("crane_load", []))
        temp_load_ids = load_cases.get("temperature_load_load", load_cases.get("temperature_load", []))
        
        # 根据类型生成组合
        all_combinations = []
        
        if combination_type in ["uls", "all"]:
            result = generator.generate_uls_combinations(
                dead_load_ids=dead_load_ids,
                live_load_ids=live_load_ids,
                wind_load_ids=wind_load_ids,
                seismic_load_ids=seismic_load_ids,
                crane_load_ids=crane_load_ids,
                temp_load_ids=temp_load_ids,
                include_favorable=include_favorable
            )
            all_combinations.extend(result["combinations"])
        
        if combination_type in ["sls", "all"]:
            result = generator.generate_sls_combinations(
                dead_load_ids=dead_load_ids,
                live_load_ids=live_load_ids,
                wind_load_ids=wind_load_ids,
                seismic_load_ids=seismic_load_ids
            )
            all_combinations.extend(result["combinations"])
        
        if combination_type in ["seismic", "all"]:
            result = generator.generate_seismic_combinations(
                dead_load_ids=dead_load_ids,
                live_load_ids=live_load_ids,
                seismic_load_ids=seismic_load_ids,
                crane_load_ids=crane_load_ids
            )
            all_combinations.extend(result["combinations"])
        
        # 统计组合类型
        summary = {
            "total": len(all_combinations),
            "uls": sum(1 for c in all_combinations if c["type"] == "uls"),
            "sls": sum(1 for c in all_combinations if c["type"] == "sls"),
            "seismic": sum(1 for c in all_combinations if c["type"] == "seismic")
        }
        
        return {
            "status": "success",
            "combinations": all_combinations,
            "expanded_cases": expanded_cases if expand_cases else None,
            "summary": summary,
            "factors": generator.factors.to_dict() if generator.factors else None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"生成荷载组合时发生错误: {str(e)}"
        }


def expand_load_cases(load_cases: Dict[str, Any]) -> Dict[str, Any]:
    """
    展开工况
    
    Args:
        load_cases: 荷载工况字典
        
    Returns:
        展开后的工况字典
    """
    try:
        generator = LoadCombinationGenerator()
        return generator.expand_load_cases_for_combination(load_cases)
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"展开工况时发生错误: {str(e)}"
        }


def process_custom_combinations(
    custom_load_ids: List[str],
    combination_method: str,
    base_combinations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    处理自定义工况组合
    
    Args:
        custom_load_ids: 自定义荷载工况ID列表
        combination_method: 组合方式 (superpose/rotate/combine)
        base_combinations: 基础组合列表
        
    Returns:
        处理后的组合列表
    """
    try:
        method = CombinationMethod(combination_method.lower())
        generator = LoadCombinationGenerator()
        
        result = generator.process_custom_load_case_combination(
            custom_load_ids=custom_load_ids,
            combination_method=method,
            base_combinations=base_combinations
        )
        
        return {
            "status": "success",
            "combinations": result,
            "count": len(result)
        }
    
    except ValueError as e:
        return {
            "status": "error",
            "error": f"无效的组合方式: {combination_method}",
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"处理自定义组合时发生错误: {str(e)}"
        }


def generate_special_member_combinations(
    load_cases: Dict[str, Any],
    member_type: str = "wind_column"
) -> Dict[str, Any]:
    """
    生成特殊构件组合
    
    Args:
        load_cases: 荷载工况字典
        member_type: 特殊构件类型
        
    Returns:
        组合结果字典
    """
    try:
        generator = LoadCombinationGenerator()
        
        dead_load_ids = load_cases.get("dead_load", [])
        live_load_ids = load_cases.get("live_load", [])
        wind_load_ids = load_cases.get("wind_load", [])
        
        result = generator.generate_special_member_combinations(
            dead_load_ids=dead_load_ids,
            live_load_ids=live_load_ids,
            wind_load_ids=wind_load_ids,
            member_type=member_type
        )
        
        return {
            "status": "success",
            "combinations": result["combinations"],
            "count": result["count"]
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"生成特殊构件组合时发生错误: {str(e)}"
        }


def create_custom_combination(
    factors: Dict[str, float],
    description: str = "",
    combination_type: str = "uls",
    code_reference: str = "custom"
) -> Dict[str, Any]:
    """
    创建自定义组合
    
    Args:
        factors: 荷载系数字典
        description: 组合描述
        combination_type: 组合类型
        code_reference: 规范条文号
        
    Returns:
        组合字典
    """
    try:
        generator = LoadCombinationGenerator()
        combo = generator.create_custom_combination(
            factors=factors,
            description=description,
            combination_type=combination_type,
            code_reference=code_reference
        )
        
        return {
            "status": "success",
            "combination": combo
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"创建自定义组合时发生错误: {str(e)}"
        }


# 主函数入口
if __name__ == "__main__":
    # 测试示例
    
    # 示例 1: 基础 ULS 组合
    print("=" * 60)
    print("示例 1: 基础 ULS 组合")
    print("=" * 60)
    
    result1 = generate_load_combinations({
        "load_cases": {
            "dead_load": ["LC_DE"],
            "live_load": ["LC_LL"],
            "wind_load": ["LC_WX"]
        },
        "combination_type": "uls"
    })
    
    print(f"状态: {result1['status']}")
    print(f"组合数量: {result1.get('summary', {}).get('total', 0)}")
    print("\n生成的组合:")
    for combo in result1.get("combinations", [])[:3]:
        print(f"  - {combo['id']}: {combo['description']}")
        print(f"    系数: {combo['factors']}")
    
    # 示例 2: 包含地震的组合
    print("\n" + "=" * 60)
    print("示例 2: 包含地震的组合")
    print("=" * 60)
    
    result2 = generate_load_combinations({
        "load_cases": {
            "dead_load": ["LC_DE"],
            "live_load": ["LC_LL"],
            "seismic_load": ["LC_EX"]
        },
        "combination_type": "all"
    })
    
    print(f"状态: {result2['status']}")
    print(f"组合数量: {result2.get('summary', {})}")
    
    # 示例 3: 展开工况
    print("\n" + "=" * 60)
    print("示例 3: 展开工况")
    print("=" * 60)
    
    result3 = generate_load_combinations({
        "load_cases": {
            "dead_load": ["LC_DE"],
            "live_load": ["LC_LL"],
            "wind_load": ["LC_WX"]
        },
        "combination_type": "uls",
        "expand_cases": True
    })
    
    print(f"状态: {result3['status']}")
    print(f"展开工况数量: {len(result3.get('expanded_cases', {}))}")
    print("\n展开的工况:")
    for exp_id, exp_data in list(result3.get("expanded_cases", {}).items())[:3]:
        print(f"  - {exp_id}: {exp_data['description']}")
    
    # 示例 4: 自定义组合系数
    print("\n" + "=" * 60)
    print("示例 4: 自定义组合系数")
    print("=" * 60)
    
    result4 = generate_load_combinations({
        "load_cases": {
            "dead_load": ["LC_DE"],
            "live_load": ["LC_LL"]
        },
        "combination_factors": {
            "gamma_g": 1.35,
            "gamma_q": 1.4
        }
    })
    
    print(f"状态: {result4['status']}")
    print(f"使用的系数: {result4.get('factors', {})}")
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)
