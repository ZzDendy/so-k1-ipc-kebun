"""Membuat gambar untuk laporan: diagram alur dan grafik latensi."""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = "results"
FONT = "DejaVu Sans"


def kotak(ax, x, y, w, h, teks, warna, tepi, ukuran=8.5, tebal=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                facecolor=warna, edgecolor=tepi, linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, teks, ha="center", va="center", fontsize=ukuran,
            fontfamily=FONT, fontweight="bold" if tebal else "normal", linespacing=1.35)


def panah(ax, x1, y1, x2, y2, gaya="-|>", warna="#444444", putus=False, lebar=1.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=gaya, mutation_scale=11,
                                 color=warna, linewidth=lebar,
                                 linestyle="--" if putus else "-",
                                 connectionstyle="arc3,rad=0"))


def diagram():
    fig, ax = plt.subplots(figsize=(9.2, 6.1))
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0.45, 6.15)
    ax.axis("off")

    warna_s, tepi_s = "#E8EEF7", "#3B5B8C"
    warna_l, tepi_l = "#E7F3E9", "#2F6B3C"

    baris = [
        (5.45, "pipe(2)", "byte stream, tanpa batas pesan", "#FDF2E0", "#B7791F"),
        (3.60, "POSIX mqueue", "msg_max=10, msgsize=8192 B, prioritas 1-9", "#FCE9E7", "#A03B2C"),
        (1.75, "broker MQTT", "topik kebun/sensor/#, QoS 1", "#EDE7F6", "#5B3B8C"),
    ]

    # Satu kotak per jalur: tiga proses sensor identik, hanya mekanismenya yang berbeda.
    for y, judul, catatan, warna, tepi in baris:
        kotak(ax, 0.15, y - 0.22, 1.9, 0.62,
              "3 proses sensor\ntanah · suhu · pompa", warna_s, tepi_s, 9.2)
        kotak(ax, 2.55, y - 0.22, 2.25, 0.62, f"{judul}\n{catatan}", warna, tepi, 9.2)
        panah(ax, 2.05, y + 0.09, 2.55, y + 0.09, lebar=0.9)

    # logger untuk pipe
    kotak(ax, 5.6, 5.23, 3.35, 0.62, "logger\nbuffer sisa + pemisah '\\n'", warna_l, tepi_l, 9.2)
    panah(ax, 4.8, 5.54, 5.6, 5.54)

    # logger untuk mqueue
    kotak(ax, 5.6, 3.38, 3.35, 0.62, "logger\n1 mq_receive = tepat 1 pesan", warna_l, tepi_l, 9.2)
    panah(ax, 4.8, 3.69, 5.6, 3.69)

    # fan-out mqtt
    kotak(ax, 5.6, 1.98, 1.6, 0.55, "logger 1", warna_l, tepi_l, 9.2)
    kotak(ax, 7.35, 1.98, 1.6, 0.55, "logger 2", warna_l, tepi_l, 9.2)
    panah(ax, 4.8, 1.84, 5.6, 2.10)
    panah(ax, 4.8, 1.84, 7.35, 2.10)

    ax.text(0.15, 0.95, "Ketiga jalur memakai sensor dan skema pesan JSON yang sama (common.py); "
                        "yang berbeda hanya mekanisme pengirimannya.",
            fontsize=8.4, fontfamily=FONT, color="#555555", style="italic")
    ax.text(0.15, 0.65, "Pada MQTT, penerima tidak saling berebut pesan: setiap logger menerima "
                        "seluruh aliran (fan-out).",
            fontsize=8.4, fontfamily=FONT, color="#555555", style="italic")
    ax.set_title("Alur komunikasi antarproses pada kasus kebun pintar",
                 fontsize=12, fontfamily=FONT, fontweight="bold", pad=4)

    fig.tight_layout()
    fig.savefig(f"{OUT}/gambar-alur.png", dpi=220, facecolor="white")
    plt.close(fig)


def grafik():
    """Pakai median dari bench.py supaya gambar dan tabel laporan memakai angka yang sama."""
    with open(f"{OUT}/bench.json", encoding="utf-8") as f:
        data = json.load(f)["hasil"]

    nama, rata, p95 = [], [], []
    for label in ("pipe", "mqueue", "mqtt"):
        if label not in data:
            continue
        nama.append("MQTT" if label == "mqtt" else label)
        rata.append(data[label]["rata"])
        p95.append(data[label]["p95"])

    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    x = range(len(nama))
    lebar = 0.36
    b1 = ax.bar([i - lebar / 2 for i in x], rata, lebar, label="rata-rata",
                color="#3B5B8C", edgecolor="#243F63", linewidth=0.6)
    b2 = ax.bar([i + lebar / 2 for i in x], p95, lebar, label="p95",
                color="#B7791F", edgecolor="#8A5A14", linewidth=0.6)
    for b in list(b1) + list(b2):
        ax.annotate(f"{b.get_height():.2f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                    textcoords="offset points", xytext=(0, 3), ha="center",
                    fontsize=7.5, fontfamily=FONT)
    ax.set_xticks(list(x))
    ax.set_xticklabels(nama, fontfamily=FONT, fontsize=9)
    ax.set_ylabel("Latensi kirim → terima (ms)", fontfamily=FONT, fontsize=8.5)
    ax.set_ylim(0, max(p95) * 1.35)
    ax.tick_params(labelsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Latensi per mekanisme (median 5 percobaan)", fontsize=9.5,
                 fontfamily=FONT, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT}/gambar-latensi.png", dpi=220, facecolor="white")
    plt.close(fig)
    return list(zip(nama, rata, p95))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    diagram()
    hasil = grafik()
    print("gambar dibuat:", [f for f in sorted(os.listdir(OUT)) if f.endswith(".png")])
    for n, r, p in hasil:
        print(f"  {n}: rata={r:.3f} ms p95={p:.3f} ms")
