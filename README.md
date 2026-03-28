# CascadeX // Decentralized Cognitive Causality Financial Engine

Real-time decentralized financial risk analysis system with reusable modular layers:

- Cognitive layer for per-user behavioral risk scoring
- Network layer with user dependency graph (NetworkX)
- Causal rule engine for explainable risk changes
- Dynamic risk propagation across connected users
- Counterfactual simulator for what-if interventions
- Intervention ranking to reduce systemic risk
- Hash-based blockchain-style immutable event log
- Simulated IoT updates for continuous state refresh
- Live risk graph visualization with Plotly

## Real-Time Workflow

The system is designed for live state updates, not a static demo flow.

1. Initialize with 5 to 10 users and relationship data.
2. Apply live user upserts or relationship upserts.
3. Push IoT-style activity events continuously.
4. Recompute risk, causes, propagation, and interventions in real time.

## Data Requirements

### User fields

- user_id
- income
- activity (0.0 to 1.0)
- transactions
- defaults

### Relationship fields

- source
- target
- weight
- relation_type

Constraint: active graph must contain 5 to 10 users for risk computation.

## Install

1. Create and activate your Python environment.
2. Install dependencies:

pip install -r requirements.txt

## Run

streamlit run app.py

## Expert Analyst Report (LLM)

Set your Groq API key via environment variable (recommended):

Windows PowerShell:

$env:GROQ_API_KEY = "your_key_here"

Then generate a professional 2-paragraph risk assessment from live pipeline output:

c:/Users/saiad/OneDrive/Documents/PROJECT/.venv/Scripts/python.exe generate_expert_report.py

Notes:
- The key is read from GROQ_API_KEY and is not hardcoded in source files.
- Prompt construction logic is in dccfe/analyst_report.py.

## Output Provided

- Risk score for each user node
- Risk propagation graph with node-level risk coloring
- Human-readable risk explanation per user
- Counterfactual outcomes after changing income and activity
- Ranked interventions by expected systemic risk reduction
- Immutable blockchain log of risk and action events

## Full Scaling Mode (50 to 500+ Users)

Run the scalable pipeline with synthetic or external datasets while preserving explainability:

python -c "from dccfe import ScalingConfig, run_full_scaling_mode; r=run_full_scaling_mode(config=ScalingConfig(user_count=500, network_mode='preferential_attachment')); print(r['system_summary']); print(r['top_risky_nodes'][:3])"

Features in scaling mode:
- Large network generation (50, 100, 500+ users)
- Random or scale-free relationship generation
- Cached adjacency for fast neighbor lookup
- Batch diffusion updates with bounded iterations (max 10)
- Partial graph visualization for large networks
- Aggregated metrics (histogram, top risk, centrality ranking)
- Shortlist intervention optimization
- Key-event logging control for memory stability
- System-level plus critical-node report generation

Scaling output schema:

{
	"system_summary": {...},
	"top_risky_nodes": [...],
	"intervention": {...},
	"stability": {...}
}

## Architecture

- app.py: real-time UI for ingestion, updates, simulation, and visualization
- dccfe/engine.py: orchestration across all layers
- dccfe/cognitive.py: lightweight explainable risk scoring
- dccfe/network_layer.py: graph node and edge management
- dccfe/causal_engine.py: causal rule application
- dccfe/propagation.py: dynamic contagion propagation
- dccfe/intervention.py: critical node analysis and intervention ranking
- dccfe/blockchain.py: hash-chain event logging
- dccfe/visualization.py: interactive graph rendering
