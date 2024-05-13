from datetime import timedelta, datetime
import plotly.express as px
import pandas as pd
import streamlit as st
from sqlalchemy import text
import uuid


def get_data():
    items_query = f"SELECT \
                user, \
                type, \
                description, \
                provider_name, \
                start_date, end_date, \
                cost, \
                t.date AS 'pmt_date', \
                t.completed, \
                a.transaction_id \
                FROM activities AS a \
                LEFT JOIN transactions as t \
                ON a.transaction_id = t.transaction_id;"
    
    providers_query = f"SELECT * FROM providers"
    users_query = f"SELECT * FROM users"

    conn = st.connection("budget", type="sql")

    items = conn.query(items_query, ttl=0)
    providers = conn.query(providers_query, ttl=0)
    users = conn.query(users_query, ttl=0)

    return conn, items, providers, users

def create_gantt(df):
    df['key'] = df['user'] + '_' + df['type']
    range_start = datetime.now() - timedelta(days=45)
    range_end = datetime.now() + timedelta(days=120)
    fig = px.timeline(df, 
                    x_start="start_date", 
                    x_end="end_date", 
                    y="key",
                    color="user",
                    hover_name="description",
                    hover_data=['description', 'provider_name', 'cost', 'pmt_date'],
                    text="description",
                    color_discrete_sequence=px.colors.qualitative.Dark2,
                    range_x=[range_start, range_end],
                    height=1000,
                    width=1000,
                    template='plotly'
                    )


    fig.add_vline(x=datetime.now(), line_width=1, line_color="red")
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up

    return fig, df

def calculate_monthly_budget(df, month, year):
    df['pmt_date_datetime'] = pd.to_datetime(df['pmt_date'])
    mask = (df['pmt_date_datetime'].dt.month == month) & (df['pmt_date_datetime'].dt.year == year)
    return df[mask]

@st.experimental_dialog("Add New Activity")
def add_activity():
    with st.form("Record Activity"):
        st.write("# Record Activity")
        user = st.radio("User", 
                        users['firstname'],
                        horizontal=True)
        
        type = st.text_input("Type")
        description = st.text_input("Description")
        provider = st.selectbox("Provider", providers['provider_name'])
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        cost = st.number_input("Fees ($)",min_value=0)
        payment_date = st.date_input("Payment Date")

        submitted = st.form_submit_button("Submit")

        if submitted:
            transaction_id = uuid.uuid4()
            created_at = datetime.now()

            with conn.session as s:
                s.execute(
                    text(
                        f"INSERT INTO activities \
                        (transaction_id, user, type, description, \
                        provider_name, start_date, end_date, \
                        created_at) \
                        VALUES \
                        ('{transaction_id}', '{user}', '{type}',\
                        '{description}', '{provider}',\
                        '{start_date}', '{end_date}',\
                        '{created_at}');"
                    )
                )
                # s.commit()
                s.execute(
                    text(
                        f"INSERT INTO transactions \
                        (transaction_id, cost, date) \
                        VALUES \
                        ('{transaction_id}', '{cost}', \
                        '{payment_date}');"
                    )
                )
                s.commit()

            st.rerun()


@st.experimental_dialog("Add New Provider")
def add_provider():
    with st.form("Add New Provider"):
        st.write("# Add New Provider")
        provider_name = st.text_input("Provider Name")
        provider_address = st.text_input("Provider Address")
        provider_phone = st.text_input("Provider Phone")
        provider_email = st.text_input("Provider Email")
        
        submitted = st.form_submit_button("Create New Provider")

        if submitted:
            with conn.session as s:
                s.execute(
                    text(
                        f"INSERT INTO providers \
                        (provider_name, address, phone, email) \
                        VALUES \
                        ('{provider_name}', '{provider_address}', '{provider_phone}', '{provider_email}');"
                    )
                )
                s.commit()

            st.rerun()



st.write("# ⚾️ Kids Activities")
conn, items, providers, users = get_data()

fig, gantt_df = create_gantt(items)

st.plotly_chart(fig, theme=None)

# Monthy budgets
current_month = datetime.now().month
current_year = datetime.now().year
next_month = (current_month + 1) % 12
next_year = current_year + int((current_month + 1) / 12)

budget_current_month = calculate_monthly_budget(items, current_month, current_year)
budget_next_month = calculate_monthly_budget(items, next_month, next_year)

output_columns = ['user', 'description', 'start_date', 'end_date', 'cost', 'pmt_date', 'transaction_id']

if not budget_current_month.empty:
    st.write(f"## Current month budget: ${budget_current_month.cost.sum():,.0f}")
    st.dataframe(budget_current_month[output_columns], hide_index=True)

if not budget_next_month.empty:
    st.write(f"## Next month budget: ${budget_next_month.cost.sum():,.0f}")
    st.dataframe(budget_next_month[output_columns], hide_index=True)

if st.button("Add Activity"):
    add_activity()

if st.button("Add New Provider"):
    add_provider()