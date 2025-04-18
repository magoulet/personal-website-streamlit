from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import yaml

from utilities.mongo import get_mongo_portfolio_document_by_date


def load_portfolio_config():
    try:
        config_path = Path("config/portfolio_config.yaml")
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            return config['default_portfolio']
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
        return None


# Define function to submit rebalance form
def submit_rebalance_form():
    rebalance_api_url = st.secrets["rebalance_api_url"]
    rebalance_api_key = st.secrets["rebalance_api_key"]

    # create dictionaries for the model and values
    model_dict = edited_df.set_index('asset')['weight'].to_dict()
    values_dict = edited_df.set_index('asset')['current_value'].to_dict()

    # create the JSON payload
    payload = {
        'model': model_dict,
        'new_money': new_money,
        'values': values_dict
    }

    if not rebalance_api_url:
        st.error("API endpoint is not set")
        return

    headers = {
        "Content-Type": "application/json",
        "x-api-key": rebalance_api_key
    }

    response = requests.post(rebalance_api_url, json=payload, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        result_header.write(f"## Rebalance Results")
        summary_output = pd.DataFrame(response_data)[['Asset', 'Total', 'Action', 'FinalValue']].style.format({
            "Total": "${:,.0f}",
            "FinalValue": "${:,.0f}",
        })
        result_asset_table.dataframe(summary_output)
    else:
        st.error(f"Error: {response.text}")

def get_ticker_value(target_date):
    collection = 'usd'
    try:
        document, returned_date = get_mongo_portfolio_document_by_date(collection, target_date)
        if not document:
            raise ValueError(f"No document found for the date: {target_date}")

        df = pd.DataFrame(document['portfolio_details'])
        # Create dictionary with Ticker as key and Value as value
        ticker_value_dict = df.set_index('Ticker')['Value'].to_dict()
        return ticker_value_dict

    except ValueError as ve:
        st.error(str(ve))
        return {}
    except Exception as e:
        st.error("An unexpected error occurred.")
        st.error(str(e))
        return {}

st.write("# ⚖️ Asset Rebalancer")
st.write("__:one: Enter your assets and weights__")

target_date = st.date_input("Date", value=None, help="Enter the date to retrieve data for")
ticker_value_dict = get_ticker_value(target_date)

default_portfolio = load_portfolio_config()

if default_portfolio:
    df = pd.DataFrame([
        {
            "asset": item['asset'],
            "weight": item['weight'],
            "current_value": ticker_value_dict.get(item['asset'])
        }
        for item in default_portfolio
    ])
else:
    df = pd.DataFrame([
        {"asset": "VTI", "weight": 0.50, "current_value": ticker_value_dict.get("VTI")},
        {"asset": "VEA", "weight": 0.15, "current_value": ticker_value_dict.get("VEA")},
        {"asset": "VWO", "weight": 0.15, "current_value": ticker_value_dict.get("VWO")},
        {"asset": "BND", "weight": 0.20, "current_value": ticker_value_dict.get("BND")}
    ])

# Round the 'current_value' column to 2 decimal places
df['current_value'] = df['current_value'].round(2)

edited_df = st.data_editor(
    df,
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "asset": st.column_config.TextColumn(
            "Asset Ticker",
            help="Enter the asset ticker",
            max_chars=20,
            # validate="^st\.[a-z_]+$"
        ),
        "weight": st.column_config.NumberColumn(
            "Weight",
            help="Enter the weight of the asset. Sum of all weights must equal 1",
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            format="%.2f"
            ),
        "current_value": st.column_config.NumberColumn(
            "Current Value",
            help="Enter the current value of the asset",
            min_value=0.0,
            step=1.0,
            default=0.0,
            format="$ %.0f"
            )
    }
    )

st.write("__:two: Enter the amount of money you want to allocate to the assets__")

new_money = st.number_input(
    "New Money", 
    value=None, 
    placeholder="Type a number...",
    help="Enter the amount of money you want to allocate to the assets",
    min_value=0.0, 
    step=1.0,
    format="%.2f",
    )

# Display asset table, empty containers to be filled in
result_header = st.empty()
result_asset_table = st.empty()
result_asset_summary = st.empty()

submit_button = st.button("Submit")
if submit_button:
    submit_rebalance_form()
