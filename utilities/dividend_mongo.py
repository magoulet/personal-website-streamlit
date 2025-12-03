import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta, date
from utilities.mongo import init_mongo_connection

@st.cache_data(ttl=60*5)
def get_dividend_history(currency=None, start_date=None, end_date=None, ticker=None, filter_by_payment_date=True):
    client = init_mongo_connection()
    db = client["portfolio_tracker"]
    collection = db["dividend_history"]
    
    query = {}
    if currency:
        query["currency"] = currency
    if ticker:
        query["ticker"] = ticker
    if start_date or end_date:
        date_query = {}
        if start_date:
            # Convert date to datetime if needed
            if isinstance(start_date, date) and not isinstance(start_date, datetime):
                start_date = datetime.combine(start_date, datetime.min.time())
            date_query["$gte"] = start_date
        if end_date:
            # Convert date to datetime if needed
            if isinstance(end_date, date) and not isinstance(end_date, datetime):
                end_date = datetime.combine(end_date, datetime.max.time())
            date_query["$lte"] = end_date
        
        # Use payment_date if available and requested, otherwise ex_dividend_date
        date_field = "payment_date" if filter_by_payment_date else "ex_dividend_date"
        query[date_field] = date_query
    
    documents = list(collection.find(query).sort("ex_dividend_date", -1))
    return pd.DataFrame(documents) if documents else pd.DataFrame()



@st.cache_data(ttl=60*60)  # Cache for 1 hour
def get_current_fx_rate(from_currency, to_currency):
    """Get current exchange rate using a free API"""
    if from_currency == to_currency:
        return 1.0
    
    try:
        # Using exchangerate-api.com (free tier)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates'].get(to_currency, 1.0)
    except:
        # Fallback rates if API fails
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
            
            # Convert dividend_amount if it exists (historical dividends)
            if 'dividend_amount' in df_converted.columns:
                df_converted.loc[mask, 'dividend_amount'] = df_converted.loc[mask, 'dividend_amount'] * rate
            
            # Convert dividend_per_share if it exists (upcoming dividends)
            if 'dividend_per_share' in df_converted.columns:
                df_converted.loc[mask, 'dividend_per_share'] = df_converted.loc[mask, 'dividend_per_share'] * rate
            
            # Convert estimated_dividend if it exists (upcoming dividends)
            if 'estimated_dividend' in df_converted.columns:
                df_converted.loc[mask, 'estimated_dividend'] = df_converted.loc[mask, 'estimated_dividend'] * rate
            
            # Update currency
            df_converted.loc[mask, 'currency'] = target_currency
    
    return df_converted

def get_dividend_summary_stats(df):
    if df.empty:
        return {}
    
    monthly_totals = df.groupby([df['ex_dividend_date'].dt.year, df['ex_dividend_date'].dt.month])['dividend_amount'].sum()
    monthly_avg = monthly_totals.mean() if not monthly_totals.empty else 0
    
    return {
        'monthly_average': monthly_avg,
        'total_dividends': df['dividend_amount'].sum(),
        'unique_tickers': df['ticker'].nunique()
    }