"""Модуль построения графа зависимостей.

Этап 3: BFS с рекурсией, обработка циклов, фильтрация.
"""

import json
from typing import Callable


def load_test_repo(path: str) -> dict[str, list[str]]:
    """Загружает тестовый репозиторий из JSON-файла.

    Args:
        path: Путь к JSON-файлу.

    Returns:
        Словарь вида {пакет: [список_зависимостей]}.

    Raises:
        ValueError: если файл не найден или некорректен.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Файл тестового репозитория не найден: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON в {path}: {e}")

    if not isinstance(data, dict):
        raise ValueError(f"Некорректный формат тестового репозитория: {path}")

    return data


def should_skip(name: str, filter_substring: str) -> bool:
    """Проверяет, нужно ли пропустить пакет по подстроке.

    Args:
        name: Имя пакета.
        filter_substring: Подстрока для фильтрации.

    Returns:
        True, если пакет нужно пропустить.
    """
    if not filter_substring:
        return False
    return filter_substring.lower() in name.lower()


def build_graph_bfs(
    root_package: str,
    get_dependencies: Callable[[str], list[str]],
    filter_substring: str = "",
    max_depth: int = 100,
) -> dict[str, list[str]]:
    """Строит граф зависимостей через BFS с рекурсией.

    Args:
        root_package: Имя корневого пакета.
        get_dependencies: Функция, возвращающая прямые зависимости пакета.
        filter_substring: Подстрока для фильтрации пакетов.
        max_depth: Максимальная глубина обхода (защита от бесконечности).

    Returns:
        Словарь {пакет: [список_зависимостей]}.
    """
    graph: dict[str, list[str]] = {}
    visited: set[str] = set()

    def bfs_recursive(queue: list[tuple[str, int]]) -> None:
        """Рекурсивная часть BFS.

        Args:
            queue: Очередь из пар (имя_пакета, глубина).
        """
        if not queue:
            return

        current_pkg, depth = queue.pop(0)

        if current_pkg in visited:
            bfs_recursive(queue)
            return

        visited.add(current_pkg)

        if depth > max_depth:
            bfs_recursive(queue)
            return

        try:
            deps = get_dependencies(current_pkg)
        except ValueError:
            deps = []

        filtered_deps = [
            d for d in deps if not should_skip(d, filter_substring)
        ]
        graph[current_pkg] = filtered_deps

        for dep in filtered_deps:
            if dep not in visited:
                queue.append((dep, depth + 1))

        bfs_recursive(queue)

    bfs_recursive([(root_package, 0)])
    return graph


def print_graph(graph: dict[str, list[str]]) -> None:
    """Печатает граф зависимостей.

    Args:
        graph: Словарь {пакет: [список_зависимостей]}.
    """
    print(f"\nГраф зависимостей (узлов: {len(graph)}):")
    for pkg, deps in sorted(graph.items()):
        if deps:
            print(f"  {pkg} -> {', '.join(deps)}")
        else:
            print(f"  {pkg} -> (нет зависимостей)")