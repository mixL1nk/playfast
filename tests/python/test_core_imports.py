"""Test that core API classes and functions are importable and accessible."""


def test_import_entry_point_analysis_classes():
    """Test that entry point analysis classes are importable."""
    from playfast.core import (
        ComponentType,
        EntryPoint,
    )

    assert EntryPoint is not None
    assert ComponentType is not None


def test_import_call_graph_classes():
    """Test that call graph classes are importable."""
    from playfast.core import (
        CallGraph,
        CallPath,
        MethodCall,
    )

    assert CallGraph is not None
    assert CallPath is not None
    assert MethodCall is not None


def test_import_flow_analysis_classes():
    """Test that flow analysis classes are importable."""
    from playfast.core import (
        DataFlow,
        DataFlowAnalyzer,
        Flow,
    )

    assert Flow is not None
    assert DataFlow is not None
    assert DataFlowAnalyzer is not None


def test_import_analysis_functions():
    """Test that analysis functions are importable and callable."""
    from playfast import core

    assert hasattr(core, "analyze_entry_points_from_apk")
    assert callable(core.analyze_entry_points_from_apk)

    assert hasattr(core, "build_call_graph_from_apk")
    assert callable(core.build_call_graph_from_apk)

    assert hasattr(core, "analyze_webview_flows_from_apk")
    assert callable(core.analyze_webview_flows_from_apk)

    assert hasattr(core, "create_webview_analyzer_from_apk")
    assert callable(core.create_webview_analyzer_from_apk)


def test_component_type_enum():
    """Test ComponentType enum values."""
    from playfast.core import ComponentType

    assert hasattr(ComponentType, "Activity")
    assert hasattr(ComponentType, "Service")
    assert hasattr(ComponentType, "BroadcastReceiver")
    assert hasattr(ComponentType, "ContentProvider")
