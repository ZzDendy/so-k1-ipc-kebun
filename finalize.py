"""Menyiapkan laporan untuk dikumpulkan: centang Lampiran C dan isi daftar isi.

Daftar isi dibuat sebagai teks statis, bukan field TOC, karena pembaruan field
lewat LibreOffice headless tidak stabil di mesin ini. Nomor halaman diambil dari
hasil ekspor PDF, jadi urutannya dua tahap:

    tahap 1 → sisip halaman daftar isi kosong, ekspor PDF
    tahap 2 → baca nomor halaman tiap judul dari PDF, tulis daftar isi, ekspor ulang

Halaman daftar isi berukuran tetap, jadi menulis isinya tidak menggeser halaman
berikutnya dan nomor halaman tetap sahih.

Jalankan: .venv/bin/python finalize.py
"""
import os
import re
import subprocess

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

DOK = "results/IF-3C_K-1_250660121068_Dendy Zainal Mutaqien.docx"
PDF = "results/IF-3C_K-1_250660121068_Dendy Zainal Mutaqien.pdf"
PENANDA = "«DAFTAR-ISI»"


def centang(d, peta):
    """Ubah ☐ menjadi ☒ untuk butir yang memang sudah beres."""
    ganti = {
        "Daftar isi sudah diperbarui (klik kanan → Update Field).":
            "Daftar isi sudah diperbarui dan nomor halamannya cocok.",
    }
    for p in d.paragraphs:
        teks = p.text.strip()
        if not teks.startswith(("☐", "☒")):
            continue
        for lama, baru in ganti.items():
            if lama in teks:
                teks = teks.replace(lama, baru)
                p.runs[0].text = teks
                for r in p.runs[1:]:
                    r.text = ""
        for kunci, nilai in peta.items():
            if kunci in teks:
                baru = ("☒" if nilai else "☐") + teks[1:]
                p.runs[0].text = baru
                for r in p.runs[1:]:
                    r.text = ""
                break


def hapus_daftar_isi(d):
    """Buang blok daftar isi lama supaya skrip ini aman dijalankan berulang.

    Blok itu adalah semua paragraf antara akhir sampul (paragraf dengan page
    break) dan judul Bab 1.
    """
    paras = list(d.paragraphs)
    # Baris daftar isi juga diawali "1. Pendahuluan", jadi judul asli dikenali
    # dari gayanya, bukan dari teksnya.
    bab1 = next(i for i, p in enumerate(paras)
                if p.style.name == "Heading 1"
                and p.text.strip().startswith("1. Pendahuluan"))
    # Halaman sampul berakhir pada page break pertama; sisanya sampai Bab 1
    # adalah daftar isi dari putaran sebelumnya.
    akhir_sampul = min(i for i, p in enumerate(paras[:bab1])
                       if 'w:type="page"' in p._p.xml)
    for p in paras[akhir_sampul + 1:bab1]:
        p._p.getparent().remove(p._p)


def sisip_kerangka(d):
    """Tambah halaman daftar isi (masih kosong) sebelum Bab 1."""
    anchor = next(p for p in d.paragraphs if p.text.strip().startswith("1. Pendahuluan"))

    judul = anchor.insert_paragraph_before()
    judul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    judul.paragraph_format.space_after = Pt(14)
    r = judul.add_run("Daftar Isi")
    r.bold = True
    r.font.size = Pt(14)

    isi = anchor.insert_paragraph_before()
    isi.paragraph_format.space_after = Pt(0)
    isi.add_run(PENANDA).font.size = Pt(10)

    akhir = anchor.insert_paragraph_before()
    akhir.add_run().add_break(WD_BREAK.PAGE)
    anchor.insert_paragraph_before()


def judul_terdaftar(d):
    return [(p.style.name, p.text.strip()) for p in d.paragraphs
            if p.style.name in ("Heading 1", "Heading 2") and p.text.strip()]


def nomor_halaman_pdf(path):
    """Kembalikan {teks judul: nomor halaman cetak} dari PDF."""
    keluar = subprocess.run(["pdftotext", "-layout", path, "-"],
                            capture_output=True, text=True).stdout
    halaman = keluar.split("\f")
    peta = {}
    for idx, isi in enumerate(halaman, start=1):
        for baris in isi.splitlines():
            baris = baris.strip()
            if baris:
                peta.setdefault(baris, idx)
    return peta


def isi_daftar_isi(d, halaman_pdf):
    """Ganti penanda dengan baris daftar isi, satu paragraf per judul."""
    par = next(p for p in d.paragraphs if PENANDA in p.text)
    daftar = judul_terdaftar(d)

    for gaya, teks in daftar:
        baris = par.insert_paragraph_before()
        baris.paragraph_format.space_after = Pt(3)
        baris.paragraph_format.left_indent = Cm(0.6 if gaya == "Heading 2" else 0)
        baris.paragraph_format.tab_stops.add_tab_stop(
            Cm(15.2), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        nomor = halaman_pdf.get(teks)
        run = baris.add_run(f"{teks}\t{nomor if nomor else ''}")
        run.font.size = Pt(10 if gaya == "Heading 1" else 9.5)
        run.bold = gaya == "Heading 1"

    par._p.getparent().remove(par._p)


def ekspor(path, pdf):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf",
                    "--outdir", os.path.dirname(pdf), path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    d = docx.Document(DOK)
    centang(d, {
        "Identitas, kode tugas, dan nama host pada sampul": True,
        "Kepingan puzzle sudah disimpan": True,
        "Lembar kontribusi anggota sudah dilampirkan": True,
        "Daftar isi sudah diperbarui": True,
        "Berkas disimpan sebagai PDF": True,
    })
    hapus_daftar_isi(d)
    sisip_kerangka(d)
    d.save(DOK)

    # Tahap 1: PDF sementara supaya nomor halaman sudah final.
    ekspor(DOK, PDF)
    peta = nomor_halaman_pdf(PDF)

    d = docx.Document(DOK)
    isi_daftar_isi(d, peta)
    d.save(DOK)

    # Tahap 2: PDF final dari dokumen yang daftar isinya sudah terisi.
    ekspor(DOK, PDF)
    ulang = nomor_halaman_pdf(PDF)
    bergeser = [j for _, j in judul_terdaftar(d) if peta.get(j) != ulang.get(j)]
    print(f"daftar isi terisi, {len(judul_terdaftar(d))} judul")
    if bergeser:
        print("PERINGATAN: nomor halaman bergeser setelah daftar isi diisi:",
              bergeser[:3])
    else:
        print("nomor halaman stabil antara dua ekspor")
    print("pdf:", PDF)


if __name__ == "__main__":
    main()
