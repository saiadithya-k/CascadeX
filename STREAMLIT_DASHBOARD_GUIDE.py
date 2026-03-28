"""
STREAMLIT DASHBOARD - USER GUIDE

Professional, interactive dashboard for DCCFE financial risk analysis.
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DCCFE STREAMLIT DASHBOARD - USER GUIDE                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. LAUNCHING THE DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Command:
    streamlit run streamlit_dashboard.py

Expected Output:
    Local URL: http://localhost:8501
    Network URL: http://192.168.x.x:8501
    
Then open http://localhost:8501 in your browser.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. LAYOUT OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIDEBAR (Left Panel)
├── 🎮 Controls
│   ├── Data Management
│   │   └── Upload CSV file
│   ├── Run Analysis button
│   ├── Node Operations
│   │   ├── Select Node dropdown
│   │   └── Modify Node
│   │       ├── Income slider
│   │       └── Activity slider
│   └── Simulation
│       ├── Propagation Steps slider
│       ├── Run Propagation button
│       └── Trigger Shock Event button

MAIN CONTENT (Right Panel)
├── 📈 System Summary
│   ├── Average Risk (metric)
│   ├── System State (metric with emoji)
│   ├── High-Risk Nodes (metric)
│   └── Blockchain Status (metric)
├── 🔗 Network Visualization (left) | 🔍 Node Analysis (right)
│   ├── Interactive graph
│   ├── Centrality metrics
│   └── Contribution breakdown
├── 💡 Detailed Analysis
│   ├── Risk explanation
│   └── Top 5 nodes table
├── 🎯 Intervention Recommendations
│   ├── Target node
│   ├── Expected impact
│   ├── Confidence score
│   └── Action buttons
└── 📊 Detailed Metrics (expandable)
    ├── All nodes table
    └── Risk distribution chart


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. SIDEBAR CONTROLS - DETAILED GUIDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A. DATA MANAGEMENT
──────────────────
Upload CSV:
  - Click "Upload CSV" to load your own data
  - Required columns: user_id, income, activity, transaction_variability
  - Default: System-provided sample data (8 nodes)

Run Analysis:
  - Click "🔄 Run Analysis" to execute full pipeline
  - Computes risks, propagates, and generates recommendations
  - Takes ~1-2 seconds for standard networks

B. NODE OPERATIONS
───────────────────
Select Node:
  - Choose which node to analyze in detail
  - Shows detailed metrics and explanations
  - Can modify income/activity for selected node

Modify Node:
  - Income Slider: Adjust financial income (500-10,000)
  - Activity Slider: Adjust activity level (0.0-1.0)
  - "📝 Apply Changes" button: Save modifications
  - Data updates reflected in next analysis

C. SIMULATION
──────────────
Propagation Steps:
  - Slider: Control how many steps to propagate (1-10)
  - More steps = longer propagation chains
  - Default: 3 steps

Run Propagation:
  - Click to simulate risk propagation through network
  - Shows how risk spreads from node to node
  - Updates network visualization

Trigger Shock Event:
  - Sudden risk increase for selected node
  - Risk increases by 15%
  - Simulates external shock or event
  - Good for scenario testing


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. MAIN CONTENT SECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A. SYSTEM SUMMARY
─────────────────
Shows 4 key metrics:

  Average Risk
    • Overall network risk percentage
    • Green: < 40% (stable)
    • Yellow: 40-65% (fragile)
    • Red: > 65% (critical)

  System State
    • 🟢 STABLE: Low risk, good conditions
    • 🟡 FRAGILE: Moderate risk, monitoring needed
    • 🔴 CRITICAL: High risk, immediate action needed

  High-Risk Nodes
    • Count of nodes with risk > 70%
    • Shows proportion of total nodes
    • Indicator of network health

  Blockchain
    • ✅ Valid: All data integrity checks pass
    • ❌ Invalid: Data integrity issues detected

System Assessment:
    • Text description of current conditions
    • Recommendations based on state
    • Action suggestions


B. NETWORK VISUALIZATION
─────────────────────────
Interactive graph showing:

  Node Visualization:
    • Color: Risk level (green=low, orange=medium, red=high)
    • Size: Importance in network (based on centrality)
    • Labels: Node IDs (U1, U2, etc.)
    • Highlight: Current node is sized larger

  Edges:
    • Connections between nodes
    • Gray lines showing relationships
    • Thicker lines = stronger connections

  Interactivity:
    • Hover over node to see risk %
    • Click/drag to explore
    • Zoom in/out for detail
    • Pan to view different areas

  Dynamic Updates:
    • Graph updates when:
      - Node is selected
      - Propagation runs
      - Modification applied
      - Analysis re-runs


C. NODE ANALYSIS PANEL
───────────────────────
Displays selected node details:

  Risk Level
    • Color-coded (red=high, yellow=medium, green=low)
    • Clear categorization for quick understanding

  Final Risk
    • Percentage score (0-100%)
    • Combined ML and rule-based risks
    • Updated after each operation

  Trend
    • INCREASING: Risk going up
    • DECREASING: Risk going down
    • STABLE: Risk in equilibrium
    • Indicates future direction

  Risk Contributions
    • Bar chart showing factor importance
    • Income: Financial stability
    • Activity: Transaction frequency
    • Variability: Transaction volatility
    • Neighbors: Influence from connected nodes

  Network Position
    • Degree Centrality: How connected (0-1)
    • Betweenness: Bridges between others (0-1)
    • Eigenvector: Influence through connected nodes (0-1)


D. DETAILED ANALYSIS
─────────────────────
"Why is this node at risk?"
    • Natural language explanation
    • No technical jargon
    • Combines multiple factors
    • Business-friendly wording

"Top 5 Highest-Risk Nodes"
    • Table showing top risks
    • Node name, risk %, level, trend
    • Helps identify critical nodes
    • Guidance for interventions


E. INTERVENTION RECOMMENDATIONS
─────────────────────────────────
Target Node
    • Primary node to intervene on
    • Addresses highest systemic risk
    • Interventions cascade to neighbors

Expected Impact
    • 🔴 HIGH: > 65% effectiveness
    • 🟡 MEDIUM: 35-65% effectiveness
    • 🟢 LOW: < 35% effectiveness
    • Based on network position and risk

Confidence
    • Likelihood intervention will succeed
    • 0-100% probability
    • More confidence = more reliable

Recommendation Text
    • Clear explanation of action
    • Why this target is chosen
    • Expected benefits
    • Secondary effects

Action Buttons:
    • "✅ Apply Intervention"
      - Reduces target node risk by 30%
      - Updates visualization
      - Shows success confirmation
      
    • "📊 View Alternative Options"
      - Shows other possible interventions
      - Secondary targets
      - Comparative analysis


F. DETAILED METRICS (Expandable)
──────────────────────────────────
Click "📊 Detailed Metrics" to expand:

  All Nodes Table
    • Complete list of all nodes
    • Risk percentage for each
    • Risk level category
    • Scroll to see all entries
    • Sort/filter as needed

  Risk Distribution
    • Bar chart of risk categories
    • How many nodes in each level
    • Visual overview of network risk
    • Identify concentration


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. COMMON WORKFLOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORKFLOW 1: QUICK HEALTH CHECK
────────────────────────────────
1. Open dashboard
2. Look at 4 metrics in System Summary
3. Check system state (color coded)
4. Read assessment text
5. Time: < 10 seconds

WORKFLOW 2: DETAILED NODE ANALYSIS
────────────────────────────────────
1. Select node from dropdown (left)
2. View node analysis panel
3. See contributions breakdown
4. Read explanation of risk
5. Check centrality metrics
6. Time: ~ 30 seconds

WORKFLOW 3: INTERVENTION SCENARIO
───────────────────────────────────
1. Review current system state
2. Read intervention recommendation
3. Check expected impact
4. Click "✅ Apply Intervention"
5. See updated visualization
6. Observe new metrics
7. Verify improvement
8. Time: ~ 1 minute

WORKFLOW 4: SHOCK EVENT SIMULATION
────────────────────────────────────
1. Select node from dropdown
2. Set propagation steps (e.g., 3-5)
3. Click "⚡ Trigger Shock Event"
4. Click "🌊 Run Propagation"
5. Watch cascade through network
6. Observe impact on metrics
7. Evaluate system resilience
8. Time: ~ 2 minutes

WORKFLOW 5: WHAT-IF ANALYSIS
──────────────────────────────
1. Select node from dropdown
2. Adjust income slider
3. Adjust activity slider
4. Click "📝 Apply Changes"
5. Click "🔄 Run Analysis"
6. Compare new metrics
7. Assess impact of changes
8. Iterate with different values
9. Time: ~ 5 minutes

WORKFLOW 6: CUSTOM DATA ANALYSIS
──────────────────────────────────
1. Prepare CSV with columns:
   - user_id
   - income
   - activity
   - transaction_variability
2. Click "Upload CSV" in sidebar
3. Click "🔄 Run Analysis"
4. Explore results
5. Use same workflows as above
6. Time: ~ 2-3 minutes


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. COLOR SCHEME REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk Levels:
  🟢 GREEN (#2ecc71)   → LOW RISK (0.0 - 0.3)
  🟡 ORANGE (#f39c12)  → MEDIUM RISK (0.3 - 0.7)
  🔴 RED (#e74c3c)     → HIGH RISK (0.7 - 1.0)

System States:
  🟢 STABLE   → Safe conditions, minimal intervention needed
  🟡 FRAGILE  → Caution required, monitoring important
  🔴 CRITICAL → Action required, intervention urgent

Impact Levels:
  🟢 LOW      → Minimal impact (< 35% effectiveness)
  🟡 MEDIUM   → Moderate impact (35-65% effectiveness)
  🔴 HIGH     → Significant impact (> 65% effectiveness)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7. TIPS & TRICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
  • Run analysis before making changes
  • Use sliders for gradual adjustments
  • Check explanations to understand "why"
  • Verify blockchain status for data integrity
  • Use propagation to see cascade effects
  • Test interventions with shock events
  • Expand detailed metrics for full picture
  • Monitor system state transitions

❌ DON'T:
  • Apply multiple changes without re-analyzing
  • Ignore low confidence interventions
  • Trust results without understanding explanations
  • Forget to verify blockchain validity
  • Use extreme slider values without reason
  • Run too many propagation steps at once
  • Skip reviewing alternative options

📊 PERFORMANCE:
  • Single node analysis: < 500ms
  • Full network analysis: 1-2 seconds
  • Propagation simulation: 2-3 seconds
  • Shock events: < 500ms
  • Graph updates: < 1 second

🔄 AUTO-REFRESH:
  • Dashboard auto-refreshes on interaction
  • Changes visible immediately
  • No manual refresh needed
  • Streamlit manages state automatically


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8. TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: "ModuleNotFoundError: No module named 'streamlit'"
Solution: pip install streamlit

Problem: "Port 8501 already in use"
Solution: streamlit run streamlit_dashboard.py --server.port 8502

Problem: Graph not showing
Solution: Run "🔄 Run Analysis" button in sidebar

Problem: Metrics showing old data
Solution: Click "🔄 Run Analysis" to refresh

Problem: Slow performance
Solution: Reduce propagation steps, or use local network only

Problem: CSV upload fails
Solution: Ensure columns: user_id, income, activity, transaction_variability

Problem: Changes not applying
Solution: Click "📝 Apply Changes" then "🔄 Run Analysis"

Problem: Intervention not working
Solution: Verify blockchain is valid, re-run analysis

Problem: Need to reset
Solution: Refresh browser (F5) or restart streamlit


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
9. KEYBOARD SHORTCUTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Browser Shortcuts:
  F5                → Refresh page
  Ctrl+Shift+J      → Open developer console
  Ctrl+Shift+Del    → Clear browser cache

Streamlit Shortcuts:
  r                 → Rerun app
  c                 → Clear cache
  s                 → Settings

Graph Interaction:
  Left-drag         → Pan view
  Scroll            → Zoom in/out
  Hover             → Show node info
  Double-click      → Reset view


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10. BEST PRACTICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANALYSIS:
  ✓ Always start with System Summary
  ✓ Check system state before decisions
  ✓ Read explanations, don't just look at numbers
  ✓ Verify blockchain validity
  ✓ Review top 5 at-risk nodes

MODIFICATIONS:
  ✓ Make one change at a time
  ✓ Apply changes and re-run analysis
  ✓ Document what you changed and why
  ✓ Compare before/after metrics
  ✓ Use small adjustments for precision

INTERVENTIONS:
  ✓ Check confidence score first
  ✓ Review expected impact
  ✓ Understand the recommendation reasoning
  ✓ Test with shock events first
  ✓ Apply interventions strategically
  ✓ Verify results after applying

MONITORING:
  ✓ Check system state regularly
  ✓ Watch for state transitions
  ✓ Monitor high-risk nodes
  ✓ Track intervention effectiveness
  ✓ Document changes over time

REPORTING:
  ✓ Screenshot system summary
  ✓ Export detailed metrics table
  ✓ Document interventions applied
  ✓ Show before/after comparisons
  ✓ Include explanations and reasoning


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
11. ADVANCED FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO TESTING:
  1. Select node
  2. Adjust parameters dramatically
  3. Apply changes
  4. Run analysis
  5. Trigger shock event
  6. Run propagation
  7. Observe cascade effects
  8. Evaluate system resilience

COMPARATIVE ANALYSIS:
  1. Take initial metrics screenshot
  2. Apply intervention
  3. Re-run analysis
  4. Take new metrics screenshot
  5. Compare metrics side-by-side
  6. Measure improvement
  7. Calculate effectiveness

INTERVENTION RANKING:
  1. Note current system state
  2. Apply intervention
  3. Record new metrics
  4. Revert (upload original data)
  5. Apply alternative intervention
  6. Record metrics
  7. Compare effectiveness
  8. Choose best option

CASCADE ANALYSIS:
  1. Select high-risk node
  2. Trigger shock event
  3. Set propagation steps to 10
  4. Run propagation
  5. Watch cascade spread
  6. Count affected nodes
  7. Identify cascade sources
  8. Plan defensive interventions


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
12. QUICK REFERENCE - SYSTEM STATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE     │ AVG RISK │ INDICATOR │ ACTION                    │ URGENCY       │
├─────────────────────────────────────────────────────────────────────────────┤
│ STABLE    │ < 40%    │ 🟢 Green  │ Monitor normally          │ Low           │
│ FRAGILE   │ 40-65%   │ 🟡 Yellow │ Increase monitoring       │ Medium        │
│ CRITICAL  │ > 65%    │ 🔴 Red    │ Immediate intervention    │ High/Urgent   │
└─────────────────────────────────────────────────────────────────────────────┘

RECOMMENDED ACTIONS BY STATE:
  STABLE
    • Review system periodically
    • Monitor top-risk nodes
    • Plan long-term improvements
    • Continue normal operations

  FRAGILE
    • Increase check frequency
    • Prepare interventions
    • Monitor propagation paths
    • Watch for escalation

  CRITICAL
    • Execute interventions immediately
    • Check cascade effects
    • Consider multiple actions
    • Monitor 24/7 if possible


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The DCCFE Streamlit Dashboard provides:

✅ COMPLETE VISIBILITY
   • System-level overview
   • Node-level details
   • Time-stamped analysis
   • Historical context

✅ INTERACTIVE CONTROLS
   • Modify parameters
   • Run simulations
   • Trigger events
   • Apply interventions

✅ PROFESSIONAL PRESENTATION
   • Color-coded indicators
   • Clear metrics
   • Beautiful visualizations
   • Understandable explanations

✅ POWERFUL ANALYSIS
   • Risk classification
   • Cascade detection
   • Intervention planning
   • Trend analysis

Ready to launch? Run:
    streamlit run streamlit_dashboard.py

Then open http://localhost:8501 in your browser!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
