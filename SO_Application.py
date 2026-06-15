import streamlit as st
import pandas as pd
import uuid
import json
import random
from datetime import datetime, timedelta
from io import BytesIO

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Credit Saison India – Sales Officer Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Credit Saison India Theme ───────────────────────────────────────────────────
CS_RED   = "#E31837"
CS_DARK  = "#1C1C1C"
CS_WHITE = "#FFFFFF"
CS_LIGHT = "#F5F5F5"
CS_GREY  = "#6C757D"
CS_GREEN = "#28A745"
CS_AMBER = "#FFC107"
CS_BLUE  = "#17A2B8"

CUSTOM_CSS = f"""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {CS_LIGHT};
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {CS_DARK} 0%, #2d2d2d 100%);
    border-right: 3px solid {CS_RED};
}}
section[data-testid="stSidebar"] * {{
    color: {CS_WHITE} !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    color: {CS_WHITE} !important;
    font-weight: 500;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] > div {{
    gap: 4px;
}}

/* ── Top Header ── */
.cs-header {{
    background: linear-gradient(135deg, {CS_DARK} 0%, {CS_RED} 100%);
    padding: 18px 28px;
    border-radius: 12px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 16px rgba(0,0,0,0.18);
}}
.cs-header h1 {{
    color: {CS_WHITE};
    font-size: 1.6rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.5px;
}}
.cs-header .subtitle {{
    color: rgba(255,255,255,0.75);
    font-size: 0.85rem;
    margin-top: 2px;
}}
.cs-logo {{
    font-size: 2.2rem;
    font-weight: 900;
    color: {CS_WHITE};
    letter-spacing: -1px;
}}
.cs-logo span {{
    color: {CS_RED};
    background: {CS_WHITE};
    padding: 2px 6px;
    border-radius: 4px;
}}

/* ── Metric Cards ── */
.metric-row {{
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}
.metric-card {{
    flex: 1;
    min-width: 140px;
    background: {CS_WHITE};
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 4px solid {CS_RED};
    transition: transform 0.15s;
}}
.metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.12);
}}
.metric-card .val {{
    font-size: 2rem;
    font-weight: 700;
    color: {CS_DARK};
    line-height: 1;
}}
.metric-card .lbl {{
    font-size: 0.78rem;
    color: {CS_GREY};
    margin-top: 4px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ── Status Badges ── */
.badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
.badge-punched    {{ background:#FFF3CD; color:#856404; }}
.badge-first      {{ background:#CCE5FF; color:#004085; }}
.badge-interested {{ background:#D4EDDA; color:#155724; }}
.badge-rejected   {{ background:#F8D7DA; color:#721C24; }}
.badge-reverted   {{ background:#E2D9F3; color:#4B0082; }}
.badge-moved      {{ background:#D1ECF1; color:#0C5460; }}
.badge-default    {{ background:#E9ECEF; color:#495057; }}

/* ── Buttons ── */
div.stButton > button {{
    background: {CS_RED};
    color: {CS_WHITE};
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 22px;
    font-size: 0.88rem;
    transition: all 0.2s;
    box-shadow: 0 2px 6px rgba(227,24,55,0.3);
}}
div.stButton > button:hover {{
    background: #c0142f;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(227,24,55,0.4);
}}
div.stButton > button:active {{
    transform: translateY(0);
}}

/* ── Section Cards ── */
.section-card {{
    background: {CS_WHITE};
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    margin-bottom: 20px;
}}
.section-title {{
    font-size: 1rem;
    font-weight: 700;
    color: {CS_DARK};
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid {CS_RED};
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* ── Flag chips ── */
.flag-chip {{
    display: inline-block;
    background: #FFF3CD;
    color: #856404;
    border: 1px solid #FFEAA7;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.71rem;
    font-weight: 600;
    margin: 2px;
}}
.flag-chip.red {{
    background: #F8D7DA;
    color: #721C24;
    border-color: #F5C6CB;
}}
.flag-chip.green {{
    background: #D4EDDA;
    color: #155724;
    border-color: #C3E6CB;
}}

/* ── Expander tweaks ── */
details summary {{
    font-weight: 600;
    color: {CS_DARK};
}}

/* ── DataEditor / Table ── */
.stDataFrame {{ border-radius: 10px; overflow: hidden; }}

/* ── Toast-style alerts ── */
.alert-success {{
    background: #D4EDDA; color: #155724;
    border-left: 4px solid {CS_GREEN};
    border-radius: 8px; padding: 12px 16px; margin: 10px 0;
    font-weight: 500;
}}
.alert-warning {{
    background: #FFF3CD; color: #856404;
    border-left: 4px solid {CS_AMBER};
    border-radius: 8px; padding: 12px 16px; margin: 10px 0;
    font-weight: 500;
}}
.alert-info {{
    background: #D1ECF1; color: #0C5460;
    border-left: 4px solid {CS_BLUE};
    border-radius: 8px; padding: 12px 16px; margin: 10px 0;
    font-weight: 500;
}}

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {{
    border: 2px dashed {CS_RED} !important;
    border-radius: 10px !important;
    background: #FFF5F6 !important;
}}

/* ── Selectbox & inputs ── */
.stSelectbox [data-baseweb="select"] > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {{
    border-radius: 8px !important;
    border-color: #dee2e6 !important;
}}

/* ── Divider ── */
hr {{ border-color: #E9ECEF; margin: 20px 0; }}

/* ── Lead row highlight on hover ── */
.lead-row:hover {{ background: #FFF5F6; }}

/* ── Sidebar nav items ── */
.nav-item {{
    padding: 10px 16px;
    border-radius: 8px;
    margin: 4px 0;
    cursor: pointer;
    color: rgba(255,255,255,0.85);
    font-weight: 500;
    transition: background 0.15s;
}}
.nav-item:hover, .nav-item.active {{
    background: rgba(227,24,55,0.25);
    color: {CS_WHITE};
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─── Session State Init ──────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "leads": {},           # lead_id -> dict
        "docs": {},            # lead_id -> list of doc info dicts
        "page": "Dashboard",
        "so_name": "Rajesh Kumar",
        "so_branch": "Mumbai – Andheri East",
        "upload_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─── Constants ──────────────────────────────────────────────────────────────────
STATUSES = [
    "First Contact", "Interested", "Lead Punched",
    "Rejected", "Reverted Back", "Lead Moved",
]
LOAN_TYPES   = ["Personal Loan", "Business Loan", "Home Loan", "LAP", "Gold Loan", "Two-Wheeler Loan"]
EMPLOYMENT   = ["Salaried", "Self-Employed", "Business Owner", "Freelancer"]
ISSUE_POOL   = [
    "Aadhaar Missing", "PAN Name Mismatch", "Bank Statement Incomplete",
    "CIBIL Score Low", "Address Proof Not Matching", "Photo Not Clear",
    "Salary Slip Outdated", "GST Certificate Expired", "ITR Not Submitted",
    "Signature Mismatch", "Date of Birth Discrepancy",
]
EXCEL_COLUMNS = [
    "Full Name", "Mobile", "Email", "Loan Type", "Loan Amount (₹)",
    "Employment Type", "Monthly Income (₹)", "PAN Number", "Aadhaar Number",
    "City", "Pincode", "Notes",
]

# ─── Helper Functions ────────────────────────────────────────────────────────────
def badge_html(status: str) -> str:
    cls = {
        "First Contact": "badge-first",
        "Interested":    "badge-interested",
        "Lead Punched":  "badge-punched",
        "Rejected":      "badge-rejected",
        "Reverted Back": "badge-reverted",
        "Lead Moved":    "badge-moved",
    }.get(status, "badge-default")
    return f'<span class="badge {cls}">{status}</span>'

def generate_lan() -> str:
    return "LAN" + str(random.randint(1000000, 9999999))

def random_issues() -> list:
    n = random.randint(0, 3)
    return random.sample(ISSUE_POOL, n)

def add_lead(row: dict, status="Lead Punched") -> str:
    lid = str(uuid.uuid4())[:8].upper()
    st.session_state.leads[lid] = {
        "id": lid,
        "full_name":      row.get("Full Name", "—"),
        "mobile":         str(row.get("Mobile", "—")),
        "email":          row.get("Email", "—"),
        "loan_type":      row.get("Loan Type", "Personal Loan"),
        "loan_amount":    row.get("Loan Amount (₹)", 0),
        "employment":     row.get("Employment Type", "Salaried"),
        "income":         row.get("Monthly Income (₹)", 0),
        "pan":            row.get("PAN Number", "—"),
        "aadhaar":        row.get("Aadhaar Number", "—"),
        "city":           row.get("City", "—"),
        "pincode":        str(row.get("Pincode", "—")),
        "notes":          row.get("Notes", ""),
        "status":         status,
        "created_at":     datetime.now().strftime("%d %b %Y, %H:%M"),
        "lan":            None,
        "lan_pushed_at":  None,
        "issues":         [],
        "docs":           [],
    }
    st.session_state.docs[lid] = []
    return lid

def download_template() -> bytes:
    df = pd.DataFrame(columns=EXCEL_COLUMNS)
    sample = {
        "Full Name": "Amit Sharma", "Mobile": "9876543210",
        "Email": "amit@example.com", "Loan Type": "Personal Loan",
        "Loan Amount (₹)": 500000, "Employment Type": "Salaried",
        "Monthly Income (₹)": 75000, "PAN Number": "ABCDE1234F",
        "Aadhaar Number": "1234-5678-9012", "City": "Mumbai",
        "Pincode": "400001", "Notes": "Good profile",
    }
    df = pd.concat([df, pd.DataFrame([sample])], ignore_index=True)
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:1.5rem; font-weight:900; color:{CS_WHITE}; letter-spacing:-0.5px;">
            Credit <span style="color:{CS_RED};">Saison</span>
        </div>
        <div style="font-size:0.72rem; color:rgba(255,255,255,0.5); letter-spacing:1px; margin-top:2px;">
            INDIA · SALES OFFICER PORTAL
        </div>
    </div>
    <hr style="border-color:rgba(255,255,255,0.1); margin:10px 0 18px 0;">
    """, unsafe_allow_html=True)

    pages = {
        "📊 Dashboard":       "Dashboard",
        "➕ Upload Leads":    "Upload Leads",
        "📁 Manage Documents":"Manage Documents",
        "🚀 Push to LAN":     "Push to LAN",
        "⚠️ Flags & Issues":  "Flags & Issues",
    }
    for label, key in pages.items():
        active = st.session_state.page == key
        style = f"background:rgba(227,24,55,0.3); border-left:3px solid {CS_RED};" if active else ""
        if st.button(
            label,
            key=f"nav_{key}",
            use_container_width=True,
        ):
            st.session_state.page = key
            st.rerun()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:18px 0;'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding:12px 8px; background:rgba(255,255,255,0.06); border-radius:8px;">
        <div style="font-size:0.78rem; color:rgba(255,255,255,0.5); margin-bottom:4px;">LOGGED IN AS</div>
        <div style="font-weight:600; color:{CS_WHITE};">{st.session_state.so_name}</div>
        <div style="font-size:0.75rem; color:rgba(255,255,255,0.55);">{st.session_state.so_branch}</div>
        <div style="font-size:0.72rem; color:rgba(255,255,255,0.4); margin-top:6px;">
            {datetime.now().strftime("%d %b %Y · %H:%M")}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Header ─────────────────────────────────────────────────────────────────────
page_icons = {
    "Dashboard":        ("📊", "Lead Dashboard"),
    "Upload Leads":     ("➕", "Upload Leads from Excel"),
    "Manage Documents": ("📁", "Manage Lead Documents"),
    "Push to LAN":      ("🚀", "Push Leads to LAN"),
    "Flags & Issues":   ("⚠️", "Flags & Issues"),
}
icon, title = page_icons.get(st.session_state.page, ("🏦", st.session_state.page))
st.markdown(f"""
<div class="cs-header">
    <div>
        <h1>{icon} {title}</h1>
        <div class="subtitle">Credit Saison India · Sales Officer Portal</div>
    </div>
    <div class="cs-logo">CS<span>i</span></div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Dashboard":

    leads = st.session_state.leads
    total = len(leads)
    by_status = {}
    for l in leads.values():
        by_status[l["status"]] = by_status.get(l["status"], 0) + 1

    # ── Metric Cards ──
    cols = st.columns(6)
    metric_data = [
        ("Total Leads",    total,                            CS_RED),
        ("Lead Punched",   by_status.get("Lead Punched", 0), "#FFC107"),
        ("Interested",     by_status.get("Interested", 0),   "#28A745"),
        ("First Contact",  by_status.get("First Contact", 0),"#17A2B8"),
        ("Reverted Back",  by_status.get("Reverted Back", 0),"#6F42C1"),
        ("Lead Moved",     by_status.get("Lead Moved", 0),   "#20C997"),
    ]
    for col, (lbl, val, color) in zip(cols, metric_data):
        col.markdown(f"""
        <div class="metric-card" style="border-left-color:{color};">
            <div class="val" style="color:{color};">{val}</div>
            <div class="lbl">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filters ──
    with st.container():
        fc1, fc2, fc3, fc4 = st.columns([2, 1.5, 1.5, 1])
        search   = fc1.text_input("🔍 Search by name, mobile, PAN…", placeholder="Search leads…", label_visibility="collapsed")
        f_status = fc2.selectbox("Status", ["All"] + STATUSES, label_visibility="collapsed")
        f_loan   = fc3.selectbox("Loan Type", ["All"] + LOAN_TYPES, label_visibility="collapsed")
        if fc4.button("＋ New Lead", use_container_width=True):
            st.session_state.page = "Upload Leads"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filter leads ──
    filtered = [
        l for l in leads.values()
        if (not search or search.lower() in (l["full_name"]+l["mobile"]+l["pan"]).lower())
        and (f_status == "All" or l["status"] == f_status)
        and (f_loan == "All" or l["loan_type"] == f_loan)
    ]

    if not filtered:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; background:white;
                    border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:3rem;">📋</div>
            <div style="font-size:1.1rem; font-weight:600; color:#495057; margin-top:12px;">
                No leads found
            </div>
            <div style="color:#6c757d; margin-top:6px;">
                Upload leads from Excel or adjust your filters
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Lead Table ──
        st.markdown(f"""
        <div style="background:white; border-radius:12px; overflow:hidden;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07); margin-bottom:10px;">
            <table style="width:100%; border-collapse:collapse; font-size:0.83rem;">
                <thead>
                <tr style="background:{CS_DARK}; color:white;">
                    <th style="padding:12px 14px; text-align:left; font-weight:600;">Lead ID</th>
                    <th style="padding:12px 14px; text-align:left; font-weight:600;">Name</th>
                    <th style="padding:12px 14px; text-align:left; font-weight:600;">Mobile</th>
                    <th style="padding:12px 14px; text-align:left; font-weight:600;">Loan Type</th>
                    <th style="padding:12px 14px; text-align:right; font-weight:600;">Amount (₹)</th>
                    <th style="padding:12px 14px; text-align:left; font-weight:600;">City</th>
                    <th style="padding:12px 14px; text-align:center; font-weight:600;">Status</th>
                    <th style="padding:12px 14px; text-align:left; font-weight:600;">Created At</th>
                    <th style="padding:12px 14px; text-align:left; font-weight:600;">LAN</th>
                    <th style="padding:12px 14px; text-align:center; font-weight:600;">Flags</th>
                </tr>
                </thead>
                <tbody>
        """, unsafe_allow_html=True)

        for i, l in enumerate(filtered):
            bg = "white" if i % 2 == 0 else "#FAFAFA"
            lan_disp   = l["lan"] if l["lan"] else "—"
            flags_count = len(l.get("issues", []))
            flags_html = f'<span style="color:#721C24; font-weight:700;">{flags_count} ⚠️</span>' if flags_count else '<span style="color:#155724;">✔ Clear</span>'
            st.markdown(f"""
            <tr style="background:{bg}; border-bottom:1px solid #F0F0F0;" class="lead-row">
                <td style="padding:11px 14px; font-family:monospace; color:{CS_RED}; font-weight:600;">{l['id']}</td>
                <td style="padding:11px 14px; font-weight:500;">{l['full_name']}</td>
                <td style="padding:11px 14px; color:#555;">{l['mobile']}</td>
                <td style="padding:11px 14px;">{l['loan_type']}</td>
                <td style="padding:11px 14px; text-align:right; font-weight:600;">
                    {f"₹{int(float(l['loan_amount'])):,}" if l['loan_amount'] else '—'}
                </td>
                <td style="padding:11px 14px;">{l['city']}</td>
                <td style="padding:11px 14px; text-align:center;">{badge_html(l['status'])}</td>
                <td style="padding:11px 14px; color:#888; font-size:0.78rem;">{l['created_at']}</td>
                <td style="padding:11px 14px; font-family:monospace; color:#17A2B8; font-size:0.8rem;">{lan_disp}</td>
                <td style="padding:11px 14px; text-align:center;">{flags_html}</td>
            </tr>
            """, unsafe_allow_html=True)

        st.markdown("</tbody></table></div>", unsafe_allow_html=True)

        # ── Lead Detail Expanders ──
        st.markdown("<br>**Click a lead below to view / edit details:**", unsafe_allow_html=True)
        for l in filtered:
            with st.expander(f"🧾 {l['full_name']}  ·  {l['id']}  ·  {l['status']}", expanded=False):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**Personal Details**")
                    st.write(f"📞 {l['mobile']}")
                    st.write(f"✉️ {l['email']}")
                    st.write(f"🏙️ {l['city']} – {l['pincode']}")
                with c2:
                    st.markdown("**Loan Details**")
                    st.write(f"💼 {l['loan_type']}")
                    amt = f"₹{int(float(l['loan_amount'])):,}" if l['loan_amount'] else "—"
                    st.write(f"💰 {amt}")
                    st.write(f"👔 {l['employment']}")
                    income = f"₹{int(float(l['income'])):,}/mo" if l['income'] else "—"
                    st.write(f"💵 {income}")
                with c3:
                    st.markdown("**KYC**")
                    st.write(f"🪪 PAN: `{l['pan']}`")
                    st.write(f"🆔 Aadhaar: `{l['aadhaar']}`")
                    if l.get("lan"):
                        st.write(f"🏷️ LAN: `{l['lan']}`")
                if l.get("notes"):
                    st.info(f"📝 {l['notes']}")
                if l.get("issues"):
                    st.markdown("**⚠️ Flags:**")
                    flags_str = "  ".join([f'<span class="flag-chip red">{f}</span>' for f in l["issues"]])
                    st.markdown(flags_str, unsafe_allow_html=True)
                docs_for_lead = st.session_state.docs.get(l["id"], [])
                if docs_for_lead:
                    st.markdown(f"**📎 Documents ({len(docs_for_lead)}):**")
                    for d in docs_for_lead:
                        st.write(f"• {d['name']}  `{d['type']}`  –  _{d['uploaded_at']}_")

                # Edit section (only if not moved)
                if l["status"] != "Lead Moved":
                    st.markdown("---")
                    st.markdown("**✏️ Edit Lead Details**")
                    ec1, ec2 = st.columns(2)
                    new_name   = ec1.text_input("Full Name",   value=l["full_name"],  key=f"e_name_{l['id']}")
                    new_mobile = ec2.text_input("Mobile",      value=l["mobile"],     key=f"e_mob_{l['id']}")
                    new_email  = ec1.text_input("Email",       value=l["email"],      key=f"e_email_{l['id']}")
                    new_city   = ec2.text_input("City",        value=l["city"],       key=f"e_city_{l['id']}")
                    new_notes  = st.text_area("Notes",         value=l["notes"],      key=f"e_notes_{l['id']}", height=70)
                    new_loan   = st.selectbox("Loan Type", LOAN_TYPES,
                                              index=LOAN_TYPES.index(l["loan_type"]) if l["loan_type"] in LOAN_TYPES else 0,
                                              key=f"e_loan_{l['id']}")
                    if st.button("💾 Save Changes", key=f"save_{l['id']}"):
                        st.session_state.leads[l["id"]].update({
                            "full_name": new_name, "mobile": new_mobile,
                            "email": new_email,    "city": new_city,
                            "notes": new_notes,    "loan_type": new_loan,
                        })
                        st.success("Lead updated successfully!")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: UPLOAD LEADS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Upload Leads":

    col_left, col_right = st.columns([1.8, 1])

    with col_left:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📥 Upload Lead Excel</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="alert-info">
            📌  Upload a standard Excel file with lead details. Each row = one lead.
            The file must contain the columns listed below. Download the template if needed.
        </div>
        """, unsafe_allow_html=True)

        tpl_col, _ = st.columns([1, 3])
        tpl_bytes = download_template()
        tpl_col.download_button(
            "⬇️ Download Template",
            data=tpl_bytes,
            file_name="CS_Lead_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        uploaded = st.file_uploader(
            "Drop Excel file here or click to browse",
            type=["xlsx", "xls"],
            label_visibility="collapsed",
        )

        if uploaded:
            try:
                df = pd.read_excel(uploaded)
                missing = [c for c in EXCEL_COLUMNS if c not in df.columns]
                if missing:
                    st.markdown(f'<div class="alert-warning">⚠️ Missing columns: {", ".join(missing)}<br>Please use the provided template.</div>', unsafe_allow_html=True)
                else:
                    df = df.dropna(subset=["Full Name"])
                    st.markdown(f'<div class="alert-success">✅ {len(df)} lead(s) found in the file.</div>', unsafe_allow_html=True)
                    st.dataframe(df, use_container_width=True, height=280)

                    if st.button(f"➕ Add {len(df)} Lead(s) to Dashboard", use_container_width=True):
                        added = 0
                        for _, row in df.iterrows():
                            add_lead(row.to_dict())
                            added += 1
                        st.session_state.upload_result = added
                        st.success(f"✅ {added} lead(s) added successfully!")
                        st.balloons()
            except Exception as e:
                st.error(f"Error reading file: {e}")

        # ── Manual Entry ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">✍️ Or Add a Single Lead Manually</div>', unsafe_allow_html=True)

        with st.form("manual_lead_form", clear_on_submit=True):
            m1, m2 = st.columns(2)
            m_name   = m1.text_input("Full Name *")
            m_mobile = m2.text_input("Mobile *")
            m_email  = m1.text_input("Email")
            m_city   = m2.text_input("City")
            m_loan   = m1.selectbox("Loan Type", LOAN_TYPES)
            m_amt    = m2.number_input("Loan Amount (₹)", min_value=0, step=10000)
            m_emp    = m1.selectbox("Employment Type", EMPLOYMENT)
            m_income = m2.number_input("Monthly Income (₹)", min_value=0, step=1000)
            m_pan    = m1.text_input("PAN Number")
            m_aadh   = m2.text_input("Aadhaar Number")
            m_pin    = m1.text_input("Pincode")
            m_notes  = st.text_area("Notes", height=70)
            submitted = st.form_submit_button("➕ Add Lead", use_container_width=True)
            if submitted:
                if not m_name or not m_mobile:
                    st.error("Full Name and Mobile are required.")
                else:
                    add_lead({
                        "Full Name": m_name, "Mobile": m_mobile, "Email": m_email,
                        "Loan Type": m_loan, "Loan Amount (₹)": m_amt,
                        "Employment Type": m_emp, "Monthly Income (₹)": m_income,
                        "PAN Number": m_pan, "Aadhaar Number": m_aadh,
                        "City": m_city, "Pincode": m_pin, "Notes": m_notes,
                    })
                    st.success(f"Lead for {m_name} added!")
                    st.rerun()

    with col_right:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📋 Required Columns</div>
        </div>
        """, unsafe_allow_html=True)
        for col in EXCEL_COLUMNS:
            st.markdown(f"• `{col}`")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="section-card">
            <div class="section-title">💡 Tips</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        - Each row in Excel = one loan lead
        - Multiple leads can be added in a single upload
        - After upload, all leads appear in the Dashboard
        - Documents can be attached from the **Manage Documents** tab
        - Once ready, use **Push to LAN** to submit
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MANAGE DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Manage Documents":

    leads = st.session_state.leads
    active_leads = {lid: l for lid, l in leads.items() if l["status"] != "Lead Moved"}

    if not active_leads:
        st.markdown("""
        <div class="alert-info">No active leads found. Upload leads first from the <b>Upload Leads</b> section.</div>
        """, unsafe_allow_html=True)
    else:
        DOC_TYPES = [
            "Aadhaar Card", "PAN Card", "Passport", "Voter ID",
            "Salary Slip (Latest)", "Salary Slip (Previous)", "Bank Statement (3M)",
            "Bank Statement (6M)", "ITR", "Form 16", "GST Certificate",
            "Business Proof", "Property Documents", "Photograph", "Other",
        ]

        st.markdown("""
        <div class="alert-info">
            Select a lead and upload documents. You can attach multiple document types per lead.
        </div>
        """, unsafe_allow_html=True)

        # Lead selector
        lead_options = {f"{l['full_name']}  [{lid}]  ·  {l['loan_type']}": lid
                        for lid, l in active_leads.items()}
        selected_label = st.selectbox("Select Lead", list(lead_options.keys()), label_visibility="visible")
        selected_lid   = lead_options[selected_label]
        selected_lead  = leads[selected_lid]

        col_up, col_docs = st.columns([1.2, 1])

        with col_up:
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">📤 Upload Documents for {selected_lead['full_name']}</div>
            </div>
            """, unsafe_allow_html=True)

            doc_type = st.selectbox("Document Type", DOC_TYPES)
            doc_file = st.file_uploader(
                "Upload file (PDF, JPG, PNG)",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"docup_{selected_lid}",
                label_visibility="collapsed",
            )
            if doc_file:
                if st.button("📎 Attach Document", use_container_width=True):
                    st.session_state.docs[selected_lid].append({
                        "name": doc_file.name,
                        "type": doc_type,
                        "size": f"{doc_file.size / 1024:.1f} KB",
                        "uploaded_at": datetime.now().strftime("%d %b %Y, %H:%M"),
                    })
                    st.success(f"✅ '{doc_file.name}' attached as {doc_type}")
                    st.rerun()

        with col_docs:
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">📁 Attached Documents</div>
            </div>
            """, unsafe_allow_html=True)

            docs_list = st.session_state.docs.get(selected_lid, [])
            if not docs_list:
                st.markdown('<div class="alert-warning">No documents attached yet.</div>', unsafe_allow_html=True)
            else:
                for i, d in enumerate(docs_list):
                    dcol1, dcol2 = st.columns([4, 1])
                    dcol1.markdown(f"""
                    <div style="background:#F8F9FA; border-radius:8px; padding:10px 12px; margin-bottom:8px;
                                border-left:3px solid {CS_RED};">
                        <div style="font-weight:600; font-size:0.83rem;">{d['name']}</div>
                        <div style="font-size:0.75rem; color:{CS_GREY};">{d['type']}  ·  {d['size']}  ·  {d['uploaded_at']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if dcol2.button("🗑️", key=f"del_doc_{selected_lid}_{i}", help="Remove"):
                        st.session_state.docs[selected_lid].pop(i)
                        st.rerun()

        # Bulk doc upload for multiple leads
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">📂 Bulk Document Upload (Multiple Leads)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="alert-info">Select multiple leads and a common document type to upload the same document to all selected leads at once.</div>
        """, unsafe_allow_html=True)

        bulk_labels  = {f"{l['full_name']}  [{lid}]": lid for lid, l in active_leads.items()}
        bulk_sel     = st.multiselect("Select Leads for Bulk Upload", list(bulk_labels.keys()))
        bulk_type    = st.selectbox("Document Type (Bulk)", DOC_TYPES, key="bulk_doc_type")
        bulk_file    = st.file_uploader("Upload Document (will be attached to all selected leads)",
                                        type=["pdf", "jpg", "jpeg", "png"], key="bulk_file",
                                        label_visibility="collapsed")
        if bulk_file and bulk_sel:
            if st.button(f"📎 Attach to {len(bulk_sel)} Lead(s)", use_container_width=True):
                for lbl in bulk_sel:
                    lid_b = bulk_labels[lbl]
                    st.session_state.docs[lid_b].append({
                        "name": bulk_file.name,
                        "type": bulk_type,
                        "size": f"{bulk_file.size / 1024:.1f} KB",
                        "uploaded_at": datetime.now().strftime("%d %b %Y, %H:%M"),
                    })
                st.success(f"✅ Document attached to {len(bulk_sel)} lead(s)!")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PUSH TO LAN
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Push to LAN":

    leads = st.session_state.leads
    eligible = {lid: l for lid, l in leads.items() if l["status"] == "Lead Punched"}

    st.markdown("""
    <div class="alert-info">
        Select one or more <b>Lead Punched</b> leads and click <b>Push to LAN</b>.
        All selected leads will be submitted simultaneously and moved out of your bucket.
    </div>
    """, unsafe_allow_html=True)

    if not eligible:
        st.markdown("""
        <div style="text-align:center; padding:50px; background:white; border-radius:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:2.5rem;">🎉</div>
            <div style="font-size:1.1rem; font-weight:600; margin-top:12px;">
                No leads pending LAN push
            </div>
            <div style="color:#6c757d; margin-top:6px;">
                Either all leads have been submitted, or there are no leads with "Lead Punched" status.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"**{len(eligible)} lead(s) eligible for LAN push:**")

        # Selection
        lead_display = {}
        for lid, l in eligible.items():
            amt = f"₹{int(float(l['loan_amount'])):,}" if l["loan_amount"] else "—"
            docs_count = len(st.session_state.docs.get(lid, []))
            lead_display[f"{l['full_name']}  ·  {l['loan_type']}  ·  {amt}  ·  📎 {docs_count} doc(s)  [{lid}]"] = lid

        selected_for_push = st.multiselect(
            "Select leads to push:",
            list(lead_display.keys()),
            default=list(lead_display.keys()),
        )

        if selected_for_push:
            # Preview table
            preview_rows = []
            for lbl in selected_for_push:
                lid = lead_display[lbl]
                l   = leads[lid]
                docs_count = len(st.session_state.docs.get(lid, []))
                preview_rows.append({
                    "Lead ID":    l["id"],
                    "Name":       l["full_name"],
                    "Loan Type":  l["loan_type"],
                    "Amount":     f"₹{int(float(l['loan_amount'])):,}" if l["loan_amount"] else "—",
                    "City":       l["city"],
                    "Documents":  f"{docs_count} attached",
                })
            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

            # Warning for no docs
            no_docs = [lbl for lbl in selected_for_push
                       if not st.session_state.docs.get(lead_display[lbl])]
            if no_docs:
                st.markdown(f"""
                <div class="alert-warning">
                    ⚠️ {len(no_docs)} lead(s) have no documents attached.
                    It is recommended to attach documents before pushing.
                </div>
                """, unsafe_allow_html=True)

            # Confirm & Push
            col_btn, _ = st.columns([1, 3])
            confirm = col_btn.checkbox(f"I confirm push of {len(selected_for_push)} lead(s) to LAN")

            if confirm:
                if st.button(f"🚀 Push {len(selected_for_push)} Lead(s) to LAN", use_container_width=False):
                    pushed_lans = []
                    for lbl in selected_for_push:
                        lid = lead_display[lbl]
                        lan = generate_lan()
                        st.session_state.leads[lid]["status"]       = "Lead Moved"
                        st.session_state.leads[lid]["lan"]          = lan
                        st.session_state.leads[lid]["lan_pushed_at"] = datetime.now().strftime("%d %b %Y, %H:%M")
                        issues = random_issues()
                        st.session_state.leads[lid]["issues"]       = issues
                        pushed_lans.append((leads[lid]["full_name"], lan, issues))

                    st.markdown(f'<div class="alert-success">✅ {len(pushed_lans)} lead(s) pushed to LAN successfully!</div>', unsafe_allow_html=True)

                    for name, lan, issues in pushed_lans:
                        flag_html = ""
                        if issues:
                            flag_html = "  ·  " + "".join(f'<span class="flag-chip red">{f}</span>' for f in issues)
                        else:
                            flag_html = '  ·  <span class="flag-chip green">No Issues</span>'
                        st.markdown(f"""
                        <div style="background:white; border-radius:8px; padding:12px 16px; margin:6px 0;
                                    box-shadow:0 1px 6px rgba(0,0,0,0.08); display:flex; align-items:center; gap:8px;">
                            <span style="font-weight:600;">{name}</span>
                            <span style="font-family:monospace; color:#17A2B8; font-size:0.83rem;">{lan}</span>
                            {flag_html}
                        </div>
                        """, unsafe_allow_html=True)

                    st.rerun()
        else:
            st.markdown('<div class="alert-warning">Please select at least one lead to push.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: FLAGS & ISSUES
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Flags & Issues":

    leads = st.session_state.leads
    moved = {lid: l for lid, l in leads.items() if l["status"] == "Lead Moved"}

    # Summary
    total_moved  = len(moved)
    with_issues  = sum(1 for l in moved.values() if l.get("issues"))
    clear_leads  = total_moved - with_issues

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""
    <div class="metric-card" style="border-left-color:{CS_BLUE};">
        <div class="val" style="color:{CS_BLUE};">{total_moved}</div>
        <div class="lbl">Total Moved to LAN</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""
    <div class="metric-card" style="border-left-color:{CS_RED};">
        <div class="val" style="color:{CS_RED};">{with_issues}</div>
        <div class="lbl">With Flags / Issues</div>
    </div>""", unsafe_allow_html=True)
    c3.markdown(f"""
    <div class="metric-card" style="border-left-color:{CS_GREEN};">
        <div class="val" style="color:{CS_GREEN};">{clear_leads}</div>
        <div class="lbl">Clear – No Issues</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not moved:
        st.markdown("""
        <div class="alert-info">
            No leads have been pushed to LAN yet. Use the <b>Push to LAN</b> section to submit leads.
        </div>
        """, unsafe_allow_html=True)
    else:
        filter_issues = st.radio(
            "Filter:", ["All", "With Issues", "No Issues"],
            horizontal=True, label_visibility="collapsed",
        )

        for lid, l in moved.items():
            issues = l.get("issues", [])
            if filter_issues == "With Issues" and not issues:
                continue
            if filter_issues == "No Issues" and issues:
                continue

            has_issues = bool(issues)
            border_color = CS_RED if has_issues else CS_GREEN
            icon = "⚠️" if has_issues else "✅"
            amt = f"₹{int(float(l['loan_amount'])):,}" if l["loan_amount"] else "—"

            with st.expander(
                f"{icon}  {l['full_name']}  ·  LAN: {l['lan']}  ·  {l['loan_type']}  ·  {amt}",
                expanded=has_issues,
            ):
                ic1, ic2, ic3 = st.columns(3)
                ic1.markdown(f"**Lead ID:** `{l['id']}`")
                ic1.markdown(f"**Mobile:** {l['mobile']}")
                ic1.markdown(f"**Email:** {l['email']}")
                ic2.markdown(f"**LAN:** `{l['lan']}`")
                ic2.markdown(f"**Pushed At:** {l.get('lan_pushed_at', '—')}")
                ic2.markdown(f"**City:** {l['city']}")
                ic3.markdown(f"**PAN:** `{l['pan']}`")
                ic3.markdown(f"**Aadhaar:** `{l['aadhaar']}`")
                ic3.markdown(f"**Employment:** {l['employment']}")

                st.markdown("---")
                if issues:
                    st.markdown(f"**⚠️ Issues / Flags ({len(issues)}):**")
                    flags_html = "".join(
                        f'<span class="flag-chip red" style="font-size:0.82rem; padding:5px 12px; margin:3px;">'
                        f'⚠️ {issue}</span>'
                        for issue in issues
                    )
                    st.markdown(flags_html, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("""
                    <div class="alert-warning">
                        Please coordinate with the credit/operations team to resolve these flags.
                        The lead will be processed after all issues are cleared.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="alert-success">
                        ✅ No flags or issues detected for this lead. Processing in progress.
                    </div>
                    """, unsafe_allow_html=True)

                docs_list = st.session_state.docs.get(lid, [])
                if docs_list:
                    st.markdown(f"**📎 Documents ({len(docs_list)}):**")
                    for d in docs_list:
                        st.markdown(f"• **{d['type']}**  –  _{d['name']}_  `{d['size']}`")
                else:
                    st.markdown('<div class="alert-warning">No documents attached.</div>', unsafe_allow_html=True)


# ─── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center; padding:16px; color:{CS_GREY}; font-size:0.75rem;
            border-top:1px solid #E9ECEF; margin-top:30px;">
    Credit Saison India Pvt. Ltd.  ·  Sales Officer Portal  ·
    Internal Use Only  ·  v1.0
</div>
""", unsafe_allow_html=True)
