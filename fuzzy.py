"""Mesin logika fuzzy (Mamdani) untuk pengendali ruang pengomposan.
Ditulis sendiri dengan NumPy agar tiap langkahnya bisa dijelaskan."""
import numpy as np

def trap(x, a, b, c, d):
    """Fungsi keanggotaan trapesium. Segitiga = trap dengan b == c."""
    x = np.asarray(x, dtype=float)
    up = np.where(b > a, (x - a) / (b - a + 1e-12), (x >= b).astype(float))
    down = np.where(d > c, (d - x) / (d - c + 1e-12), (x <= c).astype(float))
    return np.clip(np.minimum(up, down), 0, 1)

# ---- Himpunan fuzzy (a, b, c, d) -----------------------------------------
INPUT = {
    "suhu": {"label": "Suhu (°C)", "range": (0, 80),
             "sets": {"dingin": (0, 0, 30, 42), "optimal": (38, 50, 50, 62), "panas": (55, 65, 80, 80)}},
    "kelembapan": {"label": "Kelembapan (%)", "range": (0, 100),
                   "sets": {"kering": (0, 0, 30, 45), "normal": (40, 55, 55, 70), "tinggi": (65, 75, 100, 100)}},
    "gas": {"label": "Indeks gas (0-100)", "range": (0, 100),
            "sets": {"rendah": (0, 0, 20, 40), "sedang": (30, 50, 50, 70), "tinggi": (60, 80, 100, 100)}},
}
OUTPUT = {
    "pemanas": {"label": "Daya pemanas (%)", "range": (0, 100),
                "sets": {"mati": (0, 0, 10, 25), "lemah": (15, 35, 35, 55), "sedang": (45, 60, 60, 75), "kuat": (65, 85, 100, 100)}},
    "pengaduk": {"label": "Durasi pengaduk (menit/siklus)", "range": (0, 30),
                 "sets": {"jarang": (0, 0, 3, 8), "sedang": (5, 12, 12, 20), "sering": (15, 22, 30, 30)}},
}

# ---- Basis aturan: (kondisi input) -> {output: himpunan} -----------------
RULES = [
    ({"suhu": "dingin", "kelembapan": "normal"}, {"pemanas": "kuat", "pengaduk": "sedang"}),
    ({"suhu": "dingin", "kelembapan": "tinggi"}, {"pemanas": "kuat", "pengaduk": "sering"}),
    ({"suhu": "dingin", "kelembapan": "kering"}, {"pemanas": "sedang", "pengaduk": "jarang"}),
    ({"suhu": "optimal", "kelembapan": "normal"}, {"pemanas": "lemah", "pengaduk": "jarang"}),
    ({"suhu": "optimal", "kelembapan": "tinggi"}, {"pemanas": "lemah", "pengaduk": "sering"}),
    ({"suhu": "optimal", "kelembapan": "kering"}, {"pemanas": "lemah", "pengaduk": "sedang"}),
    ({"suhu": "panas"}, {"pemanas": "mati", "pengaduk": "sedang"}),
    ({"gas": "tinggi"}, {"pengaduk": "sering"}),
    ({"gas": "sedang"}, {"pengaduk": "sedang"}),
    ({"gas": "rendah", "suhu": "optimal"}, {"pengaduk": "jarang"}),
]

def fuzzify(values):
    """Ubah angka sensor menjadi derajat keanggotaan tiap himpunan."""
    return {v: {s: float(trap(values[v], *p)) for s, p in INPUT[v]["sets"].items()} for v in INPUT}

def infer(values):
    """Mamdani: fuzzifikasi -> evaluasi aturan (min) -> agregasi (max) -> centroid."""
    mu = fuzzify(values)
    fired = []
    agg = {o: np.zeros(501) for o in OUTPUT}
    xs = {o: np.linspace(*OUTPUT[o]["range"], 501) for o in OUTPUT}
    for i, (cond, cons) in enumerate(RULES, 1):
        w = min(mu[v][s] for v, s in cond.items())  # AND = min
        fired.append({"no": i, "kekuatan": w, "jika": cond, "maka": cons})
        if w <= 0:
            continue
        for o, s in cons.items():
            agg[o] = np.maximum(agg[o], np.minimum(w, trap(xs[o], *OUTPUT[o]["sets"][s])))  # klip & gabung
    out = {}
    for o in OUTPUT:
        area = agg[o].sum()
        mid = sum(OUTPUT[o]["range"]) / 2
        out[o] = float((xs[o] * agg[o]).sum() / area) if area > 1e-9 else mid  # centroid
    return {"keluaran": out, "aturan": fired, "mu": mu, "agregasi": agg, "xs": xs}

def baseline(values):
    """Pembanding non-AI: pemanas on/off pada batas tetap, pengaduk jadwal tetap."""
    return {"pemanas": 100.0 if values["suhu"] < 45 else 0.0, "pengaduk": 10.0}

def status(values, ph=7.0):
    """Label status kompos berdasarkan aturan sederhana."""
    s = []
    if values["gas"] >= 65: s.append("Kurang udara (indikasi anaerob), perlu aerasi")
    if values["kelembapan"] >= 70: s.append("Terlalu basah")
    if values["kelembapan"] <= 35: s.append("Terlalu kering")
    if values["suhu"] < 38: s.append("Suhu terlalu rendah, mikroba kurang aktif")
    if values["suhu"] > 62: s.append("Suhu terlalu tinggi")
    if ph < 6.5: s.append("pH asam (di bawah 6,5)")
    if ph > 7.5: s.append("pH basa (di atas 7,5)")
    return s or ["Normal, kondisi pengomposan baik"]
