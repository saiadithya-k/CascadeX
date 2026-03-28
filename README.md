# CascadeX

Financial Risk Intelligence platform for real-time network risk monitoring, explainable causal analysis, contagion simulation, and intervention planning.

CascadeX combines behavioral signals and graph dynamics into a live operational dashboard designed for analyst workflows and executive decision support.

## Why CascadeX

- Real-time risk updates from user and relationship events
- Explainable risk decomposition (income, activity, variability, network influence)
- Dynamic propagation modeling across connected entities
- What-if simulation and intervention optimization
- Blockchain-style immutable event timeline
- Interactive Streamlit dashboard with Plotly network visuals
- Scalable execution path for 50 to 500+ users

## Core Capabilities

1. Data ingestion and validation for users and relationships
2. Hybrid risk modeling (rule-based plus ML probability)
3. Causal adjustment with human-readable explanations
4. Multi-step network propagation
5. Counterfactual simulation and trajectory analysis
6. Intervention ranking by systemic impact
7. Stability classification: stable, fragile, critical
8. Optional analyst narrative generation through Groq

## Tech Stack

- Python 3.10+
- Streamlit
- NetworkX
- Plotly
- NumPy, Pandas, scikit-learn

## Quick Start

### 1) Install

```bash
pip install -r requirements.txt
```

### 2) Run locally

```bash
streamlit run app.py
```

### 3) Open dashboard

Visit `http://localhost:8501` in your browser.

## Streamlit Cloud Deployment

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app with:
	 - Branch: `main`
	 - Main file path: `app.py`
4. Add secrets in app settings:

```toml
GROQ_API_KEY = "your_real_key"
```

Reference template: `.streamlit/secrets.toml.example`.

## Data Contracts

### Users CSV

Required columns:

- `user_id`
- `income` (must be `> 0`)
- `activity` (range `0..1`)
- `transactions` (non-negative integer)
- `defaults` (non-negative integer)

### Relationships CSV

Required columns:

- `source`
- `target`
- `weight`
- `relation_type`

Recommended `weight` range is `0..1` for normalized influence semantics.

## Project Structure

```text
app.py                          # Main Streamlit dashboard
dccfe/engine.py                 # Orchestration layer
dccfe/cognitive.py              # Risk scoring logic
dccfe/causal_engine.py          # Causal contribution updates
dccfe/propagation.py            # Diffusion engine
dccfe/intervention.py           # Intervention optimization
dccfe/visualization.py          # Graph visualization utilities
dccfe/analyst_report.py         # LLM report generation
dccfe/scaling.py                # Large-scale execution mode
```

## Output Model

Primary pipeline and validation outputs include:

```json
{
	"system_summary": {},
	"node_results": [],
	"intervention": {},
	"reports": {},
	"validation_status": true
}
```

## Validation and Quality

Comprehensive end-to-end validation is available through:

```bash
python validate_end_to_end.py
```

This checks data quality, model behavior, graph integrity, causal and propagation correctness, simulation consistency, intervention impact, stability metrics, edge cases, and performance.

## Scaling Mode

Run a high-volume scenario:

```bash
python run_full_scaling_mode.py
```

Or from Python:

```python
from dccfe import ScalingConfig, run_full_scaling_mode

result = run_full_scaling_mode(
		config=ScalingConfig(
				user_count=500,
				network_mode="preferential_attachment",
				average_degree=8,
		)
)
print(result["system_summary"])
```

## Security Notes

- Keep `.streamlit/secrets.toml` out of source control.
- Use environment variables or Streamlit Cloud secrets for API keys.
- Do not hardcode credentials in scripts or notebooks.

## License

Use and adapt for research, demonstration, and internal analytics workflows.
