# K-1 — Implementasi Komunikasi Antarproses (IPC)

Tugas kelompok mata kuliah Sistem Operasi (USA-WP2260110), Kelas IF-3C, tema
**IoT dan Smart Farming**. Kasus: tiga proses sensor kebun mengirim pembacaan ke
satu proses logger.

Laporan lengkap: [`results/IF-3C_K-1_250660121068_Dendy Zainal Mutaqien.pdf`](results/IF-3C_K-1_250660121068_Dendy%20Zainal%20Mutaqien.pdf)

## Isi

| Mekanisme | Berkas | Yang ditunjukkan |
|---|---|---|
| Pipe anonim | `pipe_demo.py` | byte stream tanpa batas pesan |
| POSIX message queue | `mq.py`, `mqueue_demo.py` | batas pesan + prioritas dijamin kernel |
| MQTT (publish-subscribe) | `mqtt_demo.py` | fan-out ke beberapa logger, QoS 1 |

Pendukung: `common.py` (format pesan), `bench.py` (pengukuran),
`test_basic.py` (pemeriksaan mandiri), `figures.py` (gambar laporan),
`report.py` (perakit laporan), `run_all.sh` (semua percobaan).

## Menjalankan

```bash
# venv bersama ada di folder induk (~/Documents/Tugas/SO/.venv)
../.venv/bin/python -m pip install paho-mqtt amqtt python-docx matplotlib

../.venv/bin/amqtt -c broker.yaml &   # broker MQTT lokal di port 1883
./run_all.sh                          # semua percobaan → results/
```

MQTT memakai broker `amqtt` karena `mosquitto` tidak tersedia tanpa akses sudo.
Hentikan broker setelah selesai dengan `pkill -f "amqtt -c broker.yaml"`.

## Hasil

Median 10 percobaan, 3 sensor × 20 pembacaan, satu host:

| Mekanisme | Diterima | Hilang | Latensi rata | p95 |
|---|---|---|---|---|
| pipe | 60/60 | 0 | 0.06 ms | 0.27 ms |
| message queue | 60/60 | 0 | 0.07 ms | 0.25 ms |
| MQTT (QoS 1) | 60/60 | 0 | 0.58 ms | 2.10 ms |

Tiga temuan yang masuk laporan:

1. **Pipe tidak menjaga batas pesan.** Tanpa penanda newline, rekaman menempel di
   satu `read()`. Dari 10 percobaan, 7 kehilangan data (run
   terburuk 52/60 diterima). Dengan newline, keutuhan terjaga
   tetapi penerima tetap wajib menyimpan sisa byte.
2. **Message queue menjaga batas dan prioritas.** `mq_receive` selalu
   mengembalikan tepat satu pesan; pesan prioritas 9 keluar lebih dulu meski
   dikirim terakhir; pesan >`mq_msgsize` ditolak `EMSGSIZE`, tidak dipotong.
3. **MQTT ~10x lebih lambat tetapi memberi fan-out.** Dua logger menerima aliran
   identik tanpa saling berebut — tidak bisa dilakukan satu antrean pipe/mqueue.

## Batas yang diketahui

- `msg_max` = 10 pesan dan `msgsize_max` = 8192 byte pada mesin uji; beban lebih
  besar membuat pengirim memblokir, bukan kehilangan data.
- Latensi diukur pada satu host; tidak mewakili jaringan nyata dan bervariasi
  antar-run. Yang stabil hanya urutannya: mqueue ≈ pipe << MQTT.
- Shared memory tidak diimplementasikan (lembar tugas memberi pilihan salah satu
  keluarga mekanisme).
