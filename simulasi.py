"""Simulasi sederhana ruang pengomposan untuk membandingkan pengendali fuzzy vs on/off.
Model ini disederhanakan (bukan data sensor asli): untuk tujuan demonstrasi pengendali."""
import numpy as np, pandas as pd
from fuzzy import infer, baseline

T_AMB, GAIN = 28.0, 50.0   # suhu ruangan, kenaikan suhu maksimum akibat pemanas

SKENARIO = {
    "Normal": dict(suhu=45, kelembapan=55, gas=20),
    "Suhu terlalu rendah": dict(suhu=26, kelembapan=55, gas=20),
    "Terlalu basah": dict(suhu=40, kelembapan=82, gas=35),
    "Gas naik (kurang udara)": dict(suhu=50, kelembapan=60, gas=75),
}

def step(s, power, stir):
    suhu, hum, gas = s["suhu"], s["kelembapan"], s["gas"]
    suhu += (T_AMB + GAIN * power / 100 - suhu) * 0.08          # pemanasan vs kehilangan panas
    hum = float(np.clip(hum - 0.02 * max(suhu - T_AMB, 0) / 10 * (1 + stir / 15) + 0.01, 20, 95))  # penguapan
    gen = 1.2 * (hum / 100) + 0.02 * max(suhu - 60, 0)           # gas dihasilkan pembusukan
    gas = float(np.clip(gas + gen - 0.05 * gas * (1 + stir / 10), 0, 100))  # aerasi mengurangi gas
    return dict(suhu=suhu, kelembapan=hum, gas=gas)

def jalankan(awal, mode, menit=180, seed=1):
    rng = np.random.default_rng(seed)
    s, rows = dict(awal), []
    for t in range(menit):
        noisy = {k: v + rng.normal(0, 0.3) for k, v in s.items()}   # derau sensor kecil
        a = infer(noisy)["keluaran"] if mode == "fuzzy" else baseline(noisy)
        rows.append(dict(menit=t, **s, pemanas=a["pemanas"], pengaduk=a["pengaduk"]))
        s = step(s, a["pemanas"], a["pengaduk"])
    return pd.DataFrame(rows)

def metrik(df):
    p = df["pemanas"].values
    on = p > 50
    return {
        "Pergantian ON/OFF pemanas": int((on[1:] != on[:-1]).sum()),
        "Energi (unit, Σ daya/100)": round(float(p.sum() / 100), 1),
        "Waktu di suhu 40–60 °C (%)": round(float(df["suhu"].between(40, 60).mean() * 100), 1),
        "Gas maksimum": round(float(df["gas"].max()), 1),
        "Gas akhir": round(float(df["gas"].iloc[-1]), 1),
        "Suhu maksimum (°C)": round(float(df["suhu"].max()), 1),
    }
