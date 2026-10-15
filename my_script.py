
import datetime
import json
import os
import platform
import sys

DEFAULT_OUTPUT = "os_info.json"


def detect_os():
    if sys.platform.startswith("win"):
        return "Windows"
    if sys.platform.startswith("linux"):
        return "Linux"
    if sys.platform == "darwin":
        return "MacOS"
    return "Unknown"


def safe(func, default=None):
    try:
        return func()
    except Exception:
        return default


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


def collect():
    os_name = detect_os()
    return {
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "os": get_os_info(os_name),
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
