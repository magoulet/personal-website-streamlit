import streamlit as st

st.set_page_config(
    page_title="My Dashboard", 
    page_icon=":tada:", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        # 'Get Help': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        # 'Report a bug': "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        # 'About': "# This is a header. This is an *extremely* cool app!"
    })
st.title("My Dashboard :tada:")
st.write("""
         Make a selection from the navigation bar on the left
         """
         )


