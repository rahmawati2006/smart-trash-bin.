import os
import numpy as np, pandas as pd, streamlit as st
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from fuzzy import INPUT, OUTPUT, RULES, trap, infer, baseline, status
from simulasi import SKENARIO, jalankan, metrik

st.set_page_config(page_title="Smart Trash Bin: Simulator AI", page_icon="♻️", layout="wide")
st.markdown("""<style>h1,h2,h3{color:#0F172A}.stTabs [data-baseweb=tab]{font-weight:600}
div[data-testid=stMetric]{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:10px}</style>""", unsafe_allow_html=True)
st.title("♻️ Smart Trash Bin: Simulator Pengendali Cerdas")
st.caption("Tugas Kecerdasan Buatan · Pengendali logika fuzzy untuk ruang pengomposan daun kering")

t1, t2, t3, t4, t5, t6 = st.tabs([
    "Beranda", 
    "Visual Simulasi Mesin", 
    "Anatomi Mesin", 
    "Simulator AI (Logika Fuzzy)", 
    "AI vs Non-AI", 
    "Dokumentasi"
])

# ---------------------------------------------------------------- Beranda
with t1:
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.subheader("Masalah dan solusi")
        st.write("Daun kering sering dibakar atau dibuang, padahal bisa jadi kompos. Mesin **Smart Trash Bin** "
                 "mencacah daun lalu mengomposkannya di ruang tertutup yang suhu, kelembapan, pH, dan gasnya dipantau.")
        st.write("Agar mesin bekerja sendiri, kami merancang **pengendali berbasis logika fuzzy**: membaca sensor lalu "
                 "memutuskan **daya pemanas** dan **lama pengadukan**, seperti manusia yang berpikir dengan kata "
                 "\"agak dingin\" atau \"cukup basah\", bukan batas kaku.")
        st.info("Web ini adalah **simulator**: menampilkan visual kerja fisik mesin sekaligus proses kalkulasi logika fuzzy di dalamnya.")
    with c2:
        st.image("assets/mesin.png", caption="Sketsa rancangan mesin (tampak depan & samping kanan)")

# ---------------------------------------------------------------- Visual Simulasi Mesin
with t2:
    st.subheader("Simulasi Praktik & Gerak Fisik Mesin")
    st.caption("Simulasi visual interaktif: lihat daun jatuh, pisau grinder berputar mencacah, kawat pemanas menyala merah membara, pengaduk bergerak bolak-balik, dan pintu solenoid terbuka otomatis.")

    # Memuat Widget Visual Interaktif HTML5/SVG
    widget_path = os.path.join(os.path.dirname(__file__), "simulator_widget.html")
    if not os.path.exists(widget_path):
        widget_path = "simulator_widget.html"

    try:
        with open(widget_path, "r", encoding="utf-8") as f:
            html_code = f.read()
        components.html(html_code, height=530)
    except Exception as e:
        st.error(f"Gagal memuat visual mesin: {e}")

    st.write("---")
    st.markdown("### 💡 Bagaimana Fisik Mesin di Atas Terhubung dengan AI?")
    c_info1, c_info2 = st.columns(2)
    with c_info1:
        st.markdown("""
        **1. Mekanisme Grinder & Keamanan:**
        - Celah masukan atas dibuat sempit (±2 cm) agar tangan pengguna tidak bisa masuk.
        - Dua pisau baja berputar berlawanan arah dengan kecepatan konstan mencacah daun menjadi serpihan kecil untuk mempercepat dekomposisi.
        - Dilengkapi tombol Stop Darurat (*E-Stop*) yang seketika memutus relai daya motor dan pemanas.
        """)
    with c_info2:
        st.markdown("""
        **2. Pengendalian Berbasis AI Fuzzy:**
        - **Kawat Pemanas (Nichrome):** Daya pemanas diatur halus (0–100%) oleh logika fuzzy berdasarkan suhu kompos saat ini (menyala merah membara saat dingin).
        - **Pengaduk Mekanis:** Mengaduk bolak-balik untuk memberi pasokan oksigen (aerasi) dan membuang gas pembusukan berlebih.
        - **Kunci Solenoid:** Pintu interlock hanya bisa dibuka jika kompos sudah matang dan suhu aman.
        """)

# ---------------------------------------------------------------- Anatomi
BAGIAN = {
 "Energi & kontrol": ("energi", "Panel surya di puncak tiang mengisi baterai di belakang. Listrik lewat tombol stop darurat ke mikrokontroler, "
    "yang mengendalikan pemanas, motor grinder, motor pengaduk, dan kunci pintu lewat relay/driver, serta membaca sensor."),
 "Input & keamanan": ("input", "Celah ±2 cm hanya meloloskan daun, bukan tangan. Corong mengarahkan daun ke tengah grinder. "
    "Tombol stop darurat memutus daya seketika."),
 "Ruang pengomposan": ("ruang", "Pemanas nichrome berinsulasi di dinding kiri-kanan menjaga suhu, pengaduk bolak-balik memberi udara (aerasi) "
    "dan mendorong kompos matang ke bawah, sensor memantau kondisi."),
 "Grinder": ("grinder", "Dua pisau berputar berlawanan arah menarik dan mencacah daun jadi serpihan kecil, sehingga luas permukaannya besar dan lebih cepat diurai mikroba."),
 "Sensor": ("sensor", "Suhu & kelembapan (DS18B20/DHT22), pH (probe analog, target 6,5–7,5), dan gas (MQ-135/MQ-4) mengirim data ke mikrokontroler."),
 "Pintu kompos & bantalan alas": ("output", "Pintu terkunci solenoid (interlock) hanya terbuka saat proses selesai dan aman. Bantalan alas menampung air lindi, cairan sisa, dan air hujan."),
}
with t3:
    pilih = st.radio("Pilih bagian mesin", list(BAGIAN), horizontal=True)
    k, teks = BAGIAN[pilih]
    a, b = st.columns([1.4, 1])
    a.image(f"assets/{k}.png")
    b.subheader(pilih); b.write(teks)

# ---------------------------------------------------------------- Simulator AI
def plot_mf(var, nilai, sets_def):
    lo, hi = sets_def["range"]; x = np.linspace(lo, hi, 400)
    fig, ax = plt.subplots(figsize=(4.2, 2.1))
    for nm, p in sets_def["sets"].items(): ax.plot(x, trap(x, *p), label=nm)
    if nilai is not None: ax.axvline(nilai, color="k", ls="--", lw=1)
    ax.set_title(sets_def["label"], fontsize=9); ax.set_ylim(0, 1.05); ax.legend(fontsize=7); ax.tick_params(labelsize=7)
    fig.tight_layout(); return fig

with t4:
    st.subheader("Simulator pengendali fuzzy (Mamdani)")
    st.caption("Geser nilai sensor, lalu lihat keputusan AI secara langsung.")
    c = st.columns(4)
    v = dict(suhu=c[0].slider("Suhu (°C)", 0, 80, 35), kelembapan=c[1].slider("Kelembapan (%)", 0, 100, 60),
             gas=c[2].slider("Indeks gas", 0, 100, 25))
    ph = c[3].slider("pH (info status)", 4.0, 10.0, 7.0, 0.1)
    hasil = infer(v); o = hasil["keluaran"]
    m = st.columns(3)
    m[0].metric("Daya pemanas", f"{o['pemanas']:.0f} %"); m[1].metric("Durasi pengaduk", f"{o['pengaduk']:.1f} menit/siklus")
    with m[2]:
        for s in status(v, ph): (st.success if s.startswith("Normal") else st.warning)(s)
    st.markdown("**Langkah 1 – Fuzzifikasi:** angka sensor diubah menjadi derajat keanggotaan (garis putus-putus = nilai saat ini).")
    g = st.columns(3)
    for col, var in zip(g, INPUT): col.pyplot(plot_mf(var, v[var], INPUT[var]))
    st.markdown("**Langkah 2 – Aturan yang menyala:**")
    df = pd.DataFrame([{"No": r["no"], "JIKA": " DAN ".join(f"{a} {b}" for a, b in r["jika"].items()),
                        "MAKA": ", ".join(f"{a} {b}" for a, b in r["maka"].items()), "Kekuatan": round(r["kekuatan"], 2)}
                       for r in hasil["aturan"] if r["kekuatan"] > 0])
    st.dataframe(df, hide_index=True) if len(df) else st.write("Tidak ada aturan yang menyala.")
    st.markdown("**Langkah 3 – Defuzzifikasi (centroid):** area gabungan aturan dijadikan satu angka keputusan.")
    g2 = st.columns(2)
    for col, var in zip(g2, OUTPUT):
        fig, ax = plt.subplots(figsize=(5, 2.1)); ax.fill_between(hasil["xs"][var], hasil["agregasi"][var], alpha=.4, color="#16A34A")
        ax.axvline(o[var], color="r", lw=2); ax.set_title(f"{OUTPUT[var]['label']} = {o[var]:.1f}", fontsize=9)
        ax.tick_params(labelsize=7); fig.tight_layout(); col.pyplot(fig)

# ---------------------------------------------------------------- Perbandingan
with t5:
    st.subheader("Fuzzy (AI) vs on/off batas tetap (non-AI)")
    st.caption("Dua pengendali dijalankan pada kondisi awal dan model ruang yang sama (180 menit). "
               "Non-AI: pemanas ON jika suhu < 45 °C, pengaduk 10 menit tetap.")
    sk = st.selectbox("Skenario awal", list(SKENARIO)); awal = SKENARIO[sk]
    df_f, df_b = jalankan(awal, "fuzzy"), jalankan(awal, "onoff")
    mf, mb = metrik(df_f), metrik(df_b)
    st.dataframe(pd.DataFrame({"Fuzzy (AI)": mf, "On/Off (non-AI)": mb}))
    for var, jd in [("suhu", "Suhu (°C)"), ("pemanas", "Daya pemanas (%)"), ("gas", "Indeks gas"), ("pengaduk", "Pengaduk (menit)")]:
        fig, ax = plt.subplots(figsize=(8, 2.2))
        ax.plot(df_f["menit"], df_f[var], label="Fuzzy", color="#16A34A"); ax.plot(df_b["menit"], df_b[var], label="On/Off", color="#DC2626", alpha=.7)
        ax.set_title(jd, fontsize=10); ax.legend(fontsize=8); ax.tick_params(labelsize=8); fig.tight_layout(); st.pyplot(fig)
    st.info("Perhatikan jumlah pergantian ON/OFF: pengendali fuzzy mengatur daya secara halus, sehingga pemanas tidak terus menyala-mati. "
            "Itu mengurangi keausan relay dan membuat suhu lebih stabil.")

# ---------------------------------------------------------------- Dokumentasi
with t6:
    st.subheader("Basis aturan fuzzy")
    st.dataframe(pd.DataFrame([{"No": i, "JIKA": " DAN ".join(f"{a} {b}" for a, b in c.items()),
                                "MAKA": ", ".join(f"{a} {b}" for a, b in k.items())} for i, (c, k) in enumerate(RULES, 1)]),
                 hide_index=True)
    st.subheader("Cara kerja singkat")
    st.markdown("""1. **Fuzzifikasi**: angka sensor → derajat keanggotaan (mis. suhu 40 °C = sebagian "dingin", sebagian "optimal").
2. **Evaluasi aturan** (Mamdani): kekuatan aturan = nilai **minimum** dari kondisinya (DAN).
3. **Agregasi**: hasil semua aturan digabung dengan **maksimum**.
4. **Defuzzifikasi**: titik berat (**centroid**) menghasilkan satu angka: daya pemanas dan durasi pengaduk.""")
    st.subheader("Keterbatasan")
    st.markdown("""- Nilai sensor berasal dari slider atau simulasi model sederhana, **bukan** data sensor fisik.
- Batas himpunan fuzzy (mis. suhu optimal sekitar 40–60 °C, pH 6,5–7,5) mengacu kisaran umum pengomposan dan perlu divalidasi dengan referensi/eksperimen.
- Model ruang (pemanasan, penguapan, produksi gas) disederhanakan untuk demonstrasi pengendali.""")
    st.subheader("Komponen mesin yang disimulasikan")
    st.dataframe(pd.DataFrame([["Panel surya, baterai, mikrokontroler", "Energi & pusat kendali (di sini diwakili kode Python)"],
        ["Sensor suhu, kelembapan, pH, gas", "Masukan pengendali (di sini: slider/simulasi)"],
        ["Pemanas nichrome", "Keluaran: daya pemanas (%)"], ["Pengaduk", "Keluaran: durasi pengaduk (menit/siklus)"]],
        columns=["Komponen", "Peran dalam simulator"]), hide_index=True)
