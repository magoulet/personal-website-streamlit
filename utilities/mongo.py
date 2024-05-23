from pymongo import MongoClient
import streamlit as st


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
def get_mongo_document_by_date(currency, date=None):
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