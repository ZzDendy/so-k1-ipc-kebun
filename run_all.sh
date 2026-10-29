#!/usr/bin/env bash
# Menjalankan seluruh percobaan K-1 dan menyimpan keluarannya di results/.
set -e
cd "$(dirname "$0")"
mkdir -p results
find results -name '*.csv' -delete

python3 test_basic.py

{
  echo "## pipe"
  python3 pipe_demo.py --n 20
  python3 pipe_demo.py --n 20 --tanpa-delimiter
  echo
  echo "## message queue"
  python3 mqueue_demo.py --n 20
  python3 mqueue_demo.py --n 20 --darurat-setiap 5
  echo
  echo "## mqtt (butuh broker di 127.0.0.1:1883)"
  ../.venv/bin/python mqtt_demo.py --n 20
  ../.venv/bin/python mqtt_demo.py --n 20 --logger 2
  echo
  echo "## perbandingan"
  ../.venv/bin/python bench.py
} 2>&1 | tee results/summary.txt
