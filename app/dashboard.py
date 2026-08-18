from datetime import datetime, timedelta, timezone

import altair as alt
import pandas as pd
import streamlit as st

from app.database.audit import get_recent_workflow_runs
from app.gmail.inbox_processor import is_finance_email
from app.gmail.mailbox_service import list_business_inbox_messages


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="EMAIL ASSISTANT DASHBOARD",
    page_icon="✉",
    layout="wide",
    initial_sidebar_state="expanded",
)

AUTO_REFRESH_MS = 15000
BENCHMARK_MEDIAN_SECONDS = 6.4


# ============================================================
# DARK BUSINESS DASHBOARD STYLE
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 12% 0%,
                rgba(70, 66, 140, 0.16),
                transparent 30%
            ),
            radial-gradient(
                circle at 90% 5%,
                rgba(0, 145, 175, 0.09),
                transparent 25%
            ),
            #07090D;
        color: #F3F5F8;
    }

    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        background: transparent;
    }

    [data-testid="stToolbar"] {
        display: none;
    }

    [data-testid="stSidebar"] {
        background: #090B10;
        border-right: 1px solid #202630;
    }

    .main .block-container {
        max-width: 1500px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background:
            linear-gradient(
                145deg,
                #121721,
                #0C1016
            );
        border: 1px solid #252C38;
        border-radius: 16px;
        padding: 16px 18px;
        min-height: 120px;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.20);
    }

    [data-testid="stMetricLabel"] {
        color: #7E899B !important;
        font-size: 0.76rem !important;
        font-weight: 650 !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
    }

    .section-title {
        color: #F4F7FA;
        font-size: 1.08rem;
        font-weight: 750;
        margin-top: 22px;
        margin-bottom: 4px;
    }

    .section-caption {
        color: #697487;
        font-size: 0.78rem;
        margin-bottom: 12px;
    }

    .summary-card {
        background:
            linear-gradient(
                145deg,
                #11151D,
                #0C0F15
            );
        border: 1px solid #242B37;
        border-radius: 15px;
        padding: 17px;
    }

    .summary-label {
        color: #687286;
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .summary-value {
        color: #F1F4F8;
        font-size: 1rem;
        font-weight: 650;
        margin-top: 6px;
    }

    .footer {
        color: #596274;
        text-align: center;
        font-size: 0.72rem;
        margin-top: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AUTO REFRESH
# ============================================================

try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(
        interval=AUTO_REFRESH_MS,
        key="email_assistant_dashboard_refresh",
    )

except ImportError:
    pass


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("EMAIL ASSISTANT")

    st.caption("Business Operations Dashboard")

    st.divider()

    if st.button(
        "Refresh Dashboard",
        width="stretch",
    ):
        st.rerun()

    recent_limit = st.slider(
        "Recent emails",
        min_value=10,
        max_value=100,
        value=25,
        step=5,
    )

    st.divider()

    st.caption("DATA SOURCES")
    st.caption("Live Gmail Inbox")
    st.caption("Workflow audit database")
    st.caption("Auto refresh: 15 seconds")


# ============================================================
# REAL GMAIL INBOX
# ============================================================

try:
    inbox_messages = list_business_inbox_messages()

except Exception as exc:

    st.error(
        f"Unable to read Gmail inbox: {exc}"
    )

    st.stop()


# ============================================================
# FINANCE EMAILS ONLY
# ============================================================

finance_messages = [
    message
    for message in inbox_messages
    if is_finance_email(
        subject=message.get("subject", ""),
        email_body=message.get("email_body", ""),
    )
]


# ============================================================
# LOAD WORKFLOW AUDIT
# ============================================================

audit_runs = get_recent_workflow_runs(
    limit=500
)


audit_by_message_id = {}

for run in audit_runs:

    message_id = run.get(
        "incoming_message_id"
    )

    if message_id:

        key = str(message_id)
        existing = audit_by_message_id.get(key)

        # Always keep the newest audit record for the Gmail message.
        if (
            existing is None
            or int(run.get("id", 0) or 0) > int(existing.get("id", 0) or 0)
        ):
            audit_by_message_id[key] = run


# ============================================================
# MAP FINANCE EMAILS TO BUSINESS STATUS
# ============================================================

business_rows = []

for message in finance_messages:

    message_id = str(
        message.get(
            "message_id",
            "",
        )
    )

    audit = audit_by_message_id.get(
        message_id
    )

    if audit:

        final_send_status = str(
            audit.get(
                "final_send_status",
                "",
            )
        ).upper()

        if final_send_status == "SENT":

            status = "Answered"

        elif final_send_status == "SEND_FAILED":

            status = "Exception"

        elif final_send_status == "NOT_SENT":

            status = "Exception"

        else:

            status = "Processed"

        response_time_ms = audit.get(
            "total_ms"
        )

        action_taken = audit.get(
            "action_taken",
            "",
        )

    else:

        # A finance email in Gmail which has not yet
        # been processed by the automation.
        status = "New"

        response_time_ms = None

        action_taken = (
            "New finance email awaiting automation."
        )

    business_rows.append(
        {
            "message_id": message_id,
            "thread_id": message.get(
                "thread_id"
            ),
            "sender_email": message.get(
                "sender_email",
                "",
            ),
            "subject": message.get(
                "subject",
                "",
            ),
            "received_date": message.get(
                "date",
                "",
            ),
            "email_body": message.get(
                "email_body",
                "",
            ),
            "status": status,
            "response_time_ms": response_time_ms,
            "action_taken": action_taken,
        }
    )


business_df = pd.DataFrame(
    business_rows
)


# ============================================================
# BUSINESS KPIs
# ============================================================

emails_received = len(
    business_df
)

emails_processed = int(
    business_df["status"]
    .isin(
        [
            "Answered",
            "Exception",
            "Processed",
        ]
    )
    .sum()
) if not business_df.empty else 0

emails_answered = int(
    (
        business_df["status"]
        == "Answered"
    ).sum()
) if not business_df.empty else 0

exceptions = int(
    (
        business_df["status"]
        == "Exception"
    ).sum()
) if not business_df.empty else 0

new_finance_emails = int(
    (
        business_df["status"]
        == "New"
    ).sum()
) if not business_df.empty else 0


if emails_received:

    response_rate = (
        emails_answered
        / emails_received
        * 100
    )

else:

    response_rate = 0.0


# ============================================================
# RESPONSE TIME
# ============================================================

response_times = pd.to_numeric(
    business_df["response_time_ms"],
    errors="coerce",
).dropna() if not business_df.empty else pd.Series(
    dtype=float
)

if len(response_times):

    average_response_time = (
        response_times.mean()
        / 1000
    )

else:

    average_response_time = 0.0


# ============================================================
# NEW EMAILS IN LAST 15 MINUTES
# ============================================================

if not business_df.empty:

    received_times = pd.to_datetime(
        business_df["received_date"],
        errors="coerce",
        utc=True,
    )

    cutoff = (
        datetime.now(
            timezone.utc
        )
        - timedelta(minutes=15)
    )

    new_last_15_minutes = int(
        (
            received_times
            >= pd.Timestamp(cutoff)
        ).sum()
    )

else:

    new_last_15_minutes = 0


# ============================================================
# HEADER
# ============================================================

st.title(
    "EMAIL ASSISTANT DASHBOARD"
)

st.caption(
    "AI-powered finance email operations "
    "and response management"
)

st.success(
    "SYSTEM OPERATIONAL"
)


# ============================================================
# BUSINESS OVERVIEW
# ============================================================

st.markdown(
    "### Business Overview"
)

st.caption(
    "Live finance-related email activity from the connected mailbox"
)


k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Emails Received",
        emails_received,
    )

with k2:
    st.metric(
        "Emails Processed",
        emails_processed,
    )

with k3:
    st.metric(
        "Emails Answered",
        emails_answered,
    )

with k4:
    st.metric(
        "Exceptions",
        exceptions,
    )


k5, k6, k7, k8 = st.columns(4)

with k5:
    st.metric(
        "Response Rate",
        f"{response_rate:.1f}%",
    )

with k6:
    st.metric(
        "New in 15 Minutes",
        new_last_15_minutes,
    )

with k7:
    st.metric(
        "Average Response Time",
        f"{average_response_time:.2f}s",
    )

with k8:
    st.metric(
        "Benchmark Median",
        f"{BENCHMARK_MEDIAN_SECONDS:.1f}s",
    )


# ============================================================
# MANAGEMENT SUMMARY
# ============================================================

st.markdown(
    "### Management Summary"
)

summary1, summary2, summary3, summary4 = st.columns(4)

with summary1:

    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">
                Finance Inbox
            </div>
            <div class="summary-value">
                {emails_received} finance emails received
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with summary2:

    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">
                Customer Responses
            </div>
            <div class="summary-value">
                {emails_answered} emails answered
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with summary3:

    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">
                New Work
            </div>
            <div class="summary-value">
                {new_finance_emails} new finance emails
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with summary4:

    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">
                Processing Speed
            </div>
            <div class="summary-value">
                {BENCHMARK_MEDIAN_SECONDS:.1f}s benchmark median
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# EMAIL STATUS CHART
# ============================================================

st.markdown(
    "### Email Operations"
)

st.caption(
    "Business outcome of finance emails"
)


status_df = pd.DataFrame(
    {
        "Status": [
            "Answered",
            "New",
            "Exception",
        ],
        "Emails": [
            emails_answered,
            new_finance_emails,
            exceptions,
        ],
    }
)


status_chart = (
    alt.Chart(
        status_df
    )
    .mark_bar(
        cornerRadiusTopLeft=7,
        cornerRadiusTopRight=7,
        size=48,
    )
    .encode(
        x=alt.X(
            "Status:N",
            axis=alt.Axis(
                title=None,
                labelColor="#9AA4B6",
            ),
        ),
        y=alt.Y(
            "Emails:Q",
            axis=alt.Axis(
                title="Emails",
                titleColor="#7D899B",
                labelColor="#9AA4B6",
                gridColor="#252B36",
                domainColor="#252B36",
            ),
        ),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(
                domain=[
                    "Answered",
                    "New",
                    "Exception",
                ],
                range=[
                    "#2ED573",
                    "#5D6BFF",
                    "#FF5C70",
                ],
            ),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip(
                "Status:N",
                title="Status",
            ),
            alt.Tooltip(
                "Emails:Q",
                title="Emails",
            ),
        ],
    )
    .properties(
        height=300,
        background="#0C1016",
    )
    .configure_view(
        stroke=None
    )
)


st.altair_chart(
    status_chart,
    width="stretch",
)


# ============================================================
# REAL FINANCE EMAIL TABLE
# ============================================================

st.markdown(
    "### Recent Finance Emails"
)

st.caption(
    "Only real finance-related emails from Gmail are shown"
)


if business_df.empty:

    st.info(
        "No finance-related emails are currently in the inbox."
    )

else:

    display_df = business_df[
        [
            "sender_email",
            "subject",
            "received_date",
            "status",
            "response_time_ms",
        ]
    ].copy()

    display_df = display_df.rename(
        columns={
            "sender_email": "Customer",
            "subject": "Subject",
            "received_date": "Received",
            "status": "Status",
            "response_time_ms": "Response Time ms",
        }
    )

    display_df["Subject"] = (
        display_df["Subject"]
        .astype(str)
        .str.slice(
            0,
            90,
        )
    )

    display_df["Received"] = (
        pd.to_datetime(
            display_df["Received"],
            errors="coerce",
            utc=True,
        )
        .dt.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    st.dataframe(
        display_df.head(
            recent_limit
        ),
        width="stretch",
        hide_index=True,
    )


# ============================================================
# DAILY BUSINESS ACTIVITY
# ============================================================

st.markdown(
    "### Email Volume"
)

if not business_df.empty:

    activity_df = business_df.copy()

    activity_df["Hour"] = (
        pd.to_datetime(
            activity_df["received_date"],
            errors="coerce",
            utc=True,
        )
        .dt.floor("h")
    )

    activity_df = (
        activity_df
        .dropna(
            subset=["Hour"]
        )
        .groupby(
            "Hour"
        )
        .size()
        .reset_index(
            name="Emails"
        )
    )

    if not activity_df.empty:

        volume_chart = (
            alt.Chart(
                activity_df
            )
            .mark_line(
                point=True,
                color="#6C72FF",
            )
            .encode(
                x=alt.X(
                    "Hour:T",
                    axis=alt.Axis(
                        title=None,
                        labelColor="#9AA4B6",
                    ),
                ),
                y=alt.Y(
                    "Emails:Q",
                    axis=alt.Axis(
                        title="Emails",
                        titleColor="#7D899B",
                        labelColor="#9AA4B6",
                        gridColor="#252B36",
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "Hour:T",
                        title="Time",
                    ),
                    alt.Tooltip(
                        "Emails:Q",
                        title="Emails",
                    ),
                ],
            )
            .properties(
                height=280,
                background="#0C1016",
            )
            .configure_view(
                stroke=None
            )
        )

        st.altair_chart(
            volume_chart,
            width="stretch",
        )

    else:

        st.info(
            "No timestamped finance email activity available."
        )

else:

    st.info(
        "No finance email activity available."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        EMAIL ASSISTANT DASHBOARD
        • Business Operations View
        • Live Gmail Data
    </div>
    """,
    unsafe_allow_html=True,
)