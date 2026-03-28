"""
Test: Refined DCCFE System - Professional presentation and clean output
"""

import pandas as pd
from dccfe import (
    run_refined_dccfe_pipeline,
    classify_risk,
    generate_clean_explanation,
    compute_global_summary,
    format_node_results,
    get_top_at_risk,
    prepare_graph_for_visualization,
)
from dccfe.graph_reasoning import create_user_graph

print("\n" + "=" * 80)
print("REFINED DCCFE SYSTEM - PROFESSIONAL OUTPUT DEMONSTRATION")
print("=" * 80)

# ============================================================================
# DEMO 1: RISK CLASSIFICATION
# ============================================================================

print("\n1️⃣  RISK CLASSIFICATION SYSTEM")
print("─" * 80)

test_scores = [0.15, 0.45, 0.85]
for score in test_scores:
    category = classify_risk(score)
    print(f"  Risk Score {score:.2f} → Category: {category.upper()}")

# ============================================================================
# DEMO 2: STRUCTURED NODE OUTPUT
# ============================================================================

print("\n2️⃣  STRUCTURED NODE OUTPUT")
print("─" * 80)

# Create sample dataset as list of dicts with risk
sample_users = [
    {"user_id": "U1", "income": 3000, "activity": 0.8, "transaction_variability": 0.2, "credit_score": 750, "risk": 0.25},
    {"user_id": "U2", "income": 1500, "activity": 0.3, "transaction_variability": 0.8, "credit_score": 500, "risk": 0.65},
    {"user_id": "U3", "income": 5000, "activity": 0.9, "transaction_variability": 0.1, "credit_score": 800, "risk": 0.15},
    {"user_id": "U4", "income": 2200, "activity": 0.2, "transaction_variability": 0.9, "credit_score": 450, "risk": 0.80},
    {"user_id": "U5", "income": 4500, "activity": 0.7, "transaction_variability": 0.3, "credit_score": 700, "risk": 0.40},
]

# Define relationships (edges)
sample_edges = [
    ("U1", "U2"),
    ("U2", "U3"),
    ("U3", "U4"),
    ("U4", "U5"),
    ("U5", "U1"),
    ("U2", "U4"),
]

# Create graph and print structured output
graph = create_user_graph(sample_users, sample_edges)

# Set risk history for trend detection
graph.nodes["U1"]["risk_history"] = [0.20, 0.22, 0.25]
graph.nodes["U2"]["risk_history"] = [0.50, 0.58, 0.65]

node_results = format_node_results(graph)
print("\nTop 2 Nodes (by risk):\n")
for i, result in enumerate(node_results[:2], 1):
    print(f"{i}. {result['node_id']} - {result['risk_level'].upper()}")
    print(f"   Final Risk: {result['final_risk']}")
    print(f"   Trend: {result['trend']}")
    print(f"   Income Factor: {result['contributions']['income']:.4f}")
    print(f"   Activity Factor: {result['contributions']['activity']:.4f}")
    print(f"   Neighbor Influence: {result['contributions']['neighbor_influence']:.4f}")
    print(f"   Degree Centrality: {result['centrality']['degree']:.4f}")
    print(f"   💬 {result['explanation']}")
    print()

# ============================================================================
# DEMO 3: HUMAN-READABLE EXPLANATIONS
# ============================================================================

print("\n3️⃣  HUMAN-READABLE EXPLANATIONS")
print("─" * 80)

for node_id in ["U2", "U4"]:
    explanation = generate_clean_explanation(node_id, graph)
    risk = float(graph.nodes[node_id].get("risk", 0.0))
    print(f"\n{node_id} (Risk: {risk:.2%})")
    print(f"  → {explanation}")

# ============================================================================
# DEMO 4: GLOBAL SYSTEM SUMMARY
# ============================================================================

print("\n4️⃣  GLOBAL SYSTEM SUMMARY")
print("─" * 80)

summary = compute_global_summary(graph)
print(f"\nSystem State: {summary['system_state'].upper()}")
print(f"Assessment: {summary['assessment']}")
print(f"Average Risk: {summary['average_risk']:.4f}")
print(f"High-Risk Nodes: {summary['high_risk_nodes']}")
print(f"Most Critical: {summary['most_critical_node']}")

# ============================================================================
# DEMO 5: VISUALIZATION DATA
# ============================================================================

print("\n5️⃣  VISUALIZATION PREPARATION")
print("─" * 80)

viz_graph, node_styles = prepare_graph_for_visualization(graph)
print(f"\nGraph prepared for visualization:")
print(f"  Nodes: {len(viz_graph.nodes)}")
print(f"  Edges: {len(viz_graph.edges)}")
print(f"\nNode styling (sample):")
for node_id in ["U1", "U4"]:
    style = node_styles[node_id]
    print(f"  {node_id}:")
    print(f"    Color: {style['color']}")
    print(f"    Size: {style['size']:.0f}")
    print(f"    Risk Class: {style['risk_class']}")

# ============================================================================
# DEMO 6: FULL REFINED PIPELINE
# ============================================================================

print("\n6️⃣  FULL REFINED PIPELINE")
print("─" * 80)

expanded_data = pd.DataFrame({
    "user_id": ["U1", "U2", "U3", "U4", "U5", "U6"],
    "income": [3500, 1800, 5200, 2100, 4800, 3200],
    "activity": [0.82, 0.35, 0.92, 0.25, 0.75, 0.60],
    "transaction_variability": [0.18, 0.75, 0.12, 0.88, 0.28, 0.40],
    "credit_score": [760, 520, 810, 470, 720, 650],
})

print("\nRunning full pipeline with 6-node network...")
report = run_refined_dccfe_pipeline(expanded_data, print_output=False)

# Print custom summary
print("\n📋 PIPELINE EXECUTION SUMMARY:")
print(f"  ✓ Nodes analyzed: {report['quality_metrics']['nodes_analyzed']}")
print(f"  ✓ High-risk nodes: {report['quality_metrics']['high_risk_count']}")
print(f"  ✓ System state: {report['quality_metrics']['system_state']}")
print(f"  ✓ Blockchain valid: {report['blockchain_valid']}")

if report.get("intervention"):
    print(f"\n💡 RECOMMENDED INTERVENTION:")
    interv = report["intervention"]
    print(f"  Target: {interv['recommended_node']}")
    print(f"  Impact: {interv['expected_impact']}")
    print(f"  Confidence: {interv['confidence']:.2%}")
    print(f"  Reason: {interv['reason']}")

# ============================================================================
# DEMO 7: TOP AT-RISK NODES
# ============================================================================

print("\n7️⃣  TOP AT-RISK NODES SUMMARY")
print("─" * 80)

top_nodes = get_top_at_risk(graph, count=3)
print("\nTop 3 highest-risk nodes:\n")
for i, node in enumerate(top_nodes, 1):
    print(f"{i}. {node['node_id']}")
    print(f"   Risk: {node['final_risk']:.4f} ({node['risk_level'].upper()})")
    print(f"   Centrality: {node['centrality']['degree']:.4f}")
    print(f"   Trend: {node['trend']}")
    print()

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("✅ REFINED DCCFE SYSTEM DEMONSTRATION COMPLETE")
print("=" * 80)

print("\n📊 FEATURES DEMONSTRATED:")
print("  ✓ Risk Classification (low/medium/high)")
print("  ✓ Structured Node Output (all components)")
print("  ✓ Human-Readable Explanations (jargon-free)")
print("  ✓ Global System Summary (state classification)")
print("  ✓ Visualization Preparation (styling + sizing)")
print("  ✓ Full Refined Pipeline (end-to-end)")
print("  ✓ Top At-Risk Summary (quick rankings)")

print("\n💼 PROFESSIONAL OUTPUT ACHIEVED:")
print("  • Clear risk classifications")
print("  • Transparent explanations")
print("  • Structured data format")
print("  • System-level insights")
print("  • Visualization-ready data")
print("  • Production-ready output")

print("\n" + "=" * 80 + "\n")
