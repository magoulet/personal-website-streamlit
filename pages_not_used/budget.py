from datetime import datetime
import io

from anytree import RenderTree, Node, PreOrderIter, PostOrderIter, findall
import plotly.graph_objects as go
from sqlalchemy import text
import streamlit as st


def get_gnucash_budget(month):
    conn = st.connection("gnucashDb", type="sql", ttl=None)
    year = datetime.now().year
    query = f"SELECT \
            budget_amounts.period_num , \
            budget_amounts.amount_num , \
            budgets.name AS budget , \
            accounts.name , accounts.description \
            FROM budget_amounts \
            LEFT JOIN budgets \
            ON budget_amounts.budget_guid = budgets.guid \
            LEFT JOIN accounts \
            ON budget_amounts.account_guid = accounts.guid \
            WHERE budget_amounts.period_num = {month} AND \
            budgets.name LIKE '{year}';"

    df = conn.query(query, ttl=60*5)

    return df

def create_structure():

    root = Node('Income', budget=0)
    housing = Node('Housing', parent=root, budget=0)
    living_expenses = Node('Living Expenses', parent=root, budget=0)
    transportation = Node('Transportation', parent=root, budget=0)
    kids = Node('Kids', parent=root, budget=0)
    other = Node('Other', parent=root, budget=0)
    root_insurance = Node('Insurance', parent=root, budget=0)
    childcare = Node('Childcare', parent=kids, budget=0)
    education = Node('Education', parent=kids, budget=0)
    kids_activities = Node('Kids Activities', parent=kids, budget=0)
    mortgage = Node('Mortgage', parent=housing, budget=0)
    home_supplies = Node('Home Supplies', parent=housing, budget=0)
    hoa = Node('HOA', parent=housing, budget=0)
    utilities = Node('Utilities', parent=housing, budget=0)
    electric_gas = Node('Electric/Gas', parent=utilities, budget=0)
    garbage = Node('Garbage collection', parent=utilities, budget=0)
    internet = Node('Internet', parent=utilities, budget=0)
    phone = Node('Phone', parent=utilities, budget=0)
    sewer = Node('Sewer', parent=utilities, budget=0)
    water = Node('Water', parent=utilities, budget=0)
    car_insurance = Node('Car Insurance', parent=transportation, budget=0)
    fuel = Node('Fuel', parent=transportation, budget=0)
    ltc_insurance = Node('LTC Insurance', parent=root_insurance, budget=0)
    food_dining = Node('Food/Dining', parent=living_expenses, budget=0)
    entertainment = Node('Entertainment', parent=living_expenses, budget=0)
    recreation = Node('Recreation', parent=living_expenses, budget=0)
    sports = Node('Sports', parent=living_expenses, budget=0)
    shopping = Node('Shopping', parent=living_expenses, budget=0)
    clothes = Node('Clothing', parent=living_expenses, budget=0)
    personal_care = Node('Personal Care', parent=living_expenses, budget=0)
    online_services = Node('Online Services', parent=living_expenses, budget=0)
    pharmacy = Node('Pharmacy', parent=living_expenses, budget=0)
    miscellaneous = Node('Miscellaneous', parent=other, budget=0)
    # salary = Node('Salary', parent=other, budget=0)
    savings = Node('Savings', parent=root, budget=0)
    brokerage = Node('Brokerage', parent=savings, budget=0)

    return root

def create_sankey_data(month=None):
    month = 11 if month is None else month
    df = get_gnucash_budget(month-1)
    df.replace('Insurance', 'Car Insurance', inplace=True)
    df.replace('Life Insurance', 'LTC Insurance', inplace=True)
    totExpenses = df[df['name'] != "Salary"]['amount_num'].sum()

    budget = dict(zip(df.name, df.amount_num))

    root = create_structure()

    for node in PreOrderIter(root, filter_=lambda n: n.is_leaf):
        try:
            node.budget = budget[node.name]
        except Exception as e:
            pass

        if node.name == "Brokerage":
            node.budget = max(0, budget['Salary'] - totExpenses)

    buffer = io.StringIO()
    buffer.write("source,target,value\n")

    for node in PostOrderIter(root, filter_=lambda n: n.is_root == False):
        node.parent.budget += node.budget
        if node.budget > 0:
            buffer.write(f"{node.parent.name},{node.name},{node.budget}\n")

    return buffer.getvalue()

def create_plot(data_str):
    # Parse the data string
    # data = [row.split(',') for row in data_str.strip().split('\n')[1:]]
    data = [line.split(',') for line in data_str.splitlines()[1:]]

    # Create nodes and links
    nodes = []
    links = []
    node_dict = {}

    for row in data:
        source_node = row[0]
        target_node = row[1]
        value = row[2]

        # Add source node to node_dict if it doesn't exist
        if source_node not in node_dict:
            node_dict[source_node] = len(nodes)
            nodes.append(dict(label=source_node, color='CornflowerBlue'))

        # Add target node to node_dict if it doesn't exist
        if target_node not in node_dict:
            node_dict[target_node] = len(nodes)
            nodes.append(dict(label=target_node, color='DarkOrange'))

        # Add link
        links.append(dict(
            source=node_dict[source_node],
            target=node_dict[target_node],
            value=value
        ))

    # Create Sankey trace
    trace = go.Sankey(
        valueformat = ",.0f",
        valuesuffix = " USD",
        node=dict(
            pad = 15,
            thickness = 15,
            line = dict(color = "black", width = 0.5),
            label=[node['label'] for node in nodes],
            color=[node['color'] for node in nodes]
        ),
        link=dict(
            source=[link['source'] for link in links],
            target=[link['target'] for link in links],
            value=[link['value'] for link in links],
        )
    )

    # Create layout
    layout = go.Layout(
        font=dict(size=11),
        height=800
    )

    # Create figure and plot
    fig = go.Figure(data=[trace], layout=layout)
    
    # Display the plot
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

st.write(f"# 💳️ Budget")
st.write(f"{datetime.now().strftime('%B %Y' )}")
data = create_sankey_data(datetime.now().month)
create_plot(data)