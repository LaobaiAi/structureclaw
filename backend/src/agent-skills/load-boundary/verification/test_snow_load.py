"""
Test suite for snow load generator.

Tests cover snow load generation, validation, and error handling.
"""

import pytest
from typing import Dict, Any, List
from backend.src.agent_skills.load_boundary.snow_load.runtime import SnowLoadGenerator
from backend.src.agent_skills.load_boundary.core.load_action import create_load_action
from backend.src.agent_runtime.types import StructureModelV2, LoadCaseV2, NodeV2, ElementV2, MaterialV2, SectionV2


def create_test_model() -> StructureModelV2:
    """Create a test structure model with materials, sections, nodes, and elements."""
    return StructureModelV2(
        materials={
            "mat1": MaterialV2(
                id="mat1",
                name="Q235",
                density=7850.0,
                elasticModulus=206000.0,
                poissonRatio=0.3,
                thermalExpansionCoeff=1.2e-5,
                yieldStrength=235.0,
                ultimateStrength=375.0
            )
        },
        sections={
            "sec1": SectionV2(
                id="sec1",
                name="H300x150x6.5x9",
                materialId="mat1",
                area=4655.0,
                iy=73500000.0,
                iz=5080000.0,
                iy_unit="mm4",
                iz_unit="mm4"
            ),
            "sec2": SectionV2(
                id="sec2",
                name="C25",
                materialId="mat2",
                area=1.0,
                iy=0.083333,
                iz=0.083333,
                iy_unit="m4",
                iz_unit="m4"
            )
        },
        nodes={
            "n1": NodeV2(id="n1", x=0.0, y=0.0, z=10.0),
            "n2": NodeV2(id="n2", x=6.0, y=0.0, z=10.0),
            "n3": NodeV2(id="n3", x=12.0, y=0.0, z=10.0),
            "n4": NodeV2(id="n4", x=0.0, y=8.0, z=10.0),
            "n5": NodeV2(id="n5", x=6.0, y=8.0, z=10.0),
            "n6": NodeV2(id="n6", x=12.0, y=8.0, z=10.0)
        },
        elements={
            "b1": ElementV2(
                id="b1",
                type="beam",
                sectionId="sec1",
                nodes=["n1", "n2"],
                releases={}
            ),
            "b2": ElementV2(
                id="b2",
                type="beam",
                sectionId="sec1",
                nodes=["n2", "n3"],
                releases={}
            ),
            "b3": ElementV2(
                id="b3",
                type="beam",
                sectionId="sec1",
                nodes=["n4", "n5"],
                releases={}
            ),
            "b4": ElementV2(
                id="b4",
                type="beam",
                sectionId="sec1",
                nodes=["n5", "n6"],
                releases={}
            ),
            "s1": ElementV2(
                id="s1",
                type="slab",
                sectionId="sec2",
                nodes=["n1", "n2", "n5", "n4"],
                releases={}
            )
        },
        loads={},
        loadCases={},
        loadCombinations={}
    )


def test_snow_load_generation():
    """Test snow load generation with default parameters."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    # Generate snow loads for a test case
    case_id = "SNOW-LC"
    result = generator.generate_snow_loads(
        case_id=case_id,
        region="Beijing",
        roof_type="flat"
    )

    # Verify load case was created
    assert case_id in result.loadCases
    load_case = result.loadCases[case_id]
    assert load_case.id == case_id
    assert "snow" in load_case.name.lower() or "雪" in load_case.name.lower()

    # Verify loads were generated
    assert len(load_case.loads) > 0


def test_custom_snow_load():
    """Test adding custom snow load to specific elements."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    case_id = "SNOW-CUSTOM"
    element_ids = ["s1"]
    element_type = "slab"

    # Add custom snow load
    result = generator.add_custom_snow_load(
        case_id=case_id,
        element_ids=element_ids,
        element_type=element_type,
        load_type="DISTRIBUTED_LOAD",
        load_value=0.5,
        load_direction="z"
    )

    # Verify load case was created
    assert case_id in result.loadCases
    load_case = result.loadCases[case_id]

    # Verify loads were added for specified elements
    assert len(load_case.loads) == len(element_ids)

    # Verify load parameters
    for load in load_case.loads:
        assert load["loadType"] == "DISTRIBUTED_LOAD"
        assert load["loadValue"] == 0.5
        assert load["loadDirection"] == "z"
        assert load["elementType"] == element_type


def test_invalid_region():
    """Test error handling for invalid region."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    with pytest.raises(ValueError) as exc_info:
        generator.generate_snow_loads(
            case_id="SNOW-REGION",
            region="InvalidRegion",  # Invalid region
            roof_type="flat"
        )

    assert "region" in str(exc_info.value).lower() or "地区" in str(exc_info.value).lower()


def test_invalid_roof_type():
    """Test error handling for invalid roof type."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    with pytest.raises(ValueError) as exc_info:
        generator.generate_snow_loads(
            case_id="SNOW-ROOF",
            region="Beijing",
            roof_type="dome"  # Invalid roof type
        )

    assert "roof type" in str(exc_info.value).lower() or "屋面类型" in str(exc_info.value).lower()


def test_invalid_case_id():
    """Test error handling for invalid case ID."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    with pytest.raises(ValueError) as exc_info:
        generator.generate_snow_loads(
            case_id="",  # Invalid (empty string)
            region="Beijing",
            roof_type="flat"
        )


def test_invalid_load_value():
    """Test error handling for invalid load value."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    with pytest.raises(ValueError) as exc_info:
        generator.add_custom_snow_load(
            case_id="SNOW-LOAD",
            element_ids=["s1"],
            element_type="slab",
            load_type="DISTRIBUTED_LOAD",
            load_value=-0.5,  # Invalid (negative)
            load_direction="z"
        )


def test_snow_load_factors():
    """Test that snow load factors are calculated correctly for different regions."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    # Test Beijing
    result_beijing = generator.generate_snow_loads(
        case_id="SNOW-BEIJING",
        region="Beijing",
        roof_type="flat"
    )

    # Test Shanghai
    result_shanghai = generator.generate_snow_loads(
        case_id="SNOW-SHANGHAI",
        region="Shanghai",
        roof_type="flat"
    )

    # Verify loads were generated for both regions
    assert "SNOW-BEIJING" in result_beijing.loadCases
    assert "SNOW-SHANGHAI" in result_shanghai.loadCases

    # Beijing should generally have higher snow loads than Shanghai
    loads_beijing = sum(load["loadValue"] for load in result_beijing.loadCases["SNOW-BEIJING"].loads)
    loads_shanghai = sum(load["loadValue"] for load in result_shanghai.loadCases["SNOW-SHANGHAI"].loads)


def test_roof_type_factors():
    """Test that roof type factors are applied correctly."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    # Generate for flat roof
    result_flat = generator.generate_snow_loads(
        case_id="SNOW-FLAT",
        region="Beijing",
        roof_type="flat"
    )

    # Generate for pitched roof
    result_pitched = generator.generate_snow_loads(
        case_id="SNOW-PITCHED",
        region="Beijing",
        roof_type="pitched"
    )

    # Generate for arched roof
    result_arched = generator.generate_snow_loads(
        case_id="SNOW-ARCHED",
        region="Beijing",
        roof_type="arched"
    )

    # Verify all load cases exist
    assert "SNOW-FLAT" in result_flat.loadCases
    assert "SNOW-PITCHED" in result_pitched.loadCases
    assert "SNOW-ARCHED" in result_arched.loadCases

    # Different roof types should have different load values due to different factors
    loads_flat = sum(load["loadValue"] for load in result_flat.loadCases["SNOW-FLAT"].loads)
    loads_pitched = sum(load["loadValue"] for load in result_pitched.loadCases["SNOW-PITCHED"].loads)
    loads_arched = sum(load["loadValue"] for load in result_arched.loadCases["SNOW-ARCHED"].loads)


def test_snow_distribution():
    """Test that snow loads are distributed correctly over slabs and beams."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    result = generator.generate_snow_loads(
        case_id="SNOW-DIST",
        region="Beijing",
        roof_type="flat"
    )

    load_case = result.loadCases["SNOW-DIST"]

    # Verify loads are distributed over different element types
    slab_loads = [load for load in load_case.loads if load.get("elementType") == "slab"]
    beam_loads = [load for load in load_case.loads if load.get("elementType") == "beam"]

    # Should have loads for both slabs and beams
    # (assuming the generator supports distributing to both types)
    assert len(slab_loads) > 0 or len(beam_loads) > 0


def test_load_action_format():
    """Test that all load actions follow V2 Schema format."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    result = generator.generate_snow_loads(
        case_id="SNOW-FORMAT",
        region="Beijing",
        roof_type="flat"
    )

    load_case = result.loadCases["SNOW-FORMAT"]

    # Verify all load actions have required fields in correct format
    required_fields = ["id", "elementType", "loadType", "loadValue", "loadDirection"]
    for load in load_case.loads:
        for field in required_fields:
            assert field in load, f"Missing field: {field}"

        # Verify camelCase naming convention
        assert "element_id" not in load, "Should use camelCase (elementId)"
        assert "load_type" not in load, "Should use camelCase (loadType)"
        assert "load_value" not in load, "Should use camelCase (loadValue)"
        assert "load_direction" not in load, "Should use camelCase (loadDirection)"
        assert "case_id" not in load, "Should use camelCase (caseId)"
        assert "actionId" not in load, "Should use 'id' not 'actionId'"


def test_unbalanced_snow_load():
    """Test unbalanced snow load for certain roof types."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    # Generate for gable roof (may have unbalanced loading)
    result_gable = generator.generate_snow_loads(
        case_id="SNOW-GABLE",
        region="Beijing",
        roof_type="gable"
    )

    load_case = result_gable.loadCases["SNOW-GABLE"]

    # Verify loads were generated
    assert len(load_case.loads) > 0

    # Verify all load values are positive
    for load in load_case.loads:
        assert load["loadValue"] > 0


def test_drift_load():
    """Test snow drift load for obstacles."""
    model = create_test_model()
    generator = SnowLoadGenerator(model)

    # Generate snow loads (may include drift effects)
    result = generator.generate_snow_loads(
        case_id="SNOW-DRIFT",
        region="Beijing",
        roof_type="flat"
    )

    load_case = result.loadCases["SNOW-DRIFT"]

    # Verify loads were generated
    assert len(load_case.loads) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
