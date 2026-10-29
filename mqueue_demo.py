"""Message queue: sensor mengirim rekaman utuh dengan prioritas ke satu logger.

Kernel menjaga batas pesan, jadi logger tidak perlu memotong byte sendiri.
Prioritas tinggi (angka besar) dipakai untuk kondisi darurat, mis. kebocoran.
"""
import argparse
import json
import os
import time

import common
import mq

PRIO_NORMAL = 1
PRIO_DARURAT = 9
MAX_MSG = 10  # /proc/sys/fs/mqueue/msg_max di mesin uji


def sensor(nama, n, darurat_setiap):
    fd = mq.buka(common.QUEUE_MQ, mq.O_WRONLY, ukuran_pesan=1024)
    for seq in range(n):
        darurat = darurat_setiap and seq % darurat_setiap == 0
        pesan = common.buat_pesan(nama, round(90 + seq * 0.3, 2), seq, time.time())
        mq.kirim(fd, pesan, PRIO_DARURAT if darurat else PRIO_NORMAL)
        time.sleep(0.002)
    mq.tutup(fd)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sensors", type=int, default=3)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--darurat-setiap", type=int, default=0,
                   help="tiap N pesan dikirim dengan prioritas darurat")
    a = p.parse_args()

    os.makedirs("results", exist_ok=True)
    mq.hapus(common.QUEUE_MQ)
    fd = mq.buka(common.QUEUE_MQ, mq.O_RDONLY, maks_pesan=MAX_MSG, ukuran_pesan=1024,
                 buat=True, eksklusif=True)

    nama_sensor = list(common.SENSORS)[: a.sensors]
    for nama in nama_sensor:
        if os.fork() == 0:
            sensor(nama, a.n, a.darurat_setiap)
            os._exit(0)

    target = a.n * len(nama_sensor)
    prioritas = []
    while len(prioritas) < target:
        data, prio = mq.terima(fd, 1024)
        pesan = json.loads(data)
        common.tulis_csv(common.LOG_MQ, (round(time.time(), 4), pesan["sensor"],
                                         pesan["nilai"], pesan["seq"], pesan["ts"]))
        prioritas.append(prio)

    mq.tutup(fd)
    mq.hapus(common.QUEUE_MQ)
    while True:
        try:
            os.wait()
        except ChildProcessError:
            break

    print(f"mqueue: diterima={len(prioritas)}/{target} tanpa pemotongan byte")
    print(f"prioritas 20 pertama: {prioritas[:20]}")


if __name__ == "__main__":
    main()
