"""MQTT publish-subscribe: sensor publish ke topik, logger subscribe.

Bedanya dengan pipe/mqueue: publisher tidak mengenal penerima, dan beberapa
logger bisa menerima pesan yang sama (fan-out). QoS 1 berarti broker boleh
mengirim ulang pesan yang belum di-ack, jadi logger sebaiknya idempoten.
"""
import argparse
import json
import os
import sys
import threading
import time

import paho.mqtt.client as mqtt

import common

TOPIK = "kebun/sensor/#"
QOS = 1


def publisher(nama, n):
    klien = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    klien.connect("127.0.0.1", 1883)
    klien.loop_start()
    for seq in range(n):
        pesan = common.buat_pesan(nama, round(20 + seq * 0.5, 2), seq, time.time())
        klien.publish(f"kebun/sensor/{nama}", pesan.rstrip(b"\n"), qos=QOS)
        time.sleep(0.002)
    time.sleep(0.3)
    klien.loop_stop()
    klien.disconnect()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sensors", type=int, default=3)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--logger", type=int, default=1, help="jumlah subscriber (uji fan-out)")
    a = p.parse_args()

    os.makedirs("results", exist_ok=True)
    nama_sensor = list(common.SENSORS)[: a.sensors]
    target = a.n * len(nama_sensor)
    kunci = threading.Lock()
    selesai = threading.Event()
    diterima = [[] for _ in range(a.logger)]

    def buat_subscriber(idx):
        path = common.LOG_MQTT if idx == 0 else f"results/log-mqtt-{idx + 1}.csv"

        def saat_pesan(klien, userdata, msg):
            pesan = json.loads(msg.payload)
            with kunci:
                common.tulis_csv(path, (round(time.time(), 4), pesan["sensor"],
                                        pesan["nilai"], pesan["seq"], pesan["ts"]))
                diterima[idx].append((pesan["sensor"], pesan["seq"]))
                if all(len(d) >= target for d in diterima):
                    selesai.set()

        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        c.on_message = saat_pesan
        c.connect("127.0.0.1", 1883)
        c.subscribe(TOPIK, qos=QOS)
        c.loop_start()
        return c

    subs = [buat_subscriber(i) for i in range(a.logger)]
    time.sleep(0.5)

    thread = [threading.Thread(target=publisher, args=(nama, a.n)) for nama in nama_sensor]
    for t in thread:
        t.start()
    for t in thread:
        t.join()

    selesai.wait(timeout=5)
    for c in subs:
        c.loop_stop()
        c.disconnect()

    for i, d in enumerate(diterima):
        unik = len(set(d))
        print(f"mqtt logger-{i + 1}: diterima={len(d)} unik={unik}/{target} "
              f"duplikat={len(d) - unik}")
    if a.logger > 1:
        print("  setiap logger menerima seluruh aliran: itu fan-out, bukan pembagian kerja.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
