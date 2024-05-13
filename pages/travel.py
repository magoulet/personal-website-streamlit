import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def get_data():
  conn = st.connection("travel", type="sql")

  query = """
      SELECT
        t1.id,
        t1.`departure_date`, t1.`return_date`,
        c.`name` AS 'country', c.`alpha_3` as 'countryCode',
        -- t.`firstname` AS 'traveler',
        DATEDIFF(t1.`return_date`, t1.`departure_date`) as 'duration',
        t1.note
      FROM
        trips AS t1
      INNER JOIN countries AS c ON t1.`location` = c.`id`
      INNER JOIN travelers AS t ON t1.`traveler` = t.`id`
      ORDER BY t1.`departure_date` DESC;
      """

  df = conn.query(query, ttl=60*60)
  df['visited'] = 'Yes'
  return df

def create_plot(df):
  fig = px.choropleth(df, 
                      locations="countryCode",
                      hover_name="country",
                      # projection="mercator",
                      color="visited",
                      color_discrete_map={"Yes": "#00b3c6"},
                      # title="Countries Visited",
                      )
  return fig

st.write(f"# ✈️ Countries Visited")

df = get_data()
fig = create_plot(df)

st.plotly_chart(fig, theme="streamlit", use_container_width=True, width=900, height=500)

st.write(f"Number of countries visited: {df.countryCode.nunique()}")

st.dataframe(
    df[[
        "departure_date", 
        "return_date", 
        "country", 
        "duration", 
        "note"
        ]].sort_values(
        by=["departure_date"],
         ascending=False,
         ),
    hide_index=True,
)
