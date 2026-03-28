from __future__ import annotations

from typing import Dict, List, Tuple

import networkx as nx
import plotly.graph_objects as go


def _build_layout(graph: nx.Graph) -> Dict[str, Tuple[float, float]]:
    if graph.number_of_nodes() == 0:
        return {}
    return nx.spring_layout(graph, seed=42)


def _edge_weight_bounds(graph: nx.Graph) -> Tuple[float, float]:
    if graph.number_of_edges() == 0:
        return 1.0, 1.0
    weights = [float(data.get("weight", 1.0)) for _, _, data in graph.edges(data=True)]
    return min(weights), max(weights)


def _scale_edge_width(
    weight: float,
    min_weight: float,
    max_weight: float,
    min_width: float = 1.0,
    max_width: float = 5.0,
) -> float:
    if max_weight <= min_weight:
        return (min_width + max_width) / 2.0
    normalized = (float(weight) - min_weight) / (max_weight - min_weight)
    return min_width + normalized * (max_width - min_width)


def _add_weighted_edge_traces(fig: go.Figure, graph: nx.Graph, layout: Dict[str, Tuple[float, float]]) -> None:
    min_weight, max_weight = _edge_weight_bounds(graph)

    first = True
    for source, target, data in graph.edges(data=True):
        x0, y0 = layout[source]
        x1, y1 = layout[target]
        weight = float(data.get("weight", 1.0))
        width = _scale_edge_width(weight, min_weight, max_weight)

        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=width, color="#7a7a7a"),
                hovertext=f"{source} ↔ {target}<br>Strength: {weight:.3f}",
                hoverinfo="text",
                name="Relationships",
                showlegend=first,
            )
        )
        first = False


def _add_node_trace(fig: go.Figure, graph: nx.Graph, layout: Dict[str, Tuple[float, float]]) -> None:
    node_x: List[float] = []
    node_y: List[float] = []
    node_labels: List[str] = []
    node_hover: List[str] = []
    node_risk: List[float] = []

    for node, data in graph.nodes(data=True):
        x, y = layout[node]
        risk = float(data.get("risk", 0.0))
        income = float(data.get("income", 0.0))
        activity = float(data.get("activity", 0.0))

        node_x.append(x)
        node_y.append(y)
        node_labels.append(str(node))
        node_risk.append(risk)
        node_hover.append(
            f"{node}<br>Risk: {risk:.3f}<br>Income: {income:.2f}<br>Activity: {activity:.2f}"
        )

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_labels,
            textposition="top center",
            hovertext=node_hover,
            hoverinfo="text",
            marker=dict(
                showscale=True,
                colorscale="YlOrRd",
                color=node_risk,
                cmin=0.0,
                cmax=1.0,
                colorbar=dict(
                    title=dict(text="Risk Score", font=dict(size=14, color="#ffffff", family="Arial Black")),
                    tickformat=".0%",
                    bgcolor="rgba(2,6,23,0.95)",
                    tickcolor="#22d3ee",
                    tickfont=dict(color="#ffffff", size=12),
                    bordercolor="#22d3ee",
                    borderwidth=3,
                    thickness=20,
                    len=0.7,
                    x=1.02,
                ),
                size=26,
                line=dict(color="#111827", width=2),
            ),
            name="Users",
            showlegend=False,
        )
    )


def _add_legend_traces(fig: go.Figure) -> None:
    # Edge strength legend only. Node risk is shown in the color bar.
    fig.add_trace(
        go.Scatter(
            x=[None, None],
            y=[None, None],
            mode="lines",
            line=dict(width=1.0, color="#3b82f6"),
            name="Weak Relationship (1px)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None, None],
            y=[None, None],
            mode="lines",
            line=dict(width=5.0, color="#ff6b35"),
            name="Strong Relationship (5px)",
        )
    )


def _build_enhanced_figure(graph: nx.Graph, title: str) -> go.Figure:
    layout = _build_layout(graph)
    fig = go.Figure()

    _add_weighted_edge_traces(fig, graph, layout)
    _add_node_trace(fig, graph, layout)
    _add_legend_traces(fig)

    fig.update_layout(
        title=title,
        showlegend=True,
        legend=dict(
            title=dict(text="Edge Strength Legend", font=dict(size=14, color="#ffffff")),
            font=dict(color="#ffffff", size=13),
            bgcolor="rgba(5,8,22,0.96)",
            bordercolor="#22d3ee",
            borderwidth=3,
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
        ),
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


def build_risk_figure(graph: nx.Graph) -> go.Figure:
    return _build_enhanced_figure(graph, title="DCCFE Network Risk Propagation")


def build_partial_risk_figure(
    graph: nx.Graph,
    top_risk_nodes: int = 25,
    top_central_nodes: int = 25,
) -> go.Figure:
    """Render only high-risk and high-centrality nodes for large networks."""
    limit = max(int(top_risk_nodes) + int(top_central_nodes), 60)
    if graph.number_of_nodes() <= limit:
        return build_risk_figure(graph)

    risk_ranked = sorted(graph.nodes, key=lambda n: float(graph.nodes[n].get("risk", 0.0)), reverse=True)
    centrality = nx.degree_centrality(graph)
    central_ranked = sorted(centrality, key=lambda n: float(centrality[n]), reverse=True)

    keep = set([str(n) for n in risk_ranked[: int(top_risk_nodes)]] + [str(n) for n in central_ranked[: int(top_central_nodes)]])
    subgraph = graph.subgraph(keep).copy()
    fig = build_risk_figure(subgraph)
    fig.update_layout(title=f"DCCFE Partial Risk View ({subgraph.number_of_nodes()} of {graph.number_of_nodes()} nodes)")
    return fig


def render_risk_graph(graph: nx.Graph) -> go.Figure:
    """Render graph with weighted edges and original continuous risk color mapping."""
    return _build_enhanced_figure(graph, title="Risk Graph")
