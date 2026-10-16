from datetime import date, timedelta
import warnings

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

from utilities.dividend_helper import get_current_fx_rate

# psycopg2 connections are fine here; silence pandas' SQLAlchemy-only warning.
warnings.filterwarnings(
    "ignore", message="pandas only supports SQLAlchemy", category=UserWarning
)

st.set_page_config(page_title="Dividend Forecast", page_icon="🔮", layout="wide")

POSTGRES = st.secrets["postgres"]


def _connect():
    return psycopg2.connect(
        host=POSTGRES["host"],
        port=POSTGRES["port"],
        user=POSTGRES["user"],
        password=POSTGRES["password"],
        database=POSTGRES["portfolio_database"],
    )


@st.cache_data(ttl=60 * 5)
def load_forecast():
    """Latest forecast run and its monthly rows."""
    conn = _connect()
    try:
        run_df = pd.read_sql(
            "SELECT MAX(run_date) AS run_date FROM dividend_forecast", conn
        )
        run_date = run_df.iloc[0]["run_date"]
        if run_date is None or pd.isna(run_date):
            return pd.DataFrame(), None

        df = pd.read_sql(
            "SELECT * FROM dividend_forecast WHERE run_date = %s "
            "ORDER BY forecast_month, ticker",
            conn,
            params=(run_date,),
        )
        return df, run_date
    finally:
        conn.close()


@st.cache_data(ttl=60 * 5)
def load_trailing_actual():
    """Dividends actually recorded over the trailing twelve months."""
    conn = _connect()
    try:
        cutoff = date.today() - timedelta(days=365)
        df = pd.read_sql(
            "SELECT currency, SUM(dividend_amount) AS amount "
            "FROM dividend_history WHERE ex_dividend_date >= %s "
            "GROUP BY currency",
            conn,
            params=(cutoff,),
        )
        return df
    finally:
        conn.close()


def to_target(amount, currency, target, rates):
    if target is None or currency == target:
        return amount
    return amount * rates[(currency, target)]


st.title("🔮 Dividend Income Forecast")
st.caption(
    "Tier 0 — trailing-twelve-month run-rate, shares held constant, "
    "seasonally allocated across the next 12 months."
)

df, run_date = load_forecast()
if df.empty:
    st.warning(
        "No forecast found. Run `python main.py` in the dividend-tracker "
        "package to generate one."
    )
    st.stop()

df["forecast_month"] = pd.to_datetime(df["forecast_month"])
df["month"] = df["forecast_month"].dt.strftime("%Y-%m")

# --- Currency display mode -------------------------------------------------
currency_mode = st.sidebar.radio(
    "Currency Display",
    ["Show separately", "Combined in USD", "Combined in CAD"],
    index=0,
)
target = None if currency_mode == "Show separately" else currency_mode.split()[-1]

rates = {
    ("CAD", "USD"): get_current_fx_rate("CAD", "USD"),
    ("USD", "CAD"): get_current_fx_rate("USD", "CAD"),
}
df["display_amount"] = [
    to_target(a, c, target, rates)
    for a, c in zip(df["amount"], df["currency"])
]

# --- Headline metrics ------------------------------------------------------
projected_usd = df.loc[df["currency"] == "USD", "amount"].sum()
projected_cad = df.loc[df["currency"] == "CAD", "amount"].sum()
projected_combined = (
    projected_usd + projected_cad * rates[("CAD", "USD")]
    if target in (None, "USD")
    else projected_usd * rates[("USD", "CAD")] + projected_cad
)
combined_currency = target or "USD"

actual = load_trailing_actual()
actual_usd = actual.loc[actual["currency"] == "USD", "amount"].sum()
actual_cad = actual.loc[actual["currency"] == "CAD", "amount"].sum()
actual_combined = (
    actual_usd + actual_cad * rates[("CAD", "USD")]
    if combined_currency == "USD"
    else actual_usd * rates[("USD", "CAD")] + actual_cad
)
delta_pct = (
    (projected_combined - actual_combined) / actual_combined * 100
    if actual_combined
    else 0
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Projected next 12m (USD)", f"${projected_usd:,.0f}")
col2.metric("Projected next 12m (CAD)", f"${projected_cad:,.0f}")
col3.metric(
    f"Projected combined ({combined_currency})", f"${projected_combined:,.0f}",
    delta=f"{delta_pct:+.1f}%",
)
col4.metric(
    f"Trailing 12m actual ({combined_currency})",
    f"${actual_combined:,.0f}",
)

# --- Monthly income chart --------------------------------------------------
st.subheader("Forward Monthly Income")

if target is None:
    left, right = st.columns(2)
    for container, currency, symbol in (
        (left, "USD", "🇺🇲"),
        (right, "CAD", "🇨🇦"),
    ):
        subset = df[df["currency"] == currency]
        if subset.empty:
            container.info(f"No {currency} forecast.")
            continue
        monthly = (
            subset.groupby(["month", "ticker"])["amount"].sum().reset_index()
        )
        fig = px.bar(
            monthly,
            x="month",
            y="amount",
            color="ticker",
            title=f"{currency} {symbol}",
            labels={"amount": "Income ($)", "month": "", "ticker": "Ticker"},
        )
        container.plotly_chart(fig, use_container_width=True)
else:
    monthly = (
        df.groupby(["month", "ticker"])["display_amount"].sum().reset_index()
    )
    fig = px.bar(
        monthly,
        x="month",
        y="display_amount",
        color="ticker",
        title=f"Projected income ({target})",
        labels={"display_amount": "Income ($)", "month": "", "ticker": "Ticker"},
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Per-ticker detail -----------------------------------------------------
st.subheader("Projected Income by Holding")

summary = (
    df.groupby(["ticker", "currency"])
    .agg(
        shares=("shares", "first"),
        dps_forward=("dps_forward", "first"),
        annual_income=("amount", "sum"),
    )
    .reset_index()
    .sort_values("annual_income", ascending=False)
)
total_by_currency = summary.groupby("currency")["annual_income"].transform("sum")
summary["weight_pct"] = summary["annual_income"] / total_by_currency * 100

st.dataframe(
    summary.style.format(
        {
            "shares": "{:,.1f}",
            "dps_forward": "${:,.4f}",
            "annual_income": "${:,.2f}",
            "weight_pct": "{:.1f}%",
        }
    ),
    hide_index=True,
    use_container_width=True,
)

st.caption(
    f"Forecast run: {run_date} · {len(summary)} holdings · "
    f"shares held constant (Tier 0)."
)
