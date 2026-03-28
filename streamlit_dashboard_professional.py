"""
DCCFE - Financial Risk Intelligence Dashboard

Professional, modern dashboard for the DCCFE system with:
- Interactive controls and real-time visualization
- Comprehensive risk analysis and insights
- Intervention planning and optimization
- System stability monitoring

Launch with: streamlit run streamlit_dashboard_professional.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime, timedelta
import json
from dccfe import one_glance_system_summary, format_node_result

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="DCCFE - Financial Risk Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "DCCFE (Dynamic Counterparty Credit Failure Examination) - Professional Risk Analysis System"
    }
)

# ============================================================================
# CSS STYLING (Dark/Light Theme Compatible)
# ============================================================================

st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .dashboard-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
        border-bottom: 3px solid #00d4ff;
    }
    
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d4ff;
        margin-bottom: 0.5rem;
    }
    
    .dashboard-subtitle {
        font-size: 1.1rem;
        color: #888;
        margin-bottom: 1rem;
    }
    
    /* KPI Card styling */
    .kpi-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        border-left: 5px solid #00d4ff;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.1);
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00d4ff;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        color: #aaa;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Section divider */
    .section-divider {
        margin: 2rem 0;
        border-top: 2px solid #00d4ff;
        opacity: 0.3;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #00d4ff;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #00d4ff;
        opacity: 0.8;
    }
    
    /* Risk badge styling */
    .risk-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .risk-badge-low {
        background-color: rgba(46, 204, 113, 0.2);
        color: #2ecc71;
        border: 1px solid #2ecc71;
    }
    
    .risk-badge-medium {
        background-color: rgba(243, 156, 18, 0.2);
        color: #f39c12;
        border: 1px solid #f39c12;
    }
    
    .risk-badge-high {
        background-color: rgba(231, 76, 60, 0.2);
        color: #e74c3c;
        border: 1px solid #e74c3c;
    }
    
    /* Insight panel styling */
    .insight-panel {
        background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 5px solid #00d4ff;
        margin: 1rem 0;
    }
    
    .insight-label {
        font-size: 0.85rem;
        color: #00d4ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.3rem;
    }
    
    .insight-value {
        font-size: 1.3rem;
        font-weight: 600;
        color: #fff;
        margin-bottom: 0.5rem;
    }
    
    /* System status badge */
    .system-status {
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    .system-status-stable {
        background-color: rgba(46, 204, 113, 0.1);
        border: 2px solid #2ecc71;
        color: #2ecc71;
    }
    
    .system-status-fragile {
        background-color: rgba(243, 156, 18, 0.1);
        border: 2px solid #f39c12;
        color: #f39c12;
    }
    
    .system-status-critical {
        background-color: rgba(231, 76, 60, 0.1);
        border: 2px solid #e74c3c;
        color: #e74c3c;
    }
    
    /* Intervention box */
    .intervention-box {
        background: linear-gradient(135deg, #1e4620 0%, #2d5f33 100%);
        border: 2px solid #2ecc71;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .intervention-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2ecc71;
        margin-bottom: 1rem;
    }
    
    /* Spacing utilities */
    .spacer-sm {
        margin: 0.5rem 0;
    }
    
    .spacer-md {
        margin: 1rem 0;
    }
    
    .spacer-lg {
        margin: 2rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state variables for persistent state across reruns."""
    if 'graph' not in st.session_state:
        st.session_state.graph = create_default_network()
    
    if 'selected_node' not in st.session_state:
        nodes = list(st.session_state.graph.nodes())
        st.session_state.selected_node = nodes[0] if nodes else None
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    if 'blockchain_logs' not in st.session_state:
        st.session_state.blockchain_logs = []
    
    if 'timeline_data' not in st.session_state:
        st.session_state.timeline_data = []
    
    if 'simulation_history' not in st.session_state:
        st.session_state.simulation_history = []
    
    if 'show_explanations' not in st.session_state:
        st.session_state.show_explanations = True
    
    if 'show_centrality' not in st.session_state:
        st.session_state.show_centrality = True

    if 'centrality_cache' not in st.session_state:
        st.session_state.centrality_cache = {"signature": None, "value": None}


# ============================================================================
# DATA GENERATION & UTILITIES
# ============================================================================

def create_default_network():
    """Create a default test network for demonstration."""
    graph = nx.Graph()
    
    users = [
        {"user_id": "U1", "income": 5200, "activity": 0.82, "variability": 0.15},
        {"user_id": "U2", "income": 3800, "activity": 0.45, "variability": 0.35},
        {"user_id": "U3", "income": 2200, "activity": 0.28, "variability": 0.68},
        {"user_id": "U4", "income": 6500, "activity": 0.91, "variability": 0.08},
        {"user_id": "U5", "income": 4100, "activity": 0.62, "variability": 0.42},
        {"user_id": "U6", "income": 2800, "activity": 0.35, "variability": 0.55},
    ]
    
    for user in users:
        user_id = user["user_id"]
        income = user["income"]
        activity = user["activity"]
        var = user["variability"]
        
        risk = max(0.0, min(1.0, 
            (1 - min(income, 8000) / 8000) * 0.3 + 
            (1 - activity) * 0.4 + 
            var * 0.3
        ))
        
        graph.add_node(
            user_id,
            income=income,
            activity=activity,
            variability=var,
            transaction_variability=var,
            risk=risk,
            risk_history=[risk],
            trend="stable"
        )
    
    edges = [
        ("U1", "U2", 0.8),
        ("U2", "U3", 0.9),
        ("U3", "U4", 0.7),
        ("U4", "U5", 0.75),
        ("U5", "U6", 0.6),
        ("U6", "U1", 0.65),
    ]
    
    for u, v, weight in edges:
        graph.add_edge(u, v, weight=weight)
    
    return graph


def create_graph_from_dataframe(df):
    """Create a graph from uploaded tabular data.

    Expected columns (with fallbacks):
    - user_id (or id)
    - income
    - activity
    - variability (or transaction_variability)
    """
    graph = nx.Graph()

    if 'user_id' not in df.columns and 'id' in df.columns:
        df = df.rename(columns={'id': 'user_id'})
    if 'variability' not in df.columns and 'transaction_variability' in df.columns:
        df = df.rename(columns={'transaction_variability': 'variability'})

    required = {'user_id', 'income', 'activity', 'variability'}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    for _, row in df.iterrows():
        user_id = str(row['user_id'])
        income = float(row['income'])
        activity = float(row['activity'])
        variability = float(row['variability'])

        risk = max(0.0, min(1.0,
            (1 - min(income, 8000) / 8000) * 0.3 +
            (1 - activity) * 0.4 +
            variability * 0.3
        ))

        graph.add_node(
            user_id,
            income=income,
            activity=activity,
            variability=variability,
            transaction_variability=variability,
            risk=risk,
            risk_history=[risk],
            trend="stable"
        )

    # Build a simple connected structure if explicit edges are not provided.
    users = list(graph.nodes())
    for i in range(len(users) - 1):
        graph.add_edge(users[i], users[i + 1], weight=0.7)
    if len(users) > 2:
        graph.add_edge(users[-1], users[0], weight=0.6)

    return graph


def get_risk_color(risk_score):
    """Map risk score to color."""
    if risk_score < 0.3:
        return "#2ecc71"  # Green
    elif risk_score < 0.7:
        return "#f39c12"  # Orange
    else:
        return "#e74c3c"  # Red


def get_risk_level(risk_score):
    """Classify risk level."""
    if risk_score < 0.3:
        return "LOW"
    elif risk_score < 0.7:
        return "MEDIUM"
    else:
        return "HIGH"


def calculate_centrality_metrics(graph):
    """Calculate various centrality metrics."""
    signature = (
        graph.number_of_nodes(),
        graph.number_of_edges(),
        tuple(sorted((str(n), round(float(graph.nodes[n].get('risk', 0.0)), 4)) for n in graph.nodes)),
    )
    if st.session_state.centrality_cache["signature"] == signature:
        return st.session_state.centrality_cache["value"]

    degree_cent = nx.degree_centrality(graph)
    betweenness_cent = nx.betweenness_centrality(graph)
    eigenvector_cent = nx.eigenvector_centrality(graph, max_iter=1000)

    value = {
        'degree': degree_cent,
        'betweenness': betweenness_cent,
        'eigenvector': eigenvector_cent
    }
    st.session_state.centrality_cache = {"signature": signature, "value": value}
    return value


def log_event(event_type, summary):
    """Log a blockchain event."""
    event = {
        'event_type': event_type,
        'summary': summary,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'hash': f"0x{np.random.randint(0, 2**32):08x}"
    }
    st.session_state.blockchain_logs.append(event)
    return event


def get_system_stability(graph):
    """Calculate overall system stability."""
    risks = [data.get('risk', 0.5) for _, data in graph.nodes(data=True)]
    avg_risk = np.mean(risks) if risks else 0.5
    
    if avg_risk < 0.3:
        return "STABLE", "#2ecc71"
    elif avg_risk < 0.7:
        return "FRAGILE", "#f39c12"
    else:
        return "CRITICAL", "#e74c3c"


def get_top_at_risk_nodes(graph, n=5):
    """Get top N nodes at highest risk."""
    risks = [(node, data.get('risk', 0.5)) for node, data in graph.nodes(data=True)]
    risks.sort(key=lambda x: x[1], reverse=True)
    return risks[:n]


def propagate_risk(graph, source_node, steps=1):
    """Propagate risk iteratively from a source node to its neighborhood."""
    visited = set([source_node])
    frontier = set([source_node])

    for _ in range(steps):
        next_frontier = set()
        for node in frontier:
            source_risk = graph.nodes[node].get('risk', 0.5)
            for neighbor in graph.neighbors(node):
                edge_weight = graph[node][neighbor].get('weight', 0.5)
                old_risk = graph.nodes[neighbor].get('risk', 0.5)
                new_risk = max(0.0, min(1.0, old_risk * 0.7 + source_risk * edge_weight * 0.3))

                graph.nodes[neighbor]['trend'] = (
                    'increasing' if new_risk > old_risk + 0.01 else
                    'decreasing' if new_risk < old_risk - 0.01 else
                    'stable'
                )
                graph.nodes[neighbor]['risk'] = new_risk
                graph.nodes[neighbor].setdefault('risk_history', []).append(new_risk)

                if neighbor not in visited:
                    next_frontier.add(neighbor)
                    visited.add(neighbor)

        frontier = next_frontier
        if not frontier:
            break

    return len(visited) - 1


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_network_visualization(graph, selected_node=None, title="Network Visualization"):
    """Create an interactive Plotly network visualization."""
    # Calculate layout
    pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)
    
    # Extract node and edge data
    edge_x = []
    edge_y = []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Centrality for sizing
    centrality = calculate_centrality_metrics(graph)['degree']
    
    # Node data
    node_x = []
    node_y = []
    node_color = []
    node_size = []
    node_text = []
    node_hover = []
    
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        risk = graph.nodes[node].get('risk', 0.5)
        income = graph.nodes[node].get('income', 0)
        activity = graph.nodes[node].get('activity', 0)
        
        node_color.append(risk)
        node_size.append(20 + centrality[node] * 30)
        node_text.append(node)
        
        hover_text = f"<b>{node}</b><br>Risk: {risk:.1%}<br>Income: ${income}<br>Activity: {activity:.0%}"
        node_hover.append(hover_text)
    
    # Create figure
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1, color='rgba(125,125,125,0.3)'),
        hoverinfo='none',
        showlegend=False
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        textfont=dict(size=12, color='white'),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=node_hover,
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale='RdYlGn_r',
            cmin=0,
            cmax=1,
            showscale=True,
            colorbar=dict(
                title="Risk Score",
                thickness=15,
                len=0.7,
                tickformat='.0%'
            ),
            line=dict(
                width=3,
                color='white' if selected_node is None else [
                    'cyan' if node == selected_node else 'white' for node in graph.nodes()
                ]
            )
        ),
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=18, color='#00d4ff')),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600,
        font=dict(color='white')
    )
    
    return fig


def create_risk_distribution_chart(graph):
    """Create risk distribution visualization."""
    risks = [data.get('risk', 0.5) for _, data in graph.nodes(data=True)]
    
    fig = go.Figure(data=[
        go.Histogram(
            x=risks,
            nbinsx=10,
            marker=dict(color='rgba(0, 212, 255, 0.7)'),
            name='Risk Distribution'
        )
    ])
    
    fig.update_layout(
        title=dict(text="<b>Risk Distribution</b>", font=dict(size=14, color='#00d4ff')),
        xaxis_title="Risk Score",
        yaxis_title="Node Count",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300,
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def create_timeline_chart(timeline_data):
    """Create timeline visualization."""
    if not timeline_data:
        # Create empty placeholder
        fig = go.Figure()
        fig.add_annotation(
            text="No timeline data available. Run a simulation to populate timeline.",
            showarrow=False,
            font=dict(size=14, color='gray')
        )
        fig.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', title=dict(text="<b>No Data</b>", font=dict(size=12, color='gray')))
        return fig
    
    df = pd.DataFrame(timeline_data)
    
    fig = px.line(
        df,
        x='time_step',
        y='avg_risk',
        title="<b>Average Risk Timeline</b>",
        markers=True
    )
    
    fig.update_layout(
        title=dict(text="<b>Average Risk Timeline</b>", font=dict(size=14, color='#00d4ff')),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300,
        hovermode='x unified',
        xaxis_title="Time Step",
        yaxis_title="Average Risk"
    )
    
    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    """Main dashboard function."""
    initialize_session_state()
    
    # ========================================================================
    # HEADER SECTION
    # ========================================================================
    
    st.markdown("""
        <div class="dashboard-header">
            <div class="dashboard-title">📊 DCCFE - Financial Risk Intelligence Dashboard</div>
            <div class="dashboard-subtitle">Real-time network risk analysis, monitoring & intervention planning</div>
        </div>
    """, unsafe_allow_html=True)

    overview = one_glance_system_summary(st.session_state.graph)
    st.markdown(
        f"""
        <div class="insight-panel" style="margin-top:0;">
            <div class="insight-label">One-Glance System Summary</div>
            <div class="insight-value">{overview['system_state'].upper()} • Confidence: {overview['confidence'].upper()}</div>
            <div style="color:#ddd;">Average Risk: {overview['average_risk']:.1%} | High-Risk Nodes: {overview['high_risk_nodes']} | Critical Node: {overview['critical_node']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # ========================================================================
    # SIDEBAR CONTROLS
    # ========================================================================
    
    st.sidebar.markdown("### ⚙️ CONTROL PANEL")
    st.sidebar.markdown("---")
    
    # Data Upload
    st.sidebar.markdown("**📁 Data Management**")
    uploaded_file = st.sidebar.file_uploader("Upload CSV (optional)", type=['csv'])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.graph = create_graph_from_dataframe(df)
            nodes = list(st.session_state.graph.nodes())
            st.session_state.selected_node = nodes[0] if nodes else None
            log_event("DATA_UPLOAD", f"Uploaded {len(df)} records and created graph with {len(nodes)} nodes")
            st.sidebar.success("CSV loaded and graph updated")
        except Exception as exc:
            st.sidebar.error(f"Upload failed: {exc}")
    
    # Node Selection
    st.sidebar.markdown("**👤 Node Selection**")
    nodes_list = list(st.session_state.graph.nodes())
    selected_node = st.sidebar.selectbox(
        "Select Node/User",
        nodes_list,
        index=nodes_list.index(st.session_state.selected_node) if st.session_state.selected_node in nodes_list else 0
    )
    st.session_state.selected_node = selected_node
    
    # Parameter Adjustment
    st.sidebar.markdown("**⚙️ Parameters**")
    current_income = st.session_state.graph.nodes[selected_node].get('income', 5000)
    income = st.sidebar.slider(
        "💰 Income",
        min_value=500,
        max_value=10000,
        value=int(current_income),
        step=500
    )
    
    current_activity = st.session_state.graph.nodes[selected_node].get('activity', 0.5)
    activity = st.sidebar.slider(
        "📈 Activity",
        min_value=0.0,
        max_value=1.0,
        value=float(current_activity),
        step=0.05
    )
    
    current_variability = st.session_state.graph.nodes[selected_node].get('variability', 0.3)
    variability = st.sidebar.slider(
        "📊 Variability",
        min_value=0.0,
        max_value=1.0,
        value=float(current_variability),
        step=0.05
    )
    
    # Action Buttons
    st.sidebar.markdown("**🎯 Actions**")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("▶️ Simulate System Evolution", use_container_width=True):
            # Update node parameters
            st.session_state.graph.nodes[selected_node]['income'] = income
            st.session_state.graph.nodes[selected_node]['activity'] = activity
            st.session_state.graph.nodes[selected_node]['variability'] = variability
            st.session_state.graph.nodes[selected_node]['transaction_variability'] = variability
            
            # Recalculate risk
            new_risk = max(0.0, min(1.0, 
                (1 - min(income, 8000) / 8000) * 0.3 + 
                (1 - activity) * 0.4 + 
                variability * 0.3
            ))
            st.session_state.graph.nodes[selected_node]['risk'] = new_risk
            
            # Log event
            log_event("SIMULATION", f"Simulated {selected_node}: Risk {new_risk:.1%}")
            st.toast(f"✅ Simulation complete! New risk: {new_risk:.1%}")
    
    with col2:
        if st.button("🌊 Model Risk Spread", use_container_width=True):
            affected = propagate_risk(st.session_state.graph, selected_node, steps=propagation_steps)

            # Log event
            log_event("PROPAGATION", f"Propagated risk from {selected_node} for {propagation_steps} steps to {affected} nodes")
            st.toast(f"✅ Propagation applied for {propagation_steps} steps, affected {affected} nodes")
    
    col3, col4 = st.sidebar.columns(2)
    
    with col3:
        if st.button("🛟 Optimize Stabilization Strategy", use_container_width=True):
            # Find intervention target (most critical node)
            top_nodes = get_top_at_risk_nodes(st.session_state.graph, 1)
            if top_nodes:
                target = top_nodes[0][0]
                log_event("INTERVENTION", f"Recommended intervention on {target}")
                st.toast(f"✅ Intervention on {target}")
    
    with col4:
        if st.button("⚡ Shock Event", use_container_width=True):
            # Trigger shock
            st.session_state.graph.nodes[selected_node]['risk'] = min(1.0, 
                st.session_state.graph.nodes[selected_node]['risk'] + 0.3
            )
            log_event("SHOCK", f"Shock event triggered on {selected_node}")
            st.toast("⚡ Shock event triggered!")
    
    # Propagation Steps
    st.sidebar.markdown("**🔧 Propagation**")
    propagation_steps = st.sidebar.slider(
        "Steps",
        min_value=1,
        max_value=10,
        value=3,
        help="Number of propagation iterations"
    )
    
    # Toggles
    st.sidebar.markdown("**👁️ Display Options**")
    show_explanations = st.sidebar.checkbox("Show Explanations", value=True)
    show_centrality = st.sidebar.checkbox("Show Centrality Metrics", value=True)
    
    st.session_state.show_explanations = show_explanations
    st.session_state.show_centrality = show_centrality
    
    # ========================================================================
    # KPI CARDS (TOP METRICS)
    # ========================================================================
    
    st.markdown("<div class='section-header'>📈 System Metrics</div>", unsafe_allow_html=True)
    
    # Calculate metrics
    risks = [data.get('risk', 0.5) for _, data in st.session_state.graph.nodes(data=True)]
    avg_risk = np.mean(risks)
    high_risk_count = sum(1 for r in risks if r >= 0.7)
    system_state, state_color = get_system_stability(st.session_state.graph)
    top_nodes = get_top_at_risk_nodes(st.session_state.graph, 1)
    critical_node = top_nodes[0][0] if top_nodes else "N/A"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Average Risk",
            f"{avg_risk:.1%}",
            delta=f"{(avg_risk - 0.45):.1%}" if abs(avg_risk - 0.45) > 0.01 else "Stable"
        )
    
    with col2:
        st.metric(
            "🔴 High-Risk Nodes",
            high_risk_count,
            delta=f"{high_risk_count - 2}" if high_risk_count != 2 else "OK"
        )
    
    with col3:
        st.metric(
            "🏥 System State",
            system_state,
            delta="Caution" if system_state == "FRAGILE" else None
        )
    
    with col4:
        st.metric(
            "⚠️ Critical Node",
            critical_node,
            delta=f"{top_nodes[0][1]:.1%} risk" if top_nodes else "N/A"
        )
    
    # ========================================================================
    # MAIN CONTENT AREA (3-Column Layout)
    # ========================================================================
    
    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📊 Network Analysis</div>", unsafe_allow_html=True)
    
    col_left, col_center, col_right = st.columns([1.2, 2.5, 1.3], gap="medium")
    
    # ========================================================================
    # SIDEBAR INSIGHTS (Left Column)
    # ========================================================================
    
    with col_left:
        st.markdown("### 📋 Node Insights")
        
        node_data = st.session_state.graph.nodes[selected_node]
        node_risk = node_data.get('risk', 0.5)
        
        # Risk Score (Large)
        st.markdown(f"""
            <div class="insight-panel">
                <div class="insight-label">Risk Score</div>
                <div class="insight-value">{node_risk:.1%}</div>
                <div style="padding: 0.5rem 0;">
                    <span class="risk-badge risk-badge-{get_risk_level(node_risk).lower()}">
                        {get_risk_level(node_risk)}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Contributions
        st.markdown("**Contributions:**")
        
        income = node_data.get('income', 5000)
        activity = node_data.get('activity', 0.5)
        variability = node_data.get('variability', 0.3)
        
        col_contrib1, col_contrib2 = st.columns(2)
        
        with col_contrib1:
            income_contribution = (1 - min(income, 8000) / 8000) * 0.3
            st.metric("💰 Income", f"{income_contribution:.1%}")
        
        with col_contrib2:
            activity_contribution = (1 - activity) * 0.4
            st.metric("📈 Activity", f"{activity_contribution:.1%}")
        
        col_contrib3, col_contrib4 = st.columns(2)
        
        with col_contrib3:
            var_contribution = variability * 0.3
            st.metric("📊 Variability", f"{var_contribution:.1%}")
        
        with col_contrib4:
            # Calculate neighbor influence
            neighbors = list(st.session_state.graph.neighbors(selected_node))
            neighbor_risks = [st.session_state.graph.nodes[n]['risk'] for n in neighbors] if neighbors else [0]
            neighbor_influence = np.mean(neighbor_risks) * 0.2 if neighbors else 0
            st.metric("🤝 Neighbors", f"{neighbor_influence:.1%}")
        
        # Trend
        trend = node_data.get('trend', 'stable')
        trend_color = '#2ecc71' if trend == 'stable' else '#f39c12' if trend == 'increasing' else '#e74c3c'
        st.markdown(f"""
            <div class="insight-panel">
                <div class="insight-label">Trend</div>
                <div style="color: {trend_color}; font-weight: 600; font-size: 1.1rem;">
                    {'📈 Increasing' if trend == 'increasing' else '📉 Decreasing' if trend == 'decreasing' else '➡️ Stable'}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Neighbor Count
        st.markdown(f"""
            <div class="insight-panel">
                <div class="insight-label">Network Position</div>
                <div class="insight-value">{len(neighbors)} neighbors</div>
            </div>
        """, unsafe_allow_html=True)

        if show_centrality:
            centrality = calculate_centrality_metrics(st.session_state.graph)
            st.markdown("**🧭 Centrality Metrics:**")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Degree", f"{centrality['degree'].get(selected_node, 0):.3f}")
            with c2:
                st.metric("Betweenness", f"{centrality['betweenness'].get(selected_node, 0):.3f}")
            st.metric("Eigenvector", f"{centrality['eigenvector'].get(selected_node, 0):.3f}")
        
        # Explanation (if enabled)
        if show_explanations:
            formatted = format_node_result(selected_node, st.session_state.graph)
            st.markdown("**📝 Risk Explanation:**")
            st.info(formatted.short_summary)
            st.caption(formatted.detailed_explanation)
    
    # ========================================================================
    # NETWORK VISUALIZATION (Center Column)
    # ========================================================================
    
    with col_center:
        st.markdown("### 🕸️ Network Graph")
        
        # Create and display network visualization
        network_fig = create_network_visualization(
            st.session_state.graph,
            selected_node=selected_node,
            title="Interactive Network Visualization"
        )
        st.plotly_chart(network_fig, use_container_width=True, height=600)
    
    # ========================================================================
    # SYSTEM INSIGHTS (Right Column)
    # ========================================================================
    
    with col_right:
        st.markdown("### 🌍 System Summary")
        
        # System Stability
        system_state, state_color = get_system_stability(st.session_state.graph)
        
        status_class = f"system-status-{system_state.lower()}"
        st.markdown(f"""
            <div class="system-status {status_class}">
                <strong style="font-size: 1.1rem;">System State</strong><br>
                <span style="font-size: 1.3rem;">{system_state}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Average Risk
        st.markdown(f"""
            <div class="insight-panel">
                <div class="insight-label">Average Network Risk</div>
                <div class="insight-value">{avg_risk:.1%}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Most Critical
        top_nodes = get_top_at_risk_nodes(st.session_state.graph, 5)
        st.markdown("**Top 5 At-Risk Nodes:**")
        for rank, (node, risk) in enumerate(top_nodes, 1):
            color = get_risk_color(risk)
            st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.3rem 0; background: rgba(0,212,255,0.1); border-left: 3px solid {color}; border-radius: 4px;">
                    <strong>{rank}. {node}</strong> - Risk: <span style="color: {color}; font-weight: 600;">{risk:.1%}</span>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)
        
        # Risk Distribution
        st.markdown("**📊 Risk Distribution:**")
        dist_fig = create_risk_distribution_chart(st.session_state.graph)
        st.plotly_chart(dist_fig, use_container_width=True)
    
    # ========================================================================
    # INTERVENTION PANEL (FULL WIDTH)
    # ========================================================================
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown("### 🛟 Intervention Recommendation", unsafe_allow_html=True)
    
    # Find best intervention target
    top_nodes = get_top_at_risk_nodes(st.session_state.graph, 1)
    if top_nodes:
        target_node, target_risk = top_nodes[0]
        risk_reduction = min(target_risk, target_risk * 0.4)  # 40% reduction potential
        
        intervention_col1, intervention_col2, intervention_col3 = st.columns([1.5, 1.5, 1])
        
        with intervention_col1:
            st.markdown(f"""
                <div class="intervention-box">
                    <div class="intervention-title">🎯 Recommended Target</div>
                    <div style="font-size: 1.3rem; font-weight: 600; color: white;">
                        {target_node}
                    </div>
                    <div style="color: #aaa; font-size: 0.9rem; margin-top: 0.5rem;">
                        Current Risk: {target_risk:.1%}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with intervention_col2:
            st.markdown(f"""
                <div class="intervention-box">
                    <div class="intervention-title">📉 Expected Impact</div>
                    <div style="font-size: 1.3rem; font-weight: 600; color: #2ecc71;">
                        -{risk_reduction:.1%}
                    </div>
                    <div style="color: #aaa; font-size: 0.9rem; margin-top: 0.5rem;">
                        New Risk: {max(0, target_risk - risk_reduction):.1%}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with intervention_col3:
            confidence = min(1.0, target_risk * 1.2)
            st.markdown(f"""
                <div class="intervention-box">
                    <div class="intervention-title">✓ Confidence</div>
                    <div style="font-size: 1.3rem; font-weight: 600; color: #2ecc71;">
                        {confidence:.0%}
                    </div>
                    <div style="color: #aaa; font-size: 0.9rem; margin-top: 0.5rem;">
                        Success Probability
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Explanation
        st.info(f"""
        **Why {target_node}?**
        
        This node has the highest current risk ({target_risk:.1%}) and serves as a critical point in the network.
        Intervening here will:
        - Reduce direct risk by {risk_reduction:.1%}
        - Stabilize {len(list(st.session_state.graph.neighbors(target_node)))} connected nodes
        - Improve overall system stability from {system_state} to STABLE
        """)
    
    # ========================================================================
    # SIMULATION TIMELINE (FULL WIDTH)
    # ========================================================================
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown("### 📈 Simulation Timeline", unsafe_allow_html=True)
    
    # Create sample timeline data
    timeline_data = []
    current_avg_risk = avg_risk
    for step in range(10):
        # Simulate slight risk changes
        current_avg_risk = max(0, current_avg_risk - 0.02)
        timeline_data.append({
            'time_step': step,
            'avg_risk': current_avg_risk
        })
    
    if timeline_data:
        timeline_fig = create_timeline_chart(timeline_data)
        st.plotly_chart(timeline_fig, use_container_width=True)
    else:
        st.info("Run simulations to populate timeline data")
    
    # ========================================================================
    # BLOCKCHAIN LOG VIEWER (FULL WIDTH)
    # ========================================================================
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown("### ⛓️ Blockchain Event Log", unsafe_allow_html=True)
    
    if st.session_state.blockchain_logs:
        with st.expander("📋 View All Events", expanded=False):
            log_df = pd.DataFrame(st.session_state.blockchain_logs)
            st.dataframe(log_df, use_container_width=True, height=300)
            
            # Summary stats
            col_log1, col_log2, col_log3 = st.columns(3)
            with col_log1:
                st.metric("Total Events", len(st.session_state.blockchain_logs))
            with col_log2:
                event_types = log_df['event_type'].nunique()
                st.metric("Event Types", event_types)
            with col_log3:
                latest = log_df.iloc[-1]['timestamp'] if len(log_df) > 0 else "N/A"
                st.metric("Latest Event", latest if isinstance(latest, str) else "N/A")
    else:
        st.info("No events logged yet. Perform actions to populate the event log.")
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    
    st.markdown("<div class='spacer-lg'></div>", unsafe_allow_html=True)
    st.markdown("""
        ---
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p><strong>DCCFE - Dynamic Counterparty Credit Failure Examination</strong></p>
            <p>Professional Financial Risk Analysis & Intelligence Platform</p>
            <p style="font-size: 0.85rem; margin-top: 1rem;">
                Real-time network analysis | Risk propagation modeling | Intervention planning
            </p>
        </div>
    """, unsafe_allow_html=True)


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
