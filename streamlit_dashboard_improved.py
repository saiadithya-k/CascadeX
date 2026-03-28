"""
DCCFE - Professional Financial Risk Intelligence Dashboard
Redesigned with improved UI/UX and better layout
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="DCCFE Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CSS STYLING - IMPROVED MODERN DESIGN
# ============================================================================

st.markdown("""
    <style>
    /* Remove default padding */
    .main { padding: 0; }
    
    /* Hero Header */
    .hero-header {
        background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
        padding: 2rem 3rem;
        border-bottom: 3px solid #00d4ff;
        margin: -1rem -1rem 2rem -1rem;
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #00d4ff;
        margin: 0;
        font-family: 'Segoe UI', sans-serif;
    }
    
    .hero-subtitle {
        font-size: 0.95rem;
        color: #aaa;
        margin-top: 0.3rem;
        letter-spacing: 0.5px;
    }
    
    /* Metrics Row */
    .metrics-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        border: 1px solid #00d4ff;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00d4ff;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-delta {
        font-size: 0.85rem;
        color: #00d4ff;
        margin-top: 0.5rem;
    }
    
    /* Section Header */
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #00d4ff;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.7rem;
        border-bottom: 2px solid #00d4ff;
    }
    
    /* Cards */
    .insight-card {
        background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        border-left: 4px solid #00d4ff;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .card-label {
        font-size: 0.75rem;
        color: #00d4ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.3rem;
    }
    
    .card-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
    }
    
    /* Risk Badge */
    .risk-badge {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    .badge-low {
        background-color: rgba(46, 204, 113, 0.2);
        color: #2ecc71;
        border: 1px solid #2ecc71;
    }
    
    .badge-medium {
        background-color: rgba(243, 156, 18, 0.2);
        color: #f39c12;
        border: 1px solid #f39c12;
    }
    
    .badge-high {
        background-color: rgba(231, 76, 60, 0.2);
        color: #e74c3c;
        border: 1px solid #e74c3c;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        width: 250px;
    }
    
    .sidebar-section {
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(0, 212, 255, 0.2);
    }
    
    .sidebar-section:last-child {
        border-bottom: none;
    }
    
    .sidebar-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #00d4ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA FUNCTIONS
# ============================================================================

def create_default_network():
    """Create default test network."""
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
            risk=risk
        )
    
    edges = [
        ("U1", "U2", 0.8), ("U2", "U3", 0.9), ("U3", "U4", 0.7),
        ("U4", "U5", 0.75), ("U5", "U6", 0.6), ("U6", "U1", 0.65),
    ]
    
    for u, v, weight in edges:
        graph.add_edge(u, v, weight=weight)
    
    return graph

def get_risk_color(risk):
    if risk < 0.3:
        return "#2ecc71"
    elif risk < 0.7:
        return "#f39c12"
    else:
        return "#e74c3c"

def get_risk_level(risk):
    if risk < 0.3:
        return "LOW"
    elif risk < 0.7:
        return "MEDIUM"
    else:
        return "HIGH"

def create_network_graph(graph, selected_node):
    """Create interactive network visualization."""
    pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)
    
    # Edges
    edge_x, edge_y = [], []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Centrality for sizing
    centrality = nx.degree_centrality(graph)
    
    # Node data
    node_x, node_y, node_color, node_size = [], [], [], []
    node_text, node_hover = [], []
    
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        risk = graph.nodes[node].get('risk', 0.5)
        income = graph.nodes[node].get('income', 0)
        activity = graph.nodes[node].get('activity', 0)
        
        node_color.append(risk)
        node_size.append(25 + centrality[node] * 35)
        node_text.append(node)
        
        hover = f"<b>{node}</b><br>Risk: {risk:.1%}<br>Income: ${income:,}<br>Activity: {activity:.0%}"
        node_hover.append(hover)
    
    fig = go.Figure()
    
    # Edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1.5, color='rgba(0, 212, 255, 0.2)'),
        hoverinfo='none',
        showlegend=False
    ))
    
    # Nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        textfont=dict(size=11, color='white', family='Arial Black'),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=node_hover,
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale='RdYlGn_r',
            cmin=0, cmax=1,
            showscale=True,
            colorbar=dict(
                title="Risk",
                thickness=12,
                len=0.7,
                tickformat='.0%'
            ),
            line=dict(
                width=3,
                color=['#00d4ff' if n == selected_node else 'white' for n in graph.nodes()]
            )
        ),
        showlegend=False
    ))
    
    fig.update_layout(
        title=dict(text="<b>Network Visualization</b>", font=dict(size=16, color='#00d4ff')),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=550,
        font=dict(color='white')
    )
    
    return fig

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session():
    if 'graph' not in st.session_state:
        st.session_state.graph = create_default_network()
    if 'selected_node' not in st.session_state:
        nodes = list(st.session_state.graph.nodes())
        st.session_state.selected_node = nodes[0] if nodes else None
    if 'events' not in st.session_state:
        st.session_state.events = []

init_session()

# ============================================================================
# MAIN LAYOUT
# ============================================================================

# HERO HEADER
st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">📊 DCCFE - Financial Risk Intelligence Dashboard</h1>
        <p class="hero-subtitle">Real-time network analysis, risk monitoring & intervention planning</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("<div class='sidebar-title'>👤 Node Control</div>", unsafe_allow_html=True)
    
    nodes_list = list(st.session_state.graph.nodes())
    selected = st.selectbox("Select Node", nodes_list, key="node_select")
    st.session_state.selected_node = selected
    
    st.markdown("<div class='sidebar-title' style='margin-top: 1.5rem;'>⚙️ Parameters</div>", unsafe_allow_html=True)
    
    income = st.slider("💰 Income", 500, 10000, 5200, 500)
    activity = st.slider("📈 Activity", 0.0, 1.0, 0.5, 0.05)
    variability = st.slider("📊 Variability", 0.0, 1.0, 0.3, 0.05)
    
    st.markdown("<div class='sidebar-title' style='margin-top: 1.5rem;'>🎯 Actions</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Simulate", use_container_width=True):
            st.session_state.graph.nodes[selected]['income'] = income
            st.session_state.graph.nodes[selected]['activity'] = activity
            st.session_state.graph.nodes[selected]['variability'] = variability
            new_risk = max(0.0, min(1.0, 
                (1 - min(income, 8000) / 8000) * 0.3 + 
                (1 - activity) * 0.4 + 
                variability * 0.3
            ))
            st.session_state.graph.nodes[selected]['risk'] = new_risk
            st.session_state.events.append(f"Simulated {selected}: {new_risk:.1%}")
            st.rerun()
    
    with col2:
        if st.button("🌊 Cascade", use_container_width=True):
            neighbors = list(st.session_state.graph.neighbors(selected))
            for n in neighbors:
                current = st.session_state.graph.nodes[n]['risk']
                new = min(1.0, current + 0.15)
                st.session_state.graph.nodes[n]['risk'] = new
            st.session_state.events.append(f"Cascaded from {selected}")
            st.rerun()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("⚡ Shock", use_container_width=True):
            st.session_state.graph.nodes[selected]['risk'] = min(1.0, 
                st.session_state.graph.nodes[selected]['risk'] + 0.3)
            st.session_state.events.append(f"Shock on {selected}")
            st.rerun()
    
    with col4:
        if st.button("🛟 Intervene", use_container_width=True):
            st.session_state.graph.nodes[selected]['risk'] = max(0.0,
                st.session_state.graph.nodes[selected]['risk'] - 0.2)
            st.session_state.events.append(f"Intervened on {selected}")
            st.rerun()

# ============================================================================
# SYSTEM METRICS
# ============================================================================

risks = [data.get('risk', 0.5) for _, data in st.session_state.graph.nodes(data=True)]
avg_risk = np.mean(risks)
high_risk_count = sum(1 for r in risks if r >= 0.7)
system_state = "CRITICAL" if avg_risk > 0.7 else "FRAGILE" if avg_risk > 0.3 else "STABLE"
state_color = "#e74c3c" if system_state == "CRITICAL" else "#f39c12" if system_state == "FRAGILE" else "#2ecc71"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Avg Risk", f"{avg_risk:.1%}", f"{(avg_risk - 0.45):.1%}")

with col2:
    st.metric("🔴 High-Risk", high_risk_count, delta=high_risk_count - 2)

with col3:
    st.metric("🏥 System", system_state, delta="OK" if system_state == "STABLE" else "⚠️")

with col4:
    top_node = max(st.session_state.graph.nodes(), key=lambda n: st.session_state.graph.nodes[n]['risk'])
    top_risk = st.session_state.graph.nodes[top_node]['risk']
    st.metric("⚠️ Critical", top_node, f"{top_risk:.1%}")

# ============================================================================
# MAIN CONTENT - 2 COLUMN LAYOUT
# ============================================================================

st.markdown("<h2 class='section-title'>📊 Network Analysis</h2>", unsafe_allow_html=True)

left, right = st.columns([2.5, 1], gap="medium")

with left:
    # Network Graph
    fig = create_network_graph(st.session_state.graph, st.session_state.selected_node)
    st.plotly_chart(fig, use_container_width=True, height=550)

with right:
    st.markdown("<h3 style='color: #00d4ff; margin-top: 0;'>Node Details</h3>", unsafe_allow_html=True)
    
    node_data = st.session_state.graph.nodes[st.session_state.selected_node]
    node_risk = node_data.get('risk', 0.5)
    
    st.markdown(f"""
        <div class="insight-card">
            <div class="card-label">Risk Score</div>
            <div class="card-value">{node_risk:.1%}</div>
            <span class="risk-badge badge-{get_risk_level(node_risk).lower()}">
                {get_risk_level(node_risk)}
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    income = node_data.get('income', 5000)
    activity = node_data.get('activity', 0.5)
    variability = node_data.get('variability', 0.3)
    
    st.markdown(f"""
        <div class="insight-card">
            <div class="card-label">Income Contribution</div>
            <div class="card-value">{(1 - min(income, 8000) / 8000) * 0.3:.1%}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="insight-card">
            <div class="card-label">Activity Contribution</div>
            <div class="card-value">{(1 - activity) * 0.4:.1%}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="insight-card">
            <div class="card-label">Variability Contribution</div>
            <div class="card-value">{variability * 0.3:.1%}</div>
        </div>
    """, unsafe_allow_html=True)
    
    neighbors = list(st.session_state.graph.neighbors(st.session_state.selected_node))
    st.markdown(f"""
        <div class="insight-card">
            <div class="card-label">Connected Nodes</div>
            <div class="card-value">{len(neighbors)}</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================================
# BOTTOM SECTION
# ============================================================================

st.markdown("<h2 class='section-title'>📈 System Overview</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Risk Distribution
    fig_dist = go.Figure(data=[
        go.Histogram(x=risks, nbinsx=8, marker=dict(color='rgba(0, 212, 255, 0.7)'))
    ])
    fig_dist.update_layout(
        title=dict(text="<b>Risk Distribution</b>", font=dict(size=14, color='#00d4ff')),
        xaxis_title="Risk Score",
        yaxis_title="Nodes",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300,
        showlegend=False
    )
    st.plotly_chart(fig_dist, use_container_width=True)

with col2:
    # Top Nodes
    st.markdown("**Top 5 At-Risk Nodes**")
    risks_sorted = sorted([(n, st.session_state.graph.nodes[n]['risk']) 
                          for n in st.session_state.graph.nodes()], 
                         key=lambda x: x[1], reverse=True)
    
    for i, (node, risk) in enumerate(risks_sorted[:5], 1):
        color = get_risk_color(risk)
        st.markdown(f"""
            <div style="padding: 0.5rem; margin: 0.3rem 0; 
                        background: rgba(0,212,255,0.08); 
                        border-left: 3px solid {color}; 
                        border-radius: 4px;">
                <strong>{i}. {node}</strong> - <span style="color: {color};">{risk:.1%}</span>
            </div>
        """, unsafe_allow_html=True)

# ============================================================================
# EVENT LOG
# ============================================================================

st.markdown("<h2 class='section-title'>📋 Activity Log</h2>", unsafe_allow_html=True)

if st.session_state.events:
    with st.expander("View Recent Actions", expanded=False):
        for event in reversed(st.session_state.events[-10:]):
            st.write(f"• {event}")
else:
    st.info("No actions yet. Use sidebar controls to start.")

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem 0;'>
        <small>DCCFE • Financial Risk Intelligence Dashboard • v1.0</small>
    </div>
""", unsafe_allow_html=True)
