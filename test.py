# app.py
import io
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="Hospital Patients (OPD/IPD-lite)", page_icon="🏥", layout="wide")

# -----------------------------
# Core logic (from your script)
# -----------------------------
COLS = ["Name","Age","Height_cm","Weight_kg","Condition"]

def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Kapil",105,176,30,"Kidney fail"],
            ["Arnab",156,149,90,"High blood pressure"],
            ["Lily", 92,168,68,"Lung infection"],
        ],
        columns=COLS
    )

def _recalc(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    # Avoid division by zero; coerce to numeric
    d["Height_cm"] = pd.to_numeric(d["Height_cm"], errors="coerce")
    d["Weight_kg"] = pd.to_numeric(d["Weight_kg"], errors="coerce")
    d["BMI"] = (d["Weight_kg"] / (d["Height_cm"] / 100) ** 2).round(1)
    d["High_risk"] = np.where(
        (d["BMI"] >= 30) | (d["Condition"].fillna("").str.casefold() == "high blood pressure"),
        "Yes",
        "No",
    )
    return d

def add_patient(d: pd.DataFrame, name, age, h_cm, w_kg, cond) -> pd.DataFrame:
    d = pd.concat([d, pd.DataFrame([[name, age, h_cm, w_kg, cond]], columns=COLS)], ignore_index=True)
    if "Patient_ID" not in d.columns:
        d.insert(0, "Patient_ID", range(1, len(d) + 1))
    else:
        d["Patient_ID"] = range(1, len(d) + 1)
    return _recalc(d)

# -----------------------------
# Session init (mirrors script)
# -----------------------------
if "df" not in st.session_state:
    df = _recalc(_base_df())
    df.insert(0, "Patient_ID", range(1, len(df) + 1))
    df = add_patient(df, "Kapil", 105, 176, 30, "Kidney fail")  # sample extra row
    st.session_state.df = df

# -----------------------------
# Header
# -----------------------------
st.title("🏥 Hospital Patient Records (Demo)")
st.caption("Built with pandas + NumPy. Tracks basic patient info, BMI, and high-risk flag.")

# -----------------------------
# Sidebar: Add patient form
# -----------------------------
with st.sidebar:
    st.header("➕ Add Patient")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Name", "")
        age = st.number_input("Age", min_value=0, max_value=150, value=30, step=1)
        h_cm = st.number_input("Height (cm)", min_value=30, max_value=250, value=170, step=1)
        w_kg = st.number_input("Weight (kg)", min_value=1, max_value=400, value=70, step=1)
        cond = st.text_input("Condition", "")
        submitted = st.form_submit_button("Add")
    if submitted:
        if name.strip():
            st.session_state.df = add_patient(st.session_state.df, name.strip(), int(age), int(h_cm), int(w_kg), cond.strip())
            st.success(f"Added patient: {name}")
        else:
            st.error("Name is required.")

    st.divider()
    st.header("💾 Save / Export")
    fname_csv = st.text_input("CSV filename", "patients.csv")
    fname_xlsx = st.text_input("Excel filename", "patients.xlsx")

    if st.button("Save to CSV"):
        st.session_state.df.to_csv(fname_csv, index=False)
        st.success(f"Saved {fname_csv}")

    try:
        if st.button("Save to Excel (.xlsx)"):
            st.session_state.df.to_excel(fname_xlsx, index=False)  # needs openpyxl
            st.success(f"Saved {fname_xlsx}")
    except Exception as e:
        st.info(f"Excel save skipped: {e}")

# -----------------------------
# Search panel (replicates menu)
# -----------------------------
st.subheader("🔎 Search Patients")
mode = st.selectbox("Search by", ["Exact Name", "Partial Name", "Patient ID"])
query = st.text_input("Enter search text / ID")

def run_search(df: pd.DataFrame, mode: str, q: str) -> pd.DataFrame:
    if not q:
        return pd.DataFrame()
    if mode == "Exact Name":
        return df[df["Name"].str.casefold() == q.casefold()]
    elif mode == "Partial Name":
        # regex=False avoids special char issues
        return df[df["Name"].str.contains(q, case=False, regex=False, na=False)]
    elif mode == "Patient ID":
        return df[df["Patient_ID"] == int(q)] if q.isdigit() else pd.DataFrame()
    return pd.DataFrame()

result = run_search(st.session_state.df, mode, query)

c1, c2 = st.columns([1,1])
with c1:
    if result.empty and query:
        st.warning("No matching patient found.")
    else:
        st.write("**Search Results**")
        st.dataframe(result, use_container_width=True)

with c2:
    st.write("**Summary (Current Data)**")
    df = st.session_state.df
    high_risk_count = (df["High_risk"] == "Yes").sum()
    avg_bmi = df["BMI"].dropna().mean() if not df.empty else float("nan")
    st.metric("Total Patients", len(df))
    st.metric("High-risk Patients", int(high_risk_count))
    st.metric("Average BMI", round(avg_bmi, 1) if pd.notna(avg_bmi) else "—")

# -----------------------------
# Editable data table
# -----------------------------
st.subheader("🗂️ Patient Table (editable)")
st.caption("Tip: Edit cells directly; BMI & High-risk recompute when you click **Apply changes**.")
edited = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
    hide_index=True
)

col_apply, col_reset = st.columns([1,1])
with col_apply:
    if st.button("Apply changes & Recalculate", type="primary"):
        # keep column order, reinsert ID if user dropped it
        if "Patient_ID" not in edited.columns:
            edited.insert(0, "Patient_ID", range(1, len(edited) + 1))
        else:
            edited["Patient_ID"] = range(1, len(edited) + 1)
        st.session_state.df = _recalc(edited)
        st.success("Recalculated BMI and High-risk flags.")
with col_reset:
    if st.button("Reset to initial sample"):
        df = _recalc(_base_df())
        df.insert(0, "Patient_ID", range(1, len(df) + 1))
        df = add_patient(df, "Kapil", 105, 176, 30, "Kidney fail")
        st.session_state.df = df
        st.info("Reset complete.")

# -----------------------------
# Download buttons
# -----------------------------
st.subheader("⬇️ Download Data")
csv_buf = io.StringIO()
st.session_state.df.to_csv(csv_buf, index=False)
st.download_button("Download CSV", data=csv_buf.getvalue(), file_name="patients.csv", mime="text/csv")

xlsx_buf = io.BytesIO()
with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
    st.session_state.df.to_excel(writer, index=False, sheet_name="patients")
st.download_button("Download Excel", data=xlsx_buf.getvalue(), file_name="patients.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.caption("Demo only — extend with OPD/IPD structures, validations, and auth as needed.")
