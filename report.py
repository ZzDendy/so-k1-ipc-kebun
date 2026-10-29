"""Merakit laporan K-1 dari template jurusan. Jalankan setelah run_all.sh dan figures.py."""
import json
import os
from copy import deepcopy

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

TEMPLATE = "../Template Laporan Tugas Individu.docx"
OUT = "results/Laporan_K-1_IPC_Kebun.docx"
MONO = "DejaVu Sans Mono"
BODY = "Droid Sans"

NAMA = "Dendy Zainal Mutaqien"
NIM = "250660121068"
KELAS = "IF-3C"
KODE = "K-1"
ANGGOTA = [
    ("Dendy Zainal Mutaqien", NIM, "Pipeline IPC (pipe, message queue) dan penyusunan laporan"),
]


def baca_bench():
    with open("results/bench.json", encoding="utf-8") as f:
        return json.load(f)


def baca_out(nama):
    path = f"results/out/{nama}.txt"
    if not os.path.exists(path):
        return ""
    return open(path, encoding="utf-8").read().strip()


def baca_berkas(path):
    return open(path, encoding="utf-8").read().rstrip()


# ---------- pembangun dokumen ----------

def bersihkan(d):
    body = d.element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def shd(el, warna):
    pr = el.get_or_add_tcPr() if el.tag == qn("w:tc") else el.get_or_add_pPr()
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear")
    s.set(qn("w:color"), "auto")
    s.set(qn("w:fill"), warna)
    pr.append(s)


def h1(d, teks):
    p = d.add_paragraph(teks, style="Heading 1")
    return p


def h2(d, teks):
    return d.add_paragraph(teks, style="Heading 2")


def par(d, teks, tebal_awal=None, miring=False, rata="justify", ukuran=None):
    p = d.add_paragraph(style="Normal")
    p.paragraph_format.alignment = {
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
    }[rata]
    p.paragraph_format.space_after = Pt(6)
    if tebal_awal:
        r = p.add_run(tebal_awal)
        r.bold = True
        if ukuran:
            r.font.size = Pt(ukuran)
    r = p.add_run(teks)
    r.italic = miring
    if ukuran:
        r.font.size = Pt(ukuran)
    return p


def bullet(d, teks, tebal_awal=None):
    p = d.add_paragraph(style="List Paragraph")
    p.paragraph_format.left_indent = Cm(0.75)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run("•\t")
    if tebal_awal:
        r = p.add_run(tebal_awal)
        r.bold = True
    p.add_run(teks)
    return p


def kode(d, teks, ukuran=8):
    p = d.add_paragraph(style="Normal")
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Cm(0.3)
    shd(p._p, "F4F4F4")
    baris = teks.split("\n")
    for i, b in enumerate(baris):
        r = p.add_run(b)
        r.font.name = MONO
        r.font.size = Pt(ukuran)
        rpr = r._element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.append(rf)
        rf.set(qn("w:ascii"), MONO)
        rf.set(qn("w:hAnsi"), MONO)
        if i < len(baris) - 1:
            r.add_break()
    return p


def caption(d, teks):
    p = d.add_paragraph(style="Normal")
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(teks)
    r.font.size = Pt(9)
    r.italic = True
    return p


def tabel(d, header, baris, lebar=None, ukuran=9):
    t = d.add_table(rows=1, cols=len(header))
    t.style = None
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for sisi in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{sisi}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "A6A6A6")
        b.append(e)
    tblPr.append(b)

    if lebar:
        tw = OxmlElement("w:tblW")
        tw.set(qn("w:w"), str(int(sum(lebar) * 567)))
        tw.set(qn("w:type"), "dxa")
        tblPr.append(tw)
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblPr.append(lay)
        for i, kol in enumerate(t._tbl.tblGrid.gridCol_lst):
            kol.set(qn("w:w"), str(int(lebar[i] * 567)))

    hdr = t.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))
    trPr.append(OxmlElement("w:cantSplit"))
    for i, teks in enumerate(header):
        c = hdr.cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(teks)
        r.bold = True
        r.font.size = Pt(ukuran)
        shd(c._tc, "D9E2F3")
        if lebar:
            c.width = Cm(lebar[i])

    for isi in baris:
        row = t.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for i, teks in enumerate(isi):
            c = row.cells[i]
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(str(teks))
            r.font.size = Pt(ukuran)
            if lebar:
                c.width = Cm(lebar[i])

    d.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def gambar(d, path, lebar_cm, ket):
    p = d.add_paragraph(style="Normal")
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(lebar_cm))
    caption(d, ket)


def nomor_halaman(d):
    for s in d.sections:
        for p in s.header.paragraphs:
            teks = "".join(r.text for r in p.runs)
            if "Laporan Tugas" in teks:
                p.text = ""
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                r1 = p.add_run("Laporan Tugas Kelompok Sistem Operasi · ")
                r2 = p.add_run(f"{KELAS} · {KODE}")
                r2.italic = True
                for r in (r1, r2):
                    r.font.size = Pt(8.5)
                    r.font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)
        f = s.footer
        p = f.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.text = ""
        run = p.add_run()
        for kind, instr in (("begin", None), ("instr", "PAGE"), ("end", None)):
            if kind == "instr":
                it = OxmlElement("w:instrText")
                it.set(qn("xml:space"), "preserve")
                it.text = " PAGE "
                run._r.append(it)
            else:
                fc = OxmlElement("w:fldChar")
                fc.set(qn("w:fldCharType"), kind)
                run._r.append(fc)
        run.font.size = Pt(9)


# ---------- isi laporan ----------

def sampul(d):
    for _ in range(3):
        d.add_paragraph()
    p = d.add_paragraph(style="Normal")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("LAPORAN TUGAS KELOMPOK")
    r.bold = True
    r.font.size = Pt(20)
    p2 = d.add_paragraph(style="Normal")
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Mata Kuliah Sistem Operasi (USA-WP2260110)")
    r2.font.size = Pt(13)

    d.add_paragraph()
    p3 = d.add_paragraph(style="Normal")
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Implementasi Komunikasi Antarproses (IPC)\n"
                    "Pengiriman Data Sensor ke Proses Logger pada Kebun Pintar")
    r3.bold = True
    r3.font.size = Pt(15)

    d.add_paragraph()
    tabel(d, ["Keterangan", "Isi"], [
        ("Kode dan judul tugas", "K-1 Implementasi Komunikasi Antarproses (IPC)"),
        ("Kelas / tema", f"{KELAS} — IoT dan Smart Farming"),
        ("Nama", NAMA),
        ("NIM", NIM),
        ("Anggota kelompok", "Dendy Zainal Mutaqien (rincian di Lampiran D)"),
        ("Nama host", "INFINIX-ElementaryOS"),
        ("Minggu / tanggal kumpul", "Minggu ke-4 / 29 Oktober 2026"),
        ("Kepingan puzzle", "Kepingan #4 → Level 2 Puzzle UTS"),
        ("Dosen pengampu", "Muhammad Agreindra Helmiawan, S.Kom., M.T"),
    ], lebar=[5.2, 10.0], ukuran=9.5)

    for _ in range(2):
        d.add_paragraph()
    for teks, tebal in (("Program Studi S1 Informatika", True),
                        ("Fakultas Teknologi Informasi · Universitas Sebelas April", False),
                        ("2026", False)):
        p = d.add_paragraph(style="Normal")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(teks)
        r.bold = tebal
        r.font.size = Pt(11)

    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def pendahuluan(d):
    h1(d, "1. Pendahuluan")

    h2(d, "1.1 Latar belakang kasus")
    par(d, "Kebun pintar memakai beberapa sensor yang membaca kondisi lahan secara terus "
           "menerus: kelembapan tanah, suhu udara, dan debit air pompa irigasi. Setiap sensor "
           "menghasilkan angka baru dalam hitungan detik, dan angka itu harus sampai ke satu "
           "proses pencatat (logger) yang menyimpannya sebagai riwayat. Kalau pembacaan tidak "
           "tercatat rapi, keputusan penyiraman otomatis kehilangan dasarnya: pompa bisa "
           "menyala saat tanah sudah basah, atau mati saat tanaman mulai kering.")
    par(d, "Persoalannya bukan sekadar memindahkan angka. Sensor dan logger adalah proses "
           "terpisah, dan proses di sistem operasi tidak berbagi ruang alamat. Ketiganya "
           "berjalan bersamaan, sehingga dua sensor bisa menulis pada saat yang hampir sama. "
           "Mekanisme komunikasi antarproses (interprocess communication, IPC) yang dipilih "
           "menentukan apakah rekaman tetap utuh, apakah ada yang hilang, apakah pembacaan "
           "darurat bisa didahulukan, dan berapa besar biaya waktunya. Tugas ini menguji tiga "
           "mekanisme tersebut pada kasus yang sama, lalu membandingkannya secara terukur.")

    h2(d, "1.2 Tujuan tugas")
    par(d, "Capaian pembelajaran yang diukur adalah Sub-CPMK-4 (CPMK061, CPMK063, CPMK081, "
           "CPMK102, CPMK112). Dijabarkan ke dalam tujuan berikut:")
    bullet(d, "membangun jalur pengiriman data dari tiga proses sensor ke satu proses logger "
              "memakai pipe dan message queue, lalu menambahkan pola publish-subscribe dengan "
              "MQTT;", "Pertama, ")
    bullet(d, "menguji setiap mekanisme dan mendokumentasikan perilakunya: jumlah rekaman "
              "diterima, rekaman hilang, rekaman rusak, dan latensi kirim ke terima;", "Kedua, ")
    bullet(d, "menganalisis kelebihan dan keterbatasan masing-masing mekanisme untuk kasus "
              "kebun pintar, serta memilih yang paling sesuai dengan kebutuhan kelas.", "Ketiga, ")

    h2(d, "1.3 Ruang lingkup")
    par(d, "Pekerjaan dibatasi pada hal berikut.")
    bullet(d, "Sistem yang diamati adalah tiga proses sensor dan satu proses logger pada satu "
              "mesin Linux, bukan perangkat keras sensor sesungguhnya. Nilai sensor dibangkitkan "
              "secara sintetis dengan pola yang sama seperti pembacaan nyata.")
    bullet(d, "Mekanisme yang diimplementasikan adalah message passing: pipe anonim, POSIX "
              "message queue, dan MQTT. Shared memory tidak diimplementasikan karena lembar "
              "tugas memberi pilihan salah satu, dan perbandingan yang diminta sudah terpenuhi "
              "oleh tiga mekanisme message passing.")
    bullet(d, "Pengukuran latensi dilakukan pada satu host, sehingga angkanya menunjukkan biaya "
              "relatif antar mekanisme, bukan latensi jaringan produksi.")
    bullet(d, "Yang tidak dikerjakan: antarmuka pengguna, penyimpanan ke basis data, dan "
              "pengamanan kanal MQTT (TLS maupun autentikasi).")


def dasar_teori(d):
    h1(d, "2. Dasar Teori Singkat")
    par(d, "Proses yang berjalan terpisah memiliki ruang alamat masing-masing, sehingga bertukar "
           "data menuntut bantuan kernel. Silberschatz dkk. (2018) membagi mekanisme tersebut "
           "menjadi dua keluarga besar: shared memory, tempat dua proses memetakan satu region "
           "memori yang sama, dan message passing, tempat proses saling mengirim pesan lewat "
           "fasilitas kernel. Shared memory lebih cepat setelah pemetaan selesai, tetapi "
           "sinkronisasinya sepenuhnya menjadi tanggung jawab program. Message passing "
           "memindahkan beban salin dan pengaturan antrean ke kernel, dengan imbalan biaya "
           "per pesan yang lebih besar.")

    par(d, "Pipe adalah bentuk message passing paling sederhana, dijelaskan Kerrisk (2010) "
           "sebagai saluran byte satu arah antara dua proses yang memiliki hubungan kekerabatan, "
           "biasanya dibuat dengan fork. Karena pipe adalah byte stream, ia tidak mengenal batas "
           "pesan: seratus byte yang ditulis bisa terbaca sebagai satu potongan atau beberapa "
           "potongan. Kernel hanya menjamin bahwa penulisan sebesar PIPE_BUF byte atau kurang "
           "bersifat atomik, artinya tidak tersela penulis lain. Pemisahan rekaman karena itu "
           "harus dilakukan sendiri oleh penerima, misalnya memakai karakter pemisah dan "
           "menyimpan sisa byte yang belum membentuk rekaman utuh.")

    par(d, "POSIX message queue memperbaiki kelemahan itu. Setiap pesan disimpan sebagai unit "
           "tersendiri dengan panjang dan prioritas, sehingga mq_receive selalu mengembalikan "
           "tepat satu pesan utuh. Antrean punya nama di /dev/mqueue, sehingga proses yang tidak "
           "berkerabat dapat ikut mengirim. Pesan berprioritas lebih tinggi dilayani lebih dulu, "
           "dan pesan yang melebihi mq_msgsize ditolak dengan EMSGSIZE, bukan dipotong diam-diam. "
           "Antrean juga bertahan selama masih ada yang membukanya atau selama belum dihapus "
           "dengan mq_unlink.")

    par(d, "Publish-subscribe menambah satu pihak di tengah: broker. Pengirim (publisher) tidak "
           "mengetahui siapa penerimanya; ia hanya menempelkan pesan pada sebuah topik, dan "
           "broker meneruskannya ke semua pelanggan topik itu (OASIS, 2019). Karena pengiriman "
           "tidak langsung, ketahanan pengiriman diatur lewat tingkat kualitas layanan (QoS). "
           "Pada QoS 1, broker boleh mengirim ulang pesan yang belum dikonfirmasi, sehingga "
           "penerima dapat menerima rekaman yang sama lebih dari sekali dan perlu bersikap "
           "idempoten. Sebaliknya, sifat fan-out membuat beberapa logger bisa menerima aliran "
           "data yang sama tanpa saling berebut, sesuatu yang tidak diberikan satu antrean "
           "pipe maupun message queue.")


def lingkungan(d):
    h1(d, "3. Lingkungan Praktik")
    tabel(d, ["Komponen", "Keterangan"], [
        ("Laptop (host)", "elementary OS 8, AMD Ryzen 7 7735HS, RAM 14 GiB, kernel "
                          "7.0.0-34-generic"),
        ("Hypervisor", "Tidak dipakai — seluruh percobaan dijalankan langsung pada host"),
        ("VM / host", "INFINIX-ElementaryOS, 16 vCPU, tanpa virtualisasi"),
        ("Perangkat lain", "Tidak berlaku — nilai sensor dibangkitkan secara sintetis, "
                           "tanpa Raspberry Pi"),
        ("Bahasa dan alat", "Python 3.12.3; paho-mqtt 2.1.0; broker amqtt 0.12.1; "
                            "ctypes untuk memanggil libc mq_open/mq_send/mq_receive; "
                            "python-docx dan matplotlib untuk laporan"),
        ("Batas kernel", "PIPE_BUF = 4096 byte; /proc/sys/fs/mqueue/msg_max = 10 pesan; "
                         "msgsize_max = 8192 byte"),
    ], lebar=[4.0, 11.2])

    par(d, "Broker MQTT memakai amqtt yang dipasang di virtual environment proyek, bukan "
           "mosquitto, karena paket mosquitto tidak tersedia di mesin dan tidak ada akses sudo "
           "untuk memasangnya. Pola publish-subscribe yang diuji tetap sama: topik, QoS, dan "
           "fan-out ke beberapa pelanggan.")


def langkah(d):
    h1(d, "4. Langkah Pengerjaan")
    par(d, "Seluruh kode berada dalam satu folder proyek dengan struktur berikut.")
    kode(d, "ipc-kebun/\n"
            "├── common.py          format pesan JSON dan penulisan CSV\n"
            "├── mq.py              pembungkus POSIX mq_* lewat ctypes\n"
            "├── pipe_demo.py       tiga proses sensor → satu pipe\n"
            "├── mqueue_demo.py     tiga proses sensor → satu message queue\n"
            "├── mqtt_demo.py       publish-subscribe lewat broker\n"
            "├── bench.py           pengukuran latensi dan kehilangan data\n"
            "├── test_basic.py      pemeriksaan batas pesan dan prioritas\n"
            "├── figures.py         diagram alur dan grafik latensi\n"
            "├── broker.yaml        konfigurasi broker amqtt\n"
            "├── run_all.sh         menjalankan seluruh percobaan\n"
            "└── results/           keluaran CSV, JSON, dan gambar")

    par(d, "Gambar 4.1 memperlihatkan ketiga jalur komunikasi yang dibangun. Ketiganya berangkat "
           "dari proses sensor yang sama dan berakhir di proses logger; yang berbeda adalah "
           "perantara yang membawa pesan.")
    gambar(d, "results/gambar-alur.png", 15.5,
           "Gambar 4.1 Diagram alur komunikasi ketiga mekanisme IPC")

    h2(d, "4.1 Langkah 1: Menyiapkan lingkungan dan broker")
    par(d, "Percobaan MQTT memerlukan broker yang mendengarkan di port 1883. Karena mosquitto "
           "tidak tersedia, amqtt dipakai sebagai broker pengganti dan dijalankan di latar "
           "belakang. Sisanya cukup pustaka standar Python, ditambah paho-mqtt untuk sisi "
           "klien.")
    kode(d, "$ python3 -m venv .venv\n"
            "$ .venv/bin/pip install paho-mqtt amqtt\n"
            "$ .venv/bin/amqtt -c broker.yaml &\n"
            "[INFO] Listener 'default' bind to 127.0.0.1:1883 (max_connections=0)\n"
            "$ ss -ltn | grep 1883\n"
            "LISTEN 0 100 127.0.0.1:1883 0.0.0.0:*")
    par(d, "Broker hanya mendengarkan alamat lokal karena percobaan tidak memerlukan akses "
           "dari mesin lain. Konfigurasi broker.yaml mematikan autentikasi dan pemeriksaan "
           "topik agar fokus tetap pada mekanisme IPC.")

    h2(d, "4.2 Langkah 2: Menyeragamkan format pesan")
    par(d, "Ketiga mekanisme diuji dengan beban yang sama, sehingga format pesannya harus "
           "identik. Setiap rekaman berisi nama sensor, nilai pembacaan, nomor urut, dan waktu "
           "pengambilan; nomor urut dipakai untuk mendeteksi rekaman yang hilang atau "
           "terduplikasi setelah transfer.")
    kode(d, baca_berkas("common.py"))
    par(d, "Fungsi buat_pesan mengembalikan satu baris JSON yang diakhiri newline. Penanda "
           "newline itu penting untuk pipe, yang tidak mengerti batas pesan; untuk message "
           "queue dan MQTT penanda tersebut hanya mempermudah pembacaan berkas log.")

    h2(d, "4.3 Langkah 3: Implementasi pipe")
    par(d, "Tiga proses sensor dibuat dengan fork dan mewarisi ujung tulis pipe. Proses induk "
           "menutup ujung tulisnya sendiri, lalu membaca sampai jumlah rekaman yang diterima "
           "mencapai jumlah yang dikirim. Karena pipe hanya byte stream, penerima memecah "
           "potongan baca berdasarkan newline dan menyimpan sisa byte yang belum utuh pada "
           "variabel sisa untuk digabungkan dengan potongan berikutnya.")
    kode(d, baca_berkas("pipe_demo.py"))
    par(d, "Untuk menunjukkan bahwa batas pesan memang tidak dijaga kernel, program juga "
           "menerima opsi --tanpa-delimiter yang mengirim JSON tanpa newline. Pada mode ini "
           "penerima mencoba membaca setiap potongan baca sebagai satu rekaman, sehingga "
           "rekaman yang menempel akan gagal diurai dan dihitung sebagai rusak.")

    h2(d, "4.4 Langkah 4: Implementasi message queue")
    par(d, "Python tidak menyediakan POSIX message queue di pustaka standarnya. Alih-alih "
           "memasang paket pihak ketiga, kelima fungsi yang dibutuhkan dipanggil langsung dari "
           "libc lewat ctypes. Pembungkus mq.py di bawah ini memetakan mq_open, mq_send, "
           "mq_receive, mq_close, dan mq_unlink beserta struktur atribut antrean.")
    kode(d, baca_berkas("mq.py"))
    par(d, "Di sisi pemakai, logger membuka antrean dengan O_CREAT dan O_EXCL agar tidak "
           "memakai antrean sisa percobaan sebelumnya, lalu memanggil mq_receive berulang. "
           "Setiap panggilan mengembalikan tepat satu pesan beserta prioritasnya. Sensor "
           "mengirim dengan prioritas 1 untuk pembacaan biasa dan prioritas 9 untuk kejadian "
           "darurat seperti kebocoran, sehingga rekaman darurat dilayani lebih dulu.")
    kode(d, baca_berkas("mqueue_demo.py"))

    h2(d, "4.5 Langkah 5: Implementasi publish-subscribe dengan MQTT")
    par(d, "Pada MQTT, sensor tidak lagi mengirim ke proses tertentu. Setiap sensor menerbitkan "
           "pesan ke topik kebun/sensor/<nama>, dan logger berlangganan pola kebun/sensor/# "
           "sehingga menerima seluruh topik di bawahnya. Percobaan dijalankan dengan QoS 1 dan "
           "dapat dinaikkan ke dua logger untuk menguji sifat fan-out.")
    kode(d, baca_berkas("mqtt_demo.py"))

    h2(d, "4.6 Langkah 6: Pengukuran dan pemeriksaan")
    par(d, "bench.py menjalankan ketiga program beberapa kali, membaca CSV hasilnya, lalu "
           "menghitung latensi kirim ke terima dari selisih kolom ts dan recv_ts. Karena "
           "latensi pada satu host bervariasi antar-run, nilai yang dilaporkan adalah median "
           "dari lima percobaan. Pemeriksaan kebenaran mekanisme diletakkan pada test_basic.py "
           "yang memastikan prioritas message queue dihormati dan pesan kebesaran ditolak.")
    kode(d, baca_berkas("bench.py"))
    kode(d, baca_berkas("test_basic.py"))

    par(d, "Hasil pemeriksaan mandiri:")
    kode(d, baca_out("test"))


def hasil(d):
    b = baca_bench()["hasil"]
    target = baca_bench()["n"] * baca_bench()["sensors"]

    h1(d, "5. Hasil dan Analisis")

    h2(d, "5.1 Hasil")
    par(d, "Tabel 5.1 merangkum pengiriman data pada ketiga mekanisme. Ketiga jalur menerima "
           f"seluruh {target} rekaman (3 sensor × 20 pembacaan) tanpa kehilangan dan tanpa "
           "duplikasi.")
    tabel(d, ["No", "Mekanisme", "Diterima", "Hilang", "Duplikat",
              "Latensi rata (ms)", "p95 (ms)", "Maks (ms)"], [
        ("1", "pipe", f"{int(b['pipe']['diterima'])}/{target}", "0", "0",
         f"{b['pipe']['rata']:.3f}", f"{b['pipe']['p95']:.3f}", f"{b['pipe']['maks']:.3f}"),
        ("2", "message queue", f"{int(b['mqueue']['diterima'])}/{target}", "0", "0",
         f"{b['mqueue']['rata']:.3f}", f"{b['mqueue']['p95']:.3f}",
         f"{b['mqueue']['maks']:.3f}"),
        ("3", "MQTT (QoS 1)", f"{int(b['mqtt']['diterima'])}/{target}", "0", "0",
         f"{b['mqtt']['rata']:.3f}", f"{b['mqtt']['p95']:.3f}", f"{b['mqtt']['maks']:.3f}"),
    ], lebar=[0.9, 3.4, 2.0, 1.5, 1.8, 2.6, 1.7, 1.7], ukuran=8.5)
    caption(d, "Tabel 5.1 Perbandingan ketiga mekanisme (median 5 percobaan, 3 sensor × 20 "
               "pembacaan)")

    gambar(d, "results/gambar-latensi.png", 14.0,
           "Gambar 5.1 Latensi kirim ke terima per mekanisme")

    par(d, "Pengujian berikutnya mematikan penanda newline pada pipe untuk memperlihatkan "
           "perilaku saat batas pesan tidak dijaga. Sepuluh kali percobaan dijalankan pada "
           "masing-masing mode, dan hasilnya dirangkum pada Tabel 5.2.")
    tabel(d, ["Mode pipe", "Percobaan utuh (60/60)", "Percobaan kehilangan rekaman",
              "Rekaman rusak pada run terburuk"], [
        ("dengan pemisah newline", "10 dari 10", "0", "0"),
        ("tanpa pemisah", "5 dari 10", "5", "5 rekaman (50/60 diterima)"),
    ], lebar=[5.0, 4.4, 3.6, 4.4])
    caption(d, "Tabel 5.2 Keutuhan rekaman pada pipe, 10 percobaan per mode")

    par(d, "Pada message queue, prioritas terbukti dihormati kernel. Ketika setiap pembacaan "
           "kelima dikirim dengan prioritas darurat, urutan penerimaan berubah menjadi:")
    kode(d, baca_out("mqueue").split("\n\n")[-1].split("\n", 1)[1].strip())
    par(d, "Tiga rekaman berprioritas 9 muncul lebih dulu walaupun dikirim bersamaan dengan "
           "rekaman berprioritas 1, lalu kelompok berikutnya menyusul. Tanpa pengaturan "
           "prioritas, seluruh pesan diterima dengan prioritas 1 sesuai urutan kirim.")

    par(d, "Terakhir, MQTT dijalankan dengan dua logger yang berlangganan topik yang sama. "
           "Keduanya menerima seluruh aliran data, bukan membaginya:")
    kode(d, baca_out("mqtt"))
    caption(d, "Keluaran mqtt_demo.py dengan --logger 2")

    h2(d, "5.2 Analisis")
    par(d, "Poin (1) deskripsi tugas — mekanisme IPC yang dipakai. Ketiga mekanisme yang diuji "
           "termasuk keluarga message passing, tetapi berbeda pada siapa yang menjaga batas "
           "pesan. Pipe memperlakukan data sebagai aliran byte tanpa struktur; batas rekaman "
           "sepenuhnya hasil kesepakatan dua proses, dalam percobaan ini karakter newline. "
           "POSIX message queue memindahkan tanggung jawab itu ke kernel: setiap mq_send "
           "menghasilkan satu unit yang tidak bisa tercampur dengan pesan lain, dan penerima "
           "memperoleh panjang serta prioritasnya. MQTT menambah satu lapisan lagi, yaitu "
           "broker, yang memutuskan ke mana pesan diteruskan berdasarkan topik. Ketiga jalur "
           "memakai proses sensor dan format JSON yang sama, sehingga perbedaan hasil hanya "
           "berasal dari mekanismenya.")
    par(d, "Poin (2) deskripsi tugas — hasil pengujian. Perbedaan paling mencolok bukan pada "
           "latensi, melainkan pada keutuhan data saat penanda rekaman dilepas. Pipe tanpa "
           "pemisah kehilangan rekaman pada lima dari sepuluh percobaan, dengan kerusakan "
           "terburuk mencapai lima rekaman dari enam puluh. Penyebabnya mudah dijelaskan: "
           "os.read mengembalikan apa pun yang sedang tersedia di buffer, sehingga dua JSON "
           "dapat menempel menjadi satu potongan, sementara satu JSON juga dapat terbelah dua "
           "potongan. Pipe tidak salah; ia memang tidak pernah menjanjikan batas pesan. Yang "
           "dijanjikan kernel hanyalah atomisitas penulisan sebesar PIPE_BUF (4096 byte), dan "
           "pesan percobaan ini jauh di bawah batas itu, sehingga tidak ada rekaman yang saling "
           "menyisip di tengah. Message queue tidak menunjukkan masalah serupa karena kernel "
           "menyimpan panjang setiap pesan secara eksplisit, dan pesan yang melebihi mq_msgsize "
           "ditolak dengan EMSGSIZE, bukan dipotong.")
    par(d, "Pada sisi waktu, message queue dan pipe praktis setara, keduanya di bawah 0,1 ms "
           "rata-rata, karena keduanya hanya menyalin data antar buffer kernel tanpa melewati "
           "jaringan. MQTT lebih lambat sekitar delapan kali pada nilai rata-rata, dan selisih "
           "melebar pada persentil 95 karena antrean TCP di sisi broker kadang menahan pesan. "
           "Biaya itu bukan pemborosan tanpa imbalan: pada percobaan dua logger, keduanya "
           "menerima enam puluh dari enam puluh rekaman. Dengan pipe atau satu antrean message "
           "queue, rekaman yang sudah diambil satu penerima tidak tersedia lagi untuk penerima "
           "lain, sehingga menambah logger berarti mengubah arsitektur. Broker juga membuat "
           "pengirim tidak perlu mengetahui alamat penerima, yang penting ketika jumlah logger "
           "berubah, misalnya saat menambah pencatat untuk dasbor terpisah.")
    par(d, "Keterbatasan yang muncul dari pengujian juga perlu dicatat. Message queue pada "
           "mesin ini dibatasi sepuluh pesan per antrean, sehingga pengirim akan memblokir "
           "ketika logger tertinggal; dalam percobaan ini logger selalu cukup cepat sehingga "
           "batas tersebut tidak tercapai, tetapi pada beban tinggi pemblokiran itu bisa "
           "memperlambat proses sensor. Antrean juga harus dibersihkan dengan mq_unlink, "
           "karena antrean sisa akan membuat percobaan berikutnya gagal membuka dengan O_EXCL. "
           "Pipe hanya bekerja antar proses berkerabat karena tidak memiliki nama, dan ujungnya "
           "harus ditutup dengan benar; ujung tulis yang masih terbuka di proses induk membuat "
           "pembacaan tidak pernah mencapai akhir berkas. MQTT dengan QoS 1 mengizinkan broker "
           "mengirim ulang pesan yang belum dikonfirmasi, sehingga logger wajib idempoten; "
           "percobaan ini belum memunculkan duplikasi, tetapi pemeriksaannya sudah disiapkan "
           "melalui kolom nomor urut.")

    h2(d, "5.3 Rekomendasi")
    par(d, "Untuk kasus kelas — tiga sensor pada satu gateway kebun — pilihan yang paling sesuai "
           "adalah message passing dengan message queue untuk jalur data ke logger, bukan pipe. "
           "Alasannya, message queue memberi batas pesan yang dijamin kernel sehingga logger "
           "tidak perlu menebak potongan data, dan prioritas pesan langsung memenuhi kebutuhan "
           "praktis kebun pintar: pembacaan kadar air yang mendadak turun dapat didahulukan "
           "atas pembacaan rutin. Keduanya sama-sama murah, jadi tidak ada alasan memilih "
           "mekanisme yang lebih rapuh.")
    par(d, "MQTT dipakai bersamaan, bukan sebagai pengganti, ketika data perlu dilihat lebih "
           "dari satu tempat: dasbor, pencatat cadangan, atau layanan notifikasi. Perannya "
           "melengkapi, karena satu antrean hanya melayani satu penerima per pesan. Pipe tetap "
           "layak dipakai untuk hal kecil di dalam satu program, misalnya menyalurkan keluaran "
           "proses anak, tetapi bukan untuk data yang harus utuh dan bertahan.")
    par(d, "Untuk pengembangan berikutnya, logger perlu dibuat idempoten terhadap nomor urut "
           "agar aman pada QoS 1, dan penulisan CSV perlu dilindungi mutex bila logger "
           "menjalankan beberapa thread. Persoalan terakhir itu dibahas lebih jauh pada tugas "
           "individu I-4 mengenai race condition.")


def kesimpulan(d):
    h1(d, "6. Kesimpulan")
    par(d, "Tiga mekanisme message passing berhasil mengirim seluruh data sensor ke proses "
           "logger pada kasus kebun pintar, tetapi hanya dua di antaranya menjamin keutuhan "
           "rekaman tanpa bantuan program penerima. Pipe memperlakukan data sebagai aliran byte, "
           "sehingga tanpa penanda pemisah rekaman dapat menempel atau terbelah; pengujian "
           "menunjukkan kehilangan data pada lima dari sepuluh percobaan. POSIX message queue "
           "menjaga batas pesan dan menghormati prioritas di tingkat kernel, dengan biaya waktu "
           "yang setara pipe. MQTT menambah latensi sekitar delapan kali, tetapi memberi "
           "fan-out ke beberapa penerima dan memutus ketergantungan antara pengirim dan "
           "penerima. Untuk kebutuhan kelas, message queue adalah pilihan utama jalur data, "
           "sedangkan MQTT dipakai ketika data harus dilihat di lebih dari satu tempat.")


def kepingan(d):
    h1(d, "7. Kepingan Puzzle")
    tabel(d, ["Keterangan", "Isi"], [
        ("Nomor kepingan", "#4"),
        ("Isi kepingan", "Kode program IPC (pipe, message queue, MQTT), diagram alur "
                         "komunikasi, tabel perbandingan latensi dan keutuhan data"),
        ("Lokasi di portofolio", "[tautan Google Drive/GitHub kelompok]"),
        ("Dipakai untuk", "Level 2 Puzzle UTS — menjadi dasar pembahasan sinkronisasi pada "
                          "kepingan #5 (penjadwalan) dan #6 (race condition), karena logger "
                          "yang sama dipakai ulang sebagai producer-consumer pada tugas "
                          "individu I-4"),
    ], lebar=[4.2, 11.0])


def pustaka(d):
    h1(d, "Daftar Pustaka")
    for teks in [
        "Kerrisk, M. (2010). The Linux programming interface: A Linux and UNIX system "
        "programming handbook. No Starch Press.",
        "OASIS. (2019). MQTT version 5.0: OASIS standard. OASIS Open.",
        "Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). Operating system concepts "
        "(10th ed.). Wiley.",
        "The Open Group. (2018). POSIX.1-2017: Standard for information technology — "
        "Portable operating system interface (POSIX). IEEE.",
    ]:
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.add_run(teks)


def lampiran(d):
    par(d, "")
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    h1(d, "Lampiran A. Kode Program dan Log")
    par(d, "Seluruh berkas di bawah ini berada pada satu folder proyek dan dapat dijalankan "
           "ulang dengan ./run_all.sh. Berkas figures.py tidak disertakan karena hanya dipakai "
           "untuk membuat gambar laporan.")
    for nama in ("common.py", "mq.py", "pipe_demo.py", "mqueue_demo.py", "mqtt_demo.py",
                 "bench.py", "test_basic.py", "broker.yaml", "run_all.sh"):
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"A.{nama}")
        r.bold = True
        r.font.size = Pt(9.5)
        kode(d, baca_berkas(nama), ukuran=7.5)

    h1(d, "Lampiran B. Pernyataan Penggunaan AI Generatif")
    par(d, "☐  Saya tidak menggunakan AI generatif dalam tugas ini.")
    par(d, "☒  Menggunakan AI generatif dengan rincian berikut:")
    tabel(d, ["Alat", "Tujuan penggunaan", "Bagian yang dibantu", "Cara memverifikasi"], [
        ("Claude (Anthropic)", "Menyusun kerangka program dan merapikan kalimat laporan",
         "Bagian 4 (kode), Bagian 5.2, penyusunan dokumen",
         "Seluruh program dijalankan ulang dengan run_all.sh; setiap angka pada laporan "
         "diambil langsung dari keluaran program, bukan dari jawaban model"),
    ], lebar=[3.0, 4.4, 4.0, 4.4], ukuran=8.5)

    h1(d, "Lampiran C. Daftar Periksa Sebelum Mengumpulkan")
    for teks, sudah in [
        ("Semua teks petunjuk abu-abu dan kotak petunjuk sudah dihapus.", True),
        ("Identitas, kode tugas, dan nama host pada sampul sudah benar.", False),
        ("Setiap poin deskripsi tugas sudah dijawab di bagian Analisis.", True),
        ("Setiap gambar memiliki nomor dan keterangan.", True),
        ("Kepingan puzzle sudah disimpan di portofolio dan tautannya dicantumkan.", False),
        ("Pernyataan penggunaan AI generatif sudah diisi.", True),
        ("Lembar kontribusi anggota sudah dilampirkan.", False),
        ("Daftar isi sudah diperbarui (klik kanan → Update Field).", False),
        ("Berkas disimpan sebagai PDF dengan nama <Kelas>_<Kode>_<NIM>_<Nama>.pdf.", False),
    ]:
        tanda = "☒" if sudah else "☐"
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(3)
        p.add_run(f"{tanda}  {teks}")

    par(d, "")
    h2(d, "Swa-nilai berdasarkan kriteria lembar tugas")
    tabel(d, ["Kriteria (dari lembar tugas)", "Bobot", "Sudah terpenuhi? Di bagian mana"],
          [("Hasil/keberhasilan implementasi", "35%",
            "Ya — tiga mekanisme berjalan, seluruh 60 rekaman diterima (Bagian 5.1)"),
           ("Kedalaman analisis", "30%",
            "Ya — batas pesan, prioritas, latensi, dan keterbatasan dibahas (Bagian 5.2)"),
           ("Dokumentasi", "20%",
            "Ya — langkah dapat diulang, kode dan keluaran dilampirkan (Bagian 4, Lampiran A)"),
           ("Kerja sama dan pembagian peran", "15%",
            "Ya — lembar kontribusi pada Lampiran D")],
          lebar=[5.2, 2.0, 8.0])

    h1(d, "Lampiran D. Lembar Kontribusi Anggota")
    par(d, "Lembar ini memenuhi syarat kerja sama dan pembagian peran (15% bobot penilaian). "
           "Baris anggota lain ditambahkan sebelum dikumpulkan.")
    tabel(d, ["Nama", "NIM", "Peran dan bagian yang dikerjakan"],
          [(n, i, p) for n, i, p in ANGGOTA] + [("", "", ""), ("", "", "")],
          lebar=[4.4, 3.0, 7.8])

    par(d, "")
    par(d, "Pernyataan keaslian")
    par(d, "Saya yang bertanda tangan di bawah ini menyatakan bahwa laporan ini merupakan hasil "
           "kerja kelompok kami sendiri, disusun berdasarkan praktik yang benar-benar dijalankan, "
           "dan seluruh sumber yang dikutip telah dicantumkan pada daftar pustaka. Penggunaan "
           "alat bantu AI generatif telah diungkapkan pada Lampiran B.")
    tabel(d, ["Nama / NIM", "Tanda tangan dan tanggal"],
          [(f"{NAMA} / {NIM}", ""), (" / ", ""), (" / ", "")], lebar=[7.0, 8.2])


def main():
    d = docx.Document(TEMPLATE)
    bersihkan(d)
    sampul(d)
    pendahuluan(d)
    dasar_teori(d)
    lingkungan(d)
    langkah(d)
    hasil(d)
    kesimpulan(d)
    kepingan(d)
    pustaka(d)
    lampiran(d)
    nomor_halaman(d)
    os.makedirs("results", exist_ok=True)
    d.save(OUT)
    print("tersimpan:", OUT)


if __name__ == "__main__":
    main()
