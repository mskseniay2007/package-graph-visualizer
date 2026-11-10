"""Модуль получения прямых зависимостей NuGet-пакета.

Этап 2: скачивание .nupkg, распаковка в памяти, парсинг .nuspec.
"""

import io
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ElementTree

HTTP_NOT_FOUND = 404


def download_nupkg(package_name: str, version: str, repo_url: str) -> bytes:
    """Скачивает .nupkg архив пакета и возвращает его байты."""
    if "/v3/" in repo_url:
        base_url = repo_url.rsplit("/v3/", 1)[0]
    else:
        base_url = "https://api.nuget.org"

    pkg_lower = package_name.lower()
    version_lower = version.lower()
    url = (
        f"{base_url}/v3-flatcontainer/{pkg_lower}/{version_lower}/"
        f"{pkg_lower}.{version_lower}.nupkg"
    )

    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        if e.code == HTTP_NOT_FOUND:
            msg = (
                f"Пакет '{package_name}' версии '{version}' "
                "не найден в репозитории."
            )
            raise ValueError(msg)
        raise ValueError(f"Ошибка HTTP при скачивании пакета: {e}")
    except Exception as e:
        raise ValueError(f"Ошибка при скачивании: {e}")


def extract_nuspec_xml(nupkg_bytes: bytes) -> str:
    """Открывает .nupkg в памяти как ZIP, находит .nuspec."""
    try:
        with zipfile.ZipFile(io.BytesIO(nupkg_bytes)) as zf:
            nuspec_files = [
                n for n in zf.namelist() if n.endswith(".nuspec")
            ]
            if not nuspec_files:
                raise ValueError("В архиве не найден .nuspec файл.")
            with zf.open(nuspec_files[0]) as nuspec_file:
                return nuspec_file.read().decode("utf-8")
    except zipfile.BadZipFile:
        raise ValueError("Файл не является корректным ZIP-архивом.")


def parse_direct_dependencies(nuspec_xml: str) -> list[tuple[str, str]]:
    """Парсит XML .nuspec и извлекает прямые зависимости."""
    try:
        root = ElementTree.fromstring(nuspec_xml)
    except ElementTree.ParseError:
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


def fetch_direct_dependencies(
    package_name: str, version: str, repo_url: str
) -> list[tuple[str, str]]:
    """Скачивает пакет и возвращает его прямые зависимости."""
    nupkg_bytes = download_nupkg(package_name, version, repo_url)
    nuspec_xml = extract_nuspec_xml(nupkg_bytes)
    return parse_direct_dependencies(nuspec_xml)