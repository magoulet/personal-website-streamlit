import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta, date
import psycopg2


@st.cache_data(ttl=60*5)
def get_dividend_history(currency=None, start_date=None, end_date=None, ticker=None, filter_by_payment_date=True):
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            database=st.secrets["postgres"]["portfolio_database"]
        )
        
        query = "SELECT * FROM dividend_history WHERE 1=1"
        params = []
        
        if currency:
            query += " AND currency = %s"
            params.append(currency)
        if ticker:
            query += " AND ticker = %s"
            params.append(ticker)
        if start_date:
            date_field = "payment_date" if filter_by_payment_date else "ex_dividend_date"
            query += f" AND {date_field} >= %s"
            params.append(start_date)
        if end_date:
            date_field = "payment_date" if filter_by_payment_date else "ex_dividend_date"
            query += f" AND {date_field} <= %s"
            params.append(end_date)
        
        query += " ORDER BY ex_dividend_date DESC"
        
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        
        return df if not df.empty else pd.DataFrame()
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60*60)
def get_current_fx_rate(from_currency, to_currency):
    """Get current exchange rate using a free API"""
    if from_currency == to_currency:
        return 1.0
    
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates'].get(to_currency, 1.0)
    except:
        fallback_rates = {
            ('CAD', 'USD'): 0.74,
            ('USD', 'CAD'): 1.35
        }
        return fallback_rates.get((from_currency, to_currency), 1.0)


def convert_currency_amounts(df, target_currency):
    """Convert dividend amounts to target currency using current rates"""
    if df.empty:
        return df
    
    df_converted = df.copy()
    
    for currency in df['currency'].unique():
        if currency != target_currency:
            rate = get_current_fx_rate(currency, target_currency)
            mask = df_converted['currency'] == currency
            
            if 'dividend_amount' in df_converted.columns:
                df_converted.loc[mask, 'dividend_amount'] = df_converted.loc[mask, 'dividend_amount'] * rate
            
            if 'dividend_per_share' in df_converted.columns:
                df_converted.loc[mask, 'dividend_per_share'] = df_converted.loc[mask, 'dividend_per_share'] * rate
            
            if 'estimated_dividend' in df_converted.columns:
                df_converted.loc[mask, 'estimated_dividend'] = df_converted.loc[mask, 'estimated_dividend'] * rate
            
            df_converted.loc[mask, 'currency'] = target_currency
    
    return df_converted


def get_dividend_summary_stats(df):
    if df.empty:
        return {}
    
    df['ex_dividend_date'] = pd.to_datetime(df['ex_dividend_date'])
    monthly_totals = df.groupby([df['ex_dividend_date'].dt.year, df['ex_dividend_date'].dt.month])['dividend_amount'].sum()
    monthly_avg = monthly_totals.mean() if not monthly_totals.empty else 0
    
    return {
        'monthly_average': monthly_avg,
        'total_dividends': df['dividend_amount'].sum(),
        'unique_tickers': df['ticker'].nunique()
    }
