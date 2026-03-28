"""
DCCFE System - Professional Streamlit Dashboard

Clean, interactive dashboard for financial risk analysis and intervention.
"""

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from datetime import datetime

from dccfe import (
    # Presentation layer
    classify_risk,
    format_node_results,
    generate_clean_explanation,
    compute_global_summary,
    get_top_at_risk,
    prepare_graph_for_visualization,
    get_visualization_legend,
    # Pipeline
    run_refined_dccfe_pipeline,
    quick_risk_snapshot,
)
from dccfe.graph_reasoning import (
    create_user_graph,
    update_node_risk,
    propagate_risk_steps,
    simulate_user_modification,
)


# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="DCCFE Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333333;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .risk-low { color: #2ecc71; font-weight: bold; }
    .risk-medium { color: #f39c12; font-weight: bold; }
    .risk-high { color: #e74c3c; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

@st.cache_resource
def create_sample_data():
    """Create sample dataset for demonstration."""
    return pd.DataFrame({
        "user_id": ["U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8"],
        "income": [3500, 1800, 5200, 2100, 4800, 3200, 2800, 5500],
        "activity": [0.82, 0.35, 0.92, 0.25, 0.75, 0.60, 0.45, 0.88],
        "transaction_variability": [0.18, 0.75, 0.12, 0.88, 0.28, 0.40, 0.65, 0.15],
    })


def initialize_session_state():
    """Initialize session state variables."""
    if "data" not in st.session_state:
        st.session_state.data = create_sample_data()
    
    if "graph" not in st.session_state:
        st.session_state.graph = None
        st.session_state.result = None
    
    if "selected_node" not in st.session_state:
        st.session_state.selected_node = "U1"
    
    if "simulation_steps" not in st.session_state:
        st.session_state.simulation_steps = 3


initialize_session_state()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_risk_color(risk_level: str) -> str:
    """Get color for risk level."""
    colors = {
        "low": "#2ecc71",
        "medium": "#f39c12",
        "high": "#e74c3c",
    }
    return colors.get(risk_level, "#95a5a6")


def create_interactive_graph(graph, node_styles, selected_node=None):
    """Create interactive Plotly graph visualization."""
    if len(graph.nodes) == 0:
        return None
    
    # Get layout
    pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)
    
    # Create edges
    edge_x, edge_y = [], []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        showlegend=False
    )
    
    # Create nodes
    node_x, node_y, node_color, node_size, node_text = [], [], [], [], []
    for node in graph.nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        style = node_styles.get(node, {})
        node_color.append(style.get("color", "#95a5a6"))
        node_size.append(style.get("size", 15))
        
        risk = float(graph.nodes[node].get("risk", 0.0))
        node_text.append(f"{node}<br>Risk: {risk:.1%}")
    
    # Highlight selected node
    if selected_node and selected_node in graph.nodes:
        idx = list(graph.nodes).index(selected_node)
        node_size[idx] = max(node_size) * 1.5  # Make it bigger
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[node for node in graph.nodes],
        textposition="top center",
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=node_size,
            color=node_color,
            line_width=2,
            line_color='white' if selected_node else '#888',
        ),
        showlegend=False
    )
    
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Network Risk Visualization",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500,
    )
    
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main Streamlit app."""
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<div class='main-title'>📊 DCCFE Financial Risk Dashboard</div>", 
                   unsafe_allow_html=True)
    with col2:
        st.write(f"*Last updated: {datetime.now().strftime('%H:%M:%S')}*")
    
    st.markdown("---")
    
    # ========================================================================
    # SIDEBAR CONTROLS
    # ========================================================================
    
    with st.sidebar:
        st.markdown("### 🎮 Controls")
        
        # Data upload
        st.markdown("**Data Management**")
        upload_file = st.file_uploader("Upload CSV", type="csv", key="upload")
        if upload_file:
            st.session_state.data = pd.read_csv(upload_file)
            st.success("Data loaded!")
        
        # Run analysis
        if st.button("🔄 Run Analysis", key="run_analysis"):
            with st.spinner("Running analysis..."):
                st.session_state.result = run_refined_dccfe_pipeline(
                    st.session_state.data,
                    print_output=False
                )
                st.success("Analysis complete!")
        
        st.markdown("---")
        
        # Node selection
        st.markdown("**Node Operations**")
        node_options = st.session_state.data["user_id"].tolist()
        st.session_state.selected_node = st.selectbox(
            "Select Node",
            node_options,
            key="node_select"
        )
        
        # Node modifications
        node_data = st.session_state.data[
            st.session_state.data["user_id"] == st.session_state.selected_node
        ].iloc[0]
        
        st.markdown("**Modify Node**")
        new_income = st.slider(
            "Income",
            min_value=500,
            max_value=10000,
            value=int(node_data["income"]),
            step=100,
            key="income_slider"
        )
        
        new_activity = st.slider(
            "Activity",
            min_value=0.0,
            max_value=1.0,
            value=float(node_data["activity"]),
            step=0.05,
            key="activity_slider"
        )
        
        if st.button("📝 Apply Changes", key="apply_changes"):
            # Update in dataframe
            idx = st.session_state.data[
                st.session_state.data["user_id"] == st.session_state.selected_node
            ].index[0]
            st.session_state.data.at[idx, "income"] = new_income
            st.session_state.data.at[idx, "activity"] = new_activity
            st.success(f"Updated {st.session_state.selected_node}")
        
        st.markdown("---")
        
        # Simulation controls
        st.markdown("**Simulation**")
        st.session_state.simulation_steps = st.slider(
            "Propagation Steps",
            min_value=1,
            max_value=10,
            value=3,
            key="sim_steps"
        )
        
        if st.button("🌊 Run Propagation", key="propagate"):
            with st.spinner("Propagating risk..."):
                if st.session_state.result and st.session_state.graph:
                    # Simulate propagation
                    history = propagate_risk_steps(
                        st.session_state.graph,
                        steps=st.session_state.simulation_steps
                    )
                    st.session_state.prop_history = history
                    st.success("Propagation complete!")
        
        if st.button("⚡ Trigger Shock Event", key="shock"):
            with st.spinner("Applying shock..."):
                if st.session_state.result and st.session_state.graph:
                    # Increase risk for selected node
                    current_risk = float(
                        st.session_state.graph.nodes[st.session_state.selected_node].get("risk", 0.0)
                    )
                    new_risk = min(1.0, current_risk + 0.15)
                    update_node_risk(st.session_state.graph, st.session_state.selected_node, new_risk)
                    st.success(f"Risk increased for {st.session_state.selected_node}")
    
    # ========================================================================
    # MAIN CONTENT
    # ========================================================================
    
    # Run initial analysis if needed
    if st.session_state.result is None:
        with st.spinner("Loading system..."):
            st.session_state.result = run_refined_dccfe_pipeline(
                st.session_state.data,
                print_output=False
            )
    
    result = st.session_state.result
    
    # ========================================================================
    # SECTION 1: SYSTEM SUMMARY
    # ========================================================================
    
    st.markdown("<div class='section-header'>📈 System Summary</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_risk = result['quality_metrics']['average_risk']
        st.metric(
            "Average Risk",
            f"{avg_risk:.1%}",
            delta=f"Network {'Stable' if avg_risk < 0.4 else 'At Risk'}"
        )
    
    with col2:
        system_state = result['quality_metrics']['system_state']
        state_color = {
            'stable': '🟢',
            'fragile': '🟡',
            'critical': '🔴'
        }.get(system_state, '⚪')
        st.metric(
            "System State",
            f"{state_color} {system_state.upper()}",
        )
    
    with col3:
        high_risk = result['quality_metrics']['high_risk_count']
        st.metric(
            "High-Risk Nodes",
            high_risk,
            delta=f"of {result['quality_metrics']['nodes_analyzed']}"
        )
    
    with col4:
        st.metric(
            "Blockchain",
            "✅ Valid" if result['blockchain_valid'] else "❌ Invalid",
        )
    
    # System assessment
    if 'system_summary' in result:
        assessment = result['system_summary'].get('assessment', '')
        if assessment:
            st.info(f"📋 {assessment}")
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 2: GRAPH VISUALIZATION & NODE ANALYSIS
    # ========================================================================
    
    col_graph, col_node = st.columns([1.5, 1])
    
    with col_graph:
        st.markdown("<div class='section-header'>🔗 Network Visualization</div>",
                   unsafe_allow_html=True)
        
        # Create graph for visualization
        if st.session_state.graph is None:
            # Create edges for initial graph
            user_ids = result['node_results'][0]['node_id'] if result['node_results'] else []
            if not isinstance(user_ids, str):
                user_ids = [n['node_id'] for n in result['node_results']]
            
            edges = []
            for i in range(len(user_ids) - 1):
                edges.append((user_ids[i], user_ids[i+1]))
            
            # Create dummy graph from data
            users = st.session_state.data.to_dict("records")
            st.session_state.graph = create_user_graph(users, edges if edges else [])
        
        graph = st.session_state.graph
        viz_graph, node_styles = prepare_graph_for_visualization(graph)
        
        fig = create_interactive_graph(graph, node_styles, st.session_state.selected_node)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col_node:
        st.markdown("<div class='section-header'>🔍 Node Analysis</div>",
                   unsafe_allow_html=True)
        
        # Find selected node in results
        node_info = None
        for node in result['node_results']:
            if node['node_id'] == st.session_state.selected_node:
                node_info = node
                break
        
        if node_info:
            # Risk level with color
            risk_level = node_info['risk_level']
            risk_color = get_risk_color(risk_level)
            st.markdown(f"**Risk Level:** <span style='color:{risk_color};font-weight:bold;'>"
                       f"{risk_level.upper()}</span>", unsafe_allow_html=True)
            
            # Risk score
            st.metric("Final Risk", f"{node_info['final_risk']:.1%}")
            st.metric("Trend", node_info['trend'].capitalize())
            
            # Contribution breakdown
            st.markdown("**Risk Contributions:**")
            contrib = node_info['contributions']
            contrib_df = pd.DataFrame({
                'Factor': ['Income', 'Activity', 'Variability', 'Neighbors'],
                'Impact': [
                    contrib['income'],
                    contrib['activity'],
                    contrib['variability'],
                    contrib['neighbor_influence']
                ]
            })
            st.bar_chart(contrib_df.set_index('Factor'))
            
            # Centrality metrics
            st.markdown("**Network Position:**")
            cent = node_info['centrality']
            st.write(f"- Degree Centrality: {cent['degree']:.4f}")
            st.write(f"- Betweenness: {cent['betweenness']:.4f}")
            st.write(f"- Eigenvector: {cent['eigenvector']:.4f}")
        else:
            st.warning("Node not found in analysis results")
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 3: NODE EXPLANATIONS
    # ========================================================================
    
    st.markdown("<div class='section-header'>💡 Detailed Analysis</div>", unsafe_allow_html=True)
    
    # Explanation
    if node_info:
        st.markdown("**Why is this node at risk?**")
        st.info(node_info['explanation'])
    
    # Top at-risk nodes
    st.markdown("**Top 5 Highest-Risk Nodes:**")
    top_nodes = result['node_results'][:5]
    
    top_df = pd.DataFrame({
        'Node': [n['node_id'] for n in top_nodes],
        'Risk': [f"{n['final_risk']:.1%}" for n in top_nodes],
        'Level': [n['risk_level'].upper() for n in top_nodes],
        'Trend': [n['trend'].capitalize() for n in top_nodes],
    })
    st.dataframe(top_df, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 4: INTERVENTIONS
    # ========================================================================
    
    st.markdown("<div class='section-header'>🎯 Intervention Recommendations</div>",
               unsafe_allow_html=True)
    
    if result.get('intervention'):
        interv = result['intervention']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Target Node", interv['recommended_node'])
        
        with col2:
            impact_color = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(interv['expected_impact'], '⚪')
            st.metric("Expected Impact", f"{impact_color} {interv['expected_impact'].upper()}")
        
        with col3:
            st.metric("Confidence", f"{interv['confidence']:.1%}")
        
        # Explanation
        st.markdown("**Recommendation:**")
        st.info(interv['reason'])
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Apply Intervention", key="apply_intervention"):
                target = interv['recommended_node']
                if target in graph.nodes:
                    current_risk = float(graph.nodes[target].get("risk", 0.0))
                    new_risk = max(0.0, current_risk - (current_risk * 0.3))
                    update_node_risk(graph, target, new_risk)
                    st.success(f"Intervention applied to {target}. Risk reduced by 30%")
        
        with col2:
            if st.button("📊 View Alternative Options", key="alternatives"):
                st.info("Alternative interventions would target secondary nodes based on cascade effects")
    else:
        st.warning("No interventions recommended at this time")
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 5: DETAILED METRICS
    # ========================================================================
    
    with st.expander("📊 Detailed Metrics"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**All Nodes:**")
            all_nodes_df = pd.DataFrame({
                'Node': [n['node_id'] for n in result['node_results']],
                'Risk': [f"{n['final_risk']:.2%}" for n in result['node_results']],
                'Level': [n['risk_level'] for n in result['node_results']],
            })
            st.dataframe(all_nodes_df, use_container_width=True)
        
        with col2:
            st.markdown("**Risk Distribution:**")
            risk_counts = {
                'Low': sum(1 for n in result['node_results'] if n['risk_level'] == 'low'),
                'Medium': sum(1 for n in result['node_results'] if n['risk_level'] == 'medium'),
                'High': sum(1 for n in result['node_results'] if n['risk_level'] == 'high'),
            }
            st.bar_chart(pd.DataFrame({
                'Category': list(risk_counts.keys()),
                'Count': list(risk_counts.values())
            }).set_index('Category'))
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
    🔒 DCCFE System v1.0 | Professional Financial Risk Dashboard<br>
    All analysis is based on network propagation and hybrid risk models
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
