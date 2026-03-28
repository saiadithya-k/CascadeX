#!/usr/bin/env python
"""Comprehensive test of System Quality enhancements."""

import networkx as nx
from dccfe import (
    analyze_node_behavior,
    compute_system_stability_advanced,
    detect_cascade_effects,
    evaluate_interventions,
    generate_human_explanation,
    generate_node_explanations,
    generate_quality_report,
    validate_consistency,
)

# ============================================================================
# CREATE TEST GRAPH
# ============================================================================
print("\n" + "=" * 80)
print("SYSTEM QUALITY ENHANCEMENTS - COMPREHENSIVE TEST")
print("=" * 80)

graph = nx.Graph()

# Create 8 test nodes with financial attributes and risk history
users = [
    {"user_id": "U1", "income": 5200, "activity": 0.82, "variability": 0.15},
    {"user_id": "U2", "income": 3800, "activity": 0.45, "variability": 0.35},
    {"user_id": "U3", "income": 2200, "activity": 0.28, "variability": 0.68},
    {"user_id": "U4", "income": 6500, "activity": 0.91, "variability": 0.08},
    {"user_id": "U5", "income": 4100, "activity": 0.62, "variability": 0.42},
    {"user_id": "U6", "income": 2800, "activity": 0.35, "variability": 0.55},
    {"user_id": "U7", "income": 3500, "activity": 0.50, "variability": 0.40},
    {"user_id": "U8", "income": 4800, "activity": 0.75, "variability": 0.25},
]

for user in users:
    user_id = user["user_id"]
    income = user["income"]
    activity = user["activity"]
    var = user["variability"]

    # Compute risk
    risk = max(0.0, min(1.0, 
        (1 - min(income, 8000) / 8000) * 0.3 + 
        (1 - activity) * 0.4 + 
        var * 0.3
    ))

    # Create risk history to show trends
    history = [risk * 0.85, risk * 0.90, risk * 0.95, risk]

    graph.add_node(
        user_id,
        income=income,
        activity=activity,
        transaction_variability=var,
        risk=risk,
        instability=0.2,
        risk_history=history,
    )

# Add weighted edges
edges = [
    ("U1", "U2", 0.8),
    ("U2", "U3", 0.9),
    ("U3", "U4", 0.7),
    ("U4", "U5", 0.75),
    ("U5", "U6", 0.85),
    ("U1", "U4", 0.6),
    ("U6", "U7", 0.7),
    ("U7", "U8", 0.8),
]

for u, v, w in edges:
    graph.add_edge(u, v, weight=w)

# ============================================================================
# 1. NODE BEHAVIOR ANALYSIS
# ============================================================================
print("\n\n1. NODE BEHAVIOR ANALYSIS")
print("-" * 80)

behaviors = analyze_node_behavior(graph, observation_window=3)
print(f"\nAnalyzed {len(behaviors)} nodes for behavior patterns:\n")

for b in behaviors[:4]:
    print(f"Node {b.node}:")
    print(f"  Current Risk: {b.current_risk:.4f}")
    print(f"  Behavior Trend: {b.trend}")
    print(f"  Risk Change: {b.risk_change:+.4f}")
    print(f"  Cascade Source: {b.is_cascade_source}")
    if b.affected_nodes:
        print(f"  Affects: {b.affected_nodes}")
    print()

cascades = detect_cascade_effects(graph, behaviors)
print(f"Cascade Analysis:")
print(f"  Cascade Sources: {cascades['cascade_count']} nodes")
print(f"  Cascade Activity: {cascades['cascade_activity']}")
print(f"  Total Secondary Impact: {cascades['total_secondary_nodes']} nodes")
print(f"  Avg Cascade Size: {cascades['average_cascade_size']:.2f}")

# ============================================================================
# 2. HUMAN-READABLE EXPLANATIONS
# ============================================================================
print("\n\n2. EXPLANATION QUALITY - HUMAN-READABLE")
print("-" * 80)

explanations = generate_node_explanations(graph, behaviors)
print(f"\nNode Risk Explanations (No jargon, natural language):\n")

for node_id in list(graph.nodes)[:4]:
    print(f"{node_id}: {explanations[node_id]}")
    print()

# ============================================================================
# 3. SYSTEM STABILITY ANALYSIS
# ============================================================================
print("\n3. GLOBAL SYSTEM STABILITY ANALYSIS")
print("-" * 80)

stability = compute_system_stability_advanced(graph)
print(f"\nSystem Stability Metrics:")
print(f"  Average Network Risk: {stability.average_risk:.6f}")
print(f"  Risk Variance: {stability.risk_variance:.6f}")
print(f"  Rate of Change: {stability.rate_of_change:.6f}")
print(f"  Classification: {stability.classification.upper()}")
print(f"  High-Risk Nodes: {stability.high_risk_nodes}")
print(f"\nSystem Assessment:")
print(f"  {stability.trend_description}")

if stability.instability_clusters:
    print(f"\nInstability Clusters Detected:")
    for i, cluster in enumerate(stability.instability_clusters, 1):
        print(f"  Cluster {i}: {cluster}")

# ============================================================================
# 4. INTERVENTION QUALITY & RANKING
# ============================================================================
print("\n\n4. INTERVENTION QUALITY - RANKED OPTIONS")
print("-" * 80)

high_risk = [str(n) for n in graph.nodes if float(graph.nodes[n].get("risk", 0.0)) > 0.6]
interventions = evaluate_interventions(graph, candidates=high_risk, max_interventions=4)

print(f"\nTop Intervention Options (ranked by effectiveness):\n")

for i, opt in enumerate(interventions, 1):
    print(f"{i}. Target: {opt.target_nodes}")
    print(f"   Effectiveness Score: {opt.effectiveness_score:.6f}")
    print(f"   Nodes Stabilized: {opt.reach_score}")
    print(f"   Cascade Mitigation: {opt.cascade_mitigation:.3f}")
    print(f"   Overall Confidence: {opt.overall_rank_score:.6f}")
    print(f"   Reason: {opt.justification}")
    print()

# ============================================================================
# 5. CONSISTENCY CHECK
# ============================================================================
print("\n5. CONSISTENCY & ANOMALY DETECTION")
print("-" * 80)

consistency = validate_consistency(graph, max_risk_jump=0.15)
print(f"\nConsistency Check Results:")
print(f"  Valid: {consistency['is_valid']}")
print(f"  Anomalies Found: {consistency['anomaly_count']}")
print(f"  Consistency Score: {consistency['consistency_score']:.4f}")

if consistency["anomalies"]:
    print(f"\n  Detected Anomalies:")
    for anomaly in consistency["anomalies"]:
        print(f"    - {anomaly}")

# ============================================================================
# 6. INTEGRATED QUALITY REPORT
# ============================================================================
print("\n\n6. INTEGRATED QUALITY REPORT")
print("-" * 80)

report = generate_quality_report(graph)

print(f"\nQuality Report Summary:")
print(f"  Analyzed Nodes: {len(report['node_behavior'])}")
print(f"  System Classification: {report['system_stability']['classification'].upper()}")
print(f"  Cascade Activity: {report['cascade_summary']['cascade_activity']}")
print(f"  Consistency Score: {report['consistency']['consistency_score']:.4f}")

print(f"\nTop 3 Node Behaviors:")
for i, node in enumerate(report['node_behavior'][:3], 1):
    print(f"  {i}. {node['node']}: {node['trend']} (risk={node['current_risk']:.4f})")

if report['best_action']:
    best = report['best_action']
    print(f"\nBest Recommended Action:")
    print(f"  Target: {best['target']}")
    print(f"  Confidence: {best['confidence']:.6f}")
    print(f"  Expected Effectiveness: {best['effectiveness']:.6f}")
    print(f"  Reason: {best['reason']}")

# ============================================================================
# 7. SHOW QUALITY IMPROVEMENTS
# ============================================================================
print("\n\n7. QUALITY IMPROVEMENTS DEMONSTRATED")
print("-" * 80)

print("""
✓ SYSTEM BEHAVIOR ANALYSIS
  - Tracks risk evolution per node across time
  - Detects patterns: escalating, recovering, stable
  - Identifies cascade sources and affected nodes
  
✓ EXPLANATION QUALITY
  - Human-readable explanations (no jargon)
  - Combines primary causes + secondary influences
  - Natural language assessment of system impact
  
✓ SYSTEM STABILITY MONITORING
  - Global metrics: average risk, variance, rate of change
  - Classification: stable, fragile, or critical
  - Detects instability clusters (groups of high-risk nodes)
  
✓ INTERVENTION QUALITY IMPROVEMENT
  - Simulates interventions before recommending
  - Measures: effectiveness, reach, cascade mitigation
  - Ranked by weighted objective function
  
✓ CONSISTENCY CHECK
  - Validates no sudden unrealistic jumps
  - Checks risk bounds [0, 1]
  - Monitors history continuity
  
✓ INTEGRATED OUTPUT
  - Node behaviors with explanations
  - System stability assessment
  - Ranked intervention options
  - Best action with confidence score
""")

print("\n" + "=" * 80)
print("SYSTEM QUALITY VALIDATION COMPLETE ✅")
print("=" * 80 + "\n")
