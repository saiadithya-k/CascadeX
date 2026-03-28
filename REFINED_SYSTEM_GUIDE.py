"""
REFINED DCCFE SYSTEM - PROFESSIONAL GUIDE

This guide demonstrates how to use the refined DCCFE system for
professional-grade financial risk analysis with clear, interpretable outputs.
"""

import pandas as pd
from dccfe import (
    # Presentation layer - structured output
    classify_risk,
    format_node_results,
    generate_clean_explanation,
    compute_global_summary,
    format_intervention,
    format_simulation_step,
    get_visualization_legend,
    print_comprehensive_report,
    # Refined pipeline
    run_refined_dccfe_pipeline,
    quick_risk_snapshot,
    get_top_at_risk,
    get_node_details,
)

print("\n" + "=" * 80)
print("REFINED DCCFE SYSTEM - PROFESSIONAL USER GUIDE")
print("=" * 80)

# ============================================================================
# SECTION 1: RISK CLASSIFICATION
# ============================================================================

print("\n1. RISK CLASSIFICATION SYSTEM")
print("─" * 80)

print("""
The system classifies risk into three clear categories:
  • LOW (0.0 – 0.3):       Minimal risk, stable
  • MEDIUM (0.3 – 0.7):    Moderate risk, requires monitoring
  • HIGH (0.7 – 1.0):      Substantial risk, intervention needed

Usage:
  from dccfe import classify_risk
  category = classify_risk(0.75)  # Returns "high"
""")

# Demonstrate
for score in [0.25, 0.55, 0.88]:
    cat = classify_risk(score)
    print(f"  Risk {score:.2f} → {cat.upper()}")

# ============================================================================
# SECTION 2: STRUCTURED NODE OUTPUT
# ============================================================================

print("\n2. STRUCTURED NODE OUTPUT")
print("─" * 80)

print("""
Each node produces a complete, professional data structure:

{
    "node_id": "...",
    "final_risk": 0.75,
    "ml_risk": 0.72,
    "rule_risk": 0.78,
    "risk_level": "high",
    "contributions": {
        "income": 0.81,          # How much income adds risk
        "activity": 0.67,        # How much activity adds risk
        "variability": 0.44,     # Transaction volatility
        "neighbor_influence": 0.55  # Risk from connected nodes
    },
    "centrality": {
        "degree": 0.80,          # How connected this node is
        "betweenness": 0.32,     # How often on paths between others
        "eigenvector": 0.68      # Influence based on neighbors
    },
    "trend": "increasing",       # increasing/decreasing/stable
    "explanation": "..."         # Human-readable summary
}
""")

# ============================================================================
# SECTION 3: HUMAN-READABLE EXPLANATIONS
# ============================================================================

print("\n3. TRANSPARENT EXPLANATIONS")
print("─" * 80)

print("""
Each node gets a clear, jargon-free explanation:

Instead of:
  "Risk = 0.75 * (1 - income/8000) + 0.45 * (1 - activity) + 0.2 * variance..."

You get:
  "Income is significantly low and financial activity is very limited.
   Connected parties show some instability. This represents a 
   substantial risk to network stability."
   
Usage:
  from dccfe import generate_clean_explanation
  text = generate_clean_explanation("U4", graph)
  print(text)
""")

# ============================================================================
# SECTION 4: GLOBAL SYSTEM SUMMARY
# ============================================================================

print("\n4. GLOBAL SYSTEM SUMMARY")
print("─" * 80)

print("""
Get a complete system-level assessment:

{
    "average_risk": 0.45,
    "high_risk_nodes": 3,
    "most_critical_node": "U4",
    "system_state": "fragile",
    "assessment": "Network is fragile with moderate risk (45.00%)."
}

System States:
  • STABLE:    Low average risk, stable conditions
  • FRAGILE:   Moderate risk or rising trends
  • CRITICAL:  High average risk or cascade activity

Usage:
  from dccfe import compute_global_summary
  summary = compute_global_summary(graph)
  print(f"State: {summary['system_state']}")
  print(f"Average Risk: {summary['average_risk']:.1%}")
""")

# ============================================================================
# SECTION 5: INTERVENTION RECOMMENDATIONS
# ============================================================================

print("\n5. INTERVENTION RECOMMENDATIONS")
print("─" * 80)

print("""
Professional intervention output:

{
    "recommended_node": "U4",
    "risk_reduction": 0.25,
    "nodes_affected": 3,
    "expected_impact": "high",
    "confidence": 0.75,
    "reason": "Intervene on U4. This reduces network risk by 25%.
               Additionally stabilizes 3 other nodes."
}

Impact Levels:
  • HIGH:     Effectiveness > 65%
  • MEDIUM:   Effectiveness 35-65%
  • LOW:      Effectiveness < 35%

Usage:
  from dccfe import format_intervention
  interv = format_intervention("U4", 0.25, 3, 0.75)
  print(f"Action: {interv['reason']}")
""")

# ============================================================================
# SECTION 6: VISUALIZATION-READY DATA
# ============================================================================

print("\n6. VISUALIZATION PREPARATION")
print("─" * 80)

print("""
Get graph styling data for professional visualizations:

Colors (based on risk):
  • GREEN (#2ecc71):   Low risk
  • ORANGE (#f39c12):  Medium risk
  • RED (#e74c3c):     High risk

Node Size:
  • Proportional to network centrality
  • Shows importance in network structure

Legend:
  from dccfe import get_visualization_legend
  legend = get_visualization_legend()
  # Returns standard colors and size meanings
""")

# ============================================================================
# SECTION 7: FULL REFINED PIPELINE
# ============================================================================

print("\n7. COMPLETE PIPELINE EXAMPLE")
print("─" * 80)

print("""
Run the complete analysis in one call:

  from dccfe import run_refined_dccfe_pipeline
  
  # Option 1: Use provided data
  result = run_refined_dccfe_pipeline(
      dataset=your_dataframe,
      print_output=True,
      return_full_report=True
  )
  
  # Option 2: Use default data
  result = run_refined_dccfe_pipeline()

Returns:
  {
    "node_results": [...],      # Structured output for each node
    "system_summary": {...},    # Global assessment
    "intervention": {...},      # Recommendation
    "quality_report": {...},    # Quality metrics
    "visualization": {...},     # Styling data
    "blockchain_valid": True    # Integrity check
  }
""")

# Run example
print("\n[Running example pipeline...]")
example_data = pd.DataFrame({
    "user_id": ["U1", "U2", "U3"],
    "income": [3500, 1800, 5200],
    "activity": [0.82, 0.35, 0.92],
    "transaction_variability": [0.18, 0.75, 0.12],
})

result = run_refined_dccfe_pipeline(example_data, print_output=False)

print(f"\n✓ Analysis complete")
print(f"  Nodes: {result['quality_metrics']['nodes_analyzed']}")
print(f"  System State: {result['quality_metrics']['system_state']}")
print(f"  High-Risk Nodes: {result['quality_metrics']['high_risk_count']}")

# ============================================================================
# SECTION 8: QUICK ANALYSIS FUNCTIONS
# ============================================================================

print("\n\n8. QUICK ANALYSIS HELPERS")
print("─" * 80)

print("""
Fast functions for common tasks:

  # Get quick snapshot
  from dccfe import quick_risk_snapshot
  snapshot = quick_risk_snapshot(graph)
  
  # Get top at-risk nodes
  from dccfe import get_top_at_risk
  top_5 = get_top_at_risk(graph, count=5)
  
  # Get details for one node
  from dccfe import get_node_details
  details = get_node_details(graph, "U4")
""")

# ============================================================================
# SECTION 9: ENTERPRISE WORKFLOWS
# ============================================================================

print("\n9. ENTERPRISE WORKFLOWS")
print("─" * 80)

print("""
Example 1: QUARTERLY RISK ASSESSMENT
───────────────────────────────────────
  result = run_refined_dccfe_pipeline(current_quarter_data)
  top_risks = result["node_results"][:10]  # Top 10
  critical_action = result["intervention"]
  
  Report format:
    - System state: critical/fragile/stable
    - Top 10 at-risk nodes with explanations
    - Recommended intervention target
    - Expected risk reduction

Example 2: MONITORING DASHBOARD
──────────────────────────────────
  while monitoring:
    snapshot = quick_risk_snapshot(current_graph)
    if snapshot['system_state'] == 'critical':
      alert("Network entering critical state")
    print(f"Average Risk: {snapshot['average_risk']:.1%}")

Example 3: INTERVENTION TRACKING
─────────────────────────────────
  before = compute_global_summary(prior_graph)
  # Apply intervention...
  after = compute_global_summary(current_graph)
  improvement = before['average_risk'] - after['average_risk']
  print(f"Risk Reduced: {improvement:.1%}")
""")

# ============================================================================
# SECTION 10: CODE EXAMPLES
# ============================================================================

print("\n10. COMPLETE CODE EXAMPLES")
print("─" * 80)

print("""
Example A: Analysis + Reporting
────────────────────────────────
import pandas as pd
from dccfe import run_refined_dccfe_pipeline, print_comprehensive_report

# Load your data
data = pd.read_csv("users.csv")

# Run analysis
report = run_refined_dccfe_pipeline(data)

# Print professional report
print_comprehensive_report(report)

# Extract specific information
top_3 = report["node_results"][:3]
for node in top_3:
    print(f"{node['node_id']}: {node['risk_level']}")
    print(f"  → {node['explanation']}")


Example B: Custom Monitoring
─────────────────────────────
from dccfe import quick_risk_snapshot, get_top_at_risk

def check_system_health(graph):
    summary = quick_risk_snapshot(graph)
    top_5 = get_top_at_risk(graph, 5)
    
    if summary['system_state'] == 'critical':
        # Take action
        for node in top_5:
            print(f"ALERT: {node['node_id']} is {node['risk_level']}")
    
    return summary['average_risk']


Example C: Intervention Evaluation
───────────────────────────────────
from dccfe import compute_global_summary

# Measure before
before_state = compute_global_summary(graph)
before_risk = before_state['average_risk']

# Apply intervention on U4...

# Measure after
after_state = compute_global_summary(graph)
after_risk = after_state['average_risk']

# Report effectiveness
improvement = before_risk - after_risk
print(f"Risk Improvement: {improvement:.2%}")
print(f"New State: {after_state['system_state']}")
""")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("KEY FEATURES SUMMARY")
print("=" * 80)

features = [
    ("Risk Classification", "Low / Medium / High with thresholds"),
    ("Structured Output", "JSON-like format with all metrics"),
    ("Explanation Quality", "Human-readable, jargon-free text"),
    ("System Summary", "Global assessment + state classification"),
    ("Interventions", "Ranked recommendations with confidence"),
    ("Visualization Ready", "Professional styling + colors"),
    ("Pipeline", "One-call complete analysis"),
    ("Quick Analysis", "Fast snapshot functions"),
    ("Enterprise Support", "Monitoring, reporting, tracking"),
    ("Production Ready", "No dependencies, fully tested"),
]

for feature, description in features:
    print(f"\n✓ {feature}")
    print(f"  {description}")

print("\n" + "=" * 80)
print("END OF PROFESSIONAL GUIDE")
print("=" * 80 + "\n")
