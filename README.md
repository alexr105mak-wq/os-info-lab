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
2. **Сбор параметров** делается модулем `platform`. Общие параметры собираются одинаково для всех ОС, а дополнительные зависят от системы:
   - Windows: редакция, сборка и пакет обновлений (`platform.win32_ver`, `platform.win32_edition`);
   - Linux: дистрибутив из `/etc/os-release` (`platform.freedesktop_os_release`) и версия libc;
   - macOS: версия macOS (`platform.mac_ver`).

   Если какой-то параметр получить не удалось, вместо него записывается `null`, а скрипт продолжает работу.
3. **Запись результата** делается через `json.dump` в кодировке UTF-8 с отступами.

## Ограничения

- Используются только стандартные модули Python: `platform`, `sys`, `os`, `datetime`, `json`. Внешние модули не нужны.
- Системные утилиты ОС (`uname`, `systeminfo`, `sysctl`, `wmic` и т.п.) не вызываются, `subprocess` не используется.

## Собираемые параметры

| Параметр | Описание | ОС |
|---|---|---|
| `collected_at` | Дата и время сбора | все |
| `os.family` | Определённая ОС: Windows / Linux / MacOS | все |
| `os.system` | Название системы | все |
| `os.release` | Релиз ОС или ядра | все |
| `os.version` | Версия ОС или ядра | все |
| `os.platform_string` | Полная строка платформы | все |
| `os.sys_platform` | Значение `sys.platform` | все |
| `os.edition` | Редакция | Windows |
| `os.build` | Номер сборки | Windows |
| `os.service_pack` | Пакет обновлений | Windows |
| `os.distribution` | Название дистрибутива | Linux |
| `os.distribution_id` | Идентификатор дистрибутива | Linux |
| `os.distribution_version` | Версия дистрибутива | Linux |
| `os.libc` | Версия libc | Linux |
| `os.macos_version` | Версия macOS | macOS |

## Пример результата (Windows)

```json
{
    "collected_at": "2026-10-15T14:15:13",
    "os": {
        "family": "Windows",
        "system": "Windows",
        "release": "11",
        "version": "10.0.26300",
        "platform_string": "Windows-11-10.0.26300-SP0",
        "sys_platform": "win32",
        "edition": "CoreSingleLanguage",
        "build": "10.0.26300",
        "service_pack": "SP0"
    }
}
```
