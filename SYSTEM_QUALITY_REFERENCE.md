# DCCFE System Quality: Core Quality Enhancements

## Overview

The DCCFE System Quality module provides **intelligent behavior analysis, clear explanations, stability monitoring, and smart interventions** to ensure the financial network operates with transparency and effectiveness.

---

## 1. System Behavior Analysis

### Purpose
Track how individual nodes' financial risk evolves over time and detect patterns that indicate system health.

### Key Features

#### `analyze_node_behavior(graph, observation_window=10)`
Analyzes each node's risk trajectory and classifies behavior.

**Returns:**
```python
NodeBehavior(
    node: str                    # Node ID
    current_risk: float          # Current risk value [0-1]
    trend: str                   # "escalating", "recovering", or "stable"
    risk_change: float           # Change from start of window
    history_length: int          # How many historical points tracked
    avg_risk: float              # Average risk in observation window
    is_cascade_source: bool      # Does this node trigger cascades?
    affected_nodes: List[str]    # Which nodes this one influences
)
```

**Example:**
```python
from dccfe import analyze_node_behavior

behaviors = analyze_node_behavior(graph, observation_window=5)
for b in behaviors:
    if b.trend == "escalating":
        print(f"⚠️  {b.node}: Risk increasing ({b.risk_change:+.4f})")
    elif b.trend == "recovering":
        print(f"✅ {b.node}: Risk decreasing ({b.risk_change:+.4f})")
```

#### `detect_cascade_effects(graph, behaviors)`
Identifies cascade patterns where one node's risk affects others.

**Returns:**
```python
{
    "cascade_count": int,           # Number of cascade sources
    "cascade_sources": List[str],   # Which nodes cause cascades
    "total_secondary_nodes": int,   # Nodes affected by cascades
    "average_cascade_size": float,  # Avg nodes per cascade
    "cascade_activity": str         # "high", "moderate", or "low"
}
```

---

## 2. Explanation Quality

### Purpose
Translate technical data into clear, human-readable explanations that stakeholders can understand without domain expertise.

### Key Features

#### `generate_human_explanation(node, graph, bayes_inference=None)`
Creates a natural language explanation of why a node has its current risk level.

**Returns:** String explanation with:
- Primary cause (e.g., "low income")
- Secondary influence (e.g., "influence from high-risk neighbors")
- System effect (e.g., "poses significant risk to network")

**Example:**
```python
from dccfe import generate_human_explanation

explanation = generate_human_explanation("U3", graph)
print(explanation)
# Output: "Risk increased due to low income. Financial instability of 
#          connected parties is further increasing the risk. This node 
#          poses a significant risk to overall network stability."
```

#### `generate_node_explanations(graph, behaviors, bayes_inference=None)`
Generates explanations for all nodes at once.

**Returns:** Dict mapping node IDs to explanation strings.

---

## 3. System Stability Analysis

### Purpose
Monitor global network health and detect systemic risks at the system level.

### Key Features

#### `compute_system_stability_advanced(graph)`
Comprehensive system-level stability assessment.

**Returns:**
```python
SystemStability(
    average_risk: float             # Network average risk [0-1]
    risk_variance: float            # Spread of risk across nodes
    rate_of_change: float           # How fast risk is changing
    classification: str             # "stable", "fragile", or "critical"
    high_risk_nodes: int            # Count of nodes with risk > 0.7
    instability_clusters: List      # Groups of neighboring high-risk nodes
    trend_description: str          # Human-readable assessment
)
```

**Classification Logic:**
- **Stable**: Low average risk + low variance + slow change
- **Fragile**: Moderate risk or rising trend
- **Critical**: High average risk or rapid increase

**Example:**
```python
from dccfe import compute_system_stability_advanced

stability = compute_system_stability_advanced(graph)
print(f"Status: {stability.classification}")
print(f"Assessment: {stability.trend_description}")

if stability.instability_clusters:
    print(f"⚠️  Instability clusters: {stability.instability_clusters}")
```

---

## 4. Intervention Quality Improvement

### Purpose
Recommend the most effective interventions by simulating outcomes before implementation.

### Key Features

#### `evaluate_interventions(graph, candidates=None, max_interventions=5, risk_reduction_factor=0.3)`
Evaluates multiple intervention options through simulation and ranks them.

**Returns:** List of ranked `InterventionOption` objects:
```python
InterventionOption(
    target_nodes: List[str]         # Which nodes to intervene on
    effectiveness_score: float      # Total network risk reduction
    reach_score: int                # Number of nodes stabilized
    cascade_mitigation: float       # Reduction in cascade activity
    overall_rank_score: float       # Combined weighted score
    justification: str              # Why this intervention works
)
```

**Simulation Process:**
1. Reduce target node's risk by `risk_reduction_factor`
2. Propagate effects to neighboring nodes
3. Measure: network-wide risk reduction, nodes stabilized, cascades reduced
4. Rank by weighted combination: 50% effectiveness + 30% reach + 20% cascade mitigation

**Example:**
```python
from dccfe import evaluate_interventions

high_risk_nodes = [n for n in graph.nodes 
                   if graph.nodes[n].get("risk", 0) > 0.65]

options = evaluate_interventions(graph, candidates=high_risk_nodes)

for i, opt in enumerate(options, 1):
    print(f"{i}. Intervene on {opt.target_nodes[0]}")
    print(f"   Effectiveness: {opt.effectiveness_score:.4f}")
    print(f"   Why: {opt.justification}")
```

---

## 5. Consistency Check

### Purpose
Validate that the system behaves realistically with smooth, continuous transitions.

### Key Features

#### `validate_consistency(graph, previous_graph=None, max_risk_jump=0.15)`
Checks for anomalies and unrealistic behavior.

**Validations:**
- Risk values stay within [0.0, 1.0]
- Risk changes between iterations don't exceed `max_risk_jump`
- Risk history is continuous (no sudden spikes)

**Returns:**
```python
{
    "is_valid": bool,              # Overall validity
    "anomaly_count": int,          # Number of issues found
    "anomalies": List[str],        # Specific anomaly descriptions
    "consistency_score": float     # 0-1 score (1 = perfect consistency)
}
```

**Example:**
```python
from dccfe import validate_consistency

check = validate_consistency(graph, previous_graph=old_graph, max_risk_jump=0.20)

if not check["is_valid"]:
    print(f"⚠️  Found {check['anomaly_count']} consistency issues:")
    for anomaly in check["anomalies"]:
        print(f"   - {anomaly}")
else:
    print("✅ System is consistent")
```

---

## 6. Integrated Quality Report

### Purpose
Combine all quality analyses into one comprehensive report for decision-making.

### Key Features

#### `generate_quality_report(graph, previous_graph=None, bayes_inference=None)`
Generates complete quality assessment in a single call.

**Returns:**
```python
{
    "node_behavior": [
        {
            "node": str,
            "current_risk": float,
            "trend": str,              # escalating/recovering/stable
            "risk_change": float,
            "is_cascade_source": bool,
            "affected_nodes": List[str]
        }
    ],
    "cascade_summary": {
        "cascade_count": int,
        "cascade_activity": str,
        ...
    },
    "node_explanations": {
        "node_id": "explanation text",
        ...
    },
    "system_stability": {
        "average_risk": float,
        "classification": str,
        "instability_clusters": List,
        "trend": str
    },
    "interventions": [
        {
            "target": List[str],
            "effectiveness": float,
            "reach": int,
            "confidence": float,
            "reason": str
        }
    ],
    "best_action": {
        "target": List[str],
        "effectiveness": float,
        "confidence": float,
        "reason": str
    },
    "consistency": {
        "is_valid": bool,
        "anomaly_count": int,
        "consistency_score": float
    }
}
```

**Example:**
```python
from dccfe import generate_quality_report

report = generate_quality_report(graph)

# Access all components
print(f"System Status: {report['system_stability']['classification']}")
print(f"Best Action: {report['best_action']['target']}")
print(f"Consistency: {report['consistency']['consistency_score']:.4f}")

# Review node-by-node
for behavior in report['node_behavior']:
    print(f"{behavior['node']}: {report['node_explanations'][behavior['node']]}")
```

---

## 7. Pipeline Integration

### Purpose
Automatically add quality analysis to standard pipeline runs.

### Key Features

#### `enhance_pipeline_output(pipeline_result, enable_quality_report=True)`
Enhances DCCFE pipeline output with quality analysis.

**Example:**
```python
from dccfe import run_dccfe_pipeline, enhance_pipeline_output

# Run standard pipeline
result = run_dccfe_pipeline()

# Add quality analysis
enhanced = enhance_pipeline_output(result, enable_quality_report=True)

# Access quality metrics
quality = enhanced["system_quality"]
print(f"System: {quality['system_classification']}")
print(f"Consistency: {quality['consistency_score']:.4f}")
```

#### `print_quality_summary(enhanced_result)`
Prints human-readable quality summary.

**Example:**
```python
from dccfe import print_quality_summary

print_quality_summary(enhanced_result)

# Output:
# ────────────────────────────────────
# SYSTEM QUALITY SUMMARY
# ────────────────────────────────────
# Status: healthy
# System Classification: stable
# Cascade Activity: low
# Consistency Score: 0.9999
# ...
```

---

## Complete Workflow Example

```python
from dccfe import (
    analyze_node_behavior,
    generate_human_explanation,
    compute_system_stability_advanced,
    evaluate_interventions,
    validate_consistency,
    generate_quality_report,
)

# 1. Analyze behaviors
behaviors = analyze_node_behavior(graph)

# 2. Find escalating nodes
escalating = [b for b in behaviors if b.trend == "escalating"]
if escalating:
    print(f"⚠️  Alert: {len(escalating)} nodes at risk")

# 3. Check stability
stability = compute_system_stability_advanced(graph)
if stability.classification == "critical":
    print("🚨 Critical system state")

# 4. Generate explanations
for node in escalating:
    exp = generate_human_explanation(node.node, graph)
    print(f"{node.node}: {exp}")

# 5. Evaluate interventions
options = evaluate_interventions(graph, 
                                candidates=[b.node for b in escalating])

# 6. Recommend best action
best = options[0]
print(f"Recommended: Intervene on {best.target_nodes[0]}")
print(f"Expected Result: {best.justification}")

# 7. Validate consistency
check = validate_consistency(graph)
if not check["is_valid"]:
    print(f"⚠️  Consistency issues: {check['anomalies']}")

# 8. Generate full report
report = generate_quality_report(graph)
print(f"Full assessment saved to report")
```

---

## Key Design Principles

### 1. **Clarity Over Complexity**
- Natural language explanations, not formulas
- Clear classifications (stable/fragile/critical)
- Transparent reasoning for recommendations

### 2. **Simulation-Based Validation**
- Interventions evaluated through simulation
- No blind recommendations
- Confidence scores based on actual impact

### 3. **System-Wide View**
- Detect cascade effects and clusters
- Monitor global metrics
- Assess interconnection risks

### 4. **Consistency Assurance**
- Validate smooth transitions
- Detect anomalies
- Ensure realistic behavior

### 5. **Integrated Analysis**
- All components work together
- Single quality report combines everything
- Easy pipeline integration

---

## Performance Characteristics

| Function | Complexity | Time (8 nodes) | Notes |
|----------|------------|----------------|-------|
| `analyze_node_behavior` | O(n log n) | < 1ms | Sorting by risk |
| `generate_human_explanation` | O(n) | < 1ms | Neighbor traversal |
| `compute_system_stability` | O(n²) | < 1ms | Cluster detection |
| `evaluate_interventions` | O(k*n²) | ~10ms | k simulations |
| `validate_consistency` | O(n*h) | < 1ms | h = history depth |
| `generate_quality_report` | O(k*n²) | ~10ms | Combined cost |

---

## API Reference Summary

### Core Analysis
- `analyze_node_behavior()` - Node behavior classification
- `detect_cascade_effects()` - Cascade pattern detection
- `generate_human_explanation()` - Natural language explanation
- `generate_node_explanations()` - Bulk explanations
- `compute_system_stability_advanced()` - System-level assessment
- `evaluate_interventions()` - Ranked intervention options
- `validate_consistency()` - Anomaly detection

### Integrated
- `generate_quality_report()` - Complete quality assessment

### Pipeline
- `enhance_pipeline_output()` - Add quality to pipeline
- `print_quality_summary()` - Print summary

---

## Common Use Cases

### 1. **Safety Check Before Intervention**
```python
options = evaluate_interventions(graph)
best = options[0]
if best.overall_rank_score > 0.5:  # High confidence threshold
    execute_intervention(best.target_nodes)
```

### 2. **Continuous Monitoring**
```python
report = generate_quality_report(graph)
if report['system_stability']['classification'] == 'critical':
    trigger_alert()
```

### 3. **Stakeholder Reporting**
```python
for node in graph.nodes:
    exp = generate_human_explanation(node, graph)
    report[node] = exp  # Non-technical explanation
```

### 4. **Cascade Risk Management**
```python
cascades = detect_cascade_effects(graph, behaviors)
if cascades['cascade_activity'] == 'high':
    focus_on_cascade_sources(cascades['cascade_sources'])
```

### 5. **System Health Dashboard**
```python
stability = compute_system_stability_advanced(graph)
dashboard = {
    "status": stability.classification,
    "avg_risk": stability.average_risk,
    "clusters": len(stability.instability_clusters),
    "consistency": validate_consistency(graph)['consistency_score']
}
```

---

## Error Handling

The system quality module is designed to fail gracefully:

```python
try:
    report = generate_quality_report(graph)
except Exception as e:
    # Returns empty report, system continues
    report = None
    logger.warning(f"Quality report generation failed: {e}")
```

All functions include bounds checking and default values to prevent crashes.

---

## Next Steps

1. **Integrate into monitoring dashboard**
2. **Set up automated alerts for critical states**
3. **Use intervention recommendations for policy decisions**
4. **Track consistency trends over time**
5. **Customize thresholds for your specific risk profile**

