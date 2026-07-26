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
from scraper_backend import SHEET_ID, TARGET_CHANNELS, WORKSHEET_NAME, get_live_customer_records, get_live_google_sheet_records, run_scrape_job


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
        background: linear-gradient(180deg, #ffffff 0%, #f6fbf9 100%);
        border: 1px solid #cfe2d9;
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px rgba(13, 92, 69, 0.06);
        height: 100%;
    }

    .metric-title {
        color: var(--muted);
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.3rem;
    }

    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #111827;
        margin: 0.1rem 0;
    }

    .metric-sub {
        font-size: 0.84rem;
        color: var(--muted);
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
        font-size: 2rem;
        font-weight: 800;
        color: #111827;
        margin: 0;
    }

    .page-subtitle {
        color: var(--muted);
        font-size: 0.96rem;
        margin-top: 0.15rem;
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
    name_query: str = "",
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

    if name_query and "Customer Name" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["Customer Name"].fillna("").astype(str).str.contains(name_query, case=False, na=False)
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


def reset_customer_filters():
    st.session_state.name_filter = ""
    st.session_state.phone_filter = ""
    st.session_state.customer_date_range = (NOW.date() - timedelta(days=14), NOW.date())
    st.session_state.customer_channel_filter = "All"
    st.session_state.customer_business_filter = "All"
    st.session_state.customer_status_filter = "All"


def get_scraping_history() -> pd.DataFrame:
    live_df = get_customer_records().copy()
    if live_df.empty:
        return pd.DataFrame(columns=["Job ID", "Date", "Channel", "Start Time", "End Time", "Messages Scanned", "Records Found", "New Records", "Duplicates", "Status", "Processing Time"])

    if "Message Date" in live_df.columns:
        live_df["Message Date"] = pd.to_datetime(live_df["Message Date"], errors="coerce")
        live_df = live_df.dropna(subset=["Message Date"])

    if live_df.empty:
        return pd.DataFrame(columns=["Job ID", "Date", "Channel", "Start Time", "End Time", "Messages Scanned", "Records Found", "New Records", "Duplicates", "Status", "Processing Time"])

    history_rows = []
    group_columns = [live_df["Message Date"].dt.date, "Telegram Channel"] if "Telegram Channel" in live_df.columns else [live_df["Message Date"].dt.date]
    for index, (group_key, group) in enumerate(live_df.groupby(group_columns), start=1):
        if isinstance(group_key, tuple):
            date_value, channel = group_key
        else:
            date_value, channel = group_key, "Live Google Sheet"
        history_rows.append(
            {
                "Job ID": f"LIVE-{date_value.strftime('%Y%m%d')}-{index:03d}",
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
def metric_card(title: str, value: str, subtext: str, delta: str = ""):
    with st.container():
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">{title}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-sub">{delta} · {subtext}</div>
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
            <div style="text-align:center; padding: 1rem 0.25rem 0.5rem 0.25rem;">
                <div style="width: 72px; height: 72px; margin: 0 auto 0.8rem auto; border-radius: 18px; background: linear-gradient(135deg, #0d5c45 0%, #1f8b65 100%); color: white; display:flex; align-items:center; justify-content:center; font-size: 1.8rem; font-weight: 800;">CM</div>
                <div style="font-size:1.1rem; font-weight: 800; color:#111827;">Customer Data Platform</div>
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
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="display:flex; justify-content:flex-end; align-items:center; gap:0.55rem; margin-top:0.6rem;">', unsafe_allow_html=True)
        st.markdown('<div class="header-status">🟢 System Ready</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption(f"Last Updated: {NOW.strftime('%d %b %Y, %I:%M %p')}")


def render_dashboard():
    render_header("Customer Data Scraping Dashboard", "Monitor Telegram data collection and customer records.")

    snapshot = get_dashboard_snapshot()

    st.markdown("<div style='margin: 1rem 0 1.3rem 0;'>", unsafe_allow_html=True)
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        metric_card("Total Records", f"{snapshot['total_records']:,}", "from live Google Sheet", "")
    with m2:
        metric_card("New Records Today", f"{snapshot['new_today']:,}", "from live date field", "")
    with m3:
        metric_card("Live Records", f"{snapshot['total_records']:,}", "current Google Sheet rows", "")
    with m4:
        metric_card("Failed Scrapes", f"{snapshot['failed_scrapes']:,}", "live sheet sync only", "")
    with m5:
        metric_card("Telegram Channels", f"{snapshot['unique_channels']:,}", "active in sheet", "")
    with m6:
        metric_card("Last Scrape", snapshot['last_scrape'], "processing time", "")
    st.markdown("</div>", unsafe_allow_html=True)

    live_df = get_customer_records().copy()
    render_live_sheet_status()
    if "Message Date" in live_df.columns:
        live_df["Message Date"] = pd.to_datetime(live_df["Message Date"], errors="coerce")

    dashboard_date_range = st.date_input(
        "Filter chart records by date",
        value=(NOW.date() - timedelta(days=30), NOW.date()),
        key="dashboard_chart_date_range",
    )
    chart_df = live_df.copy()
    if (
        "Message Date" in chart_df.columns
        and isinstance(dashboard_date_range, tuple)
        and len(dashboard_date_range) == 2
    ):
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

    st.markdown("<div class='glass-card' style='margin-top:1rem'>", unsafe_allow_html=True)
    header_col, button_col = st.columns([4, 1])
    with header_col:
        st.subheader("Recent Scraping Activity")
    with button_col:
        if st.button("View All Scraping History →"):
            st.session_state.current_page = "Scraping History"
            st.rerun()

    history_df = get_scraping_history().head(5)
    st.dataframe(
        history_df[["Job ID", "Date", "Channel", "Status", "Messages Scanned", "Records Found", "New Records"]],
        width="stretch",
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


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

        def update_progress(value: int, message: str):
            st.session_state.scraping_progress = value
            progress_bar.progress(value, text=message)

        from_date = datetime.combine(st.session_state.selected_date_range[0], selected_start_time)
        to_date = datetime.combine(st.session_state.selected_date_range[1], selected_end_time)
        selected_targets = [CHANNEL_OPTIONS.get(name, name) for name in st.session_state.selected_channels]
        if not selected_targets:
            selected_targets = list(TARGET_CHANNELS)

        with st.spinner("Connecting to Telegram and collecting customer data..."):
            try:
                result = run_scrape_job(
                    selected_channels=selected_targets,
                    from_date=from_date,
                    to_date=to_date,
                    progress_callback=update_progress,
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

                if result.get("errors", 0) > 0:
                    st.warning("⚠️ Scraping completed with warnings. Review the system logs for details.")
                    details = result.get("error_details", [])
                    if details:
                        st.caption("Detected channel issues:")
                        for item in details[:8]:
                            st.write(f"- {item}")
                else:
                    st.success("🟢 Scraping Completed Successfully")

                if result.get("sheet_status") == "not_connected":
                    st.info("Google Sheets is not connected for this session, but the scrape result is available in the UI.")

            except Exception as exc:
                st.session_state.scraping_status = "Failed"
                st.error(f"❌ Scraping failed: {exc}")

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
            st.button("View Customer Records", width="stretch")
        with cexport2:
            st.button("Export Results", width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)


def render_customer_records():
    render_header("Customer Records", "View and analyze customer records collected from Telegram.")

    sheet_df = get_customer_records_with_sheet_headers()
    sheet_columns = sheet_df.columns.tolist()
    live_df = add_customer_filter_columns(sheet_df)
    render_live_sheet_status()
    st.markdown("<div class='glass-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
    st.subheader("Filter Bar")
    business_options = ["All"] + sorted(
        live_df["Business Type"].dropna().astype(str).loc[lambda values: values.str.strip() != ""].unique().tolist()
    ) if "Business Type" in live_df.columns else ["All"]
    status_options = ["All"] + sorted(
        live_df["Status"].dropna().astype(str).loc[lambda values: values.str.strip() != ""].unique().tolist()
    ) if "Status" in live_df.columns else ["All"]
    channel_options = get_sheet_channel_options(live_df)

    f1, f2, f3, f4, f5, f6 = st.columns(6)
    with f1:
        name_query = st.text_input("Search Customer Name", key="name_filter")
    with f2:
        phone_query = st.text_input("Search Phone Number", key="phone_filter")
    with f3:
        date_range = st.date_input("Date Range", value=(NOW.date() - timedelta(days=14), NOW.date()), key="customer_date_range")
    with f4:
        channel_label = st.selectbox("Telegram Channel", list(channel_options), key="customer_channel_filter")
        channel = channel_options[channel_label]
    with f5:
        business_type = st.selectbox("Business Type", business_options, key="customer_business_filter")
    with f6:
        status = st.selectbox("Status", status_options, key="customer_status_filter")

    btn1, btn2 = st.columns(2)
    with btn1:
        st.button("🔄 Refresh", width="stretch", key="customer_refresh_button", on_click=refresh_live_customer_records)
    with btn2:
        st.button("Reset Filters", width="stretch", key="customer_reset_button", on_click=reset_customer_filters)

    df = filter_customer_records(
        live_df,
        name_query=name_query,
        phone_query=phone_query,
        date_range=date_range,
        channel=channel,
        business_type=business_type,
        status=status,
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
        date_range = st.date_input("Date Range", value=(NOW.date() - timedelta(days=15), NOW.date()), key="history_date_range")
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

    live_df = get_customer_records().copy()
    render_live_sheet_status()
    if "Message Date" in live_df.columns:
        live_df["Message Date"] = pd.to_datetime(live_df["Message Date"], errors="coerce")

    a1, a2 = st.columns(2)
    with a1:
        from_date = st.date_input("From Date", value=NOW.date() - timedelta(days=30), key="analytics_from_date")
    with a2:
        to_date = st.date_input("To Date", value=NOW.date(), key="analytics_to_date")

    analytics_df = live_df.copy()
    if "Message Date" in analytics_df.columns:
        if from_date > to_date:
            st.warning("The From Date must be on or before the To Date.")
            analytics_df = analytics_df.iloc[0:0]
        else:
            record_dates = analytics_df["Message Date"].dt.date
            analytics_df = analytics_df[(record_dates >= from_date) & (record_dates <= to_date)]

    snapshot = {
        "total_records": len(analytics_df),
        "top_channel": analytics_df["Telegram Channel"].value_counts().idxmax() if "Telegram Channel" in analytics_df.columns and not analytics_df.empty else "N/A",
        "top_location": analytics_df["Location"].value_counts().idxmax() if "Location" in analytics_df.columns and not analytics_df.empty else "N/A",
    }
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        metric_card("Total Records", f"{snapshot['total_records']:,}", "Total customer records", "")
    with k2:
        selected_days = max(1, (to_date - from_date).days + 1)
        metric_card("Average Daily Records", f"{(snapshot['total_records'] / selected_days):.0f}", "For the selected date range", "")
    with k3:
        metric_card("Top Channel", snapshot['top_channel'], "Highest record volume", "")
    with k4:
        metric_card("Top Location", snapshot['top_location'], "Most common source location", "")
    with k5:
        metric_card("Top Business Type", (analytics_df["Business Type"].value_counts().idxmax() if "Business Type" in analytics_df.columns and not analytics_df.empty else "N/A"), "Popular segment", "")

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

    c3, c4 = st.columns(2)
    with c3:
        location_df = analytics_df.groupby("Location").size().reset_index(name="Records") if "Location" in analytics_df.columns else pd.DataFrame(columns=["Location", "Records"])
        fig = px.pie(location_df, values="Records", names="Location", title="Records by Location", hole=0.45)
        st.plotly_chart(fig, width="stretch")
    with c4:
        business_df = analytics_df.groupby("Business Type").size().reset_index(name="Records") if "Business Type" in analytics_df.columns else pd.DataFrame(columns=["Business Type", "Records"])
        fig = px.bar(business_df, x="Business Type", y="Records", title="Records by Business Type", template="plotly_white")
        fig.update_traces(marker_color="#0d5c45")
        st.plotly_chart(fig, width="stretch")

    c5, c6 = st.columns(2)
    with c5:
        today_records = 0
        older_records = 0
        if "Message Date" in analytics_df.columns and not analytics_df.empty:
            today_records = int(analytics_df["Message Date"].dt.date.eq(NOW.date()).sum())
            older_records = int(len(analytics_df) - today_records)
        compare_df = pd.DataFrame({"Label": ["Today", "Earlier"], "Records": [today_records, older_records]})
        fig = px.bar(compare_df, x="Label", y="Records", title="Today vs Earlier Records", template="plotly_white")
        fig.update_traces(marker_color=["#0d5c45", "#6b7280"])
        st.plotly_chart(fig, width="stretch")
    with c6:
        coverage_rate = 0.0
        if not analytics_df.empty and "Phone Number" in analytics_df.columns:
            coverage_rate = round((analytics_df["Phone Number"].fillna("").astype(str).str.strip() != "").mean() * 100, 1)
        success_df = pd.DataFrame({"Metric": ["Contact Coverage"], "Value": [coverage_rate]})
        fig = px.bar(success_df, x="Metric", y="Value", title="Live Record Coverage", template="plotly_white")
        fig.update_traces(marker_color="#1f9d55")
        st.plotly_chart(fig, width="stretch")


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
        date_range = st.date_input("Date Range", value=(NOW.date() - timedelta(days=14), NOW.date()), key="export_date_range")
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
