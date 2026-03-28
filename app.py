from __future__ import annotations

import json
import os
import time
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st

from dccfe import DCCFEEngine, Relationship, UserRecord
from dccfe.analyst_report import AnalystReportContext, generate_analyst_report
from dccfe.visualization import build_partial_risk_figure, build_risk_figure


st.set_page_config(page_title="CascadeX - Financial Risk Intelligence", layout="wide", initial_sidebar_state="expanded")


def _apply_custom_theme() -> None:
    st.markdown(
        """
        <style>
        * {
            margin: 0;
            padding: 0;
        }

        :root {
            --bg-main: #050816;
            --bg-elev: #0f172a;
            --bg-soft: #111827;
            --bg-card: rgba(15,23,42,0.88);
            --text-main: #f0f4f8;
            --text-soft: #cbd5e1;
            --text-muted: #94a3b8;
            --accent-cyan: #22d3ee;
            --accent-pink: #fb7185;
            --accent-green: #34d399;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #a78bfa;
            --accent-blue: #3b82f6;
            --accent-orange: #ff6b35;
            --border-light: rgba(148,163,184,0.16);
            --border-medium: rgba(148,163,184,0.26);
        }

        /* Main App Background */
        .stApp {
            background: 
                radial-gradient(circle at 8% -10%, rgba(34,211,238,0.08), transparent 50%),
                radial-gradient(circle at 95% 5%, rgba(251,113,133,0.08), transparent 50%),
                radial-gradient(circle at 50% 100%, rgba(167,139,250,0.06), transparent 50%),
                linear-gradient(180deg, var(--bg-main) 0%, #0a0e1a 100%);
            color: var(--text-main);
        }

        /* Header */
        [data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Main Content */
        [data-testid="stMainBlockContainer"] {
            padding-top: 1rem;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(15,23,42,0.95) 0%, rgba(17,24,39,0.92) 100%);
            border-right: 4px dotted #22d3ee;
            box-shadow: -5px 0 15px rgba(34,211,238,0.1);
        }

        /* Sidebar Header */
        [data-testid="stSidebar"] [data-testid="stVerticalBlockContainer"] > :first-child {
            padding-top: 0.5rem !important;
        }

        /* Headings */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-main);
            font-weight: 600;
            letter-spacing: 0.3px;
        }

        h1 {
            font-size: 2.2rem;
            margin-bottom: 0.5rem;
        }

        h2 {
            font-size: 1.5rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 3px dashed #ff6b35;
            padding-bottom: 0.5rem;
        }

        h3 {
            font-size: 1.2rem;
            margin-top: 1rem;
            margin-bottom: 0.75rem;
            color: #a78bfa;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(15,23,42,0.92) 0%, rgba(17,24,39,0.88) 100%);
            border: 3px double #34d399;
            border-radius: 14px;
            padding: 1.2rem;
            box-shadow: 0 0 20px rgba(52,211,153,0.2), inset 0 0 10px rgba(167,139,250,0.05);
            transition: all 0.3s ease;
        }

        [data-testid="stMetric"]:hover {
            border-color: #22d3ee;
            box-shadow: 0 0 30px rgba(34,211,238,0.3), inset 0 0 15px rgba(167,139,250,0.1);
            transform: translateY(-3px);
        }

        [data-testid="stMetric"] > div:nth-child(2) {
            background: linear-gradient(90deg, #22d3ee, #a78bfa, #fb7185);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.8rem;
            font-weight: 700;
        }

        /* Forms & Inputs */
        [data-baseweb="select"] > div,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSlider > div > div > div,
        .stTextArea textarea {
            background: rgba(15,23,42,0.95) !important;
            border: 2px solid #3b82f6 !important;
            color: var(--text-main) !important;
            border-radius: 8px !important;
            font-size: 0.95rem !important;
            transition: all 0.2s ease !important;
            box-shadow: inset 0 0 8px rgba(59,130,246,0.15) !important;
        }

        [data-baseweb="select"] > div:hover,
        .stTextInput > div > div > input:hover,
        .stNumberInput > div > div > input:hover,
        .stTextArea textarea:hover {
            border-color: #22d3ee !important;
            box-shadow: inset 0 0 12px rgba(34,211,238,0.25) !important;
        }

        [data-baseweb="select"] > div:focus-within,
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea textarea:focus {
            border: 2px solid #a78bfa !important;
            box-shadow: 0 0 20px rgba(167,139,250,0.4), inset 0 0 8px rgba(167,139,250,0.2) !important;
            outline: none !important;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, rgba(34,211,238,0.25), rgba(251,113,133,0.25), rgba(167,139,250,0.25));
            border: 2px outset;
            border-color: #ff6b35;
            color: var(--text-main);
            border-radius: 10px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease;
            cursor: pointer;
            box-shadow: 0 4px 0 rgba(255,107,53,0.3);
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, rgba(34,211,238,0.4), rgba(251,113,133,0.4), rgba(167,139,250,0.4));
            border-color: #ffb347;
            box-shadow: 0 6px 0 rgba(255,107,53,0.4);
            transform: translateY(-2px);
        }

        .stButton > button:active {
            box-shadow: 0 2px 0 rgba(255,107,53,0.2);
            transform: translateY(0);
        }

        /* Download Button */
        [data-testid="stDownloadButton"] > button {
            background: linear-gradient(135deg, rgba(52,211,153,0.3), rgba(34,211,238,0.25));
            border: 2px ridge #34d399;
            box-shadow: 0 3px 8px rgba(52,211,153,0.25);
        }

        /* File Uploader */
        [data-testid="stFileUploader"] {
            border-radius: 12px;
            border: 3px dotted #a78bfa;
            padding: 1.5rem;
            background: rgba(167,139,250,0.04);
            box-shadow: inset 0 0 10px rgba(167,139,250,0.08);
        }

        /* DataFrames & Tables */
        [data-testid="stDataFrame"],
        [data-testid="stDataFrameContainer"],
        [data-testid="stJsonViewerRoot"] {
            border: 2px solid #ff6b35;
            border-radius: 12px;
            background: rgba(15,23,42,0.6);
            box-shadow: 0 0 15px rgba(255,107,53,0.15);
        }

        /* Tabs */
        [data-testid="stTabs"] [aria-selected="true"] {
            color: #22d3ee !important;
            border-bottom: 3px solid #22d3ee !important;
            border-bottom-width: 3px !important;
        }

        [data-testid="stTabs"] [aria-selected="false"] {
            color: var(--text-muted) !important;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            border: 2px dashed #ff6b35;
            border-radius: 10px;
            background: rgba(15,23,42,0.5);
            box-shadow: 0 0 10px rgba(255,107,53,0.12);
        }

        /* Text and Info Boxes */
        .stInfo, .stSuccess, .stWarning, .stError {
            border-radius: 10px;
            padding: 1rem;
        }

        .stSuccess {
            border-left: 5px solid #34d399 !important;
            border-right: 2px solid #34d399 !important;
            background: rgba(52,211,153,0.15) !important;
            box-shadow: inset 3px 0 0 #34d399 !important;
        }

        .stInfo {
            border-top: 4px solid #22d3ee !important;
            border-bottom: 4px solid #22d3ee !important;
            background: rgba(34,211,238,0.15) !important;
            box-shadow: 0 0 15px rgba(34,211,238,0.2) !important;
        }

        .stWarning {
            border-left: 5px solid #ff6b35 !important;
            border-top: 2px solid #ff6b35 !important;
            background: rgba(255,107,53,0.15) !important;
            box-shadow: inset 5px 0 0 rgba(255,107,53,0.3) !important;
        }

        .stError {
            border: 2px solid #fb7185 !important;
            border-left: 6px solid #fb7185 !important;
            background: rgba(251,113,133,0.15) !important;
            box-shadow: -3px 0 10px rgba(251,113,133,0.2) !important;
        }

        /* Custom Hero Block */
        .hero-block {
            border-radius: 16px;
            border: 4px ridge;
            border-color: #22d3ee;
            background: linear-gradient(135deg, rgba(15,23,42,0.88), rgba(17,24,39,0.75));
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 0 30px rgba(34,211,238,0.2), inset 0 0 20px rgba(167,139,250,0.05);
        }

        .hero-title {
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.1;
            background: linear-gradient(90deg, #22d3ee, #a78bfa, #fb7185, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-title-main {
            display: inline-block;
        }

        .hero-title-accent {
            display: inline-block;
            margin-top: 0.25rem;
            font-size: 1.2rem;
            font-weight: 700;
            line-height: 1.15;
            background: linear-gradient(90deg, #f6c453, #ffd700, #22d3ee);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-sub {
            margin-top: 0.75rem;
            color: var(--text-soft);
            font-size: 0.95rem;
            line-height: 1.5;
            background: linear-gradient(90deg, #cbd5e1, #22d3ee);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* KPI Section */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }

        /* Section Headers */
        .section-header {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-main);
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 4px dotted #a78bfa;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Dividers */
        hr {
            border: none;
            height: 1px;
            background: repeating-linear-gradient(90deg, #22d3ee 0px, #22d3ee 10px, transparent 10px, transparent 20px);
            margin: 2rem 0;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(15,23,42,0.5);
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #22d3ee, #a78bfa);
            border-radius: 4px;
            box-shadow: 0 0 10px rgba(34,211,238,0.2);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #fb7185, #22d3ee);
            box-shadow: 0 0 15px rgba(251,113,133,0.3);
        }

        /* Checkbox */
        [data-testid="stCheckbox"] {
            color: var(--text-soft);
        }

        [data-testid="stCheckbox"] input {
            border-color: #22d3ee !important;
        }

        /* Toggle */
        [data-testid="stToggle"] {
            margin: 0.5rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_apply_custom_theme()

# HEADER
st.markdown(
    """
    <div class="hero-block">
        <div class="hero-title">
            <span class="hero-title-main">🌈 CascadeX</span><br>
            <span class="hero-title-accent">Financial Risk Intelligence</span>
        </div>
        <div class="hero-sub">Real-time network risk analysis, monitoring & intervention planning with cognitive behavior analysis</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def _init_state() -> None:
    if "engine" not in st.session_state:
        st.session_state.engine = DCCFEEngine()
    if "loaded" not in st.session_state:
        st.session_state.loaded = False


def _parse_users(df: pd.DataFrame) -> List[UserRecord]:
    required = {"user_id", "income", "activity", "transactions", "defaults"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing user columns: {sorted(missing)}")

    users: List[UserRecord] = []
    for _, row in df.iterrows():
        users.append(
            UserRecord(
                user_id=str(row["user_id"]),
                income=float(row["income"]),
                activity=float(row["activity"]),
                transactions=int(row["transactions"]),
                defaults=int(row["defaults"]),
            )
        )
    return users


def _parse_relationships(df: pd.DataFrame) -> List[Relationship]:
    required = {"source", "target", "weight", "relation_type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing relation columns: {sorted(missing)}")

    rels: List[Relationship] = []
    for _, row in df.iterrows():
        rels.append(
            Relationship(
                source=str(row["source"]),
                target=str(row["target"]),
                weight=float(row["weight"]),
                relation_type=str(row["relation_type"]),
            )
        )
    return rels


def _risk_level(risk: float) -> str:
    if risk >= 0.7:
        return "high"
    if risk >= 0.4:
        return "medium"
    return "low"


def _status(value: float, low: float, high: float) -> str:
    if value <= low:
        return "stable"
    if value >= high:
        return "elevated"
    return "moderate"


def _build_report_context(engine: DCCFEEngine, user_id: str) -> AnalystReportContext:
    node = engine.graph.nodes[user_id]
    risk = float(node.get("risk", 0.0))
    income = float(node.get("income", 0.0))
    activity = float(node.get("activity", 0.0))
    transactions = int(node.get("transactions", 0))

    neighbors = list(engine.graph.neighbors(user_id))
    neighbor_risk = 0.0
    if neighbors:
        neighbor_risk = sum(float(engine.graph.nodes[n].get("risk", 0.0)) for n in neighbors) / len(neighbors)

    explanation = list(node.get("explanation", []))
    behavior_pattern = ", ".join(explanation[:2]) if explanation else "stable financial behavior"

    all_risks = [float(engine.graph.nodes[n].get("risk", 0.0)) for n in engine.graph.nodes]
    avg_risk = sum(all_risks) / len(all_risks) if all_risks else 0.0
    high_risk_count = sum(1 for r in all_risks if r >= 0.7)

    critical_nodes = sorted(engine.graph.nodes, key=lambda n: float(engine.graph.nodes[n].get("risk", 0.0)), reverse=True)
    critical_nodes_text = ", ".join(critical_nodes[:3]) if critical_nodes else "none"
    cascade_detected = "yes" if neighbor_risk >= 0.6 and high_risk_count > 1 else "no"

    return AnalystReportContext(
        user_id=user_id,
        risk_level=_risk_level(risk),
        trend="stable",
        income_status=_status(1.0 - min(income / 8000.0, 1.0), 0.33, 0.66),
        activity_status=_status(1.0 - activity, 0.33, 0.66),
        variability_status=_status(min(transactions / 15.0, 1.0), 0.33, 0.66),
        neighbor_influence=_status(neighbor_risk, 0.33, 0.66),
        behavior_pattern=behavior_pattern,
        system_state="critical" if avg_risk > 0.65 else ("fragile" if avg_risk > 0.4 else "stable"),
        avg_risk=avg_risk,
        high_risk_count=high_risk_count,
        cascade=cascade_detected,
        critical_nodes=critical_nodes_text,
    )


def _resolve_report_api_key() -> str | None:
    key = None
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        key = None
    if key:
        return str(key)
    env_key = os.getenv("GROQ_API_KEY")
    return str(env_key) if env_key else None


def _generate_local_expert_report(context: AnalystReportContext) -> str:
    primary_driver = "network influence"
    if context.income_status == "elevated":
        primary_driver = "income pressure"
    elif context.activity_status == "elevated":
        primary_driver = "low activity instability"
    elif context.variability_status == "elevated":
        primary_driver = "transaction variability"

    paragraph_1 = (
        f"User {context.user_id} is currently in a {context.risk_level} risk state, with {primary_driver} acting as the main driver. "
        f"The recent trend appears {context.trend}, and the surrounding network influence is {context.neighbor_influence}, "
        f"which suggests that connected users are contributing meaningfully to this node's exposure. "
        f"Overall behavior indicates a {context.behavior_pattern} pattern that should be monitored closely."
    )

    paragraph_2 = (
        f"At the system level, conditions are {context.system_state} with average risk near {context.avg_risk:.2f} and {context.high_risk_count} high-risk nodes. "
        f"Given the current profile, the most effective action is targeted support for this node and nearby critical users ({context.critical_nodes}) "
        f"to reduce contagion pressure and improve short-term stability. If early support is sustained, forward risk should moderate rather than cascade."
    )

    return f"{paragraph_1}\n\n{paragraph_2}"


_init_state()
engine: DCCFEEngine = st.session_state.engine

# ============================================================================
# SIDEBAR CONTROL PANEL
# ============================================================================
with st.sidebar:
    st.markdown("### ⚙️ CONTROL PANEL")
    
    # ========================================================================
    # DATA MANAGEMENT
    # ========================================================================
    st.markdown("#### 📊 Data Management")
    
    users_file = st.file_uploader("Upload users CSV", type=["csv"], key="users_file", help="CSV with: user_id, income, activity, transactions, defaults")
    rels_file = st.file_uploader("Upload relationships CSV", type=["csv"], key="rels_file", help="CSV with: source, target, weight, relation_type")

    if st.button("🚀 Initialize Engine", use_container_width=True, key="init_btn"):
        if users_file is None or rels_file is None:
            st.error("⚠️ Upload both CSV files first")
        else:
            try:
                with st.spinner("Loading and processing data..."):
                    users_df = pd.read_csv(users_file)
                    rels_df = pd.read_csv(rels_file)
                    users = _parse_users(users_df)
                    relationships = _parse_relationships(rels_df)
                    st.session_state.engine = DCCFEEngine()
                    engine = st.session_state.engine
                    engine.load_users(users)
                    engine.load_relationships(relationships)
                    engine.recompute()
                    st.session_state.loaded = True
                    st.success(f"✅ Engine ready: {len(users)} users, {len(relationships)} relationships")
            except ValueError as ve:
                st.error(f"❌ Data Error: {ve}")
            except Exception as exc:
                st.error(f"❌ Failed to load dataset: {str(exc)[:200]}")

    st.markdown("---")
    
    # ========================================================================
    # NODE SELECTION
    # ========================================================================
    st.markdown("#### 👤 Node Selection")
    if st.session_state.loaded and engine.graph.number_of_nodes() > 0:
        selected_node = st.selectbox("Select Node/User", list(engine.graph.nodes), key="selected_node")
        st.caption(f"Risk: {float(engine.graph.nodes[selected_node].get('risk', 0.0)):.2%} | Income: ${float(engine.graph.nodes[selected_node].get('income', 0.0)):.0f}")

    st.markdown("---")
    
    # ========================================================================
    # PARAMETERS
    # ========================================================================
    st.markdown("#### 🔧 Parameters")
    
    # Live User Upsert
    st.markdown("**Live User Upsert**")
    live_user_id = st.text_input("User ID", value="", key="user_id_input", placeholder="e.g., U5")
    col_inc, col_act = st.columns(2)
    with col_inc:
        live_income = st.number_input("Income", min_value=0.0, value=3000.0, step=100.0, key="income_input")
    with col_act:
        live_activity = st.slider("Activity", min_value=0.0, max_value=1.0, value=0.5, step=0.05, key="activity_slider")
    col_tx, col_def = st.columns(2)
    with col_tx:
        live_transactions = st.number_input("Transactions", min_value=0, value=5, step=1, key="tx_input")
    with col_def:
        live_defaults = st.number_input("Defaults", min_value=0, value=0, step=1, key="def_input")
    
    if st.button("✏️  Add/Update User", use_container_width=True, key="upsert_user_btn"):
        if not live_user_id.strip():
            st.error("User ID is required")
        else:
            try:
                engine.upsert_user(
                    UserRecord(
                        user_id=live_user_id.strip(),
                        income=float(live_income),
                        activity=float(live_activity),
                        transactions=int(live_transactions),
                        defaults=int(live_defaults),
                    )
                )
                st.session_state.loaded = engine.graph.number_of_nodes() >= 5
                if st.session_state.loaded:
                    engine.recompute()
                    st.success(f"✅ User {live_user_id} updated")
                else:
                    st.info(f"User added ({engine.graph.number_of_nodes()}/5 needed)")
            except Exception as exc:
                st.error(f"❌ Update failed: {str(exc)[:150]}")

    st.markdown("**Live Relationship Upsert**")
    rel_source = st.text_input("Source User", value="", key="rel_source_input", placeholder="e.g., U1")
    rel_target = st.text_input("Target User", value="", key="rel_target_input", placeholder="e.g., U2")
    col_wt, col_type = st.columns(2)
    with col_wt:
        rel_weight = st.number_input("Weight", min_value=0.0, value=1.0, step=0.1, key="rel_weight_input")
    with col_type:
        rel_type = st.selectbox(
            "Type",
            options=["dependency", "similarity", "influence"],
            index=0,
            key="rel_type_select",
        )
    
    if st.button("🔗 Add/Update Relationship", use_container_width=True, key="upsert_rel_btn"):
        if not rel_source.strip() or not rel_target.strip():
            st.error("Both source and target users required")
        else:
            try:
                engine.upsert_relationship(
                    Relationship(
                        source=rel_source.strip(),
                        target=rel_target.strip(),
                        weight=float(rel_weight),
                        relation_type=rel_type.strip() or "dependency",
                    )
                )
                if engine.graph.number_of_nodes() >= 5:
                    engine.recompute()
                    st.session_state.loaded = True
                st.success(f"✅ Relationship added")
            except Exception as exc:
                st.error(f"❌ Failed: {str(exc)[:150]}")

if not st.session_state.loaded:
    st.info(
        "👈 **Getting Started:**\n\n"
        "1. Upload CSV files in the sidebar (Data Management)\n"
        "2. Click \"Initialize Engine\"\n\n"
        "**CSV Format:**\n"
        "- **Users**: user_id, income, activity, transactions, defaults\n"
        "- **Relationships**: source, target, weight, relation_type (dependency/similarity/influence)"
    )
    st.stop()

# ============================================================================
# MAIN DASHBOARD CONTENT
# ============================================================================

# Extract Key Metrics
risk_preview = engine.export_risk_table()
avg_risk = float(risk_preview["risk"].mean()) if not risk_preview.empty else 0.0
high_risk_nodes = int((risk_preview["risk"] >= 0.7).sum()) if not risk_preview.empty else 0
critical_user = str(risk_preview.iloc[0]["user_id"]) if not risk_preview.empty else "N/A"
network_size = int(engine.graph.number_of_nodes())

# Determine system state
if avg_risk >= 0.65:
    sys_state = "🔴 CRITICAL"
    sys_color = "rgba(239,68,68,0.2)"
elif avg_risk >= 0.4:
    sys_state = "🟠 FRAGILE"
    sys_color = "rgba(245,158,11,0.2)"
else:
    sys_state = "🟢 STABLE"
    sys_color = "rgba(52,211,153,0.2)"

# System Metrics KPI Section
st.markdown("### 📈 System Metrics")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.metric("Average Risk", f"{avg_risk:.1%}", delta=f"{avg_risk*100:.1f} pts", delta_color="inverse")

with kpi_col2:
    st.metric("High-Risk Nodes", f"{high_risk_nodes}", delta=f"{high_risk_nodes} nodes", delta_color="off")

with kpi_col3:
    st.metric("System State", sys_state.split()[1], delta="Monitor", delta_color="off")

with kpi_col4:
    st.metric("Network Size", f"{network_size}", delta=f"{network_size} users", delta_color="off")

st.markdown("---")

# ============================================================================
# NETWORK ANALYSIS SECTION (Two Columns)
# ============================================================================
st.markdown("### 🔗 Network Analysis")

# Create two-column layout for main content + sidebar analysis
left_col, right_col = st.columns([2, 1])

with left_col:
    # TAB 1: Network Graph Visualization
    st.markdown("#### Interactive Network Visualization")
    node_count = engine.graph.number_of_nodes()
    large_graph_mode = node_count > 80

    if large_graph_mode:
        st.caption("📌 Large graph mode: rendering subgraph (high-risk + high-centrality nodes)")
        try:
            st.plotly_chart(build_partial_risk_figure(engine.graph, top_risk_nodes=30, top_central_nodes=30), use_container_width=True)
        except Exception as e:
            st.error(f"Visualization error: {str(e)[:100]}")
    else:
        try:
            st.plotly_chart(build_risk_figure(engine.graph), use_container_width=True)
        except Exception as e:
            st.error(f"Visualization error: {str(e)[:100]}")

    # TAB 2: Risk Table
    st.markdown("#### Risk Score Table")
    risk_df_display = engine.export_risk_table()
    st.dataframe(risk_df_display, use_container_width=True, height=250)

with right_col:
    # Node Insights Card
    st.markdown("#### 👤 Node Insights")
    
    if st.session_state.loaded and engine.graph.number_of_nodes() > 0:
        selected_for_analysis = st.selectbox("Analyze Node", list(engine.graph.nodes), key="analyze_node_key")
        
        node_data = engine.graph.nodes[selected_for_analysis]
        node_risk = float(node_data.get("risk", 0.0))
        node_income = float(node_data.get("income", 0.0))
        node_activity = float(node_data.get("activity", 0.0))
        node_tx = int(node_data.get("transactions", 0))
        
        # Display node metrics
        st.metric("Risk Score", f"{node_risk:.1%}", delta_color="inverse")
        st.metric("Income", f"${node_income:.0f}")
        st.metric("Activity", f"{node_activity:.2f}")
        st.metric("Transactions", f"{node_tx}")
        
        # Neighbors
        neighbors = list(engine.graph.neighbors(selected_for_analysis))
        st.caption(f"Connections: {len(neighbors)}")
        
        if neighbors:
            neighbor_risks = [float(engine.graph.nodes[n].get("risk", 0.0)) for n in neighbors]
            if neighbor_risks:
                st.metric("Neighbor Avg Risk", f"{sum(neighbor_risks)/len(neighbor_risks):.1%}")

    # System State Card
    st.markdown("#### 🌐 System Summary")
    st.markdown(
        f"""
        <div style="background: {sys_color}; padding: 1rem; border-radius: 10px; border: 1px solid rgba(148,163,184,0.2);">
        <b>Status: {sys_state}</b><br>
        Avg Risk: {avg_risk:.1%}<br>
        High Risk: {high_risk_nodes}/{network_size}<br>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ============================================================================
# ADVANCED TOOLS (Expandable Sections)
# ============================================================================
st.markdown("### 🛠️  Advanced Tools")

# IoT Updates
with st.expander("⚡ Real-Time IoT Update", expanded=False):
    col_iot_sel, col_iot_space = st.columns([2, 1])
    with col_iot_sel:
        iot_user = st.selectbox("User", list(engine.graph.nodes), key="iot_user_select")
    
    col_inc_delta, col_act_delta, col_tx_delta = st.columns(3)
    with col_inc_delta:
        income_delta = st.number_input(
            "Income Delta",
            value=0.0,
            step=100.0,
            key="income_delta_input",
            help="Unbounded change"
        )
    with col_act_delta:
        activity_delta = st.number_input(
            "Activity Delta",
            min_value=-0.4,
            max_value=0.4,
            value=0.0,
            step=0.01,
            key="activity_delta_input",
            format="%.2f",
        )
    with col_tx_delta:
        transaction_delta = st.number_input(
            "Transaction Delta",
            min_value=-10,
            max_value=10,
            value=0,
            step=1,
            key="transaction_delta_input",
        )

    if abs(float(income_delta)) >= 1000 or abs(float(activity_delta)) >= 0.3 or abs(int(transaction_delta)) >= 8:
        st.warning("⚠️  Extreme delta detected - sharp risk changes expected")

    default_event = st.checkbox("Default event occurred", key="default_event_check")

    if st.button("Apply IoT Event", use_container_width=True, key="apply_iot_btn"):
        try:
            engine.apply_iot_update(
                user_id=iot_user,
                income_delta=income_delta,
                activity_delta=activity_delta,
                transaction_delta=transaction_delta,
                default_event=default_event,
            )
            st.success("✅ IoT event applied - network updated")
        except Exception as e:
            st.error(f"❌ Failed: {str(e)[:150]}")

    auto_tick = st.toggle("Continuous simulated IoT stream", value=False, key="auto_tick_toggle")
    if auto_tick:
        touched = engine.random_iot_tick()
        if touched:
            st.caption(f"Random tick: {touched}")
        time.sleep(1.0)
        st.rerun()

# Counterfactual Simulator
with st.expander("🔮 Counterfactual What-If Simulator", expanded=False):
    cf_user = st.selectbox("Scenario User", list(engine.graph.nodes), key="cf_user_select")
    col_cf_inc, col_cf_act = st.columns(2)
    with col_cf_inc:
        cf_income = st.number_input(
            "Scenario Income",
            min_value=0.0,
            value=float(engine.graph.nodes[cf_user].get("income", 0.0)),
            step=100.0,
            key="cf_income_input"
        )
    with col_cf_act:
        cf_activity = st.slider(
            "Scenario Activity",
            min_value=0.0,
            max_value=1.0,
            value=float(engine.graph.nodes[cf_user].get("activity", 0.0)),
            step=0.01,
            key="cf_activity_slider"
        )
    
    if st.button("Run What-If Analysis", use_container_width=True, key="run_whatif_btn"):
        try:
            scenario = engine.simulate_what_if({cf_user: {"income": cf_income, "activity": cf_activity}})
            st.dataframe(scenario, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)[:150]}")

# Intervention Engine
with st.expander("🎯 Intervention Engine", expanded=False):
    st.caption("AI-powered intervention suggestions to reduce network risk")
    try:
        suggestions = engine.suggest_interventions(top_k=3)
        if suggestions:
            st.dataframe(pd.DataFrame(suggestions), use_container_width=True)
        else:
            st.info("No interventions available")
    except Exception as e:
        st.error(f"❌ Failed to generate suggestions: {str(e)[:150]}")

# Expert Analyst Report
with st.expander("📋 Expert Analyst Report", expanded=False):
    report_user = st.selectbox("Report User", list(engine.graph.nodes), key="report_user_select")
    st.caption("🔐 API key configured server-side (hidden from frontend)")
    
    if st.button("Generate Expert Report", use_container_width=True, key="generate_report_btn"):
        try:
            with st.spinner("Generating expert analysis..."):
                api_key = _resolve_report_api_key()
                context = _build_report_context(engine, report_user)
                
                if api_key:
                    try:
                        report_text = generate_analyst_report(
                            context=context,
                            api_key=api_key,
                        )
                        st.session_state["expert_report_text"] = report_text
                        st.success("✅ Expert report generated (LLM)")
                    except RuntimeError as llm_err:
                        # API key exists but failed - use fallback
                        st.warning(f"⚠️  LLM API error: {str(llm_err)[:100]}... Using local synthesis")
                        report_text = _generate_local_expert_report(context)
                        st.session_state["expert_report_text"] = report_text
                        st.info("Generated local expert-style analysis")
                else:
                    # No API key - use fallback
                    report_text = _generate_local_expert_report(context)
                    st.session_state["expert_report_text"] = report_text
                    st.info("Generated local expert-style analysis (no LLM)")
        except Exception as exc:
            st.error(f"❌ Report generation failed: {str(exc)[:200]}")

    if st.session_state.get("expert_report_text"):
        st.text_area(
            "Analyst Assessment",
            value=str(st.session_state.get("expert_report_text", "")),
            height=200,
            disabled=True,
            key="report_text_area",
        )

st.markdown("---")

# ============================================================================
# LARGE GRAPH ANALYTICS (if applicable)
# ============================================================================
if node_count > 80:
    st.markdown("### 📊 Aggregated Metrics (Large Network Mode)")
    
    col_agg1, col_agg2 = st.columns(2)
    with col_agg1:
        st.metric("Average Risk", f"{avg_risk:.3f}")
    with col_agg2:
        st.metric("High-Risk Nodes", f"{high_risk_nodes}")

    # Risk Histogram
    try:
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
        risk_df_full = engine.export_risk_table()
        grouped = pd.cut(risk_df_full["risk"], bins=bins, labels=labels, include_lowest=True)
        hist_df = grouped.value_counts(sort=False).reset_index()
        hist_df.columns = ["risk_band", "count"]
        st.plotly_chart(
            px.bar(hist_df, x="risk_band", y="count", title="Risk Distribution Histogram",
                   labels={"risk_band": "Risk Band", "count": "Number of Nodes"}),
            use_container_width=True
        )
    except Exception as e:
        st.warning(f"Could not render histogram: {str(e)[:100]}")

    # Top 10 High-Risk Nodes
    st.markdown("#### Top 10 High-Risk Nodes")
    st.dataframe(risk_preview.head(10), use_container_width=True)

    # Centrality Ranking
    st.markdown("#### Centrality Ranking (Degree)")
    try:
        degree_list = []
        for n in engine.graph.nodes:
            degree_list.append({"Node": str(n), "Degree": int(engine.graph.degree[n])})
        central_df = pd.DataFrame(degree_list).sort_values(by="Degree", ascending=False).head(10)
        st.dataframe(central_df, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not compute centrality: {str(e)[:100]}")

st.markdown("---")

# ============================================================================
# USER EXPLANATION & BLOCKCHAIN LOG
# ============================================================================
st.markdown("### 📚 System Information")

col_explain, col_audit = st.columns(2)

with col_explain:
    st.markdown("#### Node Explanation")
    explain_user_select = st.selectbox("Explain Node", list(engine.graph.nodes), key="explain_user_select_key")
    try:
        explanation = engine.explain_user(explain_user_select)
        if explanation:
            for item in explanation:
                st.write(f"• {item}")
        else:
            st.caption("No explanation available")
    except Exception as e:
        st.error(f"Could not generate explanation: {str(e)[:100]}")

with col_audit:
    st.markdown("#### Blockchain Event Log")
    try:
        st.json(engine.blockchain.tail(6), expanded=False)
    except Exception as e:
        st.error(f"Could not load blockchain: {str(e)[:100]}")

st.markdown("---")

# ============================================================================
# EXPORT & DOWNLOAD
# ============================================================================
st.markdown("### 💾 Export & Download")
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    st.download_button(
        label="📥 Export Blockchain Log",
        data=json.dumps(engine.blockchain.tail(200), indent=2),
        file_name="cascadex_blockchain_log.json",
        mime="application/json",
        use_container_width=True,
    )

with col_dl2:
    try:
        risk_csv = engine.export_risk_table().to_csv(index=False)
        st.download_button(
            label="📥 Export Risk Table",
            data=risk_csv,
            file_name="cascadex_risk_table.csv",
            mime="text/csv",
            use_container_width=True,
        )
    except Exception as e:
        st.caption(f"Export unavailable: {str(e)[:50]}")
