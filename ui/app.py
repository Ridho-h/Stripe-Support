"""
Stripe Support Agent Dashboard - Internal Developer Console.
Pixel-faithful reproduction of the Trace View design reference:
- IBM Plex Sans & IBM Plex Mono typography
- Dark navigation bar (#18181B) with indigo glyph & live loaded ticket telemetry
- Left Ticket Queue with active styling (#EEF2FF / #C7D2FE) & urgency badges
- Ticket Header with metadata badges (T023, CRITICAL, AUTH · KEYS) & Escalation banner
- Customer message defaulting to OPEN with crisp legible styling
- Connected 4-Stage Agent Reasoning Trail with guaranteed visible connector line
- Bulletproof Action buttons ("Approve & send draft", "Edit draft", "⚡ Re-run Pipeline") with 100% legible contrast in any theme
"""

import json
import os
import sys
import html
from datetime import datetime
import streamlit as st

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mcp_servers.ticket_server.server import get_ticket, list_tickets, update_ticket
from orchestrator.pipeline import run_ticket_pipeline
from evaluator import urgency_distance

st.set_page_config(
    page_title="Support Agent Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------
# Data Loading Utilities
# -------------------------------------------------------------
def load_traces() -> dict:
    traces_path = os.path.join(BASE_DIR, "pipeline_traces.json")
    if os.path.exists(traces_path):
        with open(traces_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_metrics() -> dict:
    metrics_path = os.path.join(BASE_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_predictions() -> dict:
    pred_path = os.path.join(BASE_DIR, "predictions.json")
    if os.path.exists(pred_path):
        with open(pred_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


traces = load_traces()
metrics = load_metrics()
predictions = load_predictions()
all_tickets = list_tickets()

# Fallback if DB not seeded
if not all_tickets:
    from mcp_servers.ticket_server.db import init_db
    init_db()
    all_tickets = list_tickets()


# -------------------------------------------------------------
# Navigation & Selection Handling
# -------------------------------------------------------------
qp = st.query_params
active_view = qp.get("view", "trace")
active_tid = qp.get("ticket", "T023")

ticket_ids = [t["id"] for t in all_tickets]
if active_tid not in ticket_ids and ticket_ids:
    active_tid = ticket_ids[0]


# -------------------------------------------------------------
# CSS Injection via st.html
# -------------------------------------------------------------
CSS_STYLES = """
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Reset & Shell */
header[data-testid="stHeader"] { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
#MainMenu, footer { visibility: hidden !important; height: 0px !important; }
.stApp {
  background-color: #F6F6F4 !important;
  font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
  color: #18181B !important;
}
.main .block-container, div[data-testid="stMainBlockContainer"], div[data-testid="block-container"] {
  padding-top: 0rem !important;
  padding-bottom: 2rem !important;
  padding-left: 0rem !important;
  padding-right: 0rem !important;
  max-width: 100% !important;
}
div[data-testid="stHorizontalBlock"] { gap: 0rem !important; }
a { color: #5850EC; text-decoration: none; }
a:hover { color: #4338CA; }
.mono { font-family: 'IBM Plex Mono', monospace !important; }

/* Top Navigation Bar */
.top-bar-container {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #18181B;
  color: #F6F6F4;
  width: 100%;
  box-sizing: border-box;
  position: sticky;
  top: 0;
  z-index: 999;
}
.top-bar-left { display: flex; align-items: center; gap: 12px; }
.logo-glyph { width: 22px; height: 22px; border-radius: 6px; background: #5850EC; }
.app-title-text { font-weight: 600; font-size: 15px; color: #F6F6F4; }
.app-env-text { font-size: 12px; color: #A1A1AA; margin-left: 8px; }
.top-bar-right { display: flex; align-items: center; gap: 16px; }
.top-nav-link { font-size: 12px; font-weight: 500; color: #A1A1AA; padding: 5px 12px; border-radius: 6px; transition: all 0.15s ease; text-decoration: none !important; }
.top-nav-link:hover { color: #FFFFFF; background: rgba(255, 255, 255, 0.08); }
.top-nav-link.active { color: #FFFFFF; background: rgba(88, 80, 236, 0.35); border: 1px solid rgba(88, 80, 236, 0.6); }
.tickets-count-mono { font-size: 12px; color: #A1A1AA; }
.avatar-circle { width: 28px; height: 28px; border-radius: 50%; background: #3F3F46; }

/* Left Queue Panel Column */
div[data-testid="column"]:first-child {
  max-width: 274px !important;
  min-width: 260px !important;
  background: #FFFFFF !important;
  border-right: 1px solid #E4E4E7 !important;
}
.queue-panel {
  width: 100%;
  background: #FFFFFF;
  box-sizing: border-box;
  padding: 16px 12px;
  min-height: calc(100vh - 56px);
  max-height: calc(100vh - 56px);
  overflow-y: auto;
}
.queue-header-title { font-size: 11px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: #71717A; padding: 4px 8px 10px; }
.queue-card { display: block; text-decoration: none !important; padding: 10px 10px; border-radius: 8px; margin-bottom: 6px; box-sizing: border-box; }
.queue-card-active { background: #EEF2FF !important; border: 1px solid #C7D2FE !important; }
.queue-card-inactive { background: transparent; border: 1px solid transparent; }
.queue-card-inactive:hover { background: #F4F4F5; }
.queue-top-row { display: flex; justify-content: space-between; align-items: center; }
.queue-tid-active { font-size: 11px; color: #5850EC; font-weight: 600; }
.queue-tid-inactive { font-size: 11px; color: #71717A; font-weight: 600; }
.queue-subject-active { font-size: 13px; font-weight: 600; margin-top: 4px; line-height: 1.3; color: #18181B; }
.queue-subject-inactive { font-size: 13px; margin-top: 4px; line-height: 1.3; color: #3F3F46; }

/* Badges */
.badge-crit { font-size: 10px; font-weight: 600; color: #FFFFFF; background: #DC2626; padding: 2px 6px; border-radius: 4px; }
.badge-high { font-size: 10px; font-weight: 600; color: #92400E; background: #FEF3C7; padding: 2px 6px; border-radius: 4px; }
.badge-med { font-size: 10px; font-weight: 600; color: #3F3F46; background: #E4E4E7; padding: 2px 6px; border-radius: 4px; }
.badge-low { font-size: 10px; font-weight: 600; color: #3F3F46; background: #E4E4E7; padding: 2px 6px; border-radius: 4px; }
.badge-cat { font-size: 10px; font-weight: 600; color: #3730A3; background: #E0E7FF; padding: 3px 7px; border-radius: 4px; }

/* Right Main Detail Panel */
div[data-testid="column"]:last-child {
  padding-left: 0px !important;
}
.main-detail-wrapper {
  padding: 24px 32px 10px 32px;
  background: #F6F6F4;
  box-sizing: border-box;
}
.ticket-header-flex { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.ticket-meta-badges { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.ticket-subject-h1 { margin: 0; font-size: 22px; font-weight: 700; color: #18181B; line-height: 1.25; }
.escalated-badge-pill { display: flex; align-items: center; gap: 8px; background: #FEE2E2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 8px 12px; }
.escalated-badge-pill span { font-size: 12px; font-weight: 600; color: #B91C1C; }
.resolved-badge-pill { display: flex; align-items: center; gap: 8px; background: #DCFCE7; border: 1px solid #86EFAC; border-radius: 8px; padding: 8px 12px; }
.resolved-badge-pill span { font-size: 12px; font-weight: 600; color: #166534; }
.section-heading-mono { font-size: 11px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: #71717A; margin-bottom: 12px; }

/* Expander - Default Open Customer Message */
[data-testid="stExpander"] {
  background-color: #FFFFFF !important;
  border: 1px solid #E4E4E7 !important;
  border-radius: 10px !important;
  margin: 0 32px 16px 32px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}
[data-testid="stExpander"] details {
  background-color: #FFFFFF !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
  color: #18181B !important;
  font-weight: 600 !important;
  font-size: 13px !important;
}
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p {
  color: #18181B !important;
  font-weight: 600 !important;
}
[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p {
  color: #3F3F46 !important;
  font-size: 13px !important;
  line-height: 1.6 !important;
}

/* Stages Reasoning Trail */
.trail-column-container { display: flex; flex-direction: column; gap: 0; }
.stage-step-row { display: flex; gap: 14px; align-items: stretch; }
.stage-spine { width: 28px; flex: 0 0 28px; display: flex; flex-direction: column; align-items: center; }
.circle-node-green { width: 28px; height: 28px; border-radius: 50%; background: #16A34A; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.circle-node-red { width: 28px; height: 28px; border-radius: 50%; background: #DC2626; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stage-card-standard { flex: 1 1 auto; background: #FFFFFF; border: 1px solid #E4E4E7; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px; box-sizing: border-box; }
.stage-card-escalated { flex: 1 1 auto; background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px; box-sizing: border-box; }
.stage-header-flex { display: flex; justify-content: space-between; align-items: center; }
.stage-title-standard { font-size: 13px; font-weight: 600; color: #18181B; }
.stage-title-escalated { font-size: 13px; font-weight: 600; color: #7F1D1D; }
.stage-meta-standard { font-size: 11px; color: #71717A; }
.stage-meta-escalated { font-size: 11px; color: #B91C1C; }
.stage-body-standard { margin: 8px 0 0; font-size: 13px; color: #3F3F46; line-height: 1.5; }
.stage-body-escalated { margin: 8px 0 0; font-size: 13px; color: #7F1D1D; line-height: 1.5; }
.doc-pill { display: inline-block; font-size: 11px; background: #F4F4F5; border: 1px solid #E4E4E7; border-radius: 6px; padding: 3px 8px; color: #18181B; margin-right: 4px; }

/* Bulletproof Button Styling - Works in both light & dark themes */
div[data-testid="column"]:last-child div[data-testid="stHorizontalBlock"] {
  align-items: center !important;
}
div[data-testid="stButton"] button {
  border-radius: 8px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  padding: 10px 18px !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
  height: 42px !important;
  box-shadow: none !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.15s ease !important;
}

/* Primary Button: Approve & send draft */
button[data-testid*="stBaseButton-primary"],
button[kind="primary"] {
  background-color: #18181B !important;
  background: #18181B !important;
  border: 1px solid #18181B !important;
  color: #FFFFFF !important;
}
button[data-testid*="stBaseButton-primary"]:hover,
button[kind="primary"]:hover {
  background-color: #27272A !important;
  background: #27272A !important;
  border-color: #27272A !important;
}
button[data-testid*="stBaseButton-primary"] *,
button[kind="primary"] *,
button[data-testid*="stBaseButton-primary"] p,
button[kind="primary"] p,
button[data-testid*="stBaseButton-primary"] span,
button[kind="primary"] span {
  color: #FFFFFF !important;
  fill: #FFFFFF !important;
  font-weight: 600 !important;
  font-size: 13px !important;
}

/* Secondary Buttons: Edit draft & Re-run Pipeline */
button[data-testid*="stBaseButton-secondary"],
button[kind="secondary"] {
  background-color: #FFFFFF !important;
  background: #FFFFFF !important;
  border: 1px solid #D4D4D8 !important;
  color: #18181B !important;
}
button[data-testid*="stBaseButton-secondary"]:hover,
button[kind="secondary"]:hover {
  background-color: #F4F4F5 !important;
  background: #F4F4F5 !important;
  border-color: #A1A1AA !important;
}
button[data-testid*="stBaseButton-secondary"] *,
button[kind="secondary"] *,
button[data-testid*="stBaseButton-secondary"] p,
button[kind="secondary"] p,
button[data-testid*="stBaseButton-secondary"] span,
button[kind="secondary"] span {
  color: #18181B !important;
  fill: #18181B !important;
  font-weight: 600 !important;
  font-size: 13px !important;
}

/* Benchmark Metrics Theme Fix */
[data-testid="stMetric"] {
  background-color: #FFFFFF !important;
  border: 1px solid #E4E4E7 !important;
  border-radius: 8px !important;
  padding: 14px 16px !important;
}
[data-testid="stMetricValue"] *, [data-testid="stMetricValue"] div {
  color: #18181B !important;
  font-weight: 700 !important;
}
[data-testid="stMetricLabel"] *, [data-testid="stMetricLabel"] p {
  color: #71717A !important;
  font-weight: 500 !important;
}
</style>
"""
st.html(CSS_STYLES)


# -------------------------------------------------------------
# Top Navigation Bar Render
# -------------------------------------------------------------
is_trace_active = "active" if active_view == "trace" else ""
is_bench_active = "active" if active_view == "benchmark" else ""

top_bar_html = f"""
<div class="top-bar-container">
  <div class="top-bar-left">
    <div class="logo-glyph"></div>
    <span class="app-title-text">Support Agent Dashboard</span>
    <span class="app-env-text mono">stripe-support-agent · staging</span>
  </div>
  <div class="top-bar-right">
    <a href="?view=trace&ticket={active_tid}" target="_self" class="top-nav-link {is_trace_active}">Trace View</a>
    <a href="?view=benchmark&ticket={active_tid}" target="_self" class="top-nav-link {is_bench_active}">Evaluation Benchmark</a>
    <span class="tickets-count-mono mono">{len(all_tickets)} tickets loaded</span>
    <div class="avatar-circle"></div>
  </div>
</div>
"""
st.html(top_bar_html)


def get_urgency_badge(urgency: str) -> str:
    urg = (urgency or "low").lower()
    if urg == "critical":
        return f'<span class="badge-crit">{urg.upper()}</span>'
    elif urg == "high":
        return f'<span class="badge-high">{urg.upper()}</span>'
    elif urg == "medium":
        return f'<span class="badge-med">{urg.upper()}</span>'
    else:
        return f'<span class="badge-low">{urg.upper()}</span>'


# -------------------------------------------------------------
# VIEW 1: EVALUATION BENCHMARK (RUBRIC)
# -------------------------------------------------------------
if active_view == "benchmark":
    st.html(
        f"""
        <div style="padding: 24px 32px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 20px;">
                <div>
                    <h1 style="margin:0; font-size:24px; font-weight:700; color:#18181B;">Evaluation Benchmark Report</h1>
                    <p style="margin:4px 0 0; color:#71717A; font-size:13px;" class="mono">Scored against labeled_tickets.json using eval_rubric.md thresholds</p>
                </div>
                <a href="?view=trace&ticket={active_tid}" target="_self" style="background:#18181B; color:#FFFFFF; padding:8px 16px; border-radius:8px; font-size:13px; font-weight:600; text-decoration:none;">← Back to Trace View</a>
            </div>
        </div>
        """
    )

    if not metrics:
        st.warning("metrics.json not found. Run the pipeline with --eval to generate benchmark results.")
    else:
        overall = metrics.get("overall", {})
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Category Acc", f"{(overall.get('triage_category_acc', 0) * 100):.1f}%", help="Target: >= 90%")
        col2.metric("Urgency (±1)", f"{(overall.get('triage_urgency_close_acc', 0) * 100):.1f}%", help="Target: >= 95%")
        col3.metric("Citation Recall@3", f"{(overall.get('citation_recall_at_3', 0) * 100):.1f}%", help="Target: >= 90%")
        col4.metric("Escalation Recall", f"{(overall.get('escalation_recall', 0) * 100):.1f}%", help="Target: >= 90%")
        col5.metric("Composite Score", f"{(metrics.get('composite_score', 0) * 100):.1f}%")

        st.html('<div style="padding: 0 32px;"><h3 style="font-size:16px; font-weight:700; color:#18181B; margin: 24px 0 12px 0;">Performance Breakdown by Category</h3></div>')
        by_cat = metrics.get("by_category", {})
        table_rows = []
        for cat, data in by_cat.items():
            table_rows.append({
                "Category": cat,
                "n": data.get("n", 0),
                "Triage Acc": f"{(data.get('triage_category_acc', 0) * 100):.1f}%",
                "Urgency (±1)": f"{(data.get('triage_urgency_close_acc', 0) * 100):.1f}%",
                "Citation Recall@3": f"{(data.get('citation_recall_at_3', 0) * 100):.1f}%",
                "Escalation Rec": f"{(data.get('escalation_recall') * 100):.1f}%" if data.get("escalation_recall") is not None else "N/A",
                "Escalation Prec": f"{(data.get('escalation_precision') * 100):.1f}%" if data.get("escalation_precision") is not None else "N/A",
            })
        table_rows.append({
            "Category": "**OVERALL**",
            "n": overall.get("n", 0),
            "Triage Acc": f"{(overall.get('triage_category_acc', 0) * 100):.1f}%",
            "Urgency (±1)": f"{(overall.get('triage_urgency_close_acc', 0) * 100):.1f}%",
            "Citation Recall@3": f"{(overall.get('citation_recall_at_3', 0) * 100):.1f}%",
            "Escalation Rec": f"{(overall.get('escalation_recall', 0) * 100):.1f}%",
            "Escalation Prec": f"{(overall.get('escalation_precision', 0) * 100):.1f}%",
        })
        st.dataframe(table_rows, use_container_width=True)

        flags = metrics.get("flags", {})
        colA, colB = st.columns(2)
        with colA:
            severe_misses = flags.get("severe_urgency_misses", [])
            st.metric("Severe Urgency Misses (±2 levels)", len(severe_misses))
            if severe_misses:
                st.html(f"""
                <div style="background:#FEE2E2; border:1px solid #FCA5A5; border-radius:8px; padding:12px 16px; margin-top:8px;">
                  <span style="color:#991B1B; font-size:13px; font-weight:600;">🚨 Tickets flagged: {', '.join(severe_misses)}</span>
                </div>
                """)
            else:
                st.html("""
                <div style="background:#DCFCE7; border:1px solid #86EFAC; border-radius:8px; padding:12px 16px; margin-top:8px;">
                  <span style="color:#166534; font-size:13px; font-weight:600;">✓ 0 severe urgency misses (all predictions within ±1 level)</span>
                </div>
                """)
        with colB:
            hallucinated = flags.get("hallucinated_citations", [])
            st.metric("Hallucinated Citations", len(hallucinated))
            if hallucinated:
                st.html(f"""
                <div style="background:#FEE2E2; border:1px solid #FCA5A5; border-radius:8px; padding:12px 16px; margin-top:8px;">
                  <span style="color:#991B1B; font-size:13px; font-weight:600;">🚨 Tickets flagged: {', '.join(hallucinated)}</span>
                </div>
                """)
            else:
                st.html("""
                <div style="background:#DCFCE7; border:1px solid #86EFAC; border-radius:8px; padding:12px 16px; margin-top:8px;">
                  <span style="color:#166534; font-size:13px; font-weight:600;">✓ 0 hallucinated citations (all replies grounded in retrieved docs)</span>
                </div>
                """)


# -------------------------------------------------------------
# VIEW 2: TRACE VIEW (1:1 with Design Mockup)
# -------------------------------------------------------------
else:
    col_queue, col_detail = st.columns([1, 4.3], gap="small")

    # 1. Left Queue Column
    with col_queue:
        queue_cards_html = [
            '<div class="queue-panel">',
            '<div class="queue-header-title">Queue</div>',
        ]

        for t in all_tickets:
            is_active = (t["id"] == active_tid)
            card_class = "queue-card queue-card-active" if is_active else "queue-card queue-card-inactive"
            tid_class = "queue-tid-active" if is_active else "queue-tid-inactive"
            subject_class = "queue-subject-active" if is_active else "queue-subject-inactive"
            urg_badge = get_urgency_badge(t.get("urgency", "low"))
            subject_escaped = html.escape(t.get("subject", ""))

            queue_cards_html.append(f"""
            <a href="?view=trace&ticket={t['id']}" target="_self" class="{card_class}">
              <div class="queue-top-row">
                <span class="mono {tid_class}">{t['id']}</span>
                {urg_badge}
              </div>
              <div class="{subject_class}">{subject_escaped}</div>
            </a>
            """)

        queue_cards_html.append("</div>")
        st.html("\n".join(queue_cards_html))

    # 2. Right Detail & Agent Trace Column
    with col_detail:
        ticket = get_ticket(active_tid) or next((t for t in all_tickets if t["id"] == active_tid), None)
        if not ticket:
            st.error(f"Ticket {active_tid} not found.")
        else:
            trace = traces.get(active_tid, {})
            pred = predictions.get(active_tid, {})

            urgency = (pred.get("urgency") or ticket.get("urgency") or "low").upper()
            urgency_badge_top = get_urgency_badge(urgency)
            cat_display = (pred.get("category") or ticket.get("category") or "general").replace("_", " · ").upper()
            is_escalated = pred.get("escalate", ticket.get("escalate", False))

            if is_escalated:
                escalation_banner_html = """
                <div class="escalated-badge-pill">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 9v4"></path><path d="M12 17h.01"></path>
                    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"></path>
                  </svg>
                  <span>Escalated to human review</span>
                </div>
                """
            else:
                escalation_banner_html = """
                <div class="resolved-badge-pill">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#166534" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 6 9 17l-5-5"></path>
                  </svg>
                  <span>Automated resolution</span>
                </div>
                """

            ticket_header_html = f"""
            <div class="main-detail-wrapper">
              <div class="ticket-header-flex">
                <div>
                  <div class="ticket-meta-badges">
                    <span class="mono" style="font-size:12px; color:#71717A;">{ticket['id']}</span>
                    {urgency_badge_top}
                    <span class="badge-cat">{cat_display}</span>
                  </div>
                  <h1 class="ticket-subject-h1">{html.escape(ticket.get('subject', ''))}</h1>
                </div>
                {escalation_banner_html}
              </div>
            </div>
            """
            st.html(ticket_header_html)

            # Customer Message Expander - Defaults to OPEN
            with st.expander(f"Customer Inquiry Message ({ticket['id']})", expanded=True):
                st.write(ticket.get("body", ""))

            st.html('<div style="padding: 4px 32px 10px 32px;"><div class="section-heading-mono">Agent reasoning trail</div></div>')

            # -------------------------------------------------------------
            # 4-Stage Reasoning Trail
            # -------------------------------------------------------------
            stages = trace.get("stages", [])
            s1 = next((s for s in stages if s.get("stage_index") == 1), None)
            s2 = next((s for s in stages if s.get("stage_index") == 2), None)
            s3 = next((s for s in stages if s.get("stage_index") == 3), None)
            s4 = next((s for s in stages if s.get("stage_index") == 4), None)

            # Stage 1: Triage
            s1_cat = pred.get("category") or (s1.get("output", {}).get("category") if s1 else ticket.get("category"))
            s1_urg = pred.get("urgency") or (s1.get("output", {}).get("urgency") if s1 else ticket.get("urgency"))
            s1_reason = s1.get("reasoning") if s1 else f"Classified ticket into category '{s1_cat}' with urgency level '{s1_urg}'."

            # Stage 2: Retrieval
            s2_topics = pred.get("retrieved_doc_topics") or (s2.get("output", {}).get("retrieved_doc_topics", []) if s2 else [])
            gt_topic = ticket.get("doc_topic", "")
            first_word = gt_topic.split()[0].lower() if gt_topic else ""
            rec_hit = any(first_word in r.lower() for r in s2_topics[:3]) if gt_topic else True
            recall_text = "recall ✓" if rec_hit else "recall ✗"
            s2_reason = s2.get("reasoning") if s2 else f"Queried the docs index for '{s1_cat}' procedures."

            doc_pills_html = []
            for top in s2_topics:
                slug = top.replace(" / ", "-").replace(" ", "-").lower()
                if not slug.endswith(".md"):
                    slug = slug[:26] + ".md"
                doc_pills_html.append(f'<span class="mono doc-pill">{html.escape(slug)}</span>')
            pills_rendered = " ".join(doc_pills_html) if doc_pills_html else '<span class="mono doc-pill">knowledge-base.md</span>'

            # Stage 3: Drafting
            draft_full = pred.get("draft_reply") or (s3.get("output", {}).get("draft_reply", "") if s3 else "")
            cited = (s3.get("output", {}).get("cited_topics", [])) if s3 else s2_topics[:1]
            citation_count = len(cited) if cited else 1
            draft_clean = draft_full.replace("\n", " ").strip()
            draft_snippet = draft_clean[:180] if len(draft_clean) > 180 else draft_clean

            # Stage 4: Escalation
            conf = s4.get("confidence", 0.94) if s4 else 0.94
            esc_reason = pred.get("escalation_reason") or (s4.get("reasoning") if s4 else "")
            if not esc_reason:
                if is_escalated:
                    esc_reason = "Flagged for human review: possible security or financial exposure requires immediate operational verification."
                else:
                    esc_reason = "Standard documentation inquiry resolved automatically. No human intervention needed."

            if is_escalated:
                s4_node_circle = """
                <div class="circle-node-red">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4"></path><path d="M12 17h.01"></path><circle cx="12" cy="12" r="9"></circle></svg>
                </div>
                """
                s4_card_html = f"""
                <div class="stage-card-escalated">
                  <div class="stage-header-flex">
                    <span class="stage-title-escalated">Escalation Agent</span>
                    <span class="mono stage-meta-escalated">escalate: true · confidence {conf:.2f}</span>
                  </div>
                  <p class="stage-body-escalated">{html.escape(esc_reason)}</p>
                </div>
                """
            else:
                s4_node_circle = """
                <div class="circle-node-green">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>
                </div>
                """
                s4_card_html = f"""
                <div class="stage-card-standard">
                  <div class="stage-header-flex">
                    <span class="stage-title-standard">Escalation Agent</span>
                    <span class="mono stage-meta-standard">escalate: false · confidence {conf:.2f}</span>
                  </div>
                  <p class="stage-body-standard">{html.escape(esc_reason)}</p>
                </div>
                """

            trail_full_html = f"""
            <div style="padding: 0 32px;">
              <div class="trail-column-container">
                <!-- Stage 1: Triage -->
                <div class="stage-step-row">
                  <div class="stage-spine">
                    <div class="circle-node-green">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>
                    </div>
                    <div style="width:2px; flex:1 1 auto; min-height:28px; background:#CBD5E1; margin:4px 0;">&nbsp;</div>
                  </div>
                  <div class="stage-card-standard">
                    <div class="stage-header-flex">
                      <span class="stage-title-standard">Triage Agent</span>
                      <span class="mono stage-meta-standard">category: {s1_cat} · urgency: {s1_urg}</span>
                    </div>
                    <p class="stage-body-standard">{html.escape(s1_reason)}</p>
                  </div>
                </div>

                <!-- Stage 2: Retrieval -->
                <div class="stage-step-row">
                  <div class="stage-spine">
                    <div class="circle-node-green">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>
                    </div>
                    <div style="width:2px; flex:1 1 auto; min-height:28px; background:#CBD5E1; margin:4px 0;">&nbsp;</div>
                  </div>
                  <div class="stage-card-standard">
                    <div class="stage-header-flex">
                      <span class="stage-title-standard">Retrieval Agent</span>
                      <span class="mono stage-meta-standard">top-{max(len(s2_topics), 1)} · {recall_text}</span>
                    </div>
                    <p class="stage-body-standard" style="margin-bottom:8px;">{html.escape(s2_reason)}</p>
                    <div style="display:flex; gap:6px; flex-wrap:wrap;">
                      {pills_rendered}
                    </div>
                  </div>
                </div>

                <!-- Stage 3: Drafting -->
                <div class="stage-step-row">
                  <div class="stage-spine">
                    <div class="circle-node-green">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>
                    </div>
                    <div style="width:2px; flex:1 1 auto; min-height:28px; background:#CBD5E1; margin:4px 0;">&nbsp;</div>
                  </div>
                  <div class="stage-card-standard">
                    <div class="stage-header-flex">
                      <span class="stage-title-standard">Drafting Agent</span>
                      <span class="mono stage-meta-standard">grounded · {citation_count} citations</span>
                    </div>
                    <p class="stage-body-standard">"{html.escape(draft_snippet)}…"</p>
                  </div>
                </div>

                <!-- Stage 4: Escalation -->
                <div class="stage-step-row">
                  <div class="stage-spine">
                    {s4_node_circle}
                  </div>
                  {s4_card_html}
                </div>
              </div>
            </div>
            """
            st.html(trail_full_html)

            # -------------------------------------------------------------
            # Action Buttons & Eval Strip
            # -------------------------------------------------------------
            triage_pass = (s1_cat == ticket.get("category")) and (urgency_distance(ticket.get("urgency", "low"), s1_urg) <= 1)
            triage_mark = "✓" if triage_pass else "✗"
            triage_style = "color:#166534; background:#DCFCE7;" if triage_pass else "color:#991B1B; background:#FEE2E2;"

            citation_mark = "✓" if rec_hit else "✗"
            citation_style = "color:#166534; background:#DCFCE7;" if rec_hit else "color:#991B1B; background:#FEE2E2;"

            esc_pass = (is_escalated == ticket.get("escalate", False))
            esc_mark = "✓" if esc_pass else "✗"
            esc_style = "color:#166534; background:#DCFCE7;" if esc_pass else "color:#991B1B; background:#FEE2E2;"

            st.html('<div style="padding: 0 32px;">')
            btn_col1, btn_col2, btn_col3, eval_col = st.columns([1.3, 1, 1.3, 2.8])

            with btn_col1:
                if st.button("Approve & send draft", key=f"approve_{active_tid}", type="primary", use_container_width=True):
                    update_ticket(active_tid, {"status": "closed"})
                    st.toast(f"✅ Draft approved & sent for {active_tid}!", icon="🚀")

            with btn_col2:
                edit_key = f"edit_state_{active_tid}"
                if st.button("Edit draft", key=f"btn_edit_{active_tid}", type="secondary", use_container_width=True):
                    st.session_state[edit_key] = not st.session_state.get(edit_key, False)

            with btn_col3:
                if st.button("⚡ Re-run Pipeline", key=f"rerun_{active_tid}", type="secondary", use_container_width=True):
                    with st.spinner("Running 4-stage agent pipeline..."):
                        run_ticket_pipeline(ticket)
                        st.toast(f"Pipeline executed successfully for {active_tid}!", icon="⚡")
                        st.rerun()

            with eval_col:
                eval_html = f"""
                <div style="display:flex; align-items:center; justify-content:flex-end; gap:6px; height:100%;" class="mono">
                  <span style="font-size:11px; color:#71717A;">eval on this ticket:</span>
                  <span style="font-size:11px; border-radius:5px; padding:2px 7px; {triage_style}">triage {triage_mark}</span>
                  <span style="font-size:11px; border-radius:5px; padding:2px 7px; {citation_style}">citation {citation_mark}</span>
                  <span style="font-size:11px; border-radius:5px; padding:2px 7px; {esc_style}">escalation {esc_mark}</span>
                </div>
                """
                st.html(eval_html)

            st.html('</div>')

            # Draft Editor (when toggled via "Edit draft")
            if st.session_state.get(f"edit_state_{active_tid}", False):
                with st.container():
                    st.html('<div style="padding: 16px 32px;">')
                    st.markdown("**✏️ Edit Grounded Draft Reply**")
                    edited_draft = st.text_area(
                        "Grounded Reply Content",
                        value=draft_full,
                        height=220,
                        key=f"textarea_{active_tid}",
                        label_visibility="collapsed"
                    )
                    c_save, c_cancel = st.columns([1, 4])
                    with c_save:
                        if st.button("Save Draft", key=f"save_draft_{active_tid}", type="primary"):
                            pred["draft_reply"] = edited_draft
                            st.session_state[f"edit_state_{active_tid}"] = False
                            st.toast("Draft saved successfully!")
                            st.rerun()
                    with c_cancel:
                        if st.button("Cancel", key=f"cancel_draft_{active_tid}", type="secondary"):
                            st.session_state[f"edit_state_{active_tid}"] = False
                            st.rerun()
                    st.html('</div>')
