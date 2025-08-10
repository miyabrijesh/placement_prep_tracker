
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

DB = "placement_tracker.db"

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        role TEXT NOT NULL,
        status TEXT NOT NULL,
        applied_on TEXT,
        interview_date TEXT,
        job_link TEXT,
        notes TEXT
    )
    """)
    return conn

def fetch_df(conn):
    return pd.read_sql_query("SELECT * FROM applications ORDER BY id DESC", conn)

st.set_page_config(page_title="Placement Prep Tracker", page_icon="✅", layout="wide")
st.title("Placement Prep Tracker")

conn = get_conn()

with st.sidebar:
    st.markdown("### Quick Filters")
    statuses = ["Interested","Applied","Online Test","Interview Scheduled","Offer","Rejected","On Hold"]
    status_filter = st.multiselect("Status", statuses, default=[])
    st.markdown("---")
    st.write("Use the **Add / Edit** panels to manage entries. Export below.")

# Add new entry
with st.expander("➕ Add Application", expanded=True):
    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            company = st.text_input("Company*", placeholder="Acme Corp")
            applied_on = st.date_input("Applied On", value=date.today())
            job_link = st.text_input("Job Link", placeholder="https://...")
        with c2:
            role = st.text_input("Role*", placeholder="SWE Intern")
            interview_date = st.date_input("Interview Date", value=None)
        with c3:
            status = st.selectbox("Status*", ["Interested","Applied","Online Test","Interview Scheduled","Offer","Rejected","On Hold"], index=0)
            notes = st.text_area("Notes", placeholder="Referral, recruiter email, etc.")
        submitted = st.form_submit_button("Add")
        if submitted:
            if not company.strip() or not role.strip():
                st.error("Company and Role are required.")
            else:
                conn.execute(
                    "INSERT INTO applications (company, role, status, applied_on, interview_date, job_link, notes) VALUES (?,?,?,?,?,?,?)",
                    (company.strip(), role.strip(), status, str(applied_on), str(interview_date) if interview_date else None, job_link.strip(), notes.strip() if notes else None)
                )
                conn.commit()
                st.success("Added! Refresh the table below.")

df = fetch_df(conn)

# Filter
if status_filter:
    df_view = df[df["status"].isin(status_filter)]
else:
    df_view = df.copy()

st.subheader("Applications")
st.dataframe(df_view, use_container_width=True, hide_index=True)

# Edit / delete
with st.expander("✏️ Edit / Delete"):
    if df.empty:
        st.info("No entries yet.")
    else:
        ids = df["id"].tolist()
        selected_id = st.selectbox("Select ID to edit/delete", ids, format_func=lambda x: f"#{x} | {df[df['id']==x]['company'].values[0]} — {df[df['id']==x]['role'].values[0]}")
        row = df[df["id"]==selected_id].iloc[0]

        with st.form("edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                company = st.text_input("Company*", value=row["company"])
                applied_on = st.text_input("Applied On", value=row["applied_on"] or "")
                job_link = st.text_input("Job Link", value=row["job_link"] or "")
            with c2:
                role = st.text_input("Role*", value=row["role"])
                interview_date = st.text_input("Interview Date", value=row["interview_date"] or "")
            with c3:
                status = st.selectbox("Status*", ["Interested","Applied","Online Test","Interview Scheduled","Offer","Rejected","On Hold"],
                                      index=["Interested","Applied","Online Test","Interview Scheduled","Offer","Rejected","On Hold"].index(row["status"]))
                notes = st.text_area("Notes", value=row["notes"] or "")
            c_edit, c_del = st.columns(2)
            with c_edit:
                update = st.form_submit_button("Update")
            with c_del:
                delete = st.form_submit_button("Delete", type="secondary")
        if update:
            conn.execute("""
                UPDATE applications 
                SET company=?, role=?, status=?, applied_on=?, interview_date=?, job_link=?, notes=?
                WHERE id=?
            """, (company.strip(), role.strip(), status, applied_on or None, interview_date or None, job_link.strip() or None, notes or None, int(selected_id)))
            conn.commit()
            st.success("Updated!")
        if delete:
            conn.execute("DELETE FROM applications WHERE id=?", (int(selected_id),))
            conn.commit()
            st.warning("Deleted.")

# Export
c1, c2 = st.columns(2)
with c1:
    if st.button("⬇️ Export CSV"):
        st.download_button("Download applications.csv", df.to_csv(index=False).encode("utf-8"), file_name="applications.csv", mime="text/csv")
with c2:
    st.info("Tip: Sort and filter the table above, then export.")
