"""Cek cepat: mqueue roundtrip dan format pesan. Jalankan: python3 test_basic.py"""
import json
import time

import common
import mq

NAMA = "/kebun-selftest"


def cek_mqueue():
    mq.hapus(NAMA)
    fd = mq.buka(NAMA, mq.O_RDONLY, maks_pesan=5, ukuran_pesan=1024, buat=True, eksklusif=True)
    w = mq.buka(NAMA, mq.O_WRONLY, ukuran_pesan=1024)

    # Prioritas tinggi harus keluar lebih dulu walaupun dikirim terakhir.
    mq.kirim(w, common.buat_pesan("tanah", 41.0, 0, time.time()), 1)
    mq.kirim(w, common.buat_pesan("tanah", 99.0, 1, time.time()), 9)

    _, p1 = mq.terima(fd, 1024)
    data, p2 = mq.terima(fd, 1024)
    assert (p1, p2) == (9, 1), f"urutan prioritas salah: {p1}, {p2}"
    assert json.loads(data)["nilai"] == 41.0

    # Pesan lebih besar dari mq_msgsize harus ditolak, bukan terpotong.
    try:
        mq.kirim(w, b"x" * 2000, 1)
    except mq.MQError as e:
        assert "Message too long" in str(e) or "EMSGSIZE" in str(e), e
    else:
        raise AssertionError("pesan kebesaran tidak ditolak")

    mq.tutup(fd)
    mq.tutup(w)
    mq.hapus(NAMA)


def cek_format():
    pesan = common.buat_pesan("suhu", 28.5, 3, 1000.0)
    assert pesan.endswith(b"\n")
    assert json.loads(pesan) == {"sensor": "suhu", "nilai": 28.5, "seq": 3, "ts": 1000.0}


if __name__ == "__main__":
    cek_format()
    cek_mqueue()
    print("ok: semua cek lulus")
