import hmac
import html
import os
from datetime import date

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="ITB Water Station", page_icon="💧", layout="centered")

# ---------- Config & storage ----------
STATUS_OK = "Layak Konsumsi"
STATUS_MAINT = "Dalam Pemeliharaan"

DEFAULT_STATION = {
    "id": "gku1",
    "name": "Gedung Kuliah Umum 1 (GKU 1)",
    "campus": "ITB Jatinangor",
    "status": STATUS_OK,
    "ph": "",
    "temperature": "Chilled / 18°C",
    "last_test": "",
    "last_maintenance": "",
    "last_filter_change": "",
    "next_maintenance": "",
}


def get_admin_password() -> str:
    pw = os.getenv("ADMIN_PASSWORD", "")
    if not pw:
        try:
            pw = st.secrets.get("ADMIN_PASSWORD", "")
        except Exception:
            pw = ""
    return pw


@st.cache_resource
def db():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def load_stations() -> list[dict]:
    rows = db().table("stations").select("*").order("id").execute().data
    if not rows:
        db().table("stations").insert(DEFAULT_STATION).execute()
        rows = [DEFAULT_STATION]
    return rows


def save_stations(stations: list[dict]) -> None:
    db().table("stations").upsert(stations).execute()


def add_report(station: str, kind: str, name: str, message: str) -> None:
    db().table("reports").insert(
        {"station": station, "type": kind, "name": name, "message": message}
    ).execute()


def fmt_date(s: str) -> str:
    if not s:
        return "-"
    try:
        return date.fromisoformat(s).strftime("%d %B %Y")
    except ValueError:
        return s


def parse_date(s: str):
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


# ---------- Styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Inter:wght@700;800&display=swap');
.stApp { background: #2B5A9E; }
header[data-testid="stHeader"] { background: transparent; }
.hero h1 { font-family:'Inter',sans-serif; font-weight:800; color:#fff; font-size:3.2rem;
           line-height:1.05; margin:0; text-transform:uppercase; }
.hero p { font-family:'Inter',sans-serif; font-weight:800; color:#B3ECFF; font-size:1.3rem;
          text-transform:uppercase; margin-top:.6rem; }
.card { background:#A5F3E8; border-radius:14px; padding:18px 22px; margin-bottom:16px;
        font-family:'Permanent Marker',cursive; color:#111; }
.card h3 { font-family:'Permanent Marker',cursive; margin:0 0 8px 0; font-size:1.5rem; color:#111; }
.card ul { margin:0; padding-left:1.2rem; font-size:1.1rem; line-height:1.9; }
.dot { display:inline-block; width:22px; height:22px; border-radius:50%; margin-right:10px; vertical-align:middle; }
.green { background:#00B85C; } .red { background:#B22222; }
.dim { opacity:.25; }
.status-row { font-size:1.05rem; margin:6px 0; }
.status-row.active { font-size:1.25rem; }
.stTabs [data-baseweb="tab"] { color:#fff; }
.stTabs [data-baseweb="tab-list"] button p { color:#fff; font-weight:700; }
label, .stMarkdown p { color:#fff; }
</style>
""",
    unsafe_allow_html=True,
)

DROP_SVG = """
<svg width="150" viewBox="0 0 120 150" xmlns="http://www.w3.org/2000/svg">
  <path d="M60 5 C70 40 105 70 105 100 A45 45 0 0 1 15 100 C15 70 50 40 60 5Z" fill="#53D0FF"/>
  <ellipse cx="45" cy="95" rx="9" ry="14" fill="#3B5566"/><ellipse cx="78" cy="95" rx="9" ry="14" fill="#3B5566"/>
  <path d="M42 118 Q60 140 80 118Z" fill="#3B5566"/>
</svg>
"""

# ---------- Header ----------
c1, c2 = st.columns([3, 1.4])
with c1:
    st.markdown(
        '<div class="hero"><h1>ITB<br>Water<br>Station</h1><p>Free water<br>for everyone</p></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(DROP_SVG, unsafe_allow_html=True)

stations = load_stations()
names = [s["name"] for s in stations]
chosen = st.selectbox("Pilih lokasi", names, index=0) if len(stations) > 1 else names[0]
station = next(s for s in stations if s["name"] == chosen)

tab_info, tab_report, tab_admin = st.tabs(["💧 Info", "📣 Laporan / Kritik & Saran", "🔒 Admin"])

# ---------- Public info ----------
with tab_info:
    left, right = st.columns([2.2, 1.3])
    ok = station["status"] == STATUS_OK
    with left:
        st.markdown(
            f"""<div class="card"><h3>Lokasi Water Station</h3>
            <div style="font-size:1.2rem">📍 {html.escape(station['name'])}<br>
            <span style="margin-left:1.6rem">{html.escape(station['campus'])}</span></div></div>""",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""<div class="card"><h3>Status</h3>
            <div class="status-row {'active' if ok else 'dim'}"><span class="dot green"></span>Layak Konsumsi</div>
            <div class="status-row {'dim' if ok else 'active'}"><span class="dot red"></span>Dalam Pemeliharaan</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""<div class="card"><h3>Kualitas Air</h3><ul>
        <li>pH Air Minum : {html.escape(station['ph']) or '-'}</li>
        <li>Suhu Air : {html.escape(station['temperature']) or '-'}</li>
        <li>Tanggal Pengujian Terakhir : {fmt_date(station['last_test'])}</li></ul></div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div class="card"><h3>Perawatan dan Pemeliharaan</h3><ul>
        <li>Maintenance Terakhir : {fmt_date(station['last_maintenance'])}</li>
        <li>Penggantian Filter Terakhir : {fmt_date(station['last_filter_change'])}</li>
        <li>Jadwal Maintenance Berikutnya : {fmt_date(station['next_maintenance'])}</li></ul></div>""",
        unsafe_allow_html=True,
    )

# ---------- Report form ----------
with tab_report:
    with st.form("report_form", clear_on_submit=True):
        kind = st.selectbox("Jenis", ["Laporan Kerusakan", "Kritik", "Saran"])
        name = st.text_input("Nama (opsional)")
        message = st.text_area("Pesan", height=150)
        sent = st.form_submit_button("Kirim", type="primary")
    if sent:
        if len(message.strip()) < 5:
            st.error("Pesan terlalu pendek.")
        else:
            add_report(station["name"], kind, name.strip()[:80], message.strip()[:2000])
            st.success("Terima kasih! Laporanmu sudah terkirim.")

# ---------- Admin ----------
with tab_admin:
    admin_pw = get_admin_password()
    if not admin_pw:
        st.warning("ADMIN_PASSWORD belum diset di server.")
    elif not st.session_state.get("auth"):
        pw = st.text_input("Password admin", type="password")
        if st.button("Login"):
            if hmac.compare_digest(pw, admin_pw):
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Password salah.")
    else:
        if st.button("Logout"):
            st.session_state["auth"] = False
            st.rerun()

        st.subheader(f"Edit: {station['name']}")
        with st.form("edit_form"):
            status = st.radio("Status", [STATUS_OK, STATUS_MAINT],
                              index=0 if station["status"] == STATUS_OK else 1, horizontal=True)
            ph = st.text_input("pH Air Minum", station["ph"])
            temp = st.text_input("Suhu Air", station["temperature"])
            last_test = st.date_input("Tanggal Pengujian Terakhir", parse_date(station["last_test"]))
            last_m = st.date_input("Maintenance Terakhir", parse_date(station["last_maintenance"]))
            last_f = st.date_input("Penggantian Filter Terakhir", parse_date(station["last_filter_change"]))
            next_m = st.date_input("Jadwal Maintenance Berikutnya", parse_date(station["next_maintenance"]))
            if st.form_submit_button("Simpan", type="primary"):
                station.update(
                    status=status, ph=ph.strip(), temperature=temp.strip(),
                    last_test=last_test.isoformat() if last_test else "",
                    last_maintenance=last_m.isoformat() if last_m else "",
                    last_filter_change=last_f.isoformat() if last_f else "",
                    next_maintenance=next_m.isoformat() if next_m else "",
                )
                save_stations(stations)
                st.success("Tersimpan.")
                st.rerun()

        with st.expander("Tambah water station baru"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("Nama lokasi (mis. Gedung Kuliah Umum 2)")
                campus = st.text_input("Kampus", "ITB Jatinangor")
                if st.form_submit_button("Tambah") and n.strip():
                    stations.append({**DEFAULT_STATION, "id": f"st{len(stations)+1}",
                                     "name": n.strip(), "campus": campus.strip()})
                    save_stations(stations)
                    st.rerun()

        st.subheader("Laporan masuk")
        rows = db().table("reports").select("*").order("id", desc=True).execute().data
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            st.download_button("Download CSV", df.to_csv(index=False), "reports.csv", "text/csv")
        else:
            st.info("Belum ada laporan.")
