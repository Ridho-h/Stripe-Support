"""
Stripe Support Agent Dashboard - Internal Developer Console.
Streamlit application displaying:
1. Support Queue View with Urgency Badges & Filters
2. Ticket Detail View with Full 4-Stage Agent Reasoning Trail
3. Ground Truth Evaluation Strip (Pass/Fail against eval_rubric.md)
4. Comprehensive Category-level Eval Benchmark Report

Theme-adaptive (supports both Dark Mode and Light Mode seamlessly).
"""

import json
import os
import sys
import textwrap
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
    page_title="Stripe Support AI Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom theme-adaptive CSS (works in both Dark and Light modes)
st.markdown(
    """
    <style>
    /* Monospace formatting for technical identifiers */
    .mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        font-family: ui-monospace, SFMono-Regular, monospace;
        letter-spacing: 0.5px;
    }
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .badge-high {
        background-color: rgba(249, 115, 22, 0.2);
        color: #f97316;
        border: 1px solid rgba(249, 115, 22, 0.4);
    }
    .badge-medium {
        background-color: rgba(234, 179, 8, 0.2);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.4);
    }
    .badge-low {
        background-color: rgba(148, 163, 184, 0.2);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.4);
    }
    .badge-escalated {
        background-color: rgba(236, 72, 153, 0.2);
        color: #ec4899;
        border: 1px solid rgba(236, 72, 153, 0.4);
    }
    .badge-pass {
        background-color: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.4);
    }
    .badge-fail {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


# -------------------------------------------------------------
# Data Loading
# -------------------------------------------------------------
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
# Sidebar: Navigation & Filters
# -------------------------------------------------------------
st.sidebar.title("⚡ Stripe Support AI")
st.sidebar.caption("Autonomous 4-Agent Triage & Grounded Drafting System")
st.sidebar.divider()

view_mode = st.sidebar.radio("View", ["Ticket Queue & Inspector", "Evaluation Benchmark (Rubric)"])

st.sidebar.divider()
st.sidebar.subheader("Filter Tickets")
selected_urgency = st.sidebar.selectbox("Urgency", ["All", "critical", "high", "medium", "low"])
selected_category = st.sidebar.selectbox(
    "Category",
    ["All", "webhooks", "payments_charges", "connect_payouts", "api_idempotency",
     "billing_subscriptions", "refunds_disputes", "auth_keys", "tax", "radar_fraud", "general"]
)
escalated_filter = st.sidebar.selectbox("Escalation", ["All", "Escalated Only", "Non-Escalated Only"])
search_query = st.sidebar.text_input("Search ID or Subject", "").strip().lower()

# Filter tickets
filtered_tickets = all_tickets
if selected_urgency != "All":
    filtered_tickets = [t for t in filtered_tickets if t.get("urgency") == selected_urgency]
if selected_category != "All":
    filtered_tickets = [t for t in filtered_tickets if t.get("category") == selected_category]
if escalated_filter == "Escalated Only":
    filtered_tickets = [t for t in filtered_tickets if t.get("escalate")]
elif escalated_filter == "Non-Escalated Only":
    filtered_tickets = [t for t in filtered_tickets if not t.get("escalate")]
if search_query:
    filtered_tickets = [
        t for t in filtered_tickets
        if search_query in t["id"].lower()
        or search_query in t["subject"].lower()
        or search_query in t["body"].lower()
    ]


# -------------------------------------------------------------
# Main Content
# -------------------------------------------------------------
if view_mode == "Evaluation Benchmark (Rubric)":
    st.header("📊 Evaluation Benchmark Report")
    st.caption("Scored against labeled_tickets.json using eval_rubric.md")

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

        st.subheader("Performance Breakdown by Category")
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
        # Add Overall
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

        st.subheader("Safety & Quality Flags")
        flags = metrics.get("flags", {})
        colA, colB = st.columns(2)
        with colA:
            severe_misses = flags.get("severe_urgency_misses", [])
            st.metric("Severe Urgency Misses (±2 levels)", len(severe_misses))
            if severe_misses:
                st.error(f"Tickets flagged: {', '.join(severe_misses)}")
            else:
                st.success("0 severe urgency misses (all predictions within ±1 level)")
        with colB:
            hallucinated = flags.get("hallucinated_citations", [])
            st.metric("Hallucinated Citations", len(hallucinated))
            if hallucinated:
                st.error(f"Tickets flagged: {', '.join(hallucinated)}")
            else:
                st.success("0 hallucinated citations (all replies grounded in retrieved docs)")

else:
    # -------------------------------------------------------------
    # Ticket Queue & Detail Inspector
    # -------------------------------------------------------------
    col_left, col_right = st.columns([1, 1.6])

    with col_left:
        st.subheader(f"Queue ({len(filtered_tickets)} tickets)")

        ticket_options = {t["id"]: f"{t['id']} — {t['subject'][:45]}" for t in filtered_tickets}
        selected_tid = st.selectbox(
            "Select Ticket",
            options=list(ticket_options.keys()),
            format_func=lambda x: ticket_options.get(x, x),
            label_visibility="collapsed",
        )

        st.caption("Click a ticket above to inspect full 4-stage pipeline execution.")

        # Ticket Summary List Table
        queue_table = []
        for t in filtered_tickets:
            queue_table.append({
                "ID": t["id"],
                "Urgency": t["urgency"].upper(),
                "Category": t["category"],
                "Escalate": "🚨 YES" if t.get("escalate") else "NO",
                "Subject": t["subject"],
            })
        st.dataframe(queue_table, height=520, use_container_width=True)

    with col_right:
        if selected_tid:
            ticket = get_ticket(selected_tid)
            trace = traces.get(selected_tid, {})
            pred = predictions.get(selected_tid, {})

            # Clean header with native Streamlit elements
            urgency_class = f"badge-{ticket['urgency']}"
            escalated_badge = "<span class='badge badge-escalated'>🚨 ESCALATED</span>" if ticket.get("escalate") else ""

            header_html = textwrap.dedent(
                f"""<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(148,163,184,0.3); padding-bottom:8px; margin-bottom:12px;">
<div>
<span class="mono" style="font-size:1.4rem; font-weight:700;">{ticket['id']}</span>&nbsp;
<span class="badge {urgency_class}">{ticket['urgency']}</span>&nbsp;
<span class="badge badge-low">{ticket['category']}</span>&nbsp;
{escalated_badge}
</div>
<div class="mono" style="font-size:0.85rem; opacity:0.85;">
Status: <b>{ticket.get('status', 'open').upper()}</b>
</div>
</div>"""
            )
            st.markdown(header_html, unsafe_allow_html=True)

            st.markdown(f"**Subject:** {ticket['subject']}")
            with st.expander("Customer Ticket Body", expanded=False):
                st.write(ticket["body"])

            # ---------------------------------------------------------
            # Eval Strip: Real pass/fail indicators against rubric
            # ---------------------------------------------------------
            st.markdown("##### 🎯 Rubric Evaluation Strip")
            with st.container(border=True):
                e1, e2, e3, e4 = st.columns(4)

                # 1. Category
                cat_match = pred.get("category") == ticket["category"]
                cat_badge = "<span class='badge badge-pass'>PASS</span>" if cat_match else "<span class='badge badge-fail'>FAIL</span>"
                e1.markdown(f"**Category:** {cat_badge}<br><span class='mono' style='font-size:0.8rem'>{pred.get('category')}</span>", unsafe_allow_html=True)

                # 2. Urgency
                pred_urg = pred.get("urgency", ticket["urgency"])
                u_dist = urgency_distance(ticket["urgency"], pred_urg)
                if u_dist == 0:
                    urg_badge = "<span class='badge badge-pass'>EXACT</span>"
                elif u_dist == 1:
                    urg_badge = "<span class='badge badge-pass'>±1 CLOSE</span>"
                else:
                    urg_badge = "<span class='badge badge-fail'>SEVERE MISS</span>"
                e2.markdown(f"**Urgency:** {urg_badge}<br><span class='mono' style='font-size:0.8rem'>{pred_urg}</span>", unsafe_allow_html=True)

                # 3. Citation Recall@3
                retrieved_topics = pred.get("retrieved_doc_topics", [])
                first_word = ticket["doc_topic"].split()[0].lower()
                rec_hit = any(first_word in r.lower() for r in retrieved_topics[:3])
                rec_badge = "<span class='badge badge-pass'>PASS</span>" if rec_hit else "<span class='badge badge-fail'>FAIL</span>"
                e3.markdown(f"**Doc Recall@3:** {rec_badge}<br><span class='mono' style='font-size:0.8rem'>{ticket['doc_topic'][:22]}...</span>", unsafe_allow_html=True)

                # 4. Escalation Decision
                esc_match = pred.get("escalate") == ticket["escalate"]
                esc_badge = "<span class='badge badge-pass'>PASS</span>" if esc_match else "<span class='badge badge-fail'>FAIL</span>"
                decision_text = "ESCALATE" if pred.get("escalate") else "STANDARD"
                e4.markdown(f"**Escalation:** {esc_badge}<br><span class='mono' style='font-size:0.8rem'>{decision_text}</span>", unsafe_allow_html=True)

            # ---------------------------------------------------------
            # 4-Stage Reasoning Trail
            # ---------------------------------------------------------
            st.markdown("##### 🔬 4-Stage Agent Reasoning Trail")

            stages = trace.get("stages", [])

            # Stage 1: Triage
            s1 = next((s for s in stages if s.get("stage_index") == 1), None)
            with st.container(border=True):
                c_title, c_lat = st.columns([3, 1])
                c_title.markdown("⚡ **Stage 1: Triage Agent**")
                c_lat.markdown(f"<div style='text-align:right;'><span class='mono' style='font-size:0.8rem; opacity:0.75;'>Latency: {s1.get('latency_ms', 0) if s1 else '-'}ms</span></div>", unsafe_allow_html=True)
                st.markdown(f"Classified: <span class='mono'><b>{pred.get('category')}</b></span> | Urgency: <span class='mono'><b>{pred.get('urgency')}</b></span>", unsafe_allow_html=True)
                st.caption(f"**Reasoning:** {s1.get('reasoning') if s1 else 'No trace available'}")

            # Stage 2: Retrieval
            s2 = next((s for s in stages if s.get("stage_index") == 2), None)
            with st.container(border=True):
                c_title, c_lat = st.columns([3, 1])
                c_title.markdown("🔍 **Stage 2: Retrieval Agent (MCP Tool: `search_docs`)**")
                c_lat.markdown(f"<div style='text-align:right;'><span class='mono' style='font-size:0.8rem; opacity:0.75;'>Latency: {s2.get('latency_ms', 0) if s2 else '-'}ms</span></div>", unsafe_allow_html=True)
                passages = (s2.get("output", {}).get("passages", [])) if s2 else []
                st.caption(f"Retrieved {len(passages)} documentation topic(s) from curated corpus:")
                for idx, p in enumerate(passages, 1):
                    with st.expander(f"#{idx} {p.get('doc_topic')} (Score: {p.get('score', '-')})", expanded=(idx == 1)):
                        st.markdown(f"**Attribution:** [{p.get('source')}]({p.get('source')})")
                        st.write(p.get("snippet"))

            # Stage 3: Drafting
            s3 = next((s for s in stages if s.get("stage_index") == 3), None)
            with st.container(border=True):
                c_title, c_lat = st.columns([3, 1])
                c_title.markdown("✍️ **Stage 3: Drafting Agent (Strict Grounding)**")
                c_lat.markdown(f"<div style='text-align:right;'><span class='mono' style='font-size:0.8rem; opacity:0.75;'>Latency: {s3.get('latency_ms', 0) if s3 else '-'}ms</span></div>", unsafe_allow_html=True)
                draft_text = pred.get("draft_reply") or (s3.get("output", {}).get("draft_reply", "")) if s3 else ""
                st.caption(f"**Reasoning:** {s3.get('reasoning') if s3 else '-'}")
                st.text_area("Generated Grounded Reply", value=draft_text, height=160, key=f"draft_{selected_tid}")

            # Stage 4: Escalation
            s4 = next((s for s in stages if s.get("stage_index") == 4), None)
            with st.container(border=True):
                c_title, c_lat = st.columns([3, 1])
                c_title.markdown("🚨 **Stage 4: Escalation Agent (Recall Biased)**")
                c_lat.markdown(f"<div style='text-align:right;'><span class='mono' style='font-size:0.8rem; opacity:0.75;'>Latency: {s4.get('latency_ms', 0) if s4 else '-'}ms</span></div>", unsafe_allow_html=True)
                is_esc = pred.get("escalate", False)
                if is_esc:
                    st.error(f"**Decision: HUMAN ESCALATION REQUIRED**\n\n**Reason:** {pred.get('escalation_reason', '-')}")
                else:
                    st.success(f"**Decision: RESOLVED WITHOUT ESCALATION**\n\n**Reason:** {pred.get('escalation_reason', '-')}")

            # Rerun Action Button
            st.divider()
            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button("⚡ Re-run Pipeline for This Ticket", use_container_width=True):
                    with st.spinner("Executing 4-stage agent pipeline..."):
                        run_ticket_pipeline(ticket)
                        st.success(f"Ticket {selected_tid} processed successfully!")
                        st.rerun()
            with c_btn2:
                new_status = st.selectbox(
                    "Update Status in SQLite",
                    options=["open", "in_progress", "drafted", "escalated", "closed"],
                    index=["open", "in_progress", "drafted", "escalated", "closed"].index(ticket.get("status", "open")),
                    label_visibility="collapsed",
                )
                if st.button("Save Status", use_container_width=True):
                    update_ticket(selected_tid, {"status": new_status})
                    st.success(f"Status updated to '{new_status}'")
                    st.rerun()
