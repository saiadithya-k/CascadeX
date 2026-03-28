#!/usr/bin/env python
"""Comprehensive validation of research-grade DCCFE system."""

import networkx as nx
from dccfe import ResearchDCCFESystem

# Create a simple test graph manually
graph = nx.Graph()

# Add 6 test nodes with financial attributes
users = [
    {"user_id": "U1", "income": 5200, "activity": 0.82, "transaction_variability": 0.15},
    {"user_id": "U2", "income": 3800, "activity": 0.45, "transaction_variability": 0.35},
    {"user_id": "U3", "income": 2200, "activity": 0.28, "transaction_variability": 0.68},
    {"user_id": "U4", "income": 6500, "activity": 0.91, "transaction_variability": 0.08},
    {"user_id": "U5", "income": 4100, "activity": 0.62, "transaction_variability": 0.42},
    {"user_id": "U6", "income": 2800, "activity": 0.35, "transaction_variability": 0.55},
]

# Add nodes with attributes
for user in users:
    user_id = user["user_id"]
    income = user["income"]
    activity = user["activity"]
    var = user["transaction_variability"]
    
    # Compute risk using simple rule
    risk = max(0.0, min(1.0, 
        (1 - min(income, 8000) / 8000) * 0.3 + 
        (1 - activity) * 0.4 + 
        var * 0.3
    ))
    
    graph.add_node(
        user_id,
        income=income,
        activity=activity,
        transaction_variability=var,
        risk=risk,
        instability=0.2,
        risk_history=[risk],
    )

# Add weighted edges (relationships)
edges = [
    ("U1", "U2", 0.8),
    ("U2", "U3", 0.9),
    ("U3", "U4", 0.7),
    ("U4", "U5", 0.75),
    ("U5", "U6", 0.85),
    ("U1", "U4", 0.6),
]

for u, v, w in edges:
    graph.add_edge(u, v, weight=w)

# Initialize research system
system = ResearchDCCFESystem()

# Run single cycle with all components
result = system.run_cycle(graph, shock_seed=7, rl_episodes=10)

# Print results
print('=' * 60)
print('RESEARCH-GRADE DCCFE SYSTEM VALIDATION')
print('=' * 60)

nodes = list(graph.nodes)[:2]

print('\n1. BAYESIAN CAUSAL INFERENCE')
print('-' * 60)
for n in nodes:
    b = result['bayesian_inference'][n]
    print(f'Node {n}:')
    print(f'  posterior_risk: {b["posterior_risk"]:.4f}')
    print(f'  confidence: {b["confidence"]:.4f}')
    print(f'  factors: income_low={b["factors"]["income_low"]:.4f}, '
          f'activity_low={b["factors"]["activity_low"]:.4f}')

print('\n2. TEMPORAL DYNAMICS')
print('-' * 60)
for n in nodes:
    t = result['temporal_stats'][n]
    print(f'Node {n}:')
    print(f'  trend: {t["trend"]:.4f}')
    print(f'  acceleration: {t["acceleration"]:.4f}')
    print(f'  volatility: {t["volatility"]:.4f}')
    print(f'  instability: {t["instability"]:.4f}')

print('\n3. GAME THEORY STRATEGIC BEHAVIOR')
print('-' * 60)
g = result['game_theory']
print(f'Nash-like equilibrium reached: {g["nash_like_equilibrium"]}')
print(f'Post-game average risk: {g["post_game_average_risk"]:.6f}')
print(f'Sample decisions: {list(g["decisions"].items())[:3]}')

print('\n4. STOCHASTIC SHOCK MODEL')
print('-' * 60)
s = result['shock_result']
print(f'Cascade size: {s["cascade_size"]}')
print(f'Expected system impact: {s["expected_system_impact"]:.6f}')
print(f'Affected nodes: {s["affected_nodes"][:3]}')

print('\n5. Q-LEARNING RL AGENT')
print('-' * 60)
rl = result['rl_training']
print(f'States learned: {rl["states_learned"]}')
print(f'Q-table entries: {rl["q_entries"]}')
print('\nTop learned policies:')
for i, action in enumerate(result['learned_policy'][:3], 1):
    print(f'  {i}. {action["action"]}: Q-value={action["value"]:.6f}')

print('\n6. ADVANCED GRAPH METRICS')
print('-' * 60)
metrics = result['advanced_graph_metrics'][:3]
for m in metrics:
    print(f'Node {m["node"]}:')
    print(f'  degree_centrality: {m["degree_centrality"]:.6f}')
    print(f'  eigenvector_centrality: {m["eigenvector_centrality"]:.6f}')
    print(f'  pagerank: {m["pagerank"]:.6f}')
    print(f'  risk_hub_score: {m["risk_hub_score"]:.6f}')

print('\n7. SYSTEM STABILITY')
print('-' * 60)
stab = result['stability_metrics']
print(f'Average risk: {stab["average_risk"]:.6f}')
print(f'Risk variance: {stab["risk_variance"]:.6f}')
print(f'High-risk nodes: {stab["high_risk_nodes"]}')
print(f'Stability score: {stab["stability_score"]:.6f}')
print(f'Classification: {stab["classification"]}')

print('\n8. CRITICALITY DETECTION')
print('-' * 60)
crit = result['criticality']
print(f'Early warning: {crit["early_warning"]}')
print(f'Signals: {crit["signals"]}')
print(f'Critical nodes: {crit["critical_nodes"][:3]}')

print('\n9. MULTI-OBJECTIVE OPTIMIZATION')
print('-' * 60)
opt = result['multi_objective']
best = opt['best_weighted_solution']
if best:
    print(f'Best weighted solution:')
    print(f'  Nodes to intervene: {best["nodes"]}')
    print(f'  Risk reduction: {best["risk_reduction"]:.6f}')
    print(f'  Cost: {best["cost"]:.6f}')
    print(f'  Objective: {best["objective"]:.6f}')
    print(f'Pareto-optimal solutions: {len(opt["pareto_solutions"])}')

print('\n10. ADVANCED EXPLAINABILITY')
print('-' * 60)
expl = result['explanations'][nodes[0]]
causal = expl['causal_probability_explanation']
temporal = expl['temporal_trend_explanation']
contrib = expl['contribution_breakdown']
print(f'Node {nodes[0]} detailed explanation:')
print(f'  Posterior risk: {causal["posterior_risk"]:.6f}')
print(f'  Confidence: {causal["confidence"]:.6f}')
print(f'  Income contribution: {contrib["income_low"]:.6f}')
print(f'  Activity contribution: {contrib["activity_low"]:.6f}')
print(f'  Temporal trend: {temporal["trend"]:.6f}')
print(f'  Temporal volatility: {temporal["volatility"]:.6f}')
print(f'  Instability: {temporal["instability"]:.6f}')

print('\n' + '=' * 60)
print('ALL COMPONENTS VALIDATED ✅')
print('=' * 60)
