import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

def get_data():
  conn = st.connection("travel", type="sql")

  query = """
      SELECT
        t1.id,
        t1.`departure_date`, t1.`return_date`,
        c.`name` AS 'country', c.`alpha_3` as 'countryCode',
        t.`firstname` AS 'traveler',
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

@st.cache_data
def get_countries():
  conn = st.connection("travel", type="sql")
  df = conn.query("SELECT id, name FROM countries ORDER BY name", ttl=3600)
  return {row['name']: row['id'] for _, row in df.iterrows()}

@st.cache_data
def get_travelers():
  conn = st.connection("travel", type="sql")
  df = conn.query("SELECT id, firstname, lastname FROM travelers ORDER BY firstname", ttl=3600)
  return {f"{row.firstname} {row.lastname}": row.id for _, row in df.iterrows()}

def insert_trip(departure_date, return_date, location_id, traveler_ids, note):
  conn = st.connection("travel", type="sql")
  with conn.session as s:
    for traveler_id in traveler_ids:
      s.execute(
        text("INSERT INTO trips (departure_date, return_date, location, traveler, note) VALUES (:departure_date, :return_date, :location, :traveler, :note)"),
        params={
          'departure_date': departure_date,
          'return_date': return_date,
          'location': location_id,
          'traveler': traveler_id,
          'note': note
        }
      )
    s.commit()

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

# Add trip form
record_trip = st.toggle("Record new trip")

if record_trip:
  countries = get_countries()
  travelers = get_travelers()
  
  with st.form("Record Trip"):
    st.write("### Record New Trip")
    
    departure_date = st.date_input("Departure Date")
    return_date = st.date_input("Return Date")
    location = st.selectbox("Location", options=list(countries.keys()))
    
    selected_travelers = st.multiselect("Travelers", options=list(travelers.keys()), 
                                       default=list(travelers.keys()))
    
    note = st.text_area(label='Note')
    
    submitted = st.form_submit_button("Submit")
    
    if submitted:
      if departure_date > return_date:
        st.error("Departure date must be before return date")
      elif not selected_travelers:
        st.error("Please select at least one traveler")
      else:
        location_id = countries[location]
        traveler_ids = [travelers[name] for name in selected_travelers]
        insert_trip(departure_date, return_date, location_id, traveler_ids, note)
        st.success(f"Trip recorded for {len(selected_travelers)} traveler(s)")
        st.cache_data.clear()

df = get_data()
fig = create_plot(df)

st.plotly_chart(fig, theme="streamlit", use_container_width=True, width=900, height=500)

st.write(f"Number of countries visited: {df.countryCode.nunique()}")

st.dataframe(
    df[[
        "departure_date", 
        "return_date", 
        "country",
        "traveler",
        "duration", 
        "note"
        ]].sort_values(
        by=["departure_date"],
         ascending=False,
         ),
    hide_index=True,
)
