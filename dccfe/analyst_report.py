from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass
class AnalystReportContext:
    user_id: str
    risk_level: str
    trend: str
    income_status: str
    activity_status: str
    variability_status: str
    neighbor_influence: str
    behavior_pattern: str
    system_state: str
    avg_risk: float
    high_risk_count: int
    cascade: str
    critical_nodes: str


def _status_from_value(value: float, low_cutoff: float, high_cutoff: float) -> str:
    if value >= high_cutoff:
        return "elevated"
    if value <= low_cutoff:
        return "stable"
    return "moderate"


def _build_behavior_pattern(node_result: Dict[str, Any]) -> str:
    contributions = dict(node_result.get("contributions", {}))
    top_factors = sorted(contributions.items(), key=lambda item: float(item[1]), reverse=True)
    if not top_factors:
        return "balanced"
    dominant = [name for name, _ in top_factors[:2]]
    return " / ".join(dominant)


def build_analyst_prompt(context: AnalystReportContext) -> str:
    user_id = context.user_id
    risk_level = context.risk_level
    trend = context.trend
    income_status = context.income_status
    activity_status = context.activity_status
    variability_status = context.variability_status
    neighbor_influence = context.neighbor_influence
    behavior_pattern = context.behavior_pattern
    system_state = context.system_state
    avg_risk = round(float(context.avg_risk), 4)
    high_risk_count = int(context.high_risk_count)
    cascade = context.cascade
    critical_nodes = context.critical_nodes

    return f"""
You are a senior financial risk analyst specializing in network-based systemic risk and behavioral finance.

Your task is to generate an expert-level financial risk assessment report based on the given data.

-------------------------------------
USER PROFILE
-------------------------------------
User ID: {user_id}
Risk Level: {risk_level}
Trend: {trend}
Income Status: {income_status}
Activity Status: {activity_status}
Transaction Variability: {variability_status}
Neighbor Influence: {neighbor_influence}
Behavior Pattern: {behavior_pattern}

-------------------------------------
SYSTEM CONTEXT
-------------------------------------
System State: {system_state}
Average Risk: {avg_risk}
High Risk Nodes: {high_risk_count}
Cascade Detected: {cascade}
Critical Nodes: {critical_nodes}

-------------------------------------
ANALYSIS INSTRUCTIONS
-------------------------------------

Perform a structured reasoning process:

1. Identify the PRIMARY DRIVER of risk
   (income / activity / variability / network influence)

2. Identify SECONDARY contributing factors

3. Analyze NETWORK EFFECTS:
   - how neighboring nodes are influencing this user
   - whether risk is being amplified through connections

4. Interpret TREND:
   - is the user stabilizing or deteriorating?

5. Relate USER RISK to SYSTEM STATE:
   - is this part of a broader systemic issue?

6. Provide a STRATEGIC RECOMMENDATION:
   - what action would reduce risk effectively?

-------------------------------------
WRITING STYLE
-------------------------------------

- Write like a professional analyst, not a chatbot
- Use clear, confident language
- Avoid bullet points
- Avoid technical jargon
- Avoid excessive numbers
- Focus on reasoning and insight

-------------------------------------
OUTPUT FORMAT
-------------------------------------

Write 2 short paragraphs:

Paragraph 1:
- Risk explanation with cause + network influence

Paragraph 2:
- System context + recommendation + forward-looking insight

-------------------------------------
GOAL
-------------------------------------

The report should feel like it was written by an expert who understands:
- financial behavior
- network effects
- systemic risk
- decision-making under uncertainty
""".strip()


def context_from_pipeline_report(
    report: Dict[str, Any],
    user_id: str,
) -> AnalystReportContext:
    node_rows = list(report.get("node_results", []))
    selected = next((row for row in node_rows if str(row.get("node_id")) == str(user_id)), None)
    if selected is None:
        raise KeyError(f"User {user_id} not found in report node_results")

    contributions = dict(selected.get("contributions", {}))
    income_status = _status_from_value(float(contributions.get("income", 0.0)), low_cutoff=0.33, high_cutoff=0.66)
    activity_status = _status_from_value(float(contributions.get("activity", 0.0)), low_cutoff=0.33, high_cutoff=0.66)
    variability_status = _status_from_value(float(contributions.get("variability", 0.0)), low_cutoff=0.33, high_cutoff=0.66)
    neighbor_status = _status_from_value(float(contributions.get("neighbor_influence", 0.0)), low_cutoff=0.33, high_cutoff=0.66)

    system_summary = dict(report.get("system_summary", {}))
    quality_internal = dict(report.get("_internal", {}))
    quality_report = dict(quality_internal.get("quality_report", {}))
    cascade_summary = list(quality_report.get("cascade_summary", []))

    critical_nodes: List[str] = []
    primary_critical = system_summary.get("critical_node")
    if primary_critical:
        critical_nodes.append(str(primary_critical))

    high_risk_nodes = [
        str(row.get("node_id"))
        for row in node_rows
        if str(row.get("risk_level", "")).lower() == "high"
    ]
    for node in high_risk_nodes:
        if node not in critical_nodes:
            critical_nodes.append(node)

    cascade_detected = "yes" if len(cascade_summary) > 0 else "no"

    return AnalystReportContext(
        user_id=str(user_id),
        risk_level=str(selected.get("risk_level", "unknown")),
        trend=str(selected.get("trend", "stable")),
        income_status=income_status,
        activity_status=activity_status,
        variability_status=variability_status,
        neighbor_influence=neighbor_status,
        behavior_pattern=_build_behavior_pattern(selected),
        system_state=str(system_summary.get("system_state", "stable")),
        avg_risk=float(system_summary.get("average_risk", 0.0)),
        high_risk_count=int(system_summary.get("high_risk_nodes", 0)),
        cascade=cascade_detected,
        critical_nodes=", ".join(critical_nodes) if critical_nodes else "none",
    )


def generate_analyst_report(
    context: AnalystReportContext,
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.3,
    timeout_seconds: int = 30,
) -> str:
    token = api_key or os.getenv("GROQ_API_KEY")
    if not token:
        raise ValueError("Missing API key. Set GROQ_API_KEY or pass api_key explicitly.")

    prompt = build_analyst_prompt(context)

    payload = {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": "You are an expert financial risk analyst."},
            {"role": "user", "content": prompt},
        ],
    }

    req = Request(
        GROQ_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = str(exc)
        
        if exc.code == 400:
            raise RuntimeError(f"Groq API validation error (400): {error_body}. Check model name, token limits, or payload structure.") from exc
        elif exc.code == 401:
            raise RuntimeError(f"Groq API authentication failed (401): Invalid API key.") from exc
        elif exc.code == 429:
            raise RuntimeError(f"Groq API rate limit (429): Too many requests. Try again later.") from exc
        else:
            raise RuntimeError(f"Groq request failed: HTTP {exc.code} - {error_body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Groq request failed (network error): {exc.reason}") from exc

    choices = body.get("choices", [])
    if not choices:
        raise RuntimeError("Groq response did not contain any choices")

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("Groq response choice did not contain message content")
    return str(content).strip()


def generate_analyst_report_from_pipeline(
    report: Dict[str, Any],
    user_id: str,
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
) -> str:
    context = context_from_pipeline_report(report=report, user_id=user_id)
    return generate_analyst_report(context=context, api_key=api_key, model=model)


def generate_reports_for_users(
    report: Dict[str, Any],
    user_ids: Iterable[str],
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
) -> Dict[str, str]:
    results: Dict[str, str] = {}
    for user_id in user_ids:
        results[str(user_id)] = generate_analyst_report_from_pipeline(
            report=report,
            user_id=str(user_id),
            api_key=api_key,
            model=model,
        )
    return results
