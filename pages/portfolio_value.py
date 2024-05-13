from datetime import datetime
import plotly.express as px
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

# Call the function for CAD data
st.write(f"# 📈 Portfolio Value (CAD)")
conn = st.connection("portfolio", type="sql", ttl=None)
cad_df = conn.query("SELECT * FROM caddata", ttl=60*60)
create_plot(cad_df, "CAD 🇨🇦")
st.write(f"Current value: CAD {cad_df.iloc[-1].value:,.0f}")

# Call the function for USD data
st.write(f"# 📈 Portfolio Value (USD)")
usd_df = conn.query("SELECT * FROM usddata", ttl=60*60)
create_plot(usd_df, "USD 🇺🇲")
st.write(f"Current value: USD {usd_df.iloc[-1].value:,.0f}")