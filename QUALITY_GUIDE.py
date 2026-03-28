#!/usr/bin/env python
"""
DCCFE System Quality: User Guide and Examples

This guide demonstrates how to use the enhanced system quality features.
"""

import networkx as nx
from dccfe import (
    # Quality analysis functions
    analyze_node_behavior,
    generate_human_explanation,
    compute_system_stability_advanced,
    detect_cascade_effects,
    evaluate_interventions,
    validate_consistency,
    generate_quality_report,
    # Pipeline integration
    enhance_pipeline_output,
    print_quality_summary,
    run_dccfe_pipeline,
)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║        DCCFE SYSTEM QUALITY - COMPREHENSIVE USER GUIDE                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# ============================================================================
# EXAMPLE 1: STANDALONE QUALITY ANALYSIS
# ============================================================================
print("""
─────────────────────────────────────────────────────────────────────────────
EXAMPLE 1: Standalone Quality Analysis on a Financial Network
─────────────────────────────────────────────────────────────────────────────

Create a financial network and analyze its quality.
""")

# Create a test graph
graph = nx.Graph()

test_users = [
    {"user_id": "U1", "income": 5500, "activity": 0.80, "var": 0.12},
    {"user_id": "U2", "income": 3200, "activity": 0.40, "var": 0.50},
    {"user_id": "U3", "income": 2100, "activity": 0.25, "var": 0.70},
    {"user_id": "U4", "income": 6800, "activity": 0.95, "var": 0.05},
]

for user in test_users:
    uid = user["user_id"]
    risk = max(0, min(1, 
        (1 - user["income"] / 8000) * 0.3 + (1 - user["activity"]) * 0.4 + user["var"] * 0.3
    ))
    graph.add_node(
        uid,
        income=user["income"],
        activity=user["activity"],
        transaction_variability=user["var"],
        risk=risk,
        risk_history=[risk * 0.9, risk * 0.95, risk],
    )

graph.add_edge("U1", "U2", weight=0.8)
graph.add_edge("U2", "U3", weight=0.9)
graph.add_edge("U3", "U4", weight=0.7)

print("Created test network with 4 nodes and 3 edges.\n")

# ════════════════════════════════════════════════════════════════════════
# 1.A - Node Behavior Analysis
# ════════════════════════════════════════════════════════════════════════
print("1.A NODE BEHAVIOR ANALYSIS")
print("──────────────────────────\n")

behaviors = analyze_node_behavior(graph, observation_window=2)

print("Analyzing how each node's risk evolves:\n")
for b in behaviors:
    status = "🔴" if b.trend == "escalating" else "🟢" if b.trend == "recovering" else "🟡"
    print(f"{status} Node {b.node}:")
    print(f"    Risk: {b.current_risk:.4f}")
    print(f"    Trend: {b.trend}")
    print(f"    Change: {b.risk_change:+.4f}")
    print()

# ════════════════════════════════════════════════════════════════════════
# 1.B - Cascade Detection
# ════════════════════════════════════════════════════════════════════════
print("1.B CASCADE EFFECT DETECTION")
print("──────────────────────────\n")

cascades = detect_cascade_effects(graph, behaviors)
print(f"Cascade analysis:")
print(f"  Cascade sources: {cascades['cascade_count']}")
print(f"  Activity level: {cascades['cascade_activity']}")
print(f"  Secondary impact: {cascades['total_secondary_nodes']} nodes affected")
print()

# ════════════════════════════════════════════════════════════════════════
# 1.C - Human-Readable Explanations
# ════════════════════════=-=-=-=-════════════════════════════════════════
print("1.C HUMAN-READABLE NODE EXPLANATIONS")
print("────────────────────────────────────\n")

explanations = generate_human_explanation("U3", graph)
print(f"Node U3:\n  {explanations}\n")

# ════════════════════════════════════════════════════════════════════════
# 1.D - System Stability
# ════════════════════════════════════════════════════════════════════════
print("1.D GLOBAL SYSTEM STABILITY")
print("──────────────────────────\n")

stability = compute_system_stability_advanced(graph)
print(f"Stability Assessment:")
print(f"  Average Risk: {stability.average_risk:.4f}")
print(f"  Variance: {stability.risk_variance:.4f}")
print(f"  Change Rate: {stability.rate_of_change:.4f}")
print(f"  Classification: {stability.classification}")
print(f"  Assessment: {stability.trend_description}")
print()

# ════════════════════════════════════════════════════════════════════════
# 1.E - Intervention Ranking
# ════════════════════════════════════════════════════════════════════════
print("1.E RANKED INTERVENTION OPTIONS")
print("──────────────────────────────\n")

high_risk_nodes = [str(n) for n in graph.nodes if float(graph.nodes[n].get("risk", 0)) > 0.5]
interventions = evaluate_interventions(graph, candidates=high_risk_nodes, max_interventions=3)

for i, opt in enumerate(interventions, 1):
    print(f"{i}. Intervene on {opt.target_nodes[0]}")
    print(f"   Effectiveness: {opt.effectiveness_score:.4f}")
    print(f"   Nodes Stabilized: {opt.reach_score}")
    print(f"   Confidence: {opt.overall_rank_score:.4f}")
    print(f"   Why: {opt.justification[:60]}...")
    print()

# ════════════════════════════════════════════════════════════════════════
# 1.F - Consistency Check
# ════════════════════════════════════════════════════════════════════════
print("1.F CONSISTENCY CHECK")
print("───────────────────\n")

consistency = validate_consistency(graph, max_risk_jump=0.15)
print(f"Validation Results:")
print(f"  Valid: {'✅' if consistency['is_valid'] else '❌'}")
print(f"  Anomalies: {consistency['anomaly_count']}")
print(f"  Consistency Score: {consistency['consistency_score']:.4f}")
print()

# ════════════════════════════════════════════════════════════════════════
# 1.G - Integrated Report
# ════════════════════════════════════════════════════════════════════════
print("1.G INTEGRATED QUALITY REPORT")
print("────────────────────────────\n")

report = generate_quality_report(graph)
print(f"Generated comprehensive quality report with sections:")
print(f"  ✓ Node behaviors ({len(report['node_behavior'])} nodes)")
print(f"  ✓ Explanations (natural language)")
print(f"  ✓ System stability (classification)")
print(f"  ✓ Intervention options ({len(report['interventions'])} ranked)")
print(f"  ✓ Best action (recommended)")
print(f"  ✓ Consistency check")
print(f"\nBest recommended action: {report['best_action']['target']}")
print(f"Reason: {report['best_action']['reason']}")
print()

# ============================================================================
# EXAMPLE 2: PIPELINE INTEGRATION
# ============================================================================
print("""
─────────────────────────────────────────────────────────────────────────────
EXAMPLE 2: Pipeline Integration with Automatic Quality Monitoring
─────────────────────────────────────────────────────────────────────────────

Run the DCCFE pipeline and automatically add quality analysis.
""")

print("Running DCCFE pipeline with quality enhancements...\n")

# Run standard pipeline
result = run_dccfe_pipeline(
    propagation_factor=0.2,
    propagation_steps=2,
    shock_enabled=False
)

# Enhance with quality analysis
enhanced_result = enhance_pipeline_output(result, enable_quality_report=True)

# Print quality summary
print_quality_summary(enhanced_result)

# ============================================================================
# EXAMPLE 3: CUSTOM QUALITY WORKFLOWS
# ============================================================================
print("""
─────────────────────────────────────────────────────────────────────────────
EXAMPLE 3: Custom Quality Workflows
─────────────────────────────────────────────────────────────────────────────

Implement custom analysis workflows using quality components.
""")

print("WORKFLOW: Crisis Response Protocol")
print("──────────────────────────────────\n")

# Create escalation monitoring
escalating = [b for b in behaviors if b.trend == "escalating"]
if escalating:
    print(f"⚠️  ALERT: {len(escalating)} nodes showing escalating risk")
    for b in escalating:
        print(f"   - {b.node}: {b.risk_change:+.4f} change")
else:
    print("✅ No escalating nodes detected")

print()

# Check cluster risk
clusters = stability.instability_clusters
if clusters:
    print(f"⚠️  ALERT: {len(clusters)} instability clusters detected")
    for cluster in clusters:
        print(f"   - Cluster: {cluster}")
else:
    print("✅ No instability clusters")

print()

# Recommend emergency action
if len(escalating) >= 2 or len(clusters) >= 2:
    print("🚨 CRITICAL: Recommend immediate intervention")
    best = report['best_action']
    if best:
        print(f"   Action: {best['target']}")
        print(f"   Expected Result: {best['reason']}")
elif escalating or clusters:
    print("⚡ WARNING: Review and prepare contingency plans")
else:
    print("✅ STABLE: Continue monitoring")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("""
─────────────────────────────────────────────────────────────────────────────
SUMMARY OF QUALITY FEATURES
─────────────────────────────────────────────────────────────────────────────

✓ BEHAVIOR ANALYSIS
  Track how node risk evolves, detect escalating/recovering/stable patterns,
  identify cascade sources affecting multiple nodes

✓ HUMAN EXPLANATIONS  
  Get clear, natural language explanations without jargon, showing primary
  causes, secondary influences, and system impact

✓ SYSTEM STABILITY
  Monitor global metrics (avg risk, variance, change rate), classify system
  as stable/fragile/critical, detect instability clusters

✓ SMART INTERVENTIONS
  Evaluate intervention options through simulation, rank by effectiveness
  and reach, understand why each action works

✓ CONSISTENCY CHECK
  Validate smooth transitions, detect unrealistic jumps, confirm bounds
  and history continuity

✓ INTEGRATED REPORTS
  Combine all analyses into one comprehensive quality report with
  recommendations and explanations

─────────────────────────────────────────────────────────────────────────────
""")

print("✅ GUIDE COMPLETE\n")
