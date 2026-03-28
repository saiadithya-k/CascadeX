"""
STREAMLIT DASHBOARD - QUICK REFERENCE CARD

One-page reference for key dashboard features.
"""

reference = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                   DCCFE DASHBOARD - QUICK REFERENCE CARD                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━ LAUNCH ━━━━━━━━━━━━━━━━━━━━━━━━

  streamlit run streamlit_dashboard.py
  
  Then open: http://localhost:8501


━━━━━━━━━━━━━━━━━━━━━━━ LAYOUT ━━━━━━━━━━━━━━━━━━━━━━━

  ┌─────────────────────────────────────────────────┐
  │  📊 DCCFE Financial Risk Dashboard              │
  ├──────────────┬──────────────────────────────────┤
  │              │                                  │
  │ SIDEBAR:     │      MAIN CONTENT:               │
  │              │                                  │
  │ • Controls   │  📈 System Summary               │
  │ • Upload     │     (4 metrics)                  │
  │ • Select     │                                  │
  │ • Modify     │  🔗 Graph | 🔍 Node Analysis    │
  │ • Simulate   │     (Interactive visualization) │
  │              │                                  │
  │ • Buttons    │  💡 Detailed Analysis            │
  │              │     (Explanations + Top 5)      │
  │              │                                  │
  │              │  🎯 Interventions                │
  │              │     (Recommendations + Actions)  │
  │              │                                  │
  │              │  📊 Metrics (Expandable)         │
  │              │                                  │
  └──────────────┴──────────────────────────────────┘


━━━━━━━━━━━━━━━━━━━━━ SYSTEM METRICS ━━━━━━━━━━━━━━━━━

  Average Risk      System State      High-Risk Nodes    Blockchain
  [0-100%]          [State Emoji]     [Count]            [✅/❌]
  
  Example:          Example:          Example:           Example:
  52.3%             🟡 FRAGILE        3 of 8             ✅ Valid


━━━━━━━━━━━━━━━━━━━━━━━ COLORS ━━━━━━━━━━━━━━━━━━━━━

  🟢 GREEN  (Low)      - Risk 0.0-0.3   → Safe
  🟡 YELLOW (Medium)   - Risk 0.3-0.7   → Caution
  🔴 RED    (High)     - Risk 0.7-1.0   → Action Needed


━━━━━━━━━━━━━━━ SIDEBAR CONTROLS ━━━━━━━━━━━━━━━━━

  UPLOAD CSV
    → Load your data (needs: user_id, income, activity, variability)

  RUN ANALYSIS
    → Execute full pipeline (1-2 seconds)

  SELECT NODE
    → Choose node for detailed analysis

  MODIFY NODE
    → Change income (500-10,000)
    → Change activity (0.0-1.0)
    → Click "Apply Changes"

  PROPAGATION STEPS
    → Slider 1-10 steps

  RUN PROPAGATION
    → Simulate risk cascade

  TRIGGER SHOCK
    → Increase node risk by 15%


━━━━━━━━━━━━━━━━ MAIN CONTENT SECTIONS ━━━━━━━━━━━━━━

  SYSTEM SUMMARY
    📈 Overview of network health in 4 metrics
    
  NETWORK VISUALIZATION
    🔗 Interactive graph showing:
       • Nodes (colored by risk, sized by importance)
       • Edges (connections between nodes)
       • Highlight current node

  NODE ANALYSIS
    🔍 Details for selected node:
       • Risk level (color-coded)
       • Risk score and trend
       • Contribution breakdown (chart)
       • Network position (centrality)

  DETAILED ANALYSIS
    💡 Why is it risky? (explanation text)
       Top 5 nodes (table)

  INTERVENTIONS
    🎯 Recommendation:
       • Target node
       • Expected impact (emoji coded)
       • Confidence score
       • Action description
       
    Buttons:
       ✅ Apply Intervention (reduces risk 30%)
       📊 View Alternatives

  DETAILED METRICS
    📊 (Click to expand)
       • All nodes table
       • Risk distribution chart


━━━━━━━━━━━━━━━━ QUICK WORKFLOWS ━━━━━━━━━━━━━━━━━

  HEALTH CHECK (10 sec)
    1. Look at 4 metrics
    2. Check system state color
    3. Read assessment text
    → ✅ Done

  ANALYZE NODE (30 sec)
    1. Select node dropdown
    2. View analysis panel
    3. Read explanation
    → ✅ Done

  INTERVENTION (1 min)
    1. Review recommendation
    2. Check impact/confidence
    3. Click Apply button
    4. See updated results
    → ✅ Done

  SHOCK TEST (2 min)
    1. Select node
    2. Click "Trigger Shock"
    3. Click "Run Propagation"
    4. Observe cascade
    → ✅ Done

  WHAT-IF (5 min)
    1. Adjust sliders
    2. Click "Apply Changes"
    3. Click "Run Analysis"
    4. Compare metrics
    → ✅ Done


━━━━━━━━━━━━━━━━━ INTERACTION TIPS ━━━━━━━━━━━━━━━━

  Graph Controls:
    • Drag to pan
    • Scroll to zoom
    • Hover for info
    • Double-click to reset

  Workflow:
    ✓ Always run analysis first
    ✓ One change at a time
    ✓ Re-run analysis after changes
    ✓ Read explanations (don't just numbers)
    ✓ Check blockchain validity


━━━━━━━━━━━━━━━━━ TROUBLESHOOTING ━━━━━━━━━━━━━━━

  Module Not Found
    → pip install streamlit

  Port Already Used
    → streamlit run ... --server.port 8502

  Graph Not Showing
    → Click "Run Analysis"

  Old Data Showing
    → Click "Run Analysis" again

  CSV won't upload
    → Need columns: user_id, income, activity,
                   transaction_variability

  Changes not applying
    → Click "Apply Changes" THEN "Run Analysis"


━━━━━━━━━━━━━━━━━ KEYBOARD SHORTCUTS ━━━━━━━━━━━━━━

  F5          → Refresh
  r           → Rerun app
  c           → Clear cache


━━━━━━━━━━━━━━━━━ SYSTEM STATES ━━━━━━━━━━━━━━━━━

  🟢 STABLE         (<40%)     → Normal operations
  🟡 FRAGILE        (40-65%)   → Increase monitoring
  🔴 CRITICAL       (>65%)     → Immediate action


━━━━━━━━━━━━━━━━━ IMPACT LEVELS ━━━━━━━━━━━━━━━━━

  🟢 LOW            (<35%)     → Minor effect
  🟡 MEDIUM         (35-65%)   → Moderate effect
  🔴 HIGH           (>65%)     → Significant effect


━━━━━━━━━━━━━━━━ EXAMPLE: QUICK START ━━━━━━━━━━━

  $ streamlit run streamlit_dashboard.py
  
  Browser opens to http://localhost:8501
  
  1️⃣  Look at System Summary metrics
      → See: 52.3% avg risk, FRAGILE state, 3 high-risk nodes
  
  2️⃣  Select node from dropdown ("U4")
      → See: 85% risk, HIGH level, increasing trend
  
  3️⃣  Read explanation
      → "Income is significantly low and activity is very limited..."
  
  4️⃣  Check intervention recommendation
      → "Target: U4, Impact: HIGH, Confidence: 72%"
  
  5️⃣  Click "Apply Intervention"
      → Success: Risk reduces from 85% to 59%
  
  6️⃣  See updated System Summary
      → Now: 48.5% avg risk (improved!)
  
  ✅ DONE in ~2 minutes!


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REMEMBER:
  • All colors are meaningful (green=safe, red=action needed)
  • All explanations are in plain English (no jargon)
  • Every metric has a purpose
  • Every button does something observable
  • System updates in real-time as you interact

For full guide, see: STREAMLIT_DASHBOARD_GUIDE.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

print(reference)
