import json
import psycopg2
from datetime import datetime
import pandas as pd
import streamlit as st
import uuid


@st.cache_data(ttl=60*5)
def get_postgres_portfolio_document_by_date(currency, date=None):
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            database=st.secrets["postgres"]["portfolio_database"]
        )
        
        if date:
            date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
            query = """
                SELECT date, currency, total_value, total_contributions, 
                       total_unrealized_gain, total_realized_gain, mwrr, portfolio_details
                FROM portfolio_snapshots 
                WHERE currency = %s AND date <= %s
                ORDER BY date DESC 
                LIMIT 1
            """
            df = pd.read_sql(query, conn, params=(currency.upper(), date_str))
        else:
            query = """
                SELECT date, currency, total_value, total_contributions,
                       total_unrealized_gain, total_realized_gain, mwrr, portfolio_details
                FROM portfolio_snapshots 
                WHERE currency = %s
                ORDER BY date DESC 
                LIMIT 1
            """
            df = pd.read_sql(query, conn, params=(currency.upper(),))

        conn.close()

        if df.empty:
            return None, None

        # Parse JSONB column - it comes back as a string
        df['portfolio_details'] = df['portfolio_details'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        
        document = df.iloc[0].to_dict()
        date_modified = document['date']
        
        return document, date_modified

    except Exception as e:
        try:
            conn.close()
        except:
            pass
        st.error(f"An error occurred: {e}")
        return None, None


@st.cache_data(ttl=0)
def get_postgres_job_applications():
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            database=st.secrets["postgres"]["job_applications_database"]
        )
        
        query = "SELECT * FROM applications ORDER BY date_applied DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict(orient='records')
    except Exception as e:
        try:
            conn.close()
        except:
            pass
        st.error(f"An error occurred: {e}")
        return None


def update_postgres_job_applications(df, original_df, core_columns):
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            database=st.secrets["postgres"]["job_applications_database"]
        )
        
        cursor = conn.cursor()
        updated_count = 0
        
        for index, row in df.iterrows():
            original_row = original_df.loc[index]
            if not row[core_columns].equals(original_row[core_columns]):
                cursor.execute("""
                    UPDATE applications 
                    SET date_applied = %s, applicant_name = %s, industry = %s, company = %s,
                        position = %s, location = %s, job_description_link = %s, resume_link = %s,
                        cover_letter_link = %s, outcome = %s, prompt_details = %s, notes = %s,
                        last_updated = %s
                    WHERE application_id = %s
                """, (
                    row['date_applied'], row['applicant_name'], row['industry'], row['company'],
                    row['position'], row['location'], row['job_description_link'], row['resume_link'],
                    row['cover_letter_link'], row['outcome'], row['prompt_details'], row['notes'],
                    datetime.now(), row['application_id']
                ))
                updated_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        return {'modified_count': updated_count}
        
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        st.error(f"An error occurred while updating the database: {e}")
        return None


def insert_postgres_job_applications(new_applications):
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            database=st.secrets["postgres"]["job_applications_database"]
        )
        
        cursor = conn.cursor()
        inserted_ids = []
        
        if isinstance(new_applications, pd.DataFrame):
            new_applications = new_applications.to_dict(orient="records")
        
        if isinstance(new_applications, list):
            for app in new_applications:
                if "application_id" not in app or not app["application_id"]:
                    app["application_id"] = str(uuid.uuid4())
                
                cursor.execute("""
                    INSERT INTO applications (application_id, date_applied, applicant_name, industry, 
                                            company, position, location, job_description_link, resume_link,
                                            cover_letter_link, outcome, prompt_details, notes, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (application_id) DO NOTHING
                """, (
                    app.get('application_id'),
                    app.get('date_applied'),
                    app.get('applicant_name'),
                    app.get('industry'),
                    app.get('company'),
                    app.get('position'),
                    app.get('location'),
                    app.get('job_description_link'),
                    app.get('resume_link'),
                    app.get('cover_letter_link'),
                    app.get('outcome'),
                    app.get('prompt_details'),
                    app.get('notes'),
                    datetime.now()
                ))
                inserted_ids.append(app['application_id'])
        
        conn.commit()
        cursor.close()
        conn.close()
        return inserted_ids
        
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        st.error(f"An error occurred while inserting into the database: {e}")
        return None
