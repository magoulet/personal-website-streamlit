import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

def get_data():
    conn = st.connection("temperatures", type="sql", ttl=None)
    df = conn.query("SELECT * FROM temperaturedata WHERE dateandtime >= DATE_SUB(CURDATE(), INTERVAL 2 DAY)", ttl=60*5)
    return df

def create_plot(df):
    # Create the primary trace for temperature
    trace1 = go.Scatter(x=df['dateandtime'], y=df['temperature'], mode='lines', name='Temperature')

    # Create the secondary trace for humidity
    trace2 = go.Scatter(x=df['dateandtime'], y=df['humidity'], mode='lines', name='Humidity', yaxis='y2', line_color="DarkRed")

    # Create the layout with two y-axes
    layout = go.Layout(
        title='Temperature and Humidity',
        xaxis=dict(title='Date and Time'),
        yaxis=dict(title='Temperature'),
        yaxis2=dict(title='Humidity', overlaying='y', side='right')
    )

    # Create the figure with both traces and the layout
    fig = go.Figure(data=[trace1, trace2], layout=layout)

    return fig

st.write(f"# 🌡️ Temperature & Humidity data (Deg C)")

df = get_data()
fig = create_plot(df)

if not df.empty:
    st.write(f"## Current temperature: {df.iloc[-1].temperature:.1f}")

st.plotly_chart(fig, theme="streamlit", use_container_width=True)
