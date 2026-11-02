"""Модуль получения прямых зависимостей NuGet-пакета.

Этап 2: скачивание .nupkg, распаковка в памяти, парсинг .nuspec.
"""

import io
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ET


def download_nupkg(package_name: str, version: str, repo_url: str) -> bytes:
    """Скачивает .nupkg архив пакета и возвращает его байты.

    Args:
        package_name: Имя пакета (например, Newtonsoft.Json).
        version: Версия пакета (например, 13.0.3).
        repo_url: URL репозитория.

    Returns:
        Байты скачанного .nupkg файла.

    Raises:
        ValueError: если пакет не найден или произошла ошибка сети.
    """
    base_url = repo_url.rsplit("/v3/", 1)[0] if "/v3/" in repo_url else "https://api.nuget.org"
    pkg_lower = package_name.lower()
    version_lower = version.lower()

    url = f"{base_url}/v3-flatcontainer/{pkg_lower}/{version_lower}/{pkg_lower}.{version_lower}.nupkg"

    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"Пакет '{package_name}' версии '{version}' не найден в репозитории.")
        raise ValueError(f"Ошибка HTTP при скачивании пакета: {e}")
    except Exception as e:
        raise ValueError(f"Ошибка при скачивании: {e}")


def extract_nuspec_xml(nupkg_bytes: bytes) -> str:
    """Открывает .nupkg в памяти как ZIP, находит .nuspec и возвращает его текст.

    Args:
        nupkg_bytes: Байты скачанного .nupkg файла.

    Returns:
        Содержимое .nuspec файла в виде строки.

    Raises:
        ValueError: если .nuspec не найден или архив повреждён.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(nupkg_bytes)) as zf:
            nuspec_files = [n for n in zf.namelist() if n.endswith(".nuspec")]
            if not nuspec_files:
                raise ValueError("В архиве не найден .nuspec файл.")
            with zf.open(nuspec_files[0]) as nuspec_file:
                return nuspec_file.read().decode("utf-8")
    except zipfile.BadZipFile:
        raise ValueError("Скачанный файл не является корректным ZIP-архивом (.nupkg).")


def parse_direct_dependencies(nuspec_xml: str) -> list[tuple[str, str]]:
    """Парсит XML .nuspec и извлекает прямые зависимости.

    Args:
        nuspec_xml: Содержимое .nuspec файла.

    Returns:
        Список кортежей (имя_зависимости, версия_или_диапазон).
    """
    try:
        root = ET.fromstring(nuspec_xml)
    except ET.ParseError:
        raise ValueError("Ошибка парсинга XML в .nuspec файле.")

    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]

    dependencies = []

    for deps_block in root.iter("dependencies"):
        for dep in deps_block.iter("dependency"):
            dep_id = dep.get("id")
            dep_version = dep.get("version", "*")
            if dep_id:
                dependencies.append((dep_id, dep_version))

    return sorted(list(set(dependencies)))


def fetch_direct_dependencies(package_name: str, version: str, repo_url: str) -> list[tuple[str, str]]:
    """Главная функция: скачивает пакет и возвращает его прямые зависимости.

    Args:
        package_name: Имя пакета.
        version: Версия пакета.
        repo_url: URL репозитория.

    Returns:
        Список кортежей (имя, версия).
    """
    nupkg_bytes = download_nupkg(package_name, version, repo_url)
    nuspec_xml = extract_nuspec_xml(nupkg_bytes)
    return parse_direct_dependencies(nuspec_xml)