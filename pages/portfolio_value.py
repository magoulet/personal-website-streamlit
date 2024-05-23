from datetime import datetime
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import streamlit as st
from sqlalchemy import text

from utilities.mongo import get_mongo_document_by_date


def create_plot(df, currency):
    fig = px.line(df, 
                  x="date", 
                  y=[
                      "contributions",
                      "value", 
                      ],
                  color_discrete_map={"contributions":"DarkRed"}
                  )

    if currency == "CAD 🇨🇦":
        min_date = datetime(2019, 9, 1)
        fig.update_xaxes(range=[min_date, datetime.now()], title_text="Date")

    fig.update_yaxes(title_text="Value")
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

def process_and_display_data(currency, df_query, collection_key):
    st.write(f"# 📈 Portfolio Value ({currency})")

    conn = st.connection("portfolio", type="sql", ttl=None)
    df = conn.query(df_query, ttl=60 * 60)
    create_plot(df, currency)
    
    document, date = get_mongo_document_by_date(collection_key)
    df = pd.DataFrame(document['portfolio_details'])

    holding_details = df.style.format({
        "Qty": "{:.1f}",
        "Price": "${:,.2f}",
        "Real. Gain": "${:,.0f}",
        "Cost Basis": "${:,.0f}",
        "Value": "${:,.0f}",
        "Unreal. Gain {%}": "{:.2f}",
        "Unreal. Gain ($)": "${:,.0f}"
    })

    general_info = f"""
    Date: {document['date'].strftime('%Y-%m-%d')}\\
    Currency: {document['currency']}\\
    Total Value: \${document['total_value']:,.0f}\\
    Total Contributions: \${document['total_contributions']:,.0f}\\
    Total Unrealized Gain: \${document['total_unrealized_gain']:,.0f}\\
    Total Realized Gain: \${document['total_realized_gain']:,.0f}\\
    MWRR: {document['mwrr']:.1%}
    """

    with st.expander("Details"):
        st.write(general_info)
        st.dataframe(holding_details, hide_index=True)


# Process and display data for CAD
process_and_display_data("CAD 🇨🇦", "SELECT * FROM caddata", 'cad')

# Process and display data for USD
process_and_display_data("USD 🇺🇲", "SELECT * FROM usddata", 'usd')
