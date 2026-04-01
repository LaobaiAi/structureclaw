"""
地震荷载技能使用示例 / Seismic Load Skill Usage Examples

演示如何使用地震荷载技能的各种功能
Demonstrates various features of the seismic load skill
"""

from seismic_load import (
    generate_seismic_loads,
    SeismicLoadGenerator,
    WeightCalculationMethod,
    ForceDistributeMethod
)
from structure_protocol.structure_model_v2 import StructureModelV2


# ============================================================================
# 示例1: 基本用法
# Example 1: Basic Usage
# ============================================================================

def example_basic_usage():
    """基本用法示例"""
    print("=" * 60)
    print("示例1: 基本用法 / Example 1: Basic Usage")
    print("=" * 60)

    # 假设已加载模型
    # model = load_model("path/to/model.json")

    # 使用默认参数生成地震荷载
    result = generate_seismic_loads(model, {
        "intensity": 7.0,
        "site_category": "II",
        "design_group": "第二组",
        "seismic_direction": "x"
    })

    print(f"状态: {result['status']}")
    print(f"荷载工况数: {result['summary']['case_count']}")
    print(f"荷载动作数: {result['summary']['action_count']}")
    print(f"底部剪力: {result['calculation_details']['base_shear']:.2f} kN")
    print()


# ============================================================================
# 示例2: 高级用法 - 指定计算方法
# Example 2: Advanced Usage - Specify Calculation Methods
# ============================================================================

def example_advanced_methods():
    """高级用法 - 指定计算方法"""
    print("=" * 60)
    print("示例2: 高级用法 - 指定计算方法")
    print("Example 2: Advanced Usage - Specify Methods")
    print("=" * 60)

    result = generate_seismic_loads(model, {
        "intensity": 7.5,
        "site_category": "II",
        "design_group": "第二组",
        "damping_ratio": 0.05,
        "seismic_direction": "x",
        "case_id": "LC_EX",

        # 指定重量计算方法
        "weight_calculation_method": "from_elements",

        # 指定地震力分配方法
        "force_distribute_method": "by_stiffness",

        # 活载组合值系数
        "live_load_factor": 0.5
    })

    print(f"重量计算方法: {result['summary']['weight_calculation_method']}")
    print(f"力分配方法: {result['summary']['force_distribute_method']}")
    print(f"活载系数: {result['summary']['live_load_factor']}")
    print()


# ============================================================================
# 示例3: 使用生成器类
# Example 3: Using Generator Class
# ============================================================================

def example_generator_class():
    """使用生成器类"""
    print("=" * 60)
    print("示例3: 使用生成器类 / Example 3: Using Generator Class")
    print("=" * 60)

    # 创建生成器，指定计算方法
    generator = SeismicLoadGenerator(
        model,
        weight_calculation_method=WeightCalculationMethod.FROM_ELEMENTS,
        force_distribute_method=ForceDistributeMethod.BY_STIFFNESS
    )

    # 生成地震荷载
    result = generator.generate_seismic_loads(
        intensity=8.0,
        site_category='II',
        design_group='第二组',
        damping_ratio=0.05,
        seismic_direction='y',
        case_id='LC_EY',
        description='Y方向地震作用'
    )

    # 获取荷载工况
    load_cases = generator.get_load_cases()
    load_actions = generator.get_load_actions()

    print(f"荷载工况: {list(load_cases.keys())}")
    print(f"荷载动作数: {len(load_actions)}")
    print()


# ============================================================================
# 示例4: 多方向地震
# Example 4: Multi-Direction Seismic
# ============================================================================

def example_multi_direction():
    """多方向地震"""
    print("=" * 60)
    print("示例4: 多方向地震 / Example 4: Multi-Direction Seismic")
    print("=" * 60)

    directions = ['x', 'y']

    for direction in directions:
        result = generate_seismic_loads(model, {
            "intensity": 7.0,
            "site_category": "II",
            "design_group": "第二组",
            "seismic_direction": direction,
            "case_id": f"LC_E{direction.upper()}",
            "description": f"{direction.upper()}方向地震作用"
        })

        base_shear = result['calculation_details']['base_shear']
        print(f"{direction.upper()}方向底部剪力: {base_shear:.2f} kN")

    print()


# ============================================================================
# 示例5: 不同结构类型
# Example 5: Different Structure Types
# ============================================================================

def example_structure_types():
    """不同结构类型"""
    print("=" * 60)
    print("示例5: 不同结构类型 / Example 5: Different Structure Types")
    print("=" * 60)

    # 框架结构
    print("框架结构 / Frame Structure:")
    result_frame = generate_seismic_loads(model, {
        "intensity": 7.0,
        "site_category": "II",
        "design_group": "第二组",
        "force_distribute_method": "by_stiffness"  # 推荐方法
    })
    print(f"  力分配方法: {result_frame['summary']['force_distribute_method']}")

    # 剪力墙结构
    print("剪力墙结构 / Shear Wall Structure:")
    result_shear = generate_seismic_loads(model, {
        "intensity": 7.0,
        "site_category": "II",
        "design_group": "第二组",
        "force_distribute_method": "by_distance"  # 推荐方法
    })
    print(f"  力分配方法: {result_shear['summary']['force_distribute_method']}")

    print()


# ============================================================================
# 示例6: 比较不同重量计算方法
# Example 6: Compare Weight Calculation Methods
# ============================================================================

def example_compare_weight_methods():
    """比较不同重量计算方法"""
    print("=" * 60)
    print("示例6: 比较重量计算方法")
    print("Example 6: Compare Weight Calculation Methods")
    print("=" * 60)

    methods = [
        "from_model_direct",
        "from_elements",
        "from_floors",
        "default_value"
    ]

    for method in methods:
        try:
            result = generate_seismic_loads(model, {
                "intensity": 7.0,
                "site_category": "II",
                "design_group": "第二组",
                "weight_calculation_method": method
            })

            total_weight = result['calculation_details']['total_weight']
            base_shear = result['calculation_details']['base_shear']

            print(f"{method:25s}: 重量={total_weight:8.2f} kN, 剪力={base_shear:8.2f} kN")
        except Exception as e:
            print(f"{method:25s}: 错误 / Error - {e}")

    print()


# ============================================================================
# 示例7: 比较不同力分配方法
# Example 7: Compare Force Distribution Methods
# ============================================================================

def example_compare_distribute_methods():
    """比较不同力分配方法"""
    print("=" * 60)
    print("示例7: 比较不同力分配方法")
    print("Example 7: Compare Force Distribution Methods")
    print("=" * 60)

    methods = ["by_stiffness", "by_distance", "evenly"]

    for method in methods:
        result = generate_seismic_loads(model, {
            "intensity": 7.0,
            "site_category": "II",
            "design_group": "第二组",
            "force_distribute_method": method
        })

        action_count = result['summary']['action_count']
        print(f"{method:15s}: 荷载动作数 / Load actions = {action_count}")

        # 显示前5个构件的力
        load_actions = result['load_actions'][:5]
        print(f"  前5个构件力 / First 5 element forces:")
        for action in load_actions:
            element_id = action['elementId']
            force = action['loadValue']
            print(f"    {element_id}: {force:.2f} kN")

        print()


# ============================================================================
# 示例8: 添加自定义地震荷载
# Example 8: Add Custom Seismic Loads
# ============================================================================

def example_custom_loads():
    """添加自定义地震荷载"""
    print("=" * 60)
    print("示例8: 添加自定义地震荷载")
    print("Example 8: Add Custom Seismic Loads")
    print("=" * 60)

    generator = SeismicLoadGenerator(model)

    # 先生成标准地震荷载
    result = generator.generate_seismic_loads(
        intensity=7.0,
        site_category='II',
        design_group='第二组',
        seismic_direction='x'
    )

    print(f"标准荷载动作数: {len(result['load_case']['loads'])}")

    # 添加自定义荷载
    generator.add_custom_seismic_load(
        element_id="C1",
        element_type="column",
        load_value=15.5,
        seismic_direction="x",
        case_id="LC_E"
    )

    generator.add_custom_seismic_load(
        element_id="C2",
        element_type="column",
        load_value=18.2,
        seismic_direction="x",
        case_id="LC_E"
    )

    # 获取更新后的荷载动作
    updated_actions = generator.get_load_actions()
    print(f"更新后荷载动作数: {len(updated_actions)}")

    # 显示自定义荷载
    custom_actions = [a for a in updated_actions if a['elementId'] in ['C1', 'C2']]
    for action in custom_actions:
        print(f"  {action['elementId']}: {action['loadValue']:.2f} kN")

    print()


# ============================================================================
# 示例9: 验证参数
# Example 9: Validate Parameters
# ============================================================================

def example_validate_parameters():
    """验证参数"""
    print("=" * 60)
    print("示例9: 验证参数 / Example 9: Validate Parameters")
    print("=" * 60)

    from seismic_load.utils import validate_seismic_parameters

    # 有效参数
    is_valid, errors = validate_seismic_parameters(
        intensity=7.0,
        site_category="II",
        design_group="第二组",
        damping_ratio=0.05,
        live_load_factor=0.5
    )
    print(f"有效参数: {is_valid}")
    if errors:
        for error in errors:
            print(f"  错误 / Error: {error}")

    # 无效参数
    print("\n无效参数测试 / Invalid parameters test:")
    is_valid, errors = validate_seismic_parameters(
        intensity=10.0,  # 无效烈度
        site_category="V",  # 无效场地类别
        design_group="第四组",  # 无效分组
        damping_ratio=0.3,  # 无效阻尼比
        live_load_factor=1.5  # 无效活载系数
    )
    print(f"有效参数: {is_valid}")
    for error in errors:
        print(f"  错误 / Error: {error}")

    print()


# ============================================================================
# 示例10: 格式化结果
# Example 10: Format Results
# ============================================================================

def example_format_results():
    """格式化结果"""
    print("=" * 60)
    print("示例10: 格式化结果 / Example 10: Format Results")
    print("=" * 60)

    from seismic_load.utils import format_seismic_result

    result = generate_seismic_loads(model, {
        "intensity": 7.0,
        "site_category": "II",
        "design_group": "第二组",
        "seismic_direction": "x"
    })

    # 中文格式化
    print("中文格式 / Chinese Format:")
    print(format_seismic_result(result, language='zh'))

    # 英文格式化
    print("\n英文格式 / English Format:")
    print(format_seismic_result(result, language='en'))


# ============================================================================
# 主函数 / Main Function
# ============================================================================

if __name__ == "__main__":
    # 注意: 实际使用时需要加载真实模型
    # Note: In actual usage, load a real model

    # 创建示例模型 (实际使用时替换为真实模型)
    model = create_example_model()

    # 运行所有示例
    example_basic_usage()
    example_advanced_methods()
    example_generator_class()
    example_multi_direction()
    example_structure_types()
    example_compare_weight_methods()
    example_compare_distribute_methods()
    example_custom_loads()
    example_validate_parameters()
    example_format_results()


def create_example_model() -> StructureModelV2:
    """创建示例模型 (用于演示)"""
    # 实际使用时加载真实模型
    # This is just for demonstration
    pass
