# Dashboard Countdown Activity Mockrun 7 - Versi Fleksibel

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime
import json
from io import StringIO

# ========== KONFIGURASI GOOGLE SHEETS ==========

# Scope akses Google Sheets dan Drive
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Ambil JSON string dari Streamlit secrets
credentials = service_account.Credentials.from_service_account_file(
    ".streamlit/dashboard-mockrun-7-b8680a9a4d00.json",
    scopes=scope
)


# Koneksi ke spreadsheet
client = gspread.authorize(credentials)
sheet = client.open("Dashboard MR7-Control").worksheet("Sheet1")
data = sheet.get_all_records()

# Ubah ke DataFrame
df = pd.DataFrame(data)

# ========== KONFIGURASI HALAMAN ==========
st.set_page_config(page_title="Dashboard Countdown Activity Mockrun 7", layout="wide")
st_autorefresh(interval=60000, key="refresh")
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }

        .card {
            background-color:#f0f0f0;
            padding:16px;
            border-radius:12px;
            text-align:center;
            box-shadow:0 4px 6px rgba(0,0,0,0.2);
            margin: 6px;
        }

        .title { font-weight:bold; margin-bottom:-4px; }

        /* Freeze header (judul dan tabs) */
        header, .stTabs [data-baseweb="tab-list"] {
            position: sticky;
            top: 0;
            background: white;
            z-index: 100;
        }

        /* Tambahan opsional: bayangan agar terlihat seperti header beku */
        header {
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .stTabs [data-baseweb="tab-list"] {
            padding-top: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Dashboard Countdown Activity Mockrun 7")

now = datetime.now()

# ========== PENGOLAHAN STATUS ==========
def is_delayed(row):
    try:
        if row.get("Actual Start", "") == "":
            return False  # Belum mulai, tidak dihitung delay

        plan_start = datetime.strptime(row["Plan Start"], "%d/%m/%Y %H:%M:%S")
        plan_end = datetime.strptime(row["Plan End"], "%d/%m/%Y %H:%M:%S")
        actual_start = datetime.strptime(row["Actual Start"], "%d/%m/%Y %H:%M:%S")
        actual_end = row.get("Actual End", "")

        # Durasi seharusnya
        planned_duration = plan_end - plan_start
        expected_end = actual_start + planned_duration

        # Jika actual end belum ada, dan sudah melewati waktu yang seharusnya selesai
        return actual_end == "" and datetime.now() > expected_end

    except Exception as e:
        print("Error in is_delayed:", e)
        return False

def render_activity(row, big=False):
    try:
        plan_start = datetime.strptime(row["Plan Start"], "%d/%m/%Y %H:%M:%S")
        plan_end = datetime.strptime(row["Plan End"], "%d/%m/%Y %H:%M:%S")
        actual_start = row.get("Actual Start", "")
        activity_name = row.get("Activity", "")

        if actual_start:
            actual_start_dt = datetime.strptime(actual_start, "%d/%m/%Y %H:%M:%S")
            duration = plan_end - plan_start
            expected_end = actual_start_dt + duration

            countdown = expected_end - now

            if is_delayed(row):
                countdown_display = f"<div style='color:red; font-weight:bold; font-size:48px;'>-{str(abs(countdown)).split('.')[0]}</div>"
                status = "<div style='color:red; font-weight:bold; font-size:32px;'>[Delay]</div>"
            else:
                countdown_display = f"<div style='font-weight:bold; font-size:48px;'>{str(countdown).split('.')[0]}</div>"
                status = "<div style='font-weight:bold; font-size:32px;'>[On Track]</div>"

        else:
            countdown_display = "<div style='font-weight:bold; font-size:48px;'>Not Started</div>"
            status = "<div style='font-weight:bold; font-size:32px;'></div>"

        actual_start_str = actual_start if actual_start else "-"

        return f"""
        <div class='card'>
            <div class='title'>{row['Code']}</div>
            <div style='font-size:16px; color:#555;'>{activity_name}</div>
            {countdown_display}
            {status}
            <div style='font-size:12px; text-align:left;'>
                <b>Plan Start:</b> {row['Plan Start']}<br>
                <b>Plan End:</b> {row['Plan End']}<br>
                <b>Actual Start:</b> {actual_start_str}
            </div>
        </div>
        """
    except Exception as e:
        error_str = str(e).replace('<','&lt;').replace('>','&gt;')
        return f"<div class='card'><b>Error:</b> {error_str}</div>"


# ========== FILTERING ==========
df_main = df[df["Key"].str.lower().isin(["main", "utama"])]
df_parallel = df[df["Key"].str.lower().isin(["parallel", "paralel"])]
df_main_delay = df_main[df_main.apply(lambda x: is_delayed(x), axis=1)]
df_parallel_delay = df_parallel[df_parallel.apply(lambda x: is_delayed(x), axis=1)]
df_delay_combined = pd.concat([df_main_delay, df_parallel_delay])

# ========== LAYOUT GRIDS ==========
def render_grid(df_subset, max_cols=3):
    cols = st.columns(max_cols)
    for i, (_, row) in enumerate(df_subset.iterrows()):
        with cols[i % max_cols]:
            st.markdown(render_activity(row), unsafe_allow_html=True)

# ========== TABS ==========
tabs = st.tabs(["Main Activity", "Parallel Activity", "Delay Activity", "Table Activity"])

# ---------- Tab: Main ----------
with tabs[0]:
    count = len(df_main)
    if count == 1:
        st.markdown(render_activity(df_main.iloc[0], big=True), unsafe_allow_html=True)
    elif count == 2:
        render_grid(df_main, max_cols=2)
    elif count <= 4:
        render_grid(df_main, max_cols=2)
    else:
        render_grid(df_main, max_cols=3)

# ---------- Tab: Parallel ----------
with tabs[1]:
    render_grid(df_parallel, max_cols=3)

# ---------- Tab: Delay ----------
with tabs[2]:
    render_grid(df_delay_combined, max_cols=3)

# ---------- Tab: Table ----------
# ---------- Tab: Table ----------
with tabs[3]:
    df_display = df.drop(columns=["Actual End"]).copy()
    df_display.index = df_display.index + 1  # Mulai dari 1

    # Tambahkan scroll horizontal
    st.markdown("""
        <style>
            .scroll-table { overflow-x: auto; }
        </style>
        <div class="scroll-table">
    """, unsafe_allow_html=True)

    st.dataframe(df_display, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

