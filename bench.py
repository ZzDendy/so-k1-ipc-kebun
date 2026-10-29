"""Jalankan ketiga mekanisme, ukur latensi kirim->terima dari CSV, cetak tabel markdown.

Beberapa percobaan diulang karena latensi satu host bervariasi antar-run;
tabel memakai nilai median dari seluruh percobaan.
"""
import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys

import common

PERCOBAAN = [
    ("pipe", [sys.executable, "pipe_demo.py"]),
    ("mqueue", [sys.executable, "mqueue_demo.py"]),
    ("mqtt", ["../.venv/bin/python", "mqtt_demo.py"]),
]
LOG = {"pipe": common.LOG_PIPE, "mqueue": common.LOG_MQ, "mqtt": common.LOG_MQTT}


def baca(path, target):
    if not os.path.exists(path):
        return None
    lat, seq = [], set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lat.append(float(row["recv_ts"]) - float(row["ts"]))
            seq.add((row["sensor"], row["seq"]))
    if not lat:
        return None
    lat.sort()
    return {
        "diterima": len(lat),
        "unik": len(seq),
        "hilang": target - len(seq),
        "duplikat": len(lat) - len(seq),
        "rata": statistics.mean(lat) * 1000,
        "p95": lat[int(len(lat) * 0.95)] * 1000,
        "maks": lat[-1] * 1000,
    }


def uji_pipe(a):
    """Keutuhan rekaman pada pipe, dengan dan tanpa penanda newline."""
    target = a.n * a.sensors
    hasil = {}
    for mode, opsi in (("delimiter", []), ("tanpa", ["--tanpa-delimiter"])):
        utuh = hilang = 0
        terburuk = target
        for _ in range(a.trials):
            if os.path.exists(common.LOG_PIPE):
                os.remove(common.LOG_PIPE)
            out = subprocess.run([sys.executable, "pipe_demo.py", "--n", str(a.n),
                                  "--sensors", str(a.sensors)] + opsi,
                                 capture_output=True, text=True)
            m = re.search(r"diterima=(\d+)/(\d+)", out.stdout)
            if not m:
                continue
            diterima = int(m.group(1))
            if diterima == target:
                utuh += 1
            else:
                hilang += 1
            terburuk = min(terburuk, diterima)
        hasil[mode] = {"utuh": utuh, "hilang": hilang, "terburuk": terburuk}
    return hasil


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=5)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--sensors", type=int, default=3)
    a = p.parse_args()
    target = a.n * a.sensors

    hasil = {}
    for nama, cmd in PERCOBAAN:
        jalankan = []
        for _ in range(a.trials):
            if os.path.exists(LOG[nama]):
                os.remove(LOG[nama])
            out = subprocess.run(cmd + ["--n", str(a.n), "--sensors", str(a.sensors)],
                                 capture_output=True, text=True)
            if out.returncode != 0:
                print(f"{nama} gagal: {out.stderr[-300:]}", file=sys.stderr)
                break
            r = baca(LOG[nama], target)
            if r:
                jalankan.append(r)
        if jalankan:
            hasil[nama] = {
                k: statistics.median(x[k] for x in jalankan)
                for k in jalankan[0]
            }
            hasil[nama]["unik"] = max(x["unik"] for x in jalankan)

    pipa = uji_pipe(a)

    print(f"Median dari {a.trials} percobaan, {a.sensors} sensor x {a.n} pembacaan.\n")
    with open("results/bench.json", "w", encoding="utf-8") as f:
        json.dump({"trials": a.trials, "n": a.n, "sensors": a.sensors,
                   "hasil": hasil, "pipe": pipa}, f, indent=2)
    print("| Mekanisme | Diterima | Hilang | Duplikat | Latensi rata (ms) | p95 (ms) | Maks (ms) |")
    print("|---|---|---|---|---|---|---|")
    for nama, _ in PERCOBAAN:
        r = hasil.get(nama)
        if not r:
            print(f"| {nama} | gagal | - | - | - | - | - |")
            continue
        print(f"| {nama} | {int(r['diterima'])}/{target} | {int(r['hilang'])} | "
              f"{int(r['duplikat'])} | {r['rata']:.3f} | {r['p95']:.3f} | {r['maks']:.3f} |")


if __name__ == "__main__":
    main()
