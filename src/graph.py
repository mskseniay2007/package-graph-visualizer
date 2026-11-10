"""Модуль построения графа зависимостей.

Этап 3-4: BFS с рекурсией, обработка циклов, фильтрация, обратные связи.
"""

import json
from typing import Callable


def load_test_repo(path: str) -> dict[str, list[str]]:
    """Загружает тестовый репозиторий из JSON-файла."""
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
    """Проверяет, нужно ли пропустить пакет по подстроке."""
    if not filter_substring:
        return False
    return filter_substring.lower() in name.lower()


def _process_bfs_node(
    current_pkg: str,
    depth: int,
    max_depth: int,
    get_deps: Callable[[str], list[str]],
    filter_sub: str,
    graph: dict[str, list[str]],
    visited: set[str],
    queue: list[tuple[str, int]]
) -> None:
    """Обрабатывает один узел в BFS и добавляет соседей в очередь."""
    visited.add(current_pkg)
    if depth > max_depth:
        return

    try:
        deps = get_deps(current_pkg)
    except ValueError:
        deps = []

    filtered_deps = [
        d for d in deps if not should_skip(d, filter_sub)
    ]
    graph[current_pkg] = filtered_deps

    for dep in filtered_deps:
        if dep not in visited:
            queue.append((dep, depth + 1))


def build_graph_bfs(
    root_package: str,
    get_dependencies: Callable[[str], list[str]],
    filter_substring: str = "",
    max_depth: int = 100,
) -> dict[str, list[str]]:
    """Строит граф зависимостей через BFS с рекурсией."""
    graph: dict[str, list[str]] = {}
    visited: set[str] = set()

    def bfs_recursive(queue: list[tuple[str, int]]) -> None:
        if not queue:
            return
        current_pkg, depth = queue.pop(0)

        if current_pkg in visited:
            bfs_recursive(queue)
            return

        _process_bfs_node(
            current_pkg, depth, max_depth,
            get_dependencies, filter_substring,
            graph, visited, queue
        )
        bfs_recursive(queue)

    bfs_recursive([(root_package, 0)])
    return graph


def print_graph(graph: dict[str, list[str]]) -> None:
    """Печатает граф зависимостей."""
    print(f"\nГраф зависимостей (узлов: {len(graph)}):")
    for pkg, deps in sorted(graph.items()):
        if deps:
            print(f"  {pkg} -> {', '.join(deps)}")
        else:
            print(f"  {pkg} -> (нет зависимостей)")


def build_reverse_graph(
    graph: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Строит обратный граф: кто зависит от кого."""
    reverse: dict[str, list[str]] = {}
    for pkg, deps in graph.items():
        if pkg not in reverse:
            reverse[pkg] = []
        for dep in deps:
            if dep not in reverse:
                reverse[dep] = []
            reverse[dep].append(pkg)
    return reverse


def _process_reverse_node(
    current: str,
    target: str,
    reverse: dict[str, list[str]],
    filter_sub: str,
    visited: set[str],
    result: list[str],
    queue: list[str]
) -> None:
    """Обрабатывает один узел при поиске обратных зависимостей."""
    visited.add(current)
    if should_skip(current, filter_sub):
        return
    if current != target:
        result.append(current)
    for parent in reverse.get(current, []):
        if parent not in visited:
            queue.append(parent)


def find_reverse_dependencies(
    graph: dict[str, list[str]],
    target: str,
    filter_substring: str = "",
) -> list[str]:
    """Находит все обратные зависимости для пакета через BFS."""
    reverse = build_reverse_graph(graph)
    visited: set[str] = set()
    result: list[str] = []

    def bfs_reverse(queue: list[str]) -> None:
        if not queue:
            return
        current = queue.pop(0)
        if current in visited:
            bfs_reverse(queue)
            return

        _process_reverse_node(
            current, target, reverse,
            filter_substring, visited, result, queue
        )
        bfs_reverse(queue)

    bfs_reverse([target])
    return sorted(result)