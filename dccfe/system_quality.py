"""
System Quality Module: Behavior Analysis, Explanations, Stability, and Intervention Quality.

Focus: Core system quality improvements
- Node behavior tracking and classification
- Human-readable explanations
- System stability monitoring with cluster detection
- Smart intervention ranking and simulation
- Consistency validation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

import networkx as nx


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return min(max(float(v), lo), hi)


def _safe_div(a: float, b: float, eps: float = 1e-9) -> float:
    return a / max(b, eps)


# ============================================================================
# 1. SYSTEM BEHAVIOR ANALYSIS
# ============================================================================


@dataclass
class NodeBehavior:
    """Node behavior classification and metrics."""

    node: str
    current_risk: float
    trend: str  # "escalating", "recovering", "stable"
    risk_change: float  # change from start of observation
    history_length: int
    avg_risk: float  # average over observation window
    is_cascade_source: bool  # does this node cause cascades?
    affected_nodes: List[str]  # nodes affected by this one


def analyze_node_behavior(
    graph: nx.Graph,
    observation_window: int = 10,
) -> List[NodeBehavior]:
    """
    Analyze how each node's risk evolves over time.
    
    Detects:
    - escalating: increasing trend
    - recovering: decreasing trend
    - stable: relatively flat
    """
    behaviors: List[NodeBehavior] = []

    for node in graph.nodes:
        node_id = str(node)
        history = list(graph.nodes[node_id].get("risk_history", []))

        if not history:
            history = [float(graph.nodes[node_id].get("risk", 0.0))]

        window = history[-observation_window:] if len(history) > 0 else [history[0]]
        current = float(graph.nodes[node_id].get("risk", 0.0))

        # Calculate trend
        if len(window) >= 2:
            change = window[-1] - window[0]
            avg = sum(window) / len(window)
        else:
            change = 0.0
            avg = current

        # Classify behavior
        if change > 0.05:
            trend = "escalating"
        elif change < -0.05:
            trend = "recovering"
        else:
            trend = "stable"

        # Check if cascade source (neighbors affected)
        neighbors = list(graph.neighbors(node_id))
        affected = [
            n
            for n in neighbors
            if float(graph.nodes[n].get("risk", 0.0))
            > float(graph.nodes[node_id].get("risk", 0.0)) * 0.8
        ]

        behavior = NodeBehavior(
            node=node_id,
            current_risk=_clamp(current),
            trend=trend,
            risk_change=change,
            history_length=len(history),
            avg_risk=_clamp(avg),
            is_cascade_source=len(affected) >= len(neighbors) * 0.5 if neighbors else False,
            affected_nodes=affected,
        )
        behaviors.append(behavior)

    return sorted(behaviors, key=lambda b: b.current_risk, reverse=True)


def detect_cascade_effects(
    graph: nx.Graph,
    behaviors: List[NodeBehavior],
) -> Dict[str, Any]:
    """
    Detect cascade effects: when one node causes multiple nodes to rise.
    
    Returns:
    - cascade_sources: nodes that trigger cascades
    - cascade_summary: overall cascade activity
    """
    cascade_sources = [b.node for b in behaviors if b.is_cascade_source]
    total_affected = sum(len(b.affected_nodes) for b in behaviors if b.is_cascade_source)

    return {
        "cascade_count": len(cascade_sources),
        "cascade_sources": cascade_sources,
        "total_secondary_nodes": total_affected,
        "average_cascade_size": (
            _safe_div(total_affected, len(cascade_sources)) if cascade_sources else 0.0
        ),
        "cascade_activity": "high" if len(cascade_sources) >= 3 else "moderate" if cascade_sources else "low",
    }


# ============================================================================
# 2. EXPLANATION QUALITY
# ============================================================================


def generate_human_explanation(
    node: str,
    graph: nx.Graph,
    bayes_inference: Dict[str, Dict[str, Any]] | None = None,
) -> str:
    """
    Generate clear, human-readable explanation without jargon or raw numbers.
    
    Combines:
    - primary cause (income, activity, or neighbors)
    - secondary influence
    - system effect
    """
    node_id = str(node)
    attrs = graph.nodes[node_id]
    risk = float(attrs.get("risk", 0.0))
    income = float(attrs.get("income", 0.0))
    activity = float(attrs.get("activity", 0.0))

    # Determine primary cause
    primary = ""
    if income < 2500:
        primary = "low income"
    elif activity < 0.4:
        primary = "limited financial activity"
    else:
        primary = "standard financial profile"

    # Secondary influence from neighbors
    neighbors = list(graph.neighbors(node_id))
    if neighbors:
        neighbor_risks = [float(graph.nodes[n].get("risk", 0.0)) for n in neighbors]
        avg_neighbor_risk = sum(neighbor_risks) / len(neighbor_risks)
        if avg_neighbor_risk > 0.65:
            secondary = " Financial instability of connected parties is further increasing the risk."
        elif avg_neighbor_risk > 0.45:
            secondary = " Some instability from connected parties is contributing."
        else:
            secondary = ""
    else:
        secondary = ""

    # System effect
    if risk > 0.75:
        system_effect = "This node poses a significant risk to overall network stability."
    elif risk > 0.5:
        system_effect = "This node is moderately affected by system conditions."
    else:
        system_effect = "This node maintains reasonable stability."

    explanation = f"Risk increased due to {primary}.{secondary} {system_effect}"
    return explanation.strip()


def generate_node_explanations(
    graph: nx.Graph,
    behaviors: List[NodeBehavior],
    bayes_inference: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, str]:
    """Generate human-readable explanations for all nodes."""
    explanations = {}
    for behavior in behaviors:
        explanations[behavior.node] = generate_human_explanation(
            behavior.node, graph, bayes_inference
        )
    return explanations


# ============================================================================
# 3. SYSTEM STABILITY ANALYSIS
# ============================================================================


@dataclass
class SystemStability:
    """System-level stability assessment."""

    average_risk: float
    risk_variance: float
    rate_of_change: float
    classification: str  # "stable", "fragile", "critical"
    high_risk_nodes: int
    instability_clusters: List[List[str]]
    trend_description: str


def compute_system_stability_advanced(graph: nx.Graph) -> SystemStability:
    """
    Analyze global system stability.
    
    Classifies as:
    - stable: low risk + low variance + low change
    - fragile: moderate risk or rising trend
    - critical: high risk or rapid increase
    """
    if graph.number_of_nodes() == 0:
        return SystemStability(
            average_risk=0.0,
            risk_variance=0.0,
            rate_of_change=0.0,
            classification="stable",
            high_risk_nodes=0,
            instability_clusters=[],
            trend_description="No nodes in system",
        )

    nodes = list(graph.nodes)
    current_risks = [float(graph.nodes[n].get("risk", 0.0)) for n in nodes]

    # Basic metrics
    avg_risk = sum(current_risks) / len(current_risks)
    variance = sum((r - avg_risk) ** 2 for r in current_risks) / len(current_risks)
    std_dev = variance ** 0.5

    # Rate of change
    histories = [list(graph.nodes[n].get("risk_history", [avg_risk])) for n in nodes]
    if all(len(h) >= 2 for h in histories):
        changes = [(h[-1] - h[-2]) for h in histories]
        rate_of_change = sum(abs(c) for c in changes) / len(changes)
    else:
        rate_of_change = 0.0

    # Classification
    high_risk = sum(1 for r in current_risks if r > 0.7)
    escalating = sum(1 for h in histories if len(h) >= 2 and (h[-1] - h[-2]) > 0.05)

    if avg_risk < 0.4 and rate_of_change < 0.02:
        classification = "stable"
        trend = "System risk is low and stable"
    elif avg_risk > 0.65 or escalating > len(nodes) * 0.3:
        classification = "critical"
        trend = "System experiencing rapid risk increase or high average risk"
    else:
        classification = "fragile"
        trend = "System at moderate risk with potential vulnerabilities"

    # Detect instability clusters
    clusters = _detect_instability_clusters(graph, threshold=0.65, min_cluster_size=2)

    return SystemStability(
        average_risk=_clamp(avg_risk),
        risk_variance=variance,
        rate_of_change=rate_of_change,
        classification=classification,
        high_risk_nodes=high_risk,
        instability_clusters=clusters,
        trend_description=trend,
    )


def _detect_instability_clusters(
    graph: nx.Graph,
    threshold: float = 0.65,
    min_cluster_size: int = 2,
) -> List[List[str]]:
    """Detect groups of high-risk nodes that form clusters."""
    high_risk_nodes = [n for n in graph.nodes if float(graph.nodes[n].get("risk", 0.0)) > threshold]

    if len(high_risk_nodes) < min_cluster_size:
        return []

    # Use simple connectivity-based clustering
    subgraph = graph.subgraph(high_risk_nodes)
    clusters = [list(c) for c in nx.connected_components(subgraph)]

    return [c for c in clusters if len(c) >= min_cluster_size]


# ============================================================================
# 4. INTERVENTION QUALITY IMPROVEMENT
# ============================================================================


@dataclass
class InterventionOption:
    """Ranked intervention option with justification."""

    target_nodes: List[str]
    effectiveness_score: float  # total network risk reduction
    reach_score: float  # number of nodes stabilized
    cascade_mitigation: float  # reduction in cascade activity
    overall_rank_score: float
    justification: str


def evaluate_interventions(
    graph: nx.Graph,
    candidates: List[str] | None = None,
    max_interventions: int = 5,
    risk_reduction_factor: float = 0.3,
) -> List[InterventionOption]:
    """
    Evaluate intervention effectiveness by simulation.
    
    For each candidate:
    - Simulate reducing its risk
    - Measure: total risk reduction, nodes stabilized, cascade mitigation
    - Rank by weighted effectiveness
    """
    if not candidates:
        # Use top high-risk nodes
        all_nodes = list(graph.nodes)
        candidates = sorted(
            all_nodes,
            key=lambda n: float(graph.nodes[n].get("risk", 0.0)),
            reverse=True,
        )[: max(max_interventions, 3)]

    baseline_risks = {str(n): float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes}
    baseline_total = sum(baseline_risks.values())

    options: List[InterventionOption] = []

    for target in candidates[:max_interventions]:
        target_id = str(target)

        # Simulate intervention
        sim = graph.copy()
        original_risk = float(sim.nodes[target_id].get("risk", 0.0))
        reduced_risk = _clamp(original_risk * (1.0 - risk_reduction_factor))
        sim.nodes[target_id]["risk"] = reduced_risk

        # Propagate once to see secondary effects
        for neighbor in sim.neighbors(target_id):
            neigh_risk = float(sim.nodes[neighbor].get("risk", 0.0))
            # Small reduction in neighbor risk due to stability
            sim.nodes[neighbor]["risk"] = _clamp(neigh_risk * 0.95)

        # Measure results
        new_total = sum(float(sim.nodes[n].get("risk", 0.0)) for n in sim.nodes)
        effectiveness = baseline_total - new_total

        # Count stabilized nodes (moved from high to moderate)
        stabilized = sum(
            1
            for n in sim.nodes
            if baseline_risks[str(n)] > 0.65 and float(sim.nodes[n].get("risk", 0.0)) <= 0.65
        )

        # Cascade mitigation (reduced cascade sources)
        baseline_behaviors = analyze_node_behavior(graph)
        baseline_cascade = detect_cascade_effects(graph, baseline_behaviors)
        sim_behaviors = analyze_node_behavior(sim)
        sim_cascade = detect_cascade_effects(sim, sim_behaviors)
        cascade_reduction = float(baseline_cascade["cascade_count"]) - float(
            sim_cascade["cascade_count"]
        )

        # Combined score
        rank_score = 0.5 * effectiveness + 0.3 * stabilized + 0.2 * cascade_reduction

        justification = (
            f"Intervention on {target_id}: "
            f"reduces network risk by {effectiveness:.3f}, "
            f"stabilizes {stabilized} nodes, "
            f"mitigates {max(0, int(cascade_reduction))} cascade sources."
        )

        option = InterventionOption(
            target_nodes=[target_id],
            effectiveness_score=round(effectiveness, 6),
            reach_score=stabilized,
            cascade_mitigation=round(cascade_reduction, 6),
            overall_rank_score=round(rank_score, 6),
            justification=justification,
        )
        options.append(option)

    options.sort(key=lambda o: o.overall_rank_score, reverse=True)
    return options


# ============================================================================
# 5. CONSISTENCY CHECK
# ============================================================================


def validate_consistency(
    graph: nx.Graph,
    previous_graph: nx.Graph | None = None,
    max_risk_jump: float = 0.15,
) -> Dict[str, Any]:
    """
    Validate system consistency: no sudden unrealistic jumps, smooth transitions.
    
    Checks:
    - risk changes within reasonable bounds
    - no node risk exceeds [0, 1]
    - stable behavior across iterations
    """
    anomalies: List[str] = []

    current_risks = {str(n): float(graph.nodes[n].get("risk", 0.0)) for n in graph.nodes}

    # Check risk bounds
    for node, risk in current_risks.items():
        if not (0.0 <= risk <= 1.0):
            anomalies.append(f"Node {node} risk out of bounds: {risk}")

    # Check jumps from previous state
    if previous_graph is not None:
        prev_risks = {str(n): float(previous_graph.nodes[n].get("risk", 0.0)) for n in previous_graph.nodes}
        for node, current_risk in current_risks.items():
            if node in prev_risks:
                prev_risk = prev_risks[node]
                jump = abs(current_risk - prev_risk)
                if jump > max_risk_jump:
                    anomalies.append(
                        f"Node {node} exceeds max jump: {prev_risk:.3f} -> {current_risk:.3f} "
                        f"(delta={jump:.3f})"
                    )

    # Check history continuity
    for node in graph.nodes:
        node_id = str(node)
        history = list(graph.nodes[node_id].get("risk_history", []))
        if len(history) >= 2:
            for i in range(1, len(history)):
                jump = abs(history[i] - history[i - 1])
                if jump > max_risk_jump:
                    anomalies.append(
                        f"Node {node_id} history jump at index {i}: "
                        f"{history[i - 1]:.3f} -> {history[i]:.3f}"
                    )

    is_valid = len(anomalies) == 0

    return {
        "is_valid": is_valid,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies[:10],  # Cap to first 10
        "consistency_score": _clamp(1.0 - (len(anomalies) / max(len(graph.nodes), 1) * 0.1)),
    }


# ============================================================================
# 6. INTEGRATED QUALITY REPORT
# ============================================================================


def generate_quality_report(
    graph: nx.Graph,
    previous_graph: nx.Graph | None = None,
    bayes_inference: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive quality report with all analyses.
    
    Returns:
    {
        "node_behavior": [...],
        "node_explanations": {...},
        "system_stability": {...},
        "interventions": [...],
        "best_action": {...},
        "consistency": {...}
    }
    """
    # 1. Behavior Analysis
    behaviors = analyze_node_behavior(graph)
    cascades = detect_cascade_effects(graph, behaviors)

    # 2. Explanations
    explanations = generate_node_explanations(graph, behaviors, bayes_inference)

    # 3. System Stability
    stability = compute_system_stability_advanced(graph)

    # 4. Interventions
    high_risk_nodes = [
        str(n)
        for n in graph.nodes
        if float(graph.nodes[n].get("risk", 0.0)) > 0.6
    ]
    interventions = evaluate_interventions(graph, candidates=high_risk_nodes, max_interventions=5)

    # 5. Best Action
    best_action = None
    if interventions:
        best = interventions[0]
        best_action = {
            "target": best.target_nodes,
            "effectiveness": best.effectiveness_score,
            "reach": best.reach_score,
            "cascade_mitigation": best.cascade_mitigation,
            "confidence": best.overall_rank_score,
            "reason": best.justification,
        }

    # 6. Consistency
    consistency = validate_consistency(graph, previous_graph)

    return {
        "node_behavior": [
            {
                "node": b.node,
                "current_risk": round(b.current_risk, 4),
                "trend": b.trend,
                "risk_change": round(b.risk_change, 4),
                "avg_recent_risk": round(b.avg_risk, 4),
                "is_cascade_source": b.is_cascade_source,
                "affected_nodes": b.affected_nodes,
            }
            for b in behaviors
        ],
        "cascade_summary": cascades,
        "node_explanations": explanations,
        "system_stability": {
            "average_risk": round(stability.average_risk, 6),
            "risk_variance": round(stability.risk_variance, 6),
            "rate_of_change": round(stability.rate_of_change, 6),
            "classification": stability.classification,
            "high_risk_nodes": stability.high_risk_nodes,
            "instability_clusters": stability.instability_clusters,
            "trend": stability.trend_description,
        },
        "interventions": [
            {
                "target": opt.target_nodes,
                "effectiveness": opt.effectiveness_score,
                "reach": opt.reach_score,
                "cascade_mitigation": opt.cascade_mitigation,
                "confidence": opt.overall_rank_score,
                "reason": opt.justification,
            }
            for opt in interventions
        ],
        "best_action": best_action,
        "consistency": consistency,
    }
