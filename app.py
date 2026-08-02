import io
import importlib
import re
import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import scraper_backend

scraper_backend = importlib.reload(scraper_backend)
from scraper_backend import (
    SHEET_ID,
    TARGET_CHANNELS,
    WORKSHEET_NAME,
    get_live_customer_records,
    get_live_google_sheet_records,
    normalize_live_sheet_for_dashboard,
    run_scrape_job,
)


# ---------------------------
# App configuration
# ---------------------------
PAGE_OPTIONS = [
    "All-in-One",
    "Dashboard",
    "Scrape Data",
    "Customer Records",
    "Scraping History",
    "Telegram Channels",
    "Analytics",
    "Data Export",
    "System Logs",
    "Settings",
]

CHANNEL_LABELS = [
    "TLK",
    "ASN",
    "BSL",
    "NRD",
    "271M",
    "598M",
    "PDT",
    "MTT",
    "CMT",
    "SRP",
    "SSP",
    "BTI",
    "PST",
    "SSM",
    "RSK",
    "BTK",
    "MMT",
    "CHA",
    "BTB",
    "VSR",
    "STG",
    "KTE",
    "KPC",
    "SNG",
    "STS",
    "PMR",
    "PVH",
    "TKM",
    "KPT",
    "NRM",
    "KCG",
    "BLG",
    "DKO",
    "SRG",
]

CHANNEL_OPTIONS = {label: channel for label, channel in zip(CHANNEL_LABELS, TARGET_CHANNELS)}
CHANNELS = list(CHANNEL_OPTIONS.keys())
DEFAULT_CHANNELS = CHANNELS[:3]
NOW = datetime.now()
BRAND_TITLE = "Scraping, Dashboard and Customer Data Management"
BRAND_SUBTITLE = "Customer data scraping & Performance"
BRAND_LOGO_URL = "https://www.chipmongbank.com/fb-og-image.jpg"

st.set_page_config(
    page_title="Customer Data Scraping Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# CSS styling
# ---------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --primary: #0d5c45;
        --primary-soft: #eaf5f1;
        --bg: #f4f7f6;
        --surface: #ffffff;
        --text: #1e2b26;
        --muted: #5f6f68;
        --border: #d6e2dd;
        --success: #1d8f5f;
        --warning: #d08711;
        --error: #b42318;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    #MainMenu, footer {visibility: hidden;}
    [data-testid="stHeader"] { display: none; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #fbfbfb 100%);
        border-right: 1px solid var(--border);
    }

    .sidebar-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 1rem;
        margin-bottom: 0.25rem;
    }

    .nav-item {
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
        margin: 0.15rem 0;
        font-weight: 600;
        color: #374151;
    }

    .nav-item.active {
        background: var(--primary);
        color: white;
        box-shadow: 0 6px 18px rgba(164, 14, 40, 0.18);
    }

    .glass-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }

    .metric-card {
        position: relative;
        overflow: hidden;
        background: linear-gradient(180deg, #ffffff 0%, #f9fcfa 100%);
        border: 1px solid rgba(13, 92, 69, 0.12);
        border-radius: 24px;
        padding: 1.15rem 1.1rem 1rem 1.1rem;
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.06);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 158px;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }

    .metric-card::before {
        content: "";
        position: absolute;
        inset: 0 auto auto 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #0d5c45 0%, #18a56c 100%);
        opacity: 0.9;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 22px 42px rgba(15, 23, 42, 0.09);
        border-color: rgba(13, 92, 69, 0.18);
    }

    .metric-title {
        color: #5f6f68;
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        line-height: 1.35;
        min-height: 2.1em;
        margin-bottom: 0.55rem;
        padding-top: 0.2rem;
    }

    .metric-value {
        font-size: clamp(1.95rem, 3vw, 2.35rem);
        font-weight: 800;
        color: #102a43;
        margin: 0;
        line-height: 1.02;
        letter-spacing: -0.04em;
    }

    .metric-value.compact {
        font-size: clamp(1rem, 1.45vw, 1.25rem);
        line-height: 1.12;
        letter-spacing: -0.02em;
        word-break: break-word;
    }

    .metric-sub {
        font-size: 0.8rem;
        color: #667881;
        line-height: 1.42;
        margin-top: 0.75rem;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.6rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid transparent;
    }

    .badge.success { background: #e9f8ef; color: #12723a; border-color: #bae6c8; }
    .badge.warning { background: #fff6df; color: #b45309; border-color: #f0d18d; }
    .badge.error { background: #fff0f0; color: #b91c1c; border-color: #f4b0b0; }

    .page-title {
        font-size: 2.15rem;
        font-weight: 800;
        color: var(--primary);
        margin: 0;
        line-height: 1.2;
    }

    .page-subtitle {
        color: #14a44d;
        font-size: 1rem;
        font-weight: 700;
        margin-top: 0.6rem;
    }

    .brand-shell {
        background: #ffffff;
        border: 1px solid rgba(13, 92, 69, 0.12);
        border-radius: 24px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        padding: 1.25rem 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 188px;
    }

    .brand-logo-wrap {
        width: 100%;
        max-width: 320px;
        margin: 0 auto;
        text-align: center;
    }

    .brand-logo-box {
        width: 100%;
        margin: 0 auto;
        background: transparent;
        border: none;
        box-shadow: none;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .brand-logo-image {
        width: min(220px, 100%);
        height: auto;
        display: block;
        object-fit: contain;
        border-radius: 0;
    }

    .brand-name {
        font-size: 1.1rem;
        font-weight: 800;
        line-height: 1.05;
        color: #495057;
        letter-spacing: 0.02em;
        display: none;
    }

    .brand-name .bank {
        color: #0ca24a;
    }

    .hero-banner {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 188px;
        padding: 0.75rem 1rem;
    }

    .hero-copy {
        width: 100%;
        text-align: center;
        max-width: 920px;
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3.4rem);
        font-weight: 800;
        color: var(--primary);
        line-height: 1.15;
        margin: 0;
    }

    .hero-subtitle {
        margin-top: 1rem;
        color: #14a44d;
        font-size: clamp(1rem, 1.4vw, 1.45rem);
        font-weight: 700;
    }

    .hero-divider {
        width: 72px;
        height: 4px;
        margin: 1rem auto 0 auto;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(13,92,69,0.15), rgba(13,92,69,0.55), rgba(13,92,69,0.15));
    }

    .header-status {
        background: #ecfdf5;
        color: #047857;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.82rem;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.7rem;
        background: #f8fafc;
        border: 1px solid var(--border);
        border-radius: 999px;
        color: #334155;
        font-weight: 600;
        font-size: 0.8rem;
    }

    .log-panel {
        background: #0f172a;
        color: #e2e8f0;
        border-radius: 16px;
        padding: 1rem;
        font-family: 'Consolas', monospace;
        font-size: 0.9rem;
        line-height: 1.6;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.16);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Live data providers
# ---------------------------
@st.cache_data(ttl=30, show_spinner=False)
def load_live_customer_records() -> pd.DataFrame:
    """Load the current customer rows from the configured Google Sheet."""
    return get_live_customer_records()


@st.cache_data(ttl=30, show_spinner=False)
def load_live_google_sheet_records() -> pd.DataFrame:
    """Load the current worksheet with its original Google Sheet headers."""
    return get_live_google_sheet_records()


def get_customer_records() -> pd.DataFrame:
    try:
        live_df = load_live_customer_records()
        st.session_state.live_sheet_error = None
        return live_df.copy()
    except Exception as exc:
        st.session_state.live_sheet_error = str(exc)
        return pd.DataFrame(columns=["Customer Name", "Phone Number", "Telegram Channel", "Message Date", "Business Type", "Status"])


def get_customer_records_with_sheet_headers() -> pd.DataFrame:
    try:
        raw_df = load_live_google_sheet_records()
        st.session_state.live_sheet_error = None
        return raw_df.copy()
    except Exception as exc:
        st.session_state.live_sheet_error = str(exc)
        return pd.DataFrame()


def refresh_live_customer_records():
    """Clear the short-lived cache so the next render reads Google Sheets again."""
    load_live_customer_records.clear()
    load_live_google_sheet_records.clear()


def render_live_sheet_status():
    error = st.session_state.get("live_sheet_error")
    if error:
        st.error(f"Unable to load the live Google Sheet: {error}")
    else:
        st.caption(f"Live data source: Google Sheet · worksheet: {WORKSHEET_NAME} · refreshes every 30 seconds")


def get_sheet_channel_options(df: pd.DataFrame) -> dict[str, str]:
    """Return UI labels mapped to the exact channel values stored in Google Sheets."""
    if "Telegram Channel" not in df.columns:
        return {"All": "All"}

    sheet_channels = sorted(
        {
            value.strip()
            for value in df["Telegram Channel"].dropna().astype(str)
            if value.strip()
        },
        key=str.casefold,
    )
    options = {"All": "All"}
    for sheet_channel in sheet_channels:
        alias = next(
            (
                code
                for code in CHANNELS
                if sheet_channel.casefold() == code.casefold()
                or sheet_channel.casefold().endswith(f" {code.casefold()}")
            ),
            None,
        )
        label = alias or sheet_channel
        if label in options:
            label = sheet_channel
        options[label] = sheet_channel

    return options


def add_customer_filter_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add internal filter fields without changing the original Google Sheet columns."""
    filter_df = df.copy()
    source_columns = {
        "Customer Name": ("Name", "Sender_Name"),
        "Phone Number": ("Tel", "Telephone"),
        "Telegram Channel": ("Source_Channel",),
        "Message Date": ("Message_Date",),
        "Business Type": ("Business",),
        "Status": ("Status",),
    }
    for display_column, candidates in source_columns.items():
        if display_column in filter_df.columns:
            continue
        source_column = next((column for column in candidates if column in filter_df.columns), None)
        if source_column:
            filter_df[display_column] = filter_df[source_column]
        else:
            filter_df[display_column] = ""

    return filter_df


def filter_customer_records(
    df: pd.DataFrame,
    *,
    sender_name_query: str = "",
    phone_query: str = "",
    date_range=None,
    channel: str = "All",
    business_type: str = "All",
    status: str = "All",
) -> pd.DataFrame:
    """Apply the customer-record filters used by the table and export views."""
    filtered_df = df.copy()

    if "Message Date" in filtered_df.columns:
        filtered_df["Message Date"] = pd.to_datetime(filtered_df["Message Date"], errors="coerce")
        if isinstance(date_range, (tuple, list)) and date_range:
            record_dates = filtered_df["Message Date"].dt.date
            filtered_df = filtered_df[record_dates >= date_range[0]]
            if len(date_range) > 1:
                filtered_df = filtered_df[record_dates <= date_range[1]]

    if sender_name_query:
        sender_columns = [column for column in ("Sender_Name", "Sender Name", "Customer Name") if column in filtered_df.columns]
        if sender_columns:
            sender_column = sender_columns[0]
            filtered_df = filtered_df[
                filtered_df[sender_column].fillna("").astype(str).str.contains(sender_name_query, case=False, na=False)
            ]
    if phone_query and "Phone Number" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["Phone Number"].fillna("").astype(str).str.contains(phone_query, case=False, na=False)
        ]
    if channel != "All" and "Telegram Channel" in filtered_df.columns:
        channel_values = filtered_df["Telegram Channel"].fillna("").astype(str).str.strip()
        channel_value = str(CHANNEL_OPTIONS.get(channel, channel)).strip()
        channel_code = str(channel).strip()
        channel_matches = channel_values.eq(channel_value)
        if channel_code:
            channel_matches |= channel_values.str.contains(
                rf"(?:^|\s){re.escape(channel_code)}$", case=False, regex=True, na=False
            )
        filtered_df = filtered_df[channel_matches]
    if business_type != "All" and "Business Type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Business Type"].astype(str) == str(business_type)]
    if status != "All" and "Status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Status"].astype(str) == str(status)]

    return filtered_df


def render_date_filter(label: str, *, mode_key: str, range_key: str, default_days: int = 14, default_mode: str = "7days last"):
    options = ["All", "Today", "7days last", "Custom Date"]
    selected_mode = st.selectbox(
        label,
        options=options,
        index=options.index(default_mode) if default_mode in options else 0,
        key=mode_key,
    )

    selected_range = None
    if selected_mode == "Custom Date":
        selected_range = st.date_input(
            "Custom Date Range",
            value=(NOW.date() - timedelta(days=default_days), NOW.date()),
            key=range_key,
        )
    elif selected_mode == "Today":
        selected_range = (NOW.date(), NOW.date())
    elif selected_mode == "7days last":
        selected_range = (NOW.date() - timedelta(days=6), NOW.date())

    return selected_mode, selected_range


def reset_customer_filters():
    st.session_state.sender_name_filter = ""
    st.session_state.customer_date_range = (NOW.date() - timedelta(days=14), NOW.date())
    st.session_state.customer_date_filter_mode = "7days last"
    st.session_state.customer_channel_filter = "All"


def get_scraping_history() -> pd.DataFrame:
    live_df = get_customer_records().copy()
    if live_df.empty:
        return pd.DataFrame(columns=["ID", "Date", "Channel", "Start Time", "End Time", "Messages Scanned", "Records Found", "New Records", "Duplicates", "Status", "Processing Time"])

    if "Message Date" in live_df.columns:
        live_df["Message Date"] = pd.to_datetime(live_df["Message Date"], errors="coerce")
        live_df = live_df.dropna(subset=["Message Date"])

    if live_df.empty:
        return pd.DataFrame(columns=["ID", "Date", "Channel", "Start Time", "End Time", "Messages Scanned", "Records Found", "New Records", "Duplicates", "Status", "Processing Time"])

    history_rows = []
    group_columns = [live_df["Message Date"].dt.date, "Telegram Channel"] if "Telegram Channel" in live_df.columns else [live_df["Message Date"].dt.date]
    for index, (group_key, group) in enumerate(live_df.groupby(group_columns), start=1):
        if isinstance(group_key, tuple):
            date_value, channel = group_key
        else:
            date_value, channel = group_key, "Live Google Sheet"
        history_rows.append(
            {
                "ID": f"LIVE-{date_value.strftime('%Y%m%d')}-{index:03d}",
                "Date": date_value.strftime("%Y-%m-%d"),
                "Channel": str(channel),
                "Start Time": "--",
                "End Time": "--",
                "Messages Scanned": int(len(group)),
                "Records Found": int(len(group)),
                "New Records": int(len(group)),
                "Duplicates": 0,
                "Status": "Synced",
                "Processing Time": "Live",
            }
        )

    return pd.DataFrame(history_rows).sort_values(["Date", "Channel"], ascending=[False, True])


def get_channel_summary() -> pd.DataFrame:
    live_df = get_customer_records().copy()
    columns = ["Channel Name", "Channel ID", "Status", "Last Scraped", "Total Messages", "Total Records", "Last Error"]
    if live_df.empty or "Telegram Channel" not in live_df.columns:
        return pd.DataFrame(columns=columns)

    live_df["Telegram Channel"] = live_df["Telegram Channel"].fillna("").astype(str).str.strip()
    live_df = live_df[live_df["Telegram Channel"] != ""]
    if live_df.empty:
        return pd.DataFrame(columns=columns)

    if "Message Date" in live_df.columns:
        live_df["Message Date"] = pd.to_datetime(live_df["Message Date"], errors="coerce")

    aliases_by_target = {target: alias for alias, target in CHANNEL_OPTIONS.items()}
    summary_rows = []
    for channel_id, group in live_df.groupby("Telegram Channel", sort=True):
        latest_date = group["Message Date"].max() if "Message Date" in group.columns else pd.NaT
        summary_rows.append(
            {
                "Channel Name": aliases_by_target.get(channel_id, channel_id),
                "Channel ID": channel_id,
                "Status": "🟢 Active",
                "Last Scraped": latest_date.strftime("%d %b %Y %H:%M") if pd.notna(latest_date) else "No date in sheet",
                "Total Messages": int(len(group)),
                "Total Records": int(len(group)),
                "Last Error": "None",
            }
        )

    return pd.DataFrame(summary_rows, columns=columns)


def get_logs() -> pd.DataFrame:
    status = st.session_state.get("scraping_status", "Idle")
    message_count = st.session_state.get("scraping_results", {}).get("messages_scanned", 0)
    data = [
        {"Date": NOW.date(), "Level": "INFO", "Module": "Scraper", "Log": f"[{NOW.strftime('%H:%M:%S')}] INFO | Scrape session status: {status}"},
        {"Date": NOW.date(), "Level": "INFO", "Module": "Telegram API", "Log": f"[{NOW.strftime('%H:%M:%S')}] INFO | Telegram backend connected to live session"},
        {"Date": NOW.date(), "Level": "INFO", "Module": "Scraper", "Log": f"[{NOW.strftime('%H:%M:%S')}] INFO | Messages scanned in current run: {message_count}"},
    ]
    return pd.DataFrame(data)


def init_session_state():
    defaults = {
        "current_page": "All-in-One",
        "scraping_status": "Idle",
        "selected_date_range": (NOW.date() - timedelta(days=7), NOW.date()),
        "selected_channels": DEFAULT_CHANNELS,
        "scraping_progress": 0,
        "scraping_results": {
            "messages_scanned": 0,
            "records_extracted": 0,
            "new_records": 0,
            "duplicates": 0,
            "invalid_records": 0,
            "errors": 0,
            "error_details": [],
            "processing_time": "0m 00s",
        },
        "selected_job": None,
        "customer_filters": {
            "search_name": "",
            "search_phone": "",
            "date_range": (NOW.date() - timedelta(days=14), NOW.date()),
            "telegram_channel": "All",
            "location": "All",
            "business_type": "All",
            "status": "All",
        },
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_session_state()


# ---------------------------
# Helpers
# ---------------------------
def metric_card(title: str, value: str, subtext: str, delta: str = "", compact_value: bool = False):
    with st.container():
        footer_text = f"{delta} · {subtext}" if delta else subtext
        value_class = "metric-value compact" if compact_value else "metric-value"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">{title}</div>
                <div class="{value_class}">{value}</div>
                <div class="metric-sub">{footer_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def status_badge(label: str):
    style = {
        "Completed": "success",
        "Running": "warning",
        "Failed": "error",
    }
    return f'<span class="badge {style.get(label, "warning")}">{label}</span>'


def get_dashboard_snapshot() -> dict:
    df = get_customer_records().copy()
    if df.empty:
        return {
            "total_records": 0,
            "new_today": 0,
            "unique_channels": 0,
            "top_channel": "N/A",
            "top_location": "N/A",
            "last_scrape": "No recent run",
            "failed_scrapes": 0,
        }

    if "Message Date" in df.columns:
        df["Message Date"] = pd.to_datetime(df["Message Date"], errors="coerce")

    today = NOW.date()
    if "Message Date" in df.columns:
        new_today = int(df["Message Date"].dt.date.eq(today).sum())
    else:
        new_today = 0

    unique_channels = int(df["Telegram Channel"].nunique()) if "Telegram Channel" in df.columns else 0
    top_channel = "N/A"
    if "Telegram Channel" in df.columns and not df["Telegram Channel"].empty:
        channel_counts = df["Telegram Channel"].value_counts()
        top_channel = channel_counts.idxmax() if not channel_counts.empty else "N/A"

    top_location = "N/A"
    if "Location" in df.columns and not df["Location"].empty:
        loc_counts = df["Location"].value_counts()
        top_location = loc_counts.idxmax() if not loc_counts.empty else "N/A"

    failed_scrapes = 0
    last_scrape_value = "No recent run"
    if "Message Date" in df.columns and not df["Message Date"].empty:
        latest_message_date = df["Message Date"].max()
        if pd.notna(latest_message_date):
            last_scrape_value = latest_message_date.strftime("%d %b %Y, %I:%M %p")

    return {
        "total_records": int(len(df)),
        "new_today": new_today,
        "unique_channels": unique_channels,
        "top_channel": str(top_channel),
        "top_location": str(top_location),
        "last_scrape": last_scrape_value,
        "failed_scrapes": failed_scrapes,
    }


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-shell" style="padding: 1rem 0.9rem; min-height: 170px;">
                <div class="brand-logo-wrap">
                    <div class="brand-logo-box">
                        <img class="brand-logo-image" src="https://www.chipmongbank.com/fb-og-image.jpg" alt="Chip Mong Bank logo">
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_nav = st.radio(
            "",
            PAGE_OPTIONS,
            index=PAGE_OPTIONS.index(st.session_state.current_page),
            label_visibility="collapsed",
            key="sidebar_page_nav",
        )
        st.session_state.current_page = selected_nav

        st.markdown("<div class='sidebar-label'>System Status</div>", unsafe_allow_html=True)
        st.markdown("<div class='pill'>🟢 System Online</div>", unsafe_allow_html=True)
        st.markdown("<div class='pill' style='margin-top:0.5rem;'>Data Scraping Platform</div>", unsafe_allow_html=True)


def render_header(title: str, subtitle: str):
    left, right = st.columns([1.05, 3.95], vertical_alignment="center")
    with left:
        st.markdown(
            """
            <div class="brand-shell">
                <div class="brand-logo-wrap">
                    <div class="brand-logo-box">
                        <img class="brand-logo-image" src="https://www.chipmongbank.com/fb-og-image.jpg" alt="Chip Mong Bank logo">
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div class="hero-banner">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="hero-copy"><div class="hero-title">{title}</div><div class="hero-divider"></div><div class="hero-subtitle">{subtitle}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption(f"Last Updated: {NOW.strftime('%d %b %Y, %I:%M %p')}")


def render_dashboard():
    render_header(BRAND_TITLE, BRAND_SUBTITLE)

    snapshot = get_dashboard_snapshot()

    st.markdown("<div style='margin: 1rem 0 1.3rem 0;'>", unsafe_allow_html=True)
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        metric_card("Total Records", f"{snapshot['total_records']:,}", "from live Google Sheet", "")
    with m2:
        metric_card("New Records Today", f"{snapshot['new_today']:,}", "from live date field", "")
    with m3:
        metric_card("Live Records", f"{snapshot['total_records']:,}", "current data's rows", "")
    with m4:
        metric_card("Failed Scrapes", f"{snapshot['failed_scrapes']:,}", "live sheet sync only", "")
    with m5:
        metric_card("Telegram Channels", f"{snapshot['unique_channels']:,}", "active in sheet", "")
    with m6:
        metric_card("Last Scrape", snapshot['last_scrape'], "processing time", "", compact_value=True)
    st.markdown("</div>", unsafe_allow_html=True)

    live_df = get_customer_records().copy()
    render_live_sheet_status()
    if "Message Date" in live_df.columns:
        live_df["Message Date"] = pd.to_datetime(live_df["Message Date"], errors="coerce")

    dashboard_filter_mode, dashboard_date_range = render_date_filter(
        "Filter date",
        mode_key="dashboard_chart_date_filter_mode",
        range_key="dashboard_chart_date_range",
        default_days=30,
        default_mode="7days last",
    )

    chart_df = live_df.copy()
    if dashboard_filter_mode != "All" and "Message Date" in chart_df.columns and dashboard_date_range:
        if isinstance(dashboard_date_range, tuple) and len(dashboard_date_range) == 2:
            record_dates = chart_df["Message Date"].dt.date
            chart_df = chart_df[
                (record_dates >= dashboard_date_range[0])
                & (record_dates <= dashboard_date_range[1])
            ]

    chart1, chart2 = st.columns(2)

    with chart1:
        daily_counts = chart_df.groupby(chart_df["Message Date"].dt.date).size().sort_index() if "Message Date" in chart_df.columns else pd.Series(dtype=int)
        daily_chart = pd.DataFrame({"Date": daily_counts.index, "Records": daily_counts.values})
        fig = px.line(daily_chart, x="Date", y="Records", title="Records Scraped by Day", template="plotly_white")
        fig.update_layout(title_x=0.02, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
        fig.update_traces(line_color="#0d5c45", line_width=3)
        st.plotly_chart(fig, width="stretch")

    with chart2:
        channel_data = chart_df.groupby("Telegram Channel").size().reset_index(name="Records") if "Telegram Channel" in chart_df.columns else pd.DataFrame(columns=["Channel", "Records"])
        channel_data = channel_data.rename(columns={"Telegram Channel": "Channel"})
        fig = px.bar(channel_data, x="Channel", y="Records", title="Records by Telegram Channel", template="plotly_white", color="Channel")
        fig.update_layout(title_x=0.02, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
        fig.update_traces(marker_color="#0d5c45")
        st.plotly_chart(fig, width="stretch")

def render_scrape_data():
    render_header("Start New Scraping Process", "Select the Telegram channels and date range to collect customer data.")

    st.info("Use this option when the scraping period follows a business day rather than a calendar day.")

    c1, c2 = st.columns(2)
    with c1:
        selected_from_date = st.date_input("From Date", value=st.session_state.selected_date_range[0], key="scrape_from_date")
    with c2:
        selected_to_date = st.date_input("To Date", value=st.session_state.selected_date_range[1], key="scrape_to_date")
    st.session_state.selected_date_range = (selected_from_date, selected_to_date)

    st.multiselect(
        "Select Telegram Channels",
        options=list(CHANNEL_OPTIONS.keys()),
        default=st.session_state.selected_channels,
        key="selected_channels",
        help="Select the Telegram channels to scrape from the live backend workflow.",
    )

    t1, t2 = st.columns(2)
    with t1:
        selected_start_time = st.time_input("Start Time", value=datetime.strptime("20:00", "%H:%M").time(), key="scrape_start_time")
    with t2:
        selected_end_time = st.time_input("End Time", value=datetime.strptime("19:00", "%H:%M").time(), key="scrape_end_time")

    st.caption("Use this option when the scraping period follows a business day rather than a calendar day.")

    if st.button("▶ Start Scraping", type="primary", width="stretch", key="start_scrape_button"):
        st.session_state.scraping_status = "In Progress"
        st.session_state.scraping_progress = 0
        st.session_state.current_page = "Scrape Data"
        progress_bar = st.progress(0, text="Starting Telegram scrape")
        terminal_box = st.empty()
        log_lines = []

        def render_terminal() -> None:
            terminal_box.markdown(
                """
                <div class="log-panel" style="max-height: 420px; overflow-y: auto; white-space: pre-wrap;">
                <strong>Live Scraping Terminal</strong>
                <br><br>
                {content}
                </div>
                """.format(content="<br>".join(line or "&nbsp;" for line in log_lines)),
                unsafe_allow_html=True,
            )

        def append_log(message: str) -> None:
            log_lines.append(message)
            render_terminal()

        def update_progress(value: int, message: str):
            st.session_state.scraping_progress = value
            progress_bar.progress(value, text=message)
            append_log(f"[{value:>3}%] {message}")

        append_log("🧪 ===== TELEGRAM SCRAPER - MULTI-TARGET EXECUTION =====")

        from_date = datetime.combine(st.session_state.selected_date_range[0], selected_start_time)
        to_date = datetime.combine(st.session_state.selected_date_range[1], selected_end_time)
        selected_targets = [CHANNEL_OPTIONS.get(name, name) for name in st.session_state.selected_channels]
        if not selected_targets:
            selected_targets = list(TARGET_CHANNELS)

        append_log(f"📋 Global Limits: 1000000 requests, 1000000 messages (TESTING=True)")
        append_log(f"📅 Scrape window: {from_date:%Y-%m-%d %H:%M:%S}  ->  {to_date:%Y-%m-%d %H:%M:%S}")
        append_log("🔗 Connecting to Telegram...")

        try:
            result = run_scrape_job(
                selected_channels=selected_targets,
                from_date=from_date,
                to_date=to_date,
                progress_callback=update_progress,
                log_callback=append_log,
            )

            st.session_state.scraping_status = result.get("status", "Completed")
            st.session_state.scraping_results = {
                "messages_scanned": result.get("messages_scanned", 0),
                "records_extracted": result.get("records_extracted", 0),
                "new_records": result.get("new_records", 0),
                "duplicates": result.get("duplicates", 0),
                "invalid_records": result.get("invalid_records", 0),
                "errors": result.get("errors", 0),
                "error_details": result.get("error_details", []),
                "processing_time": result.get("processing_time", "0m 00s"),
            }

            warnings = result.get("warnings", [])
            if warnings:
                append_log("")
                append_log("⚠️ Validation warnings:")
                for warning in warnings[:20]:
                    append_log(f"  • {warning}")
                if len(warnings) > 20:
                    append_log(f"  • ... and {len(warnings) - 20} more warnings")

            append_log("")
            append_log("🎉 EXECUTION COMPLETED!")
            append_log("📊 Final Statistics:")
            append_log(f"  • Total API Requests: {st.session_state.scraping_results.get('messages_scanned', 0)}/1000000")
            append_log(f"  • Total Messages Fetched: {st.session_state.scraping_results.get('messages_scanned', 0)}")
            append_log(f"  • Total Structured Records Found: {st.session_state.scraping_results.get('records_extracted', 0)}")
            append_log(f"  • Time Elapsed: {st.session_state.scraping_results.get('processing_time', '0m 00s')}")

            if result.get("status") == "Failed":
                st.error("❌ Telegram Scraping Failed")
                st.error(result.get("error_details", ["Unknown error"])[0])
                st.info("💡 **Troubleshooting:**\n"
                       "1. Ensure TELEGRAM_SESSION_STRING is set in Streamlit Secrets\n"
                       "2. Generate a session string from a local Python script\n"
                       "3. Check that your Telegram API credentials are correct\n"
                       "4. Try again in a few minutes (Telegram may be rate-limiting)")
            elif result.get("errors", 0) > 0:
                st.warning("⚠️ Scraping completed with warnings.")
                details = result.get("error_details", [])
                if details:
                    with st.expander("View channel errors"):
                        for item in details[:10]:
                            st.code(item)
            else:
                st.success("✅ Scraping Completed Successfully")

            if result.get("sheet_status") == "not_connected":
                st.info("📋 Google Sheets is not connected for this session, but data is available in the UI.")

        except RuntimeError as exc:
            error_msg = str(exc)
            st.session_state.scraping_status = "Failed"
            st.error(error_msg)
            append_log(f"❌ {error_msg}")
            if "TELEGRAM_SESSION_STRING" in error_msg:
                st.warning("**🔐 Setup required:**\n"
                          "For Streamlit Cloud, add your Telegram session string to Secrets:\n"
                          "1. Run the app locally\n"
                          "2. Go to Scrape Data page → Settings → 'Generate Telegram Session'\n"
                          "3. Copy the session string\n"
                          "4. Paste it into Streamlit Secrets as `TELEGRAM_SESSION_STRING`")
            elif "Timeout" in error_msg:
                st.warning("**⏱️ Connection timeout.**\n"
                          "Telegram servers may be unreachable or overloaded.\n"
                          "Please try again in a few moments.")
        except Exception as exc:
            st.session_state.scraping_status = "Failed"
            st.error(f"❌ Scraping failed: {type(exc).__name__}: {str(exc)[:200]}")
            append_log(f"❌ Scraping failed: {type(exc).__name__}: {str(exc)[:200]}")
            st.info("Check the System Logs for more details.")

        st.session_state.scraping_progress = 100
        progress_bar.progress(100, text="Scraping process finished")

    status_col = st.columns(6)
    with status_col[0]:
        st.metric("Scraping Status", st.session_state.scraping_status)
    with status_col[1]:
        st.metric("Current Channel", st.session_state.selected_channels[0] if st.session_state.selected_channels else "CHA")
    with status_col[2]:
        st.metric("Messages Processed", f"{st.session_state.scraping_results.get('messages_scanned', 0):,}")
    with status_col[3]:
        st.metric("Records Extracted", f"{st.session_state.scraping_results.get('records_extracted', 0):,}")
    with status_col[4]:
        st.metric("New Records", f"{st.session_state.scraping_results.get('new_records', 0):,}")
    with status_col[5]:
        st.metric("Duplicates", f"{st.session_state.scraping_results.get('duplicates', 0):,}")

    st.progress(st.session_state.scraping_progress / 100, text=f"Progress: {st.session_state.scraping_progress}%")

    if st.session_state.scraping_status in {"Completed", "Completed with warnings"}:
        st.markdown("<div class='glass-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
        st.subheader("Scraping Result Summary")
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        with r1:
            st.metric("Total Messages Scanned", f"{st.session_state.scraping_results.get('messages_scanned', 0):,}")
        with r2:
            st.metric("Total Records Extracted", f"{st.session_state.scraping_results.get('records_extracted', 0):,}")
        with r3:
            st.metric("New Records", f"{st.session_state.scraping_results.get('new_records', 0):,}")
        with r4:
            st.metric("Duplicate Records", f"{st.session_state.scraping_results.get('duplicates', 0):,}")
        with r5:
            st.metric("Invalid Records", f"{st.session_state.scraping_results.get('invalid_records', 0):,}")
        with r6:
            st.metric("Errors", f"{st.session_state.scraping_results.get('errors', 0):,}")
        st.metric("Processing Time", st.session_state.scraping_results.get('processing_time', '0m 00s'))
        cexport1, cexport2 = st.columns(2)
        with cexport1:
            st.button("View Customer Records", width="stretch", on_click=go_to_page, args=("Customer Records",))
        with cexport2:
            st.button("Export Results", width="stretch", on_click=go_to_page, args=("Data Export",))
        st.markdown("</div>", unsafe_allow_html=True)


def render_customer_records():
    render_header("Customer Records", "View and analyze customer records collected from Telegram.")

    sheet_df = get_customer_records_with_sheet_headers()
    sheet_columns = sheet_df.columns.tolist()
    live_df = add_customer_filter_columns(sheet_df)
    render_live_sheet_status()
    st.markdown("<div class='glass-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
    st.subheader("Filter Bar")
    channel_options = get_sheet_channel_options(live_df)

    f1, f2, f3 = st.columns(3)
    with f1:
        sender_name_query = st.text_input("Sender Name", key="sender_name_filter")
    with f2:
        date_filter_mode, date_range = render_date_filter(
            "Filter date",
            mode_key="customer_date_filter_mode",
            range_key="customer_date_range",
            default_days=14,
            default_mode="7days last",
        )
    with f3:
        channel_label = st.selectbox("Telegram Channel", list(channel_options), key="customer_channel_filter")
        channel = channel_options[channel_label]

    btn1, btn2 = st.columns(2)
    with btn1:
        st.button("🔄 Refresh", width="stretch", key="customer_refresh_button", on_click=refresh_live_customer_records)
    with btn2:
        st.button("Reset Filters", width="stretch", key="customer_reset_button", on_click=reset_customer_filters)

    df = filter_customer_records(
        live_df,
        sender_name_query=sender_name_query,
        date_range=date_range,
        channel=channel,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Total Records", f"{len(df):,}", "Matching the selected filters", "")
    with k2:
        new_today = int(df["Message Date"].dt.date.eq(NOW.date()).sum()) if "Message Date" in df.columns else 0
        metric_card("New Today", f"{new_today:,}", "Matching the selected filters", "")
    with k3:
        active_channels = int(df["Telegram Channel"].nunique()) if "Telegram Channel" in df.columns else 0
        metric_card("Active Channels", f"{active_channels:,}", "Matching the selected filters", "")
    with k4:
        last_updated = df["Message Date"].max().strftime("%H:%M %p") if "Message Date" in df.columns and not df.empty and pd.notna(df["Message Date"].max()) else "No matching data"
        metric_card("Last Updated", last_updated, NOW.strftime("%d %b %Y"), "")

    display_df = df.reindex(columns=sheet_columns)
    st.dataframe(display_df, width="stretch", height=420, hide_index=True)

    csv = display_df.to_csv(index=False)
    excel_bytes = io.BytesIO()
    display_df.to_excel(excel_bytes, index=False, engine="openpyxl")
    b1, b2 = st.columns(2)
    with b1:
        st.download_button("Download CSV", csv, file_name="customer_records.csv", mime="text/csv")
    with b2:
        st.download_button("Download Excel", excel_bytes.getvalue(), file_name="customer_records.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown("</div>", unsafe_allow_html=True)


def render_scraping_history():
    render_header("Scraping History", "Review historical scraping runs and selected job details.")

    hist = get_scraping_history()
    render_live_sheet_status()
    if hist.empty:
        st.info("No scraping history is available yet. Run a scrape to populate this view.")
        return

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Total Jobs", str(len(hist)), "Across all channels", "")
    with k2:
        metric_card("Successful Jobs", str((hist['Status'] == 'Completed').sum()), "Completed successfully", "")
    with k3:
        metric_card("Failed Jobs", str((hist['Status'] == 'Failed').sum()), "Needs attention", "")
    with k4:
        avg_processing = hist["Processing Time"].dropna().astype(str).str.extract(r"(\d+)m", expand=False).astype(float).mean() if not hist.empty else 0
        metric_card("Average Processing Time", f"{avg_processing:.0f}m", "Across selected jobs", "")

    st.markdown("<div class='glass-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    history_channels = ["All"] + sorted(hist["Channel"].dropna().astype(str).unique().tolist())
    history_statuses = ["All"] + sorted(hist["Status"].dropna().astype(str).unique().tolist())
    with h1:
        date_filter_mode, date_range = render_date_filter(
            "Filter date",
            mode_key="history_date_filter_mode",
            range_key="history_date_range",
            default_days=15,
            default_mode="7days last",
        )
    with h2:
        selected_channel = st.selectbox("Telegram Channel", history_channels, key="history_channel_filter")
    with h3:
        selected_status = st.selectbox("Status", history_statuses, key="history_status_filter")

    filtered_hist = hist.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        history_dates = pd.to_datetime(filtered_hist["Date"], errors="coerce").dt.date
        filtered_hist = filtered_hist[(history_dates >= date_range[0]) & (history_dates <= date_range[1])]
    if selected_channel != "All":
        filtered_hist = filtered_hist[filtered_hist["Channel"].astype(str) == selected_channel]
    if selected_status != "All":
        filtered_hist = filtered_hist[filtered_hist["Status"] == selected_status]

    if filtered_hist.empty:
        st.info("No scraping jobs match the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    job_selection = st.dataframe(
        filtered_hist,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="history_jobs_table",
    )
    selected_rows = job_selection.selection.rows
    selected_index = selected_rows[0] if selected_rows and selected_rows[0] < len(filtered_hist) else 0
    selected_job = filtered_hist.iloc[selected_index]
    st.session_state.selected_job = selected_job

    st.subheader("Job Details")
    st.write(selected_job.to_dict())
    st.markdown("</div>", unsafe_allow_html=True)


def render_telegram_channels():
    render_header("Telegram Channel Monitoring", "Track channel status, activity, and recent scrape health.")

    channel_df = get_channel_summary()
    render_live_sheet_status()
    total_channels = len(channel_df)
    active_channels = int((channel_df["Status"] == "🟢 Active").sum()) if not channel_df.empty else 0
    inactive_channels = max(total_channels - active_channels, 0)
    last_activity = NOW.strftime("%H:%M %p")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Total Channels", f"{total_channels:,}", "Configured channels", "")
    with k2:
        metric_card("Active Channels", f"{active_channels:,}", "Currently healthy", "")
    with k3:
        metric_card("Inactive Channels", f"{inactive_channels:,}", "Requires review", "")
    with k4:
        metric_card("Last Activity", last_activity, NOW.strftime("%d %b %Y"), "")

    with st.expander("Add Telegram Channel"):
        c_name = st.text_input("Channel Name")
        c_id = st.text_input("Channel ID")
        c_desc = st.text_area("Channel Description")
        c_status = st.selectbox("Status", ["Active", "Inactive", "Warning"])
        if st.button("Save Channel", type="primary"):
            st.success("Channel saved to session state for future integration.")

    df = get_channel_summary()
    st.dataframe(df, width="stretch", hide_index=True)


def render_analytics():
    render_header("Customer Data Analytics", "Monitor platform performance and record trends.")

    sheet_df = get_customer_records_with_sheet_headers()
    live_df = normalize_live_sheet_for_dashboard(sheet_df)
    render_live_sheet_status()
    if "Message Date" in live_df.columns:
        live_df["Message Date"] = pd.to_datetime(live_df["Message Date"], errors="coerce")

    analytics_df = live_df.copy()
    analytics_filter_mode, analytics_date_range = render_date_filter(
        "Filter date",
        mode_key="analytics_date_filter_mode",
        range_key="analytics_date_range",
        default_days=30,
        default_mode="7days last",
    )
    if "Message Date" in analytics_df.columns and analytics_date_range:
        if isinstance(analytics_date_range, tuple) and len(analytics_date_range) == 2:
            record_dates = analytics_df["Message Date"].dt.date
            analytics_df = analytics_df[(record_dates >= analytics_date_range[0]) & (record_dates <= analytics_date_range[1])]

    snapshot = {
        "total_records": len(analytics_df),
        "top_channel": analytics_df["Telegram Channel"].value_counts().idxmax() if "Telegram Channel" in analytics_df.columns and not analytics_df.empty else "N/A",
    }
    top_sender = "N/A"
    top_sender_count = 0
    sender_columns = [column for column in ("Customer Name", "Sender_Name", "Sender Name", "Name") if column in analytics_df.columns]
    if sender_columns and not analytics_df.empty:
        sender_series = analytics_df[sender_columns[0]].fillna("").astype(str).str.strip()
        sender_series = sender_series[(sender_series != "") & (sender_series.str.casefold() != "bp_bot")]
        if not sender_series.empty:
            sender_counts = sender_series.value_counts()
            top_sender = sender_counts.idxmax()
            top_sender_count = int(sender_counts.max())

    potential_series = analytics_df["Potential_Level"].fillna("").astype(str).str.strip().str.upper() if "Potential_Level" in analytics_df.columns else pd.Series(dtype=str)

    def count_potential(level_code: str) -> int:
        if potential_series.empty:
            return 0
        if level_code == "H":
            return int((potential_series.str.startswith("H") | potential_series.str.contains("HIGH", case=False, na=False)).sum())
        if level_code == "M":
            return int((potential_series.str.startswith("M") | potential_series.str.contains("MED", case=False, na=False)).sum())
        if level_code == "L":
            return int((potential_series.str.startswith("L") | potential_series.str.contains("LOW", case=False, na=False)).sum())
        return 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Total Records", f"{snapshot['total_records']:,}", "Total customer records", "")
    with k2:
        if analytics_date_range and isinstance(analytics_date_range, tuple) and len(analytics_date_range) == 2:
            selected_days = max(1, (analytics_date_range[1] - analytics_date_range[0]).days + 1)
        elif "Message Date" in analytics_df.columns and not analytics_df.empty:
            date_values = analytics_df["Message Date"].dropna().dt.date
            selected_days = max(1, (date_values.max() - date_values.min()).days + 1) if not date_values.empty else 1
        else:
            selected_days = 1
        metric_card("Average Daily Records", f"{(snapshot['total_records'] / selected_days):.0f}", "For the selected date range", "")
    with k3:
        metric_card("Top Channel", snapshot['top_channel'], "Highest record volume", "", compact_value=True)
    with k4:
        metric_card("Top Sender", top_sender, f"{top_sender_count:,} records", "", compact_value=True)

    st.markdown("<div style='height: 0.9rem;'></div>", unsafe_allow_html=True)

    k5, k6, k7 = st.columns(3)
    with k5:
        metric_card("Total High Potentail (H)", f"{count_potential('H'):,}", "Counted from Potential_Level", "")
    with k6:
        metric_card("Total Meduim Potentail (M)", f"{count_potential('M'):,}", "Counted from Potential_Level", "")
    with k7:
        metric_card("Total Low Potentail (L)", f"{count_potential('L'):,}", "Counted from Potential_Level", "")

    st.markdown("<div style='height: 1.35rem;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        trend_data = analytics_df.groupby(analytics_df["Message Date"].dt.date).size().reset_index(name="Records") if "Message Date" in analytics_df.columns else pd.DataFrame(columns=["Date", "Records"])
        trend_data = trend_data.rename(columns={"Message Date": "Date"})
        fig = px.line(trend_data, x="Date", y="Records", title="Records Trend", template="plotly_white")
        fig.update_traces(line_color="#0d5c45", line_width=3)
        st.plotly_chart(fig, width="stretch")
    with c2:
        channel_df = analytics_df.groupby("Telegram Channel").size().reset_index(name="Records") if "Telegram Channel" in analytics_df.columns else pd.DataFrame(columns=["Channel", "Records"])
        channel_df = channel_df.rename(columns={"Telegram Channel": "Channel"})
        fig = px.bar(channel_df, x="Channel", y="Records", title="Records by Channel", template="plotly_white")
        fig.update_traces(marker_color="#0d5c45")
        st.plotly_chart(fig, width="stretch")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("KPI Breakdown")

    sender_source = None
    for column in ("Sender_Name", "Sender Name", "Customer Name", "Name"):
        if column in analytics_df.columns:
            sender_source = column
            break

    if sender_source:
        sender_breakdown = (
            analytics_df[analytics_df[sender_source].fillna("").astype(str).str.strip() != ""]
            .assign(Sender=analytics_df[sender_source].fillna("").astype(str).str.strip())
            .query('Sender.str.casefold() != "bp_bot"', engine="python")
            .groupby("Sender")
            .size()
            .reset_index(name="Leads Total")
            .sort_values("Leads Total", ascending=False)
        )
    else:
        sender_breakdown = pd.DataFrame(columns=["Sender", "Leads Total"])

    if "Potential_Product" in analytics_df.columns:
        product_breakdown = (
            analytics_df[analytics_df["Potential_Product"].fillna("").astype(str).str.strip() != ""]
            .assign(**{"Product Type": analytics_df["Potential_Product"].fillna("").astype(str).str.strip()})
            .groupby("Product Type")
            .size()
            .reset_index(name="Total")
            .sort_values("Total", ascending=False)
        )
    else:
        product_breakdown = pd.DataFrame(columns=["Product Type", "Total"])

    if "Business" in analytics_df.columns:
        business_breakdown = (
            analytics_df[analytics_df["Business"].fillna("").astype(str).str.strip() != ""]
            .assign(**{"Business Type": analytics_df["Business"].fillna("").astype(str).str.strip()})
            .groupby("Business Type")
            .size()
            .reset_index(name="Total")
            .sort_values("Total", ascending=False)
        )
    else:
        business_breakdown = pd.DataFrame(columns=["Business Type", "Total"])

    if "Bank" in analytics_df.columns:
        bank_breakdown = (
            analytics_df[analytics_df["Bank"].fillna("").astype(str).str.strip() != ""]
            .assign(**{"Competitor Bank": analytics_df["Bank"].fillna("").astype(str).str.strip()})
            .groupby("Competitor Bank")
            .size()
            .reset_index(name="Total")
            .sort_values("Total", ascending=False)
        )
    else:
        bank_breakdown = pd.DataFrame(columns=["Competitor Bank", "Total"])

    if "Telegram Channel" in analytics_df.columns:
        source_breakdown = (
            analytics_df[analytics_df["Telegram Channel"].fillna("").astype(str).str.strip() != ""]
            .assign(**{"Source Channels": analytics_df["Telegram Channel"].fillna("").astype(str).str.strip()})
            .groupby("Source Channels")
            .size()
            .reset_index(name="Total Sent")
            .sort_values("Total Sent", ascending=False)
        )
        if not source_breakdown.empty:
            source_breakdown["% of Total"] = (source_breakdown["Total Sent"] / max(len(analytics_df), 1) * 100).round(1).astype(str) + "%"
    else:
        source_breakdown = pd.DataFrame(columns=["Source Channels", "Total Sent", "% of Total"])

    unique_customer_total = 0
    unique_customer_source = None
    for column in ("Phone Number", "Tel", "Customer Name", "Sender_Name", "Name"):
        if column in analytics_df.columns:
            unique_customer_source = column
            break
    if unique_customer_source:
        unique_customer_total = int(
            analytics_df[unique_customer_source].fillna("").astype(str).str.strip().replace("", pd.NA).dropna().nunique()
        )

    def chart_card(title: str):
        return st.container()

    st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)
    kpi_top_1, kpi_top_2 = st.columns([1, 4])
    with kpi_top_1:
        metric_card("Unique Customers", f"{unique_customer_total:,}", "Live unique customer count", "")
    with kpi_top_2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("KPI Breakdown")

        def make_bar_frame(frame: pd.DataFrame, label_col: str, value_col: str, limit: int = 8) -> pd.DataFrame:
            if frame.empty:
                return frame
            return frame.head(limit).copy()

        chart_row_1, chart_row_2 = st.columns(2)

        with chart_row_1:
            st.caption("Sender")
            if not sender_breakdown.empty:
                sender_chart = make_bar_frame(sender_breakdown, "Sender", "Leads Total")
                fig = px.bar(sender_chart, x="Leads Total", y="Sender", orientation="h", template="plotly_white")
                fig.update_traces(marker_color="#0d5c45", text=sender_chart["Leads Total"], textposition="outside")
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Leads Total", yaxis_title="")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No sender data available.")

        with chart_row_2:
            st.caption("Product Type")
            if not product_breakdown.empty:
                product_chart = make_bar_frame(product_breakdown, "Product Type", "Total")
                fig = px.bar(product_chart, x="Total", y="Product Type", orientation="h", template="plotly_white")
                fig.update_traces(marker_color="#147d57", text=product_chart["Total"], textposition="outside")
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Total", yaxis_title="")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No product type data available.")

        chart_row_3, chart_row_4 = st.columns(2)
        with chart_row_3:
            st.caption("Business Type")
            if not business_breakdown.empty:
                business_chart = make_bar_frame(business_breakdown, "Business Type", "Total")
                fig = px.bar(business_chart, x="Total", y="Business Type", orientation="h", template="plotly_white")
                fig.update_traces(marker_color="#1f9d55", text=business_chart["Total"], textposition="outside")
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Total", yaxis_title="")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No business type data available.")

        with chart_row_4:
            st.caption("Competitor Bank")
            if not bank_breakdown.empty:
                bank_chart = make_bar_frame(bank_breakdown, "Competitor Bank", "Total")
                fig = px.bar(bank_chart, x="Total", y="Competitor Bank", orientation="h", template="plotly_white")
                fig.update_traces(marker_color="#0f6f8f", text=bank_chart["Total"], textposition="outside")
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Total", yaxis_title="")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No competitor bank data available.")

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        st.caption("Source Channels")
        if not source_breakdown.empty:
            source_chart = make_bar_frame(source_breakdown, "Source Channels", "Total Sent")
            fig = px.bar(source_chart, x="Total Sent", y="Source Channels", orientation="h", template="plotly_white")
            fig.update_traces(
                marker_color="#0d5c45",
                text=source_chart["% of Total"] if "% of Total" in source_chart.columns else source_chart["Total Sent"],
                textposition="outside",
            )
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Total Sent", yaxis_title="")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No source channel data available.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_data_export():
    render_header("Data Export", "Export customer records and scraping results.")

    source_df = get_customer_records().copy()
    render_live_sheet_status()
    business_options = ["All"] + sorted(
        source_df["Business Type"].dropna().astype(str).loc[lambda values: values.str.strip() != ""].unique().tolist()
    ) if "Business Type" in source_df.columns else ["All"]
    channel_options = get_sheet_channel_options(source_df)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_filter_mode, date_range = render_date_filter(
            "Filter date",
            mode_key="export_date_filter_mode",
            range_key="export_date_range",
            default_days=14,
            default_mode="7days last",
        )
    with f2:
        channel_label = st.selectbox("Telegram Channel", list(channel_options), key="export_channel_filter")
        channel = channel_options[channel_label]
    with f3:
        business_type = st.selectbox("Business Type", business_options, key="export_business_filter")
    with f4:
        st.caption("Exports contain only records matching these filters.")

    st.markdown("<div class='glass-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
    st.subheader("Export Summary")
    export_df = filter_customer_records(
        source_df,
        date_range=date_range,
        channel=channel,
        business_type=business_type,
    )
    st.metric("Records Available for Export", f"{len(export_df):,}")
    csv_bytes = export_df.to_csv(index=False).encode()
    excel_bytes = io.BytesIO()
    export_df.to_excel(excel_bytes, index=False, engine="openpyxl")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 Export CSV", csv_bytes, file_name="scraping_export.csv", mime="text/csv")
    with c2:
        st.download_button("📊 Export Excel", excel_bytes.getvalue(), file_name="scraping_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown("</div>", unsafe_allow_html=True)


def go_to_page(page_name: str) -> None:
    st.session_state.current_page = page_name
    st.rerun()


def render_system_logs():
    render_header("System Logs", "Review operational activity and support-level events.")

    logs = get_logs()
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        selected_date = st.date_input("Date", value=NOW.date(), key="logs_date")
    with l2:
        selected_level = st.selectbox("Log Level", ["All"] + sorted(logs["Level"].unique().tolist()), key="logs_level")
    with l3:
        selected_module = st.selectbox("Module", ["All"] + sorted(logs["Module"].unique().tolist()), key="logs_module")
    with l4:
        search_query = st.text_input("Search", key="logs_search")

    filtered_logs = logs[logs["Date"] == selected_date]
    if selected_level != "All":
        filtered_logs = filtered_logs[filtered_logs["Level"] == selected_level]
    if selected_module != "All":
        filtered_logs = filtered_logs[filtered_logs["Module"] == selected_module]
    if search_query:
        filtered_logs = filtered_logs[
            filtered_logs["Log"].str.contains(search_query, case=False, na=False)
        ]

    st.markdown("<div class='log-panel'>", unsafe_allow_html=True)
    if filtered_logs.empty:
        st.write("No logs match the selected filters.")
    for log in filtered_logs["Log"].tolist():
        st.markdown(log)
    st.markdown("</div>", unsafe_allow_html=True)


def render_settings():
    render_header("System Settings", "Configure dashboard behavior and live data integrations.")

    st.subheader("Telegram Configuration")
    st.metric("API Status", "🟢 Connected")
    st.caption("API credentials remain stored in the backend environment.")

    st.subheader("Google Sheets Configuration")
    st.metric("Connection Status", "🟢 Connected")
    st.info("Live sheet data is used for the dashboard and export views.")
    st.metric("Spreadsheet Name", SHEET_ID[:12] + "...")
    st.metric("Worksheet", WORKSHEET_NAME)

    st.subheader("Application Settings")
    st.checkbox("Auto Refresh", value=True, key="settings_auto_refresh")
    st.checkbox("Enable Notifications", value=True, key="settings_notifications")
    st.selectbox("Default Date Range", ["Last 7 Days", "Last 30 Days", "Custom Range"], key="settings_date_range")
    st.multiselect("Default Channels", CHANNELS, default=CHANNELS[:2], key="settings_default_channels")

    st.subheader("Appearance")
    st.selectbox("Theme", ["Corporate Light", "Corporate Dark"], key="settings_theme")


def render_all_in_one():
    render_dashboard()

    st.divider()
    with st.expander("Scrape Data", expanded=False):
        render_scrape_data()

    st.divider()
    with st.expander("Customer Records", expanded=False):
        render_customer_records()

    st.divider()
    with st.expander("Scraping History", expanded=False):
        render_scraping_history()

    st.divider()
    with st.expander("Telegram Channels", expanded=False):
        render_telegram_channels()

    st.divider()
    with st.expander("Analytics", expanded=False):
        render_analytics()

    st.divider()
    with st.expander("Data Export", expanded=False):
        render_data_export()

    st.divider()
    with st.expander("System Logs", expanded=False):
        render_system_logs()

    st.divider()
    with st.expander("Settings", expanded=False):
        render_settings()


# ---------------------------
# Main UI flow
# ---------------------------
render_sidebar()

if st.session_state.current_page == "All-in-One":
    render_all_in_one()
elif st.session_state.current_page == "Dashboard":
    render_dashboard()
elif st.session_state.current_page == "Scrape Data":
    render_scrape_data()
elif st.session_state.current_page == "Customer Records":
    render_customer_records()
elif st.session_state.current_page == "Scraping History":
    render_scraping_history()
elif st.session_state.current_page == "Telegram Channels":
    render_telegram_channels()
elif st.session_state.current_page == "Analytics":
    render_analytics()
elif st.session_state.current_page == "Data Export":
    render_data_export()
elif st.session_state.current_page == "System Logs":
    render_system_logs()
else:
    render_settings()
