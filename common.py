"""Utilitas bersama: format pesan sensor dan penyimpanan ke CSV."""
import json
import os

SENSORS = {
    "tanah": ("kelembapan", "%"),
    "suhu": ("celsius", "C"),
    "pompa": ("debit", "L/m"),
}

QUEUE_PIPE = "/tmp/ipc-kebun-pipe"
QUEUE_MQ = "/kebun-sensor"
LOG_PIPE = "results/log-pipe.csv"
LOG_MQ = "results/log-mq.csv"
LOG_MQTT = "results/log-mqtt.csv"


def buat_pesan(sensor, nilai, seq, ts):
    """Satu pembacaan sensor sebagai bytes JSON, diakhiri newline."""
    return (json.dumps({"sensor": sensor, "nilai": nilai, "seq": seq, "ts": ts}) + "\n").encode()


def tulis_csv(path, baris, ada_header=None):
    """Tambah satu baris ke CSV. Header ditulis kalau berkas belum ada."""
    baru = ada_header if ada_header is not None else not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if baru:
            f.write("recv_ts,sensor,nilai,seq,ts\n")
        f.write(",".join(str(x) for x in baris) + "\n")
