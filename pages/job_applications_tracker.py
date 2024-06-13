from datetime import datetime
import pandas as pd
import streamlit as st
import uuid

from utilities.mongo import get_mongo_job_applications, insert_mongo_job_applications ,update_mongo_job_applications


# Modal to create new application
@st.experimental_dialog("Add New Application")
def add_application(latest_application):
    with st.form("Add Application"):
        st.write("Note: pre-filled with most recent application")
        applicant_name = st.text_input("Applicant Name", value=latest_application.get("applicant_name", ""))
        industry = st.text_input("Industry", value=latest_application.get("industry", ""))
        company = st.text_input("Company", value=latest_application.get("company", ""))
        position = st.text_input("Position", value=latest_application.get("position", ""))
        location = st.text_input("Location", value=latest_application.get("location", ""))
        job_description_link = st.text_input("Job Description Link", value=latest_application.get("job_description_link", ""))
        resume_link = st.text_input("Resume Link", value=latest_application.get("resume_link", ""))
        cover_letter_link = st.text_input("Cover Letter Link", value=latest_application.get("cover_letter_link", ""))
        outcome = st.text_input("Outcome", value=latest_application.get("outcome", ""))
        prompt_details = st.text_input("Prompt Details", value=latest_application.get("prompt_details", ""))
        notes = st.text_input("Notes", value=latest_application.get("notes", ""))
        submitted = st.form_submit_button("Submit")

        if submitted:
            now = datetime.now()
            new_application = {
                "date_applied": now,
                "applicant_name": applicant_name,
                "industry": industry,
                "company": company,
                "position": position,
                "location": location,
                "job_description_link": job_description_link,
                "resume_link": resume_link,
                "cover_letter_link": cover_letter_link,
                "outcome": outcome,
                "prompt_details": prompt_details,
                "notes": notes,
                "application_id": str(uuid.uuid4()),  # Generate a unique ID
                "created_at": now,  # Add a timestamp
                "last_updated": now,
            }
            try:
                # Convert the new application to DataFrame
                new_application_df = pd.DataFrame([new_application])
                # Insert the new application into MongoDB
                insert_result = insert_mongo_job_applications(new_application_df)
                st.success("New application added successfully!")

            except Exception as e:
                st.error(f"An error occurred while adding the new application: {e}")

            st.rerun()

def get_latest_application(df):
    # Get the most recent application
    latest_application = df.sort_values("date_applied").iloc[-1]
    return latest_application

# Streamlit app layout
st.set_page_config(
    page_title="Job Applications Tracker",
    page_icon="🧊",
    layout="wide",
    )

# Columns to display in the editor
display_columns = [
    "date_applied",
    "applicant_name",
    "industry",
    "company",
    "position",
    "location",
    "job_description_link",
    "resume_link",
    "cover_letter_link",
    "outcome",
    "prompt_details",
    "notes",
    "last_updated",
    "application_id",
]

# Columns used to identify modified rows
core_columns = [
    "date_applied",
    "applicant_name",
    "industry",
    "company",
    "position",
    "location",
    "job_description_link",
    "resume_link",
    "cover_letter_link",
    "outcome",
    "prompt_details",
    "notes",
]

st.write("# 🧊 Job Applications Tracker")

# Retrieve applications
documents = get_mongo_job_applications()
df = pd.DataFrame(documents)
latest_application = get_latest_application(df)

# Subset DataFrame for display
df_display = df[display_columns]

# Display and edit DataFrame
edited_df = st.data_editor(
    df_display,
    hide_index=True,
    use_container_width=True,
    column_config={
        "date_applied": st.column_config.DateColumn(
            "date_applied"
        ),
        "job_description_link": st.column_config.LinkColumn(
            "job_description_link", display_text="Job Description"
        ),
        "resume_link": st.column_config.LinkColumn(
            "resume_link", display_text="Resume"
        ),
        "cover_letter_link": st.column_config.LinkColumn(
            "cover_letter_link", display_text="Cover Letter"
        ),
    },
)


# Button to save changes
if st.button("Save Changes"):
    try:
        # Update the database with the merged DataFrame
        result = update_mongo_job_applications(edited_df, df, core_columns)
        st.success("Changes saved successfully!")

    except Exception as e:
        st.error("An error occurred while saving changes.")
        st.error(str(e))

# Button to add new application
if st.button("Add Application"):
    add_application(latest_application)