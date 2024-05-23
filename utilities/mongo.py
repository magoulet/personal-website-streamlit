from datetime import datetime
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

    try:
        if date:
            # Convert datetime.date to datetime.datetime
            query_date = datetime.combine(date, datetime.min.time())
            query = {'date': query_date}
        else:
            query = {}

        document = collection.find_one(query, sort=[('date', -1)])

        # Extract the date of the document, if a document is found
        if document:
            date_modified = document['date']
        else:
            date_modified = None
            if date:
                raise ValueError(f"No document found for the date: {date}")
            else:
                raise ValueError("No documents found in the collection.")

        return document, date_modified

    except Exception as e:
        # Handle exceptions such as connection issues, and log the error for debugging
        print(f"An error occurred: {e}")
        return None, None