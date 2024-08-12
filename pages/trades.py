import streamlit as st
from sqlalchemy import text


def get_data():
    conn = st.connection("portfolio", type="sql", ttl=None)
    trades = conn.query("SELECT * FROM transactions", ttl=0)
    transfers = conn.query("SELECT * FROM contributions", ttl=0)

    return conn, trades, transfers

def create_transfer_dataframe(df, currency):
    mask = (transfers["currency"] == currency)
    df = transfers[mask].sort_values(
        by=["date"],
         ascending=False,
         )
    return df

conn, trades, transfers = get_data()

# List of trades
st.write("# 🏦 All trades to date")
st.dataframe(
    trades.sort_values(
        by=["Date"],
         ascending=False,
         ),
    hide_index=True,
)
st.write(f"{len(trades)} entries")

# List of transfers
st.write("# All transfers to date")
st.write("## USD 🇺🇲")
st.dataframe(create_transfer_dataframe(transfers, "USD"))
# st.line_chart(transfers[mask], x="date", y="contribution")

st.write("## CAD 🇨🇦")
st.dataframe(create_transfer_dataframe(transfers, "CAD"))
# st.line_chart(transfers[mask], x="date", y="contribution")

record_trade_feature = st.toggle("Record new trade")

if record_trade_feature:
    with st.form("Record Trade"):
        st.write("# Record New Trade")
        date = st.date_input("Date")
        type = st.radio("Type", ["Buy", "Sell"])
        ticker = st.text_input("Ticker")
        units = st.number_input(
            "Number of Units (Negative = Sell)",
            help="Negative values will be interpreted as a sell",
            format="%0.7f"
        )
        price = st.number_input("Price", format="%0.7f")
        fees = st.number_input(
            "Fees",
            min_value=0,
            value=0,
            )
        split_ratio = st.number_input("Split Ratio", min_value=1, value=1)
        broker = st.radio("Broker", st.secrets["brokers"])
        asset_class = st.radio("Asset Class", st.secrets["asset_classes"])
        currency = st.radio("Currency", st.secrets["currencies"])
                                            

        submitted = st.form_submit_button("Submit")

        if submitted:
            with conn.session as s:
                s.execute(
                    text("INSERT INTO transactions ("
                            "Date, Type, Ticker, Units, Price, Fees, SplitRatio, Broker, AssetClass, Currency"
                            ") VALUES ("
                            ":date, :type, :ticker, :units, :price, :fees, :split_ratio, :broker, :asset_class, :currency"
                            ");"),
                    params=dict(
                        date=date,
                        type=type,
                        ticker=ticker,
                        units=units,
                        price=price,
                        fees=fees,
                        split_ratio=split_ratio,
                        broker=broker,
                        asset_class=asset_class,
                        currency=currency,
                        )
                )
                s.commit()

            st.write("Trade recorded")
