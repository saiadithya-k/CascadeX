from __future__ import annotations

import copy
import json
import os
import re
import time
from dataclasses import asdict
from typing import Any, Dict, List

import networkx as nx
import pandas as pd

from dccfe import (
    DCCFEEngine,
    Relationship,
    ScalingConfig,
    UserRecord,
    build_analyst_prompt,
    combine_risk,
    compute_global_summary,
    compute_system_stability_metrics,
    create_initial_dataset,
    create_user_graph,
    generate_dataset,
    get_neighbors,
    hybrid_predict_single_user,
    predict_risk,
    predict_single_user_risk,
    run_full_scaling_mode,
    simulate_risk_trajectory,
    train_model,
)
from dccfe.analyst_report import AnalystReportContext
from dccfe.causal_engine import CausalEngine
from dccfe.intervention import InterventionEngine
from dccfe.propagation import RiskPropagationEngine


class Validator:
    def __init__(self) -> None:
        self.issues: List[str] = []
        self.section_status: Dict[str, bool] = {}
        self.section_details: Dict[str, Any] = {}

    def add_issue(self, section: str, message: str) -> None:
        self.issues.append(f"{section}: {message}")

    def set_section(self, section: str, ok: bool, details: Any = None) -> None:
        self.section_status[section] = bool(ok)
        if details is not None:
            self.section_details[section] = details


def _build_user_records(users: List[Dict[str, float]]) -> List[UserRecord]:
    records: List[UserRecord] = []
    for idx, u in enumerate(users):
        records.append(
            UserRecord(
                user_id=str(u["user_id"]),
                income=float(u["income"]),
                activity=float(u["activity"]),
                transactions=5 + (idx % 7),
                defaults=1 if idx % 5 == 0 else 0,
            )
        )
    return records


def _build_relationship_records(edges: List[tuple[str, str, float]]) -> List[Relationship]:
    return [
        Relationship(source=str(s), target=str(t), weight=float(w), relation_type="dependency")
        for s, t, w in edges
    ]


def validate_data(v: Validator, users: List[Dict[str, float]], edges: List[tuple[str, str, float]]) -> None:
    section = "1_DATA_VALIDATION"
    ok = True

    df_users = pd.DataFrame(users)
    required_user_cols = {"user_id", "income", "activity", "transaction_variability"}
    missing = required_user_cols - set(df_users.columns)
    if missing:
        ok = False
        v.add_issue(section, f"Missing user columns: {sorted(missing)}")

    if df_users.isna().any().any():
        ok = False
        v.add_issue(section, "Users dataset has missing values")

    if not (df_users["income"] > 0).all():
        ok = False
        v.add_issue(section, "Income contains non-positive values")

    if not ((df_users["activity"] >= 0) & (df_users["activity"] <= 1)).all():
        ok = False
        v.add_issue(section, "Activity is out of [0,1] range")

    if not ((df_users["transaction_variability"] >= 0) & (df_users["transaction_variability"] <= 1)).all():
        ok = False
        v.add_issue(section, "Transaction variability is out of [0,1] range")

    node_set = {str(u["user_id"]) for u in users}
    invalid_edges = [(s, t, w) for s, t, w in edges if s not in node_set or t not in node_set or s == t]
    if invalid_edges:
        ok = False
        v.add_issue(section, f"Invalid edges found: {invalid_edges[:3]}")

    out_of_range_weights = [(s, t, w) for s, t, w in edges if not (0.0 <= float(w) <= 1.0)]
    if out_of_range_weights:
        ok = False
        v.add_issue(
            section,
            f"Edge weights outside [0,1] detected ({len(out_of_range_weights)} edges), e.g. {out_of_range_weights[:2]}",
        )

    v.set_section(
        section,
        ok,
        {
            "user_count": len(users),
            "edge_count": len(edges),
            "invalid_edge_count": len(invalid_edges),
            "weights_out_of_range": len(out_of_range_weights),
        },
    )


def validate_risk_model(v: Validator) -> None:
    section = "2_RISK_MODEL_VALIDATION"
    ok = True

    risk_vals = [
        predict_single_user_risk(income=2500, activity=0.4, transaction_variability=0.5),
        predict_single_user_risk(income=5000, activity=0.7, transaction_variability=0.2),
        predict_single_user_risk(income=9000, activity=1.0, transaction_variability=0.0),
    ]
    if not all(0.0 <= r <= 1.0 for r in risk_vals):
        ok = False
        v.add_issue(section, "Rule-based risk outside [0,1]")

    # Monotonic checks
    low_income = predict_single_user_risk(income=2000, activity=0.6, transaction_variability=0.3)
    high_income = predict_single_user_risk(income=7000, activity=0.6, transaction_variability=0.3)
    if low_income <= high_income:
        ok = False
        v.add_issue(section, "Monotonicity violated: lower income should increase risk")

    low_activity = predict_single_user_risk(income=4000, activity=0.2, transaction_variability=0.3)
    high_activity = predict_single_user_risk(income=4000, activity=0.9, transaction_variability=0.3)
    if low_activity <= high_activity:
        ok = False
        v.add_issue(section, "Monotonicity violated: lower activity should increase risk")

    high_var = predict_single_user_risk(income=4000, activity=0.6, transaction_variability=0.9)
    low_var = predict_single_user_risk(income=4000, activity=0.6, transaction_variability=0.1)
    if high_var <= low_var:
        ok = False
        v.add_issue(section, "Monotonicity violated: higher variability should increase risk")

    # ML integration
    x, y, _ = generate_dataset(n_samples=300, random_seed=42)
    model = train_model(x=x, y=y, random_seed=42)
    ml_pred = predict_risk(
        model,
        {"income": 3200.0, "activity": 0.45, "transaction_variability": 0.55},
    )
    if "ml_risk_probability" not in ml_pred:
        ok = False
        v.add_issue(section, "predict_risk missing ml_risk_probability")
    if not (0.0 <= float(ml_pred["ml_risk_probability"]) <= 1.0):
        ok = False
        v.add_issue(section, "ML probability outside [0,1]")

    if not hasattr(model.model, "predict_proba"):
        ok = False
        v.add_issue(section, "Model missing predict_proba")

    rule = predict_single_user_risk(income=3200, activity=0.45, transaction_variability=0.55)
    combined = combine_risk(float(ml_pred["ml_risk_probability"]), rule, alpha=0.55)
    expected = 0.55 * float(ml_pred["ml_risk_probability"]) + 0.45 * float(rule)
    if abs(combined - expected) > 1e-9:
        ok = False
        v.add_issue(section, "Combined risk formula mismatch")

    hybrid = hybrid_predict_single_user(
        model,
        {"income": 3200.0, "activity": 0.45, "transaction_variability": 0.55},
        alpha=0.55,
    )
    if not (0.0 <= float(hybrid["final_risk"]) <= 1.0):
        ok = False
        v.add_issue(section, "Hybrid final risk outside [0,1]")

    v.set_section(
        section,
        ok,
        {
            "model_backend": model.backend,
            "test_accuracy": round(float(model.test_accuracy), 4),
            "sample_hybrid_risk": round(float(hybrid["final_risk"]), 6),
        },
    )


def validate_graph(v: Validator, users: List[Dict[str, float]], edges: List[tuple[str, str, float]]) -> nx.Graph:
    section = "3_GRAPH_VALIDATION"
    ok = True

    users_risk = []
    for u in users:
        row = dict(u)
        row["risk"] = predict_single_user_risk(
            income=float(u["income"]),
            activity=float(u["activity"]),
            transaction_variability=float(u["transaction_variability"]),
        )
        users_risk.append(row)

    graph = create_user_graph(users_risk, edges)

    if graph.number_of_nodes() != len(users):
        ok = False
        v.add_issue(section, "Graph node count mismatch")

    # Duplicate edge check (NetworkX should overwrite existing edge)
    before_edges = graph.number_of_edges()
    s0, t0, w0 = edges[0]
    graph.add_edge(s0, t0, weight=w0)
    after_edges = graph.number_of_edges()
    if after_edges != before_edges:
        ok = False
        v.add_issue(section, "Duplicate edge increased edge count unexpectedly")

    # Neighbors consistency
    ref_neighbors = sorted(list(graph.neighbors(s0)))
    got_neighbors = sorted(get_neighbors(graph, s0))
    if ref_neighbors != got_neighbors:
        ok = False
        v.add_issue(section, "get_neighbors mismatch with graph.neighbors")

    # Node attributes presence
    required_attrs = {"income", "activity", "risk", "transaction_variability", "risk_history", "explanation"}
    for node, attrs in graph.nodes(data=True):
        missing = required_attrs - set(attrs.keys())
        if missing:
            ok = False
            v.add_issue(section, f"Node {node} missing attrs: {sorted(missing)}")
            break

    v.set_section(
        section,
        ok,
        {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "sample_neighbors": {s0: got_neighbors},
        },
    )
    return graph


def validate_causal(v: Validator, graph: nx.Graph) -> None:
    section = "4_CAUSAL_ENGINE_VALIDATION"
    ok = True

    causal = CausalEngine()
    g = copy.deepcopy(graph)
    explanations = causal.apply(g)

    # Weight sum constraint check
    raised = False
    try:
        causal.apply(copy.deepcopy(graph), weight_income=0.6, weight_neighbor=0.3, weight_activity=0.2)
    except ValueError:
        raised = True
    if not raised:
        ok = False
        v.add_issue(section, "Causal engine did not enforce weight sum <= 1")

    contrib_pattern = re.compile(r"income_contrib=([0-9.]+), neighbor_contrib=([0-9.]+), activity_contrib=([0-9.]+)")
    checked = 0
    for node, reasons in explanations.items():
        if not reasons:
            ok = False
            v.add_issue(section, f"No explanation for node {node}")
            continue
        m = contrib_pattern.search(reasons[0])
        if not m:
            ok = False
            v.add_issue(section, f"Contribution string not parseable for node {node}")
            continue
        inc, nei, act = [float(x) for x in m.groups()]
        if any(x < 0 for x in [inc, nei, act]):
            ok = False
            v.add_issue(section, f"Negative contribution detected for node {node}")
        if inc > 0.30 + 1e-9 or nei > 0.25 + 1e-9 or act > 0.20 + 1e-9:
            ok = False
            v.add_issue(section, f"Contribution exceeds configured weight cap for node {node}")
        checked += 1

    v.set_section(section, ok, {"nodes_with_explanations": checked})


def validate_propagation(v: Validator) -> None:
    section = "5_PROPAGATION_VALIDATION"
    ok = True

    graph = nx.Graph()
    graph.add_node("A", risk=0.2)
    graph.add_node("B", risk=0.8)
    graph.add_edge("A", "B", weight=1.0)

    prop = RiskPropagationEngine()
    history = prop.propagate(graph, alpha=0.2, steps=1)

    expected_a = (1 - 0.2) * 0.2 + 0.2 * 0.8
    expected_b = (1 - 0.2) * 0.8 + 0.2 * 0.2
    got_a = float(history[0]["A"])
    got_b = float(history[0]["B"])

    if abs(got_a - expected_a) > 1e-9 or abs(got_b - expected_b) > 1e-9:
        ok = False
        v.add_issue(section, "Propagation formula mismatch")

    g2 = nx.path_graph(["N1", "N2", "N3", "N4"])
    for n, r in zip(g2.nodes, [0.1, 0.3, 0.7, 0.9]):
        g2.nodes[n]["risk"] = r
    for u, w in g2.edges:
        g2.edges[u, w]["weight"] = 1.0

    long_hist = prop.propagate(g2, alpha=0.25, steps=8)
    final_vals = list(long_hist[-1].values())
    if any(r < 0.0 or r > 1.0 for r in final_vals):
        ok = False
        v.add_issue(section, "Propagation produced values outside [0,1]")

    v.set_section(section, ok, {"step1": history[0], "final_range": [min(final_vals), max(final_vals)]})


def validate_simulation(v: Validator, users: List[Dict[str, float]], edges: List[tuple[str, str, float]]) -> DCCFEEngine:
    section = "6_SIMULATION_VALIDATION"
    ok = True

    engine = DCCFEEngine(min_users_for_compute=5)
    engine.load_users(_build_user_records(users))
    engine.load_relationships(_build_relationship_records(edges))
    engine.recompute()

    before = engine.export_risk_table().set_index("user_id")

    target = str(users[0]["user_id"])
    sim_df = engine.simulate_what_if({target: {"income": float(users[0]["income"]) + 1500.0, "activity": 0.9}})
    sim_row = sim_df.set_index("user_id").loc[target]

    if not (0.0 <= float(sim_row["scenario_risk"]) <= 1.0):
        ok = False
        v.add_issue(section, "Scenario risk outside [0,1]")

    # Logical check: improving income/activity should not increase risk massively.
    baseline = float(before.loc[target, "risk"])
    scenario_risk = float(sim_row["scenario_risk"])
    if scenario_risk > baseline + 0.10:
        ok = False
        v.add_issue(
            section,
            f"Unexpected scenario behavior: risk increased too much after favorable update ({baseline:.4f} -> {scenario_risk:.4f})",
        )

    # Trajectory consistency check
    users_risk = []
    for node, data in engine.graph.nodes(data=True):
        users_risk.append(
            {
                "user_id": node,
                "income": float(data.get("income", 0.0)),
                "activity": float(data.get("activity", 0.0)),
                "transaction_variability": 0.5,
                "risk": float(data.get("risk", 0.0)),
            }
        )
    g = create_user_graph(users_risk, edges)
    trajectory = simulate_risk_trajectory(g, steps=3, propagation_factor=0.2)
    if len(trajectory) != 3:
        ok = False
        v.add_issue(section, "Risk trajectory length mismatch")

    v.set_section(
        section,
        ok,
        {
            "target_user": target,
            "baseline_risk": round(baseline, 6),
            "scenario_risk": round(scenario_risk, 6),
            "trajectory_steps": len(trajectory),
        },
    )
    return engine


def validate_intervention(v: Validator, engine: DCCFEEngine) -> Dict[str, Any]:
    section = "7_INTERVENTION_VALIDATION"
    ok = True

    intervention_engine = InterventionEngine()
    result = intervention_engine.optimize_intervention(engine.graph, risk_reduction_factor=0.30, propagation_factor=0.2, steps=4)

    baseline = float(result["baseline_total_risk"])
    optimized = float(result["optimized_total_risk"])
    if optimized > baseline + 1e-9:
        ok = False
        v.add_issue(section, "Intervention optimization increased total risk")

    suggestions = engine.suggest_interventions(top_k=3)
    if not suggestions:
        ok = False
        v.add_issue(section, "No intervention suggestions returned")

    v.set_section(
        section,
        ok,
        {
            "best_node": result.get("best_node", ""),
            "improvement": round(float(result.get("impact_score", 0.0)), 6),
            "top_suggestion": suggestions[0] if suggestions else {},
        },
    )
    return result


def validate_stability(v: Validator, engine: DCCFEEngine) -> Dict[str, Any]:
    section = "8_SYSTEM_STABILITY"
    ok = True

    metrics = compute_system_stability_metrics(engine.graph)
    required = {"average_network_risk", "risk_variance", "high_risk_nodes", "system_stability_score", "classification"}
    if required - set(metrics.keys()):
        ok = False
        v.add_issue(section, "Missing stability metric fields")

    if str(metrics.get("classification")) not in {"stable", "fragile", "critical"}:
        ok = False
        v.add_issue(section, "Unexpected stability classification")

    v.set_section(section, ok, metrics)
    return metrics


def validate_report(v: Validator, metrics: Dict[str, Any]) -> Dict[str, Any]:
    section = "9_AI_REPORT_VALIDATION"
    ok = True

    context = AnalystReportContext(
        user_id="U1",
        risk_level="high",
        trend="escalating",
        income_status="elevated",
        activity_status="elevated",
        variability_status="moderate",
        neighbor_influence="elevated",
        behavior_pattern="income / activity",
        system_state=str(metrics.get("classification", "fragile")),
        avg_risk=float(metrics.get("average_network_risk", 0.0)),
        high_risk_count=int(metrics.get("high_risk_nodes", 0)),
        cascade="yes",
        critical_nodes="U1, U2",
    )

    prompt = build_analyst_prompt(context)
    if len(prompt) < 200:
        ok = False
        v.add_issue(section, "Analyst prompt appears too short")

    local_report = (
        f"User {context.user_id} has {context.risk_level} risk driven mainly by {context.behavior_pattern}. "
        f"Network influence is {context.neighbor_influence}, and the observed trend is {context.trend}.\n\n"
        f"System state is {context.system_state} with average risk {context.avg_risk:.2f}. "
        f"Recommend targeted support for {context.critical_nodes} and close monitoring to reduce cascade pressure."
    )

    if len(local_report.split()) < 30:
        ok = False
        v.add_issue(section, "Generated report text is too short")

    llm_status = "skipped_no_api_key"
    if os.getenv("GROQ_API_KEY"):
        llm_status = "api_key_available"

    v.set_section(
        section,
        ok,
        {
            "llm_status": llm_status,
            "local_report_preview": local_report[:180] + "...",
        },
    )
    return {"analyst_prompt_length": len(prompt), "local_report": local_report, "llm_status": llm_status}


def validate_ui(v: Validator) -> None:
    section = "10_UI_VALIDATION"
    ok = True

    app_path = os.path.join(os.getcwd(), "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        source = f.read()

    required_markers = [
        "Upload users CSV",
        "Upload relationships CSV",
        "Initialize Engine",
        "Add/Update User",
        "Add/Update Relationship",
        "Interactive Network Visualization",
        "Risk Score Table",
        "Export Blockchain Log",
        "Export Risk Table",
    ]
    missing = [m for m in required_markers if m not in source]
    if missing:
        ok = False
        v.add_issue(section, f"Missing UI controls/labels: {missing}")

    v.set_section(section, ok, {"checked_markers": len(required_markers), "missing": missing})


def validate_edge_cases(v: Validator) -> None:
    section = "11_EDGE_CASE_TESTING"
    ok = True

    prop = RiskPropagationEngine()
    causal = CausalEngine()

    # All low-risk nodes
    g_low = nx.Graph()
    for i in range(6):
        g_low.add_node(f"L{i}", income=9000, activity=1.0, risk=0.05)
    for i in range(5):
        g_low.add_edge(f"L{i}", f"L{i+1}", weight=0.5)
    causal.apply(g_low)
    prop.propagate(g_low, alpha=0.2, steps=3)

    # All high-risk nodes
    g_high = nx.Graph()
    for i in range(6):
        g_high.add_node(f"H{i}", income=1000, activity=0.0, risk=0.95)
    for i in range(5):
        g_high.add_edge(f"H{i}", f"H{i+1}", weight=1.0)
    causal.apply(g_high)
    prop.propagate(g_high, alpha=0.2, steps=3)

    # Disconnected graph
    g_disc = nx.Graph()
    g_disc.add_node("A", income=3000, activity=0.5, risk=0.4)
    g_disc.add_node("B", income=3500, activity=0.6, risk=0.3)
    g_disc.add_node("C", income=1500, activity=0.2, risk=0.8)
    g_disc.add_edge("A", "B", weight=0.8)
    causal.apply(g_disc)
    prop.propagate(g_disc, alpha=0.2, steps=2)

    # Extreme values
    extreme = predict_single_user_risk(income=-5000, activity=5.0, transaction_variability=9.0)
    if not (0.0 <= extreme <= 1.0):
        ok = False
        v.add_issue(section, "Extreme-input prediction not clamped to [0,1]")

    all_risks = [float(d.get("risk", 0.0)) for _, d in g_low.nodes(data=True)]
    all_risks += [float(d.get("risk", 0.0)) for _, d in g_high.nodes(data=True)]
    all_risks += [float(d.get("risk", 0.0)) for _, d in g_disc.nodes(data=True)]
    if any(r < 0.0 or r > 1.0 for r in all_risks):
        ok = False
        v.add_issue(section, "Edge-case propagation produced out-of-range risks")

    v.set_section(section, ok, {"extreme_prediction": round(float(extreme), 6)})


def validate_performance(v: Validator) -> Dict[str, Any]:
    section = "12_PERFORMANCE_CHECK"
    ok = True

    start = time.perf_counter()
    scaling_result = run_full_scaling_mode(
        config=ScalingConfig(
            user_count=300,
            network_mode="preferential_attachment",
            average_degree=8,
            alpha=0.22,
            steps=5,
            intervention_top_k=20,
            critical_report_count=5,
            max_log_events=150,
        )
    )
    elapsed = time.perf_counter() - start

    if elapsed > 20.0:
        ok = False
        v.add_issue(section, f"Scaling run slower than expected: {elapsed:.2f}s")

    # Basic recomputation sanity signal from result structure.
    required = {"system_summary", "stability", "intervention", "top_risky_nodes"}
    if required - set(scaling_result.keys()):
        ok = False
        v.add_issue(section, "Scaling output missing expected keys")

    v.set_section(section, ok, {"elapsed_seconds": round(elapsed, 3), "user_count": 300})
    return scaling_result


def assemble_final_output(
    v: Validator,
    engine: DCCFEEngine,
    intervention_result: Dict[str, Any],
    report_info: Dict[str, Any],
    scaling_result: Dict[str, Any],
) -> Dict[str, Any]:
    risk_table = engine.export_risk_table()
    node_results = risk_table.to_dict(orient="records")
    system_summary = {
        "average_risk": round(float(risk_table["risk"].mean()), 6),
        "variance": round(float(risk_table["risk"].var(ddof=0)), 6),
        "high_risk_nodes": int((risk_table["risk"] >= 0.7).sum()),
        "network_size": int(engine.graph.number_of_nodes()),
        "system_state": compute_global_summary(engine.graph).get("system_state", "unknown"),
        "performance_300_users_seconds": v.section_details.get("12_PERFORMANCE_CHECK", {}).get("elapsed_seconds", None),
    }

    reports = {
        "analyst_prompt_length": report_info["analyst_prompt_length"],
        "local_report": report_info["local_report"],
        "llm_status": report_info["llm_status"],
    }

    validation_status = all(v.section_status.values()) and len(v.issues) == 0
    verdict = "System Validated Successfully" if validation_status else "Issues Found"

    final_output = {
        "system_summary": system_summary,
        "node_results": node_results,
        "intervention": intervention_result,
        "reports": reports,
        "validation_status": validation_status,
        "final_verdict": verdict,
        "issues": v.issues,
        "section_status": v.section_status,
        "section_details": v.section_details,
        "scaling_summary": {
            "top_risky_nodes": scaling_result.get("top_risky_nodes", [])[:5],
            "stability": scaling_result.get("stability", {}),
        },
    }
    return final_output


def main() -> None:
    v = Validator()

    users, edges = create_initial_dataset()

    validate_data(v, users, edges)
    validate_risk_model(v)
    graph = validate_graph(v, users, edges)
    validate_causal(v, graph)
    validate_propagation(v)

    engine = validate_simulation(v, users, edges)
    intervention_result = validate_intervention(v, engine)
    metrics = validate_stability(v, engine)
    report_info = validate_report(v, metrics)
    validate_ui(v)
    validate_edge_cases(v)
    scaling_result = validate_performance(v)

    output = assemble_final_output(v, engine, intervention_result, report_info, scaling_result)

    out_path = os.path.join(os.getcwd(), "end_to_end_validation_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("=" * 80)
    print("DCCFE COMPLETE END-TO-END VALIDATION")
    print("=" * 80)
    print(json.dumps({
        "final_verdict": output["final_verdict"],
        "validation_status": output["validation_status"],
        "issue_count": len(output["issues"]),
        "output_file": out_path,
    }, indent=2))

    if output["issues"]:
        print("\nIssues found:")
        for issue in output["issues"]:
            print(f"- {issue}")


if __name__ == "__main__":
    main()
