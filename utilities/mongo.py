from datetime import datetime
from pymongo import MongoClient, UpdateOne
import pandas as pd
import streamlit as st
import uuid

# Initialize MongoDB connection
@st.cache_resource
def init_mongo_connection():
    client = MongoClient(
        username=st.secrets["mongo"]["username"],
        password=st.secrets["mongo"]["password"],
        host=st.secrets["mongo"]["host"]
        # port argument can be omitted if you're using the default port
    )
    return client

# Get portfolio document by date
@st.cache_data(ttl=60*5)
def get_mongo_portfolio_document_by_date(currency, date=None):
    client = init_mongo_connection()
    database_name = st.secrets["mongo"]["portfolio_database"]
    collection_name = st.secrets["mongo"]["portfolio_collection"][currency]
    db = client[database_name]
    collection = db[collection_name]

    try:
        if date:
            query_date = datetime.combine(date, datetime.min.time())
            query = {'date': query_date}
        else:
            query = {}

        # Fetch the document
        document = collection.find_one(query, sort=[('date', -1)])

        # Extract the date, if found
        if document:
            date_modified = document['date']
        else:
            date_modified = None
            error_msg = f"No document found for the date: {date}" if date else "No documents found in the collection."
            raise ValueError(error_msg)

        return document, date_modified

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

# Get job applications
@st.cache_data(ttl=0)
def get_mongo_job_applications():
    client = init_mongo_connection()
    database_name = st.secrets["mongo"]["job_applications_database"]
    collection_name = st.secrets["mongo"]["job_applications_collection"]
    db = client[database_name]
    collection = db[collection_name]

    try:
        # Fetch all documents
        documents = collection.find({})
        documents = list(documents)
        return documents
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Update job applications
def update_mongo_job_applications(df, original_df, core_columns):
    client = init_mongo_connection()
    database_name = st.secrets["mongo"]["job_applications_database"]
    collection_name = st.secrets["mongo"]["job_applications_collection"]
    db = client[database_name]
    collection = db[collection_name]

    try:
        operations = []
        for index, row in df.iterrows():
            original_row = original_df.loc[index]
            if not row[core_columns].equals(original_row[core_columns]):
                filter = {"application_id": row["application_id"]}
                new_values = row.to_dict()
                new_values["last_updated"] = datetime.now()  # Add the current timestamp for modified rows
                operations.append(UpdateOne(filter, {"$set": new_values}))

        if operations:
            result = collection.bulk_write(operations)
            return result.bulk_api_result
        else:
            return None
    except Exception as e:
        st.error(f"An error occurred while updating the database: {e}")
        return None

def insert_mongo_job_applications(new_applications):
    client = init_mongo_connection()
    database_name = st.secrets["mongo"]["job_applications_database"]
    collection_name = st.secrets["mongo"]["job_applications_collection"]
    db = client[database_name]
    collection = db[collection_name]

    try:
        # Determine if the input is a DataFrame or a list of dictionaries
        if isinstance(new_applications, pd.DataFrame):
            # Convert DataFrame to a list of dictionaries
            new_applications = new_applications.to_dict(orient="records")
        
        if isinstance(new_applications, list):
            # Ensure each entry has a unique application_id
            for app in new_applications:
                if "application_id" not in app:
                    app["application_id"] = str(uuid.uuid4())

            result = collection.insert_many(new_applications)
            return result.inserted_ids

        else:
            raise ValueError("Input must be a DataFrame or a list of dictionaries")

    except Exception as e:
        st.error(f"An error occurred while inserting into the database: {e}")
        return None
