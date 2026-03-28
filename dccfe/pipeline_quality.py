"""
Pipeline Quality Integration: Seamlessly integrate system quality analysis into DCCFE pipeline.

This module adds quality monitoring to the standard pipeline execution flow.
"""

from __future__ import annotations

from typing import Any, Dict

import networkx as nx

from .system_quality import generate_quality_report, validate_consistency


def enhance_pipeline_output(
    pipeline_result: Dict[str, Any],
    enable_quality_report: bool = True,
) -> Dict[str, Any]:
    """
    Enhance pipeline output with quality analysis.
    
    Args:
        pipeline_result: Output from run_dccfe_pipeline
        enable_quality_report: Whether to include quality report
        
    Returns:
        Enhanced pipeline result with quality analysis
    """
    enhanced = dict(pipeline_result)

    if not enable_quality_report:
        return enhanced

    # Extract graph from pipeline result
    try:
        # Try different possible graph keys
        graph = None
        for key in ['graph_after_reasoning', 'simulated_state', 'post_propagation_state']:
            if key in pipeline_result and hasattr(pipeline_result[key], 'to_dict'):
                # It's a DataFrame, skip
                continue
            if key in pipeline_result and isinstance(pipeline_result[key], nx.Graph):
                graph = pipeline_result[key]
                break
        
        # If no graph found, reconstruct from nodes in state DataFrames
        if graph is None:
            # Try to get graph from post_propagation_state if available
            if 'post_propagation_state' in pipeline_result:
                df = pipeline_result['post_propagation_state']
                if not df.empty:
                    graph = _dataframe_to_graph(df, pipeline_result.get('initial_state'))

        if graph is None:
            # Fallback: create minimal graph
            return enhanced

        # Generate quality report
        quality_report = generate_quality_report(graph)

        # Check consistency
        consistency_check = validate_consistency(graph, max_risk_jump=0.20)

        enhanced["quality_report"] = quality_report
        enhanced["system_quality"] = {
            "status": "healthy" if quality_report["best_action"] else "unknown",
            "system_classification": quality_report["system_stability"]["classification"],
            "cascade_activity": quality_report["cascade_summary"]["cascade_activity"],
            "consistency_score": consistency_check["consistency_score"],
            "anomaly_count": consistency_check["anomaly_count"],
            "behavior_summary": {
                "escalating_nodes": sum(
                    1 for b in quality_report["node_behavior"] if b["trend"] == "escalating"
                ),
                "recovering_nodes": sum(
                    1 for b in quality_report["node_behavior"] if b["trend"] == "recovering"
                ),
                "stable_nodes": sum(
                    1 for b in quality_report["node_behavior"] if b["trend"] == "stable"
                ),
            },
        }

    except Exception as e:
        # Graceful fallback if quality report generation fails
        enhanced["quality_report"] = None
        enhanced["system_quality"] = {
            "status": "unavailable",
            "error": str(e),
        }

    return enhanced


def _dataframe_to_graph(df_with_state: Any, df_initial: Any = None) -> nx.Graph | None:
    """Reconstruct networkx graph from DataFrame state."""
    try:
        graph = nx.Graph()
        
        if hasattr(df_with_state, 'empty') and df_with_state.empty:
            return None
        
        if hasattr(df_with_state, 'iterrows'):
            for idx, row in df_with_state.iterrows():
                node_id = str(row.get('user_id', row.get('node', idx)))
                attrs = {
                    'risk': float(row.get('risk', 0.0)),
                    'income': float(row.get('income', 0.0)),
                    'activity': float(row.get('activity', 0.0)),
                    'transaction_variability': float(row.get('transaction_variability', 0.0)),
                }
                
                # Try to preserve risk_history from initial state
                if df_initial is not None and hasattr(df_initial, 'iterrows'):
                    for _, init_row in df_initial.iterrows():
                        if str(init_row.get('user_id', init_row.get('node'))) == node_id:
                            hist = init_row.get('risk_history', [attrs['risk']])
                            attrs['risk_history'] = list(hist) if hist else [attrs['risk']]
                            break
                if 'risk_history' not in attrs:
                    attrs['risk_history'] = [attrs['risk']]
                
                graph.add_node(node_id, **attrs)
        
        return graph if graph.number_of_nodes() > 0 else None
    except Exception:
        return None


def print_quality_summary(enhanced_result: Dict[str, Any]) -> None:
    """Print human-readable quality summary."""
    if "system_quality" not in enhanced_result:
        return

    sq = enhanced_result["system_quality"]
    print("\n" + "-" * 70)
    print("SYSTEM QUALITY SUMMARY")
    print("-" * 70)
    print(f"Status: {sq.get('status', 'unknown')}")
    print(f"System Classification: {sq.get('system_classification', 'unknown')}")
    print(f"Cascade Activity: {sq.get('cascade_activity', 'unknown')}")
    print(f"Consistency Score: {sq.get('consistency_score', 'N/A'):.4f}")
    print(f"Anomalies Detected: {sq.get('anomaly_count', 0)}")

    behavior = sq.get("behavior_summary", {})
    if behavior:
        print(f"\nNode Behaviors:")
        print(f"  Escalating: {behavior.get('escalating_nodes', 0)}")
        print(f"  Recovering: {behavior.get('recovering_nodes', 0)}")
        print(f"  Stable: {behavior.get('stable_nodes', 0)}")

    if "quality_report" in enhanced_result and enhanced_result["quality_report"]:
        report = enhanced_result["quality_report"]
        if report.get("best_action"):
            best = report["best_action"]
            print(f"\nRecommended Action:")
            print(f"  Target: {best['target']}")
            print(f"  Confidence: {best['confidence']:.4f}")
            print(f"  Reason: {best['reason']}")
    
    print("-" * 70 + "\n")
