from datetime import datetime
import plotly.express as px
from pymongo import MongoClient
import streamlit as st
from sqlalchemy import text


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

@st.cache_resource
def init_mongo_connection():
    client = MongoClient(
        username = st.secrets["mongo"]["username"],
        password = st.secrets["mongo"]["password"],
        host = st.secrets["mongo"]["host"],
        port = st.secrets["mongo"]["port"]
        )
    return client

@st.cache_data(ttl=60*5)
def get_document_by_date(currency, date=None):
    client = init_mongo_connection()
    database_name = st.secrets["mongo"]["database"]
    collection_name = st.secrets["mongo"]["collection"][currency]
    db = client[database_name]
    collection = db[collection_name]

    document = collection.find_one(sort=[('date', -1)])

    # Extract the date of the document, if a document is found
    if document:
        date_modified = document['date']
    else:
        date_modified = None
        
    return document, date_modified

# Call the function for CAD data
st.write(f"# 📈 Portfolio Value (CAD)")
conn = st.connection("portfolio", type="sql", ttl=None)
cad_df = conn.query("SELECT * FROM caddata", ttl=60*60)
create_plot(cad_df, "CAD 🇨🇦")
# st.write(f"Current value: CAD {cad_df.iloc[-1].value:,.0f}")

document, date = get_document_by_date('cad')

general_info_cad = f"""
    Date: {document['date'].strftime('%Y-%m-%d')}\\
    Currency: {document['currency']}\\
    Total Value: \${document['total_value']:,.0f}\\
    Total Contributions: \${document['total_contributions']:,.0f}\\
    Total Unrealized Gain: \${document['total_unrealized_gain']:,.0f}\\
    Total Realized Gain: \${document['total_realized_gain']:,.0f}\\
    MWRR: {document['mwrr']:.1%}
"""
with st.expander("Details"):
    st.write(general_info_cad)

# Call the function for USD data
st.write(f"# 📈 Portfolio Value (USD)")
usd_df = conn.query("SELECT * FROM usddata", ttl=60*60)
create_plot(usd_df, "USD 🇺🇲")
# st.write(f"Current value: USD {usd_df.iloc[-1].value:,.0f}")

document, date = get_document_by_date('usd')

general_info_usd = f"""
    Date: {document['date'].strftime('%Y-%m-%d')}\\
    Currency: {document['currency']}\\
    Total Value: \${document['total_value']:,.0f}\\
    Total Contributions: \${document['total_contributions']:,.0f}\\
    Total Unrealized Gain: \${document['total_unrealized_gain']:,.0f}\\
    Total Realized Gain: \${document['total_realized_gain']:,.0f}\\
    MWRR: {document['mwrr']:.1%}
"""

with st.expander("Details"):
    st.write(general_info_usd)
