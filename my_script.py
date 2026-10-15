"""Определяет ОС, собирает её параметры и сохраняет их в JSON.

Запуск: python my_script.py [путь_к_json]
Используются только стандартные модули Python; системные утилиты ОС
(uname, systeminfo, sysctl, wmic и т.п.) не вызываются.
"""

import ctypes
import ctypes.util
import datetime
import getpass
import json
import locale
import os
import platform
import shutil
import socket
import struct
import sys
import time
import uuid

DEFAULT_OUTPUT = "os_info.json"


def detect_os():
    """Возвращает 'Windows', 'Linux', 'MacOS' или 'Unknown'."""
    if sys.platform.startswith("win"):
        return "Windows"
    if sys.platform.startswith("linux"):
        return "Linux"
    if sys.platform == "darwin":
        return "MacOS"
    return "Unknown"


def safe(func, default=None):
    """Выполняет func и возвращает default, если сбор параметра не удался."""
    try:
        return func()
    except Exception:
        return default


# ---------- вспомогательные функции для macOS (sysctl через libc, без утилиты) ----------

def _mac_sysctl(name, ctype):
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
    if ctype is str:
        size = ctypes.c_size_t(0)
        libc.sysctlbyname(name.encode(), None, ctypes.byref(size), None, 0)
        buf = ctypes.create_string_buffer(size.value)
        libc.sysctlbyname(name.encode(), buf, ctypes.byref(size), None, 0)
        return buf.value.decode()
    value = ctype()
    size = ctypes.c_size_t(ctypes.sizeof(value))
    if libc.sysctlbyname(name.encode(), ctypes.byref(value), ctypes.byref(size), None, 0) != 0:
        raise OSError("sysctlbyname failed: " + name)
    return value


# ---------- сбор параметров ----------

def get_os_info(os_name):
    info = {
        "family": os_name,
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "platform_string": platform.platform(),
        "sys_platform": sys.platform,
    }
    if os_name == "Windows":
        release, version, csd, ptype = platform.win32_ver()
        info["edition"] = safe(platform.win32_edition)
        info["build"] = version
        info["service_pack"] = csd or None
    elif os_name == "Linux":
        os_release = safe(platform.freedesktop_os_release, {})
        info["distribution"] = os_release.get("PRETTY_NAME")
        info["distribution_id"] = os_release.get("ID")
        info["distribution_version"] = os_release.get("VERSION_ID")
        libc_name, libc_version = safe(platform.libc_ver, ("", ""))
        info["libc"] = (libc_name + " " + libc_version).strip() or None
    elif os_name == "MacOS":
        mac_release, _, mac_machine = platform.mac_ver()
        info["macos_version"] = mac_release
    return info


def get_cpu_info(os_name):
    cpu = {
        "architecture": platform.machine(),
        "bitness": struct.calcsize("P") * 8,
        "logical_cores": os.cpu_count(),
        "model": None,
    }
    if os_name == "Windows":
        cpu["model"] = safe(platform.processor) or os.environ.get("PROCESSOR_IDENTIFIER")
    elif os_name == "Linux":
        def read_model():
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if line.lower().startswith(("model name", "hardware", "processor\t: ")):
                        value = line.split(":", 1)[1].strip()
                        if value and not value.isdigit():
                            return value
            return None
        cpu["model"] = safe(read_model)
    elif os_name == "MacOS":
        cpu["model"] = safe(lambda: _mac_sysctl("machdep.cpu.brand_string", str))
    return cpu


def get_memory_info(os_name):
    total = available = None
    if os_name == "Windows":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            total, available = stat.ullTotalPhys, stat.ullAvailPhys
    elif os_name == "Linux":
        def read_meminfo():
            values = {}
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    key, rest = line.split(":", 1)
                    values[key] = int(rest.split()[0]) * 1024
            return values.get("MemTotal"), values.get("MemAvailable")
        total, available = safe(read_meminfo, (None, None))
    elif os_name == "MacOS":
        total = safe(lambda: _mac_sysctl("hw.memsize", ctypes.c_uint64).value)
        available = None  # на macOS без утилит доступна только общая память

    def to_gb(value):
        return round(value / 1024 ** 3, 2) if value else None

    return {
        "total_bytes": total,
        "available_bytes": available,
        "total_gb": to_gb(total),
        "available_gb": to_gb(available),
        "used_percent": round((1 - available / total) * 100, 1) if total and available else None,
    }


def get_disk_info():
    root = os.path.abspath(os.sep) if os.name != "nt" else os.environ.get("SystemDrive", "C:") + "\\"
    usage = shutil.disk_usage(root)
    return {
        "path": root,
        "total_gb": round(usage.total / 1024 ** 3, 2),
        "used_gb": round(usage.used / 1024 ** 3, 2),
        "free_gb": round(usage.free / 1024 ** 3, 2),
        "used_percent": round(usage.used / usage.total * 100, 1),
    }


def get_uptime_seconds(os_name):
    if os_name == "Windows":
        kernel32 = ctypes.windll.kernel32
        kernel32.GetTickCount64.restype = ctypes.c_ulonglong
        return kernel32.GetTickCount64() // 1000
    if os_name == "Linux":
        with open("/proc/uptime", encoding="utf-8") as f:
            return int(float(f.read().split()[0]))
    if os_name == "MacOS":
        class Timeval(ctypes.Structure):
            _fields_ = [("tv_sec", ctypes.c_long), ("tv_usec", ctypes.c_long)]
        boot = _mac_sysctl("kern.boottime", Timeval)
        return int(time.time() - boot.tv_sec)
    return None


def get_boot_info(os_name):
    uptime = safe(lambda: get_uptime_seconds(os_name))
    if uptime is None:
        return {"uptime_seconds": None, "uptime_human": None, "boot_time": None}
    boot_time = datetime.datetime.now() - datetime.timedelta(seconds=uptime)
    days, rest = divmod(uptime, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    return {
        "uptime_seconds": uptime,
        "uptime_human": f"{days}d {hours}h {minutes}m",
        "boot_time": boot_time.isoformat(timespec="seconds"),
    }


def get_network_info():
    hostname = socket.gethostname()

    def local_ip():
        # UDP-сокет ничего не отправляет: connect лишь выбирает исходящий интерфейс
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]

    mac = uuid.getnode()
    return {
        "hostname": hostname,
        "fqdn": safe(socket.getfqdn),
        "local_ip": safe(local_ip),
        "mac_address": ":".join(f"{(mac >> shift) & 0xff:02x}" for shift in range(40, -1, -8)),
    }


def get_user_info():
    return {
        "username": safe(getpass.getuser),
        "home_dir": os.path.expanduser("~"),
        "is_admin": safe(_is_admin),
        "shell": os.environ.get("SHELL") or os.environ.get("COMSPEC"),
    }


def _is_admin():
    if os.name == "nt":
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    return os.geteuid() == 0


def get_locale_info():
    lang, encoding = safe(locale.getlocale, (None, None))
    offset = -time.timezone if not time.localtime().tm_isdst else -time.altzone
    return {
        "language": lang,
        "encoding": encoding,
        "preferred_encoding": locale.getpreferredencoding(False),
        "filesystem_encoding": sys.getfilesystemencoding(),
        "timezone": time.tzname[time.localtime().tm_isdst],
        "utc_offset_hours": offset / 3600,
    }


def get_python_info():
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
        "executable": sys.executable,
    }


def collect():
    os_name = detect_os()
    return {
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "os": get_os_info(os_name),
        "cpu": get_cpu_info(os_name),
        "memory": get_memory_info(os_name),
        "disk": safe(get_disk_info),
        "boot": get_boot_info(os_name),
        "network": get_network_info(),
        "user": get_user_info(),
        "locale": get_locale_info(),
        "python": get_python_info(),
    }


def main():
    output = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT
    data = collect()
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Обнаружена ОС: {data['os']['family']}")
    print(f"Параметры сохранены в файл: {os.path.abspath(output)}")


if __name__ == "__main__":
    main()
