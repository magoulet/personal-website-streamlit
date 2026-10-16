import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utilities.dividend_helper import get_dividend_history, get_dividend_summary_stats, convert_currency_amounts

st.set_page_config(page_title="Dividends", page_icon="💰", layout="wide")

st.title("💰 Dividends")

# Sidebar filters
st.sidebar.header("Filters")
currency_filter = st.sidebar.selectbox("Currency", ["All", "USD", "CAD"])
currency = None if currency_filter == "All" else currency_filter

# Currency display mode
st.sidebar.header("Currency Display")
currency_mode = st.sidebar.radio(
    "Display Mode",
    ["Show separately", "Convert to USD", "Convert to CAD"],
    index=0
)

# Date range filter for dividends
date_range = st.date_input(
    "Date Range",
    value=(datetime.now() - timedelta(days=365), datetime.now()),
    max_value=datetime.now()
)

# Filter by payment date option
filter_by_payment = st.checkbox("Filter by payment date (instead of ex-dividend date)", value=True)

start_date = date_range[0] if len(date_range) == 2 else None
end_date = date_range[1] if len(date_range) == 2 else None

df = get_dividend_history(currency=currency, start_date=start_date, end_date=end_date, filter_by_payment_date=filter_by_payment)

if df.empty:
    st.warning("No dividend data found for the selected filters.")
else:
    df['ex_dividend_date'] = pd.to_datetime(df['ex_dividend_date'])
    
    # Apply currency conversion if needed
    if currency_mode == "Convert to USD":
        df = convert_currency_amounts(df, "USD")
    elif currency_mode == "Convert to CAD":
        df = convert_currency_amounts(df, "CAD")
    
    # Ticker filter
    tickers = ["All"] + sorted(df['ticker'].unique().tolist())
    ticker_filter = st.selectbox("Ticker", tickers)
    if ticker_filter != "All":
        df = df[df['ticker'] == ticker_filter]
    
    # Summary metrics (never mix currencies when showing separately)
    stats = get_dividend_summary_stats(df)
    by_currency = stats.get('by_currency', {})
    currencies = sorted(by_currency.keys())

    if len(currencies) == 1:
        currency_label = currencies[0]
        values = by_currency[currency_label]
        summary_cols = st.columns(3)
        summary_cols[0].metric(
            f"Total Dividends ({currency_label})",
            f"${values['total']:,.2f}",
        )
        summary_cols[1].metric(
            f"Monthly Average ({currency_label})",
            f"${values['monthly_average']:,.2f}",
        )
        summary_cols[2].metric("Unique Tickers", stats.get('unique_tickers', 0))
    else:
        st.caption("Showing currencies separately — totals are not combined.")
        summary_cols = st.columns(len(currencies) * 2 + 1)
        for index, currency_label in enumerate(currencies):
            values = by_currency[currency_label]
            summary_cols[index * 2].metric(
                f"Total Dividends ({currency_label})",
                f"${values['total']:,.2f}",
            )
            summary_cols[index * 2 + 1].metric(
                f"Monthly Average ({currency_label})",
                f"${values['monthly_average']:,.2f}",
            )
        summary_cols[-1].metric("Unique Tickers", stats.get('unique_tickers', 0))
    
    # Monthly totals chart
    st.subheader("Monthly Dividend Totals")
    monthly_data = df.groupby([df['ex_dividend_date'].dt.to_period('M'), 'currency'])['dividend_amount'].sum().reset_index()
    monthly_data['month'] = monthly_data['ex_dividend_date'].astype(str)
    
    fig_monthly = px.bar(monthly_data, x='month', y='dividend_amount', color='currency',
                         title="Monthly Dividend Income", labels={'dividend_amount': 'Dividend Amount ($)'})
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # By ticker chart
    st.subheader("Dividends by Ticker")
    ticker_data = df.groupby(['ticker', 'currency'])['dividend_amount'].sum().reset_index()
    fig_ticker = px.bar(ticker_data, x='ticker', y='dividend_amount', color='currency',
                        title="Total Dividends by Ticker", labels={'dividend_amount': 'Dividend Amount ($)'})
    st.plotly_chart(fig_ticker, use_container_width=True)
    
    # Recent payments table
    st.subheader("Dividend Payments")
    
    # Use payment_date if available, otherwise use ex_dividend_date
    date_col = 'payment_date' if 'payment_date' in df.columns else 'ex_dividend_date'
    display_cols = [date_col, 'ticker', 'currency', 'dividend_per_share', 'shares_held', 'dividend_amount']
    
    recent_df = df.nlargest(20, 'ex_dividend_date')[display_cols]
    recent_df[date_col] = pd.to_datetime(recent_df[date_col]).dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        recent_df.style.format({
            'dividend_amount': '${:,.2f}',
            'dividend_per_share': '${:.4f}',
            'shares_held': '{:,.0f}'
        }),
        hide_index=True,
        use_container_width=True
    )

