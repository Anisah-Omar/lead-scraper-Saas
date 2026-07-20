import streamlit as st
import pandas as pd
import requests
import hashlib
import re
from datetime import datetime

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="LeadPulse | B2B Lead Generation Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# BACKEND CONFIGURATION
# ==============================================================================
VERCEL_API_BASE_URL = "https://business-lead-scraper.vercel.app"
VERCEL_LEADS_ENDPOINT = f"{VERCEL_API_BASE_URL}/scrape-leads"
VERCEL_SERVER_MAX_RESULTS = 20  # hard cap enforced by the backend's MAX_RESULTS constant

INTASEND_SANDBOX_URL = "https://intasend.com/api/v1/payment/mpesa-stk-push/"
INTASEND_SANDBOX_PUBLIC_KEY = "ISPubKey_test_00000000-0000-0000-0000-000000000000"
INTASEND_SANDBOX_TOKEN = ""  # Populate with a real sandbox token in production

CREDIT_BUNDLES = {
    "Starter Bundle — 100 Credits (KES 500)": {"credits": 100, "amount": 500},
    "Growth Bundle — 500 Credits (KES 1,500)": {"credits": 500, "amount": 1500},
    "Agency Pro Layer — 2,000 Credits (KES 4,500)": {"credits": 2000, "amount": 4500},
}

# ==============================================================================
# CUSTOM CSS — PREMIUM SAAS THEME
# ==============================================================================
CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
    }

    .stApp {
        background-color: #f5f6fa;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Card module */
    .lp-card {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 1.75rem 2rem;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(15, 23, 42, 0.05);
        margin-bottom: 1.25rem;
    }

    .lp-header-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.03em;
        margin-bottom: 0.15rem;
    }

    .lp-header-subtitle {
        font-size: 1rem;
        color: #6b7280;
        font-weight: 400;
        margin-bottom: 1.75rem;
    }

    .lp-wallet-card {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border-radius: 14px;
        padding: 1.5rem;
        color: #ffffff;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 14px rgba(17, 24, 39, 0.25);
    }

    .lp-wallet-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9ca3af;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .lp-wallet-value {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }

    .lp-wallet-caption {
        font-size: 0.82rem;
        color: #9ca3af;
        margin-top: 0.4rem;
    }

    .lp-section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }

    .lp-badge {
        display: inline-block;
        background-color: #eef2ff;
        color: #4338ca;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    div.stButton > button {
        background-color: #111827;
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        transition: all 0.15s ease-in-out;
        width: 100%;
    }

    div.stButton > button:hover {
        background-color: #2563eb;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        transform: translateY(-1px);
    }

    div.stButton > button:active {
        transform: translateY(0px);
    }

    div[data-testid="stFormSubmitButton"] > button {
        background-color: #2563eb;
    }

    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #1d4ed8;
    }

    .stDownloadButton > button {
        background-color: #059669;
        color: #ffffff;
        border-radius: 10px;
        font-weight: 600;
        border: none;
    }

    .stDownloadButton > button:hover {
        background-color: #047857;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        padding: 0.55rem 0.8rem;
    }

    .stSelectbox > div > div {
        border-radius: 10px;
    }

    div[data-baseweb="tab-list"] {
        gap: 6px;
    }

    button[data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        font-weight: 600;
    }

    .lp-footer-note {
        text-align: center;
        color: #9ca3af;
        font-size: 0.8rem;
        margin-top: 2rem;
    }

    hr {
        margin: 1.2rem 0;
        border-color: #eef0f3;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# PASSWORD HASHING HELPERS
# ==============================================================================
def hash_password(raw_password: str) -> str:
    """Return a SHA-256 hex digest of the given plaintext password."""
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Compare a plaintext password against a stored SHA-256 hash."""
    return hash_password(raw_password) == hashed_password


# ==============================================================================
# SESSION-STATE "DATABASE" INITIALIZATION
# ==============================================================================
def init_user_database():
    if "user_db" not in st.session_state:
        st.session_state.user_db = {
            "test@leadpulse.com": {
                "password_hash": hash_password("password123"),
                "credits": 5,
                "created_at": "2026-01-01",
            },
            "agency@marketing.co.ke": {
                "password_hash": hash_password("grow2026"),
                "credits": 120,
                "created_at": "2026-01-01",
            },
        }

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    if "last_results" not in st.session_state:
        st.session_state.last_results = None


init_user_database()


# ==============================================================================
# M-PESA / INTASEND SANDBOX HELPER
# ==============================================================================
def normalize_kenyan_phone(raw_phone: str) -> str:
    """
    Normalize a Kenyan mobile phone number into the unified '2547XXXXXXXX'
    format, stripping common prefixes such as leading '0' or '+254'.
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", raw_phone or "")

    if cleaned.startswith("+254"):
        cleaned = "254" + cleaned[4:]
    elif cleaned.startswith("254"):
        cleaned = cleaned
    elif cleaned.startswith("0"):
        cleaned = "254" + cleaned[1:]
    elif cleaned.startswith("7") or cleaned.startswith("1"):
        cleaned = "254" + cleaned
    else:
        cleaned = cleaned

    return cleaned


def send_mpesa_stk_push(phone: str, amount: int):
    """
    Trigger an M-Pesa STK push via the IntaSend sandbox endpoint.
    Returns a dict describing the outcome. Falls back gracefully to a
    simulated sandbox success if the API token is missing or the live
    request fails, so demos are never blocked.
    """
    normalized_phone = normalize_kenyan_phone(phone)

    if not re.match(r"^2547\d{8}$", normalized_phone):
        return {
            "success": False,
            "simulated": False,
            "message": "Invalid Kenyan phone number format. Use 07XXXXXXXX or +2547XXXXXXXX.",
        }

    if not INTASEND_SANDBOX_TOKEN:
        return {
            "success": True,
            "simulated": True,
            "message": f"Sandbox mode: STK push simulated for {normalized_phone} (KES {amount}).",
        }

    headers = {
        "Authorization": f"Bearer {INTASEND_SANDBOX_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "public_key": INTASEND_SANDBOX_PUBLIC_KEY,
        "amount": amount,
        "phone_number": normalized_phone,
        "currency": "KES",
        "api_ref": f"leadpulse-{datetime.utcnow().isoformat()}",
    }

    try:
        response = requests.post(
            INTASEND_SANDBOX_URL, json=payload, headers=headers, timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return {
            "success": True,
            "simulated": False,
            "message": "STK push sent successfully. Check your phone to complete payment.",
            "raw_response": data,
        }
    except requests.exceptions.RequestException as request_error:
        return {
            "success": True,
            "simulated": True,
            "message": f"Sandbox fallback triggered ({request_error}). Credits applied for demo continuity.",
        }
    except ValueError as parse_error:
        return {
            "success": True,
            "simulated": True,
            "message": f"Sandbox fallback triggered (bad response payload: {parse_error}).",
        }
    except Exception as unexpected_error:
        return {
            "success": True,
            "simulated": True,
            "message": f"Sandbox fallback triggered (unexpected error: {unexpected_error}).",
        }


# ==============================================================================
# LEAD EXTRACTION HELPER
# ==============================================================================
def fetch_leads_from_vercel(keyword: str, location: str, limit: int):
    """
    Fetch raw lead records from the Vercel serverless backend and return
    them as a cleanly renamed Pandas DataFrame. Returns (dataframe, error).
    """
    # The backend only accepts 'keyword' and 'location' — it has no 'limit'
    # param and internally caps results at VERCEL_SERVER_MAX_RESULTS, so the
    # slider value is applied client-side after the response comes back.
    params = {
        "keyword": keyword,
        "location": location,
    }

    try:
        response = requests.get(VERCEL_LEADS_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as request_error:
        return None, f"Could not reach the extraction backend: {request_error}"
    except ValueError as parse_error:
        return None, f"Backend returned an unreadable payload: {parse_error}"

    records = payload.get("leads", payload) if isinstance(payload, dict) else payload

    if not records:
        return pd.DataFrame(), None

    records = records[:limit]

    try:
        df = pd.DataFrame(records)
    except Exception as build_error:
        return None, f"Failed to parse lead records into a table: {build_error}"

    rename_map = {
        "business_name": "Business Name",
        "name": "Business Name",
        "website": "Website URL",
        "website_url": "Website URL",
        "url": "Website URL",
        "description": "Description Snippet",
        "snippet": "Description Snippet",
        "summary": "Description Snippet",
        "domain": "Core Domain Address",
        "core_domain": "Core Domain Address",
    }
    df = df.rename(columns=rename_map)

    desired_columns = [
        "Business Name",
        "Website URL",
        "Description Snippet",
        "Core Domain Address",
    ]
    for column in desired_columns:
        if column not in df.columns:
            df[column] = ""

    df = df[desired_columns]
    return df, None


# ==============================================================================
# AUTH VIEWS
# ==============================================================================
def render_login_form():
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email address", placeholder="you@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("🔒 Log In")

        if submitted:
            email_clean = (email or "").strip().lower()
            user_record = st.session_state.user_db.get(email_clean)

            if not user_record:
                st.error("No account found with that email address.")
            elif not verify_password(password, user_record["password_hash"]):
                st.error("Incorrect password. Please try again.")
            else:
                st.session_state.authenticated = True
                st.session_state.current_user = email_clean
                st.success("Login successful. Redirecting to your workspace...")
                st.rerun()


def render_signup_form():
    with st.form("signup_form", clear_on_submit=False):
        new_email = st.text_input("Email address", placeholder="you@company.com", key="signup_email")
        new_password = st.text_input(
            "Create password", type="password", placeholder="Minimum 6 characters", key="signup_pw"
        )
        confirm_password = st.text_input(
            "Confirm password", type="password", placeholder="Re-enter password", key="signup_pw_confirm"
        )
        submitted = st.form_submit_button("✨ Create Free Account")

        if submitted:
            email_clean = (new_email or "").strip().lower()

            if not email_clean or "@" not in email_clean or "." not in email_clean:
                st.error("Please enter a valid email address.")
            elif email_clean in st.session_state.user_db:
                st.error("An account with that email already exists. Please log in instead.")
            elif len(new_password or "") < 6:
                st.error("Password must be at least 6 characters long.")
            elif new_password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            else:
                st.session_state.user_db[email_clean] = {
                    "password_hash": hash_password(new_password),
                    "credits": 3,
                    "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
                }
                st.session_state.authenticated = True
                st.session_state.current_user = email_clean
                st.success("Account created! You've received 3 free trial credits.")
                st.balloons()
                st.rerun()


def render_auth_gate():
    st.markdown('<div class="lp-header-title">📡 LeadPulse</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-header-subtitle">Premium B2B lead generation, delivered on demand.</div>',
        unsafe_allow_html=True,
    )

    left_spacer, center_col, right_spacer = st.columns([1, 1.4, 1])

    with center_col:
        st.markdown('<div class="lp-card">', unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["🔒 Secure Login", "✨ Create Account"])

        with login_tab:
            render_login_form()
            st.caption("Demo accounts — test@leadpulse.com / password123 · agency@marketing.co.ke / grow2026")

        with signup_tab:
            render_signup_form()

        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# WALLET + BILLING SIDEBAR
# ==============================================================================
def render_wallet_sidebar():
    user_record = st.session_state.user_db[st.session_state.current_user]

    with st.sidebar:
        st.markdown(
            f"""
            <div class="lp-wallet-card">
                <div class="lp-wallet-label">Signed in as</div>
                <div style="font-size:0.95rem; font-weight:600; margin-bottom:0.9rem;">{st.session_state.current_user}</div>
                <div class="lp-wallet-label">Available Credits</div>
                <div class="lp-wallet-value">{user_record['credits']}</div>
                <div class="lp-wallet-caption">1 credit = 1 lead extraction</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Log Out"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.last_results = None
            st.rerun()

        st.markdown("---")
        st.markdown('<div class="lp-section-title">💳 Top Up via M-Pesa</div>', unsafe_allow_html=True)

        selected_bundle_label = st.selectbox(
            "Choose a credit bundle",
            options=list(CREDIT_BUNDLES.keys()),
            key="bundle_select",
        )
        phone_input = st.text_input(
            "M-Pesa phone number",
            placeholder="07XX XXX XXX or +2547XXXXXXXX",
            key="mpesa_phone",
        )

        if st.button("📲 Send STK Push"):
            if not phone_input or not phone_input.strip():
                st.error("Please enter a valid M-Pesa phone number.")
            else:
                bundle = CREDIT_BUNDLES[selected_bundle_label]
                with st.spinner("Sending STK push to your phone..."):
                    result = send_mpesa_stk_push(phone_input, bundle["amount"])

                if result["success"]:
                    st.session_state.user_db[st.session_state.current_user]["credits"] += bundle["credits"]
                    st.success(result["message"])
                    st.balloons()
                    st.rerun()
                else:
                    st.error(result["message"])


# ==============================================================================
# MAIN WORKSPACE
# ==============================================================================
def render_workspace():
    user_record = st.session_state.user_db[st.session_state.current_user]

    st.markdown('<div class="lp-header-title">📡 LeadPulse Workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-header-subtitle">Extract fresh, verified B2B leads in seconds.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lp-card">', unsafe_allow_html=True)
    st.markdown('<div class="lp-section-title">🔍 Deep Lead Extraction</div>', unsafe_allow_html=True)

    input_col1, input_col2 = st.columns(2)
    with input_col1:
        keyword = st.text_input("Keyword", placeholder="e.g. digital marketing agency")
    with input_col2:
        location_city = st.text_input("Location City", placeholder="e.g. Nairobi")

    result_limit = st.slider("Result limit", min_value=10, max_value=100, value=25, step=5)
    if result_limit > VERCEL_SERVER_MAX_RESULTS:
        st.caption(
            f"⚠️ The extraction engine currently returns up to {VERCEL_SERVER_MAX_RESULTS} "
            "verified leads per search — you may receive fewer than requested."
        )

    st.markdown(
        f'<span class="lp-badge">Cost: 1 credit per extraction · Balance: {user_record["credits"]} credits</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    extract_clicked = st.button("🚀 Run Extraction")
    st.markdown("</div>", unsafe_allow_html=True)

    if extract_clicked:
        if not keyword or not keyword.strip():
            st.warning("Please enter a keyword to search.")
        elif not location_city or not location_city.strip():
            st.warning("Please enter a target location city.")
        elif user_record["credits"] < 1:
            st.error("You're out of credits. Please top up via M-Pesa in the sidebar to continue.")
        else:
            with st.spinner("Extracting leads from the LeadPulse engine..."):
                leads_df, fetch_error = fetch_leads_from_vercel(
                    keyword.strip(), location_city.strip(), result_limit
                )

            if fetch_error:
                st.error(fetch_error)
            elif leads_df is None or leads_df.empty:
                st.info("No leads were found for that search. Try a broader keyword or location.")
            else:
                st.session_state.user_db[st.session_state.current_user]["credits"] -= 1
                st.session_state.last_results = leads_df
                st.success(f"Extraction complete — {len(leads_df)} leads retrieved. 1 credit deducted.")
                st.rerun()

    if st.session_state.last_results is not None:
        results_df = st.session_state.last_results

        st.markdown('<div class="lp-card">', unsafe_allow_html=True)
        st.markdown('<div class="lp-section-title">📊 Extracted Leads</div>', unsafe_allow_html=True)
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        csv_bytes = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv_bytes,
            file_name=f"leadpulse_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="lp-footer-note">LeadPulse © 2026 — Premium B2B Lead Generation SaaS</div>',
        unsafe_allow_html=True,
    )


# ==============================================================================
# APP ENTRYPOINT
# ==============================================================================
def main():
    if not st.session_state.authenticated:
        render_auth_gate()
    else:
        render_wallet_sidebar()
        render_workspace()


if __name__ == "__main__":
    main()