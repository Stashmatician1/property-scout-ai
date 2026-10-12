import os
from pathlib import Path

import pandas as pd # type: ignore
import requests
import streamlit as st

APP_TITLE = "Mumbai Property Valuation AI"

# ==================================================
# PAGE CONFIG (must be the first Streamlit call)
# ==================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================
# BACKEND URL (set API_BASE_URL in your host's
# environment variables or Streamlit secrets)
# ==================================================


def get_base_url():
    url = os.getenv("API_BASE_URL")
    if not url:
        try:
            url = st.secrets.get("API_BASE_URL")
        except Exception:
            url = None
    return (url or "http://127.0.0.1:8000").rstrip("/")


BASE_URL = get_base_url()
API_URL = f"{BASE_URL}/analyze-property"
HEALTH_URL = f"{BASE_URL}/"
PAYMENT_URL = f"{BASE_URL}/payment"

# ==================================================
# METRIC CARD
# ==================================================


def metric_card(title, value, icon):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{icon}<br>{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# GLOBAL CSS
# ==================================================

st.markdown(
    """
<style>
.premium-card{position:sticky;top:20px;background:white;border-radius:16px;padding:20px;box-shadow:0px 8px 25px rgba(0,0,0,.08);}
.premium-title{font-size:24px;font-weight:bold;}
.premium-price{font-size:34px;color:#2563EB;font-weight:bold;margin-top:20px;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
/* APP BACKGROUND */
.stApp{background:#f8fafc;color:#0f172a;}
.stApp::before{content:"";position:fixed;top:-250px;right:-250px;width:700px;height:700px;
  background:radial-gradient(rgba(59,130,246,.18),transparent 70%);filter:blur(120px);pointer-events:none;z-index:0;}
.stTabs [data-baseweb="tab"]{color:#000000 !important;font-weight:700 !important;font-size:18px !important;}
.stMetric{color:#000000 !important;}
.stMarkdown{color:#000000 !important;}
.stCaption{color:#374151 !important;}
div[data-testid="stMetricValue"]{color:#000000 !important;font-weight:800 !important;}
div[data-testid="stMetricLabel"]{color:#1f2937 !important;font-weight:700 !important;}

/* SIDEBAR */
section[data-testid="stSidebar"]{background:#ffffff;color:#000000;border-right:2px solid #d1d5db;}

/* MAIN CONTAINER */
.stInfo,.stSuccess,.stWarning{font-size:18px !important;font-weight:600 !important;}
.block-container{padding-top:1.5rem;padding-bottom:2rem;max-width:1400px;}
h1,h2,h3,h4,h5,h6,p,span,label{color:#0f172a !important;}

/* BUTTONS */
.stButton button{width:100%;height:55px;font-size:20px;font-weight:700;border-radius:14px;border:none;
  background:linear-gradient(90deg,#22c55e,#4ade80);color:white;box-shadow:0 10px 20px rgba(34,197,94,.25);}
.stButton button:hover{transform:translateY(-3px);transition:all .25s ease;box-shadow:0 15px 30px rgba(34,197,94,.35);}

/* METRIC CARDS */
.metric-card{background:linear-gradient(145deg,#16365f,#234f82);border-radius:22px;padding:25px;text-align:center;
  border:1px solid rgba(255,255,255,.08);box-shadow:0 15px 35px rgba(0,0,0,.35);backdrop-filter:blur(12px);
  min-height:160px;transition:all .3s ease;}
.metric-card:hover{transform:translateY(-6px);box-shadow:0 25px 50px rgba(0,0,0,.45);}
.metric-label{color:#475569;font-size:18px;margin-bottom:12px;}
.metric-value{color:#0f172a;font-size:46px;font-weight:800;}

/* SNAPSHOT / VERDICT CARDS */
.snapshot-card{background:linear-gradient(145deg,#122a47,#18395f);border-radius:18px;padding:25px;
  border:1px solid rgba(255,255,255,.08);box-shadow:0 10px 25px rgba(0,0,0,.25);}
.verdict-card{background:linear-gradient(145deg,#154528,#1d6339);border:1px solid #2c7a4b;border-radius:18px;
  padding:30px;text-align:center;box-shadow:0 12px 25px rgba(0,0,0,.25);}
.stSuccess{border-radius:14px;}
.gold-text{background:linear-gradient(90deg,#fbbf24,#fde68a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}

/* HERO */
.hero-container{background:linear-gradient(135deg,#0f172a,#1e3a8a,#2563eb);border-radius:25px;padding:45px;
  margin-bottom:30px;color:white;box-shadow:0px 20px 40px rgba(0,0,0,0.25);}
.hero-title{font-size:54px;font-weight:900;color:white !important;margin-bottom:10px;}
.hero-subtitle{font-size:28px;font-weight:700;color:#dbeafe !important;margin-bottom:18px;}
.hero-text{font-size:18px;color:#e2e8f0 !important;line-height:1.7;}
.hero-badge{display:inline-block;background:#22c55e;color:white;padding:8px 18px;border-radius:30px;
  font-size:15px;font-weight:700;margin-bottom:20px;}
.hero-feature{font-size:18px;margin-top:10px;}
</style>
""",
    unsafe_allow_html=True,
)

# ==================================================
# SESSION STATE
# ==================================================

if "property_data" not in st.session_state:
    st.session_state.property_data = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None

# TODO: set to True ONLY after the backend verifies a Razorpay payment
# (call /api/verify-payment). Never unlock from a URL parameter alone.
if "premium_unlocked" not in st.session_state:
    st.session_state.premium_unlocked = False

# ==================================================
# HELPERS
# ==================================================


def g(d, k, default=None):
    return d.get(k, default) if isinstance(d, dict) else default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def clamp01(value):
    return min(max(value, 0.0), 1.0)


def extract_error(response):
    """Turn a failed API response into a short, user-friendly message."""
    if response.status_code == 404 and "Application not found" in response.text:
        return "The analysis service is offline. Please try again shortly."
    try:
        body = response.json()
        if isinstance(body, dict):
            msg = body.get("message") or body.get("detail")
            if msg:
                return str(msg)
    except ValueError:
        pass
    return (response.text or "")[:300] or f"HTTP {response.status_code}"


@st.cache_data(ttl=30, show_spinner=False)
def api_status(url):
    try:
        return requests.get(url, timeout=5).status_code
    except requests.RequestException:
        return None


def show_verdict(verdict):
    v = str(verdict).upper()
    if "BUY" in v:
        st.success(f"✅ Recommendation: {verdict}")
    elif v == "HOLD":
        st.warning(f"🟠 Recommendation: {verdict}")
    else:
        st.error(f"🔴 Recommendation: {verdict}")


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.title("🏠 Property Value Engine")
    st.caption("Find Fair Value • Assess Risk • Make Smarter Property Investments")
    st.divider()

    for item in [
        "Should I Buy This Property?",
        "Can I Afford It?",
        "What Is It Worth?",
        "How Risky Is It?",
        "Expected Return Potential",
        "AI Investment Verdict",
    ]:
        st.write(f"✓ {item}")

    st.divider()

    status = api_status(HEALTH_URL)
    if status is None:
        st.error("API Offline")
    elif 200 <= status < 300:
        st.success("FastAPI Running")
    else:
        st.warning(f"API Responded: {status}")

    st.caption("Tip: upload a property PDF first, then generate the report.")

# ==================================================
# HEADER
# ==================================================

st.title("🏠 Property Value Engine")

st.markdown("### Is It Actually Worth The Price?\n India edition ")

st.info(
    "📄 Upload a property brochure (PDF), complete your buyer profile, "
    "then click **Generate Investment Report** to receive an AI-powered "
    "investment analysis."
)

st.caption(
    "Upload a Property Brochure • Discover Fair Market Value • "
    "Evaluate Investment Potential • Reduce Buying Risk"
)

# ==================================================
# HERO / IMAGES
# ==================================================

skyline_col, property_col = st.columns([2, 1])

with skyline_col:
    skyline_path = Path("assets/mumbai_skyline.jpg")
    if skyline_path.exists():
        st.image(str(skyline_path), width=750)
    else:
        st.info("Add `assets/mumbai_skyline.jpg` to show the skyline hero image.")

with property_col:
    st.subheader("🏠 Property Image")
    uploaded_image = st.file_uploader(
        "Upload Property Image",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )

    if uploaded_image:
        st.image(uploaded_image, width="stretch")
    else:
        st.caption("Optional: upload a property photo for reference.")

# ==================================================
# BUYER PROFILE
# ==================================================

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("👤 Buyer Profile")

c1, c2, c3 = st.columns(3)

with c1:
    monthly_income = st.number_input(
        "Monthly Income (₹)",
        min_value=0.0,
        value=100000.0,
        step=10000.0,
        format="%.2f",
    )

with c2:
    existing_emi = st.number_input(
        "Existing EMI (₹)",
        min_value=0.0,
        value=0.0,
        step=5000.0,
        format="%.2f",
    )

with c3:
    down_payment = st.number_input(
        "Down Payment (₹)",
        min_value=0.0,
        value=1000000.0,
        step=100000.0,
        format="%.2f",
    )

# ==================================================
# PROPERTY DOCUMENT
# ==================================================

st.subheader("📄 Property Document")

uploaded_file = st.file_uploader(
    "Upload Property PDF",
    type=["pdf", "txt"],
    help=(
        "Upload a property brochure, title report, "
        "sales document, or due diligence PDF or TXT file."
    ),
)

if uploaded_file:
    st.success(f"Loaded: {uploaded_file.name}")
    st.caption(f"File Size: {uploaded_file.size / 1024:.1f} KB")

# ==================================================
# ANALYZE PROPERTY
# ==================================================

st.divider()

left, right = st.columns([1, 3])

with left:
    run_analysis = st.button(
        "🚀 Generate Investment Report",
        width="stretch",
    )

with right:
    st.caption(
        "AI analyzes the uploaded property document "
        "along with your buyer profile to produce "
        "an investment report."
    )

# ==================================================
# RUN ANALYSIS
# ==================================================

if run_analysis:

    if uploaded_file is None:
        st.warning("Please upload a property PDF first.")

    else:
        try:
            with st.spinner("Analyzing property document..."):
                response = requests.post(
                    API_URL,
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    },
                    data={
                        "monthly_income": monthly_income,
                        "existing_emi": existing_emi,
                        "down_payment": down_payment,
                    },
                    timeout=300,
                )

            if response.status_code == 200:
                try:
                    st.session_state.property_data = response.json()
                    st.session_state.last_error = None
                    st.success("✅ Analysis complete.")
                except ValueError:
                    st.session_state.property_data = None
                    st.session_state.last_error = "API returned invalid JSON."
                    st.error(st.session_state.last_error)

            else:
                error_message = extract_error(response)
                st.session_state.property_data = None
                st.session_state.last_error = error_message
                st.error(f"API Error: {error_message}")

        except requests.Timeout:
            st.session_state.property_data = None
            st.error("Request timed out.")

        except requests.ConnectionError:
            st.session_state.property_data = None
            st.error("Cannot connect to the analysis service.")

        except requests.RequestException as e:
            st.session_state.property_data = None
            st.error(f"Connection Error: {e}")

        except Exception as e:
            st.session_state.property_data = None
            st.error(f"Unexpected Error: {e}")

# ==================================================
# RESULTS
# ==================================================

data = st.session_state.property_data

if data:

    scores = g(data, "scores", {})
    investment = safe_float(g(scores, "investment", 0))
    risk_score = safe_float(g(scores, "risk", 0))
    grade = g(data, "grade", "N/A")
    confidence = safe_int(g(data, "confidence", 0))
    verdict = g(data, "verdict", "HOLD")

    dashboard_col, premium_col = st.columns([4, 1], gap="large")

    # ------------------------------------------------
    # LEFT: DASHBOARD
    # ------------------------------------------------
    with dashboard_col:

        st.markdown("## 📊 Investment Dashboard")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 Investment", f"{investment:.0f}")
        m2.metric("⚠ Risk", f"{risk_score:.0f}")
        m3.metric("⭐ Grade", grade)
        m4.metric("🎯 Confidence", f"{confidence}%")

        st.divider()

        st.subheader("📌 Investment Recommendation")
        show_verdict(verdict)

        st.subheader("📈 Investment Potential")
        st.metric("Investment Score", f"{investment:.1f}/100")
        st.progress(clamp01(investment / 100))

        if investment >= 70:
            st.success("🟢 Strong Investment Opportunity")
        elif investment >= 50:
            st.warning("🟠 Moderate Opportunity")
        else:
            st.error("🔴 Weak Investment")

        st.subheader("⚠ Risk Level")
        st.metric("Risk Score", f"{risk_score:.1f}/100")
        st.progress(clamp01(risk_score / 100))

        if risk_score < 35:
            st.success("🟢 Low Risk")
        elif risk_score < 65:
            st.warning("🟠 Medium Risk")
        else:
            st.error("🔴 High Risk")

        # ---------------- TABS ----------------
        premium = st.session_state.premium_unlocked

        if premium:
            tabs = st.tabs(
                ["Overview", "Insights", "Geo", "Affordability", "Risk", "PDF", "Raw"]
            )
        else:
            tabs = st.tabs(["Overview"])

        # OVERVIEW
        with tabs[0]:
            location = g(data, "location", "Unknown")
            builder = g(data, "builder", "Unknown")
            size = g(data, "property_size", "Unknown")
            price = safe_int(g(data, "property_price", 0))

            o1, o2 = st.columns(2)

            with o1:
                st.info(
                    "\n\n".join(
                        [
                            f"📍 Location: {location}",
                            f"🏗 Builder: {builder}",
                            f"🏠 Size: {size} sq.ft",
                            f"💰 Price: ₹{price:,.0f}",
                        ]
                    )
                )

            with o2:
                st.success(
                    "\n\n".join(
                        [
                            f"⭐ Grade: {grade}",
                            f"🎯 Confidence: {confidence}%",
                            f"📈 Investment Score: {investment:.1f}",
                            f"⚠ Risk Score: {risk_score:.1f}",
                        ]
                    )
                )

            st.divider()
            st.subheader("Executive Summary")
            st.write(g(data, "summary", "No summary available."))

        if premium:

            # INSIGHTS
            with tabs[1]:
                entities = g(data, "entities", {})
                if entities:
                    st.json(entities)
                else:
                    st.info("No entity extraction available.")

            # GEO
            with tabs[2]:
                geo = g(data, "geo_location", {})
                lat = geo.get("lat") if isinstance(geo, dict) else None
                lon = geo.get("lon") if isinstance(geo, dict) else None

                if lat is not None and lon is not None:
                    import pydeck as pdk

                    df = pd.DataFrame(
                        [{"lat": safe_float(lat), "lon": safe_float(lon)}]
                    )
                    st.pydeck_chart(
                        pdk.Deck(
                            map_provider="carto",
                            map_style="dark",
                            initial_view_state=pdk.ViewState(
                                latitude=safe_float(lat),
                                longitude=safe_float(lon),
                                zoom=12,
                            ),
                            layers=[
                                pdk.Layer(
                                    "ScatterplotLayer",
                                    data=df,
                                    get_position="[lon, lat]",
                                    get_fill_color="[255,0,0,255]",
                                    get_radius=300,
                                )
                            ],
                        )
                    )
                    st.caption(f"Latitude: {lat} • Longitude: {lon}")
                else:
                    st.warning("No geo coordinates available.")

            # AFFORDABILITY
            with tabs[3]:
                aff = g(data, "affordability", {})

                if aff:
                    st.subheader("Affordability Analysis")

                    a1, a2, a3 = st.columns(3)
                    a1.metric(
                        "Property Price",
                        f"₹{safe_float(aff.get('property_price')):,.0f}",
                    )
                    a2.metric(
                        "Down Payment",
                        f"₹{safe_float(aff.get('down_payment')):,.0f}",
                    )
                    a3.metric(
                        "Loan Amount",
                        f"₹{safe_float(aff.get('loan_amount')):,.0f}",
                    )

                    st.divider()

                    b1, b2, b3 = st.columns(3)
                    b1.metric(
                        "Estimated EMI",
                        f"₹{safe_float(aff.get('estimated_emi')):,.0f}",
                    )
                    b2.metric("Debt Ratio", f"{aff.get('debt_ratio', 'N/A')}%")
                    b3.metric("LTV Ratio", f"{aff.get('loan_to_value', 'N/A')}%")

                    st.divider()
                    st.success(
                        f"Affordability Rating: {aff.get('affordability_rating', 'N/A')}"
                    )
                else:
                    st.warning("No affordability analysis returned.")

            # RISK
            with tabs[4]:
                st.metric("Risk Score", risk_score)
                st.metric("Location Score", g(scores, "location", 0))
                st.metric("Connectivity", g(scores, "connectivity", 0))
                st.metric("Lifestyle", g(scores, "lifestyle", 0))

            # PDF PREVIEW
            with tabs[5]:
                st.text_area(
                    "PDF Text Preview",
                    g(data, "document_preview", ""),
                    height=400,
                )

            # RAW
            with tabs[6]:
                with st.expander("Developer Data"):
                    st.json(data)

    # ------------------------------------------------
    # RIGHT: PURCHASE PANEL
    # ------------------------------------------------
    with premium_col:
        st.markdown(
            """
<div class="premium-card">
<div class="premium-title">🔒 Professional Report</div>
<p>The complete report includes:</p>
<ul>
<li>✅ Fair Market Valuation</li>
<li>✅ Investment Analysis</li>
<li>✅ Builder Intelligence</li>
<li>✅ Rental Yield</li>
<li>✅ Risk Assessment</li>
<li>✅ Executive PDF Report</li>
</ul>
<div class="premium-price">₹250/-</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.link_button("💳 Purchase Report", PAYMENT_URL, width="stretch")
        st.caption("🔒 Secure Payment • Powered by Razorpay")

    if not st.session_state.premium_unlocked:
        st.success(
            "🔒 Purchase the Professional Report to receive a downloadable Executive PDF."
        )
