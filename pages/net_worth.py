import plotly.express as px
import streamlit as st
from sqlalchemy import text


def get_data():
    conn = st.connection("portfolio", type="sql", ttl=None)
    df = conn.query("SELECT * FROM networth", ttl=0)
    return conn, df

def create_plot(df):
    fig = px.line(
        df,
        x="date", 
        y="netWorthUsd", 
        labels={"date": "Date", "netWorthUsd": "Net Worth (USD)"},
        )
    return fig

st.write("# 💰️ Net Worth")
conn, df = get_data()
fig = create_plot(df)

st.plotly_chart(fig, theme="streamlit", use_container_width=True)

record_trade_feature = st.toggle("Add Record")

if record_trade_feature:
    with st.form("Record Net Worth"):
        st.write("# Record Net Worth")
        date = st.date_input("Date")
        net_worth = st.number_input("Net Worth (USD)")

        submitted = st.form_submit_button("Submit")

        if submitted:
            with conn.session as s:
                s.execute(
                    text("INSERT INTO networth ("
                            "Date, netWorthUsd"
                            ") VALUES ("
                            ":date, :net_worth"
                            ");"),
                    params=dict(
                        date=date,
                        net_worth=net_worth,
                        )
                )
                s.commit()

            st.write("Net Worth recorded")
