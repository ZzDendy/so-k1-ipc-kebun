"""Pipe: beberapa proses sensor menulis ke satu pipe, logger membaca.

Pipe adalah byte stream tanpa batas pesan. Logika pemisah rekaman ada di sini
(newline), bukan di kernel. Jalankan --tanpa-delimiter untuk melihat akibatnya.
"""
import argparse
import json
import os
import sys
import time

import common

PIPE_BUF = 4096


def sensor(nama, n, fd_tulis, pakai_delimiter):
    for seq in range(n):
        pesan = common.buat_pesan(nama, round(20 + seq * 0.5, 2), seq, time.time())
        if not pakai_delimiter:
            pesan = pesan.rstrip(b"\n")
        # os.write menulis utuh selama <= PIPE_BUF; di atas itu bisa disela proses lain.
        os.write(fd_tulis, pesan)
        time.sleep(0.002)
    os.close(fd_tulis)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sensors", type=int, default=3)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--tanpa-delimiter", action="store_true")
    a = p.parse_args()

    os.makedirs("results", exist_ok=True)
    baca, tulis = os.pipe()
    nama_sensor = list(common.SENSORS)[: a.sensors]
    pakai_delimiter = not a.tanpa_delimiter

    for nama in nama_sensor:
        if os.fork() == 0:
            os.close(baca)
            sensor(nama, a.n, tulis, pakai_delimiter)
            os._exit(0)
    os.close(tulis)

    target = a.n * len(nama_sensor)
    diterima = 0
    rusak = 0
    gabung = 0
    sisa = b""
    while diterima < target:
        chunk = os.read(baca, PIPE_BUF)
        if not chunk:
            break
        if chunk.count(b"{") > 1:
            gabung += 1
        if not pakai_delimiter:
            # Tidak ada cara memulihkan batas pesan setelah rekaman menempel.
            try:
                pesan = json.loads(chunk)
            except json.JSONDecodeError:
                rusak += 1
                continue
            common.tulis_csv(common.LOG_PIPE, (round(time.time(), 4), pesan["sensor"],
                                               pesan["nilai"], pesan["seq"], pesan["ts"]))
            diterima += 1
            continue
        buf = sisa + chunk
        baris = buf.split(b"\n")
        sisa = baris.pop()
        for b in baris:
            pesan = json.loads(b)
            common.tulis_csv(common.LOG_PIPE, (round(time.time(), 4), pesan["sensor"],
                                               pesan["nilai"], pesan["seq"], pesan["ts"]))
            diterima += 1

    while True:
        try:
            os.wait()
        except ChildProcessError:
            break

    print(f"pipe: diterima={diterima}/{target} rusak={rusak} read_multipesan={gabung}")
    if gabung:
        print(f"  {gabung} read berisi lebih dari satu rekaman: pipe tidak menjaga batas pesan")


if __name__ == "__main__":
    main()
