"""
System Presentation Module: Clean, structured, professional output formatting.

Transforms raw system data into clear, human-readable, professionally formatted results.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, List, Tuple

import networkx as nx


# ============================================================================
# RISK CLASSIFICATION
# ============================================================================


def classify_risk(score: float) -> str:
    """
    Classify risk score into human-readable category.
    
    Args:
        score: Risk score [0.0, 1.0]
        
    Returns:
        "low", "medium", or "high"
    """
    score = max(0.0, min(1.0, float(score)))
    if score < 0.3:
        return "low"
    elif score < 0.7:
        return "medium"
    else:
        return "high"


def get_risk_color(score: float) -> str:
    """Get hex color for risk score for visualization."""
    category = classify_risk(score)
    colors = {
        "low": "#2ecc71",      # Green
        "medium": "#f39c12",   # Orange
        "high": "#e74c3c",     # Red
    }
    return colors.get(category, "#95a5a6")


# ============================================================================
# STRUCTURED NODE OUTPUT
# ============================================================================


@dataclass
class NodeResult:
    """Structured result for a single node."""

    node_id: str
    final_risk: float
    ml_risk: float
    rule_risk: float
    risk_level: str  # low/medium/high
    contributions: Dict[str, float]  # income, activity, variability, neighbor_influence
    centrality: Dict[str, float]  # degree, betweenness, eigenvector
    trend: str  # increasing/decreasing/stable
    short_summary: str
    detailed_explanation: str
    explanation: str


def compute_confidence_label(
    ml_accuracy: float,
    prediction_consistency: float,
) -> str:
    """Compute confidence label from model accuracy and prediction consistency."""
    score = (max(0.0, min(1.0, ml_accuracy)) * 0.6) + (max(0.0, min(1.0, prediction_consistency)) * 0.4)
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "moderate"
    return "low"


def _estimate_prediction_consistency(graph: nx.Graph) -> float:
    """Estimate prediction consistency from risk history smoothness across nodes."""
    smoothness_scores: List[float] = []
    for node in graph.nodes:
        history = list(graph.nodes[str(node)].get("risk_history", []))
        if len(history) < 2:
            smoothness_scores.append(1.0)
            continue
        deltas = [abs(history[i] - history[i - 1]) for i in range(1, len(history))]
        avg_jump = sum(deltas) / len(deltas) if deltas else 0.0
        smoothness_scores.append(max(0.0, min(1.0, 1.0 - (avg_jump / 0.25))))
    return mean(smoothness_scores) if smoothness_scores else 1.0


def one_glance_system_summary(
    graph: nx.Graph,
    ml_accuracy: float = 0.78,
    prediction_consistency: float | None = None,
) -> Dict[str, Any]:
    """Return concise one-glance overview for UI and pipeline output."""
    if graph.number_of_nodes() == 0:
        return {
            "system_state": "stable",
            "average_risk": 0.0,
            "high_risk_nodes": 0,
            "critical_node": None,
            "confidence": "low",
            "message": "No nodes available for assessment.",
        }

    risks = {str(n): float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes}
    values = list(risks.values())
    avg_risk = sum(values) / len(values)
    high_risk_nodes = sum(1 for r in values if r >= 0.7)
    critical_node = max(risks, key=risks.get)

    all_low = all(r < 0.3 for r in values)
    all_high = all(r >= 0.7 for r in values)

    if all_low:
        state = "stable"
        message = "All nodes are currently low risk."
    elif all_high:
        state = "critical"
        message = "All nodes are currently high risk."
    elif avg_risk < 0.4:
        state = "stable"
        message = "System risk remains low overall."
    elif avg_risk > 0.65:
        state = "critical"
        message = "System risk is elevated and requires intervention."
    else:
        state = "fragile"
        message = "System is moderately vulnerable and should be monitored."

    component_messages: List[str] = []
    if not nx.is_connected(graph):
        components = [list(c) for c in nx.connected_components(graph)]
        for idx, comp in enumerate(components, start=1):
            comp_risks = [float(graph.nodes[n].get("risk", 0.0)) for n in comp]
            comp_avg = sum(comp_risks) / len(comp_risks)
            comp_high = sum(1 for r in comp_risks if r >= 0.7)
            component_messages.append(
                f"Component {idx}: avg risk {comp_avg:.1%}, high-risk nodes {comp_high}."
            )
        message += " Graph is disconnected; component-level analysis applied."

    consistency = prediction_consistency if prediction_consistency is not None else _estimate_prediction_consistency(graph)
    confidence = compute_confidence_label(ml_accuracy=ml_accuracy, prediction_consistency=consistency)

    return {
        "system_state": state,
        "average_risk": round(avg_risk, 4),
        "high_risk_nodes": int(high_risk_nodes),
        "critical_node": critical_node,
        "confidence": confidence,
        "message": message,
        "component_analysis": component_messages,
    }


def format_node_result(
    node: str,
    graph: nx.Graph,
    ml_risk: float | None = None,
    rule_risk: float | None = None,
) -> NodeResult:
    """
    Format a single node into structured result.
    
    Args:
        node: Node ID
        graph: NetworkX graph with node attributes
        ml_risk: ML-based risk score (optional)
        rule_risk: Rule-based risk score (optional)
        
    Returns:
        NodeResult with all structured data
    """
    node_id = str(node)
    attrs = graph.nodes[node_id]

    # Risk scores
    final_risk = float(attrs.get("risk", 0.0))
    if ml_risk is None:
        ml_risk = final_risk
    if rule_risk is None:
        rule_risk = final_risk
    ml_risk = max(0.0, min(1.0, ml_risk))
    rule_risk = max(0.0, min(1.0, rule_risk))
    final_risk = max(0.0, min(1.0, final_risk))

    risk_level = classify_risk(final_risk)

    # Contributions
    income = float(attrs.get("income", 0.0))
    activity = float(attrs.get("activity", 0.0))
    variability = float(attrs.get("transaction_variability", 0.0))

    income_contrib = max(0.0, min(1.0, 1.0 - (income / 8000.0)))
    activity_contrib = max(0.0, min(1.0, 1.0 - activity))
    var_contrib = max(0.0, min(1.0, variability))

    # Neighbor influence
    neighbors = list(graph.neighbors(node_id))
    if neighbors:
        neighbor_risks = [float(graph.nodes[n].get("risk", 0.0)) for n in neighbors]
        neighbor_influence = sum(neighbor_risks) / len(neighbor_risks)
    else:
        neighbor_influence = 0.0

    contributions = {
        "income": round(income_contrib, 4),
        "activity": round(activity_contrib, 4),
        "variability": round(var_contrib, 4),
        "neighbor_influence": round(neighbor_influence, 4),
    }

    # Centrality metrics
    degree = nx.degree_centrality(graph).get(node_id, 0.0)
    try:
        betweenness = nx.betweenness_centrality(graph).get(node_id, 0.0)
    except:
        betweenness = 0.0

    try:
        eigenvector = nx.eigenvector_centrality(graph, max_iter=100).get(node_id, 0.0)
    except:
        eigenvector = 0.0

    centrality = {
        "degree": round(degree, 4),
        "betweenness": round(betweenness, 4),
        "eigenvector": round(eigenvector, 4),
    }

    # Trend
    history = list(attrs.get("risk_history", [final_risk]))
    if len(history) >= 2:
        change = history[-1] - history[-2]
        if change > 0.05:
            trend = "increasing"
        elif change < -0.05:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Short + detailed explanation
    short_summary = _generate_short_summary(graph, node_id, contributions, final_risk)
    detailed_explanation = _generate_clean_explanation(node_id, graph, contributions, final_risk)
    explanation = detailed_explanation

    return NodeResult(
        node_id=node_id,
        final_risk=round(final_risk, 4),
        ml_risk=round(ml_risk, 4),
        rule_risk=round(rule_risk, 4),
        risk_level=risk_level,
        contributions=contributions,
        centrality=centrality,
        trend=trend,
        short_summary=short_summary,
        detailed_explanation=detailed_explanation,
        explanation=explanation,
    )


def format_node_results(
    graph: nx.Graph,
    ml_risks: Dict[str, float] | None = None,
    rule_risks: Dict[str, float] | None = None,
) -> List[Dict[str, Any]]:
    """Format all nodes into structured results."""
    ml_risks = ml_risks or {}
    rule_risks = rule_risks or {}

    results = []
    for node in graph.nodes:
        node_id = str(node)
        result = format_node_result(
            node_id,
            graph,
            ml_risk=ml_risks.get(node_id),
            rule_risk=rule_risks.get(node_id),
        )
        results.append({
            "node_id": result.node_id,
            "final_risk": result.final_risk,
            "ml_risk": result.ml_risk,
            "rule_risk": result.rule_risk,
            "risk_level": result.risk_level,
            "contributions": result.contributions,
            "centrality": result.centrality,
            "trend": result.trend,
            "short_summary": result.short_summary,
            "detailed_explanation": result.detailed_explanation,
            "explanation": result.explanation,
        })

    # Sort by risk (highest first)
    results.sort(key=lambda r: r["final_risk"], reverse=True)
    return results


# ============================================================================
# CLEAN EXPLANATION ENGINE
# ============================================================================


def _generate_clean_explanation(
    node: str,
    graph: nx.Graph,
    contributions: Dict[str, float],
    final_risk: float,
) -> str:
    """
    Generate clean, human-readable explanation.
    
    No raw numbers, natural language, combined factors.
    """
    node_id = str(node)
    attrs = graph.nodes[node_id]
    income = float(attrs.get("income", 0.0))
    activity = float(attrs.get("activity", 0.0))

    # Primary cause
    primary = ""
    if income < 2500:
        primary = "Income is significantly low"
    elif income < 3500:
        primary = "Income is moderate to low"
    elif income < 5000:
        primary = "Income is moderate"
    else:
        primary = "Income is reasonably stable"

    if activity < 0.35:
        primary += " and financial activity is very limited"
    elif activity < 0.6:
        primary += " and activity is somewhat limited"
    else:
        primary += " with reasonable activity"

    # Secondary influence
    neighbor_influence = contributions.get("neighbor_influence", 0.0)
    secondary = ""
    if neighbor_influence > 0.65:
        secondary = "Connected parties show significant instability. "
    elif neighbor_influence > 0.45:
        secondary = "Some connected parties are experiencing instability. "
    else:
        secondary = "Connected parties are generally stable. "

    # System impact
    if final_risk > 0.75:
        impact = "This represents a substantial risk to the financial network."
    elif final_risk > 0.5:
        impact = "This poses a moderate risk to network stability."
    else:
        impact = "This maintains reasonable stability in the network."

    explanation = f"{primary}. {secondary}{impact}"
    return explanation.strip()


def _generate_short_summary(
    graph: nx.Graph,
    node_id: str,
    contributions: Dict[str, float],
    final_risk: float,
) -> str:
    """Generate one-line summary without raw numeric values."""
    attrs = graph.nodes[node_id]
    income = float(attrs.get("income", 0.0))
    activity = float(attrs.get("activity", 0.0))
    neighbor_influence = contributions.get("neighbor_influence", 0.0)

    drivers: List[str] = []
    if income < 3000:
        drivers.append("low income")
    if activity < 0.45:
        drivers.append("limited activity")
    if neighbor_influence > 0.6:
        drivers.append("strong neighbor influence")

    if not drivers:
        if final_risk >= 0.7:
            return "High risk driven by combined systemic pressures."
        if final_risk >= 0.3:
            return "Moderate risk with mixed behavioral and network signals."
        return "Low risk supported by stable personal and network conditions."

    prefix = "High risk" if final_risk >= 0.7 else "Moderate risk" if final_risk >= 0.3 else "Low risk"
    if len(drivers) == 1:
        return f"{prefix} due to {drivers[0]}."
    if len(drivers) == 2:
        return f"{prefix} due to {drivers[0]} and {drivers[1]}."
    return f"{prefix} due to {drivers[0]}, {drivers[1]}, and {drivers[2]}."


def generate_clean_explanation(node: str, graph: nx.Graph) -> str:
    """Generate clean explanation for a node."""
    node_id = str(node)
    attrs = graph.nodes[node_id]
    final_risk = float(attrs.get("risk", 0.0))

    neighbors = list(graph.neighbors(node_id))
    if neighbors:
        neighbor_risks = [float(graph.nodes[n].get("risk", 0.0)) for n in neighbors]
        neighbor_influence = sum(neighbor_risks) / len(neighbor_risks) if neighbors else 0.0
    else:
        neighbor_influence = 0.0

    contributions = {
        "neighbor_influence": neighbor_influence,
    }

    return _generate_clean_explanation(node_id, graph, contributions, final_risk)


# ============================================================================
# GLOBAL SYSTEM SUMMARY
# ============================================================================


def compute_global_summary(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute system-level summary with clean classification.
    
    Returns:
        {
            "average_risk": float,
            "high_risk_nodes": int,
            "most_critical_node": str,
            "system_state": "stable" / "fragile" / "critical",
            "assessment": str,
        }
    """
    if graph.number_of_nodes() == 0:
        return {
            "average_risk": 0.0,
            "high_risk_nodes": 0,
            "most_critical_node": None,
            "critical_node": None,
            "system_state": "stable",
            "confidence": "low",
            "assessment": "No nodes in system.",
        }

    risks = {str(n): float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes}
    avg_risk = sum(risks.values()) / len(risks)
    high_risk = sum(1 for r in risks.values() if r > 0.7)
    most_critical = max(risks, key=risks.get) if risks else None

    all_low = all(r < 0.3 for r in risks.values())
    all_high = all(r >= 0.7 for r in risks.values())

    if all_low:
        state = "stable"
        assessment = "All nodes are low risk."
    elif all_high:
        state = "critical"
        assessment = "All nodes are high risk."
    elif avg_risk < 0.4:
        state = "stable"
        assessment = "Network is stable with low average risk."
    elif avg_risk > 0.65:
        state = "critical"
        assessment = f"Network is critical with high average risk ({avg_risk:.2%})."
    else:
        state = "fragile"
        assessment = f"Network is fragile with moderate risk ({avg_risk:.2%})."

    concise = one_glance_system_summary(graph)

    return {
        "average_risk": round(avg_risk, 4),
        "high_risk_nodes": high_risk,
        "most_critical_node": most_critical,
        "critical_node": most_critical,
        "system_state": state,
        "confidence": concise.get("confidence", "low"),
        "assessment": assessment,
        "component_analysis": concise.get("component_analysis", []),
    }


# ============================================================================
# INTERVENTION OUTPUT CLEANUP
# ============================================================================


def format_intervention(
    target_node: str,
    risk_reduction: float,
    nodes_affected: int,
    effectiveness_score: float,
) -> Dict[str, Any]:
    """
    Format intervention recommendation cleanly.
    
    Args:
        target_node: Node to intervene on
        risk_reduction: Reduction in total network risk
        nodes_affected: Number of nodes benefiting
        effectiveness_score: Score [0-1]
        
    Returns:
        Structured intervention output
    """
    if effectiveness_score > 0.65:
        impact = "high"
    elif effectiveness_score > 0.35:
        impact = "medium"
    else:
        impact = "low"

    connectivity_phrase = (
        "high connectivity makes this node a strong risk amplifier"
        if nodes_affected >= 3
        else "this node has meaningful local influence"
        if nodes_affected >= 1
        else "this node is locally isolated"
    )

    reason = f"Intervene on {target_node} because {connectivity_phrase}. "
    reason += f"This action is expected to lower immediate risk pressure and improve neighbor stability. "
    if nodes_affected > 1:
        reason += f"Estimated downstream benefit includes stabilization of {nodes_affected} connected nodes and stronger overall system resilience."
    else:
        reason += "Estimated downstream benefit is localized but supports overall system resilience."

    return {
        "recommended_node": target_node,
        "risk_reduction": round(risk_reduction, 4),
        "nodes_affected": nodes_affected,
        "expected_impact": impact,
        "confidence": round(effectiveness_score, 4),
        "reason": reason,
    }


def format_before_after_comparison(
    before_graph: nx.Graph,
    after_graph: nx.Graph,
) -> Dict[str, Any]:
    """Format before vs after intervention comparison."""
    before_risks = [float(before_graph.nodes[n].get("risk", 0.0)) for n in before_graph.nodes]
    after_risks = [float(after_graph.nodes[n].get("risk", 0.0)) for n in after_graph.nodes]

    before_avg = sum(before_risks) / len(before_risks) if before_risks else 0.0
    after_avg = sum(after_risks) / len(after_risks) if after_risks else 0.0

    before_high = sum(1 for r in before_risks if r >= 0.7)
    after_high = sum(1 for r in after_risks if r >= 0.7)

    reduction = max(0.0, before_avg - after_avg)
    stabilized = max(0, before_high - after_high)
    pct_change = (reduction / before_avg) if before_avg > 1e-9 else 0.0

    return {
        "before": {
            "average_risk": round(before_avg, 4),
            "high_risk_nodes": int(before_high),
        },
        "after": {
            "average_risk": round(after_avg, 4),
            "high_risk_nodes": int(after_high),
        },
        "improvement": {
            "risk_reduction": round(reduction, 4),
            "nodes_stabilized": int(stabilized),
            "percentage_change": round(pct_change, 4),
        },
    }


# ============================================================================
# SIMULATION TIMELINE OUTPUT
# ============================================================================


@dataclass
class SimulationStep:
    """Single step in simulation timeline."""

    time_step: int
    node_states: List[Dict[str, Any]]
    avg_risk: float
    system_state: str


def format_simulation_step(
    step: int,
    graph: nx.Graph,
) -> Dict[str, Any]:
    """Format a single simulation step."""
    risks = {str(n): float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes}
    avg_risk = sum(risks.values()) / len(risks) if risks else 0.0

    node_states = [
        {
            "id": node_id,
            "risk": round(risk, 4),
            "level": classify_risk(risk),
        }
        for node_id, risk in sorted(risks.items(), key=lambda x: x[1], reverse=True)
    ]

    if avg_risk < 0.4:
        state = "stable"
    elif avg_risk > 0.65:
        state = "critical"
    else:
        state = "fragile"

    return {
        "time_step": step,
        "node_states": node_states,
        "average_risk": round(avg_risk, 4),
        "system_state": state,
    }


# ============================================================================
# BLOCKCHAIN LOG CLEANUP
# ============================================================================


def format_blockchain_event(
    event_type: str,
    summary: str,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Format blockchain event for readable logging.
    
    Args:
        event_type: "propagation", "simulation", "intervention", etc.
        summary: Human-readable summary
        details: Additional details dict
        
    Returns:
        Formatted event
    """
    return {
        "event": event_type,
        "summary": summary,
        "details": details or {},
    }


# ============================================================================
# FINAL COMPREHENSIVE REPORT
# ============================================================================


def generate_final_report(
    graph: nx.Graph,
    ml_risks: Dict[str, float] | None = None,
    rule_risks: Dict[str, float] | None = None,
    intervention_target: str | None = None,
    intervention_effectiveness: float = 0.0,
    simulation_steps: List[Dict[str, Any]] | None = None,
    blockchain_valid: bool = True,
) -> Dict[str, Any]:
    """
    Generate comprehensive final report with all components.
    
    Returns:
        {
            "node_results": [...],
            "system_summary": {...},
            "intervention": {...},
            "simulation": [...],
            "quality_metrics": {...},
            "blockchain_valid": bool,
        }
    """
    # Node results
    node_results = format_node_results(graph, ml_risks, rule_risks)

    # System summary
    system_summary = compute_global_summary(graph)

    # Intervention
    intervention = None
    if intervention_target:
        # Compute impact
        target_risk = float(graph.nodes[intervention_target].get("risk", 0.0))
        reduction = target_risk * 0.3  # Assume 30% reduction
        neighbors = len(list(graph.neighbors(intervention_target)))

        intervention = format_intervention(
            intervention_target,
            risk_reduction=reduction,
            nodes_affected=neighbors,
            effectiveness_score=intervention_effectiveness,
        )

    # Simulation
    simulation = simulation_steps or []

    # Quality metrics
    quality_metrics = {
        "nodes_analyzed": len(node_results),
        "high_risk_count": system_summary["high_risk_nodes"],
        "average_risk": system_summary["average_risk"],
        "system_state": system_summary["system_state"],
    }

    return {
        "node_results": node_results,
        "system_summary": system_summary,
        "intervention": intervention,
        "simulation": simulation,
        "quality_metrics": quality_metrics,
        "blockchain_valid": blockchain_valid,
    }


# ============================================================================
# VISUALIZATION ENHANCEMENT
# ============================================================================


def prepare_graph_for_visualization(graph: nx.Graph) -> Tuple[nx.Graph, Dict[str, Any]]:
    """
    Prepare graph and styling for professional visualization.
    
    Returns:
        (graph, node_styles) where node_styles contains:
        - color: Risk-based color
        - size: Centrality-based size
        - label: Node ID
    """
    graph_copy = graph.copy()

    node_styles = {}
    centralities = nx.degree_centrality(graph)

    for node in graph.nodes:
        node_id = str(node)
        risk = float(graph.nodes[node_id].get("risk", 0.0))
        centrality = centralities.get(node_id, 0.0)

        # Color based on risk
        color = get_risk_color(risk)

        # Size based on centrality (scale 300-1500)
        size = 300 + (centrality * 1200)

        node_styles[node_id] = {
            "color": color,
            "size": size,
            "label": node_id,
            "risk_class": classify_risk(risk),
        }

    return graph_copy, node_styles


def get_visualization_legend() -> Dict[str, str]:
    """Get legend for visualization."""
    return {
        "low_risk": "#2ecc71 (Risk: 0.0 - 0.3)",
        "medium_risk": "#f39c12 (Risk: 0.3 - 0.7)",
        "high_risk": "#e74c3c (Risk: 0.7 - 1.0)",
        "node_size": "Proportional to network centrality",
    }


# ============================================================================
# REPORT PRINTING HELPERS
# ============================================================================


def print_comprehensive_report(report: Dict[str, Any]) -> None:
    """Print comprehensive report in readable format."""
    print("\n" + "=" * 80)
    print("DCCFE SYSTEM - COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 80)

    # System Summary
    summary = report.get("system_summary", {})
    print(f"\n📊 SYSTEM SUMMARY")
    print(f"{'─' * 80}")
    print(f"State: {summary.get('system_state', 'unknown').upper()}")
    print(f"Assessment: {summary.get('assessment', 'N/A')}")
    print(f"Average Risk: {summary.get('average_risk', 0.0):.4f}")
    print(f"High-Risk Nodes: {summary.get('high_risk_nodes', 0)}")
    print(f"Most Critical: {summary.get('most_critical_node', 'N/A')}")

    # Top Nodes
    nodes = report.get("node_results", [])[:3]
    if nodes:
        print(f"\n🔴 TOP 3 NODES (BY RISK)")
        print(f"{'─' * 80}")
        for node in nodes:
            print(f"\n{node['node_id']}: {node['risk_level'].upper()} ")
            print(f"  Risk: {node['final_risk']:.4f}")
            print(f"  Trend: {node['trend']}")
            print(f"  {node['explanation']}")

    # Intervention
    intervention = report.get("intervention")
    if intervention:
        print(f"\n💡 RECOMMENDED INTERVENTION")
        print(f"{'─' * 80}")
        print(f"Target: {intervention.get('recommended_node', 'N/A')}")
        print(f"Impact: {intervention.get('expected_impact', 'unknown').upper()}")
        print(f"Reason: {intervention.get('reason', 'N/A')}")

    # Quality
    quality = report.get("quality_metrics", {})
    print(f"\n✅ QUALITY METRICS")
    print(f"{'─' * 80}")
    print(f"Nodes Analyzed: {quality.get('nodes_analyzed', 0)}")
    print(f"Blockchain Valid: {report.get('blockchain_valid', False)}")

    print("\n" + "=" * 80 + "\n")
