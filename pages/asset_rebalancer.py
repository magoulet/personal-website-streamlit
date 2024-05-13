import pandas as pd
import streamlit as st
import requests
import json
import os


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
        summary_output = pd.DataFrame(response_data)[['Asset', 'Total', 'Action', 'FinalValue']]
        result_asset_table.dataframe(summary_output)
        result_asset_summary.write(f"Total value after rebalancing: ${summary_output.FinalValue.sum():,.0f}")
    else:
        st.error(f"Error: {response.text}")

st.write("# ⚖️ Asset Rebalancer")
st.write("__:one: Enter your assets and weights__")

# Initialize asset data
df = pd.DataFrame([
    {"asset": "VTI", "weight": 0.50, "current_value": 0},
    {"asset": "VEA", "weight": 0.15, "current_value": 0},
    {"asset": "VWO", "weight": 0.15, "current_value": 0 },
    {"asset": "BND", "weight": 0.20, "current_value": 0}
])

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
