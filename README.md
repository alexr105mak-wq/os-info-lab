# Лабораторная работа 1. Сбор параметров ОС

Скрипт `my_script.py` определяет, в какой операционной системе он запущен (Windows, Linux или macOS), собирает её параметры и сохраняет их в файл формата JSON.

## Запуск

```bash
python my_script.py
```

Результат записывается в `os_info.json` в текущей папке. Другое имя файла можно передать аргументом:

```bash
python my_script.py result.json
```

Требуется Python 3.10 или новее. Устанавливать ничего не нужно.

## Как работает

1. **Определение ОС** выполняется по `sys.platform`: `win*` означает Windows, `linux*` означает Linux, `darwin` означает macOS.
2. **Сбор параметров** разбит на группы, у каждой группы своя функция. Если ОС отдаёт параметр по-своему, функция выбирает нужный способ:
   - Windows: функции WinAPI через `ctypes` (`GlobalMemoryStatusEx`, `GetTickCount64`, `IsUserAnAdmin`);
   - Linux: чтение файлов `/proc/cpuinfo`, `/proc/meminfo`, `/proc/uptime` и `/etc/os-release`;
   - macOS: вызов `sysctlbyname` из libc через `ctypes`.

   Если какой-то параметр получить не удалось, вместо него записывается `null`, а скрипт продолжает работу.
3. **Запись результата** делается через `json.dump` в кодировке UTF-8 с отступами.

## Ограничения

- Используются только стандартные модули Python: `platform`, `sys`, `os`, `ctypes`, `socket`, `uuid`, `shutil`, `getpass`, `locale`, `time`, `datetime`, `struct`, `json`. Внешние модули не нужны.
- Системные утилиты ОС (`uname`, `systeminfo`, `sysctl`, `wmic` и т.п.) не вызываются, `subprocess` не используется. По той же причине скрипт обходится без `platform.architecture()` и без `platform.processor()` на Linux и macOS: обе функции внутри запускают внешние команды (`file`, `uname -p`).

## Собираемые параметры

| Группа | Параметр | Описание |
|---|---|---|
| — | `collected_at` | Дата и время сбора |
| `os` | `family` | Определённая ОС: Windows / Linux / MacOS |
| | `system`, `release`, `version` | Название, релиз и версия ядра или ОС |
| | `platform_string` | Полная строка платформы |
| | `sys_platform` | Значение `sys.platform` |
| | `edition`, `build`, `service_pack` | Редакция, сборка и пакет обновлений (только Windows) |
| | `distribution`, `distribution_id`, `distribution_version`, `libc` | Дистрибутив и версия libc (только Linux) |
| | `macos_version` | Версия macOS (только macOS) |
| `cpu` | `architecture` | Архитектура (AMD64, x86_64, arm64…) |
| | `bitness` | Разрядность (32 или 64) |
| | `logical_cores` | Число логических ядер |
| | `model` | Модель процессора |
| `memory` | `total_bytes`, `total_gb` | Объём ОЗУ |
| | `available_bytes`, `available_gb` | Свободная ОЗУ (кроме macOS) |
| | `used_percent` | Процент занятой памяти |
| `disk` | `path` | Системный диск или корень ФС |
| | `total_gb`, `used_gb`, `free_gb`, `used_percent` | Объём, занятое и свободное место |
| `boot` | `uptime_seconds`, `uptime_human` | Время работы с момента загрузки |
| | `boot_time` | Время загрузки системы |
| `network` | `hostname`, `fqdn` | Имя компьютера и полное доменное имя |
| | `local_ip` | Локальный IP-адрес основного интерфейса |
| | `mac_address` | MAC-адрес |
| `user` | `username`, `home_dir` | Текущий пользователь и его домашняя папка |
| | `is_admin` | Запущен ли скрипт с правами администратора (root) |
| | `shell` | Командная оболочка |
| `locale` | `language`, `encoding`, `preferred_encoding`, `filesystem_encoding` | Язык и кодировки |
| | `timezone`, `utc_offset_hours` | Часовой пояс и смещение от UTC |
| `python` | `version`, `implementation`, `compiler`, `executable` | Сведения об интерпретаторе |

## Пример результата (Windows, сокращено)

```json
{
    "collected_at": "2026-10-15T14:10:00",
    "os": {
        "family": "Windows",
        "system": "Windows",
        "release": "11",
        "version": "10.0.26300",
        "edition": "CoreSingleLanguage"
    },
    "cpu": {
        "architecture": "AMD64",
        "bitness": 64,
        "logical_cores": 14,
        "model": "Intel64 Family 6 Model 170 Stepping 4, GenuineIntel"
    },
    "memory": {
        "total_gb": 15.54,
        "available_gb": 2.08,
        "used_percent": 86.6
    },
    "boot": {
        "uptime_human": "0d 14h 22m"
    }
}
```
