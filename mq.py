"""Pembungkus POSIX message queue lewat ctypes, tanpa paket tambahan."""
import ctypes
import os

_libc = ctypes.CDLL("libc.so.6", use_errno=True)
_libc.mq_open.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p]
_libc.mq_open.restype = ctypes.c_int
_libc.mq_send.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint]
_libc.mq_send.restype = ctypes.c_int
_libc.mq_receive.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint)]
_libc.mq_receive.restype = ctypes.c_ssize_t
_libc.mq_close.argtypes = [ctypes.c_int]
_libc.mq_unlink.argtypes = [ctypes.c_char_p]

O_RDONLY, O_WRONLY, O_CREAT, O_EXCL = 0, 1, 0o100, 0o200


class MQAttr(ctypes.Structure):
    _fields_ = [
        ("mq_flags", ctypes.c_long),
        ("mq_maxmsg", ctypes.c_long),
        ("mq_msgsize", ctypes.c_long),
        ("mq_curmsgs", ctypes.c_long),
    ]


class MQError(OSError):
    pass


def _cek(hasil, nama):
    if hasil < 0:
        e = ctypes.get_errno()
        raise MQError(e, f"mq_{nama}: {os.strerror(e)}")
    return hasil


def buka(nama, mode, maks_pesan=10, ukuran_pesan=1024, buat=False, eksklusif=False):
    flag = O_CREAT if buat else 0
    if eksklusif:
        flag |= O_EXCL
    attr = MQAttr(0, maks_pesan, ukuran_pesan, 0) if buat else None
    ptr = ctypes.byref(attr) if attr is not None else None
    fd = _cek(_libc.mq_open(nama.encode(), mode | flag, 0o600, ptr), "open")
    return fd


def kirim(fd, data, prioritas=0):
    _cek(_libc.mq_send(fd, data, len(data), prioritas), "send")


def terima(fd, ukuran_pesan=1024):
    buf = ctypes.create_string_buffer(ukuran_pesan)
    prio = ctypes.c_uint(0)
    n = _cek(_libc.mq_receive(fd, buf, ukuran_pesan, ctypes.byref(prio)), "receive")
    return buf.raw[:n], prio.value


def tutup(fd):
    _libc.mq_close(fd)


def hapus(nama):
    _libc.mq_unlink(nama.encode())
