import streamlit as st
import pandas as pd
import uuid
import random
import base64
import os
from datetime import datetime
from io import BytesIO

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Credit Saison India – Sales Officer Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Brand Palette (extracted from Credit Saison India logo) ────────────────────
CS_TEAL      = "#00A79D"   # primary brand teal
CS_TEAL_DARK = "#007A73"   # darker teal for depth
CS_TEAL_MID  = "#009990"   # mid-teal for gradients
CS_TEAL_LIGHT= "#E6F7F6"   # very light teal for backgrounds
CS_WHITE     = "#FFFFFF"
CS_DARK      = "#1A2E2D"   # near-black with teal tint
CS_GREY      = "#6C757D"
CS_LIGHT_BG  = "#F4FAFA"   # page background
CS_GREEN     = "#28A745"
CS_AMBER     = "#E8A020"
CS_RED_FLAG  = "#D93025"   # only for alerts / flags (not brand colour)
CS_BLUE      = "#0D7EA3"

# ─── Logo Helper ────────────────────────────────────────────────────────────────
def _logo_b64() -> str:
    """Return base64 of cs_logo.png if it exists, else empty string."""
    logo_path = os.path.join(os.path.dirname(__file__), "cs_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

_LOGO_B64 = _logo_b64()
LOGO_HTML = (
    f'<img src="data:image/png;base64,{_LOGO_B64}" '
    f'style="height:54px; border-radius:6px;" alt="Credit Saison India">'
    if _LOGO_B64
    else f"""
    <div style="display:inline-flex;flex-direction:column;align-items:center;
                background:{CS_TEAL};border-radius:8px;padding:6px 14px;line-height:1.2;">
        <span style="color:{CS_WHITE};font-size:0.75rem;font-weight:800;letter-spacing:1.5px;">CREDIT</span>
        <span style="color:{CS_WHITE};font-size:0.75rem;font-weight:800;letter-spacing:1.5px;">SAISON</span>
        <span style="color:{CS_WHITE};font-size:0.65rem;font-weight:600;letter-spacing:3px; opacity:0.9;">INDIA</span>
    </div>"""
)

# ─── CSS ────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {CS_LIGHT_BG};
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {CS_DARK} 0%, {CS_TEAL_DARK} 100%);
    border-right: 3px solid {CS_TEAL};
}}
section[data-testid="stSidebar"] * {{
    color: {CS_WHITE} !important;
}}

/* ── Header ── */
.cs-header {{
    background: linear-gradient(120deg, {CS_DARK} 0%, {CS_TEAL_DARK} 55%, {CS_TEAL} 100%);
    padding: 16px 28px;
    border-radius: 14px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 24px rgba(0,167,157,0.22);
}}
.cs-header h1 {{
    color: {CS_WHITE};
    font-size: 1.55rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.3px;
}}
.cs-header .subtitle {{
    color: rgba(255,255,255,0.70);
    font-size: 0.82rem;
    margin-top: 3px;
    font-weight: 400;
}}

/* ── Metric Cards ── */
.metric-card {{
    background: {CS_WHITE};
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    border-left: 4px solid {CS_TEAL};
    transition: transform 0.15s, box-shadow 0.15s;
    height: 100%;
}}
.metric-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 18px rgba(0,167,157,0.18);
}}
.metric-card .val {{
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
    color: {CS_TEAL_DARK};
}}
.metric-card .lbl {{
    font-size: 0.72rem;
    color: {CS_GREY};
    margin-top: 5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}}

/* ── Status Badges ── */
.badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.71rem;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
.badge-punched    {{ background:#FFF3CD; color:#7A5800; }}
.badge-first      {{ background:#D1ECF1; color:#0C5460; }}
.badge-interested {{ background:#D4EDDA; color:#155724; }}
.badge-rejected   {{ background:#F8D7DA; color:#721C24; }}
.badge-reverted   {{ background:#E2D9F3; color:#4B0082; }}
.badge-moved      {{ background:#CCF0EE; color:#005B56; border:1px solid {CS_TEAL}; }}
.badge-default    {{ background:#E9ECEF; color:#495057; }}

/* ── Primary Buttons ── */
div.stButton > button {{
    background: linear-gradient(135deg, {CS_TEAL} 0%, {CS_TEAL_DARK} 100%);
    color: {CS_WHITE};
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 22px;
    font-size: 0.88rem;
    transition: all 0.2s;
    box-shadow: 0 2px 8px rgba(0,167,157,0.35);
    letter-spacing: 0.2px;
}}
div.stButton > button:hover {{
    background: linear-gradient(135deg, {CS_TEAL_MID} 0%, {CS_TEAL} 100%);
    transform: translateY(-2px);
    box-shadow: 0 5px 16px rgba(0,167,157,0.45);
}}
div.stButton > button:active {{ transform: translateY(0); }}

/* ── Section Cards ── */
.section-card {{
    background: {CS_WHITE};
    border-radius: 12px;
    padding: 22px 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    margin-bottom: 18px;
}}
.section-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: {CS_DARK};
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 2px solid {CS_TEAL};
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* ── Flag Chips ── */
.flag-chip {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    margin: 2px;
    background:#FFF3CD; color:#7A5800; border:1px solid #FFE082;
}}
.flag-chip.red   {{ background:#FDECEA; color:#7B1D1D; border-color:#F5A9A0; }}
.flag-chip.green {{ background:#E8F5E9; color:#1B5E20; border-color:#A5D6A7; }}

/* ── Alert Boxes ── */
.alert-success {{
    background:#E8F5E9; color:#1B5E20;
    border-left:4px solid {CS_GREEN};
    border-radius:8px; padding:12px 16px; margin:10px 0; font-weight:500;
}}
.alert-warning {{
    background:#FFF8E1; color:#7A5800;
    border-left:4px solid {CS_AMBER};
    border-radius:8px; padding:12px 16px; margin:10px 0; font-weight:500;
}}
.alert-info {{
    background:{CS_TEAL_LIGHT}; color:{CS_TEAL_DARK};
    border-left:4px solid {CS_TEAL};
    border-radius:8px; padding:12px 16px; margin:10px 0; font-weight:500;
}}
.alert-danger {{
    background:#FDECEA; color:#7B1D1D;
    border-left:4px solid {CS_RED_FLAG};
    border-radius:8px; padding:12px 16px; margin:10px 0; font-weight:500;
}}

/* ── File Uploader ── */
[data-testid="stFileUploaderDropzone"] {{
    border: 2px dashed {CS_TEAL} !important;
    border-radius: 10px !important;
    background: {CS_TEAL_LIGHT} !important;
}}

/* ── Inputs / Selects ── */
.stSelectbox [data-baseweb="select"] > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {{
    border-radius: 8px !important;
}}
.stSelectbox [data-baseweb="select"] > div:focus-within,
.stTextInput > div > div > input:focus {{
    border-color: {CS_TEAL} !important;
    box-shadow: 0 0 0 2px rgba(0,167,157,0.18) !important;
}}

/* ── Expander ── */
details summary {{
    font-weight: 600;
    color: {CS_DARK};
}}
details[open] summary {{
    color: {CS_TEAL_DARK};
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-thumb {{ background: {CS_TEAL}; border-radius: 4px; }}
::-webkit-scrollbar-track {{ background: #f0f0f0; }}

/* ── Footer ── */
.cs-footer {{
    text-align: center;
    padding: 16px;
    color: {CS_GREY};
    font-size: 0.74rem;
    border-top: 1px solid #E0EFEE;
    margin-top: 40px;
}}

/* ── Sidebar nav button active state ── */
section[data-testid="stSidebar"] div.stButton > button {{
    background: transparent;
    box-shadow: none;
    color: rgba(255,255,255,0.80) !important;
    text-align: left;
    font-weight: 500;
    border-radius: 8px;
    border: none;
    padding: 10px 14px;
    width: 100%;
}}
section[data-testid="stSidebar"] div.stButton > button:hover {{
    background: rgba(0,167,157,0.25) !important;
    color: {CS_WHITE} !important;
    transform: none;
    box-shadow: none;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─── Session State ───────────────────────────────────────────────────────────────
def _init():
    for k, v in {
        "leads": {}, "docs": {}, "page": "Dashboard",
        "so_name": "Rajesh Kumar", "so_branch": "Mumbai – Andheri East",
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ─── Constants ───────────────────────────────────────────────────────────────────
STATUSES   = ["First Contact","Interested","Lead Punched","Rejected","Reverted Back","Lead Moved"]
LOAN_TYPES = ["Personal Loan","Business Loan","Home Loan","LAP","Gold Loan","Two-Wheeler Loan"]
EMPLOYMENT = ["Salaried","Self-Employed","Business Owner","Freelancer"]
DOC_TYPES  = [
    "Aadhaar Card","PAN Card","Passport","Voter ID",
    "Salary Slip (Latest)","Salary Slip (Previous)","Bank Statement (3M)",
    "Bank Statement (6M)","ITR","Form 16","GST Certificate",
    "Business Proof","Property Documents","Photograph","Other",
]
ISSUE_POOL = [
    "Aadhaar Missing","PAN Name Mismatch","Bank Statement Incomplete",
    "CIBIL Score Low","Address Proof Not Matching","Photo Not Clear",
    "Salary Slip Outdated","GST Certificate Expired","ITR Not Submitted",
    "Signature Mismatch","Date of Birth Discrepancy",
]
EXCEL_COLS = [
    "Full Name","Mobile","Email","Loan Type","Loan Amount (₹)",
    "Employment Type","Monthly Income (₹)","PAN Number","Aadhaar Number",
    "City","Pincode","Notes",
]

# ─── Helpers ─────────────────────────────────────────────────────────────────────
def badge(status: str) -> str:
    cls = {
        "First Contact":"badge-first","Interested":"badge-interested",
        "Lead Punched":"badge-punched","Rejected":"badge-rejected",
        "Reverted Back":"badge-reverted","Lead Moved":"badge-moved",
    }.get(status,"badge-default")
    return f'<span class="badge {cls}">{status}</span>'

def new_lan() -> str:
    return "LAN" + str(random.randint(1000000,9999999))

def add_lead(row: dict) -> str:
    lid = str(uuid.uuid4())[:8].upper()
    st.session_state.leads[lid] = {
        "id":lid, "full_name":row.get("Full Name","—"),
        "mobile":str(row.get("Mobile","—")), "email":row.get("Email","—"),
        "loan_type":row.get("Loan Type","Personal Loan"),
        "loan_amount":row.get("Loan Amount (₹)",0),
        "employment":row.get("Employment Type","Salaried"),
        "income":row.get("Monthly Income (₹)",0),
        "pan":row.get("PAN Number","—"), "aadhaar":row.get("Aadhaar Number","—"),
        "city":row.get("City","—"), "pincode":str(row.get("Pincode","—")),
        "notes":row.get("Notes",""),
        "status":"Lead Punched",
        "created_at":datetime.now().strftime("%d %b %Y, %H:%M"),
        "lan":None, "lan_pushed_at":None, "issues":[],
    }
    st.session_state.docs[lid] = []
    return lid

def excel_template() -> bytes:
    df = pd.DataFrame([{
        "Full Name":"Amit Sharma","Mobile":"9876543210","Email":"amit@example.com",
        "Loan Type":"Personal Loan","Loan Amount (₹)":500000,"Employment Type":"Salaried",
        "Monthly Income (₹)":75000,"PAN Number":"ABCDE1234F",
        "Aadhaar Number":"1234-5678-9012","City":"Mumbai","Pincode":"400001",
        "Notes":"Good profile",
    }])
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

def fmt_amt(v) -> str:
    try:
        return f"₹{int(float(v)):,}"
    except Exception:
        return "—"


# ─── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo in sidebar
    st.markdown(f"""
    <div style="display:flex; flex-direction:column; align-items:center;
                padding: 22px 10px 14px 10px; gap:10px;">
        {LOGO_HTML}
        <div style="font-size:0.65rem; color:rgba(255,255,255,0.4);
                    letter-spacing:2px; text-transform:uppercase; margin-top:4px;">
            Sales Officer Portal
        </div>
    </div>
    <div style="height:1px; background:rgba(255,255,255,0.10); margin:0 12px 16px 12px;"></div>
    """, unsafe_allow_html=True)

    pages = {
        "📊  Dashboard":        "Dashboard",
        "➕  Upload Leads":     "Upload Leads",
        "📁  Manage Documents": "Manage Documents",
        "🚀  Push to LAN":      "Push to LAN",
        "⚠️  Flags & Issues":   "Flags & Issues",
    }
    for label, key in pages.items():
        active = st.session_state.page == key
        bg     = f"background:rgba(0,167,157,0.30); border-left:3px solid {CS_TEAL}; border-radius:8px;" if active else ""
        # use a lightweight HTML link-style button
        clicked = st.button(label, key=f"nav_{key}", use_container_width=True)
        if clicked:
            st.session_state.page = key
            st.rerun()

    st.markdown(f"""
    <div style="height:1px; background:rgba(255,255,255,0.10); margin:16px 12px 14px 12px;"></div>
    <div style="padding:12px 10px; background:rgba(255,255,255,0.07); border-radius:8px; margin:0 4px;">
        <div style="font-size:0.68rem; color:rgba(255,255,255,0.45); margin-bottom:4px; letter-spacing:0.5px;">
            LOGGED IN AS
        </div>
        <div style="font-weight:700; font-size:0.88rem; color:{CS_WHITE};">
            {st.session_state.so_name}
        </div>
        <div style="font-size:0.74rem; color:rgba(255,255,255,0.55); margin-top:2px;">
            {st.session_state.so_branch}
        </div>
        <div style="font-size:0.68rem; color:rgba(255,255,255,0.35); margin-top:8px;">
            {datetime.now().strftime("%d %b %Y  ·  %H:%M")}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Page Header ─────────────────────────────────────────────────────────────────
PAGE_META = {
    "Dashboard":        ("📊", "Lead Dashboard"),
    "Upload Leads":     ("➕", "Upload Leads from Excel"),
    "Manage Documents": ("📁", "Manage Lead Documents"),
    "Push to LAN":      ("🚀", "Push Leads to LAN"),
    "Flags & Issues":   ("⚠️", "Flags & Issues"),
}
icon, title = PAGE_META.get(st.session_state.page, ("🏦", st.session_state.page))
st.markdown(f"""
<div class="cs-header">
    <div>
        <h1>{icon} {title}</h1>
        <div class="subtitle">Credit Saison India · Internal Sales Officer Portal</div>
    </div>
    {LOGO_HTML}
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Dashboard":

    leads = st.session_state.leads
    by_s  = {}
    for l in leads.values():
        by_s[l["status"]] = by_s.get(l["status"], 0) + 1

    # ── Metrics ──
    m_data = [
        ("Total Leads",   len(leads),                       CS_TEAL),
        ("Lead Punched",  by_s.get("Lead Punched",  0),     CS_AMBER),
        ("Interested",    by_s.get("Interested",    0),     CS_GREEN),
        ("First Contact", by_s.get("First Contact", 0),     CS_BLUE),
        ("Reverted Back", by_s.get("Reverted Back", 0),     "#7B61C4"),
        ("Lead Moved",    by_s.get("Lead Moved",    0),     CS_TEAL_DARK),
    ]
    cols = st.columns(6)
    for col, (lbl, val, color) in zip(cols, m_data):
        col.markdown(f"""
        <div class="metric-card" style="border-left-color:{color};">
            <div class="val" style="color:{color};">{val}</div>
            <div class="lbl">{lbl}</div>
        </div><br>
        """, unsafe_allow_html=True)

    # ── Filters ──
    fc1, fc2, fc3, fc4 = st.columns([2.5, 1.5, 1.5, 1])
    search   = fc1.text_input("", placeholder="🔍  Search by name, mobile, PAN…", label_visibility="collapsed")
    f_status = fc2.selectbox("", ["All Statuses"] + STATUSES, label_visibility="collapsed")
    f_loan   = fc3.selectbox("", ["All Loan Types"] + LOAN_TYPES, label_visibility="collapsed")
    if fc4.button("＋ Add Lead", use_container_width=True):
        st.session_state.page = "Upload Leads"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filter ──
    filtered = [
        l for l in leads.values()
        if (not search or search.lower() in (l["full_name"]+l["mobile"]+l["pan"]).lower())
        and (f_status == "All Statuses" or l["status"] == f_status)
        and (f_loan   == "All Loan Types" or l["loan_type"] == f_loan)
    ]

    if not filtered:
        st.markdown(f"""
        <div style="text-align:center; padding:64px 20px; background:{CS_WHITE};
                    border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.06);">
            <div style="font-size:3rem;">📋</div>
            <div style="font-size:1.1rem; font-weight:700; color:{CS_DARK}; margin-top:14px;">
                No leads found
            </div>
            <div style="color:{CS_GREY}; margin-top:6px; font-size:0.88rem;">
                Upload leads from Excel or adjust your filters above
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Table ──
        st.markdown(f"""
        <div style="background:{CS_WHITE}; border-radius:12px; overflow:hidden;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07); margin-bottom:10px;">
        <table style="width:100%; border-collapse:collapse; font-size:0.82rem;">
            <thead>
            <tr style="background:{CS_DARK}; color:{CS_WHITE};">
                <th style="padding:12px 14px; font-weight:600; text-align:left;">Lead ID</th>
                <th style="padding:12px 14px; font-weight:600; text-align:left;">Name</th>
                <th style="padding:12px 14px; font-weight:600; text-align:left;">Mobile</th>
                <th style="padding:12px 14px; font-weight:600; text-align:left;">Loan Type</th>
                <th style="padding:12px 14px; font-weight:600; text-align:right;">Amount</th>
                <th style="padding:12px 14px; font-weight:600; text-align:left;">City</th>
                <th style="padding:12px 14px; font-weight:600; text-align:center;">Status</th>
                <th style="padding:12px 14px; font-weight:600; text-align:left;">Created</th>
                <th style="padding:12px 14px; font-weight:600; text-align:left;">LAN</th>
                <th style="padding:12px 14px; font-weight:600; text-align:center;">Flags</th>
            </tr>
            </thead><tbody>
        """, unsafe_allow_html=True)

        for i, l in enumerate(filtered):
            bg = CS_WHITE if i % 2 == 0 else CS_TEAL_LIGHT
            lan_d  = l["lan"] or "—"
            n_flag = len(l.get("issues", []))
            f_html = (f'<span style="color:#7B1D1D;font-weight:700;">{n_flag} ⚠</span>'
                      if n_flag else f'<span style="color:{CS_TEAL_DARK};">✔ Clear</span>')
            st.markdown(f"""
            <tr style="background:{bg}; border-bottom:1px solid #EEF6F6;">
                <td style="padding:11px 14px; font-family:monospace; color:{CS_TEAL_DARK}; font-weight:700;">{l['id']}</td>
                <td style="padding:11px 14px; font-weight:600;">{l['full_name']}</td>
                <td style="padding:11px 14px; color:#555;">{l['mobile']}</td>
                <td style="padding:11px 14px;">{l['loan_type']}</td>
                <td style="padding:11px 14px; text-align:right; font-weight:600;">{fmt_amt(l['loan_amount'])}</td>
                <td style="padding:11px 14px;">{l['city']}</td>
                <td style="padding:11px 14px; text-align:center;">{badge(l['status'])}</td>
                <td style="padding:11px 14px; color:#888; font-size:0.76rem;">{l['created_at']}</td>
                <td style="padding:11px 14px; font-family:monospace; color:{CS_BLUE}; font-size:0.79rem;">{lan_d}</td>
                <td style="padding:11px 14px; text-align:center;">{f_html}</td>
            </tr>
            """, unsafe_allow_html=True)

        st.markdown("</tbody></table></div>", unsafe_allow_html=True)

        # ── Expandable Detail / Edit ──
        st.markdown(f"<div style='color:{CS_GREY}; font-size:0.82rem; margin:14px 0 8px 0;'>▾  Click a lead to view or edit details</div>", unsafe_allow_html=True)
        for l in filtered:
            with st.expander(f"  {l['full_name']}   ·   {l['id']}   ·   {l['status']}", expanded=False):
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.markdown(f"<div style='font-weight:700; color:{CS_TEAL_DARK}; margin-bottom:6px;'>Personal</div>", unsafe_allow_html=True)
                    st.write(f"📞 {l['mobile']}")
                    st.write(f"✉️ {l['email']}")
                    st.write(f"🏙️ {l['city']}  –  {l['pincode']}")
                with d2:
                    st.markdown(f"<div style='font-weight:700; color:{CS_TEAL_DARK}; margin-bottom:6px;'>Loan</div>", unsafe_allow_html=True)
                    st.write(f"💼 {l['loan_type']}")
                    st.write(f"💰 {fmt_amt(l['loan_amount'])}")
                    st.write(f"👔 {l['employment']}")
                    st.write(f"💵 {fmt_amt(l['income'])}/mo")
                with d3:
                    st.markdown(f"<div style='font-weight:700; color:{CS_TEAL_DARK}; margin-bottom:6px;'>KYC</div>", unsafe_allow_html=True)
                    st.write(f"🪪 PAN: `{l['pan']}`")
                    st.write(f"🆔 Aadhaar: `{l['aadhaar']}`")
                    if l.get("lan"):
                        st.write(f"🏷️ LAN: `{l['lan']}`")

                if l.get("notes"):
                    st.info(f"📝 {l['notes']}")

                if l.get("issues"):
                    chips = " ".join(f'<span class="flag-chip red">⚠ {f}</span>' for f in l["issues"])
                    st.markdown(f"**Flags:** {chips}", unsafe_allow_html=True)

                docs = st.session_state.docs.get(l["id"], [])
                if docs:
                    st.markdown(f"**📎 Documents ({len(docs)}):**")
                    for d in docs:
                        st.write(f"• {d['name']}  `{d['type']}`  –  _{d['uploaded_at']}_")

                # Edit (locked after move)
                if l["status"] != "Lead Moved":
                    st.markdown("---")
                    st.markdown(f"<span style='font-weight:700; color:{CS_TEAL_DARK};'>✏️ Edit Details</span>", unsafe_allow_html=True)
                    ec1, ec2 = st.columns(2)
                    n_name   = ec1.text_input("Full Name",   value=l["full_name"],  key=f"e_nm_{l['id']}")
                    n_mobile = ec2.text_input("Mobile",      value=l["mobile"],     key=f"e_mb_{l['id']}")
                    n_email  = ec1.text_input("Email",       value=l["email"],      key=f"e_em_{l['id']}")
                    n_city   = ec2.text_input("City",        value=l["city"],       key=f"e_ct_{l['id']}")
                    n_loan   = st.selectbox("Loan Type", LOAN_TYPES,
                                            index=LOAN_TYPES.index(l["loan_type"]) if l["loan_type"] in LOAN_TYPES else 0,
                                            key=f"e_lt_{l['id']}")
                    n_notes  = st.text_area("Notes", value=l["notes"], key=f"e_nt_{l['id']}", height=68)
                    if st.button("💾 Save", key=f"sv_{l['id']}"):
                        st.session_state.leads[l["id"]].update({
                            "full_name":n_name, "mobile":n_mobile,
                            "email":n_email,    "city":n_city,
                            "loan_type":n_loan, "notes":n_notes,
                        })
                        st.success("Lead updated.")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD LEADS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Upload Leads":

    left, right = st.columns([1.8, 1])

    with left:
        st.markdown(f'<div class="alert-info">📌  Upload a standard Excel file. Each row = one lead. Download the template to get started.</div>', unsafe_allow_html=True)

        tc, _ = st.columns([1, 3])
        tc.download_button("⬇️ Download Template", data=excel_template(),
                           file_name="CS_Lead_Template.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        uploaded = st.file_uploader("", type=["xlsx","xls"], label_visibility="collapsed")

        if uploaded:
            try:
                df = pd.read_excel(uploaded)
                missing = [c for c in EXCEL_COLS if c not in df.columns]
                if missing:
                    st.markdown(f'<div class="alert-warning">⚠️ Missing columns: {", ".join(missing)}</div>', unsafe_allow_html=True)
                else:
                    df = df.dropna(subset=["Full Name"])
                    st.markdown(f'<div class="alert-success">✅ {len(df)} lead(s) ready to import.</div>', unsafe_allow_html=True)
                    st.dataframe(df, use_container_width=True, height=260)
                    if st.button(f"➕ Import {len(df)} Lead(s) to Dashboard", use_container_width=True):
                        for _, row in df.iterrows():
                            add_lead(row.to_dict())
                        st.success(f"✅ {len(df)} lead(s) added!")
                        st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown(f"<div style='height:1px;background:#E0EFEE;margin:22px 0;'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">✍️ Add Single Lead Manually</div>', unsafe_allow_html=True)

        with st.form("manual_form", clear_on_submit=True):
            a1, a2 = st.columns(2)
            m_name   = a1.text_input("Full Name *")
            m_mobile = a2.text_input("Mobile *")
            m_email  = a1.text_input("Email")
            m_city   = a2.text_input("City")
            m_loan   = a1.selectbox("Loan Type", LOAN_TYPES)
            m_amt    = a2.number_input("Loan Amount (₹)", min_value=0, step=10000)
            m_emp    = a1.selectbox("Employment Type", EMPLOYMENT)
            m_income = a2.number_input("Monthly Income (₹)", min_value=0, step=1000)
            m_pan    = a1.text_input("PAN Number")
            m_aadh   = a2.text_input("Aadhaar Number")
            m_pin    = a1.text_input("Pincode")
            m_notes  = st.text_area("Notes", height=68)
            sub      = st.form_submit_button("➕ Add Lead", use_container_width=True)
            if sub:
                if not m_name or not m_mobile:
                    st.error("Full Name and Mobile are required.")
                else:
                    add_lead({
                        "Full Name":m_name,"Mobile":m_mobile,"Email":m_email,
                        "Loan Type":m_loan,"Loan Amount (₹)":m_amt,
                        "Employment Type":m_emp,"Monthly Income (₹)":m_income,
                        "PAN Number":m_pan,"Aadhaar Number":m_aadh,
                        "City":m_city,"Pincode":m_pin,"Notes":m_notes,
                    })
                    st.success(f"Lead for {m_name} added!")
                    st.rerun()

    with right:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">📋 Required Excel Columns</div>
            {''.join(f'<div style="padding:5px 0; border-bottom:1px solid {CS_TEAL_LIGHT}; font-size:0.82rem;"><code>{c}</code></div>' for c in EXCEL_COLS)}
        </div>
        <div class="section-card" style="margin-top:16px;">
            <div class="section-title">💡 Tips</div>
            <ul style="font-size:0.83rem; color:{CS_GREY}; padding-left:18px; line-height:1.9;">
                <li>Each Excel row = one loan lead</li>
                <li>Multiple leads in a single upload</li>
                <li>All new leads land as <b>Lead Punched</b></li>
                <li>Attach docs in <b>Manage Documents</b></li>
                <li>Submit via <b>Push to LAN</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MANAGE DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Manage Documents":

    leads = st.session_state.leads
    active = {lid:l for lid,l in leads.items() if l["status"] != "Lead Moved"}

    if not active:
        st.markdown('<div class="alert-info">No active leads. Upload leads first.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-info">Select a lead and attach documents. Multiple document types supported per lead.</div>', unsafe_allow_html=True)

        opts = {f"{l['full_name']}  [{lid}]  ·  {l['loan_type']}": lid for lid,l in active.items()}
        sel_lbl = st.selectbox("Select Lead", list(opts.keys()))
        sel_lid = opts[sel_lbl]
        sel_l   = leads[sel_lid]

        cup, cdocs = st.columns([1.3, 1])

        with cup:
            st.markdown(f'<div class="section-title">📤 Upload Document — {sel_l["full_name"]}</div>', unsafe_allow_html=True)
            doc_type = st.selectbox("Document Type", DOC_TYPES, key="doc_type_sel")
            doc_file = st.file_uploader("Upload (PDF / JPG / PNG)", type=["pdf","jpg","jpeg","png"],
                                        key=f"upf_{sel_lid}", label_visibility="collapsed")
            if doc_file:
                if st.button("📎 Attach Document", use_container_width=True):
                    st.session_state.docs[sel_lid].append({
                        "name": doc_file.name, "type": doc_type,
                        "size": f"{doc_file.size/1024:.1f} KB",
                        "uploaded_at": datetime.now().strftime("%d %b %Y, %H:%M"),
                    })
                    st.success(f"✅ Attached: {doc_file.name}")
                    st.rerun()

        with cdocs:
            st.markdown(f'<div class="section-title">📁 Attached Documents</div>', unsafe_allow_html=True)
            dl = st.session_state.docs.get(sel_lid, [])
            if not dl:
                st.markdown('<div class="alert-warning">No documents attached yet.</div>', unsafe_allow_html=True)
            else:
                for i, d in enumerate(dl):
                    r1, r2 = st.columns([5, 1])
                    r1.markdown(f"""
                    <div style="background:{CS_TEAL_LIGHT}; border-radius:8px; padding:10px 12px;
                                margin-bottom:8px; border-left:3px solid {CS_TEAL};">
                        <div style="font-weight:600; font-size:0.82rem;">{d['name']}</div>
                        <div style="font-size:0.74rem; color:{CS_GREY};">{d['type']}  ·  {d['size']}  ·  {d['uploaded_at']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if r2.button("🗑", key=f"deld_{sel_lid}_{i}"):
                        st.session_state.docs[sel_lid].pop(i)
                        st.rerun()

        # Bulk upload
        st.markdown(f"<div style='height:1px;background:#E0EFEE;margin:22px 0;'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📂 Bulk Upload — Same Document to Multiple Leads</div>', unsafe_allow_html=True)
        bulk_map  = {f"{l['full_name']}  [{lid}]": lid for lid,l in active.items()}
        bulk_sel  = st.multiselect("Select Leads", list(bulk_map.keys()))
        bulk_type = st.selectbox("Document Type", DOC_TYPES, key="bulk_type")
        bulk_file = st.file_uploader("Upload File", type=["pdf","jpg","jpeg","png"],
                                     key="bulk_file", label_visibility="collapsed")
        if bulk_file and bulk_sel:
            if st.button(f"📎 Attach to {len(bulk_sel)} Lead(s)", use_container_width=False):
                for lbl in bulk_sel:
                    lid_b = bulk_map[lbl]
                    st.session_state.docs[lid_b].append({
                        "name": bulk_file.name, "type": bulk_type,
                        "size": f"{bulk_file.size/1024:.1f} KB",
                        "uploaded_at": datetime.now().strftime("%d %b %Y, %H:%M"),
                    })
                st.success(f"✅ Attached to {len(bulk_sel)} lead(s).")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PUSH TO LAN
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Push to LAN":

    leads     = st.session_state.leads
    eligible  = {lid:l for lid,l in leads.items() if l["status"] == "Lead Punched"}

    st.markdown(f"""
    <div class="alert-info">
        Select one or more <b>Lead Punched</b> leads and click <b>Push to LAN</b>.
        All selected leads are submitted simultaneously and moved out of your bucket.
    </div>
    """, unsafe_allow_html=True)

    if not eligible:
        st.markdown(f"""
        <div style="text-align:center; padding:56px 20px; background:{CS_WHITE}; border-radius:14px;
                    box-shadow:0 2px 10px rgba(0,0,0,0.06);">
            <div style="font-size:2.8rem;">🎉</div>
            <div style="font-size:1.1rem; font-weight:700; color:{CS_DARK}; margin-top:14px;">
                No leads pending LAN push
            </div>
            <div style="color:{CS_GREY}; margin-top:6px; font-size:0.88rem;">
                All leads have been submitted or there are no Lead Punched leads.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        lead_opts = {}
        for lid, l in eligible.items():
            dc = len(st.session_state.docs.get(lid, []))
            lead_opts[f"{l['full_name']}  ·  {l['loan_type']}  ·  {fmt_amt(l['loan_amount'])}  ·  📎 {dc} doc(s)  [{lid}]"] = lid

        sel_push = st.multiselect("Select leads to push:", list(lead_opts.keys()),
                                  default=list(lead_opts.keys()))

        if sel_push:
            rows = []
            for lbl in sel_push:
                lid = lead_opts[lbl]
                l   = leads[lid]
                dc  = len(st.session_state.docs.get(lid, []))
                rows.append({
                    "Lead ID":l["id"], "Name":l["full_name"], "Loan Type":l["loan_type"],
                    "Amount":fmt_amt(l["loan_amount"]), "City":l["city"],
                    "Documents":f"{dc} attached",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            no_docs = [lbl for lbl in sel_push if not st.session_state.docs.get(lead_opts[lbl])]
            if no_docs:
                st.markdown(f'<div class="alert-warning">⚠️ {len(no_docs)} lead(s) have no documents attached. Recommended to upload docs before pushing.</div>', unsafe_allow_html=True)

            confirm = st.checkbox(f"I confirm push of {len(sel_push)} lead(s) to LAN")
            if confirm:
                if st.button(f"🚀 Push {len(sel_push)} Lead(s) to LAN", use_container_width=False):
                    results = []
                    for lbl in sel_push:
                        lid    = lead_opts[lbl]
                        lan    = new_lan()
                        issues = random.sample(ISSUE_POOL, random.randint(0, 3))
                        st.session_state.leads[lid].update({
                            "status":"Lead Moved", "lan":lan,
                            "lan_pushed_at":datetime.now().strftime("%d %b %Y, %H:%M"),
                            "issues":issues,
                        })
                        results.append((leads[lid]["full_name"], lan, issues))

                    st.markdown(f'<div class="alert-success">✅ {len(results)} lead(s) pushed to LAN!</div>', unsafe_allow_html=True)
                    for name, lan, issues in results:
                        chips = "".join(f'<span class="flag-chip red">⚠ {f}</span>' for f in issues) or f'<span class="flag-chip green">✔ No Issues</span>'
                        st.markdown(f"""
                        <div style="background:{CS_WHITE}; border-radius:9px; padding:12px 16px; margin:5px 0;
                                    box-shadow:0 1px 6px rgba(0,0,0,0.08); border-left:4px solid {CS_TEAL};">
                            <span style="font-weight:700;">{name}</span>
                            <span style="font-family:monospace; color:{CS_TEAL_DARK};
                                         font-size:0.82rem; margin:0 10px;">{lan}</span>
                            {chips}
                        </div>
                        """, unsafe_allow_html=True)
                    st.rerun()
        else:
            st.markdown('<div class="alert-warning">Please select at least one lead.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FLAGS & ISSUES
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Flags & Issues":

    leads = st.session_state.leads
    moved = {lid:l for lid,l in leads.items() if l["status"] == "Lead Moved"}

    total_m   = len(moved)
    with_iss  = sum(1 for l in moved.values() if l.get("issues"))
    clear_ct  = total_m - with_iss

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""<div class="metric-card" style="border-left-color:{CS_BLUE};">
        <div class="val" style="color:{CS_BLUE};">{total_m}</div>
        <div class="lbl">Moved to LAN</div></div><br>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-card" style="border-left-color:{CS_RED_FLAG};">
        <div class="val" style="color:{CS_RED_FLAG};">{with_iss}</div>
        <div class="lbl">With Flags</div></div><br>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="metric-card" style="border-left-color:{CS_GREEN};">
        <div class="val" style="color:{CS_GREEN};">{clear_ct}</div>
        <div class="lbl">Clear – No Issues</div></div><br>""", unsafe_allow_html=True)

    if not moved:
        st.markdown('<div class="alert-info">No leads pushed to LAN yet. Use <b>Push to LAN</b> to submit leads.</div>', unsafe_allow_html=True)
    else:
        f_opt = st.radio("", ["All","With Issues","No Issues"], horizontal=True, label_visibility="collapsed")

        for lid, l in moved.items():
            issues = l.get("issues", [])
            if f_opt == "With Issues" and not issues:  continue
            if f_opt == "No Issues"   and issues:      continue

            border = CS_RED_FLAG if issues else CS_GREEN
            ico    = "⚠️" if issues else "✅"

            with st.expander(f"{ico}  {l['full_name']}   ·   LAN: {l['lan']}   ·   {l['loan_type']}   ·   {fmt_amt(l['loan_amount'])}", expanded=bool(issues)):
                d1, d2, d3 = st.columns(3)
                d1.markdown(f"**Lead ID:** `{l['id']}`")
                d1.markdown(f"**Mobile:** {l['mobile']}")
                d1.markdown(f"**Email:** {l['email']}")
                d2.markdown(f"**LAN:** `{l['lan']}`")
                d2.markdown(f"**Pushed:** {l.get('lan_pushed_at','—')}")
                d2.markdown(f"**City:** {l['city']}")
                d3.markdown(f"**PAN:** `{l['pan']}`")
                d3.markdown(f"**Aadhaar:** `{l['aadhaar']}`")
                d3.markdown(f"**Employment:** {l['employment']}")

                st.markdown("---")
                if issues:
                    st.markdown(f"**⚠️ Flags / Issues ({len(issues)}):**")
                    chips = " ".join(f'<span class="flag-chip red" style="font-size:0.8rem;padding:5px 12px;">⚠ {f}</span>' for f in issues)
                    st.markdown(chips, unsafe_allow_html=True)
                    st.markdown(f'<div class="alert-warning" style="margin-top:12px;">Please coordinate with the credit / operations team to resolve these flags before further processing.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-success">✅ No flags detected. Lead is being processed.</div>', unsafe_allow_html=True)

                docs = st.session_state.docs.get(lid, [])
                if docs:
                    st.markdown(f"**📎 Documents ({len(docs)}):**")
                    for d in docs:
                        st.markdown(f"• **{d['type']}**  –  _{d['name']}_  `{d['size']}`")
                else:
                    st.markdown('<div class="alert-warning">No documents attached.</div>', unsafe_allow_html=True)


# ─── Footer ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="cs-footer">
    {LOGO_HTML}
    <div style="margin-top:10px;">
        Credit Saison India Pvt. Ltd. &nbsp;·&nbsp; Sales Officer Portal &nbsp;·&nbsp;
        Internal Use Only &nbsp;·&nbsp; v2.0
    </div>
</div>
""", unsafe_allow_html=True)
